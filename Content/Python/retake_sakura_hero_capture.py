# -*- coding: utf-8 -*-
"""UE Sakura hero retake — open L_WP_SakuraDream, pilot establishing cam, HighResShot.

Run via Monolith execute_file or editor console:
  py Content/Python/retake_sakura_hero_capture.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
OUT_DIR = ROOT / "Saved" / "Portfolio" / "Renders" / "Hero"
SITE_CHAR = ROOT / "my-site-clean" / "generated" / "assets"
AUDIT = ROOT / "Saved" / "Audit" / "ue_sakura_hero_retake_20260714.json"
MAP_PATH = "/Game/Maps/WorldPillars/L_WP_SakuraDream"
WIDTH, HEIGHT = 1920, 1080


def _log(msg: str) -> None:
    unreal.log(f"[sakura-retake] {msg}")


def _load_map() -> bool:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les:
        _log("no LevelEditorSubsystem")
        return False
    # Already on map?
    try:
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        world = ues.get_editor_world() if ues else None
        if world and "sakura" in str(world.get_name()).lower():
            _log(f"already on {world.get_name()}")
            return True
    except Exception:
        pass
    ok = les.load_level(MAP_PATH)
    _log(f"load_level {MAP_PATH} -> {ok}")
    return bool(ok)


def _find_camera():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.CameraActor)
    prefer = (
        "Cam_Hero_Establishing",
        "Cam_Hero_Route",
        "Cam_Hero",
        "CameraActor",
    )
    by_name = {a.get_actor_label(): a for a in actors}
    for name in prefer:
        if name in by_name:
            return by_name[name], name
    # soft match
    for a in actors:
        label = a.get_actor_label()
        if "Establishing" in label or "Hero" in label:
            return a, label
    if actors:
        a = actors[0]
        return a, a.get_actor_label()
    return None, None


def _pilot_camera(cam) -> None:
    # Set viewport to camera
    try:
        unreal.EditorLevelLibrary.pilot_level_actor(cam)
        _log("piloted camera")
    except Exception as exc:
        _log(f"pilot failed: {exc}")
    try:
        # Match look-through
        unreal.EditorLevelLibrary.editor_set_game_view(True)
    except Exception:
        pass


def _high_res_shot(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Prefer EditorLevelLibrary high-res screenshot API
    filename = str(path).replace("\\", "/")
    last = None
    for call in (
        lambda: unreal.AutomationLibrary.take_high_res_screenshot(
            WIDTH, HEIGHT, filename
        ),
        lambda: unreal.SystemLibrary.execute_console_command(
            None, f"HighResShot {WIDTH}x{HEIGHT} filename=\"{filename}\""
        ),
    ):
        try:
            call()
            _log(f"shot requested -> {filename}")
            return
        except Exception as exc:
            last = exc
    raise RuntimeError(f"screenshot failed: {last}")


def main() -> dict:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "map": MAP_PATH,
        "steps": [],
    }
    if not _load_map():
        report["error"] = "failed to load sakura map"
        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    cam, label = _find_camera()
    report["camera"] = label
    if cam:
        _pilot_camera(cam)
        report["steps"].append(f"pilot:{label}")
    else:
        report["steps"].append("no_camera_using_viewport")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUT_DIR / f"hero_l_wp_sakuradream_establishing_{stamp}_{WIDTH}x{HEIGHT}.png"
    _high_res_shot(out)
    report["shot_path"] = str(out)
    report["steps"].append("high_res_requested")

    # Also write a stable alias for web remount once file exists (may lag a tick)
    alias = SITE_CHAR / "unreal" / "hero_l_wp_sakuradream_1920x1080.png"
    report["web_alias"] = str(alias)
    report["note"] = (
        "HighResShot is async — if alias missing, copy newest Hero PNG manually "
        "then python Tools/assign_plate.py sakura.hero generated/assets/unreal/hero_l_wp_sakuradream_1920x1080.png"
    )

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _log(json.dumps(report))
    print(json.dumps(report))
    return report


if __name__ == "__main__":
    main()
