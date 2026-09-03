"""Setup roguelike blueprints and assets for Melodia.

Creates:
- BP_RoguelikeRunManager - Manages run state, floor progression
- BP_ArtifactPickup - Mid-run upgrade pickups
- BP_BlessingAltar - Meta-progression shrines (persistent)
- BP_FloorGenerator - Procs new floors
- DT_RoguelikeRooms - Room template data table
- DT_Artifacts - Artifact data table
- DT_Blessings - Blessing data table

RUN IN UNREAL EDITOR PYTHON CONSOLE:
import setup_roguelike; print(setup_roguelike.build_roguelike_setup())
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    import unreal
    UNREAL_AVAILABLE = True
except Exception:
    UNREAL_AVAILABLE = False


# Asset paths
ROGUELIKE_PATH = "/Game/Melodia/Roguelike"
RUN_MANAGER_BP = f"{ROGUELIKE_PATH}/BP_RoguelikeRunManager"
ARTIFACT_BP = f"{ROGUELIKE_PATH}/BP_ArtifactPickup"
BLESSING_ALTAR_BP = f"{ROGUELIKE_PATH}/BP_BlessingAltar"
FLOOR_GEN_BP = f"{ROGUELIKE_PATH}/BP_FloorGenerator"


def generate_room_data_table() -> dict:
    """Generate room template data table for UE DataTable asset."""
    from gmm.game.roguelike import ROOM_TEMPLATES
    
    rows = {}
    for room_id, template in ROOM_TEMPLATES.items():
        rows[room_id] = template.to_dict()
    
    return {
        "DataType": "RoguelikeRoom",
        "Rows": rows,
    }


def generate_artifact_data_table() -> dict:
    """Generate artifact data table."""
    from gmm.game.roguelike import ARTIFACTS
    
    rows = {}
    for artifact_id, artifact in ARTIFACTS.items():
        rows[artifact_id] = artifact.to_dict()
    
    return {
        "DataType": "RoguelikeArtifact",
        "Rows": rows,
    }


def generate_blessing_data_table() -> dict:
    """Generate blessing data table."""
    from gmm.game.roguelike import BLESSINGS
    
    rows = {}
    for blessing_id, blessing in BLESSINGS.items():
        rows[blessing_id] = blessing.to_dict()
    
    return {
        "DataType": "RoguelikeBlessing",
        "Rows": rows,
    }


def save_data_tables() -> dict:
    """Save all roguelike data tables to JSON files."""
    results = {}
    
    # Rooms
    room_data = generate_room_data_table()
    room_path = Path("Content/Melodia/DataStuctures/DT_RoguelikeRooms.json")
    room_path.parent.mkdir(parents=True, exist_ok=True)
    room_path.write_text(json.dumps(room_data, indent=2), encoding="utf-8")
    results["rooms"] = str(room_path)
    
    # Artifacts
    artifact_data = generate_artifact_data_table()
    artifact_path = Path("Content/Melodia/DataStuctures/DT_Artifacts.json")
    artifact_path.write_text(json.dumps(artifact_data, indent=2), encoding="utf-8")
    results["artifacts"] = str(artifact_path)
    
    # Blessings
    blessing_data = generate_blessing_data_table()
    blessing_path = Path("Content/Melodia/DataStuctures/DT_Blessings.json")
    blessing_path.write_text(json.dumps(blessing_data, indent=2), encoding="utf-8")
    results["blessings"] = str(blessing_path)
    
    return results


def create_roguelike_blueprint_assets() -> dict:
    """Create blueprint assets in Unreal (requires editor)."""
    if not UNREAL_AVAILABLE:
        return {"ok": False, "error": "Unreal module not available"}
    
    import unreal
    
    results = {}
    
    # Ensure directory exists
    if not unreal.EditorAssetLibrary.does_directory_exist(ROGUELIKE_PATH):
        try:
            unreal.EditorAssetLibrary.make_directory(ROGUELIKE_PATH)
            results["directory_created"] = True
        except Exception as e:
            results["directory_error"] = str(e)
    
    # Create Run Manager BP
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Actor)
    
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    bp = asset_tools.create_asset(
        "BP_RoguelikeRunManager",
        ROGUELIKE_PATH,
        unreal.Blueprint,
        factory,
    )
    
    if bp:
        unreal.EditorAssetLibrary.save_asset(RUN_MANAGER_BP)
        results["run_manager_created"] = True
    
    # Create Artifact Pickup BP
    factory2 = unreal.BlueprintFactory()
    factory2.set_editor_property("parent_class", unreal.Actor)
    bp2 = asset_tools.create_asset(
        "BP_ArtifactPickup",
        ROGUELIKE_PATH,
        unreal.Blueprint,
        factory2,
    )
    
    if bp2:
        unreal.EditorAssetLibrary.save_asset(ARTIFACT_BP)
        results["artifact_pickup_created"] = True
    
    # Create Blessing Altar BP
    factory3 = unreal.BlueprintFactory()
    factory3.set_editor_property("parent_class", unreal.Actor)
    bp3 = asset_tools.create_asset(
        "BP_BlessingAltar",
        ROGUELIKE_PATH,
        unreal.Blueprint,
        factory3,
    )
    
    if bp3:
        unreal.EditorAssetLibrary.save_asset(BLESSING_ALTAR_BP)
        results["blessing_altar_created"] = True
    
    return results


def build_roguelike_setup() -> dict:
    """Main entry point - creates all roguelike scaffolding."""
    results = {
        "data_tables": save_data_tables(),
        "blueprints": {} if not UNREAL_AVAILABLE else create_roguelike_blueprint_assets(),
    }
    
    if UNREAL_AVAILABLE:
        results["blueprints"]["unreal_available"] = True
    else:
        results["blueprints"]["note"] = "Run in Unreal Editor to create blueprints"
    
    # Add next steps
    results["next_steps"] = [
        "1. In Unreal Editor, open Content Browser",
        "2. Navigate to /Game/Melodia/Roguelike folder",
        "3. BP_RoguelikeRunManager - Add variables: CurrentFloor (int), Act (int), Artifacts (array)",
        "4. BP_ArtifactPickup - Add StaticMesh component, OnOverlap event to grant artifact",
        "5. BP_BlessingAltar - Add interaction to spend golden tokens on blessings",
        "6. Create Data Tables from the generated JSON files",
        "7. Place BP_FloorGenerator in level to proc new floors",
    ]
    
    return results


if __name__ == "__main__":
    report = build_roguelike_setup()
    print(json.dumps(report, indent=2))