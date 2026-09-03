#!/usr/bin/env python3
"""
Apply MI_Copernicus_CymaticReactive to 10+ cathedral mesh actors.

Mesh path patterns (JELLY_Cathedral_Body_SERAPH_*):
  /Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/

Applies the material to static mesh components of actors with
matching SM_Cathedral or JELLY_Cathedral_Body prefix in LV_SeaAbove_Prototype.

Run inside UE Editor Python (Monolith run_python):
    exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/_mi_cymatic_reactive_apply.py", encoding="utf-8").read())
"""
import unreal

MI_PATH = "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CymaticReactive"
MAP_PATH = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"

# Cathedral mesh name prefixes to match
CATHEDRAL_PREFIXES = [
    "JELLY_Cathedral_Body",
    "SM_Cathedral",
    "Cathedral",
]

# Maximum pieces to update
MAX_PIECES = 50


def find_cathedral_actors():
    """Find all cathedral actors in the map."""
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        print("[apply] ERROR: No editor world")
        return []

    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    cathedral_actors = []

    for actor in all_actors:
        actor_label = actor.get_actor_label()
        actor_class = actor.get_class().get_name()

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


def apply_material_to_actor(actor, material):
    """Apply material to all static mesh components of an actor."""
    applied = 0

    # Get static mesh components
    comps = actor.get_components_by_class(unreal.StaticMeshComponent)
    for comp in comps:
        try:
            # Set material on all materials
            mat_count = comp.get_num_materials()
            for i in range(mat_count):
                comp.set_material(i, material)
                applied += 1
        except Exception as e:
            print(f"  [apply] WARNING: Failed to set material on {actor.get_actor_label()}: {e}")

    return applied


def main():
    print("=" * 60)
    print("Applying MI_Copernicus_CymaticReactive to Cathedral Pieces")
    print("=" * 60)

    # Load the material instance
    mi = unreal.EditorAssetLibrary.load_asset(MI_PATH)
    if not mi:
        print(f"[apply] ERROR: MI not found: {MI_PATH}")
        print("[apply] Run _mi_cymatic_reactive_create.py first")
        return []

    print(f"[apply] Loaded MI: {MI_PATH}")

    # Find cathedral actors
    actors = find_cathedral_actors()
    print(f"[apply] Found {len(actors)} cathedral actors")

    if not actors:
        print("[apply] No cathedral actors found. Checking for static meshes...")
        # Try loading meshes directly
        mesh_dir = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes"
        if unreal.EditorAssetLibrary.does_directory_exist(mesh_dir):
            meshes = unreal.EditorAssetLibrary.list_assets(mesh_dir, recursive=True)
            print(f"[apply] Found {len(meshes)} meshes in {mesh_dir}")
            for m in meshes[:10]:
                print(f"  {m}")
        return []

    # Apply material
    updated = 0
    total_mats = 0
    for actor in actors[:MAX_PIECES]:
        label = actor.get_actor_label()
        mats = apply_material_to_actor(actor, mi)
        if mats > 0:
            print(f"  [apply] {label}: {materials} material slots updated")
            updated += 1
            total_mats += mats

    print(f"\n[RESULT] Updated {updated} actors with {total_mats} total material slots")
    return updated


if __name__ == "__main__":
    main()