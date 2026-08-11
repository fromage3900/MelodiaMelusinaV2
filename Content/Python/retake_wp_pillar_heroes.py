# -*- coding: utf-8 -*-
"""Retake WP pillar heroes via proven render_exporter path."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal

import render_exporter as rex

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
AUDIT = ROOT / "Saved" / "Audit" / "ue_pillar_hero_retake_20260714.json"
SITE_UNREAL = ROOT / "my-site-clean" / "generated" / "assets" / "unreal"

MAPS = [
    ("/Game/Maps/WorldPillars/L_WP_SakuraDream", "sakuradream"),
    ("/Game/Maps/WorldPillars/L_WP_SpaceCathedral", "spacecathedral"),
]


def _load(path: str) -> None:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(path)
    time.sleep(2.0)


def _best_hero_camera():
    cams = rex._list_hero_cameras()
    if not cams:
        # fall back to any cine / CameraActor with Hero in label
        cams = rex._list_cine_cameras()
    prefer = ("Establishing", "Route", "Materials", "Hero")
    for key in prefer:
        for c in cams:
            if key.lower() in (c.get("label") or "").lower():
                return c["actor"], c.get("label")
    if cams:
        return cams[0]["actor"], cams[0].get("label")
    return None, None


def main() -> dict:
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "captures": []}
    for map_path, slug in MAPS:
        entry = {"map": map_path, "slug": slug}
        try:
            _load(map_path)
            cam, label = _best_hero_camera()
            entry["camera"] = label
            if cam is None:
                entry["error"] = "no camera"
                report["captures"].append(entry)
                continue
            result = rex.capture_hero_from_camera(cam, width=1920, height=1080)
            entry["result"] = result
            # Promote Sakura to stable web alias when present
            path = result.get("path") or result.get("output")
            if path and slug == "sakuradream":
                src = Path(path)
                if src.is_file() and src.stat().st_size > 800_000:
                    dest = SITE_UNREAL / "hero_l_wp_sakuradream_1920x1080.png"
                    dest.write_bytes(src.read_bytes())
                    entry["web_alias"] = str(dest)
                    entry["bytes"] = src.stat().st_size
        except Exception as exc:
            entry["error"] = str(exc)
        report["captures"].append(entry)

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
