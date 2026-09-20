"""Pose the editor viewport to a WC_Lookdev_* camera. No sleep. No capture.

Usage (Monolith execute_file): pose_lookdev_viewport.py <camera_name> [beauty]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved" / "WorldCompiler" / "morning_rainbow_bloom_3900" / "ue" / "pose_lookdev_viewport.json"


def _label(a) -> str:
    try:
        return a.get_actor_label()
    except Exception:
        return ""


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.endswith(".py")]
    cam_name = args[0] if args else "website_oblique"
    rec = {"camera": cam_name, "ok": False}
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors() or []
    target = None
    labels = []
    for a in actors:
        lbl = _label(a)
        labels.append(lbl)
        if lbl == f"WC_Lookdev_{cam_name}":
            target = a
            break
    rec["found"] = bool(target)
    if not target:
        rec["error"] = "camera_not_found"
        rec["sample_labels"] = [l for l in labels if "Lookdev" in l or l.startswith("WC_")][:40]
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        return

    loc = target.get_actor_location()
    rot = target.get_actor_rotation()
    rec["loc"] = [loc.x, loc.y, loc.z]
    rec["rot"] = [rot.pitch, rot.yaw, rot.roll]
    cam_comp = getattr(target, "camera_component", None) or target.get_component_by_class(unreal.CameraComponent)
    fov = None
    if cam_comp:
        try:
            fov = float(cam_comp.get_editor_property("field_of_view"))
        except Exception:
            fov = None
    rec["fov"] = fov

    piloted = False
    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if les and hasattr(les, "pilot_level_actor"):
            les.pilot_level_actor(target)
            piloted = True
    except Exception as exc:
        rec["pilot_err"] = str(exc)[:200]
    if not piloted:
        try:
            unreal.EditorLevelLibrary.pilot_level_actor(target)
            piloted = True
        except Exception as exc:
            rec["pilot_ell_err"] = str(exc)[:200]
            try:
                unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
                rec["viewport_set"] = True
            except Exception as exc2:
                rec["viewport_err"] = str(exc2)[:200]
    rec["piloted"] = piloted

    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        unreal.SystemLibrary.execute_console_command(world, "r.Editor.Viewport.Realtime 1", None)
        unreal.SystemLibrary.execute_console_command(world, "DisableAllScreenMessages", None)
        unreal.SystemLibrary.execute_console_command(world, "stat none", None)
        if fov:
            unreal.SystemLibrary.execute_console_command(world, f"fov {fov}", None)
    except Exception as exc:
        rec["console_err"] = str(exc)[:200]

    rec["ok"] = bool(piloted or rec.get("viewport_set"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
