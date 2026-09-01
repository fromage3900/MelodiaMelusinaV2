import unreal
import json

# ============================================================
# PHASE 4: Verify PCG generation results (simple)
# ============================================================

actors = unreal.EditorLevelLibrary.get_all_level_actors()
pcg_volumes = [a for a in actors if type(a).__name__ == 'PCGVolume']

print(f"PCGVolumes: {len(pcg_volumes)}")
for vol in pcg_volumes:
    label = vol.get_actor_label()
    loc = vol.get_actor_location()
    scale = vol.get_actor_scale3d()
    
    # Get all ISM components
    isms = vol.get_components_by_class(unreal.InstancedStaticMeshComponent)
    total_instances = 0
    for ism in isms:
        total_instances += ism.get_instance_count()
    
    print(f"  {label:40s} @[{loc.x:.0f},{loc.y:.0f},{loc.z:.0f}] ISMs:{len(isms)} Instances:{total_instances}")

# Count total actors after PCG
actors_after = unreal.EditorLevelLibrary.get_all_level_actors()
from collections import Counter
classes = Counter(type(a).__name__ for a in actors_after)
print(f"\n=== Actor Summary ===")
print(f"Total actors: {len(actors_after)}")
for cls, count in sorted(classes.items(), key=lambda x: -x[1]):
    if count > 1:
        print(f"  {count:4d}  {cls}")

# Save the level
print("\nSaving level...")
unreal.EditorLevelLibrary.save_current_level()
print("Level saved.")
