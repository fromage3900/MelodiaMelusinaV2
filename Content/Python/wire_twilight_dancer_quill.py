"""Bind the compiled Twilight Dancer Quill scene to the existing NPC placeholder.

Run only from the Unreal Editor after the native build and Quill asset compile.
This script changes only the existing NPC interaction component's Quill fields;
it does not create actors, edit UI assets, or author quest/reward data.
"""

import unreal

ACTOR_LABEL = "MelodiaNPC_MD_01_TwilightDancer"
SCRIPT_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaQuillTwilightDancer"


def main() -> bool:
    script = unreal.load_asset(SCRIPT_PATH)
    if script is None:
        raise RuntimeError(f"Missing compiled Twilight Dancer QuillScript: {SCRIPT_PATH}")

    actor = next(
        (candidate for candidate in unreal.EditorLevelLibrary.get_all_level_actors()
         if candidate.get_actor_label() == ACTOR_LABEL),
        None,
    )
    if actor is None:
        raise RuntimeError(f"Missing existing Twilight Dancer actor: {ACTOR_LABEL}")

    interaction = actor.get_editor_property("interaction")
    if interaction is None:
        raise RuntimeError(f"Twilight Dancer actor has no interaction component: {ACTOR_LABEL}")

    interaction.set_editor_property("quill_dialogue", script)
    interaction.set_editor_property("quill_starting_label", unreal.Name("Start"))
    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Failed to save the Twilight Dancer actor binding")

    unreal.log(f"MELUSINA_TWILIGHT_DANCER_QUILL_WIRED actor={ACTOR_LABEL} script={SCRIPT_PATH}")
    return True


if __name__ == "__main__":
    main()
