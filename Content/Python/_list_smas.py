import unreal
import json

# List all SMA labels to find Atlantis pieces
actors = unreal.EditorLevelLibrary.get_all_level_actors()
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]

labels = sorted([a.get_actor_label() for a in sma])
print(f"Total SMAs: {len(labels)}")
for label in labels:
    print(label)
