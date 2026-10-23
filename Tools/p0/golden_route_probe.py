"""Diagnostic: how does the editor's Python reach a GAME INSTANCE subsystem, and what
carries the Quill beat?

Runs inside PIE (the game instance only exists there).
"""
import unreal

print("GOLDEN_ROUTE unreal_subsystem_names=%s" % [
    n for n in dir(unreal) if "ubsystem" in n][:40])

for klass in ("GameInstance", "World", "Actor"):
    try:
        names = [n for n in dir(getattr(unreal, klass)) if "ubsystem" in n.lower()]
        print("GOLDEN_ROUTE unreal.%s.subsystem_members=%s" % (klass, names))
    except Exception as exc:  # noqa: BLE001
        print("GOLDEN_ROUTE unreal.%s unavailable %s" % (klass, exc))

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
print("GOLDEN_ROUTE world=%s" % (world.get_name() if world else "NONE"))
if world:
    gi = unreal.GameplayStatics.get_game_instance(world)
    print("GOLDEN_ROUTE gi=%s class=%s" % (gi.get_name(), gi.get_class().get_name()))
    for name in dir(gi):
        if "ubsystem" in name.lower():
            print("GOLDEN_ROUTE gi_member=%s" % name)
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    for actor in actors:
        label = actor.get_actor_label() if hasattr(actor, "get_actor_label") else ""
        cname = actor.get_class().get_name()
        blob = (actor.get_name() + " " + label + " " + cname).lower()
        if any(k in blob for k in ("quill", "priestess", "petal", "npc", "dialog", "story")):
            print("GOLDEN_ROUTE story_actor=%s label=%s class=%s" % (
                actor.get_name(), label, cname))
    for actor in actors:
        if "Melusina" in actor.get_name():
            for comp in actor.get_components_by_class(unreal.ActorComponent):
                cn = comp.get_class().get_name()
                if "Narrative" in cn or "Quill" in cn or "Melodia" in cn:
                    print("GOLDEN_ROUTE pawn_component=%s" % cn)
