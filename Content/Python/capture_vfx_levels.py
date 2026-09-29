"""Synchronous SceneCapture2D multi-level rendering script for VFX & Niagara audit verification.

Runs headlessly via UnrealEditor-Cmd.exe with -AllowCommandletRendering.
Captures key showcase levels:
1. L_Lookdev_PetalCantata (Sakura Petals cascade, ground settle, flipbook)
2. L_CelestialPond (Cosmic Draw, celestial starfield, nebula SDF)
3. L_MelusinaMorning (Fairy glitter trails, morning mist, glint particles)
4. ZenForestTest (Zen petal vortex, ambient motes)

Exports plates to Saved/Portfolio/Renders/VFX_Audit/.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path("C:/EnvironmentPortfolio/BS_GodFile")
OUT_DIR = PROJECT_ROOT / "Saved" / "Portfolio" / "Renders" / "VFX_Audit"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "vfx_plates_capture_report.json"

LEVELS_TO_CAPTURE = [
    {
        "id": "SakuraDream",
        "title": "Sakura Dream — Petal Cascade & Ground Settle (Fix A)",
        "level": "/Game/_PROJECT/Levels/RenderTests/L_Lookdev_PetalCantata",
        "camera_prefer": ("Cam_Hero_Establishing", "CineCamera_Hero_Establishing", "Cam_Hero"),
        "fallback_cam_loc": (-1200.0, 800.0, 350.0),
        "fallback_cam_rot": (-15.0, -35.0, 0.0),
        "fov": 35.0,
    },
    {
        "id": "CosmicOrrery",
        "title": "Cosmic Orrery — NS_ConstellationDraw & SDF Nebulae",
        "level": "/Game/EnvSandbox/Environments/L_CelestialPond",
        "camera_prefer": ("Cam_Hero_Establishing", "Cam_Hero", "CineCamera_LandscapeLoop"),
        "fallback_cam_loc": (0.0, -1800.0, 500.0),
        "fallback_cam_rot": (-12.0, 90.0, 0.0),
        "fov": 30.0,
    },
    {
        "id": "MelusinaMorning",
        "title": "Melusina Morning — Fairy Dust Trails & Glitter Piles",
        "level": "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
        "camera_prefer": ("Cam_Hero_Establishing", "Cam_Morning_Hero", "CineCameraActor"),
        "fallback_cam_loc": (-2400.0, 1800.0, 650.0),
        "fallback_cam_rot": (-18.0, -25.0, 0.0),
        "fov": 32.0,
    },
    {
        "id": "ZenForest",
        "title": "Zen Forest — Ghibli Petal Vortex & Ambient Motes",
        "level": "/Game/ZenForestTest",
        "camera_prefer": ("Cam_Hero_Establishing", "Cam_Hero", "CineCameraActor"),
        "fallback_cam_loc": (500.0, -800.0, 300.0),
        "fallback_cam_rot": (-10.0, 120.0, 0.0),
        "fov": 38.0,
    },
]


def load_level(level_path: str) -> bool:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les:
        return False
    try:
        unreal.log(f"[Capture] Loading level {level_path}...")
        return les.load_level(level_path)
    except Exception as e:
        unreal.log_warning(f"[Capture] load_level error {level_path}: {e}")
        return False


def find_or_spawn_camera(entry: dict):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(eas.get_all_level_actors() or []) if eas else []
    for p in entry["camera_prefer"]:
        for a in actors:
            if a.get_actor_label() == p:
                return a
    for a in actors:
        if "Camera" in a.get_class().get_name() or "Cam" in (a.get_actor_label() or ""):
            return a

    # Spawn fallback cine camera
    loc = unreal.Vector(*entry["fallback_cam_loc"])
    rot = unreal.Rotator(*entry["fallback_cam_rot"])
    cam_actor = eas.spawn_actor_from_class(unreal.CineCameraActor.static_class(), loc, rot)
    if cam_actor:
        cam_actor.set_actor_label(f"VFXAudit_Cam_{entry['id']}")
    return cam_actor


def capture_plate(entry: dict) -> Path | None:
    width, height = 1280, 720
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"VFX_{entry['id']}_{width}x{height}.png"
    out_file = OUT_DIR / filename

    if out_file.is_file() and out_file.stat().st_size > 100000:
        unreal.log(f"[Capture] Plate already exists and valid ({out_file.stat().st_size} bytes): {out_file}")
        return out_file

    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = ues.get_editor_world() if ues else unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        return None

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cam = find_or_spawn_camera(entry)
    loc = cam.get_actor_location() if cam else unreal.Vector(*entry["fallback_cam_loc"])
    rot = cam.get_actor_rotation() if cam else unreal.Rotator(*entry["fallback_cam_rot"])

    capture_actor = eas.spawn_actor_from_class(unreal.SceneCapture2D.static_class(), loc, rot)
    if not capture_actor:
        return None

    try:
        rt = unreal.RenderingLibrary.create_render_target2d(
            world, width, height, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0, 0, 0, 1), False
        )
        cc = capture_actor.get_components_by_class(unreal.SceneCaptureComponent2D)[0]
        cc.set_editor_property("texture_target", rt)
        cc.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        cc.set_editor_property("capture_every_frame", False)
        cc.set_editor_property("capture_on_movement", False)
        cc.set_editor_property("fov_angle", float(entry["fov"]))
        cc.capture_scene()
        unreal.RenderingLibrary.export_render_target(world, rt, str(OUT_DIR), filename)
        unreal.log(f"[Capture] SceneCapture exported: {out_file}")
    except Exception as e:
        unreal.log_warning(f"[Capture] SceneCapture error: {e}")
    finally:
        eas.destroy_actor(capture_actor)

    if out_file.is_file() and out_file.stat().st_size > 0:
        return out_file
    return None


def main() -> int:
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "plates": [],
        "success": False
    }

    captured_plates = []
    for entry in LEVELS_TO_CAPTURE:
        unreal.log(f"--- Processing Showcase Level: {entry['id']} ({entry['level']}) ---")
        out_file = OUT_DIR / f"VFX_{entry['id']}_1280x720.png"
        if out_file.is_file() and out_file.stat().st_size > 100000:
            captured_plates.append({
                "id": entry["id"],
                "title": entry["title"],
                "level": entry["level"],
                "path": str(out_file),
                "ok": True,
                "cached": True
            })
            continue

        if load_level(entry["level"]):
            time.sleep(1.0)
            res = capture_plate(entry)
            captured_plates.append({
                "id": entry["id"],
                "title": entry["title"],
                "level": entry["level"],
                "path": str(res) if res else None,
                "ok": res is not None
            })
        else:
            captured_plates.append({
                "id": entry["id"],
                "title": entry["title"],
                "level": entry["level"],
                "path": None,
                "ok": False,
                "error": "level_load_failed"
            })

    report["plates"] = captured_plates
    report["success"] = any(p["ok"] for p in captured_plates)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[Capture] Completed. Report written to {REPORT_PATH}")
    print(json.dumps(report, indent=2))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
