import unreal
import json

# ============================================================
# RE-PLACE GAEA TERRAIN + FINAL REVIEW
# ============================================================

# Load Gaea mesh
gaea_path = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/SM_Gaea_LiquidCathedral_1025.SM_Gaea_LiquidCathedral_1025"
gaea = unreal.EditorAssetLibrary.load_asset(gaea_path)
gaea_mi_path = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/MI_Gaea_LiquidCathedral_Substrate.MI_Gaea_LiquidCathedral_Substrate"
gaea_mi = unreal.EditorAssetLibrary.load_asset(gaea_mi_path)

if gaea:
    # Place at 1x scale, Z offset to match cathedral base
    gaea_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
        gaea,
        unreal.Vector(0, 0, 13258),
        unreal.Rotator(0, 0, 0)
    )
    if gaea_actor:
        gaea_actor.set_actor_scale3d(unreal.Vector(1, 1, 1))
        gaea_actor.set_actor_label("Gaea_LiquidCathedral_Terrain")
        if gaea_mi:
            comp = gaea_actor.get_component_by_class(unreal.StaticMeshComponent)
            if comp:
                comp.set_editor_property("override_materials", [gaea_mi])
        print("Gaea terrain re-placed")
else:
    print("[WARN] Gaea mesh not found")

# Final review
actors = unreal.EditorLevelLibrary.get_all_level_actors()
gaea_actors = [a for a in actors if 'Gaea' in a.get_actor_label()]
sma_actors = [a for a in actors if type(a).__name__ == 'StaticMeshActor']
landscape_actors = [a for a in actors if type(a).__name__ == 'Landscape']
pcg_volumes = [a for a in actors if type(a).__name__ == 'PCGVolume']

print(f"\n=== FINAL LEVEL STATE ===")
print(f"Gaea terrain: {len(gaea_actors)}")
print(f"StaticMeshActors: {len(sma_actors)}")
print(f"Landscape actors: {len(landscape_actors)}")
print(f"PCG Volumes: {len(pcg_volumes)}")
print(f"Total actors: {len(actors)}")

# Count by category
atlantis = sum(1 for a in sma_actors if 'ATL' in a.get_actor_label())
cathedral = sum(1 for a in sma_actors if 'Cathedral' in a.get_actor_label() and 'ATL' not in a.get_actor_label())
houdini = sum(1 for a in sma_actors if 'P4_Cathedral' in a.get_actor_label())
other = len(sma_actors) - atlantis - cathedral - houdini

print(f"\nBy category:")
print(f"  Atlantis Palace: {atlantis}")
print(f"  Cathedral Kitbash: {cathedral}")
print(f"  Houdini Cathedral: {houdini}")
print(f"  Other: {other}")

# Save
unreal.EditorLevelLibrary.save_current_level()
print("\nLevel saved.")
