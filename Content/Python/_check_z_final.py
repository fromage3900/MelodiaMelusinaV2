import unreal
import json

# Check all actor Z positions
actors = unreal.EditorLevelLibrary.get_all_level_actors()
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]

z_values = [a.get_actor_location().z for a in sma]
z_min = min(z_values)
z_max = max(z_values)
z_avg = sum(z_values) / len(z_values)

print(f"Cathedral Z range: {z_min:.0f} to {z_max:.0f}")
print(f"Cathedral Z avg: {z_avg:.0f}")
print(f"Landscape Z: 13405")

# Check PCG Z
pcg = [a for a in actors if type(a).__name__ == "PCGVolume"]
for vol in pcg:
    loc = vol.get_actor_location()
    print(f"\n{vol.get_actor_label()} Z: {loc.z:.0f}")

# Check reef pieces
reef = [a for a in sma if any(kw in a.get_actor_label() for kw in ["Reef_", "Flora_", "Kelp_", "Coral_", "Starfish"])]
print(f"\nReef pieces: {len(reef)}")
for r in reef[:5]:
    loc = r.get_actor_location()
    print(f"  {r.get_actor_label()} @Z={loc.z:.0f}")
