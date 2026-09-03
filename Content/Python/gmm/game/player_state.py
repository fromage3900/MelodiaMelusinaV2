"""Player State — stat container with XP/leveling, inventory, equipment, save/load.

Pure-Python runtime that mirrors BP_JRPGGameInstance + BP_JRPGSaveGame
from the TurnBasedJRPGTemplate. Compatible with the template's data model:

    S_UnitStats: maxHP, maxMP, minAttack, maxAttack, defense, speed, hit, ...
    S_PlayerUnitData: Exp, currentHP, currentMP, Weapon, Armor, Shield, Helm, Boots
    E_EquipmentType: Weapon, Armor, Shield, Helm, Boots
    E_ActionType: Attack, Skill, Item, Flee, None, Interact

Works standalone (no UE required). Call save_json() / load_json() for persistence.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Constants (aligned with template E_EquipmentType)
# ---------------------------------------------------------------------------

EQUIPMENT_SLOTS = ("weapon", "armor", "shield", "helm", "boots")


@dataclass
class Equipment:
    """Equipment item — compatible with template's BP_EquipmentBase."""
    item_id: str
    display_name: str
    slot: str = "weapon"
    min_attack_bonus: float = 0.0
    max_attack_bonus: float = 0.0
    defense_bonus: float = 0.0
    magic_attack_bonus: float = 0.0
    magic_defense_bonus: float = 0.0
    speed_bonus: int = 0
    hp_bonus: float = 0.0
    mp_bonus: float = 0.0
    element: str = ""
    description: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class InventoryItem:
    """Inventory item stack — compatible with template's BP_ItemBase."""
    item_id: str
    display_name: str
    item_type: str = "usable"  # usable, misc, craft, key
    quantity: int = 1
    max_stack: int = 99
    description: str = ""
    heal_hp: float = 0.0
    heal_mp: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class SaveSlot:
    """Save data — compatible with template's BP_JRPGSaveGame."""
    slot_name: str = "save_00"
    save_date: str = ""
    play_time_seconds: float = 0.0
    level_name: str = "MelodiaOverworld"
    player_hp: float = 100.0
    player_mp: float = 100.0
    xp: int = 0
    level: int = 1
    gold: int = 0
    equipment: dict[str, str] = field(default_factory=lambda: {
        "weapon": "", "armor": "", "shield": "", "helm": "", "boots": "",
    })
    inventory: dict[str, int] = field(default_factory=dict)
    unlocked_skills: list[str] = field(default_factory=list)
    completed_encounters: list[str] = field(default_factory=list)
    mana_current: float = 50.0
    mana_max: float = 100.0
    golden_tokens: int = 0
    element_shards: dict[str, int] = field(default_factory=dict)
    total_tokens_collected: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Player State
# ---------------------------------------------------------------------------

class MelodiaPlayerState:
    """Player state container — manages stats, equipment, inventory, XP/leveling.

    Usage:
        ps = MelodiaPlayerState()
        ps.add_xp(50)
        ps.equip_item(sword)
        ps.take_damage(15)
        ps.save_to_file("save.json")
    """

    BASE_XP_TO_NEXT = 100
    XP_MULT = 1.5

    def __init__(self):
        self.level: int = 1
        self.xp: int = 0

        self.max_hp: float = 100.0
        self.max_mp: float = 100.0
        self.hp: float = 100.0
        self.mp: float = 100.0

        self.min_attack: float = 8.0
        self.max_attack: float = 12.0
        self.defense: float = 8.0
        self.speed: int = 90
        self.hit: float = 0.95
        self.min_magical_attack: float = 6.0
        self.max_magical_attack: float = 10.0
        self.magic_defense: float = 8.0
        self.sp: float = 50.0
        self.max_sp: float = 100.0
        self.ult_gauge: float = 0.0

        self.gold: int = 0

        # Equipment by slot (item_id -> Equipment)
        self.equipment: dict[str, Optional[Equipment]] = {
            s: None for s in EQUIPMENT_SLOTS
        }

        # Inventory (item_id -> InventoryItem)
        self.inventory: dict[str, InventoryItem] = {}

        # Unlocked skill IDs
        self.unlocked_skills: list[str] = []

        # Completed encounter IDs (for respawn tracking)
        self.completed_encounters: list[str] = []

        # Equipment library (all owned equipment, not just equipped)
        self.equipment_library: dict[str, Equipment] = {}

        # Token wallet (mana, energy shards, currency)
        from gmm.game.tokens import TokenWallet
        self.token_wallet: TokenWallet = TokenWallet()

        # Play time
        self._start_time: float = time.time()
        self.play_time_seconds: float = 0.0

    # -- Stats --

    def xp_to_next_level(self) -> int:
        return int(self.BASE_XP_TO_NEXT * (self.XP_MULT ** (self.level - 1)))

    def add_xp(self, amount: int) -> list[int]:
        """Add XP and return list of levels gained."""
        gained = []
        self.xp += max(0, amount)
        while self.xp >= self.xp_to_next_level():
            self.xp -= self.xp_to_next_level()
            self.level += 1
            self._apply_level_up()
            gained.append(self.level)
        return gained

    def _apply_level_up(self):
        hp_gain = 8 + self.level * 2
        mp_gain = 5 + self.level
        self.max_hp += hp_gain
        self.max_mp += mp_gain
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.min_attack += 1
        self.max_attack += 1.5
        self.defense += 1
        self.min_magical_attack += 1
        self.max_magical_attack += 1.5
        self.magic_defense += 1
        self.max_sp += 5
        self.sp = self.max_sp

    def take_damage(self, amount: float) -> float:
        """Apply damage after defense reduction. Returns actual damage dealt."""
        effective = max(0, amount - self.defense * 0.5)
        self.hp = max(0, self.hp - effective)
        return effective

    def heal(self, amount: float):
        self.hp = min(self.max_hp, self.hp + amount)

    def restore_mp(self, amount: float):
        self.mp = min(self.max_mp, self.mp + amount)

    def spend_sp(self, cost: int) -> bool:
        if self.sp >= cost:
            self.sp -= cost
            return True
        return False

    def add_ult(self, amount: float):
        self.ult_gauge = min(100.0, self.ult_gauge + amount)

    def reset_ult(self):
        self.ult_gauge = 0.0

    def full_restore(self):
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.sp = self.max_sp

    # -- Equipment --

    def equip_item(self, item: Equipment):
        slot = item.slot
        if slot not in EQUIPMENT_SLOTS:
            return
        self.equipment[slot] = item
        self.equipment_library[item.item_id] = item

    def unequip_slot(self, slot: str) -> Optional[Equipment]:
        item = self.equipment.get(slot)
        self.equipment[slot] = None
        return item

    def get_equipped_stats(self) -> dict[str, float]:
        stats = {
            "min_attack": self.min_attack,
            "max_attack": self.max_attack,
            "defense": self.defense,
            "speed": float(self.speed),
            "min_magical_attack": self.min_magical_attack,
            "max_magical_attack": self.max_magical_attack,
            "magic_defense": self.magic_defense,
            "hp_bonus": 0.0,
            "mp_bonus": 0.0,
        }
        for item in self.equipment.values():
            if not item:
                continue
            stats["min_attack"] += item.min_attack_bonus
            stats["max_attack"] += item.max_attack_bonus
            stats["defense"] += item.defense_bonus
            stats["magic_defense"] += item.magic_defense_bonus
            stats["speed"] += item.speed_bonus
            stats["min_magical_attack"] += item.magic_attack_bonus
            stats["max_magical_attack"] += item.magic_attack_bonus
            stats["hp_bonus"] += item.hp_bonus
            stats["mp_bonus"] += item.mp_bonus
        return stats

    # -- Inventory --

    def add_item(self, item: InventoryItem):
        existing = self.inventory.get(item.item_id)
        if existing:
            existing.quantity = min(existing.max_stack, existing.quantity + item.quantity)
        else:
            clamped = InventoryItem(
                item_id=item.item_id, display_name=item.display_name,
                item_type=item.item_type, quantity=min(item.max_stack, item.quantity),
                max_stack=item.max_stack, description=item.description,
                heal_hp=item.heal_hp, heal_mp=item.heal_mp,
            )
            self.inventory[item.item_id] = clamped

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        item = self.inventory.get(item_id)
        if not item or item.quantity < quantity:
            return False
        item.quantity -= quantity
        if item.quantity <= 0:
            del self.inventory[item_id]
        return True

    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        item = self.inventory.get(item_id)
        return item is not None and item.quantity >= quantity

    def add_gold(self, amount: int):
        self.gold += max(0, amount)

    def spend_gold(self, amount: int) -> bool:
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    # -- Skills --

    def unlock_skill(self, skill_id: str):
        if skill_id not in self.unlocked_skills:
            self.unlocked_skills.append(skill_id)

    def has_skill(self, skill_id: str) -> bool:
        return skill_id in self.unlocked_skills

    def skills_for_level(self) -> list[str]:
        from gmm.melodia.skills import DEMO_SKILLS
        return [s.skill_id for s in DEMO_SKILLS if s.mechanic_level <= self.level]

    # -- Save/Load --

    def to_save_data(self) -> SaveSlot:
        return SaveSlot(
            slot_name="auto_save",
            save_date=time.strftime("%Y-%m-%d %H:%M:%S"),
            play_time_seconds=max(time.time() - self._start_time, 1e-6),
            player_hp=self.hp,
            player_mp=self.mp,
            xp=self.xp,
            level=self.level,
            gold=self.gold,
            equipment={s: (e.item_id if e else "") for s, e in self.equipment.items()},
            inventory={k: v.quantity for k, v in self.inventory.items()},
            unlocked_skills=list(self.unlocked_skills),
            completed_encounters=list(self.completed_encounters),
            # Token wallet persistence
            mana_current=self.token_wallet.mana_current,
            mana_max=self.token_wallet.mana_max,
            golden_tokens=self.token_wallet.golden_tokens,
            element_shards=dict(self.token_wallet.shards),
        )

    def load_from_save(self, save: SaveSlot):
        self.xp = save.xp
        self.level = save.level
        self.gold = save.gold
        self.inventory = {}
        for item_id, qty in save.inventory.items():
            self.inventory[item_id] = InventoryItem(item_id=item_id, display_name=item_id, quantity=qty)
        self.unlocked_skills = list(save.unlocked_skills)
        self.completed_encounters = list(save.completed_encounters)
        self._recalc_stats()
        self.hp = min(self.max_hp, save.player_hp)
        self.mp = min(self.max_mp, save.player_mp)
        # Restore token wallet
        self.token_wallet.mana_current = getattr(save, 'mana_current', self.token_wallet.mana_current)
        self.token_wallet.mana_max = getattr(save, 'mana_max', self.token_wallet.mana_max)
        self.token_wallet.golden_tokens = getattr(save, 'golden_tokens', 0)
        if hasattr(save, 'element_shards') and save.element_shards:
            self.token_wallet.shards.update(save.element_shards)

    def _recalc_stats(self):
        for _ in range(1, self.level):
            self._apply_level_up()

    def save_to_file(self, path: str = "") -> str:
        if not path:
            path = os.path.join(os.getcwd(), "melodia_save.json")
        data = self.to_save_data().to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def load_from_file(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        save = SaveSlot(**data)
        self.load_from_save(save)
        return True

    def describe(self) -> dict:
        return {
            "level": self.level,
            "xp": self.xp,
            "xp_to_next": self.xp_to_next_level(),
            "hp": f"{self.hp:.0f}/{self.max_hp:.0f}",
            "mp": f"{self.mp:.0f}/{self.max_mp:.0f}",
            "sp": f"{self.sp:.0f}/{self.max_sp:.0f}",
            "ult": f"{self.ult_gauge:.0f}/100",
            "gold": self.gold,
            "attack": f"{self.min_attack:.0f}-{self.max_attack:.0f}",
            "defense": f"{self.defense:.0f}",
            "skills_unlocked": len(self.unlocked_skills),
            "items": len(self.inventory),
            "equipped": {s: (e.display_name if e else None) for s, e in self.equipment.items()},
            # Token wallet
            "mana": f"{self.token_wallet.mana_current:.0f}/{self.token_wallet.mana_max:.0f}",
            "shards": dict(self.token_wallet.shards),
            "golden_tokens": self.token_wallet.golden_tokens,
            "total_tokens_collected": self.token_wallet.total_collected,
        }
