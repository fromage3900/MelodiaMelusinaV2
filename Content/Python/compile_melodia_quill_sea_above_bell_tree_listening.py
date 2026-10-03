from pathlib import Path

import unreal

ASSET_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaQuillSeaAboveBellTreeListening"
TEMPLATE_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess"
SOURCE_PATH = (
    Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()))
    / "MelodiaIntegration"
    / "Narrative"
    / "MelodiaQuillSeaAboveBellTreeListening.qsc"
)

if not SOURCE_PATH.is_file():
    raise RuntimeError(f"Missing checked-in QuillScript source: {SOURCE_PATH}")

source = SOURCE_PATH.read_text(encoding="utf-8")
for label in ("<@> Answer", "<@> Wait", "<@> Resolve"):
    if source.count(label) != 1:
        raise RuntimeError(f"Bell Tree Listening must define '{label}' exactly once")

asset = unreal.load_asset(ASSET_PATH)
if asset is None:
    template = unreal.load_asset(TEMPLATE_PATH)
    if template is None:
        raise RuntimeError(f"Missing QuillScript template: {TEMPLATE_PATH}")
    asset = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(
        "MelodiaQuillSeaAboveBellTreeListening", "/Game/MelodiaIntegration/Narrative", template
    )
if asset is None:
    raise RuntimeError("Could not create Bell Tree Listening QuillScript asset")

if not unreal.MelodiaNarrativeSubsystem.compile_quill_source(asset, source):
    raise RuntimeError("CompileQuillSource rejected Bell Tree Listening dialogue")
if not unreal.EditorAssetLibrary.save_loaded_asset(asset, False):
    raise RuntimeError("Failed to save compiled Bell Tree Listening QuillScript asset")

unreal.log(
    "MELUSINA_BELL_TREE_LISTENING_QUILL_COMPILED "
    f"statements={len(asset.get_editor_property('statements'))}"
)
