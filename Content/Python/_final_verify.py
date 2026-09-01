import unreal
import json

# Final verification
actors = unreal.EditorLevelLibrary.get_all_level_actors()
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]

result = {
    "total": len(actors),
    "sma": len(sma),
    "atlantis": sum(1 for a in sma if "ATL" in a.get_actor_label()),
    "cathedral": sum(1 for a in sma if "Cathedral" in a.get_actor_label() and "ATL" not in a.get_actor_label()),
    "houdini": sum(1 for a in sma if "P4_Cathedral" in a.get_actor_label()),
    "pcg": len([a for a in actors if type(a).__name__ == "PCGVolume"]),
    "canonical_z": None,
    "z_range": None,
}

# Get landscape Z
for a in actors:
    if "CanonicalLandscape" in a.get_actor_label():
        result["canonical_z"] = a.get_actor_location().z
        break

# Get cathedral Z range
z_vals = [a.get_actor_location().z for a in sma]
if z_vals:
    result["z_range"] = {
        "min": min(z_vals),
        "max": max(z_vals),
        "avg": sum(z_vals) / len(z_vals),
    }

print(json.dumps(result, indent=2))
