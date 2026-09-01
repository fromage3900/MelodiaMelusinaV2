import unreal
import json

# List all actors and their labels
actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Find junk
junk_keywords = ["Sphere", "Plane", "Reef_", "Flora_", "Kelp_", "Coral_", "Starfish", "HayStack", "Greybox"]
junk = []
for a in actors:
    label = a.get_actor_label()
    for kw in junk_keywords:
        if kw.lower() in label.lower():
            loc = a.get_actor_location()
            junk.append(f"{label} @[{loc.x:.0f},{loc.y:.0f},{loc.z:.0f}]")
            break

print(f"Junk found: {len(junk)}")
for j in junk[:30]:
    print(f"  {j}")

# Also check total
print(f"\nTotal actors: {len(actors)}")
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]
print(f"StaticMeshActors: {len(sma)}")

# First 20 SMA names
for a in sma[:20]:
    loc = a.get_actor_location()
    print(f"  {a.get_actor_label()} @[{loc.x:.0f},{loc.y:.0f},{loc.z:.0f}]")
