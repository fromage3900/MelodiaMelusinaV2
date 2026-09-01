import unreal
import json
import os

# ============================================================
# GAEA LIQUID CATHEDRAL — Review + Place in Sea Above
# ============================================================

# Load Gaea mesh
gaea_mesh_path = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/SM_Gaea_LiquidCathedral_1025.SM_Gaea_LiquidCathedral_1025"
gaea_mesh = unreal.EditorAssetLibrary.load_asset(gaea_mesh_path)

if gaea_mesh:
    print(f"Gaea mesh: {gaea_mesh.get_name()}")
    
    # Get bounds via get_bounds()
    try:
        bounds = gaea_mesh.get_bounds()
        print(f"Bounds Origin: {bounds.origin}")
        print(f"Bounds Extent: {bounds.extent}")
        print(f"Bounds Min: ({bounds.origin.x - bounds.extent.x}, {bounds.origin.y - bounds.extent.y}, {bounds.origin.z - bounds.extent.z})")
        print(f"Bounds Max: ({bounds.origin.x + bounds.extent.x}, {bounds.origin.y + bounds.extent.y}, {bounds.origin.z + bounds.extent.z})")
    except Exception as e:
        print(f"Bounds error: {e}")
    
    # Get physics tri mesh bounds
    try:
        bounds = gaea_mesh.get_render_data().get_bounds()
        print(f"Render Bounds: {bounds}")
    except:
        pass
else:
    print("[FATAL] Gaea mesh not found")

# Load Gaea MI
gaea_mi_path = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/MI_Gaea_LiquidCathedral_Substrate.MI_Gaea_LiquidCathedral_Substrate"
gaea_mi = unreal.EditorAssetLibrary.load_asset(gaea_mi_path)
if gaea_mi:
    print(f"Gaea MI: {gaea_mi.get_name()}")
else:
    print("[WARN] Gaea MI not found")

# Check current level state
actors = unreal.EditorLevelLibrary.get_all_level_actors()
landscape_actors = [a for a in actors if type(a).__name__ == 'Landscape']
gaea_actors = [a for a in actors if 'Gaea' in a.get_actor_label() or 'LiquidCathedral' in a.get_actor_label()]
sma_actors = [a for a in actors if type(a).__name__ == 'StaticMeshActor']

print(f"\nLevel state:")
print(f"  Landscape actors: {len(landscape_actors)}")
print(f"  Gaea actors: {len(gaea_actors)}")
print(f"  StaticMeshActors: {len(sma_actors)}")

# Check for existing Gaea placement
for g in gaea_actors:
    loc = g.get_actor_location()
    print(f"  Gaea: {g.get_actor_label()} @[{loc.x:.0f},{loc.y:.0f},{loc.z:.0f}]")
