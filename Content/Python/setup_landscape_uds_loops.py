"""Capture UDS day/night landscape loops for the four WP pillars.

Terrain-forward cine cameras + Ultra Dynamic Sky TimeOfDay scrub.
Outputs frame folders under Saved/Portfolio/Renders/LandscapeLoops/<pillar>/.

Run in-editor (level must be open or will load):
  py Content/Python/setup_landscape_uds_loops.py
  py Content/Python/setup_landscape_uds_loops.py --pillar SakuraDream
  py Content/Python/setup_landscape_uds_loops.py --dry-run

Then encode:
  .\\my-site-clean\\tools\\encode_landscape_loops.ps1
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = PROJECT_ROOT / "Saved" / "Portfolio" / "Renders" / "LandscapeLoops"
MANIFEST = PROJECT_ROOT / "Saved" / "Portfolio" / "LandscapeLoops" / "landscape_loops_manifest.json"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "landscape_uds_loops.json"

FRAME_RATE = 30
LOOP_SECONDS = 10
LOOP_FRAMES = FRAME_RATE * LOOP_SECONDS  # 300
RESOLUTION = 1280

# TimeOfDay scrub: dawn → noon → dusk → night → dawn (UDS 0–2400 style)
TOD_START = 5.5
TOD_END = 29.5  # wraps past 24 for seamless night→dawn

PILLARS = [
    {
        "id": "WP_SakuraDream",
        "level": "/Game/EnvSandbox/Environments/WP/L_WP_SakuraDream",
        "poster": "WP_SakuraDream_terrain.png",
        "camera_label": "CineCamera_LandscapeLoop",
        # Terrain-forward — avoid sky-only heroes
        "cam_loc": (1800.0, -2200.0, 420.0),
        "cam_look": (400.0, -400.0, 80.0),
        "focal": 35.0,
    },
    {
        "id": "WP_SpaceCathedral",
        "level": "/Game/EnvSandbox/Environments/WP/L_WP_SpaceCathedral",
        "poster": "WP_SpaceCathedral_terrain.png",
        "camera_label": "CineCamera_LandscapeLoop",
        "cam_loc": (1600.0, 1900.0, 520.0),
        "cam_look": (0.0, 0.0, 200.0),
        "focal": 32.0,
    },
    {
        "id": "WP_BaroqueGrotto",
        "level": "/Game/EnvSandbox/Environments/WP/L_WP_BaroqueGrotto",
        "poster": "WP_BaroqueGrotto_terrain.png",
        "camera_label": "CineCamera_LandscapeLoop",
        "cam_loc": (-1400.0, 1100.0, 280.0),
        "cam_look": (200.0, 0.0, 40.0),
        "focal": 28.0,
    },
    {
        "id": "WP_CosmicOrrery",
        "level": "/Game/EnvSandbox/Environments/WP/L_WP_CosmicOrrery",
        "poster": "WP_CosmicOrrery_terrain.png",
        "camera_label": "CineCamera_LandscapeLoop",
        "cam_loc": (2200.0, -800.0, 680.0),
        "cam_look": (0.0, 0.0, 120.0),
        "focal": 30.0,
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _look_at(cam, target):
    import unreal

    dx = target[0] - cam[0]
    dy = target[1] - cam[1]
    dz = target[2] - cam[2]
    yaw = math.degrees(math.atan2(dy, dx))
    horiz = math.sqrt(dx * dx + dy * dy)
    pitch = -math.degrees(math.atan2(dz, horiz))
    return unreal.Rotator(pitch, yaw, 0.0)


def _find_uds_actor(eas):
    import unreal

    for actor in eas.get_all_level_actors() or []:
        name = actor.get_class().get_name() if actor.get_class() else ""
        label = actor.get_actor_label() or ""
        if "UltraDynamicSky" in name or "Ultra_Dynamic_Sky" in label or "UDS" in label:
            return actor
        if "UltraDynamicWeather" in name:
            return actor
    return None


def _set_tod(uds, hours: float) -> bool:
    import unreal

    if not uds:
        return False
    # Common UDS property names across versions
    for prop in ("Time of Day", "TimeOfDay", "time_of_day", "TOD"):
        try:
            uds.set_editor_property(prop.replace(" ", ""), hours % 24.0)
            return True
        except Exception:
            pass
    try:
        # Some builds expose via Blueprint callable
        if hasattr(uds, "set_time_of_day"):
            uds.set_time_of_day(hours % 24.0)
            return True
    except Exception:
        pass
    unreal.log_warning("[LandscapeLoops] Could not set UDS TimeOfDay — capture stills at current TOD")
    return False


def _ensure_camera(eas, pillar: dict):
    import unreal

    label = pillar["camera_label"]
    cam = None
    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label() == label:
            cam = actor
            break
    if not cam:
        cam = eas.spawn_actor_from_class(
            unreal.CineCameraActor,
            unreal.Vector(*pillar["cam_loc"]),
            _look_at(pillar["cam_loc"], pillar["cam_look"]),
        )
        if cam:
            cam.set_actor_label(label)
    else:
        cam.set_actor_location(unreal.Vector(*pillar["cam_loc"]), False, False)
        cam.set_actor_rotation(_look_at(pillar["cam_loc"], pillar["cam_look"]), False)
    if cam:
        cine = cam.get_cine_camera_component()
        if cine:
            cine.set_editor_property("current_focal_length", float(pillar["focal"]))
    return cam


def capture_pillar(pillar: dict, *, dry_run: bool = False) -> dict:
    import unreal

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    level = pillar["level"]
    level_asset = f"{level}.{level.rsplit('/', 1)[-1]}"

    result = {
        "id": pillar["id"],
        "level": level,
        "frames": LOOP_FRAMES,
        "duration_sec": LOOP_SECONDS,
        "poster": pillar["poster"],
        "ok": False,
    }

    if not unreal.EditorAssetLibrary.does_asset_exist(level_asset) and not unreal.EditorAssetLibrary.does_asset_exist(level):
        result["error"] = "level_missing"
        unreal.log_warning(f"[LandscapeLoops] missing {level}")
        return result

    if dry_run:
        result["ok"] = True
        result["dry_run"] = True
        return result

    try:
        les.load_level(level)
    except Exception as exc:
        result["error"] = f"load_failed:{exc}"
        return result

    out_dir = OUT_ROOT / pillar["id"]
    out_dir.mkdir(parents=True, exist_ok=True)

    cam = _ensure_camera(eas, pillar)
    uds = _find_uds_actor(eas)
    result["uds_found"] = bool(uds)
    result["camera"] = cam.get_actor_label() if cam else None

    # Pilotable camera for screenshots
    if cam:
        try:
            unreal.EditorLevelLibrary.pilot_level_actor(cam)
        except Exception:
            pass

    captured = 0
    for frame in range(LOOP_FRAMES):
        t = frame / float(LOOP_FRAMES)
        tod = TOD_START + (TOD_END - TOD_START) * t
        _set_tod(uds, tod)
        # Allow sky to update
        try:
            unreal.SystemLibrary.execute_console_command(None, "r.SkyAtmosphere.AerialPerspectiveLUT.FastApplyOnOpaque 1")
        except Exception:
            pass
        filename = str(out_dir / f"{pillar['id']}_{frame:04d}.png")
        try:
            unreal.AutomationLibrary.take_high_res_screenshot(RESOLUTION, RESOLUTION, filename)
            captured += 1
        except Exception as exc:
            unreal.log_warning(f"[LandscapeLoops] frame {frame}: {exc}")

    result["captured"] = captured
    result["output_dir"] = str(out_dir)
    result["ok"] = captured > 0
    result["webm_hint"] = f"generated/assets/landscape-loops/{pillar['id']}.webm"
    return result


def main() -> int:
    dry = "--dry-run" in sys.argv
    only = None
    if "--pillar" in sys.argv:
        idx = sys.argv.index("--pillar")
        if idx + 1 < len(sys.argv):
            only = sys.argv[idx + 1]

    pillars = PILLARS
    if only:
        pillars = [p for p in PILLARS if only.lower() in p["id"].lower()]

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    for pillar in pillars:
        entries.append(capture_pillar(pillar, dry_run=dry))

    manifest = {
        "generated_at": _now(),
        "generated_by": "setup_landscape_uds_loops.py",
        "frame_rate": FRAME_RATE,
        "loop_seconds": LOOP_SECONDS,
        "loop_frames": LOOP_FRAMES,
        "resolution": RESOLUTION,
        "tod_range": [TOD_START, TOD_END],
        "count": len(entries),
        "entries": entries,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2) if "json" in sys.argv else manifest)
    return 0 if all(e.get("ok") for e in entries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
