from pathlib import Path

import unreal

ASSET_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaQuillTwilightDancer"
TEMPLATE_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess"
SOURCE_PATH = (
    Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()))
    / "MelodiaIntegration"
    / "Narrative"
    / "MelodiaQuillTwilightDancer.qsc"
)

if not SOURCE_PATH.is_file():
    raise RuntimeError(f"Missing checked-in QuillScript source: {SOURCE_PATH}")

source = SOURCE_PATH.read_text(encoding="utf-8")
if source.count("melodia:quest:melodia_q_echo_03") != 1:
    raise RuntimeError("Twilight Dancer must issue exactly one q_echo_03 acceptance intent")
for token in ("melodia_q_echo_02_complete", "melodia_q_echo_03_complete"):
    if token not in source:
        raise RuntimeError(f"Missing persistent Twilight Dancer state token '{token}'")

asset = unreal.load_asset(ASSET_PATH)
if asset is None:
    template = unreal.load_asset(TEMPLATE_PATH)
    if template is None:
        raise RuntimeError(f"Missing QuillScript template: {TEMPLATE_PATH}")
    asset = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(
        "MelodiaQuillTwilightDancer", "/Game/MelodiaIntegration/Narrative", template
    )
if asset is None:
    raise RuntimeError("Could not create Twilight Dancer QuillScript asset")

if not unreal.MelodiaNarrativeSubsystem.compile_quill_source(asset, source):
    raise RuntimeError("CompileQuillSource rejected Twilight Dancer dialogue")
if not unreal.EditorAssetLibrary.save_loaded_asset(asset, False):
    raise RuntimeError("Failed to save compiled Twilight Dancer QuillScript asset")

unreal.log(
    "MELUSINA_TWILIGHT_DANCER_QUILL_COMPILED "
    f"statements={len(asset.get_editor_property('statements'))}"
)
