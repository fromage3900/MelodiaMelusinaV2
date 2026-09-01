import unreal

# ============================================================
# HEIGHT-AWARE CLEANUP - Snap pieces to landscape surface
# ============================================================

actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Find landscape
landscape = None
for a in actors:
    if "CanonicalLandscape" in a.get_actor_label():
        landscape = a
        break

if landscape is None:
    print("[FATAL] CanonicalLandscape not found")
    exit()

landscape_z = landscape.get_actor_location().z
print(f"Landscape Z: {landscape_z:.0f}")

# Get all StaticMeshActors
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]
print(f"Total SMAs: {len(sma)}")

# Snap all pieces to sit on landscape
# Use a small offset so pieces don't z-fight with ground
offset = 50  # Small offset above ground

moved = 0
for a in sma:
    loc = a.get_actor_location()
    # Keep X,Y but set Z to landscape + offset
    new_z = landscape_z + offset
    
    # Only move if significantly off
    if abs(loc.z - new_z) > 100:
        a.set_actor_location(unreal.Vector(loc.x, loc.y, new_z), False, False)
        moved += 1

print(f"Moved {moved} pieces to Z={new_z:.0f}")

unreal.EditorLevelLibrary.save_current_level()
print("Saved")
