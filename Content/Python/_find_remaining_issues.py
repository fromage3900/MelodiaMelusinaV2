import unreal
import json

# List all non-standard meshes
actors = unreal.EditorLevelLibrary.get_all_level_actors()
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]

# Known cathedral meshes
cathedral_keywords = ["Cathedral", "P4_Cathedral", "ATL", "Starskiff", "SeaAbove_ObservationCliff"]
junk_keywords = ["SeaAbove_ObservationCliff", "SM_Starskiff", "SM_Clutter", "SM_Flora", "SM_Kelp", "SM_Coral"]

junk = []
atlantis = []
other = []

for a in sma:
    label = a.get_actor_label()
    if any(kw in label for kw in junk_keywords):
        loc = a.get_actor_location()
        junk.append(f"{label} @Z={loc.z:.0f}")
    elif "ATL" in label:
        loc = a.get_actor_location()
        atlantis.append(f"{label} @[{loc.x:.0f},{loc.y:.0f},{loc.z:.0f}]")
    elif not any(kw in label for kw in cathedral_keywords):
        other.append(label)

print(f"Junk pieces ({len(junk)}):")
for j in junk[:15]:
    print(f"  {j}")

print(f"\nAtlantis pieces ({len(atlantis)}):")
for a in atlantis[:10]:
    print(f"  {a}")

print(f"\nOther unknown ({len(other)}):")
for o in other[:10]:
    print(f"  {o}")
