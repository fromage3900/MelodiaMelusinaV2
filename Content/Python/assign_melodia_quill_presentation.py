"""Assign the canonical Melodia Quill presentation to active narrative scenes.

Run inside Unreal Editor after a successful native build and compilation of the
four WBP classes. Quill remains lifecycle and progression authority; this script
only assigns presentation classes and verifies saved readback.
"""
import unreal

SCENES = (
    "/Game/MelodiaIntegration/Narrative/MelodiaMorningIntro",
    "/Game/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess",
    "/Game/MelodiaIntegration/Narrative/MelodiaQuillSmoke",
    "/Game/MelodiaIntegration/Narrative/MelodiaQuillStarWeaver",
    "/Game/MelodiaIntegration/Narrative/MelodiaQuillTwilightDancer",
    "/Game/MelodiaIntegration/Narrative/MelodiaQuillDawnVeil",
    "/Game/MelodiaIntegration/Narrative/MelodiaQuillSolsticeDrum",
    "/Game/MelodiaIntegration/Narrative/MelodiaQuillHarmonyAwakening",
)
DIALOG_CLASS = "/Game/Melodia/UI/Quill/WBP_MelodiaQuillDialog.WBP_MelodiaQuillDialog_C"
CHOICE_CLASS = "/Game/Melodia/UI/Quill/WBP_MelodiaQuillChoiceEntry.WBP_MelodiaQuillChoiceEntry_C"
SELECTION_CLASS = "/Game/Melodia/UI/Quill/WBP_MelodiaQuillSelection.WBP_MelodiaQuillSelection_C"
BACKGROUND_CLASS = "/Game/Melodia/UI/Quill/WBP_MelodiaQuillBackground.WBP_MelodiaQuillBackground_C"


def require_asset(path):
    asset = unreal.load_asset(path)
    if asset is None:
        raise RuntimeError(f"Missing required asset: {path}")
    return asset


def require_class(path):
    cls = unreal.load_class(None, path)
    if cls is None:
        raise RuntimeError(f"Missing generated class (compile its WBP first): {path}")
    return cls


dialog_class = require_class(DIALOG_CLASS)
choice_class = require_class(CHOICE_CLASS)
selection_class = require_class(SELECTION_CLASS)
background_class = require_class(BACKGROUND_CLASS)
selection_cdo = unreal.get_default_object(selection_class)
selection_cdo.set_editor_property("choice_entry_class", choice_class)

expected = {
    "dialog_box_class": dialog_class,
    "selection_box_class": selection_class,
    "background_box_class": background_class,
}
assigned = []
for scene_path in SCENES:
    scene = require_asset(scene_path)
    settings = scene.get_editor_property("settings")
    for property_name, presentation_class in expected.items():
        settings.set_editor_property(property_name, presentation_class)
    scene.set_editor_property("settings", settings)
    if not unreal.EditorAssetLibrary.save_loaded_asset(scene, False):
        raise RuntimeError(f"Failed to save Quill scene: {scene_path}")

    readback = scene.get_editor_property("settings")
    for property_name, presentation_class in expected.items():
        actual = readback.get_editor_property(property_name)
        if actual != presentation_class:
            raise RuntimeError(
                f"Readback mismatch {scene_path}.{property_name}: {actual} != {presentation_class}"
            )
    assigned.append(scene_path)

selection_wbp = require_asset("/Game/Melodia/UI/Quill/WBP_MelodiaQuillSelection")
if not unreal.EditorAssetLibrary.save_loaded_asset(selection_wbp, False):
    raise RuntimeError("Failed to save WBP_MelodiaQuillSelection")
actual_choice = unreal.get_default_object(selection_class).get_editor_property("choice_entry_class")
if actual_choice != choice_class:
    raise RuntimeError(f"Readback mismatch for choice_entry_class: {actual_choice} != {choice_class}")

unreal.log(
    "MELODIA_QUILL_PRESENTATION_ASSIGNED "
    f"scenes={len(assigned)} dialog={dialog_class.get_name()} "
    f"selection={selection_class.get_name()} choice={choice_class.get_name()} "
    f"background={background_class.get_name()} paths={assigned}"
)
