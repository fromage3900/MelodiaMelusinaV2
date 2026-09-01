import unreal
import json

# Final state verification
actors = unreal.EditorLevelLibrary.get_all_level_actors()
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]

result = {
    "world": unreal.EditorLevelLibrary.get_editor_world().get_name(),
    "total_actors": len(actors),
    "sma_count": len(sma),
    "atlantis": sum(1 for a in sma if "ATL" in a.get_actor_label()),
    "cathedral": sum(1 for a in sma if "Cathedral" in a.get_actor_label() and "ATL" not in a.get_actor_label()),
    "houdini": sum(1 for a in sma if "P4_Cathedral" in a.get_actor_label()),
    "gaea": len([a for a in actors if "Gaea" in a.get_actor_label()]),
    "pcg": len([a for a in actors if type(a).__name__ == "PCGVolume"]),
    "landscape": len([a for a in actors if type(a).__name__ == "Landscape"]),
}

print(json.dumps(result, indent=2))
