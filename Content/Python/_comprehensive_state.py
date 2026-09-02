import unreal
import json

# Final comprehensive state check
actors = unreal.EditorLevelLibrary.get_all_level_actors()
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]

# Get unique mesh types with counts
mesh_counts = {}
for a in sma:
    label = a.get_actor_label()
    import re
    base = re.sub(r'\d+$', '', label).rstrip('_')
    if base not in mesh_counts:
        mesh_counts[base] = {"count": 0, "z_min": float('inf'), "z_max": float('-inf')}
    mesh_counts[base]["count"] += 1
    loc = a.get_actor_location()
    mesh_counts[base]["z_min"] = min(mesh_counts[base]["z_min"], loc.z)
    mesh_counts[base]["z_max"] = max(mesh_counts[base]["z_max"], loc.z)

# Check PCG
pcg = [a for a in actors if type(a).__name__ == "PCGVolume"]
pcg_total = 0
for vol in pcg:
    isms = vol.get_components_by_class(unreal.InstancedStaticMeshComponent)
    pcg_total += sum(ism.get_instance_count() for ism in isms)

# Check Copernicus MIs
mi_dir = "/Game/EnvSandbox/Materials/Instances/Copernicus/"
mis = unreal.EditorAssetLibrary.list_assets(mi_dir)
mis = [m for m in mis if "MI_Copernicus_" in m]

result = {
    "world": unreal.EditorLevelLibrary.get_editor_world().get_name(),
    "total_actors": len(actors),
    "sma_count": len(sma),
    "pcg_volumes": len(pcg),
    "pcg_instances": pcg_total,
    "copernicus_mis": len(mis),
    "mesh_types": len(mesh_counts),
    "top_meshes": dict(sorted(mesh_counts.items(), key=lambda x: -x[1]["count"])[:10]),
    "z_range": {
        "min": min(a.get_actor_location().z for a in sma),
        "max": max(a.get_actor_location().z for a in sma),
    },
    "canonical_z": next((a.get_actor_location().z for a in actors if "Canonical" in a.get_actor_label()), None),
}

print(json.dumps(result, indent=2, default=str))
