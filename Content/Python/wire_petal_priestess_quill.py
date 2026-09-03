"""Bind the compiled Petal Priestess Quill scene to the existing Zen Forest NPC.

Run only after the closed-editor native build that adds QuillDialogue to
UMelodiaNPCInteractionComponent. This script changes no transforms, meshes,
lighting, landscape, or quest/battle data.
"""

import unreal

ACTOR_LABEL = "MelodiaNPC_SD_02_PetalPriestess"
SCRIPT_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess"


def main() -> bool:
    script = unreal.load_asset(SCRIPT_PATH)
    if script is None:
        raise RuntimeError(f"Missing compiled Priestess Quill asset: {SCRIPT_PATH}")

    actor = next(
        (candidate for candidate in unreal.EditorLevelLibrary.get_all_level_actors()
         if candidate.get_actor_label() == ACTOR_LABEL),
        None,
    )
    if actor is None:
        raise RuntimeError(f"Missing existing Priestess actor: {ACTOR_LABEL}")

    interaction = actor.get_editor_property("interaction")
    if interaction is None:
        raise RuntimeError("Priestess actor has no Melodia NPC interaction component")

    interaction.set_editor_property("quill_dialogue", script)
    interaction.set_editor_property("quill_starting_label", unreal.Name("Start"))
    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Failed to save the Priestess actor binding")

    unreal.log(f"MELUSINA_PRIESTESS_QUILL_WIRED actor={ACTOR_LABEL} script={SCRIPT_PATH}")
    return True


if __name__ == "__main__":
    main()
