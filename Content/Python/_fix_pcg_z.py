import unreal

# Move PCG volumes to match landscape Z
actors = unreal.EditorLevelLibrary.get_all_level_actors()

for a in actors:
    if type(a).__name__ == "PCGVolume":
        loc = a.get_actor_location()
        # Move to landscape Z + offset
        a.set_actor_location(unreal.Vector(loc.x, loc.y, 13500), False, False)
        print(f"Moved {a.get_actor_label()} to Z=13500")

unreal.EditorLevelLibrary.save_current_level()
print("Saved.")
