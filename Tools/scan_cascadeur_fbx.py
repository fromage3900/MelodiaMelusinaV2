"""Offline Cascadeur FBX scanner.

Run with Blender, not Unreal:
  blender --background --python Tools/scan_cascadeur_fbx.py -- file.fbx report.json

The scanner imports the FBX into a temporary Blender scene, reports the armature
contract, and never writes back to the source FBX.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
from melusina_anim_unit_guard import (  # noqa: E402
    classify_fbx_header_units,
    classify_spine_translation,
    forbidden_lane_a_reasons,
    find_sidecar,
    read_json_object,
)


LEGACY_REQUIRED_BONES = {
    "DEF_eye_L",
    "DEF_eye_R",
    "c_kilt_master_x",
    "head_x",
    "root",
}
CANONICAL_SOURCE_SKELETON = "/Game/Melodia/Mocap/Source/SK_Source_Melusina"
CANONICAL_SOURCE_CONTRACT = _TOOLS.parent / "specs" / "anim_presets" / "melusina_source_skeleton_contract.json"


def parse_args() -> tuple[Path, Path]:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 2:
        raise SystemExit("usage: blender --background --python scan_cascadeur_fbx.py -- input.fbx report.json")
    return Path(args[0]).resolve(), Path(args[1]).resolve()


def main() -> None:
    source, report_path = parse_args()
    if not source.is_file():
        raise SystemExit(f"FBX not found: {source}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(
        filepath=str(source),
        use_anim=True,
        use_image_search=False,
        use_custom_normals=False,
    )

    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    bones = sorted({bone.name for armature in armatures for bone in armature.data.bones})
    sidecar = find_sidecar(source)
    manifest = None
    sidecar_errors: list[str] = []
    if sidecar is not None:
        manifest, read_error = read_json_object(sidecar)
        if read_error:
            sidecar_errors.append(read_error)
    else:
        sidecar_errors.append("No sidecar (.json or .manifest.json)")

    canonical_source = bool(
        manifest
        and manifest.get("schema_version") == 2
        and manifest.get("canonical_skeleton") == CANONICAL_SOURCE_SKELETON
    )
    required_bones = set(LEGACY_REQUIRED_BONES)
    if canonical_source:
        try:
            contract = json.loads(CANONICAL_SOURCE_CONTRACT.read_text(encoding="utf-8"))
            required_bones = set(contract["bone_names"])
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
            sidecar_errors.append(f"canonical source contract unavailable: {exc}")
    missing = sorted(required_bones.difference(bones))

    scene = bpy.context.scene
    fps = float(scene.render.fps) / float(scene.render.fps_base or 1.0)
    actions = []
    for action in bpy.data.actions:
        actions.append({
            "name": action.name,
            "frame_start": action.frame_range[0],
            "frame_end": action.frame_range[1],
            "frame_count": int(action.frame_range[1] - action.frame_range[0] + 1),
        })

    header = classify_fbx_header_units(source)
    if sidecar is not None and manifest is not None and not canonical_source:
        sidecar_errors.extend(forbidden_lane_a_reasons(manifest, source.name))

    spine_probe = None
    if armatures:
        arm = armatures[0]
        for name in ("c_spine_02_x", "c_spine_02.x"):
            bone = arm.data.bones.get(name)
            if bone is None:
                continue
            loc = bone.head_local
            spine_probe = {
                "bone": name,
                "head_local": [float(loc.x), float(loc.y), float(loc.z)],
                "class": classify_spine_translation(float(loc.y)),
                "note": "Blender import space; header_class is the FBX-file signal",
            }
            break

    report = {
        "source": str(source),
        "fps": fps,
        "armatures": [armature.name for armature in armatures],
        "meshes": [mesh.name for mesh in meshes],
        "bone_count": len(bones),
        "bones": bones,
        "canonical_source": canonical_source,
        "required_bones": sorted(required_bones),
        "missing_required_bones": missing,
        "actions": actions,
        "header": header,
        "sidecar": str(sidecar) if sidecar else None,
        "sidecar_errors": sidecar_errors,
        "spine_probe": spine_probe,
        "lane_a_ready": (
            bool(armatures)
            and not missing
            and abs(fps - 30.0) < 0.01
            and not sidecar_errors
        ),
        "unit_header_warn": header.get("header_class")
        in {"blender_meters", "blender_meters_x100_header"},
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
