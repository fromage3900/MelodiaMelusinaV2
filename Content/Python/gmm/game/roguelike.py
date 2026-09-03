"""Offline roguelike balance simulation and authoring fixtures.

MelodiaCore is the sole shipping runtime authority. Nothing in this module may own
live phases, saves, entitlements, callbacks, or Unreal generation.

Adds:
- Floor/dungeon generation with room templates
- Random encounter pools
- Meta-progression via Blessings (permanent upgrades)
- Artifact system (temporary mid-run upgrades)
- Ascension bosses
- Run state management
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from gmm.game.player_state import MelodiaPlayerState


# =============================================================================
# Floor Generation
# =============================================================================

@dataclass
class RoomTemplate:
    """Room layout template for procedural floors."""
    room_id: str
    display_name: str
    enemy_pool: list[str]  # Enemy IDs that can spawn here
    token_shrine_chance: float = 0.3  # Chance for token shrine room
    is_boss_room: bool = False
    is_shop_room: bool = False
    is_treasure_room: bool = False

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "display_name": self.display_name,
            "enemy_pool": self.enemy_pool,
            "token_shrine_chance": self.token_shrine_chance,
            "is_boss_room": self.is_boss_room,
            "is_shop_room": self.is_shop_room,
            "is_treasure_room": self.is_treasure_room,
        }


# Room templates - defining encounter variety
# Generated Slime variants added to pools (Ollama/Qwen content)
# Source: Imports/Data/EnemyVariants/ - 48 variants across 7 elements
ROOM_TEMPLATES: dict[str, RoomTemplate] = {
    "start": RoomTemplate(
        room_id="start",
        display_name="Melodia Grove",
        enemy_pool=["CrystalShard", "SakuraPhantom"],
    ),
    "standard": RoomTemplate(
        room_id="standard",
        display_name="Whispering Grove",
        # Original enemies + Generated Slime variants (Common/Lesser tiers)
        enemy_pool=[
            "CrystalShard", "StoneGolem", "VoidWraith", "SakuraPhantom", "StormFalcon",
            # Forte Slimes (Common/Lesser)
            "SlimeForteFestivo", "SlimeForteFugue", "SlimeFortePresto", "SlimeForteRondo",
            # Gale Slimes (Common/Lesser)
            "SlimeGaleBurst", "SlimeGaleTroupe", "SlimeGaleWhirl",
            # Stone Slimes (Common/Lesser)
            "SlimeStoneBulwark", "SlimeStonemaw", "SlimeStoneStalwart",
            # Radiant Slimes (Common/Lesser)
            "SlimeRadiantHarmony", "SlimeRadianceSpark", "SlimeRadiantSparkle",
            # Umbral Slimes (Common/Lesser)
            "SlimeUmbralHarmony", "SlimeUmbralFugue", "SlimeUmbralMishmash",
            # Arcane Slimes (Common/Lesser)
            "SlimeMelodicHarmony", "SlimeStarfall", "SlimeSorcererSweep",
            # Tide Slimes (Common/Lesser)
            "SlimeTideChord", "SlimeTideCurrent", "SlimeTideSurge",
        ],
    ),
    "elite": RoomTemplate(
        room_id="elite",
        display_name="Everburning Clearing",
        # Original enemies + Elite-tier Slimes (Greater/Crowned tiers)
        enemy_pool=[
            "FireDrake", "ShadowWraith", "ArcaneGolem", "AbyssalKraken",
            # Forte Greater/Crowned
            "SlimeMelodicStorm", "SlimeFortePhenomenon", "SlimeForteFestivo",
            # Gale Greater/Crowned
            "SlimeGaleToccata", "SlimeGaleHarbinger", "SlimeGaleHarmonia",
            # Stone Greater/Crowned
            "SlimeStonetide", "SlimeStonemaul", "SlimeStoneBrawler",
            # Radiant Greater/Crowned
            "SlimeRadianceDuet", "SlimeRadianceWaltz",
            # Umbral Greater/Crowned
            "SlimeUmbralHarbinger", "SlimeShadowWaltz",
            # Arcane Greater/Crowned
            "SlimeMelodrone", "SlimeForteTide",
            # Tide Greater/Crowned
            "SlimeTidalWave", "SlimeTidalHarmony", "SlimeFurvor",
        ],
    ),
    "boss": RoomTemplate(
        room_id="boss",
        display_name="Boss Arena",
        enemy_pool=["TitanPrime", "HarmonyVoid"],
        is_boss_room=True,
    ),
    "shop": RoomTemplate(
        room_id="shop",
        display_name="Token Shrine",
        enemy_pool=[],
        is_shop_room=True,
    ),
    "treasure": RoomTemplate(
        room_id="treasure",
        display_name="Abandoned Cache",
        enemy_pool=["FireDrake", "StoneGolem"],
        is_treasure_room=True,
    ),
}


# =============================================================================
# Artifact System (Mid-run temporary upgrades)
# =============================================================================

@dataclass
class Artifact:
    """Temporary upgrade found during a run."""
    artifact_id: str
    display_name: str
    description: str
    modifier_id: str  # References gmm.game.modifiers registry
    cost_golden_tokens: int = 0  # Cost at shop

    def to_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "display_name": self.display_name,
            "description": self.description,
            "modifier_id": self.modifier_id,
            "cost_golden_tokens": self.cost_golden_tokens,
        }


ARTIFACTS: dict[str, Artifact] = {
    "BurningChord": Artifact(
        artifact_id="BurningChord",
        display_name="Burning Chord",
        description="Skills deal +50% damage but cost +1 SP",
        modifier_id="ResonantFocus",
        cost_golden_tokens=3,
    ),
    "EchoingBeat": Artifact(
        artifact_id="EchoingBeat",
        display_name="Echoing Beat",
        description="Perfect timing grants bonus damage",
        modifier_id="Crescendo_Minor",
        cost_golden_tokens=2,
    ),
    "SwiftTempo": Artifact(
        artifact_id="SwiftTempo",
        display_name="Swift Tempo",
        description="+20% speed for this run",
        modifier_id="HasteDance",
        cost_golden_tokens=4,
    ),
    "StoneCarapace": Artifact(
        artifact_id="StoneCarapace",
        display_name="Stone Carapace",
        description="Take 20% less damage",
        modifier_id="GuardHymn",
        cost_golden_tokens=3,
    ),
}


# =============================================================================
# Blessing System (Permanent meta-upgrades)
# =============================================================================

@dataclass
class Blessing:
    """Permanent upgrade unlocked with collected tokens."""
    blessing_id: str
    display_name: str
    description: str
    token_cost: int  # How many golden tokens to unlock
    effect_type: str  # "starting_mana", "max_sp", "element_unlock", "passive"
    effect_value: float = 0.0
    effect_str: str = ""  # Optional string parameter (element name)

    def to_dict(self) -> dict:
        return {
            "blessing_id": self.blessing_id,
            "display_name": self.display_name,
            "description": self.description,
            "token_cost": self.token_cost,
            "effect_type": self.effect_type,
            "effect_value": self.effect_value,
            "effect_str": self.effect_str,
        }


BLESSINGS: dict[str, Blessing] = {
    "DeepenedResonance": Blessing(
        blessing_id="DeepenedResonance",
        display_name="Deepened Resonance",
        description="Start each run with 75 mana instead of 50",
        token_cost=50,
        effect_type="starting_mana",
        effect_value=75.0,
    ),
    "ExpandedHarmony": Blessing(
        blessing_id="ExpandedHarmony",
        display_name="Expanded Harmony",
        description="Maximum SP increased to 7",
        token_cost=100,
        effect_type="max_sp",
        effect_value=7.0,
    ),
    "EmberGift": Blessing(
        blessing_id="EmberGift",
        display_name="Ember Gift",
        description="Unlock Forte element affinity",
        token_cost=25,
        effect_type="element_unlock",
        effect_str="Forte",
    ),
    "TidalGift": Blessing(
        blessing_id="TidalGift",
        display_name="Tidal Gift",
        description="Unlock Tide element affinity",
        token_cost=25,
        effect_type="element_unlock",
        effect_str="Tide",
    ),
    "RhythmMaster": Blessing(
        blessing_id="RhythmMaster",
        display_name="Rhythm Master",
        description="Perfect timing window extended by 10ms",
        token_cost=75,
        effect_type="perfect_window_bonus",
        effect_value=10.0,
    ),
    "ComboKeeper": Blessing(
        blessing_id="ComboKeeper",
        display_name="Combo Keeper",
        description="Combo persists between battles in same act",
        token_cost=150,
        effect_type="combo_persistence",
    ),
    # Generated Room Modifier Blessings (Ollama/Qwen) - EXTENDS existing
    "RoomMod_ModHarmonyMire": Blessing(
        blessing_id="RoomMod_ModHarmonyMire",
        display_name="Melodic Fortitude",
        description="HP +10% for every perfect note",
        token_cost=50,
        effect_type="starting_mana",
        effect_value=10.0,
        effect_str="",
    ),
    "RoomMod_ModMelodicFate": Blessing(
        blessing_id="RoomMod_ModMelodicFate",
        display_name="Harmonic Guardian",
        description="Boosts your ultimate gauge by 5%",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_ModMelodicHarmony": Blessing(
        blessing_id="RoomMod_ModMelodicHarmony",
        display_name="Melodic Fortitude",
        description="Increase HP by 10%",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_ModMelodicLabyrinth": Blessing(
        blessing_id="RoomMod_ModMelodicLabyrinth",
        display_name="Harmonic Boost",
        description="Rhythm timing window +20% for 10 turns.",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_ModMelodicMire": Blessing(
        blessing_id="RoomMod_ModMelodicMire",
        display_name="Harmonic Haven",
        description="HP +10% for each piece of sheet music found.",
        token_cost=50,
        effect_type="starting_mana",
        effect_value=10.0,
        effect_str="",
    ),
    "RoomMod_ModMelodicPuzzle": Blessing(
        blessing_id="RoomMod_ModMelodicPuzzle",
        display_name="Harmonic Guardian",
        description="Reduces incoming damage by 10% while under rhythm timing window.",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_ModMelodicTune": Blessing(
        blessing_id="RoomMod_ModMelodicTune",
        display_name="Harmonious Heart",
        description="HP +10% when rhythm timing window is perfect.",
        token_cost=50,
        effect_type="starting_mana",
        effect_value=10.0,
        effect_str="",
    ),
    "RoomMod_ModMelodious": Blessing(
        blessing_id="RoomMod_ModMelodious",
        display_name="Harmonic Boost",
        description="Increases rhythm timing window by 10%",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_ModMelodiousLabyrinth": Blessing(
        blessing_id="RoomMod_ModMelodiousLabyrinth",
        display_name="Harmonic Heartbeat",
        description="Increases rhythm timing window by 5%.",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_ModMelodyMalediction": Blessing(
        blessing_id="RoomMod_ModMelodyMalediction",
        display_name="Harmonic Harmony",
        description="HP +10% within the next boss fight.",
        token_cost=50,
        effect_type="starting_mana",
        effect_value=10.0,
        effect_str="",
    ),
    "RoomMod_ModMelodyMaze": Blessing(
        blessing_id="RoomMod_ModMelodyMaze",
        display_name="Harmonic Heart",
        description="HP +10% for each perfect rhythm.",
        token_cost=50,
        effect_type="starting_mana",
        effect_value=10.0,
        effect_str="",
    ),
    "RoomMod_ModMelodyMist": Blessing(
        blessing_id="RoomMod_ModMelodyMist",
        display_name="Harmony Boost",
        description="Increases rhythm timing window by 10%",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_ModMidiMagic": Blessing(
        blessing_id="RoomMod_ModMidiMagic",
        display_name="Harmonic Harmony",
        description="Increase ultimate gauge by 10%.",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_ModMuseScore": Blessing(
        blessing_id="RoomMod_ModMuseScore",
        display_name="Melodic Harmony",
        description="Increases rhythm timing window by 10%",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_ModMusicalHarmony": Blessing(
        blessing_id="RoomMod_ModMusicalHarmony",
        display_name="Melodic Boost",
        description="Increase rhythm timing window by 10%",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_ModMusicNoteBlast": Blessing(
        blessing_id="RoomMod_ModMusicNoteBlast",
        display_name="Melodic Boost",
        description="HP +5% per note hit",
        token_cost=50,
        effect_type="starting_mana",
        effect_value=5.0,
        effect_str="",
    ),
    "RoomMod_ModMusicPulse": Blessing(
        blessing_id="RoomMod_ModMusicPulse",
        display_name="Melodic Fortitude",
        description="Increase toughness by 10%",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_ModMysticHarmony": Blessing(
        blessing_id="RoomMod_ModMysticHarmony",
        display_name="Melodic Fortitude",
        description="Increases HP by 10%",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_SheetMusicChamber": Blessing(
        blessing_id="RoomMod_SheetMusicChamber",
        display_name="Melodic Fortitude",
        description="HP +10% when within rhythm timing window",
        token_cost=50,
        effect_type="starting_mana",
        effect_value=10.0,
        effect_str="",
    ),
    "RoomMod_SheetMusicHarmony": Blessing(
        blessing_id="RoomMod_SheetMusicHarmony",
        display_name="Melodic Fortitude",
        description="Increase ultimate gauge by 10% for every perfect note.",
        token_cost=50,
        effect_type="passive",
        effect_value=0.0,
        effect_str="",
    ),
    "RoomMod_ModRhythmBlessing": Blessing(
        blessing_id="RoomMod_ModRhythmBlessing",
        display_name="Cadence Pulse",
        description="Perfect timing grants +15% rhythm window for 3 turns.",
        token_cost=50,
        effect_type="perfect_window_bonus",
        effect_value=15.0,
        effect_str="",
    ),
}


# =============================================================================
# Run State
# =============================================================================

@dataclass
class FloorState:
    """Current floor/progression state."""
    floor_number: int = 1
    act_number: int = 1
    rooms_cleared: int = 0
    rooms_since_boss: int = 0
    shop_rooms_entered: int = 0
    treasure_rooms_entered: int = 0

    def to_dict(self) -> dict:
        return {
            "floor_number": self.floor_number,
            "act_number": self.act_number,
            "rooms_cleared": self.rooms_cleared,
            "rooms_since_boss": self.rooms_since_boss,
            "shop_rooms_entered": self.shop_rooms_entered,
            "treasure_rooms_entered": self.treasure_rooms_entered,
        }


@dataclass
class RunState:
    """Complete state of a roguelike run."""
    current_floor: FloorState = field(default_factory=FloorState)
    player: MelodiaPlayerState = field(default_factory=MelodiaPlayerState)
    artifacts: list[str] = field(default_factory=list)  # Artifact IDs held
    ascension_level: int = 0  # For optional challenge scaling
    run_active: bool = False
    start_seed: int = 0

    def to_dict(self) -> dict:
        return {
            "current_floor": self.current_floor.to_dict(),
            "artifacts": self.artifacts,
            "ascension_level": self.ascension_level,
            "run_active": self.run_active,
            "start_seed": self.start_seed,
        }


# =============================================================================
# Floor Generation
# =============================================================================

def generate_floor(floor_number: int, seed: int | None = None) -> list[str]:
    """Generate a floor's room sequence.

    Returns list of room_ids for the floor.
    """
    if seed is not None:
        random.seed(seed + floor_number)

    rooms = []

    # Every 5th floor is a boss floor
    if floor_number % 5 == 0:
        rooms.append("boss")
    else:
        # Standard floor: 3-4 rooms
        room_count = random.randint(3, 4)
        for _ in range(room_count):
            # Chance for special rooms
            r = random.random()
            if r < 0.15:
                rooms.append("shop")
            elif r < 0.30:
                rooms.append("treasure")
            else:
                # Elite rooms more common on higher floors
                if floor_number >= 3 and random.random() < 0.3:
                    rooms.append("elite")
                else:
                    rooms.append("standard")

    return rooms


def select_random_enemy(room_id: str, seed: int | None = None) -> Optional[str]:
    """Get a random enemy from a room's pool."""
    template = ROOM_TEMPLATES.get(room_id)
    if not template or not template.enemy_pool:
        return None

    if seed is not None:
        random.seed(seed)

    return random.choice(template.enemy_pool)


def get_room_template(room_id: str) -> Optional[RoomTemplate]:
    """Get room template by ID."""
    return ROOM_TEMPLATES.get(room_id)


def get_artifact(artifact_id: str) -> Optional[Artifact]:
    """Get artifact by ID."""
    return ARTIFACTS.get(artifact_id)


def get_blessing(blessing_id: str) -> Optional[Blessing]:
    """Get blessing by ID."""
    return BLESSINGS.get(blessing_id)


def run_roguelike_summary() -> dict:
    """Get summary of roguelike systems."""
    return {
        "room_templates": len(ROOM_TEMPLATES),
        "artifacts": len(ARTIFACTS),
        "blessings": len(BLESSINGS),
        "room_ids": list(ROOM_TEMPLATES.keys()),
        "artifact_ids": list(ARTIFACTS.keys()),
        "blessing_ids": list(BLESSINGS.keys()),
    }