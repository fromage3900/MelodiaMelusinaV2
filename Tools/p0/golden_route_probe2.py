"""Diagnostic: the EXISTING routes for the narrative, the save and the Quill.

The golden run must use the house's own owners, not a re-implementation, so this probes
what is already callable.
"""
import unreal

print("GOLDEN_ROUTE unreal_game_instance=%s" % [
    n for n in dir(unreal) if "game_instance" in n.lower()][:14])
print("GOLDEN_ROUTE unreal_narrative=%s" % [
    n for n in dir(unreal) if "Narrative" in n][:14])
print("GOLDEN_ROUTE unreal_quill=%s" % [
    n for n in dir(unreal) if "Quill" in n][:14])

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if not world:
    print("GOLDEN_ROUTE world=NONE")
else:
    gi = unreal.GameplayStatics.get_game_instance(world)
    for label, holder in (("gi", gi),):
        try:
            calls = [n for n in dir(holder)
                     if any(k in n.lower() for k in ("save", "narrative", "travel", "quill", "slot", "record"))]
            print("GOLDEN_ROUTE %s_callables=%s" % (label, calls[:26]))
        except Exception as exc:  # noqa: BLE001
            print("GOLDEN_ROUTE %s error %s" % (label, exc))

    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    for actor in actors:
        if "Melusina" not in actor.get_name():
            continue
        calls = [n for n in dir(actor)
                 if any(k in n.lower() for k in ("save", "narrative", "travel", "quill", "slot"))]
        print("GOLDEN_ROUTE pawn_callables=%s" % calls[:26])
        for comp in actor.get_components_by_class(unreal.ActorComponent):
            cn = comp.get_class().get_name()
            if "Narrative" in cn or "Quill" in cn or "Save" in cn or "Magic" in cn:
                ccalls = [n for n in dir(comp)
                          if any(k in n.lower() for k in ("save", "narrative", "travel", "quill", "slot", "transform"))]
                print("GOLDEN_ROUTE component=%s callables=%s" % (cn, ccalls[:22]))
