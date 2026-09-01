import unreal
import json
import os

# ============================================================
# STEP 1: Load Gaea LiquidCathedral terrain + review placement
# ============================================================

# Load the Gaea terrain mesh
gaea_mesh_path = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/SM_Gaea_LiquidCathedral_1025.SM_Gaea_LiquidCathedral_1025"
gaea_mesh = unreal.EditorAssetLibrary.load_asset(gaea_mesh_path)

if gaea_mesh:
    print(f"Gaea mesh: {gaea_mesh.get_name()}")
    bounds = gaea_mesh.get_bounded_extent()
    print(f"Bounds: {bounds}")
else:
    print("[FATAL] Gaea mesh not found")

# Load the substrate MI
gaea_mi_path = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/MI_Gaea_LiquidCathedral_Substrate.MI_Gaea_LiquidCathedral_Substrate"
gaea_mi = unreal.EditorAssetLibrary.load_asset(gaea_mi_path)
if gaea_mi:
    print(f"Gaea MI: {gaea_mi.get_name()}")
else:
    print("[WARN] Gaea MI not found")

# Get current level actors
actors = unreal.EditorLevelLibrary.get_all_level_actors()
landscape_actors = [a for a in actors if type(a).__name__ == 'Landscape']
print(f"\nLandscape actors: {len(landscape_actors)}")
for l in landscape_actors:
    print(f"  {l.get_actor_label()}")

# Check for existing Gaea placement
gaea_actors = [a for a in actors if 'Gaea' in a.get_actor_label()]
print(f"Gaea actors: {len(gaea_actors)}")
for g in gaea_actors:
    print(f"  {g.get_actor_label()}")
