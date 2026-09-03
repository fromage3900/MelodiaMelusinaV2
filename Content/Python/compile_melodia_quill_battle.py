from pathlib import Path

import unreal

ASSET_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaQuillSmoke"
SOURCE_PATH = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())) / "MelodiaIntegration" / "Narrative" / "MelodiaQuillSmoke.qsc"
EXPECTED_NOTIFICATIONS = (
    "$ Notify melodia:battle:melodia_smoke_encounter",
    "$ Notify melodia:flag:melodia_smoke_complete:true",
    "$ Notify melodia:quest:melodia_q_echo_01",
    "$ Notify melodia:reward:melodia_smoke_reward",
)
EXPECTED_POST_BATTLE_LINES = (
    "Victory. The dream remembers your courage",
    "The dream releases you gently",
    "We escaped with the melody intact",
)
EXPECTED_PERSISTENT_VARIABLES = (
    "melodia_met_melodious",
    "melodia_first_dream_resolved",
    "melodia_battle_result",
)

if not SOURCE_PATH.is_file():
    raise RuntimeError(f"Missing checked-in QuillScript source: {SOURCE_PATH}")

source = SOURCE_PATH.read_text(encoding="utf-8")
asset = unreal.load_asset(ASSET_PATH)
if asset is None:
    raise RuntimeError(f"Missing QuillScript asset: {ASSET_PATH}")

for notification in EXPECTED_NOTIFICATIONS:
    count = source.count(notification)
    if count != 1:
        raise RuntimeError(f"Expected exactly one authored notification '{notification}', found {count}")
for line in EXPECTED_POST_BATTLE_LINES:
    if line not in source:
        raise RuntimeError(f"Missing authored post-battle dialogue marker: {line}")
if source.count("{melodia_battle_result} == victory") != 1:
    raise RuntimeError("Expected exactly one Victory result branch")
if source.count("{melodia_battle_result} == defeat") != 1:
    raise RuntimeError("Expected exactly one Defeat result branch")
if source.count("{melodia_battle_result} == fled") != 1:
    raise RuntimeError("Expected exactly one Fled result branch")
if source.count("The battle could not begin") != 1:
    raise RuntimeError("Expected exactly one fail-closed unavailable battle acknowledgement")
victory_start = source.index("? if: {melodia_battle_result} == victory")
victory_end = source.index("? else:", victory_start)
quest_notification = source.index("$ Notify melodia:quest:melodia_q_echo_01")
if not victory_start < quest_notification < victory_end:
    raise RuntimeError("Quest 1 completion must be authored only in the Victory branch")
for variable in EXPECTED_PERSISTENT_VARIABLES:
    if variable not in source:
        raise RuntimeError(f"Expected persistent Melodia variable '{variable}'")
if "$ met_melodious = off" in source or "$ first_dream_resolved = off" in source:
    raise RuntimeError("Quill source must not overwrite loaded narrative state at scene start")

if not unreal.MelodiaNarrativeSubsystem.compile_quill_source(asset, source):
    raise RuntimeError("CompileQuillSource rejected the checked-in authored source")

compiled_source = asset.get_editor_property("source_code")
if compiled_source.replace("\r\n", "\n") != source.replace("\r\n", "\n"):
    raise RuntimeError("Compiled asset source does not exactly match the checked-in .qsc source")

statements = asset.get_editor_property("statements")
for notification in EXPECTED_NOTIFICATIONS:
    matching = [
        statement
        for statement in statements
        if notification in statement.get_editor_property("source_line")
    ]
    if len(matching) != 1:
        raise RuntimeError(f"Expected exactly one compiled statement for '{notification}', found {len(matching)}")

if not unreal.EditorAssetLibrary.save_loaded_asset(asset, False):
    raise RuntimeError("Failed to save compiled QuillScript asset")

unreal.log(
    f"MELUSINA_QUILL_COMPILED: source={SOURCE_PATH} statements={len(statements)} "
    f"notifications={len(EXPECTED_NOTIFICATIONS)} post_battle_lines={len(EXPECTED_POST_BATTLE_LINES)}"
)
