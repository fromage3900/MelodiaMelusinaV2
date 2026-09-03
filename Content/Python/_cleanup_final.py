import unreal

# ============================================================
# CLEANUP: Delete proxies, move CanonicalLandscape to match cathedral
# ============================================================

actors = unreal.EditorLevelLibrary.get_all_level_actors()

# 1. Delete proxy/placeholder actors
proxy_keywords = ["Proxy", "CentralCore", "BellProxy"]
deleted = []
for a in actors:
    label = a.get_actor_label()
    for kw in proxy_keywords:
        if kw in label:
            unreal.EditorLevelLibrary.destroy_actor(a)
            deleted.append(label)
            break

print(f"Deleted {len(deleted)} proxies:")
for d in deleted:
    print(f"  {d}")

# 2. Move CanonicalLandscape down to match cathedral base (Z=13405)
for a in actors:
    if "CanonicalLandscape" in a.get_actor_label():
        loc = a.get_actor_location()
        # Move from Z=24810 to Z=13405 (difference: -11405)
        a.set_actor_location(unreal.Vector(loc.x, loc.y, 13405), False, False)
        print(f"\nMoved CanonicalLandscape to Z=13405")
        break

unreal.EditorLevelLibrary.save_current_level()
print("Saved.")
