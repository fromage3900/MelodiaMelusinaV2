"""Read-only inventory of Blender actions and NLA strips in the ARP stage.

This is deliberately separate from the exporter: it never changes the active
action, remaps bones, or saves the portfolio stage.  It exists to distinguish a
real authored locomotion take from the solved v22 idle before a canonical
source-rig export is attempted.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy


def iter_action_fcurves(action):
    """Yield curves from both legacy and Blender 4.4+ layered actions."""

    if action is None:
        return
    if getattr(action, "is_action_layered", False):
        for layer in action.layers:
            for strip in layer.strips:
                for channelbag in strip.channelbags:
                    yield from channelbag.fcurves
    elif hasattr(action, "fcurves"):
        yield from action.fcurves


def bone_name_from_path(path: str) -> str | None:
    marker = "pose.bones["
    if marker not in path:
        return None
    remainder = path.split(marker, 1)[1]
    if not remainder or remainder[0] not in {"'", '"'}:
        return None
    quote = remainder[0]
    end = remainder.find(quote, 1)
    return remainder[1:end] if end > 1 else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("Saved/Audit/melusina_stage_actions.json"))
    parser.add_argument(
        "--inspect-action",
        action="append",
        default=[],
        help="Include layered curve/path details for this action; repeatable.",
    )
    parser.add_argument(
        "--motion-bones",
        default="root_x,c_traj,spine_01_x,spine_02_x,thigh_stretch_l,thigh_stretch_r,foot_l,foot_r",
        help="Comma-separated bone names used for motion coverage inspection.",
    )
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])


def main() -> int:
    args = parse_args()
    output = args.output
    if not output.is_absolute():
        output = Path(bpy.data.filepath).resolve().parent / output
    motion_bones = [name.strip() for name in args.motion_bones.split(",") if name.strip()]
    actions = []
    for action in bpy.data.actions:
        curves = list(iter_action_fcurves(action))
        actions.append({
            "name": action.name,
            "frame_start": float(action.frame_range[0]),
            "frame_end": float(action.frame_range[1]),
            "fcurve_count": len(curves),
            "animated_bone_count": len({
                bone_name_from_path(curve.data_path)
                for curve in curves
                if bone_name_from_path(curve.data_path)
            }),
        })
    nla = []
    armatures = []
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            armatures.append({
                "object": obj.name,
                "bone_count": len(obj.data.bones),
                "bone_sample": [bone.name for bone in list(obj.data.bones)[:12]],
                "active_action": (
                    obj.animation_data.action.name
                    if obj.animation_data and obj.animation_data.action
                    else None
                ),
            })
        animation = obj.animation_data
        if not animation or not animation.nla_tracks:
            continue
        tracks = []
        for track in animation.nla_tracks:
            tracks.append({
                "name": track.name,
                "mute": bool(track.mute),
                "strips": [
                    {
                        "name": strip.name,
                        "action": strip.action.name if strip.action else None,
                        "frame_start": float(strip.frame_start),
                        "frame_end": float(strip.frame_end),
                    }
                    for strip in track.strips
                ],
            })
        nla.append({"object": obj.name, "type": obj.type, "tracks": tracks})
    report = {
        "schema": "melodia.melusina_stage_actions.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": bpy.data.filepath,
        "read_only": True,
        "actions": sorted(actions, key=lambda row: row["name"].lower()),
        "armatures": armatures,
        "nla": nla,
        "stage_saved": False,
    }
    if args.inspect_action:
        details = []
        for name in args.inspect_action:
            action = bpy.data.actions.get(name)
            if action is None:
                details.append({"name": name, "found": False})
                continue
            curves = list(iter_action_fcurves(action))
            paths = [curve.data_path for curve in curves]
            motion = {}
            for bone in motion_bones:
                token = f'pose.bones["{bone}"]'
                alternate = f"pose.bones['{bone}']"
                selected = [curve for curve in curves if token in curve.data_path or alternate in curve.data_path]
                location_curves = [curve for curve in selected if curve.data_path.endswith("location")]
                motion[bone] = {
                    "curve_count": len(selected),
                    "location_curve_count": len(location_curves),
                    "location_ranges": [
                        {
                            "data_path": curve.data_path,
                            "array_index": curve.array_index,
                            "value_min": min(float(point.co[1]) for point in curve.keyframe_points),
                            "value_max": max(float(point.co[1]) for point in curve.keyframe_points),
                            "first": [float(curve.keyframe_points[0].co[0]), float(curve.keyframe_points[0].co[1])] if curve.keyframe_points else None,
                            "last": [float(curve.keyframe_points[-1].co[0]), float(curve.keyframe_points[-1].co[1])] if curve.keyframe_points else None,
                        }
                        for curve in location_curves
                    ],
                }
            details.append({
                "name": name,
                "found": True,
                "frame_start": float(action.frame_range[0]),
                "frame_end": float(action.frame_range[1]),
                "fcurve_count": len(curves),
                "animated_bone_count": len({
                    bone_name_from_path(path)
                    for path in paths
                    if bone_name_from_path(path)
                }),
                "motion_bones": motion,
                "path_sample": sorted(set(paths))[:80],
            })
        report["inspected_actions"] = details
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "action_count": len(actions), "nla_object_count": len(nla), "stage_saved": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
