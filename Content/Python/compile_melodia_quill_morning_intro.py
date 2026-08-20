"""Compile the editable Morning -> KaleidoNave opening Quill source.

Run inside Unreal Editor after a native build.  The script is intentionally
editor-backed: offline checks live in Tools/test_melodia_first_dream_route_contract.py,
while this file owns the source-to-uasset materialization step and readback.
"""

from pathlib import Path

import unreal


ASSET_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaMorningIntro"
TEMPLATE_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess"
SOURCE_PATH = (
    Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()))
    / "MelodiaIntegration"
    / "Narrative"
    / "MelodiaMorningIntro.qsc"
)

EXPECTED_DIALOGUE_MARKERS = (
    "The festival banners are down.",
    "The perch is empty again.",
    "Sir flew off for snacks again.",
    "The quiet petal answers.",
    "I'll keep the seat warm.",
)
EXPECTED_CHOICE_MARKERS = (
    "Follow the quiet chirp.",
    "Wait and listen.",
)
EXPECTED_PERSISTENT_VARIABLES = ("melodia_met_melodious",)
EXPECTED_DEPARTURE_CALL = "$ %melodia_morning_sir.BeginWindowDeparture"
FORBIDDEN_AUTHORITY_MARKERS = (
    "OpenLevel",
    "SaveGame",
    "melodia:travel:",
    "melodia:battle:",
)


if not SOURCE_PATH.is_file():
    raise RuntimeError(f"Missing checked-in QuillScript source: {SOURCE_PATH}")

source = SOURCE_PATH.read_text(encoding="utf-8")

for marker in EXPECTED_DIALOGUE_MARKERS + EXPECTED_CHOICE_MARKERS:
    if source.count(marker) != 1:
        raise RuntimeError(f"Expected exactly one MorningIntro marker '{marker}'")

if source.count(EXPECTED_DEPARTURE_CALL) != 1:
    raise RuntimeError("MorningIntro must call the tagged Sir departure exactly once")
if source.count("$ End") != 1:
    raise RuntimeError("MorningIntro must have exactly one terminal End")
for variable in EXPECTED_PERSISTENT_VARIABLES:
    if variable not in source:
        raise RuntimeError(f"Missing persistent MorningIntro variable '{variable}'")
if any(marker in source for marker in FORBIDDEN_AUTHORITY_MARKERS):
    raise RuntimeError(
        "MorningIntro must not own save, map, travel-intent, or battle authority"
    )
if "$ melodia_met_melodious = off" in source:
    raise RuntimeError("MorningIntro must not overwrite loaded narrative state")

asset = unreal.load_asset(ASSET_PATH)
if asset is None:
    template = unreal.load_asset(TEMPLATE_PATH)
    if template is None:
        raise RuntimeError(f"Missing QuillScript template: {TEMPLATE_PATH}")
    asset = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(
        "MelodiaMorningIntro",
        "/Game/MelodiaIntegration/Narrative",
        template,
    )
if asset is None:
    raise RuntimeError(f"Could not load or create QuillScript asset: {ASSET_PATH}")

if not unreal.MelodiaNarrativeSubsystem.compile_quill_source(asset, source):
    raise RuntimeError("CompileQuillSource rejected the checked-in MorningIntro source")

compiled_source = asset.get_editor_property("source_code")
if compiled_source.replace("\r\n", "\n") != source.replace("\r\n", "\n"):
    raise RuntimeError("Compiled MorningIntro source does not match the checked-in .qsc")

statements = asset.get_editor_property("statements")
for marker in EXPECTED_DIALOGUE_MARKERS + EXPECTED_CHOICE_MARKERS:
    matching = [
        statement
        for statement in statements
        if marker in str(statement.get_editor_property("text"))
    ]
    if len(matching) != 1:
        raise RuntimeError(
            f"Expected exactly one compiled MorningIntro statement for '{marker}', "
            f"found {len(matching)}"
        )
departure_matches = [
    statement
    for statement in statements
    if EXPECTED_DEPARTURE_CALL in statement.get_editor_property("source_line")
]
if len(departure_matches) != 1:
    raise RuntimeError(
        "Expected exactly one compiled MorningIntro departure statement, "
        f"found {len(departure_matches)}"
    )

if not unreal.EditorAssetLibrary.save_loaded_asset(asset, False):
    raise RuntimeError("Failed to save compiled MorningIntro QuillScript asset")

unreal.log(
    "MELUSINA_MORNING_INTRO_QUILL_COMPILED "
    f"source={SOURCE_PATH} statements={len(statements)} "
    f"dialogue_markers={len(EXPECTED_DIALOGUE_MARKERS)} choices={len(EXPECTED_CHOICE_MARKERS)}"
)
