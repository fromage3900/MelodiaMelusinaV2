# -*- coding: utf-8 -*-
"""Force one deferred HighResShot by toggling PIE briefly after piloting camera."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
AUDIT = ROOT / "Saved" / "Audit" / "ue_sakura_pie_flush_20260714.json"
MAP = "/Game/EnvSandbox/Environments/WP/L_WP_SakuraDream"


def main() -> dict:
    report = {"generated_at": datetime.now(timezone.utc).isoformat()}
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(MAP)
    time.sleep(1.0)

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    pick = None
    for a in eas.get_all_level_actors() or []:
        try:
            if a.get_class() and a.get_class().get_name() in ("CineCameraActor", "CameraActor"):
                if "Establishing" in a.get_actor_label():
                    pick = a
                    break
        except Exception:
            continue
    report["camera"] = pick.get_actor_label() if pick else None
    if pick:
        if hasattr(les, "pilot_level_actor"):
            les.pilot_level_actor(pick)
        else:
            unreal.EditorLevelLibrary.pilot_level_actor(pick)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rel = f"PortfolioHero/sakura_pie_{stamp}.png"
    expected = ROOT / "Saved" / "Screenshots" / "PortfolioHero" / f"sakura_pie_{stamp}.png"
    expected.parent.mkdir(parents=True, exist_ok=True)
    report["expected"] = str(expected)

    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, rel)

    # Flush by entering and leaving PIE (forces a rendered frame)
    try:
        pie = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        # Request play in editor — UE 5.8 API
        unreal.EditorLevelLibrary.editor_play_simulate()
        report["pie"] = "simulate_requested"
        time.sleep(2.0)
        unreal.EditorLevelLibrary.editor_end_play()
        report["pie_end"] = True
    except Exception as exc:
        report["pie_error"] = str(exc)
        try:
            unreal.SystemLibrary.execute_console_command(None, "HighResShot 1920x1080")
            report["console_hires"] = True
        except Exception as exc2:
            report["console_error"] = str(exc2)

    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return report


if __name__ == "__main__":
    main()
