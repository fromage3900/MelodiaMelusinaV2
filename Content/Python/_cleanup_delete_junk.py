import unreal

# ============================================================
# SEA ABOVE CLEANUP — Delete junk, snap to landscape
# ============================================================

actors = unreal.EditorLevelLibrary.get_all_level_actors()

# 1. Delete junk assets
junk_keywords = ["Sphere", "Plane", "Reef_", "Flora_", "Kelp_", "Coral_", "Starfish", "HayStack"]
deleted = []
for a in actors:
    label = a.get_actor_label()
    for kw in junk_keywords:
        if kw in label:
            unreal.EditorLevelLibrary.destroy_actor(a)
            deleted.append(label)
            break

print(f"Deleted {len(deleted)} junk actors:")
for d in deleted[:10]:
    print(f"  {d}")
if len(deleted) > 10:
    print(f"  ... +{len(deleted)-10} more")

unreal.EditorLevelLibrary.save_current_level()
print("Saved")
