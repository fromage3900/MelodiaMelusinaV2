import unreal
import json

# ============================================================
# PHASE 1: Remove 4 overlapping PCG volumes using proper method
# ============================================================

actors = unreal.EditorLevelLibrary.get_all_level_actors()
pcg_volumes = [a for a in actors if type(a).__name__ == 'PCGVolume']

print(f"Found {len(pcg_volumes)} PCGVolumes")
for vol in pcg_volumes:
    label = vol.get_actor_label()
    loc = vol.get_actor_location()
    print(f"  Removing: {label} @[{loc.x:.0f},{loc.y:.0f},{loc.z:.0f}]")
    # Use EditorLevelLibrary to destroy
    success = unreal.EditorLevelLibrary.destroy_actor(vol)
    print(f"    -> {'OK' if success else 'FAIL'}")

# Verify removal
actors_after = unreal.EditorLevelLibrary.get_all_level_actors()
pcg_after = [a for a in actors_after if type(a).__name__ == 'PCGVolume']
print(f"\nRemaining PCGVolumes: {len(pcg_after)}")

print("\n=== PHASE 1 complete ===")
