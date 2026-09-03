"""Bind the authored battle HUD Blueprint to the Melodia smoke GameMode.

Run headlessly after the UI texture import:
    UnrealEditor-Cmd.exe BS_GodFile.uproject \
      -ExecutePythonScript=Content/Python/setup_melodia_battle_hud.py
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal


GAME_MODE_ASSET = "/Game/Melodia/_PROJECT/BP_MelodiaGameMode"
GAME_MODE_CLASS = f"{GAME_MODE_ASSET}.BP_MelodiaGameMode_C"
HUD_CLASS = "/Game/Melodia/UI/WBP_Battle_Rhythm.WBP_Battle_Rhythm_C"
REPORT_PATH = Path(__file__).resolve().parents[2] / "Saved" / "Melodia" / "battle_hud_setup.json"


def _load_class(path: str):
    loaded = unreal.load_class(None, path)
    if not loaded:
        raise RuntimeError(f"Unable to load class: {path}")
    return loaded


def main() -> bool:
    game_mode_class = _load_class(GAME_MODE_CLASS)
    hud_class = _load_class(HUD_CLASS)
    game_mode_cdo = unreal.get_default_object(game_mode_class)
    if not game_mode_cdo:
        raise RuntimeError(f"Unable to access GameMode CDO: {GAME_MODE_CLASS}")

    game_mode_cdo.set_editor_property("hud_widget_class", hud_class)
    unreal.EditorAssetLibrary.save_asset(GAME_MODE_ASSET, only_if_is_dirty=False)

    configured_class = game_mode_cdo.get_editor_property("hud_widget_class")
    report = {
        "game_mode": GAME_MODE_CLASS,
        "expected_hud": HUD_CLASS,
        "configured_hud": configured_class.get_path_name() if configured_class else None,
    }
    report["ok"] = report["configured_hud"] == HUD_CLASS
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"[MelodiaBattleHUD] Wrote {REPORT_PATH}")
    unreal.log(f"[MelodiaBattleHUD] ok={report['ok']}")
    return bool(report["ok"])


if __name__ == "__main__":
    main()
