"""Blender 5.2 headless exporter for the MUAL-2 canonical source rig.

This script is intentionally read-only with respect to the stage ``.blend``.
It copies the selected action, renames the ARP bones in memory using the
approved map, removes every control/helper bone outside the 464-bone
``SK_Source_Melusina`` contract, retimes keyframes to 30 FPS, and exports an
armature-only FBX plus a v2 manifest.  It exits non-zero if the contract cannot
be proven.

Example::

    blender.exe -b <authoritative-v22-stage.blend> \
      --python Tools/export_melusina_animation_source.py -- \
      --action <action> --clip-name A_BL_Source_Idle_Loop \
      --arp-addon <extracted-auto-rig-pro-directory> \
      --output Exports/AnimationLibrary/Blender

The stage is never saved. The authoritative v22 ARP stage and its existing
ARP operator own visual controller baking; this script only normalizes the
resulting baked audit FBX to the read-only serialized
``SK_Source_Melusina.uasset`` contract.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys
from pathlib import Path

import bpy


TOOLS = Path(__file__).resolve().parent
PROJECT = TOOLS.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
MAP_PATH = PROJECT / "specs/anim_presets/melusina_arp_to_contract_bones.json"
CONTRACT_MAP_PATH = PROJECT / "specs/anim_presets/melusina_contract_bones.json"
SOURCE_CONTRACT_PATH = PROJECT / "specs/anim_presets/melusina_source_skeleton_contract.json"
HIERARCHY_PATH = PROJECT / "specs/anim_presets/melusina_contract_hierarchy.json"
OUTPUT_ROOT = PROJECT / "Exports/AnimationLibrary/Blender"
OUTPUT_FPS = 30
REQUIRED_MOTION_BONES = {
    "c_traj", "root_x", "spine_01_x", "spine_02_x", "spine_03_x", "neck_x", "head_x",
    "shoulder_l", "shoulder_r", "arm_stretch_l", "arm_stretch_r", "forearm_stretch_l",
    "forearm_stretch_r", "hand_l", "hand_r", "thigh_stretch_l", "thigh_stretch_r",
    "leg_stretch_l", "leg_stretch_r", "foot_l", "foot_r", "toes_01_l", "toes_01_r",
}


def log(message: str) -> None:
    print(f"[mual-blender] {message}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", help="Exact Blender action name. Required unless --action-hint resolves one action.")
    parser.add_argument("--action-hint", default="Idle", help="Substring used when --action is omitted.")
    parser.add_argument("--armature", default="character_rig")
    parser.add_argument("--nla-track", default="", help="Optional NLA track to resolve when --action is omitted.")
    parser.add_argument(
        "--arp-addon",
        default="",
        help="Extracted Auto-Rig Pro add-on directory. Required: ARP owns the visual pose bake.",
    )
    parser.add_argument("--clip-name", required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--context", default="locomotion")
    parser.add_argument("--consumer", default="blendspace")
    parser.add_argument("--root-motion", choices=("in_place", "root"), default="in_place")
    parser.add_argument("--loop", action="store_true")
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])


def load_contract() -> tuple[dict, dict, set[str], dict[str, str | None]]:
    if not MAP_PATH.is_file() or not CONTRACT_MAP_PATH.is_file() or not SOURCE_CONTRACT_PATH.is_file():
        raise RuntimeError("approved ARP map or source skeleton contract is missing")
    arp_mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    contract_mapping = json.loads(CONTRACT_MAP_PATH.read_text(encoding="utf-8"))
    mapping = dict(arp_mapping)
    mapping["semantic_map"] = {
        **contract_mapping.get("semantic_map", {}),
        **arp_mapping.get("semantic_map", {}),
        # The verified contract map carries the ARP reference-bone remaps for
        # the finger deform chain (index2_ref_l -> index2_l, etc.).
        **contract_mapping.get("bone_map", {}),
    }
    source = json.loads(SOURCE_CONTRACT_PATH.read_text(encoding="utf-8"))
    hierarchy = json.loads(HIERARCHY_PATH.read_text(encoding="utf-8"))
    if source.get("bone_count") != 464 or len(source.get("bone_names", [])) != 464:
        raise RuntimeError("SK_Source_Melusina contract must contain exactly 464 bones")
    parent_map = {str(name): (None if parent in (None, "") else str(parent)) for name, parent in hierarchy.get("parent_map", {}).items()}
    source_bones = set(source["bone_names"])
    if set(parent_map) - source_bones != {"Retopo_Cube_003_001"}:
        raise RuntimeError("source contract hierarchy is not the target hierarchy minus the synthetic bone")
    return mapping, source, source_bones, parent_map


def find_action(armature, args: argparse.Namespace):
    if args.action:
        action = bpy.data.actions.get(args.action)
        if action is None:
            raise RuntimeError(f"action not found: {args.action}")
        return action, "explicit"
    if args.nla_track and armature.animation_data:
        for track in armature.animation_data.nla_tracks:
            if track.name == args.nla_track:
                actions = [strip.action for strip in track.strips if strip.action]
                if len(actions) == 1:
                    return actions[0], f"NLA:{args.nla_track}"
                raise RuntimeError(f"NLA track {args.nla_track!r} resolved {len(actions)} actions")
    matches = [action for action in bpy.data.actions if args.action_hint.lower() in action.name.lower()]
    if len(matches) != 1:
        raise RuntimeError(f"action hint {args.action_hint!r} resolved {len(matches)} actions; use --action")
    return matches[0], "hint"


def final_bone_name(name: str, semantic: dict[str, str], drop: set[str]) -> str:
    sanitized = name.replace(".", "_")
    if sanitized in semantic:
        sanitized = semantic[sanitized]
    if name in drop or sanitized in drop:
        return ""
    return sanitized


def build_bone_plan(armature, mapping: dict, source_bones: set[str]) -> dict:
    semantic = mapping.get("semantic_map", {})
    drop = set(mapping.get("drop", []))
    renames: dict[str, str] = {}
    drops: list[str] = []
    unresolved: list[str] = []
    destinations: dict[str, list[str]] = {}
    source_bones_by_name = {bone.name: bone for bone in armature.data.bones}
    for bone in armature.data.bones:
        destination = final_bone_name(bone.name, semantic, drop)
        if not destination or destination not in source_bones:
            drops.append(bone.name)
            continue
        destinations.setdefault(destination, []).append(bone.name)
        if destination != bone.name:
            renames[bone.name] = destination
    collisions = {dst: srcs for dst, srcs in destinations.items() if len(srcs) > 1}
    # ARP contains both a deform bone (for example ``thigh_stretch.l``) and a
    # controller (``thigh.l``).  The established Melusina export gate resolves
    # this by retaining the single use_deform source, never by guessing from
    # the spelling of the destination.
    for destination, sources in collisions.items():
        deform_sources = [source for source in sources if source_bones_by_name[source].use_deform]
        if len(deform_sources) > 1:
            raise RuntimeError(f"multiple deform bones map to {destination}: {deform_sources}")
        winner = deform_sources[0] if deform_sources else sorted(sources)[0]
        for source in sources:
            if source != winner:
                if source not in drops:
                    drops.append(source)
                renames.pop(source, None)
    resolved_collisions = collisions
    collisions = {}
    present = set(destinations)
    missing_contract = sorted(source_bones - present)
    # In the established ARP export route, inactive source controls may be
    # absent from the baked audit FBX.  They are completed as static synthetic
    # structure below; unresolved means a mapping collision/ambiguity, not an
    # inactive contract bone.
    unresolved = []
    return {
        "renames": renames,
        "drops": drops,
        "collisions": collisions,
        "resolved_collisions": resolved_collisions,
        "unresolved": unresolved,
        "missing_contract": missing_contract,
        "pre_count": len(armature.data.bones),
        "post_count": len(present) + len(missing_contract),
    }


def apply_bone_plan(armature, plan: dict) -> None:
    if plan["collisions"]:
        raise RuntimeError(f"bone-name collisions: {plan['collisions']}")
    if plan["unresolved"]:
        raise RuntimeError(f"unresolved source bones ({len(plan['unresolved'])}): {plan['unresolved'][:12]}")

    # Temporary names make swaps and semantic remaps deterministic.
    temp_names: dict[str, str] = {}
    for index, (source, destination) in enumerate(plan["renames"].items()):
        bone = armature.data.bones.get(source)
        if bone:
            temp = f"__MUAL_TMP_{index:04d}"
            temp_names[temp] = destination
            bone.name = temp
    for temp, destination in temp_names.items():
        bone = armature.data.bones.get(temp)
        if bone:
            bone.name = destination
    # Blender 5.2 exposes removal on EditBones, not the read-only Bone
    # collection.  The mode switch is in-memory and does not save the stage.
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    if armature.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")
    for name in plan["drops"]:
        bone = armature.data.edit_bones.get(name)
        if bone:
            armature.data.edit_bones.remove(bone)
    # The ARP audit export can omit inactive contract controls.  They are
    # structural bones, not animated sources, so complete the in-memory
    # source-rig table deterministically before applying the UE hierarchy.
    root = armature.data.edit_bones.get("root") or next(iter(armature.data.edit_bones), None)
    for name in plan.get("missing_contract", []):
        if armature.data.edit_bones.get(name):
            continue
        bone = armature.data.edit_bones.new(name)
        if root is not None and root is not bone:
            bone.parent = root
            bone.head = root.head
            bone.tail = root.tail
    bpy.ops.object.mode_set(mode="OBJECT")


def apply_contract_hierarchy(armature, parent_map: dict[str, str | None]) -> None:
    """Apply the verified UE/source hierarchy to the in-memory ARP export copy."""

    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    if armature.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")
    for bone in armature.data.edit_bones:
        parent_name = parent_map.get(bone.name)
        bone.parent = armature.data.edit_bones.get(parent_name) if parent_name else None
        bone.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")


def assign_action_with_slot(armature, action) -> bool:
    """Assign a Blender 4.2+/5.x layered action and its active slot."""

    if armature.animation_data is None:
        armature.animation_data_create()
    # The portfolio stage can be left in NLA tweak mode.  Blender exposes the
    # active action as read-only in that mode; exiting it is an in-memory state
    # change and is required before the established action-slot assignment.
    if armature.animation_data.use_tweak_mode:
        armature.animation_data.use_tweak_mode = False
    armature.animation_data.action = action
    slot = None
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                if channelbag.slot is not None:
                    slot = channelbag.slot
                    break
            if slot is not None:
                break
        if slot is not None:
            break
    if slot is not None:
        armature.animation_data.action_slot = slot
    return armature.animation_data.action is action


def enable_arp_addon(addon_path: str) -> str:
    """Enable Auto-Rig Pro from an extracted add-on directory in this process."""

    path = Path(addon_path).expanduser().resolve()
    if not path.is_dir() or not (path / "__init__.py").is_file():
        raise RuntimeError(f"ARP add-on directory must contain __init__.py: {path}")
    sys.path.insert(0, str(path.parent))
    bpy.ops.preferences.script_directory_add(directory=str(path.parent))
    bpy.ops.preferences.addon_enable(module=path.name)
    operator = getattr(getattr(bpy.ops, "arp", None), "arp_export_fbx_panel", None)
    if operator is None:
        raise RuntimeError("ARP add-on enabled but bpy.ops.arp.arp_export_fbx_panel is unavailable")
    return str(path)


def arp_bake_export(armature, filepath: Path) -> Path:
    """Use the established ARP FBX operator as the visual-pose bake gate."""

    operator = getattr(getattr(bpy.ops, "arp", None), "arp_export_fbx_panel", None)
    if operator is None:
        raise RuntimeError("Auto-Rig Pro is required; no bpy.ops.arp.arp_export_fbx_panel")
    scene = bpy.context.scene
    saved = {}
    for name, value in {
        "arp_export_rig_type": "UNIVERSAL",
        "arp_export_rig_name": "SK_Melusina_Skeleton",
        "arp_ge_sel_only": True,
        "arp_ge_sel_bones_only": False,
    }.items():
        if hasattr(scene, name):
            saved[name] = getattr(scene, name)
            setattr(scene, name, value)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    before = {
        path: path.stat().st_mtime_ns
        for path in filepath.parent.glob(f"{filepath.stem}.arp*.fbx")
        if path.is_file()
    }
    audit_path = filepath.with_name(filepath.stem + ".arp.fbx")
    if audit_path.exists():
        audit_path.unlink()
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    try:
        result = operator(filepath=str(audit_path), quick_export=True)
    except Exception as exc:
        raise RuntimeError(f"ARP pose bake/export failed: {exc}") from exc
    finally:
        for name, value in saved.items():
            setattr(scene, name, value)
    if audit_path.is_file() and audit_path.stat().st_size >= 100:
        return audit_path
    # ARP 3.77 appends the active action to the requested stem.  Consume that
    # versioned operator output rather than assuming the older `.arp.fbx`
    # naming convention used by the wardrobe gate.
    candidates = [
        path for path in filepath.parent.glob(f"{filepath.stem}.arp*.fbx")
        if path.is_file()
        and path.stat().st_size >= 100
        and path.stat().st_mtime_ns > before.get(path, 0)
    ]
    if not candidates:
        raise RuntimeError(f"ARP operator returned {result!r} but wrote no audit FBX")
    return max(candidates, key=lambda path: path.stat().st_mtime_ns)


def import_baked_armature(filepath: Path):
    """Import the ARP-baked audit into memory and return its armature/action."""

    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(filepath), use_anim=True, use_image_search=False)
    imported = [obj for obj in bpy.data.objects if obj not in before and obj.type == "ARMATURE"]
    armature = max(imported, key=lambda obj: len(obj.data.bones), default=None)
    if armature is None:
        raise RuntimeError("ARP audit FBX imported without an armature")
    action = armature.animation_data.action if armature.animation_data else None
    if action is None:
        actions = [action for action in bpy.data.actions if action.users]
        if len(actions) == 1:
            action = actions[0]
    if action is None:
        raise RuntimeError("ARP audit FBX imported without an animation action")
    return armature, action


def iter_fcurves(action):
    if getattr(action, "is_action_layered", False):
        for layer in action.layers:
            for strip in layer.strips:
                for channelbag in strip.channelbags:
                    yield from channelbag.fcurves
    elif hasattr(action, "fcurves"):
        yield from action.fcurves


def retime_and_remap_action(
    action,
    bone_name_map: dict[str, str],
    input_fps: float,
    translation_scale: float = 1.0,
):
    if input_fps <= 0:
        raise RuntimeError("input FPS must be positive")
    copied = action.copy()
    copied.name = f"__MUAL_{action.name}_{OUTPUT_FPS}fps"
    start = float(action.frame_range[0])
    scale = OUTPUT_FPS / input_fps
    for fcurve in iter_fcurves(copied):
        for source, destination in bone_name_map.items():
            fcurve.data_path = fcurve.data_path.replace(f'pose.bones["{source}"]', f'pose.bones["{destination}"]')
            fcurve.data_path = fcurve.data_path.replace(f"pose.bones['{source}']", f"pose.bones['{destination}']")
        for point in fcurve.keyframe_points:
            point.co[0] = (point.co[0] - start) * scale
            point.handle_left[0] = (point.handle_left[0] - start) * scale
            point.handle_right[0] = (point.handle_right[0] - start) * scale
            if translation_scale != 1.0 and fcurve.data_path.endswith("location"):
                point.co[1] *= translation_scale
                point.handle_left[1] *= translation_scale
                point.handle_right[1] *= translation_scale
        fcurve.update()
    return copied, max(0, int(math.ceil((float(action.frame_range[1]) - start) * scale)))


def scale_armature_to_cm(armature, factor: float = 100.0) -> None:
    """Bake the ARP stage's metre bind coordinates into centimetres."""

    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    if armature.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")
    for bone in armature.data.edit_bones:
        bone.head = tuple(float(value) * factor for value in bone.head)
        bone.tail = tuple(float(value) * factor for value in bone.tail)
    bpy.ops.object.mode_set(mode="OBJECT")


def read_fbx_unit_scale(path: Path) -> float | None:
    data = path.read_bytes()
    cursor = 0
    while True:
        cursor = data.find(b"UnitScaleFactor", cursor)
        if cursor < 0:
            return None
        if cursor >= 8 and data[cursor - 8 : cursor] == b"Original":
            cursor += 15
            continue
        window = data[cursor : cursor + 192]
        marker = window.find(b"double")
        dpos = window.find(b"D", marker) if marker >= 0 else -1
        if dpos >= 0 and dpos + 9 <= len(window):
            return float(struct.unpack_from("<d", window, dpos + 1)[0])
        cursor += 15


def export(args: argparse.Namespace) -> dict:
    mapping, source_contract, source_bones, parent_map = load_contract()
    armature = bpy.data.objects.get(args.armature)
    if not armature or armature.type != "ARMATURE":
        raise RuntimeError(f"armature not found or not an armature: {args.armature}")
    action, action_resolution = find_action(armature, args)
    if action.frame_range[1] <= action.frame_range[0]:
        raise RuntimeError(f"action has no usable frame range: {action.name} {tuple(action.frame_range)}")

    input_fps = float(bpy.context.scene.render.fps) / float(bpy.context.scene.render.fps_base or 1.0)
    unit_settings = bpy.context.scene.unit_settings
    if unit_settings.system != "METRIC" or unit_settings.scale_length <= 0:
        raise RuntimeError("stage must use a positive metric unit scale")

    if not args.arp_addon:
        raise RuntimeError(
            "--arp-addon is required: the established ARP operator must bake "
            "controller constraints before controls are filtered"
        )
    enable_arp_addon(args.arp_addon)
    # Make the selected ARP action the active action consumed by the ARP
    # exporter.  This is the same Blender 5.x action-slot assignment used by
    # the existing split-take tooling; it also exits NLA tweak mode in memory.
    if not assign_action_with_slot(armature, action):
        raise RuntimeError(f"could not assign selected action for ARP export: {action.name}")
    if armature.animation_data:
        for track in armature.animation_data.nla_tracks:
            track.mute = True
    args.output.mkdir(parents=True, exist_ok=True)
    audit_path = arp_bake_export(armature, args.output / f"{args.clip_name}.fbx")
    log(f"ARP audit bake written: {audit_path}")
    baked_armature, baked_action = import_baked_armature(audit_path)
    log(f"imported ARP-baked armature {baked_armature.name} ({len(baked_armature.data.bones)} bones)")
    log("building combined ARP/contract bone plan")
    plan = build_bone_plan(baked_armature, mapping, source_bones)
    if plan["unresolved"]:
        raise RuntimeError(
            f"source bones are unresolved after ARP remap; "
            f"unresolved={plan['unresolved'][:40]}"
        )
    apply_bone_plan(baked_armature, plan)
    log(f"filtered/remapped armature to {len(baked_armature.data.bones)} source bones")
    apply_contract_hierarchy(baked_armature, parent_map)
    log("applied verified source hierarchy")

    bone_name_map = plan["renames"]
    scale_armature_to_cm(baked_armature, 100.0)
    retimed_action, output_end = retime_and_remap_action(
        baked_action, bone_name_map, input_fps, translation_scale=100.0
    )
    if not assign_action_with_slot(baked_armature, retimed_action):
        raise RuntimeError("retimed action could not be assigned with an active Blender action slot")

    # Blender's unit scale is display metadata.  0.01 means one Blender unit is
    # one centimetre; this makes the FBX header and baked translations agree.
    original_scale_length = unit_settings.scale_length
    unit_settings.system = "METRIC"
    unit_settings.scale_length = 0.01
    scene = bpy.context.scene
    original_fps = (scene.render.fps, scene.render.fps_base)
    scene.render.fps = OUTPUT_FPS
    scene.render.fps_base = 1.0
    scene.frame_start = 0
    scene.frame_end = output_end

    args.output.mkdir(parents=True, exist_ok=True)
    fbx_path = args.output / f"{args.clip_name}.fbx"
    manifest_path = args.output / f"{args.clip_name}.manifest.json"
    bpy.ops.object.select_all(action="DESELECT")
    baked_armature.select_set(True)
    bpy.context.view_layer.objects.active = baked_armature
    bpy.ops.export_scene.fbx(
        filepath=str(fbx_path),
        use_selection=True,
        object_types={"ARMATURE"},
        add_leaf_bones=False,
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        bake_anim_step=1.0,
        global_scale=1.0,
        apply_unit_scale=False,
        apply_scale_options="FBX_SCALE_NONE",
        use_space_transform=True,
        axis_forward="-Z",
        axis_up="Y",
    )

    # Restore in-memory scene settings before producing the report.  Nothing in
    # this script calls bpy.ops.wm.save_as_mainfile or saves the source stage.
    unit_settings.scale_length = original_scale_length
    scene.render.fps, scene.render.fps_base = original_fps

    if not fbx_path.is_file() or fbx_path.stat().st_size <= 0:
        raise RuntimeError("FBX export produced no artifact")
    unit_scale = read_fbx_unit_scale(fbx_path)
    if unit_scale is None or abs(unit_scale - 1.0) > 0.01:
        raise RuntimeError(f"FBX unit header is not centimetres: UnitScaleFactor={unit_scale}")

    try:
        project_relative = fbx_path.resolve().relative_to(PROJECT.resolve()).as_posix()
    except ValueError:
        project_relative = fbx_path.as_posix()
    from animation_import_pipeline.manifest_v2 import deterministic_clip_id

    manifest = {
        "schema_version": 2,
        "clip_id": deterministic_clip_id("blender", "Melusina stage Blender action", args.clip_name),
        "clip_name": args.clip_name,
        "display_name": args.clip_name,
        "source_type": "blender",
        "source_file": project_relative,
        "source_name": f"Melusina stage action: {action.name}",
        "provenance": f"{Path(bpy.data.filepath).name}:{action.name}",
        "license": "project-authored",
        "canonical_rig": "SK_Source_Melusina",
        "canonical_skeleton": "/Game/Melodia/Mocap/Source/SK_Source_Melusina",
        "target_skeleton": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton",
        "target_mesh": "/Game/Melodia/Characters/Melusina/SK_Melusina",
        "retarget_profile": "RTG_Source_to_Melusina",
        "fps": OUTPUT_FPS,
        "units": "cm",
        "frame_start": 0,
        "frame_end": output_end,
        "loop": bool(args.loop),
        "root_motion": args.root_motion,
        "context": args.context,
        "consumer": args.consumer,
        "animation_only": True,
        "one_clip_per_file": True,
        "status": "canonical",
        "status_reasons": ["ARP map applied in memory", "control/helper bones filtered", "action retimed to 30 FPS", "FBX header verified as centimetres"],
        "promotion_target": "",
        "notify_contract": [],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "blend": bpy.data.filepath,
        "armature": baked_armature.name,
        "action": action.name,
        "action_resolution": action_resolution,
        "input_fps": input_fps,
        "output_fps": OUTPUT_FPS,
        "source_bone_count": source_contract["bone_count"],
        "contract_bones_present": plan["post_count"],
        "contract_bones_missing_optional": plan["missing_contract"],
        "required_motion_bones": sorted(REQUIRED_MOTION_BONES),
        "armature_bone_count_after_filter": len(baked_armature.data.bones),
        "arp_audit_fbx": str(audit_path),
        "frame_range": [0, output_end],
        "fbx": str(fbx_path),
        "manifest": str(manifest_path),
        "unit_scale_factor": unit_scale,
        "stage_saved": False,
    }


def main() -> int:
    args = parse_args()
    try:
        report = export(args)
        print("REPORT:" + json.dumps(report), flush=True)
        return 0
    except Exception as exc:
        print("REPORT:" + json.dumps({"ok": False, "error": str(exc), "stage_saved": False}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
