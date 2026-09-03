"""NPC Level Populator — spawns NPCs in level with AI controllers and interaction components.

Integrates with PCG for procedural placement and MelodiaCore for battle encounters.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any
import json
import random

try:
    import unreal
except ImportError:
    unreal = None


class NPCAIType(Enum):
    STATIONARY = "Stationary"       # Shop, quest giver
    PATROL = "Patrol"               # Walks a path
    WANDER = "Wander"               # Wanders in radius
    SCHEDULE = "Schedule"           # Time-based location changes
    EVENT = "Event"                 # Spawns for world events


@dataclass
class NPCSpawnPoint:
    """Single NPC spawn definition."""
    npc_id: str
    archetype: str
    location: tuple[float, float, float] = (0, 0, 0)
    rotation: tuple[float, float, float] = (0, 0, 0)
    ai_type: NPCAIType = NPCAIType.STATIONARY
    patrol_path: str = ""  # Actor name of spline/path
    wander_radius: float = 500.0
    schedule: dict = field(default_factory=dict)  # Time -> location mapping

    # Interaction
    interaction_type: str = "dialogue"  # dialogue, shop, battle, photo, quest
    interaction_data: dict = field(default_factory=dict)

    # Visual
    outfit_variant: str = "default"
    expression_override: str = ""

    # Runtime
    spawn_weight: float = 1.0
    min_level: int = 1
    max_level: int = 50


@dataclass
class ZonePopulation:
    """Population definition for a zone/level."""
    zone_name: str
    level_path: str
    npc_spawns: list[NPCSpawnPoint]
    max_concurrent: int = 20
    respawn_time: float = 300.0  # seconds


# ──────────────────────────────────────────────────────────────────────
# PREDEFINED POPULATIONS FOR TEST LEVEL
# ──────────────────────────────────────────────────────────────────────

def create_test_population(level_name: str = "L_PCGTest_Forest") -> ZonePopulation:
    """Create the 10 NPC pilot population for L_PCGTest_Forest."""

    # Define spawn points around the forest level
    spawns = [
        # Sakura Dreamers (4) - Near healing areas, shrines
        NPCSpawnPoint(
            npc_id="SD_01_SakuraMaiden",
            archetype="SakuraDreamer",
            location=(-1200, 800, 120),
            rotation=(0, 45, 0),
            ai_type=NPCAIType.STATIONARY,
            interaction_type="shop",
            interaction_data={"shop_type": "healing_items", "inventory": ["PetalTea", "SakuraSalve", "DreamDust"]},
            outfit_variant="default",
        ),
        NPCSpawnPoint(
            npc_id="SD_02_PetalPriestess",
            archetype="SakuraDreamer",
            location=(2500, -1500, 100),
            rotation=(0, -90, 0),
            ai_type=NPCAIType.PATROL,
            patrol_path="ShrinePatrolPath",
            interaction_type="dialogue",
            interaction_data={"dialogue_tree": "PetalPriestess_Intro", "quest_giver": True},
            outfit_variant="priestess",
        ),
        NPCSpawnPoint(
            npc_id="SD_03_BlossomGuide",
            archetype="SakuraDreamer",
            location=(-800, -2200, 80),
            rotation=(0, 180, 0),
            ai_type=NPCAIType.WANDER,
            wander_radius=800,
            interaction_type="dialogue",
            interaction_data={"dialogue_tree": "BlossomGuide_Paths", "tips": ["hidden_grove", "photo_spot"]},
            outfit_variant="guide",
        ),
        NPCSpawnPoint(
            npc_id="SD_04_FlowerMerchant",
            archetype="SakuraDreamer",
            location=(1800, 1900, 110),
            rotation=(0, -135, 0),
            ai_type=NPCAIType.STATIONARY,
            interaction_type="shop",
            interaction_data={"shop_type": "cosmetics", "inventory": ["PetalDye_Pink", "Ribbon_White", "FlowerCrown"]},
            outfit_variant="merchant",
        ),

        # Cosmic Weavers (3) - Near observatory, star-viewing spots
        NPCSpawnPoint(
            npc_id="CW_01_StarWeaver",
            archetype="CosmicWeaver",
            location=(3200, 2800, 200),
            rotation=(0, -45, 0),
            ai_type=NPCAIType.STATIONARY,
            interaction_type="battle",
            interaction_data={"battle_archetype": "CosmicWeaver_Battle", "difficulty": "normal", "rewards": ["StarlightThread", "ConstellationMap"]},
            outfit_variant="default",
        ),
        NPCSpawnPoint(
            npc_id="CW_02_VoidSeamstress",
            archetype="CosmicWeaver",
            location=(-2500, 3000, 150),
            rotation=(0, 90, 0),
            ai_type=NPCAIType.SCHEDULE,
            schedule={
                "06:00": (-2500, 3000, 150),  # Morning: observatory
                "18:00": (-1800, 2200, 100),  # Evening: garden
                "22:00": (-3000, 3500, 250),  # Night: high tower
            },
            interaction_type="dialogue",
            interaction_data={"dialogue_tree": "VoidSeamstress_Night", "time_sensitive": True},
            outfit_variant="seamstress",
        ),
        NPCSpawnPoint(
            npc_id="CW_03_AstralScribe",
            archetype="CosmicWeaver",
            location=(500, -3500, 90),
            rotation=(0, 0, 0),
            ai_type=NPCAIType.STATIONARY,
            interaction_type="quest",
            interaction_data={"quest_chain": "StarfallChronicles", "step": 1},
            outfit_variant="scribe",
        ),

        # Mirage Dancers (3) - Wind paths, open clearings
        NPCSpawnPoint(
            npc_id="MD_01_TwilightDancer",
            archetype="MirageDancer",
            location=(-3000, -500, 80),
            rotation=(0, 135, 0),
            ai_type=NPCAIType.WANDER,
            wander_radius=1200,
            interaction_type="photo",
            interaction_data={"pose_set": "TwilightDance", "photo_reward": "TwilightRibbon"},
            outfit_variant="dancer",
        ),
        NPCSpawnPoint(
            npc_id="MD_02_WindWalker",
            archetype="MirageDancer",
            location=(2800, -2800, 100),
            rotation=(0, -180, 0),
            ai_type=NPCAIType.PATROL,
            patrol_path="WindPath_Clearing",
            interaction_type="battle",
            interaction_data={"battle_archetype": "MirageDancer_Battle", "difficulty": "hard", "rewards": ["WindBell", "ZephyrStep"]},
            outfit_variant="walker",
        ),
        NPCSpawnPoint(
            npc_id="MD_03_ZephyrChampion",
            archetype="MirageDancer",
            location=(0, 0, 250),  # Center of forest - champion
            rotation=(0, 0, 0),
            ai_type=NPCAIType.EVENT,
            interaction_type="battle",
            interaction_data={
                "battle_archetype": "MirageDancer_Battle",
                "difficulty": "boss",
                "rewards": ["ChampionScarf", "ZephyrTitle", "MasterDancerPose"],
                "unlock_requirement": "defeat_2_mirage_dancers",
            },
            outfit_variant="champion",
        ),
    ]

    return ZonePopulation(
        zone_name="PCGTest_Forest",
        level_path=f"/Game/Levels/{level_name}",
        npc_spawns=spawns,
        max_concurrent=15,
        respawn_time=300.0,
    )


# ──────────────────────────────────────────────────────────────────────
# UNREAL SPAWNING FUNCTIONS
# ──────────────────────────────────────────────────────────────────────

def spawn_npc_in_level(spawn_point: NPCSpawnPoint, level_path: str) -> str | None:
    """Spawn a single NPC in the level. Returns actor path or None."""
    if unreal is None:
        return None

    try:
        # Load the NPC Blueprint (generated by pipeline)
        bp_path = f"/Game/NPCs/Blueprints/BP_NPC_{spawn_point.npc_id}"
        bp_class = unreal.EditorAssetLibrary.load_asset(bp_path)
        if not bp_class:
            unreal.log_warning(f"NPC Blueprint not found: {bp_path}")
            return None

        # Spawn actor
        world = unreal.EditorLevelLibrary.get_editor_world()
        if not world:
            unreal.log_error("No editor world")
            return None

        transform = unreal.Transform(
            location=unreal.Vector(*spawn_point.location),
            rotation=unreal.Rotator(*spawn_point.rotation),
            scale=unreal.Vector(1, 1, 1)
        )

        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            bp_class.generated_class(),
            transform.location,
            transform.rotation
        )

        if not actor:
            return None

        # Configure NPC
        _configure_npc_actor(actor, spawn_point)

        # Set label
        actor.set_actor_label(f"NPC_{spawn_point.npc_id}")

        unreal.log(f"Spawned NPC: {spawn_point.npc_id} at {spawn_point.location}")
        return actor.get_path_name()

    except Exception as e:
        unreal.log_error(f"Failed to spawn {spawn_point.npc_id}: {e}")
        return None


def _configure_npc_actor(actor, spawn_point: NPCSpawnPoint):
    """Configure spawned NPC actor with AI and interaction."""
    # Set AI type
    if hasattr(actor, "set_ai_type"):
        actor.set_ai_type(spawn_point.ai_type.value)

    # Configure patrol/wander
    if spawn_point.ai_type == NPCAIType.PATROL and spawn_point.patrol_path:
        if hasattr(actor, "set_patrol_path"):
            path_actor = unreal.EditorLevelLibrary.find_actor_by_name(spawn_point.patrol_path)
            if path_actor:
                actor.set_patrol_path(path_actor)

    elif spawn_point.ai_type == NPCAIType.WANDER:
        if hasattr(actor, "set_wander_radius"):
            actor.set_wander_radius(spawn_point.wander_radius)

    elif spawn_point.ai_type == NPCAIType.SCHEDULE:
        if hasattr(actor, "set_schedule"):
            actor.set_schedule(spawn_point.schedule)

    # Configure interaction
    if hasattr(actor, "set_interaction"):
        actor.set_interaction(spawn_point.interaction_type, spawn_point.interaction_data)

    # Apply outfit variant
    if spawn_point.outfit_variant != "default" and hasattr(actor, "apply_outfit_variant"):
        actor.apply_outfit_variant(spawn_point.outfit_variant)

    # Set expression
    if spawn_point.expression_override and hasattr(actor, "set_facial_expression"):
        actor.set_facial_expression(spawn_point.expression_override)

    # Melodia battle component
    if spawn_point.interaction_type == "battle" and hasattr(actor, "melodia_battle_component"):
        battle_comp = actor.melodia_battle_component
        battle_comp.enemy_id = spawn_point.interaction_data.get("battle_archetype", "")
        battle_comp.difficulty = spawn_point.interaction_data.get("difficulty", "normal")


def populate_zone(zone: ZonePopulation) -> dict:
    """Populate a zone with all its NPCs."""
    if unreal is None:
        return {"error": "Not in Unreal environment"}

    # Load level
    unreal.EditorLevelLibrary.load_level(zone.level_path)

    results = {
        "zone": zone.zone_name,
        "level": zone.level_path,
        "spawned": [],
        "failed": [],
    }

    for spawn in zone.npc_spawns:
        actor_path = spawn_npc_in_level(spawn, zone.level_path)
        if actor_path:
            results["spawned"].append({
                "npc_id": spawn.npc_id,
                "actor": actor_path,
                "location": spawn.location,
            })
        else:
            results["failed"].append(spawn.npc_id)

    # Save level
    unreal.EditorLevelLibrary.save_current_level()

    return results


def export_population_json(zone: ZonePopulation, output_path: Path = None) -> str:
    """Export population data as JSON for runtime loading."""
    if output_path is None:
        output_path = Path(__file__).parent / f"population_{zone.zone_name}.json"

    data = {
        "zone_name": zone.zone_name,
        "level_path": zone.level_path,
        "max_concurrent": zone.max_concurrent,
        "respawn_time": zone.respawn_time,
        "npc_spawns": [asdict(sp) for sp in zone.npc_spawns],
    }

    # Convert enums
    for sp in data["npc_spawns"]:
        sp["ai_type"] = sp["ai_type"].value if isinstance(sp["ai_type"], Enum) else sp["ai_type"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return str(output_path)


if __name__ == "__main__":
    # Generate test population
    zone = create_test_population()

    if unreal:
        results = populate_zone(zone)
        print(json.dumps(results, indent=2))
    else:
        # Export JSON for reference
        path = export_population_json(zone)
        print(f"Exported population: {path}")
        print(f"NPCs: {len(zone.npc_spawns)}")
        for sp in zone.npc_spawns:
            print(f"  {sp.npc_id} ({sp.archetype}) - {sp.ai_type.value} - {sp.interaction_type}")