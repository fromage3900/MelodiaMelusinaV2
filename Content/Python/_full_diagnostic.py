import unreal
import json

# Full diagnostic - what's in the level
actors = unreal.EditorLevelLibrary.get_all_level_actors()
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]

# Get unique mesh types
mesh_counts = {}
for a in sma:
    loc = a.get_actor_location()
    label = a.get_actor_label()
    # Extract base name (without number suffix)
    import re
    base = re.sub(r'\d+$', '', label).rstrip('_')
    if base not in mesh_counts:
        mesh_counts[base] = {"count": 0, "z_range": [float('inf'), float('-inf')]}
    mesh_counts[base]["count"] += 1
    mesh_counts[base]["z_range"][0] = min(mesh_counts[base]["z_range"][0], loc.z)
    mesh_counts[base]["z_range"][1] = max(mesh_counts[base]["z_range"][1], loc.z)

# Sort by count
sorted_meshes = sorted(mesh_counts.items(), key=lambda x: -x[1]["count"])

print(f"Total SMAs: {len(sma)}")
print(f"Unique mesh types: {len(mesh_counts)}")
print()

for name, info in sorted_meshes[:30]:
    z_min, z_max = info["z_range"]
    print(f"  {name:40s} {info['count']:3d}  Z:{z_min:.0f}-{z_max:.0f}")
