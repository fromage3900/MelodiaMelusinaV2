"""Sync SceneCapture2D still — bypasses async HighResShot flush.

Works under Monolith editor_query (unattended). Writes PNG immediately via
RenderingLibrary.export_render_target after CaptureScene.

  py Content/Python/retake_scenecapture_still.py
  py Content/Python/retake_scenecapture_still.py --pillar SpaceCathedral
  # or via Monolith execute_file
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "Saved" / "Portfolio" / "Renders" / "Hero"
AUDIT = PROJECT_ROOT / "Saved" / "Audit" / "ue_scenecapture_retake.json"

PILLARS = {
    "SakuraDream": {
        "level": "/Game/EnvSandbox/Environments/WP/L_WP_SakuraDream",
        "camera_prefer": (
            "Cam_Hero_Establishing",
            "CineCamera_Hero_Establishing",
            "Cam_Hero",
            "CineCamera_LandscapeLoop",
        ),
        "alias": "retake_sakura_hero",
        "width": 1920,
        "height": 1080,
        "fov": 35.0,
    },
    "SpaceCathedral": {
        "level": "/Game/EnvSandbox/Environments/WP/L_WP_SpaceCathedral",
        "camera_prefer": (
            "Cam_Hero_Establishing",
            "Cam_Hero",
            "CineCamera_LandscapeLoop",
        ),
        "alias": "retake_spacecathedral_hero",
        "width": 1920,
        "height": 1080,
        "fov": 32.0,
    },
    "BaroqueGrotto": {
        "level": "/Game/EnvSandbox/Environments/WP/L_WP_BaroqueGrotto",
        "camera_prefer": (
            "Cam_Hero_Establishing",
            "Cam_Hero",
            "CineCamera_LandscapeLoop",
        ),
        "alias": "retake_baroquegrotto_hero",
        "width": 1920,
        "height": 1080,
        "fov": 28.0,
    },
    "CosmicOrrery": {
        "level": "/Game/EnvSandbox/Environments/WP/L_WP_CosmicOrrery",
        "camera_prefer": (
            "Cam_Hero_Establishing",
            "Cam_Hero",
            "CineCamera_LandscapeLoop",
        ),
        "alias": "retake_cosmicorrery_hero",
        "width": 1920,
        "height": 1080,
        "fov": 30.0,
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _world():
    import unreal

    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if ues and hasattr(ues, "get_editor_world"):
        w = ues.get_editor_world()
        if w:
            return w
    try:
        return unreal.EditorLevelLibrary.get_editor_world()
    except Exception:
        return None


def _load_level(level_path: str) -> dict:
    import unreal

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les:
        return {"ok": False, "error": "no_LevelEditorSubsystem"}
    try:
        les.load_level(level_path)
    except Exception as exc:
        return {"ok": False, "error": f"load_level:{exc}"}
    return {"ok": True, "level": level_path}


def _find_camera(prefer: tuple[str, ...]):
    import unreal

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(eas.get_all_level_actors() or []) if eas else []
    by_label = {}
    cine = []
    for a in actors:
        label = a.get_actor_label() or ""
        cn = a.get_class().get_name() if a.get_class() else ""
        by_label[label] = a
        if "Camera" in cn:
            cine.append((label, a, cn))
    for name in prefer:
        if name in by_label:
            return by_label[name], name, "prefer"
    for label, actor, cn in cine:
        if "Hero" in label or "Establish" in label:
            return actor, label, cn
    if cine:
        return cine[0][1], cine[0][0], cine[0][2]
    return None, None, None


def _cine_fov(camera, default: float) -> float:
    import unreal

    try:
        cine = camera.get_cine_camera_component()
        if cine:
            return float(cine.get_editor_property("current_focal_length") or default)
    except Exception:
        pass
    try:
        cam = camera.camera_component
        if cam:
            return float(cam.get_editor_property("field_of_view") or default)
    except Exception:
        pass
    return default


def capture_pillar(pillar_id: str = "SakuraDream") -> dict:
    import unreal

    cfg = PILLARS.get(pillar_id)
    if not cfg:
        return {"ok": False, "error": f"unknown_pillar:{pillar_id}"}

    load = _load_level(cfg["level"])
    if not load.get("ok"):
        return load

    # Settle streaming / WP
    try:
        unreal.SystemLibrary.execute_console_command(None, "r.ForceLOD 0")
    except Exception:
        pass

    world = _world()
    if not world:
        return {"ok": False, "error": "no_editor_world_after_load", "load": load}

    camera, cam_label, cam_how = _find_camera(cfg["camera_prefer"])
    if not camera:
        return {
            "ok": False,
            "error": "no_camera",
            "world": unreal.SystemLibrary.get_path_name(world),
        }

    # Pilot for viewport parity (optional)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if les and hasattr(les, "pilot_level_actor"):
        try:
            les.pilot_level_actor(camera)
        except Exception:
            pass

    loc = camera.get_actor_location()
    rot = camera.get_actor_rotation()
    fov = _cine_fov(camera, float(cfg["fov"]))
    # Approximate FOV from focal length if value looks like mm not degrees
    if fov < 10 or fov > 170:
        # typical 35mm ~ 54deg on 36mm sensor — keep configured fallback
        fov = float(cfg["fov"])
        # If cine focal length returned, convert roughly: FOV ≈ 2*atan(18/f)*180/pi
        try:
            cine = camera.get_cine_camera_component()
            fl = float(cine.get_editor_property("current_focal_length") or 35.0)
            import math

            fov = math.degrees(2.0 * math.atan(18.0 / max(fl, 1.0)))
        except Exception:
            fov = float(cfg["fov"])

    width = int(cfg["width"])
    height = int(cfg["height"])
    stamp = time.strftime("%Y%m%d_%H%M%S")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"{cfg['alias']}_{cam_label or 'cam'}_{stamp}_{width}x{height}"
    out_path = OUT_DIR / f"{stem}.png"

    # Transient RT + SceneCapture2D (same path as UnrealMCP C++ take_screenshot)
    try:
        rt = unreal.RenderingLibrary.create_render_target2d(
            world,
            width,
            height,
            unreal.TextureRenderTargetFormat.RTF_RGBA8,
            unreal.LinearColor(0.0, 0.0, 0.0, 1.0),
            False,
        )
    except Exception as exc:
        return {"ok": False, "error": f"rt_init:{exc}"}
    if not rt:
        return {"ok": False, "error": "rt_null"}

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    capture = None
    try:
        if eas and hasattr(eas, "spawn_actor_from_class"):
            capture = eas.spawn_actor_from_class(
                unreal.SceneCapture2D.static_class(), loc, rot
            )
        if not capture:
            capture = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.SceneCapture2D.static_class(), loc, rot
            )
    except Exception as exc:
        return {"ok": False, "error": f"spawn_capture:{exc}"}

    if not capture:
        return {"ok": False, "error": "spawn_capture_null"}

    try:
        capture.set_actor_label(f"TMP_RetakeCapture_{pillar_id}")
        cc = capture.get_capture_component_2d() if hasattr(capture, 'get_capture_component_2d') else capture.get_components_by_class(unreal.SceneCaptureComponent2D)[0]
        cc.set_editor_property("texture_target", rt)
        cc.set_editor_property(
            "capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
        )
        cc.set_editor_property("capture_every_frame", False)
        cc.set_editor_property("capture_on_movement", False)
        try:
            cc.set_editor_property("always_persist_rendering_state", True)
        except Exception:
            pass
        cc.set_editor_property("fov_angle", float(fov))
        # Hide self
        try:
            hidden = list(cc.get_editor_property("hidden_actors") or [])
            hidden.append(capture)
            cc.set_editor_property("hidden_actors", hidden)
        except Exception:
            pass

        cc.capture_scene()

        # Sync export — blocks until RT has pixels (like MCP ReadPixels flush)
        exported = unreal.RenderingLibrary.export_render_target(
            world, rt, str(OUT_DIR), f"{stem}.png"
        )
        ok_file = out_path.is_file() and out_path.stat().st_size > 10_000
        result = {
            "ok": bool(exported) or ok_file,
            "pillar": pillar_id,
            "level": cfg["level"],
            "camera": cam_label,
            "camera_how": cam_how,
            "fov": fov,
            "output": str(out_path),
            "bytes": out_path.stat().st_size if out_path.is_file() else 0,
            "export_return": bool(exported),
            "world": unreal.SystemLibrary.get_path_name(world),
            "generated_at": _now(),
            "method": "SceneCapture2D+export_render_target",
        }
    except Exception as exc:
        result = {"ok": False, "error": f"capture:{exc}", "pillar": pillar_id}
    finally:
        try:
            if eas and capture:
                eas.destroy_actor(capture)
            elif capture:
                unreal.EditorLevelLibrary.destroy_actor(capture)
        except Exception:
            pass

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
    return result


def main() -> int:
    pillar = "SakuraDream"
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--pillar" and i < len(sys.argv) - 1:
            pillar = sys.argv[i + 1]
        elif arg.startswith("--pillar="):
            pillar = arg.split("=", 1)[1]
        elif arg in PILLARS:
            pillar = arg
    result = capture_pillar(pillar)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
