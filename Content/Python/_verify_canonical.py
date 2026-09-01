import unreal
import json

# Check CanonicalLandscape Z vs Cathedral pieces
actors = unreal.EditorLevelLibrary.get_all_level_actors()

canonical = None
sma = []
for a in actors:
    if "CanonicalLandscape" in a.get_actor_label():
        canonical = a
    if type(a).__name__ == "StaticMeshActor":
        sma.append(a)

if canonical:
    loc = canonical.get_actor_location()
    print(f"CanonicalLandscape Z: {loc.z:.0f}")

if sma:
    first = sma[0].get_actor_location()
    print(f"First SMA Z: {first.z:.0f}")
    print(f"Difference: {first.z - loc.z:.0f}")

print(f"\nTotal SMAs: {len(sma)}")
print(f"Canonical visible: {canonical is not None}")
