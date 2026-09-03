"""Data Registry — config-driven asset generator for enemies, skills, stats.

Creates UDataTable assets in the Content Browser from the existing
Python data (DEMO_ENEMIES, DEMO_SKILLS), making balance tuning possible
without editing Python code.

Also provides in-memory data access for standalone testing
(no UE editor required).

Data model aligned with TurnBasedJRPGTemplate S_UnitStats:
    maxHP, maxMP, minAttack, maxAttack, defense, speed, hit,
    minMagicalAttack, maxMagicalAttack, magicDefense, actionTime

Melodia-specific additions:
    element (str), bpm (float), toughness (float), instrument (str)
"""
from __future__ import annotations

import dataclasses
import json
from typing import Any, Optional

from gmm.melodia.enemies import list_enemies, DEMO_ENEMIES, ELEMENTS
from gmm.melodia.skills import list_skills, DEMO_SKILLS


# ---------------------------------------------------------------------------
# Data Models (compatible with TurnBasedJRPGTemplate S_UnitStats)
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class EnemyStats:
    """Enemy stat block — matches S_UnitStats pattern + Melodia extras."""
    enemy_id: str
    display_name: str
    max_hp: float = 100.0
    max_mp: float = 50.0
    min_attack: float = 5.0
    max_attack: float = 15.0
    defense: float = 5.0
    speed: int = 80
    hit: float = 0.9
    min_magical_attack: float = 0.0
    max_magical_attack: float = 0.0
    magic_defense: float = 5.0
    action_time: float = 1.0
    toughness: float = 100.0
    element: str = "Forte"
    bpm: float = 120.0
    display_mesh: Optional[str] = None
    xp_reward: int = 50
    gold_reward: int = 30

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class SkillData:
    """Skill definition — compatible with E_ActionType.Skill."""
    skill_id: str
    display_name: str
    description: str = ""
    element: str = "Forte"
    instrument: str = "MusicBox"
    mechanic_level: int = 1
    sp_cost: int = 1
    power_scalar: float = 1.0
    note_pitches: tuple[int, ...] = (60,)
    note_durations: tuple[float, ...] = (0.25,)
    base_damage: float = 25.0
    aoe: bool = False
    heal_scale: float = 0.0

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["note_pitches"] = list(d["note_pitches"])
        d["note_durations"] = list(d["note_durations"])
        return d


@dataclasses.dataclass
class PlayerUnitStats:
    """Player character stats — compatible with S_PlayerUnitData."""
    unit_id: str
    display_name: str
    class_name: str = "Melodist"
    max_hp: float = 100.0
    max_mp: float = 100.0
    min_attack: float = 8.0
    max_attack: float = 12.0
    defense: float = 8.0
    speed: int = 90
    hit: float = 0.95
    min_magical_attack: float = 6.0
    max_magical_attack: float = 10.0
    magic_defense: float = 8.0
    action_time: float = 0.8
    xp_to_next: int = 100
    xp_mult: float = 1.5

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# In-Memory Registry (no UE editor required)
# ---------------------------------------------------------------------------

class MelodiaDataRegistry:
    """Data registry for enemies, skills, and player stats.

    Provides in-memory access for standalone testing.
    Call build_data_tables() in the editor to generate UDataTable assets.
    """

    def __init__(self):
        self.enemies: dict[str, EnemyStats] = {}
        self.skills: dict[str, SkillData] = {}
        self.player_units: dict[str, PlayerUnitStats] = {}
        self._load_defaults()

    def _load_defaults(self):
        """Seed registry from the existing demo data."""
        for e in DEMO_ENEMIES.values():
            self.enemies[e.enemy_id] = EnemyStats(
                enemy_id=e.enemy_id,
                display_name=e.display_name,
                max_hp=e.max_hp,
                max_attack=e.base_damage,
                speed=e.speed,
                toughness=e.max_toughness,
                element=e.element,
                bpm=e.bpm,
                display_mesh=e.display_mesh,
                xp_reward=int(e.max_hp * 0.4),
                gold_reward=int(e.max_hp * 0.25),
            )

        for s in DEMO_SKILLS:
            base_dmg = 10 + s.power_scalar * 15
            self.skills[s.skill_id] = SkillData(
                skill_id=s.skill_id,
                display_name=s.display_name,
                description=f"A level-{s.mechanic_level} {s.instrument} technique.",
                element=s.element,
                instrument=s.instrument,
                mechanic_level=s.mechanic_level,
                sp_cost=s.sp_cost,
                power_scalar=s.power_scalar,
                note_pitches=s.note_pitches,
                note_durations=s.note_durations,
                base_damage=base_dmg,
                heal_scale=0.2 if "heal" in s.element.lower() or "Heal" in s.display_name else 0.0,
            )

        self.player_units["melodist"] = PlayerUnitStats(
            unit_id="melodist",
            display_name="Melodist",
            class_name="Melodist",
        )

    def get_enemy(self, enemy_id: str) -> Optional[EnemyStats]:
        return self.enemies.get(enemy_id)

    def get_skill(self, skill_id: str) -> Optional[SkillData]:
        return self.skills.get(skill_id)

    def get_player_unit(self, unit_id: str = "melodist") -> Optional[PlayerUnitStats]:
        return self.player_units.get(unit_id)

    def list_enemies(self) -> list[dict]:
        return [e.to_dict() for e in self.enemies.values()]

    def list_skills(self) -> list[dict]:
        return [s.to_dict() for s in self.skills.values()]

    def export_json(self, path: str = "") -> str:
        """Export registry to JSON for data table seeding."""
        data = {
            "enemies": {k: v.to_dict() for k, v in self.enemies.items()},
            "skills": {k: v.to_dict() for k, v in self.skills.items()},
            "player_units": {k: v.to_dict() for k, v in self.player_units.items()},
        }
        text = json.dumps(data, indent=2, default=str)
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        return text

    def summary(self) -> dict:
        return {
            "enemy_count": len(self.enemies),
            "skill_count": len(self.skills),
            "player_unit_count": len(self.player_units),
            "enemies": list(self.enemies.keys()),
            "skills": list(self.skills.keys()),
            "elements": list(set(e.element for e in self.enemies.values())),
        }


# ---------------------------------------------------------------------------
# UE Editor: UDataTable Builder (requires running editor)
# ---------------------------------------------------------------------------

def _make_table_path(name: str) -> str:
    return f"/Game/Data/Melodia/DT_{name}"


def build_data_tables(registry: Optional[MelodiaDataRegistry] = None,
                      force: bool = False) -> dict:
    """Generate UDataTable assets from registry data.

    Requires running UE Editor with Python scripting.

    Tables created:
        DT_MelodiaEnemies  — Enemy stat definitions
        DT_MelodiaSkills   — Skill data
        DT_MelodiaPlayer   — Player unit defaults
    """
    if registry is None:
        registry = MelodiaDataRegistry()

    try:
        import unreal
    except ImportError:
        return {"ok": False, "error": "unreal module not available (not in editor)"}

    results = {}

    # Enemies table
    try:
        enemy_path = _make_table_path("MelodiaEnemies")
        existing = unreal.EditorAssetLibrary.does_asset_exist(enemy_path)
        if existing and not force:
            results["enemies"] = {"ok": True, "path": enemy_path, "skipped": True}
        else:
            table = _create_data_table(enemy_path, "EnemyStats")
            for enemy in registry.enemies.values():
                row = table.add_row(enemy.enemy_id)
                _set_row_fields(row, enemy.to_dict())
            unreal.EditorAssetLibrary.save_asset(enemy_path)
            results["enemies"] = {"ok": True, "path": enemy_path, "rows": len(registry.enemies)}
    except Exception as e:
        results["enemies"] = {"ok": False, "error": str(e)}

    # Skills table
    try:
        skill_path = _make_table_path("MelodiaSkills")
        existing = unreal.EditorAssetLibrary.does_asset_exist(skill_path)
        if existing and not force:
            results["skills"] = {"ok": True, "path": skill_path, "skipped": True}
        else:
            table = _create_data_table(skill_path, "SkillData")
            for skill in registry.skills.values():
                row = table.add_row(skill.skill_id)
                _set_row_fields(row, skill.to_dict())
            unreal.EditorAssetLibrary.save_asset(skill_path)
            results["skills"] = {"ok": True, "path": skill_path, "rows": len(registry.skills)}
    except Exception as e:
        results["skills"] = {"ok": False, "error": str(e)}

    # Player table
    try:
        player_path = _make_table_path("MelodiaPlayer")
        existing = unreal.EditorAssetLibrary.does_asset_exist(player_path)
        if existing and not force:
            results["player"] = {"ok": True, "path": player_path, "skipped": True}
        else:
            table = _create_data_table(player_path, "PlayerUnitStats")
            for unit in registry.player_units.values():
                row = table.add_row(unit.unit_id)
                _set_row_fields(row, unit.to_dict())
            unreal.EditorAssetLibrary.save_asset(player_path)
            results["player"] = {"ok": True, "path": player_path, "rows": len(registry.player_units)}
    except Exception as e:
        results["player"] = {"ok": False, "error": str(e)}

    all_ok = all(r.get("ok") for r in results.values())
    return {"ok": all_ok, "results": results}


def _create_data_table(path: str, struct_name: str):
    """Create or load a UDataTable asset at path."""
    import unreal
    factory = unreal.DataTableFactory()
    struct_script = unreal.load_asset(f"/Script/{struct_name}")
    if struct_script:
        factory.struct = struct_script
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset = asset_tools.create_asset(
        path.split("/")[-1],
        "/".join(path.split("/")[:-1]),
        None,
        unreal.DataTable,
        factory,
    )
    return asset


def _set_row_fields(row, data: dict):
    """Set all serializable fields on a DataTable row."""
    for key, value in data.items():
        if isinstance(value, (int, float, str, bool)):
            try:
                setattr(row, key, value)
            except Exception:
                pass
        elif isinstance(value, (list, tuple)):
            try:
                setattr(row, key, list(value))
            except Exception:
                pass
