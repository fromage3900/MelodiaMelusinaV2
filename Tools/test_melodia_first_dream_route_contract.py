#!/usr/bin/env python3
"""Offline contract checks for the player-facing First Dream source route.

This suite deliberately does not contact Unreal, Monolith, PIE, or the shared
contract runner.  It proves source/spec alignment only; editor compilation,
asset readback, and golden-run evidence remain live gates.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NARRATIVE_DIR = ROOT / "Content" / "MelodiaIntegration" / "Narrative"
MORNING_SOURCE = NARRATIVE_DIR / "MelodiaMorningIntro.qsc"
MORNING_ASSET = NARRATIVE_DIR / "MelodiaMorningIntro.uasset"
MORNING_COMPILER = ROOT / "Content" / "Python" / "compile_melodia_quill_morning_intro.py"
SMOKE_SOURCE = NARRATIVE_DIR / "MelodiaQuillSmoke.qsc"
SMOKE_COMPILER = ROOT / "Content" / "Python" / "compile_melodia_quill_battle.py"
ROUTE_SPEC = ROOT / "specs" / "p0" / "core_p0_dream_golden_run.v1.json"
NARRATIVE_HEADER = (
    ROOT
    / "Source"
    / "BS_GodFile"
    / "MelodiaIntegration"
    / "MelodiaNarrativeSubsystem.h"
)
NARRATIVE_CPP = (
    ROOT
    / "Source"
    / "BS_GodFile"
    / "MelodiaIntegration"
    / "MelodiaNarrativeSubsystem.cpp"
)
PERSONA_CPP = (
    ROOT
    / "Source"
    / "BS_GodFile"
    / "MelodiaIntegration"
    / "MelodiaPersonaSubsystem.cpp"
)
BRIDGE_CPP = (
    ROOT
    / "Source"
    / "BS_GodFile"
    / "MelodiaIntegration"
    / "MelodiaExternalJRPGBridgeSubsystem.cpp"
)
SIR_HEADER = (
    ROOT
    / "Plugins"
    / "MelodiaCore"
    / "Source"
    / "MelodiaCore"
    / "MelodiaSirMelodiousIntroActor.h"
)

NOTIFY_RE = re.compile(
    r"\$ Notify (melodia:(?:battle|quest|flag|travel|reward|stat|item):"
    r"[A-Za-z0-9_./+\-]+(?::[A-Za-z0-9_./+\-]+){0,3})"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_count(text: str, marker: str, expected: int = 1) -> None:
    require(
        text.count(marker) == expected,
        f"{marker!r}: expected {expected}, found {text.count(marker)}",
    )


def test_morning_source_and_materialization_path() -> None:
    source = read(MORNING_SOURCE)
    compiler = read(MORNING_COMPILER)

    require(MORNING_ASSET.is_file(), "the existing MorningIntro uasset is missing")
    for marker in (
        "The festival banners are down.",
        "The perch is empty again.",
        "Sir flew off for snacks again.",
        "The quiet petal answers.",
        "I'll keep the seat warm.",
        "Follow the quiet chirp.",
        "Wait and listen.",
        "$ %melodia_morning_sir.BeginWindowDeparture",
    ):
        require_count(source, marker)

    require_count(source, "$ End")
    require("$ melodia_met_melodious = off" not in source, "source resets loaded state")
    for forbidden in ("OpenLevel", "SaveGame", "melodia:travel:", "melodia:battle:"):
        require(forbidden not in source, f"Morning source owns forbidden authority: {forbidden}")

    for marker in (
        'ASSET_PATH = "/Game/MelodiaIntegration/Narrative/MelodiaMorningIntro"',
        "TEMPLATE_PATH",
        "SOURCE_PATH",
        "compile_quill_source",
        "save_loaded_asset",
    ):
        require(marker in compiler, f"Morning compile path is missing {marker!r}")


def test_smoke_consequence_completes_quest_through_quill() -> None:
    source = read(SMOKE_SOURCE)
    compiler = read(SMOKE_COMPILER)

    for marker in (
        "$ Notify melodia:battle:melodia_smoke_encounter",
        "$ Notify melodia:flag:melodia_smoke_complete:true",
        "$ Notify melodia:quest:melodia_q_echo_01",
        "$ Notify melodia:reward:melodia_smoke_reward",
    ):
        require_count(source, marker)
        require(marker in compiler, f"Smoke compiler does not require {marker!r}")

    victory_start = source.index("? if: {melodia_battle_result} == victory")
    victory_end = source.index("? else:", victory_start)
    quest_position = source.index("$ Notify melodia:quest:melodia_q_echo_01")
    require(
        victory_start < quest_position < victory_end,
        "quest 1 completion must remain in the Smoke Victory branch",
    )
    for result in ("victory", "defeat", "fled"):
        require_count(source, f"{{melodia_battle_result}} == {result}")
    require_count(source, "The battle could not begin")


def test_notifications_and_native_route_are_single_authority() -> None:
    notification_sources = sorted(NARRATIVE_DIR.glob("*.qsc"))
    require(notification_sources, "no checked-in narrative sources found")
    for path in notification_sources:
        text = read(path)
        for token in NOTIFY_RE.findall(text):
            parts = token.split(":")
            if parts[1] == "flag":
                require(len(parts) == 4, f"{path.name}: malformed flag intent {token}")
                require(parts[3] in ("true", "false"), f"{path.name}: malformed flag value")
            elif parts[1] == "stat":
                require(len(parts) == 5, f"{path.name}: malformed stat intent {token}")
            elif parts[1] == "item":
                require(
                    len(parts) == 5 and parts[2] == "give",
                    f"{path.name}: malformed item intent {token}",
                )
            else:
                require(len(parts) == 3, f"{path.name}: malformed intent {token}")

    narrative_header = read(NARRATIVE_HEADER)
    narrative_cpp = read(NARRATIVE_CPP)
    bridge_cpp = read(BRIDGE_CPP)
    persona_cpp = read(PERSONA_CPP)

    require("UFUNCTION()\n\tvoid HandleQuillNotification" in narrative_header,
            "Quill notification callback is not reflected")
    require("Quill->OnNotified.AddUniqueDynamic" in narrative_cpp,
            "Quill notification delegate is not bound")
    require("OnBattleRequested.Broadcast(EncounterId)" in narrative_cpp,
            "battle intent does not leave NarrativeSubsystem")
    require("NarrativeSubsystem->CompleteBattle(MelodiaResult)" in bridge_cpp,
            "stock battle result does not return to NarrativeSubsystem")
    require("ActorHasTag(EncounterId)" in bridge_cpp,
            "battle adapter does not use the canonical raw encounter tag")
    require("Encounter_CrystalShard" not in persona_cpp,
            "stale encounter-specific quest authority remains in Persona")
    require(
        'CompleteQuest(TEXT("melodia_q_echo_01"))' not in persona_cpp,
        "battle presentation observer still completes a quest directly",
    )


def test_route_spec_and_native_default_agree() -> None:
    spec = json.loads(read(ROUTE_SPEC))
    route = spec["map_authority"]["player_route"]
    require(
        route == [
            "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
            "/Game/EnvSandbox/Environments/L_KaleidoNave",
        ],
        f"player route drifted: {route}",
    )
    require("/Game/L_Melodia_Dreamstate" in spec["map_authority"]["retired_route_legs"],
            "retired Dreamstate route leg is not recorded")

    sir_header = read(SIR_HEADER)
    require(
        'DepartureDestinationLevel = TEXT("/Game/EnvSandbox/Environments/L_KaleidoNave")'
        in sir_header,
        "native Sir departure default does not match the live player route",
    )


def main() -> int:
    tests = (
        test_morning_source_and_materialization_path,
        test_smoke_consequence_completes_quest_through_quill,
        test_notifications_and_native_route_are_single_authority,
        test_route_spec_and_native_default_agree,
    )
    for test in tests:
        test()
    print(f"validated {len(tests)} First Dream source-route contract checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
