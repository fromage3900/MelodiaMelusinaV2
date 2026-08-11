"""Equipment Catalog — starter equipment definitions for the Melodia rhythm battle game.

Each piece of equipment maps to one of 5 slots and provides stat bonuses.
Compatible with Equipment dataclass in player_state.py.

Usage:
    from gmm.game.equipment_catalog import get_equipment, list_equipment
    sword = get_equipment("iron_sword")
"""
from __future__ import annotations

from gmm.game.player_state import Equipment


# ---------------------------------------------------------------------------
# Weapons
# ---------------------------------------------------------------------------

WEAPONS = [
    Equipment(item_id="iron_sword", display_name="Iron Sword", slot="weapon",
              min_attack_bonus=3, max_attack_bonus=5),
    Equipment(item_id="steel_blade", display_name="Steel Blade", slot="weapon",
              min_attack_bonus=6, max_attack_bonus=9, speed_bonus=5),
    Equipment(item_id="crystal_rapier", display_name="Crystal Rapier", slot="weapon",
              min_attack_bonus=4, max_attack_bonus=12, speed_bonus=10, element="Forte"),
    Equipment(item_id="tidal_wand", display_name="Tidal Wand", slot="weapon",
              min_attack_bonus=2, max_attack_bonus=8, magic_attack_bonus=10,
              element="Tide", hp_bonus=10),
    Equipment(item_id="umbral_scythe", display_name="Umbral Scythe", slot="weapon",
              min_attack_bonus=8, max_attack_bonus=14, defense_bonus=3,
              element="Umbral", speed_bonus=-5),
]

# ---------------------------------------------------------------------------
# Armor
# ---------------------------------------------------------------------------

ARMORS = [
    Equipment(item_id="leather_vest", display_name="Leather Vest", slot="armor",
              defense_bonus=5, hp_bonus=10),
    Equipment(item_id="chainmail", display_name="Chainmail", slot="armor",
              defense_bonus=10, hp_bonus=20),
    Equipment(item_id="forte_plate", display_name="Forte Plate", slot="armor",
              defense_bonus=15, hp_bonus=30, magic_defense_bonus=5,
              element="Forte"),
    Equipment(item_id="arcane_robe", display_name="Arcane Robe", slot="armor",
              defense_bonus=3, magic_defense_bonus=15, mp_bonus=30,
              element="Arcane"),
    Equipment(item_id="gale_mantle", display_name="Gale Mantle", slot="armor",
              defense_bonus=7, magic_defense_bonus=7, speed_bonus=15,
              element="Gale"),
]

# ---------------------------------------------------------------------------
# Shields
# ---------------------------------------------------------------------------

SHIELDS = [
    Equipment(item_id="wooden_shield", display_name="Wooden Shield", slot="shield",
              defense_bonus=8, hp_bonus=15),
    Equipment(item_id="iron_shield", display_name="Iron Shield", slot="shield",
              defense_bonus=12, hp_bonus=25),
    Equipment(item_id="crystal_barrier", display_name="Crystal Barrier", slot="shield",
              defense_bonus=10, magic_defense_bonus=10, hp_bonus=20,
              element="Radiant"),
    Equipment(item_id="stone_wall", display_name="Stone Wall", slot="shield",
              defense_bonus=18, hp_bonus=35, speed_bonus=-10, element="Stone"),
]

# ---------------------------------------------------------------------------
# Helms
# ---------------------------------------------------------------------------

HELMS = [
    Equipment(item_id="leather_cap", display_name="Leather Cap", slot="helm",
              defense_bonus=3, hp_bonus=5),
    Equipment(item_id="iron_helm", display_name="Iron Helm", slot="helm",
              defense_bonus=6, hp_bonus=10),
    Equipment(item_id="crown_of_tides", display_name="Crown of Tides", slot="helm",
              defense_bonus=4, magic_defense_bonus=8, mp_bonus=20,
              element="Tide"),
    Equipment(item_id="diadem_of_radiance", display_name="Diadem of Radiance", slot="helm",
              magic_attack_bonus=8, mp_bonus=15, element="Radiant"),
]

# ---------------------------------------------------------------------------
# Boots
# ---------------------------------------------------------------------------

BOOTS = [
    Equipment(item_id="leather_boots", display_name="Leather Boots", slot="boots",
              speed_bonus=5, defense_bonus=1),
    Equipment(item_id="iron_greaves", display_name="Iron Greaves", slot="boots",
              defense_bonus=5, speed_bonus=2),
    Equipment(item_id="gale_striders", display_name="Gale Striders", slot="boots",
              speed_bonus=20, defense_bonus=2, element="Gale"),
    Equipment(item_id="umbral_treads", display_name="Umbral Treads", slot="boots",
              speed_bonus=10, magic_defense_bonus=5, element="Umbral"),
]

# ---------------------------------------------------------------------------
# Rare-tier equipment (daemon-generated)
# ---------------------------------------------------------------------------

RARE_WEAPONS = [
    Equipment(item_id="forte_brand", display_name="Forte Brand", slot="weapon",
              min_attack_bonus=10, max_attack_bonus=16, speed_bonus=8,
              element="Forte"),
    Equipment(item_id="tide_trident", display_name="Tide Trident", slot="weapon",
              min_attack_bonus=8, max_attack_bonus=14, hp_bonus=30,
              element="Tide"),
    Equipment(item_id="umbral_sickle", display_name="Umbral Sickle", slot="weapon",
              min_attack_bonus=12, max_attack_bonus=18, defense_bonus=5,
              element="Umbral"),
    Equipment(item_id="arcane_staff", display_name="Arcane Staff", slot="weapon",
              min_attack_bonus=5, max_attack_bonus=10, magic_attack_bonus=15,
              element="Arcane"),
    Equipment(item_id="gale_blade", display_name="Gale Blade", slot="weapon",
              min_attack_bonus=9, max_attack_bonus=12, speed_bonus=25,
              element="Gale"),
]

RARE_SHIELDS = [
    Equipment(item_id="forte_aegis", display_name="Forte Aegis", slot="shield",
              defense_bonus=14, hp_bonus=30, magic_defense_bonus=8, element="Forte"),
    Equipment(item_id="tide_barrier", display_name="Tide Barrier", slot="shield",
              defense_bonus=10, hp_bonus=45, magic_defense_bonus=12, element="Tide"),
    Equipment(item_id="umbral_ward", display_name="Umbral Ward", slot="shield",
              defense_bonus=8, magic_defense_bonus=20, speed_bonus=5, element="Umbral"),
    Equipment(item_id="arcane_buckler", display_name="Arcane Buckler", slot="shield",
              defense_bonus=12, magic_defense_bonus=15, mp_bonus=25, element="Arcane"),
]

RARE_ARMORS = [
    Equipment(item_id="forte_cuirass", display_name="Forte Cuirass", slot="armor",
              defense_bonus=18, hp_bonus=40, element="Forte"),
    Equipment(item_id="tide_scale", display_name="Tide Scale", slot="armor",
              defense_bonus=12, hp_bonus=50, magic_defense_bonus=10,
              element="Tide"),
    Equipment(item_id="umbral_shroud", display_name="Umbral Shroud", slot="armor",
              defense_bonus=10, magic_defense_bonus=20, speed_bonus=10,
              element="Umbral"),
    Equipment(item_id="arcane_vestments", display_name="Arcane Vestments", slot="armor",
              defense_bonus=8, magic_defense_bonus=25, mp_bonus=40,
              element="Arcane"),
    Equipment(item_id="gale_habit", display_name="Gale Habit", slot="armor",
              defense_bonus=6, magic_defense_bonus=6, speed_bonus=30,
              element="Gale"),
]

# ---------------------------------------------------------------------------
# Rare-tier helms (daemon-generated)
# ---------------------------------------------------------------------------

RARE_HELMS = [
    Equipment(item_id="forte_crown", display_name="Forte Crown", slot="helm",
              defense_bonus=8, hp_bonus=20, element="Forte"),
    Equipment(item_id="tide_circlet", display_name="Tide Circlet", slot="helm",
              defense_bonus=4, magic_defense_bonus=12, mp_bonus=30, element="Tide"),
    Equipment(item_id="umbral_visage", display_name="Umbral Visage", slot="helm",
              magic_attack_bonus=10, magic_defense_bonus=8, speed_bonus=5, element="Umbral"),
    Equipment(item_id="gale_headband", display_name="Gale Headband", slot="helm",
              defense_bonus=2, speed_bonus=25, magic_defense_bonus=4, element="Gale"),
]

# ---------------------------------------------------------------------------
# Rare-tier boots (daemon-generated)
# ---------------------------------------------------------------------------

RARE_BOOTS = [
    Equipment(item_id="forte_treads", display_name="Forte Treads", slot="boots",
              defense_bonus=8, speed_bonus=8, hp_bonus=15, element="Forte"),
    Equipment(item_id="tide_waders", display_name="Tide Waders", slot="boots",
              defense_bonus=4, speed_bonus=5, hp_bonus=25, element="Tide"),
    Equipment(item_id="arcane_slippers", display_name="Arcane Slippers", slot="boots",
              magic_defense_bonus=8, speed_bonus=15, mp_bonus=15, element="Arcane"),
    Equipment(item_id="storm_striders", display_name="Storm Striders", slot="boots",
              defense_bonus=3, speed_bonus=35, element="Gale"),
]

# ---------------------------------------------------------------------------
# Combined catalog
# ---------------------------------------------------------------------------

ALL_EQUIPMENT: list[Equipment] = WEAPONS + ARMORS + SHIELDS + HELMS + BOOTS + RARE_WEAPONS + RARE_SHIELDS + RARE_HELMS + RARE_BOOTS + RARE_ARMORS
_EQUIP_MAP: dict[str, Equipment] = {e.item_id: e for e in ALL_EQUIPMENT}


def get_equipment(item_id: str) -> Equipment | None:
    return _EQUIP_MAP.get(item_id)


def list_equipment(slot: str = "") -> list[dict]:
    items = ALL_EQUIPMENT
    if slot:
        items = [e for e in ALL_EQUIPMENT if e.slot == slot]
    return [e.to_dict() for e in items]


def list_by_slot() -> dict[str, list[dict]]:
    slots = {}
    for e in ALL_EQUIPMENT:
        slots.setdefault(e.slot, []).append(e.to_dict())
    return slots


def starter_kit() -> list[Equipment]:
    return [
        get_equipment("iron_sword"),
        get_equipment("leather_vest"),
        get_equipment("wooden_shield"),
        get_equipment("leather_cap"),
        get_equipment("leather_boots"),
    ]


def catalog_summary() -> dict:
    return {
        "total": len(ALL_EQUIPMENT),
        "by_slot": {s: len([e for e in ALL_EQUIPMENT if e.slot == s])
                     for s in ("weapon", "armor", "shield", "helm", "boots")},
        "items": [e.item_id for e in ALL_EQUIPMENT],
    }
