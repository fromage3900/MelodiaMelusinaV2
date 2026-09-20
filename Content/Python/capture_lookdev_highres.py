"""Pilot WC_Lookdev camera, force viewport mode, request HighResShot 3840x2160.

No sleep. Driver waits on disk.

Usage: capture_lookdev_highres.py <camera> <mode> <out_png>
mode: beauty | wireframe | lighting | pcg
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "Saved" / "WorldCompiler" / "morning_rainbow_bloom_3900" / "ue" / "capture_lookdev_highres.json"


def _label(a) -> str:
    try:
        return a.get_actor_label()
    except Exception:
        return ""


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _cmd(s: str) -> None:
    unreal.SystemLibrary.execute_console_command(_world(), s, None)


def _find_cam(name: str):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors() or []:
        if _label(a) == f"WC_Lookdev_{name}":
            return a
    return None


def _apply_mode(mode: str) -> list[str]:
    cmds = [
        "r.Editor.Viewport.Realtime 1",
        "r.ScreenPercentage 100",
        "DisableAllScreenMessages",
        "stat none",
        "showflag.StaticMeshes 1",
        "showflag.InstancedStaticMeshes 1",
        "showflag.Landscape 1",
        "showflag.Particles 1",
        "showflag.Lighting 1",
        "showflag.PostProcessing 1",
        "showflag.Wireframe 0",
        "viewmode lit",
    ]
    if mode == "wireframe":
        cmds += ["showflag.Wireframe 1", "showflag.PostProcessing 0"]
    elif mode == "lighting":
        cmds += ["viewmode lightingonly"]
    elif mode == "pcg":
        cmds += ["viewmode unlit", "showflag.PostProcessing 0"]
    for c in cmds:
        _cmd(c)
    return cmds


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.endswith(".py")]
    cam_name = args[0] if args else "website_oblique"
    mode = args[1] if len(args) > 1 else "beauty"
    out = Path(args[2]) if len(args) > 2 else ROOT / "Saved" / "Screenshots" / "WindowsEditor" / "morning_4k.png"
    rec = {"camera": cam_name, "mode": mode, "out": str(out).replace("\\", "/"), "ok": False}
    cam = _find_cam(cam_name)
    rec["found"] = bool(cam)
    if not cam:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        return

    loc = cam.get_actor_location()
    rot = cam.get_actor_rotation()
    rec["loc"] = [loc.x, loc.y, loc.z]
    rec["rot"] = [rot.pitch, rot.yaw, rot.roll]
    rec["cmds"] = _apply_mode(mode)

    try:
        unreal.EditorLevelLibrary.editor_set_game_view(True)
        rec["game_view"] = True
    except Exception as exc:
        rec["game_view_err"] = str(exc)[:160]

    piloted = False
    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if les and hasattr(les, "pilot_level_actor"):
            les.pilot_level_actor(cam)
            piloted = True
    except Exception as exc:
        rec["pilot_les_err"] = str(exc)[:160]
    if not piloted:
        try:
            unreal.EditorLevelLibrary.pilot_level_actor(cam)
            piloted = True
        except Exception as exc:
            rec["pilot_ell_err"] = str(exc)[:160]
            try:
                unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
                rec["viewport_set"] = True
            except Exception as exc2:
                rec["viewport_err"] = str(exc2)[:160]
    rec["piloted"] = piloted

    cam_comp = getattr(cam, "camera_component", None) or cam.get_component_by_class(unreal.CameraComponent)
    if cam_comp:
        try:
            fov = float(cam_comp.get_editor_property("field_of_view"))
            rec["fov"] = fov
            _cmd(f"fov {fov}")
        except Exception:
            pass

    out.parent.mkdir(parents=True, exist_ok=True)
    filename = str(out).replace("\\", "/")
    rec["shot_requested"] = True
    rec["via"] = "HighResShot_console_async"
    _cmd(f'HighResShot 3840x2160 filename="{filename}"')
    rec["ok"] = bool(piloted or rec.get("viewport_set"))
    rec["error"] = None
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(rec, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
