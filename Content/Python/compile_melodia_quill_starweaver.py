from pathlib import Path

import unreal

ASSET_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaQuillStarWeaver"
TEMPLATE_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess"
SOURCE_PATH = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())) / "MelodiaIntegration" / "Narrative" / "MelodiaQuillStarWeaver.qsc"

if not SOURCE_PATH.is_file():
    raise RuntimeError(f"Missing checked-in QuillScript source: {SOURCE_PATH}")

source = SOURCE_PATH.read_text(encoding="utf-8")
if source.count("melodia:quest:melodia_q_echo_02") != 1:
    raise RuntimeError("Star Weaver must issue exactly one q_echo_02 intent per interaction")
for token in ("melodia_q_echo_01_complete", "melodia_q_echo_02_complete"):
    if token not in source:
        raise RuntimeError(f"Missing persistent Star Weaver state token '{token}'")

asset = unreal.load_asset(ASSET_PATH)
if asset is None:
    template = unreal.load_asset(TEMPLATE_PATH)
    if template is None:
        raise RuntimeError(f"Missing QuillScript template: {TEMPLATE_PATH}")
    asset = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(
        "MelodiaQuillStarWeaver", "/Game/MelodiaIntegration/Narrative", template
    )
if asset is None:
    raise RuntimeError("Could not create Star Weaver QuillScript asset")

if not unreal.MelodiaNarrativeSubsystem.compile_quill_source(asset, source):
    raise RuntimeError("CompileQuillSource rejected Star Weaver dialogue")
if not unreal.EditorAssetLibrary.save_loaded_asset(asset, False):
    raise RuntimeError("Failed to save compiled Star Weaver QuillScript asset")

unreal.log(f"MELUSINA_STAR_WEAVER_QUILL_COMPILED statements={len(asset.get_editor_property('statements'))}")
