# -*- coding: utf-8 -*-
"""Sakura WP retake — correct map path + relative screenshot filename."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
AUDIT = ROOT / "Saved" / "Audit" / "ue_sakura_wp_retake_20260714.json"
MAP = "/Game/EnvSandbox/Environments/WP/L_WP_SakuraDream"
HERO_DIR = ROOT / "Saved" / "Portfolio" / "Renders" / "Hero"


def _pilot(cam) -> None:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if les and hasattr(les, "pilot_level_actor"):
        les.pilot_level_actor(cam)
    else:
        unreal.EditorLevelLibrary.pilot_level_actor(cam)


def main() -> dict:
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "map": MAP}
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ok = les.load_level(MAP)
    report["load_ok"] = bool(ok)
    time.sleep(1.5)

    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = ues.get_editor_world() if ues else None
    report["world"] = str(world.get_name()) if world else None

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cams = []
    for a in eas.get_all_level_actors() or []:
        try:
            cls = a.get_class()
            cname = cls.get_name() if cls else ""
            if cname in ("CineCameraActor", "CameraActor"):
                cams.append(a)
        except Exception:
            continue
    report["camera_labels"] = [a.get_actor_label() for a in cams]
    pick = None
    for a in cams:
        if "Establishing" in a.get_actor_label():
            pick = a
            break
    if pick is None and cams:
        pick = cams[0]
    report["camera"] = pick.get_actor_label() if pick else None
    if not pick:
        report["error"] = "no camera"
        AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report))
        return report

    _pilot(pick)
    time.sleep(0.5)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Relative to Saved/Screenshots — AutomationLibrary often writes here
    rel = f"PortfolioHero/sakura_establishing_{stamp}.png"
    abs_shot = ROOT / "Saved" / "Screenshots" / "PortfolioHero" / f"sakura_establishing_{stamp}.png"
    abs_shot.parent.mkdir(parents=True, exist_ok=True)

    try:
        unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, rel)
        report["shot_rel"] = rel
        report["shot_abs_expected"] = str(abs_shot)
    except Exception as exc:
        report["shot_error"] = str(exc)
        # Fallback: absolute path into Hero dir
        dest = HERO_DIR / f"hero_l_wp_sakuradream_Cam_Hero_Establishing_{stamp}_1920x1080.png"
        try:
            unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(dest))
            report["shot_abs"] = str(dest)
        except Exception as exc2:
            report["shot_error2"] = str(exc2)

    # Nudge a frame so deferred screenshot can flush
    try:
        unreal.SystemLibrary.execute_console_command(None, "r.ScreenPercentage 100")
        unreal.SystemLibrary.execute_console_command(None, "Slate.bAllowThrottling 0")
    except Exception:
        pass

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return report


if __name__ == "__main__":
    main()
