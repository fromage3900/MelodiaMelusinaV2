#!/usr/bin/env python3
"""
Create MI_Copernicus_CymaticReactive material instance and apply to cathedral pieces.

This script is designed to be run via the UE Editor Python environment.
It creates a new material instance with audio-reactive parameters that read
from MPC_Melodia_Palette, then applies it to cathedral mesh actors.

Usage:
    1. In UE Editor, open Windows > Developer Tools > Output Log
    2. Run: exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/_mi_cymatic_reactive_all.py", encoding="utf-8").read())
    
    OR via Monolith:
    python Tools/ue_run_python.py --file Content/Python/_mi_cymatic_reactive_all.py
"""
import unreal
import json
from pathlib import Path

MI_PATH = "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CymaticReactive"
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

# Audio-reactive scalar parameters
AUDIO_REACTIVE_PARAMS = {
    "CymaticAmplitude": 1.0,
    "BeatPulse": 0.0,
    "BassIntensity": 0.5,
    "CymaticModeN": 3.0,
    "CymaticModeM": 2.0,
}

CATHEDRAL_PREFIXES = [
    "JELLY_Cathedral_Body",
    "SM_Cathedral",
    "Cathedral",
]

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "mi_cymatic_reactive_report.json"


def create_mi():
    """Create the MI_Copernicus_CymaticReactive material instance."""
    print("\n" + "=" * 60)
    print("STEP 1: Creating MI_Copernicus_CymaticReactive")
    print("=" * 60)

    if unreal.EditorAssetLibrary.does_asset_exist(MI_PATH):
        mi = unreal.EditorAssetLibrary.load_asset(MI_PATH)
        print(f"[create] MI already exists: {MI_PATH}")
        return mi

    master = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if not master:
        print(f"[create] ERROR: Master material not found: {MASTER_PATH}")
        return None

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi_dir = "/Game/EnvSandbox/Materials/Instances/Copernicus"

    if not unreal.EditorAssetLibrary.does_directory_exist(mi_dir):
        unreal.EditorAssetLibrary.make_directory(mi_dir)
        print(f"[create] Created directory: {mi_dir}")

    mi = asset_tools.create_asset(
        "MI_Copernicus_CymaticReactive",
        mi_dir,
        unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew()
    )

    if not mi:
        print("[create] ERROR: Failed to create MI")
        return None

    try:
        mi.set_editor_property("parent", master)
        print(f"[create] Set parent: {MASTER_PATH}")
    except Exception as e:
        print(f"[create] WARNING: Failed to set parent: {e}")

    # Set audio-reactive scalar parameters
    for param_name, param_value in AUDIO_REACTIVE_PARAMS.items():
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                mi, param_name, param_value
            )
            print(f"[create] Set scalar {param_name} = {param_value}")
        except Exception as e:
            print(f"[create] WARNING: Failed to set {param_name}: {e}")

    try:
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        print(f"[create] Saved: {MI_PATH}")
    except Exception as e:
        print(f"[create] WARNING: Failed to save: {e}")

    return mi


def find_cathedral_pieces():
    """Find all cathedral mesh actors in the current map."""
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        print("[find] ERROR: No editor world")
        return []

    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    cathedral_actors = []

    for actor in all_actors:
        actor_label = actor.get_actor_label()

        # Check if actor name matches cathedral prefixes
        is_cathedral = False
        for prefix in CATHEDRAL_PREFIXES:
            if prefix.lower() in actor_label.lower():
                is_cathedral = True
                break

        # Also check static mesh component
        if not is_cathedral:
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            if comp and comp.static_mesh:
                mesh_name = comp.static_mesh.get_name()
                for prefix in CATHEDRAL_PREFIXES:
                    if prefix.lower() in mesh_name.lower():
                        is_cathedral = True
                        break

        if is_cathedral:
            cathedral_actors.append(actor)

    return cathedral_actors


def apply_mi_to_pieces(mi, actors):
    """Apply material instance to cathedral pieces."""
    print("\n" + "=" * 60)
    print("STEP 2: Applying MI to Cathedral Pieces")
    print("=" * 60)

    updated = 0
    total_mats = 0
    updated_actors = []

    for actor in actors:
        label = actor.get_actor_label()
        comps = actor.get_components_by_class(unreal.StaticMeshComponent)
        actor_mats = 0

        for comp in comps:
            try:
                mat_count = comp.get_num_materials()
                for i in range(mat_count):
                    comp.set_material(i, mi)
                    actor_mats += 1
            except Exception as e:
                print(f"  [apply] WARNING: {label}: {e}")

        if actor_mats > 0:
            print(f"  [apply] {label}: {actor_mats} material slots")
            updated += 1
            total_mats += actor_mats
            updated_actors.append(label)

    return updated, total_mats, updated_actors


def generate_report(mi, updated, total_mats, updated_actors):
    """Generate a JSON report of the operation."""
    print("\n" + "=" * 60)
    print("STEP 3: Generating Report")
    print("=" * 60)

    report = {
        "mi_created": MI_PATH,
        "parent": MASTER_PATH,
        "mpc_source": MPC_PATH,
        "parameters": AUDIO_REACTIVE_PARAMS,
        "pieces_updated": updated,
        "total_material_slots": total_mats,
        "updated_actors": updated_actors,
        "status": "success" if updated > 0 else "no_pieces_found"
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"[report] Saved to: {OUTPUT_PATH}")
    return report


def main():
    print("=" * 60)
    print("MI_Copernicus_CymaticReactive - Create & Apply")
    print("=" * 60)

    # Step 1: Create MI
    mi = create_mi()
    if not mi:
        print("\n[FAILED] MI creation failed")
        return None

    # Step 2: Find cathedral pieces
    actors = find_cathedral_pieces()
    print(f"\n[find] Found {len(actors)} cathedral actors")

    if not actors:
        print("[find] No cathedral actors found in current map")
        print("[find] Make sure LV_SeaAbove_Prototype is loaded")
        # Still generate report
        report = generate_report(mi, 0, 0, [])
        return report

    # Step 3: Apply MI
    updated, total_mats, updated_actors = apply_mi_to_pieces(mi, actors)

    # Step 4: Generate report
    report = generate_report(mi, updated, total_mats, updated_actors)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"MI Created: {MI_PATH}")
    print(f"Parameters: {len(AUDIO_REACTIVE_PARAMS)}")
    for k, v in AUDIO_REACTIVE_PARAMS.items():
        print(f"  {k} = {v}")
    print(f"Pieces Updated: {updated}")
    print(f"Total Material Slots: {total_mats}")
    print(f"Report: {OUTPUT_PATH}")

    return report


if __name__ == "__main__":
    main()