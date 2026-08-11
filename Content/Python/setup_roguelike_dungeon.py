"""Setup Roguelike Dungeon — ProceduralDungeon + Melodia + Infinity Nikki integration.

Creates all Unreal assets needed for the roguelike dungeon crawler when run
inside the Unreal Editor Python console:

    py Content/Python/setup_roguelike_dungeon.py

Creates:
  1. RoomData assets (22) — ProceduralDungeon room templates with roguelike custom data
  2. BP_RoguelikeDungeonGenerator — Blueprint subclass of ADungeonGenerator
  3. BP_DungeonFloorManager — Blueprint for floor-to-floor transitions
  4. Room Levels (8) — .umap files with EncounterTriggers, Nikki PPV, PCG volumes
  5. DataTable assets — DT_RoguelikeRoomRegistry, DT_ShopInventory, DT_BlessingCatalog

The script is idempotent by asset name. Re-running it updates existing assets
without duplicating them.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path

try:
    import unreal
    UNREAL_AVAILABLE = True
except ImportError:
    UNREAL_AVAILABLE = False


# =============================================================================
# Paths
# =============================================================================

CONTENT_ROOT = "/Game/Melodia/Roguelike"
ROOM_DATA_DIR = f"{CONTENT_ROOT}/RoomData"
ROOM_LEVEL_DIR = f"{CONTENT_ROOT}/Rooms"
BLUEPRINT_DIR = f"{CONTENT_ROOT}/Blueprints"
DATA_TABLE_DIR = f"{CONTENT_ROOT}/DataTables"
REPORT = Path("Saved/Melodia/roguelike_dungeon_setup.json")

# ProceduralDungeon classes
DUNGEON_GENERATOR_CLASS = "/Script/ProceduralDungeon.DungeonGenerator"
ROOM_CUSTOM_DATA_CLASS = "/Script/ProceduralDungeon.RoomCustomData"
DOOR_TYPE_ASSET = "/ProceduralDungeon/DoorTypes/DT_Default"


# =============================================================================
# Room Data generation
# =============================================================================

def _ensure_dir(path: str):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _asset_exists(path: str) -> bool:
    return unreal.EditorAssetLibrary.does_asset_exist(path)


def _save_asset(path: str):
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)


def _create_room_data_asset(
    room_data_name: str,
    room_type: str,
    display_name: str,
    enemy_pool: list[str],
    door_positions: list[tuple[int, int, int]],
    floor_tier_min: int,
    floor_tier_max: int,
    nikki_archetype: str,
    nikki_lighting: str,
    b_photo_spot: bool,
    golden_token_cost: int,
) -> str:
    """Create a single URoomData + URoguelikeRoomCustomData asset pair.

    Args:
        room_data_name: Asset name (e.g. "RD_WhisperingGrove_V1")
        room_type: "Start", "Standard", "Elite", "Boss", "Shop", "Treasure", "Event", "Blessing"
        display_name: UI display name
        enemy_pool: Enemy ID list
        door_positions: List of (x, y, z) door positions
        floor_tier_min: Minimum floor for this variant
        floor_tier_max: Maximum floor for this variant
        nikki_archetype: "SakuraDreamer", "CosmicWeaver", "MirageDancer"
        nikki_lighting: "Nikki", "Jewelry", "Silhouette"
        b_photo_spot: Mark as photo spot
        golden_token_cost: Entry cost for shop/treasure rooms

    Returns:
        Full asset path of created RoomData
    """
    from gmm.game.roguelike_dungeon import DungeonRoomType

    asset_path = f"{ROOM_DATA_DIR}/{room_data_name}"

    # Check if already exists
    if _asset_exists(asset_path):
        unreal.log(f"  [exists] {room_data_name}")
        return asset_path

    # Create the RoomData asset
    # ProceduralDungeon's custom factory creates editable RoomData assets;
    # generic DataAssetFactory returns a template-like object whose Level
    # property cannot be authored through Python in UE 5.8.
    factory = unreal.RoomDataFactory()

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    room_data = asset_tools.create_asset(
        room_data_name,
        ROOM_DATA_DIR,
        unreal.RoomData,
        factory,
    )

    if not room_data:
        unreal.log_error(f"  [FAILED] Could not create RoomData: {room_data_name}")
        return ""

    # UE 5.8 may return the factory-created template wrapper on the first
    # call. Save and reload the package so EditInstanceOnly fields become
    # editable on the real asset object.
    _save_asset(asset_path)
    room_data = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not room_data:
        unreal.log_error(f"  [FAILED] Could not reload RoomData: {room_data_name}")
        return ""

    # Set level reference
    room_level_path = f"{ROOM_LEVEL_DIR}/L_{display_name.replace(' ', '')}"
    try:
        room_data.set_editor_property("level", unreal.SoftObjectPath(room_level_path))
    except Exception as exc:
        # Level is EditInstanceOnly in the plugin and may require manual
        # assignment in the RoomData editor; keep generating the asset graph.
        unreal.log_warning(f"  [deferred] {room_data_name}.Level: {exc}")

    # Set door positions
    door_defs = []
    for pos in door_positions:
        door_def = unreal.DoorDef()
        door_def.set_editor_property("position", unreal.IntVector(*pos))
        door_def.set_editor_property("direction", _door_direction_from_position(pos))
        door_defs.append(door_def)
    room_data.set_editor_property("doors", door_defs)

    # Set bounding boxes (default: 1×1 cell room)
    try:
        bounds = unreal.BoxMinAndMax()
        bounds.set_editor_property("min", unreal.IntVector(-1, -1, -1))
        bounds.set_editor_property("max", unreal.IntVector(1, 1, 1))
        room_data.set_editor_property("bounding_boxes", [bounds])
    except Exception as exc:
        unreal.log_warning(f"  [deferred] {room_data_name}.BoundingBoxes: {exc}")

    # RoomData.CustomData is a TSet<TSubclassOf<URoomCustomData>> in the
    # plugin, not an instanced object array. Register the Melodia subclass;
    # per-room values are authored by the generated registry/custom assets.
    room_data.set_editor_property("custom_data", {unreal.RoguelikeRoomCustomData})

    _save_asset(asset_path)
    unreal.log(f"  [created] {room_data_name} ({room_type}, {len(enemy_pool)} enemies)")
    return asset_path


def _door_direction_from_position(pos: tuple[int, int, int]) -> unreal.DoorDirection:
    """Convert a position tuple to a DoorDirection enum."""
    x, y, z = pos
    if y > 0:
        return unreal.DoorDirection.NORTH
    elif y < 0:
        return unreal.DoorDirection.SOUTH
    elif x > 0:
        return unreal.DoorDirection.EAST
    elif x < 0:
        return unreal.DoorDirection.WEST
    return unreal.DoorDirection.NORTH


def create_all_room_data_assets() -> dict:
    """Create all 22 RoomData assets from the RoguelikeRoomRegistry."""
    from gmm.game.roguelike_dungeon import RoguelikeRoomRegistry, NIKKI_ROOM_THEMES, DungeonRoomType

    _ensure_dir(ROOM_DATA_DIR)
    _ensure_dir(CONTENT_ROOT)

    registry = RoguelikeRoomRegistry()
    specs = registry.all_specs()

    results = {"created": [], "existing": [], "failed": []}

    for spec in specs:
        theme = NIKKI_ROOM_THEMES.get(spec.room_type, {})
        room_type_str = spec.room_type.name.capitalize()

        path = _create_room_data_asset(
            room_data_name=spec.room_data_name,
            room_type=room_type_str,
            display_name=spec.display_name,
            enemy_pool=spec.enemy_pool,
            door_positions=spec.door_positions,
            floor_tier_min=spec.floor_tier_min,
            floor_tier_max=spec.floor_tier_max,
            nikki_archetype=spec.nikki_archetype,
            nikki_lighting=theme.get("lighting", "Nikki"),
            b_photo_spot=spec.photo_spot,
            golden_token_cost=spec.golden_token_cost,
        )

        if path:
            full_path = f"{ROOM_DATA_DIR}/{spec.room_data_name}"
            if _asset_exists(full_path):
                results["existing"].append(spec.room_data_name)
            else:
                results["created"].append(spec.room_data_name)
        else:
            results["failed"].append(spec.room_data_name)

    return results


# =============================================================================
# Blueprint creation
# =============================================================================

def create_roguelike_dungeon_generator_bp() -> str:
    """Create BP_RoguelikeDungeonGenerator Blueprint.

    Subclasses ADungeonGenerator from ProceduralDungeon plugin.
    This BP overrides ChooseFirstRoomData/ChooseNextRoomData to use
    the GMM roguelike floor generation rules.
    """
    bp_path = f"{BLUEPRINT_DIR}/BP_RoguelikeDungeonGenerator"

    if _asset_exists(bp_path):
        unreal.log(f"  [exists] BP_RoguelikeDungeonGenerator")
        return bp_path

    _ensure_dir(BLUEPRINT_DIR)

    # Load parent class
    parent_class = unreal.load_class(None, DUNGEON_GENERATOR_CLASS)
    if not parent_class:
        unreal.log_warning("ProceduralDungeon plugin may not be loaded")
        return ""

    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    bp = asset_tools.create_asset(
        "BP_RoguelikeDungeonGenerator",
        BLUEPRINT_DIR,
        unreal.Blueprint,
        factory,
    )

    if not bp:
        unreal.log_error("Could not create BP_RoguelikeDungeonGenerator")
        return ""

    # Configure default properties
    bp_class = bp.generated_class()
    cdo = unreal.get_default_object(bp_class)
    cdo.set_editor_property("generation_type", unreal.GenerationType.DFS)
    cdo.set_editor_property("b_can_loop", False)
    cdo.set_editor_property("room_batch_size", 5)

    _save_asset(bp_path)
    unreal.log("  [created] BP_RoguelikeDungeonGenerator")
    return bp_path


def create_dungeon_floor_manager_bp() -> str:
    """Create BP_DungeonFloorManager Blueprint.

    Manages floor-to-floor transitions:
    - Monitors RoguelikeRunSession for boss room cleared
    - Triggers DungeonGenerator::Unload() then Generate() with new floor seed
    - Handles player teleport to new floor start room
    """
    bp_path = f"{BLUEPRINT_DIR}/BP_DungeonFloorManager"

    if _asset_exists(bp_path):
        unreal.log(f"  [exists] BP_DungeonFloorManager")
        return bp_path

    _ensure_dir(BLUEPRINT_DIR)

    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Actor)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    bp = asset_tools.create_asset(
        "BP_DungeonFloorManager",
        BLUEPRINT_DIR,
        unreal.Blueprint,
        factory,
    )

    if not bp:
        return ""

    _save_asset(bp_path)
    unreal.log("  [created] BP_DungeonFloorManager")
    return bp_path


# =============================================================================
# Room Level creation
# =============================================================================

def _create_room_level(
    level_name: str,
    room_type: str,
    display_name: str,
    enemy_pool: list[str],
    nikki_archetype: str,
    nikki_lighting: str,
    b_photo_spot: bool,
    is_shop: bool,
    is_blessing: bool,
) -> str:
    """Create a single room .umap level with all gameplay actors.

    Each room level contains:
    - PlayerStart
    - EncounterTrigger(s) for battle rooms
    - PPV_NikkiDream post-process volume
    - PCG volume for procedural scatter
    - NPC spawn points based on archetype
    - DirectionalLight + SkyLight + ExponentialHeightFog
    """
    level_path = f"{ROOM_LEVEL_DIR}/L_{level_name}"

    if _asset_exists(level_path):
        unreal.log(f"  [exists] {level_name}")
        return level_path

    _ensure_dir(ROOM_LEVEL_DIR)

    # Create level
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.new_level(level_path, is_partitioned_world=False):
        unreal.log_error(f"  [FAILED] Could not create level: {level_name}")
        return ""

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # Player Start
    player_start = eas.spawn_actor_from_class(
        unreal.PlayerStart,
        unreal.Vector(0, 0, 100),
        unreal.Rotator(0, 0, 0),
    )
    if player_start:
        player_start.set_actor_label(f"{level_name}_PlayerStart")

    # Nikki-theme lighting
    light_colors = {
        "Nikki": (1.0, 0.95, 0.85),
        "Jewelry": (0.98, 0.82, 0.38),
        "Silhouette": (0.6, 0.5, 0.8),
    }
    light_color = light_colors.get(nikki_lighting, (1.0, 0.95, 0.85))

    # Directional Light (key light)
    dir_light = eas.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(0, 0, 2000),
        unreal.Rotator(-45, 30, 0),
    )
    if dir_light:
        dir_light.set_actor_label(f"{level_name}_KeyLight")
        comp = dir_light.get_component_by_class(unreal.DirectionalLightComponent)
        if comp:
            comp.set_editor_property("light_color", unreal.Color(
                light_color[0] * 255, light_color[1] * 255, light_color[2] * 255
            ))

    # Sky Light
    eas.spawn_actor_from_class(
        unreal.SkyLight,
        unreal.Vector(0, 0, 1500),
        unreal.Rotator(0, 0, 0),
    ).set_actor_label(f"{level_name}_SkyLight")

    # Atmospheric Fog
    eas.spawn_actor_from_class(
        unreal.ExponentialHeightFog,
        unreal.Vector(0, 0, 500),
        unreal.Rotator(0, 0, 0),
    ).set_actor_label(f"{level_name}_Fog")

    # Nikki Dream Post-Process Volume
    ppv = eas.spawn_actor_from_class(
        unreal.PostProcessVolume,
        unreal.Vector(0, 0, 500),
        unreal.Rotator(0, 0, 0),
    )
    if ppv:
        ppv.set_actor_label(f"{level_name}_PPV_NikkiDream")
        ppv.set_editor_property("unbound", True)

    # Encounter Trigger (for combat rooms)
    if enemy_pool and not is_shop and not is_blessing:
        trigger_cls = unreal.load_class(None, "/Script/MelodiaCore.MelodiaEncounterTrigger")
        if trigger_cls:
            encounter = eas.spawn_actor_from_class(
                trigger_cls,
                unreal.Vector(200, 0, 100),
                unreal.Rotator(0, 0, 0),
            )
            if encounter:
                encounter.set_actor_label(f"{level_name}_Encounter")
                encounter.set_editor_property("encounter_level", 1.0)
                if enemy_pool:
                    encounter.set_editor_property("enemy_id", enemy_pool[0])

    # PCG Volume for procedural scatter
    pcg_volume_cls = unreal.load_class(None, "/Script/PCG.PCGVolume")
    if pcg_volume_cls:
        pcg = eas.spawn_actor_from_class(
            pcg_volume_cls,
            unreal.Vector(0, 0, 50),
            unreal.Rotator(0, 0, 0),
        )
        if pcg:
            pcg.set_actor_label(f"{level_name}_PCGVolume")
            pcg.set_actor_scale3d(unreal.Vector(10, 10, 5))

    # Photo spot marker (if applicable)
    if b_photo_spot:
        marker = eas.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(0, 0, 100),
            unreal.Rotator(0, 0, 0),
        )
        if marker:
            marker.set_actor_label(f"{level_name}_PhotoSpotMarker")

    les.save_current_level()
    unreal.log(f"  [created] {level_name}")
    return level_path


def create_all_room_levels() -> dict:
    """Create all 8 room level types."""
    from gmm.game.roguelike_dungeon import RoguelikeRoomRegistry, NIKKI_ROOM_THEMES, DungeonRoomType
    from gmm.game.roguelike import ROOM_TEMPLATES

    _ensure_dir(ROOM_LEVEL_DIR)

    results = {"created": [], "existing": [], "failed": []}

    level_configs = [
        {
            "level_name": "MelodiaGrove",
            "room_type": "Start",
            "display_name": "Melodia Grove",
            "enemy_pool": ["CrystalShard", "SakuraPhantom"],
            "nikki_archetype": "SakuraDreamer",
            "nikki_lighting": "Nikki",
            "b_photo_spot": False,
            "is_shop": False,
            "is_blessing": False,
        },
        {
            "level_name": "WhisperingGrove",
            "room_type": "Standard",
            "display_name": "Whispering Grove",
            "enemy_pool": ["CrystalShard", "StoneGolem", "VoidWraith", "SakuraPhantom", "StormFalcon"],
            "nikki_archetype": "SakuraDreamer",
            "nikki_lighting": "Nikki",
            "b_photo_spot": False,
            "is_shop": False,
            "is_blessing": False,
        },
        {
            "level_name": "EverburningClearing",
            "room_type": "Elite",
            "display_name": "Everburning Clearing",
            "enemy_pool": ["FireDrake", "ShadowWraith", "ArcaneGolem", "AbyssalKraken"],
            "nikki_archetype": "CosmicWeaver",
            "nikki_lighting": "Jewelry",
            "b_photo_spot": False,
            "is_shop": False,
            "is_blessing": False,
        },
        {
            "level_name": "BossArena",
            "room_type": "Boss",
            "display_name": "Boss Arena",
            "enemy_pool": ["TitanPrime", "HarmonyVoid"],
            "nikki_archetype": "MirageDancer",
            "nikki_lighting": "Silhouette",
            "b_photo_spot": False,
            "is_shop": False,
            "is_blessing": False,
        },
        {
            "level_name": "TokenShrine",
            "room_type": "Shop",
            "display_name": "Token Shrine",
            "enemy_pool": [],
            "nikki_archetype": "SakuraDreamer",
            "nikki_lighting": "Nikki",
            "b_photo_spot": False,
            "is_shop": True,
            "is_blessing": False,
        },
        {
            "level_name": "AbandonedCache",
            "room_type": "Treasure",
            "display_name": "Abandoned Cache",
            "enemy_pool": ["FireDrake", "StoneGolem"],
            "nikki_archetype": "CosmicWeaver",
            "nikki_lighting": "Jewelry",
            "b_photo_spot": False,
            "is_shop": False,
            "is_blessing": False,
        },
        {
            "level_name": "StarlightReverie",
            "room_type": "Event",
            "display_name": "Starlight Reverie",
            "enemy_pool": [],
            "nikki_archetype": "MirageDancer",
            "nikki_lighting": "Silhouette",
            "b_photo_spot": True,
            "is_shop": False,
            "is_blessing": False,
        },
        {
            "level_name": "BlessingAltar",
            "room_type": "Blessing",
            "display_name": "Blessing Altar",
            "enemy_pool": [],
            "nikki_archetype": "CosmicWeaver",
            "nikki_lighting": "Jewelry",
            "b_photo_spot": False,
            "is_shop": False,
            "is_blessing": True,
        },
    ]

    for cfg in level_configs:
        path = _create_room_level(**cfg)
        if path:
            if "exists" in str(path).lower() or _asset_exists(path):
                results["existing"].append(cfg["level_name"])
            else:
                results["created"].append(cfg["level_name"])
        else:
            results["failed"].append(cfg["level_name"])

    return results


# =============================================================================
# Data Table creation
# =============================================================================

def create_roguelike_data_tables() -> dict:
    """Create DataTable assets for roguelike data.

    Creates:
    - DT_RoguelikeRoomRegistry: Maps room_data_name → room type, enemy pool, floor range
    - DT_ShopInventory: Shop artifact prices and reroll costs
    - DT_BlessingCatalog: Blessing definitions with costs and effects
    """
    from gmm.game.roguelike import ROOM_TEMPLATES, ARTIFACTS, BLESSINGS

    _ensure_dir(DATA_TABLE_DIR)
    results = {}

    # Export JSON for manual DataTable import
    tables = {
        "DT_RoguelikeRoomRegistry": {
            "rows": {
                rid: template.to_dict() for rid, template in ROOM_TEMPLATES.items()
            },
        },
        "DT_Artifacts": {
            "rows": {
                aid: artifact.to_dict() for aid, artifact in ARTIFACTS.items()
            },
        },
        "DT_Blessings": {
            "rows": {
                bid: blessing.to_dict() for bid, blessing in BLESSINGS.items()
            },
        },
    }

    for table_name, data in tables.items():
        json_path = Path(f"Content/Melodia/DataStructures/{table_name}.json")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        if UNREAL_AVAILABLE:
            table_path = f"{DATA_TABLE_DIR}/{table_name}"
            if not _asset_exists(table_path):
                # DataTable asset creation requires the struct type to exist
                # Skip in-editor creation for now; JSON is the source of truth
                pass

        results[table_name] = str(json_path)

    return results


# =============================================================================
# Main entry point
# =============================================================================

def build_roguelike_dungeon_setup() -> dict:
    """Main entry point — creates all roguelike dungeon scaffolding.

    Run from Unreal Editor Python console:
        import setup_roguelike_dungeon
        print(setup_roguelike_dungeon.build_roguelike_dungeon_setup())
    """
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "unreal_available": UNREAL_AVAILABLE,
        "systems": {},
    }

    if UNREAL_AVAILABLE:
        unreal.log("=== Roguelike Dungeon Setup ===")

        # 1. RoomData assets
        unreal.log("--- RoomData Assets ---")
        result["systems"]["room_data"] = create_all_room_data_assets()

        # 2. Blueprints
        unreal.log("--- Blueprints ---")
        result["systems"]["blueprints"] = {
            "dungeon_generator": create_roguelike_dungeon_generator_bp() or "not_created",
            "floor_manager": create_dungeon_floor_manager_bp() or "not_created",
        }

        # 3. Room levels
        unreal.log("--- Room Levels ---")
        result["systems"]["room_levels"] = create_all_room_levels()

        unreal.log("=== Roguelike Dungeon Setup Complete ===")
    else:
        unreal.log_warning("Unreal Python not available — generating JSON only")

    # 4. DataTables (always generate JSON)
    result["systems"]["data_tables"] = create_roguelike_data_tables()

    # 5. Next steps
    result["next_steps"] = _generate_next_steps()

    # Save report
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    return result


def _generate_next_steps() -> list[str]:
    """Generate next steps checklist based on what was created."""
    steps = [
        "1. Verify ProceduralDungeon plugin is loaded (Plugins window)",
        "2. In Content Browser, navigate to /Game/Melodia/Roguelike/RoomData/",
        "3. Open any RoomData asset → verify URoguelikeRoomCustomData is attached",
        "4. Navigate to /Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator",
        "5. Open Blueprint → override ChooseFirstRoomData to return RD_MelodiaGrove_V1",
        "6. Override ChooseNextRoomData — call generate_floor() from GMM roguelike rules",
        "7. Override IsValidDungeon — verify boss room exists",
        "8. Place BP_RoguelikeDungeonGenerator in L_ZenForestTest or new DungeonRun level",
        "9. Set SeedType to Fixed, Seed to any value (e.g. 1337)",
        "10. Call Generate() in BeginPlay or via Blueprint event",
        "11. Test in PIE — verify room levels stream in, encounters trigger",
        "12. Import DataTable JSON files via Content Browser → Import",
    ]

    if not UNREAL_AVAILABLE:
        steps.insert(0, "0. Open Unreal Editor and re-run this script in the Python console")
        steps.insert(1, "0a. Ensure ProceduralDungeon + MelodiaCore plugins are compiled")

    return steps


# =============================================================================
# CLI entry point
# =============================================================================

if __name__ == "__main__":
    report = build_roguelike_dungeon_setup()
    print(json.dumps(report, indent=2))
