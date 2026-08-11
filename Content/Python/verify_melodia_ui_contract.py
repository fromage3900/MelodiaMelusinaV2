"""Read-only preflight for the Melodia battle HUD integration.

Run from the project root without Unreal Editor access:
    python Content/Python/verify_melodia_ui_contract.py
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "Saved" / "Melodia" / "ui_contract.json"

REQUIRED_ASSETS = (
    "Content/Melodia/UI/WBP_Battle_Rhythm.uasset",
    "Content/Melodia/UI/WBP_GradePop.uasset",
)

MOBILE_ASSET = "Content/Melodia/UI/WBP_Battle_Mobile.uasset"

MOBILE_ATLAS = (
    "Content/EnvSandbox/Textures/Source/MelodiaGameUI/T_Melodia_LanePress.png",
    "Content/EnvSandbox/Textures/Source/MelodiaGameUI/T_Melodia_SkillChipBG.png",
    "Content/EnvSandbox/Textures/Source/MelodiaGameUI/T_Melodia_MobileTopBar.png",
    "Content/EnvSandbox/Textures/Source/MelodiaGameUI/T_Melodia_SafeAreaMask.png",
    "Content/EnvSandbox/Textures/Source/MelodiaGameUI/T_Melodia_HighwayBG.png",
)

REQUIRED_HUD_EVENTS = (
    "SetHUDMode",
    "SetJudgment",
    "DoPulse",
    "TriggerSparkleBurst",
    "SetEnemyVitals",
    "SetPartyVitals",
    "SetSkillPoints",
    "SetUltimateGauge",
    "SetEnemyBreakGauge",
    "SetNoteHighwayActive",
    "ShowActionPrompt",
    "SetBattlePhaseBanner",
    "PushFloatingCombatText",
    "TriggerDamageFlash",
    "ShowBattleStatus",
)


def main() -> int:
    hud_header = ROOT / "Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmHUDWidget.h"
    hud_source = ROOT / "Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmHUDWidget.cpp"
    mobile_header = ROOT / "Plugins/MelodiaCore/Source/MelodiaCore/MelodiaMobileHUD.h"
    game_mode = ROOT / "Plugins/MelodiaCore/Source/MelodiaCore/MelodiaGameMode.cpp"

    checks: list[dict[str, object]] = []
    for relative_path in REQUIRED_ASSETS:
        path = ROOT / relative_path
        checks.append({
            "name": path.stem,
            "passed": path.is_file() and path.stat().st_size > 0,
            "detail": relative_path,
            "tier": "desktop",
        })

    header_text = hud_header.read_text(encoding="utf-8") if hud_header.is_file() else ""
    source_text = hud_source.read_text(encoding="utf-8") if hud_source.is_file() else ""
    for event_name in REQUIRED_HUD_EVENTS:
        checks.append({
            "name": f"hud_event_{event_name}",
            "passed": f"void {event_name}" in header_text and f"{event_name}_Implementation" in source_text,
            "detail": "Blueprint-native event available to WBP_Battle_Rhythm.",
            "tier": "desktop",
        })

    game_mode_text = game_mode.read_text(encoding="utf-8") if game_mode.is_file() else ""
    checks.append({
        "name": "game_mode_spawns_configured_hud",
        "passed": "CreateWidget<UMelodiaRhythmHUDWidget>" in game_mode_text,
        "detail": "MelodiaGameMode can spawn a configured UMelodiaRhythmHUDWidget subclass.",
        "tier": "desktop",
    })

    # --- Mobile Pass C preflight (soft: does not fail desktop ok) ---
    mobile_path = ROOT / MOBILE_ASSET
    mobile_header_text = mobile_header.read_text(encoding="utf-8") if mobile_header.is_file() else ""
    checks.append({
        "name": "mobile_cpp_MelodiaMobileHUD",
        "passed": "class MELODIACORE_API UMelodiaMobileHUD" in mobile_header_text
        and "ForwardLaneTap" in mobile_header_text
        and "LaneButtons" in mobile_header_text,
        "detail": "UMelodiaMobileHUD ready for WBP_Battle_Mobile parent + 4 lanes.",
        "tier": "mobile",
    })
    atlas_ok = all((ROOT / rel).is_file() for rel in MOBILE_ATLAS)
    checks.append({
        "name": "mobile_atlas_batch_n",
        "passed": atlas_ok,
        "detail": "LanePress / SkillChip / MobileTopBar / SafeArea / HighwayBG present in Source.",
        "tier": "mobile",
    })
    checks.append({
        "name": "WBP_Battle_Mobile",
        "passed": mobile_path.is_file() and mobile_path.stat().st_size > 0,
        "detail": MOBILE_ASSET,
        "tier": "mobile",
        "blocking_release": True,
    })

    desktop_checks = [c for c in checks if c.get("tier") == "desktop"]
    mobile_checks = [c for c in checks if c.get("tier") == "mobile"]
    desktop_ok = all(bool(c["passed"]) for c in desktop_checks)
    mobile_ok = all(bool(c["passed"]) for c in mobile_checks)

    report = {
        "ok": desktop_ok,
        "mobile_ok": mobile_ok,
        "scope": "desktop battle HUD preflight + mobile Pass C soft checks",
        "checks": checks,
        "pass_c_next": (
            "Open /Game/Melodia/UI/WBP_Battle_Mobile in UMG Designer — "
            "name BindWidgets, assign LaneButtons[0..3], brush Batch N atlas "
            "(UE 5.8 protects WidgetTree from Python)."
        ),
        "next_editor_step": (
            "Set BP_MelodiaGameMode.HUDWidgetClass to /Game/Melodia/UI/WBP_Battle_Rhythm, "
            "then implement the Blueprint event hooks listed in Docs/MELODIA_BATTLE_UI_INTEGRATION_2026-07-11.md."
        ),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if desktop_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
