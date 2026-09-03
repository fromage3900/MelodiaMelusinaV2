from pathlib import Path

import unreal

ASSET_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess"
SOURCE_PATH = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())) / "MelodiaIntegration" / "Narrative" / "MelodiaQuillPetalPriestess.qsc"

if not SOURCE_PATH.is_file():
    raise RuntimeError(f"Missing checked-in QuillScript source: {SOURCE_PATH}")

source = SOURCE_PATH.read_text(encoding="utf-8")
asset = unreal.load_asset(ASSET_PATH)
if asset is None:
    raise RuntimeError(f"Missing QuillScript asset: {ASSET_PATH}")

if source.count("melodia:quest:melodia_q_echo_01") != 1:
    raise RuntimeError("The Priestess must issue exactly one quest acceptance intent")
if source.count("melodia:stat:priestess_first_echo:melodia_harmony:1") != 1:
    raise RuntimeError("The Priestess Harmony answer must issue exactly one stable social-stat intent")
for token in ("melodia_priestess_greeted", "melodia_q_echo_01_complete", "HarmonyAnswer", "ListeningAnswer"):
    if token not in source:
        raise RuntimeError(f"Missing persistent Priestess state or choice token '{token}'")

if not unreal.MelodiaNarrativeSubsystem.compile_quill_source(asset, source):
    raise RuntimeError("CompileQuillSource rejected Priestess dialogue")

if not unreal.EditorAssetLibrary.save_loaded_asset(asset, False):
    raise RuntimeError("Failed to save compiled Petal Priestess QuillScript asset")

unreal.log(f"MELUSINA_PRIESTESS_QUILL_COMPILED statements={len(asset.get_editor_property('statements'))}")
