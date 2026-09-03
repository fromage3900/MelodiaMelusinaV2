"""Enemy definition wrappers — mirrors FMelodiaEnemyDef from MelodiaCore C++.

Data-driven access to the 5 demo enemies hard-coded in MelodiaEnemyDefinition.cpp.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

ENEMY_FIELDS = ("enemy_id", "display_name", "max_hp", "max_toughness",
                "base_damage", "speed", "element", "bpm", "display_mesh")

ELEMENTS = ("Forte", "Tide", "Gale", "Stone", "Radiant", "Umbral", "Arcane")


@dataclass
class MelodiaEnemyDef:
    enemy_id: str
    display_name: str
    max_hp: float = 300.0
    max_toughness: float = 100.0
    base_damage: float = 15.0
    speed: int = 80
    element: str = "Forte"
    bpm: float = 120.0
    display_mesh: Optional[str] = None
    mesh_scale: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)


DEMO_ENEMIES: dict[str, MelodiaEnemyDef] = {
    "CrystalShard": MelodiaEnemyDef(
        enemy_id="CrystalShard", display_name="Crystal Shard",
        max_hp=80, max_toughness=22, base_damage=7, speed=60,
        element="Forte", bpm=120.0,
    ),
    "StoneGolem": MelodiaEnemyDef(
        enemy_id="StoneGolem", display_name="Stone Golem",
        max_hp=155, max_toughness=40, base_damage=12, speed=50,
        element="Stone", bpm=100.0,
    ),
    "VoidWraith": MelodiaEnemyDef(
        enemy_id="VoidWraith", display_name="Void Wraith",
        max_hp=200, max_toughness=80, base_damage=22, speed=110,
        element="Umbral", bpm=140.0,
    ),
    "SakuraPhantom": MelodiaEnemyDef(
        enemy_id="SakuraPhantom", display_name="Sakura Phantom",
        max_hp=140, max_toughness=28, base_damage=10, speed=85,
        element="Radiant", bpm=128.0,
    ),
    "CosmicSentinel": MelodiaEnemyDef(
        enemy_id="CosmicSentinel", display_name="Cosmic Sentinel",
        max_hp=500, max_toughness=200, base_damage=25, speed=70,
        element="Arcane", bpm=144.0,
    ),
    "FireDrake": MelodiaEnemyDef(
        enemy_id="FireDrake", display_name="Fire Drake",
        max_hp=160, max_toughness=70, base_damage=12, speed=75,
        element="Forte", bpm=150.0,
    ),
    "ShadowWraith": MelodiaEnemyDef(
        enemy_id="ShadowWraith", display_name="Shadow Wraith",
        max_hp=100, max_toughness=40, base_damage=15, speed=95,
        element="Umbral", bpm=90.0,
    ),
    "ArcaneGolem": MelodiaEnemyDef(
        enemy_id="ArcaneGolem", display_name="Arcane Golem",
        max_hp=250, max_toughness=120, base_damage=10, speed=30,
        element="Arcane", bpm=70.0,
    ),
    "StormFalcon": MelodiaEnemyDef(
        enemy_id="StormFalcon", display_name="Storm Falcon",
        max_hp=90, max_toughness=30, base_damage=8, speed=120,
        element="Gale", bpm=180.0,
    ),
    "AbyssalKraken": MelodiaEnemyDef(
        enemy_id="AbyssalKraken", display_name="Abyssal Kraken",
        max_hp=300, max_toughness=150, base_damage=14, speed=20,
        element="Tide", bpm=60.0,
    ),
}

# Elite enemies — 2x stats for mid-game challenge
ELITE_ENEMIES: dict[str, MelodiaEnemyDef] = {
    "InfernoLord": MelodiaEnemyDef(
        enemy_id="InfernoLord", display_name="Inferno Lord",
        max_hp=350, max_toughness=150, base_damage=28, speed=65,
        element="Forte", bpm=160.0,
    ),
    "AbyssWatcher": MelodiaEnemyDef(
        enemy_id="AbyssWatcher", display_name="Abyss Watcher",
        max_hp=300, max_toughness=120, base_damage=35, speed=100,
        element="Umbral", bpm=130.0,
    ),
    "TempestDragon": MelodiaEnemyDef(
        enemy_id="TempestDragon", display_name="Tempest Dragon",
        max_hp=400, max_toughness=180, base_damage=30, speed=90,
        element="Gale", bpm=200.0,
    ),
}

# Boss enemies — 5x stats for end-game challenge
BOSS_ENEMIES: dict[str, MelodiaEnemyDef] = {
    "TitanPrime": MelodiaEnemyDef(
        enemy_id="TitanPrime", display_name="Titan Prime",
        max_hp=1200, max_toughness=500, base_damage=45, speed=40,
        element="Stone", bpm=80.0,
    ),
    "HarmonyVoid": MelodiaEnemyDef(
        enemy_id="HarmonyVoid", display_name="Harmony Void",
        max_hp=800, max_toughness=300, base_damage=55, speed=120,
        element="Arcane", bpm=200.0,
    ),
}

ALL_ENEMIES: dict[str, MelodiaEnemyDef] = {}
ALL_ENEMIES.update(DEMO_ENEMIES)
ALL_ENEMIES.update(ELITE_ENEMIES)
ALL_ENEMIES.update(BOSS_ENEMIES)


def list_enemies() -> list[dict]:
    return [e.to_dict() for e in ALL_ENEMIES.values()]


def get_enemy(enemy_id: str) -> Optional[MelodiaEnemyDef]:
    return ALL_ENEMIES.get(enemy_id)


def audit_enemy_summary() -> dict:
    return {
        "count": len(ALL_ENEMIES),
        "enemies": list(ALL_ENEMIES.keys()),
        "elements": list(set(e.element for e in ALL_ENEMIES.values())),
    }
