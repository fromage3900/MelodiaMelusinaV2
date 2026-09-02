import unreal
import json

# Verify final state
actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Check CanonicalLandscape Z
for a in actors:
    if "CanonicalLandscape" in a.get_actor_label():
        loc = a.get_actor_location()
        print(f"CanonicalLandscape Z: {loc.z:.0f}")
        break

# Check cathedral Z range
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]
z_vals = [a.get_actor_location().z for a in sma]
print(f"Cathedral Z range: {min(z_vals):.0f} to {max(z_vals):.0f}")
print(f"Cathedral Z avg: {sum(z_vals)/len(z_vals):.0f}")

# Count by category
result = {
    "total": len(actors),
    "sma": len(sma),
    "atlantis": sum(1 for a in sma if "ATL" in a.get_actor_label()),
    "cathedral": sum(1 for a in sma if "Cathedral" in a.get_actor_label() and "ATL" not in a.get_actor_label()),
    "houdini": sum(1 for a in sma if "P4_Cathedral" in a.get_actor_label()),
    "pcg": len([a for a in actors if type(a).__name__ == "PCGVolume"]),
}
print(json.dumps(result, indent=2))
