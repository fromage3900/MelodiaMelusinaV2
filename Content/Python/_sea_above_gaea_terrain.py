import unreal
import json
import os

# ============================================================
# GAEA TERRAIN → SEA ABOVE: Full terrain replacement
# ============================================================

# Load Gaea mesh
gaea_path = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/SM_Gaea_LiquidCathedral_1025.SM_Gaea_LiquidCathedral_1025"
gaea = unreal.EditorAssetLibrary.load_asset(gaea_path)

if gaea is None:
    print("[FATAL] Gaea mesh not found")
    exit()

print(f"Gaea mesh loaded: {gaea.get_name()}")

# Load Gaea MI
gaea_mi_path = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/MI_Gaea_LiquidCathedral_Substrate.MI_Gaea_LiquidCathedral_Substrate"
gaea_mi = unreal.EditorAssetLibrary.load_asset(gaea_mi_path)
print(f"Gaea MI: {gaea_mi.get_name() if gaea_mi else '(not found)'}")

# Get current level actors
actors = unreal.EditorLevelLibrary.get_all_level_actors()
landscapes = [a for a in actors if type(a).__name__ == 'Landscape']
landscape_proxies = [a for a in actors if type(a).__name__ == 'LandscapeStreamingProxy']
gaea_actors = [a for a in actors if 'Gaea' in a.get_actor_label()]
sma_actors = [a for a in actors if type(a).__name__ == 'StaticMeshActor']

print(f"\nCurrent level state:")
print(f"  Landscapes: {len(landscapes)}")
print(f"  LandscapeStreamingProxies: {len(landscape_proxies)}")
print(f"  Gaea actors: {len(gaea_actors)}")
print(f"  StaticMeshActors: {len(sma_actors)}")

# Check existing Gaea placement
for g in gaea_actors:
    loc = g.get_actor_location()
    scl = g.get_actor_scale3d()
    print(f"  Gaea: {g.get_actor_label()} @[{loc.x:.0f},{loc.y:.0f},{loc.z:.0f}] scale=[{scl.x:.1f},{scl.y:.1f},{scl.z:.1f}]")

# Check landscape bounds
for l in landscapes:
    loc = l.get_actor_location()
    scl = l.get_actor_scale3d()
    print(f"  Landscape: {l.get_actor_label()} @[{loc.x:.0f},{loc.y:.0f},{loc.z:.0f}] scale=[{scl.x:.1f},{scl.y:.1f},{scl.z:.1f}]")
