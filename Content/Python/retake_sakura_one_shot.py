# -*- coding: utf-8 -*-
"""Request ONE Sakura Establishing HighResShot (async — poll disk after)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

import render_exporter as rex

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
AUDIT = ROOT / "Saved" / "Audit" / "ue_sakura_one_shot_20260714.json"
MAP = "/Game/Maps/WorldPillars/L_WP_SakuraDream"


def main() -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(MAP)
    cams = rex._list_hero_cameras() or rex._list_cine_cameras()
    pick = None
    for c in cams:
        if "Establishing" in (c.get("label") or ""):
            pick = c
            break
    if pick is None and cams:
        pick = cams[0]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "camera": pick.get("label") if pick else None,
        "cameras_found": [c.get("label") for c in cams],
    }
    if not pick:
        report["error"] = "no camera"
    else:
        report["result"] = rex.capture_hero_from_camera(pick["actor"], width=1920, height=1080)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return report


if __name__ == "__main__":
    main()
