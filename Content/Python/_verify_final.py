import unreal

# Verify CanonicalLandscape is visible and in place
actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in actors:
    if "CanonicalLandscape" in a.get_actor_label():
        hidden = a.get_editor_property("bHidden")
        loc = a.get_actor_location()
        print(f"CanonicalLandscape: hidden={hidden}, Z={loc.z:.0f}")
        break

# Confirm no Gaea terrain is visible
gaea_visible = False
for a in actors:
    if "Gaea" in a.get_actor_label():
        hidden = a.get_editor_property("bHidden")
        loc = a.get_actor_location()
        print(f"Gaea: hidden={hidden}, Z={loc.z:.0f}")
        if not hidden:
            gaea_visible = True

if not gaea_visible:
    print("Gaea terrain is hidden - good.")

# State
sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]
print(f"\nTotal actors: {len(actors)}")
print(f"Cathedral SMAs: {len(sma)}")
