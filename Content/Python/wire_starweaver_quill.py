import unreal

ACTOR_LABEL = "MelodiaNPC_CW_01_StarWeaver"
SCRIPT_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaQuillStarWeaver"

script = unreal.load_asset(SCRIPT_PATH)
if script is None:
    raise RuntimeError(f"Missing compiled Star Weaver QuillScript: {SCRIPT_PATH}")

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
actor = next((item for item in actors if item.get_actor_label() == ACTOR_LABEL), None)
if actor is None:
    raise RuntimeError(f"Missing Zen Forest actor: {ACTOR_LABEL}")

component = next((item for item in actor.get_components_by_class(unreal.ActorComponent) if item.get_name() == "Interaction"), None)
if component is None:
    raise RuntimeError(f"Missing Interaction component on {ACTOR_LABEL}")

component.set_editor_property("quill_dialogue", script)
component.set_editor_property("quill_starting_label", "Start")
actor.modify()

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Failed to save current level after Star Weaver wiring")

unreal.log("MELUSINA_STAR_WEAVER_QUILL_WIRED")
