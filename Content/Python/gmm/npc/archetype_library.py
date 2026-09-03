"""NPC Archetype Library — defines the 3 archetypes with all NPC data for generation.

This is the single source of truth for NPC archetype definitions.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any
import json


class NPCRole(Enum):
    SUPPORT = "Support"
    CONTROLLER = "Controller"
    DPS = "DPS"
    SOCIAL = "Social"


class Element(Enum):
    FORTE = "Forte"
    TIDE = "Tide"
    GALE = "Gale"
    STONE = "Stone"
    RADIANT = "Radiant"
    UMBRAL = "Umbral"
    ARCANE = "Arcane"


@dataclass
class OutfitPiece:
    """Single outfit piece with cloth simulation config."""
    slot_name: str
    display_name: str
    skeletal_mesh: str  # Relative path from /Game/NPCs/Outfits/
    material_slot: str  # Material slot name on base body
    cloth_config: dict = field(default_factory=dict)  # Mobile/PC configs

    # Compatibility
    compatible_archetypes: list[str] = field(default_factory=list)
    required_by_archetype: list[str] = field(default_factory=list)


@dataclass
class AnimationPersonality:
    """Animation personality for an archetype."""
    idle_set: str
    walk_style: str
    run_style: str
    interaction_gestures: list[str]
    facial_expressions: list[str]
    spring_bone_groups: list[str]  # Hair, skirt, accessories


@dataclass
class ArchetypeDefinition:
    """Complete archetype definition."""
    id: str
    display_name: str
    description: str
    role: NPCRole
    element: Element
    count: int
    bpm: float

    # Visual
    palette_name: str
    body_types: list[str]
    outfit_pieces: list[str]  # Required pieces for this archetype
    optional_accessories: list[str] = field(default_factory=list)

    # Animation
    animation_personality: AnimationPersonality = None

    # Battle (only for battle-capable archetypes)
    battle_archetype_id: str = ""
    enemy_def_overrides: dict = field(default_factory=dict)

    # Spawning
    spawn_zones: list[str] = field(default_factory=list)
    schedule: dict = field(default_factory=dict)  # Time of day, weather, etc.

    # Progression
    affinity_rewards: dict = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────
# OUTFIT PIECE DEFINITIONS
# ──────────────────────────────────────────────────────────────────────

OUTFIT_PIECES = {
    # Sakura Dreamer pieces
    "kimono_sleeve_top": OutfitPiece(
        slot_name="Torso",
        display_name="Kimono Sleeve Top",
        skeletal_mesh="SakuraDreamer/SK_KimonoSleeveTop",
        material_slot="Torso",
        cloth_config={
            "mobile": {"enabled": False, "baked_anim": True},
            "pc": {"enabled": True, "solver": "Chaos", "iterations": 8},
        },
        compatible_archetypes=["SakuraDreamer"],
        required_by_archetype=["SakuraDreamer"],
    ),
    "hakama_skirt": OutfitPiece(
        slot_name="Legs",
        display_name="Hakama Skirt",
        skeletal_mesh="SakuraDreamer/SK_HakamaSkirt",
        material_slot="Legs",
        cloth_config={
            "mobile": {"enabled": True, "solver": "DistanceConstraint", "chains": 2, "iterations": 4},
            "pc": {"enabled": True, "solver": "Chaos", "iterations": 12, "self_collision": True},
        },
        compatible_archetypes=["SakuraDreamer"],
        required_by_archetype=["SakuraDreamer"],
    ),
    "petal_hair_ribbon": OutfitPiece(
        slot_name="Head",
        display_name="Petal Hair Ribbon",
        skeletal_mesh="SakuraDreamer/SK_PetalHairRibbon",
        material_slot="Hair",
        cloth_config={
            "mobile": {"enabled": True, "solver": "VRMSpringBone", "stiffness": 0.8},
            "pc": {"enabled": True, "solver": "VRMSpringBone", "stiffness": 0.6},
        },
        compatible_archetypes=["SakuraDreamer"],
    ),
    "falling_petal_accessory": OutfitPiece(
        slot_name="Back",
        display_name="Falling Petal Accessory",
        skeletal_mesh="SakuraDreamer/SK_FallingPetalAccessory",
        material_slot="Back",
        cloth_config={"mobile": {"enabled": False}, "pc": {"enabled": True, "particle_system": True}},
        compatible_archetypes=["SakuraDreamer"],
    ),

    # Cosmic Weaver pieces
    "stellar_cape": OutfitPiece(
        slot_name="Back",
        display_name="Stellar Cape",
        skeletal_mesh="CosmicWeaver/SK_StellarCape",
        material_slot="Back",
        cloth_config={
            "mobile": {"enabled": True, "solver": "DistanceConstraint", "chains": 3, "iterations": 4},
            "pc": {"enabled": True, "solver": "Chaos", "iterations": 16, "wind_field": True},
        },
        compatible_archetypes=["CosmicWeaver"],
        required_by_archetype=["CosmicWeaver"],
    ),
    "constellation_corset": OutfitPiece(
        slot_name="Torso",
        display_name="Constellation Corset",
        skeletal_mesh="CosmicWeaver/SK_ConstellationCorset",
        material_slot="Torso",
        cloth_config={"mobile": {"enabled": False}, "pc": {"enabled": False}},
        compatible_archetypes=["CosmicWeaver"],
        required_by_archetype=["CosmicWeaver"],
    ),
    "orbital_hair_ornaments": OutfitPiece(
        slot_name="Head",
        display_name="Orbital Hair Ornaments",
        skeletal_mesh="CosmicWeaver/SK_OrbitalHairOrnaments",
        material_slot="Hair",
        cloth_config={
            "mobile": {"enabled": True, "solver": "VRMSpringBone", "stiffness": 0.9},
            "pc": {"enabled": True, "solver": "VRMSpringBone", "stiffness": 0.7},
        },
        compatible_archetypes=["CosmicWeaver"],
    ),
    "cosmic_gloves": OutfitPiece(
        slot_name="Arms",
        display_name="Cosmic Gloves",
        skeletal_mesh="CosmicWeaver/SK_CosmicGloves",
        material_slot="Arms",
        cloth_config={"mobile": {"enabled": False}, "pc": {"enabled": False}},
        compatible_archetypes=["CosmicWeaver"],
    ),

    # Mirage Dancer pieces
    "asymmetric_gradient_dress": OutfitPiece(
        slot_name="Torso",
        display_name="Asymmetric Gradient Dress",
        skeletal_mesh="MirageDancer/SK_AsymmetricGradientDress",
        material_slot="Torso",
        cloth_config={
            "mobile": {"enabled": True, "solver": "DistanceConstraint", "chains": 2, "iterations": 4},
            "pc": {"enabled": True, "solver": "Chaos", "iterations": 12},
        },
        compatible_archetypes=["MirageDancer"],
        required_by_archetype=["MirageDancer"],
    ),
    "wind_torn_scarf": OutfitPiece(
        slot_name="Neck",
        display_name="Wind-Torn Scarf",
        skeletal_mesh="MirageDancer/SK_WindTornScarf",
        material_slot="Neck",
        cloth_config={
            "mobile": {"enabled": True, "solver": "VRMSpringBone", "stiffness": 0.5},
            "pc": {"enabled": True, "solver": "Chaos", "iterations": 10, "wind_field": True},
        },
        compatible_archetypes=["MirageDancer"],
    ),
    "ankle_bells": OutfitPiece(
        slot_name="Feet",
        display_name="Ankle Bells",
        skeletal_mesh="MirageDancer/SK_AnkleBells",
        material_slot="Feet",
        cloth_config={"mobile": {"enabled": False}, "pc": {"enabled": False}},
        compatible_archetypes=["MirageDancer"],
    ),
    "trailing_ribbons": OutfitPiece(
        slot_name="Back",
        display_name="Trailing Ribbons",
        skeletal_mesh="MirageDancer/SK_TrailingRibbons",
        material_slot="Back",
        cloth_config={
            "mobile": {"enabled": True, "solver": "VRMSpringBone", "stiffness": 0.4, "chains": 4},
            "pc": {"enabled": True, "solver": "Chaos", "iterations": 14, "wind_field": True},
        },
        compatible_archetypes=["MirageDancer"],
    ),
}


# ──────────────────────────────────────────────────────────────────────
# ANIMATION PERSONALITIES
# ──────────────────────────────────────────────────────────────────────

ANIMATION_PERSONALITIES = {
    "SakuraDreamer": AnimationPersonality(
        idle_set="IDLE_GentleSway",
        walk_style="WALK_LightStep",
        run_style="RUN_GracefulGlide",
        interaction_gestures=["wave_gentle", "gesture_explain", "offer_item", "pose_photo", "blessing"],
        facial_expressions=["gentle_smile", "soft_laugh", "thoughtful", "dreamy", "serene", "curious"],
        spring_bone_groups=["hair", "ribbon", "petals", "sleeves"],
    ),
    "CosmicWeaver": AnimationPersonality(
        idle_set="IDLE_MysticalFloat",
        walk_style="WALK_PurposefulStride",
        run_style="RUN_StarlightTrail",
        interaction_gestures=["gesture_reading", "crystal_gaze", "weaving_motion", "star_point", "knowing_nod"],
        facial_expressions=["mystical", "knowing_smile", "contemplative", "stargazing", "focused", "gentle"],
        spring_bone_groups=["hair", "ornaments", "cape", "glove_trails"],
    ),
    "MirageDancer": AnimationPersonality(
        idle_set="IDLE_BreezyShift",
        walk_style="WALK_DanceStep",
        run_style="RUN_WindRider",
        interaction_gestures=["spin_flourish", "ribbon_wave", "confident_grin", "wind_swept_hair", "photo_pose_dynamic"],
        facial_expressions=["joyful", "determined", "wind_swept", "playful", "confident", "breezy_laugh"],
        spring_bone_groups=["hair", "scarf", "ribbons", "dress_hem", "bells"],
    ),
}


# ──────────────────────────────────────────────────────────────────────
# ARCHETYPE DEFINITIONS
# ──────────────────────────────────────────────────────────────────────

ARCHETYPES = {
    "SakuraDreamer": ArchetypeDefinition(
        id="SakuraDreamer",
        display_name="Sakura Dreamer",
        description="Floral support archetype — petal motifs, flowing sleeves, cherry blossom palette. Healer/buffer in battle.",
        role=NPCRole.SUPPORT,
        element=Element.RADIANT,
        count=4,
        bpm=128.0,
        palette_name="SakuraDreamer",
        body_types=["petite", "standard", "willowy"],
        outfit_pieces=["kimono_sleeve_top", "hakama_skirt", "petal_hair_ribbon"],
        optional_accessories=["falling_petal_accessory"],
        animation_personality=ANIMATION_PERSONALITIES["SakuraDreamer"],
        battle_archetype_id="Enemy_SakuraDreamer",
        enemy_def_overrides={
            "MaxHP": 140.0,
            "MaxToughness": 28.0,
            "BaseDamage": 10.0,
            "Speed": 85,
            "Element": "Radiant",
            "BPMOverride": 128.0,
            "MeshScale": 1.1,
        },
        spawn_zones=["SakuraGrove", "HealingShrine", "PetalPlaza", "DreamGarden"],
        schedule={"day": 0.7, "night": 0.3, "rain": 0.1, "clear": 0.9},
        affinity_rewards={
            1: "PetalHairRibbon_ColorVariant",
            3: "KimonoSleeve_PatternUnlock",
            5: "HakamaSkirt_GradientDye",
            10: "Exclusive_Pose_PetalDance",
        },
    ),

    "CosmicWeaver": ArchetypeDefinition(
        id="CosmicWeaver",
        display_name="Cosmic Weaver",
        description="Stellar controller archetype — star-field fabric, constellation jewelry, iridescent violet-blue. Buff/debuffer in battle.",
        role=NPCRole.CONTROLLER,
        element=Element.ARCANE,
        count=3,
        bpm=144.0,
        palette_name="CosmicWeaver",
        body_types=["tall", "willowy"],
        outfit_pieces=["stellar_cape", "constellation_corset", "orbital_hair_ornaments"],
        optional_accessories=["cosmic_gloves"],
        animation_personality=ANIMATION_PERSONALITIES["CosmicWeaver"],
        battle_archetype_id="Enemy_CosmicWeaver",
        enemy_def_overrides={
            "MaxHP": 200.0,
            "MaxToughness": 80.0,
            "BaseDamage": 12.0,
            "Speed": 70,
            "Element": "Arcane",
            "BPMOverride": 144.0,
            "MeshScale": 1.3,
        },
        spawn_zones=["StarObservatory", "CosmicLibrary", "VoidLoom", "AstralNexus"],
        schedule={"day": 0.3, "night": 0.9, "rain": 0.5, "clear": 0.8, "meteor_shower": 1.0},
        affinity_rewards={
            1: "OrbitalHairOrnament_ColorVariant",
            3: "StellarCape_StarDensity",
            5: "ConstellationCorset_PatternUnlock",
            10: "Exclusive_Pose_StarWeaving",
        },
    ),

    "MirageDancer": ArchetypeDefinition(
        id="MirageDancer",
        display_name="Mirage Dancer",
        description="Twilight evasion archetype — gradient fabrics, trailing ribbons, gold-accented aurora palette. High-mobility DPS in battle.",
        role=NPCRole.DPS,
        element=Element.GALE,
        count=3,
        bpm=180.0,
        palette_name="MirageDancer",
        body_types=["willowy", "standard", "athletic"],
        outfit_pieces=["asymmetric_gradient_dress", "wind_torn_scarf", "ankle_bells"],
        optional_accessories=["trailing_ribbons"],
        animation_personality=ANIMATION_PERSONALITIES["MirageDancer"],
        battle_archetype_id="Enemy_MirageDancer",
        enemy_def_overrides={
            "MaxHP": 90.0,
            "MaxToughness": 30.0,
            "BaseDamage": 18.0,
            "Speed": 120,
            "Element": "Gale",
            "BPMOverride": 180.0,
            "MeshScale": 0.95,
        },
        spawn_zones=["TwilightDunes", "WindTemple", "MirageOasis", "ZephyrPeak"],
        schedule={"day": 0.6, "night": 0.8, "rain": 0.2, "clear": 1.0, "windy": 1.0},
        affinity_rewards={
            1: "AnkleBells_ToneVariant",
            3: "WindTornScarf_LengthVariant",
            5: "GradientDress_ColorShiftUnlock",
            10: "Exclusive_Pose_ZephyrDance",
        },
    ),
}


# ──────────────────────────────────────────────────────────────────────
# ENEMY DEFINITION GENERATOR
# ──────────────────────────────────────────────────────────────────────

def generate_enemy_definitions() -> dict[str, dict]:
    """Generate FMelodiaEnemyDef-compatible dicts for each battle archetype."""
    enemies = {}
    for arch_id, arch in ARCHETYPES.items():
        if arch.battle_archetype_id:
            base = {
                "EnemyId": arch.battle_archetype_id,
                "DisplayName": f"{arch.display_name} (Battle Form)",
                "MaxHP": arch.enemy_def_overrides.get("MaxHP", 150.0),
                "MaxToughness": arch.enemy_def_overrides.get("MaxToughness", 50.0),
                "BaseDamage": arch.enemy_def_overrides.get("BaseDamage", 15.0),
                "Speed": arch.enemy_def_overrides.get("Speed", 80),
                "Element": arch.enemy_def_overrides.get("Element", "Forte"),
                "BPMOverride": arch.enemy_def_overrides.get("BPMOverride", 120.0),
                "MeshScale": arch.enemy_def_overrides.get("MeshScale", 1.0),
            }
            enemies[arch.battle_archetype_id] = base
    return enemies


def export_archetype_library(output_path: Path = None) -> str:
    """Export archetype library as JSON for pipeline consumption."""
    if output_path is None:
        output_path = Path(__file__).parent / "archetype_library.json"

    data = {
        "archetypes": {},
        "outfit_pieces": {},
        "enemy_definitions": generate_enemy_definitions(),
    }

    for arch_id, arch in ARCHETYPES.items():
        data["archetypes"][arch_id] = {
            "id": arch.id,
            "display_name": arch.display_name,
            "description": arch.description,
            "role": arch.role.value,
            "element": arch.element.value,
            "count": arch.count,
            "bpm": arch.bpm,
            "palette_name": arch.palette_name,
            "body_types": arch.body_types,
            "outfit_pieces": arch.outfit_pieces,
            "optional_accessories": arch.optional_accessories,
            "battle_archetype_id": arch.battle_archetype_id,
            "enemy_def_overrides": arch.enemy_def_overrides,
            "spawn_zones": arch.spawn_zones,
            "schedule": arch.schedule,
            "affinity_rewards": arch.affinity_rewards,
        }

    for piece_id, piece in OUTFIT_PIECES.items():
        data["outfit_pieces"][piece_id] = {
            "slot_name": piece.slot_name,
            "display_name": piece.display_name,
            "skeletal_mesh": piece.skeletal_mesh,
            "material_slot": piece.material_slot,
            "cloth_config": piece.cloth_config,
            "compatible_archetypes": piece.compatible_archetypes,
            "required_by_archetype": piece.required_by_archetype,
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return str(output_path)


def get_archetype(arch_id: str) -> ArchetypeDefinition | None:
    """Get archetype by ID."""
    return ARCHETYPES.get(arch_id)


def get_all_archetypes() -> list[ArchetypeDefinition]:
    """Get all archetypes."""
    return list(ARCHETYPES.values())


def get_total_npc_count() -> int:
    """Total NPCs across all archetypes."""
    return sum(a.count for a in ARCHETYPES.values())


if __name__ == "__main__":
    path = export_archetype_library()
    print(f"Exported archetype library to: {path}")
    print(f"Total NPCs: {get_total_npc_count()}")
    for arch in get_all_archetypes():
        print(f"  {arch.id}: {arch.count} NPCs ({arch.role.value}, {arch.element.value})")