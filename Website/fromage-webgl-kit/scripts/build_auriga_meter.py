#!/usr/bin/env python3
"""Build the owned Auriga Meter demo asset for Product Motion Lab.

Run with Blender:
  blender --background --python tools/fromage-webgl-kit/scripts/build_auriga_meter.py -- \
    --output tools/fromage-webgl-kit/prototypes/product-motion-lab/assets/auriga_meter.glb

The asset is intentionally generic and client-independent. It exists to prove:
- clean named hierarchy;
- parented annotation anchors;
- deterministic authored animation;
- web-ready GLB export;
- reproducible local generation.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    import bpy
except ImportError as exc:  # pragma: no cover - requires Blender
    raise SystemExit("This script must be executed with Blender's Python.") from exc

SCRIPT = Path(__file__).resolve()
KIT_ROOT = SCRIPT.parents[1]
DEFAULT_OUTPUT = KIT_ROOT / "prototypes" / "product-motion-lab" / "assets" / "auriga_meter.glb"


def blender_argv() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the generic Auriga Meter GLB.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--save-blend", type=Path, default=None)
    parser.add_argument("--fps", type=int, default=30)
    return parser.parse_args(blender_argv())


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def material(name: str, rgba: tuple[float, float, float, float], *, metallic: float, roughness: float):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def parent(child, parent_obj) -> None:
    child.parent = parent_obj


def empty(name: str, parent_obj=None, location=(0.0, 0.0, 0.0)):
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.12
    obj.location = location
    if parent_obj is not None:
        parent(obj, parent_obj)
    return obj


def rounded_box(name: str, dimensions: tuple[float, float, float], location: tuple[float, float, float], mat, *, parent_obj=None, bevel: float = 0.06):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel_mod = obj.modifiers.new(name="EdgeSoftening", type="BEVEL")
    bevel_mod.width = bevel
    bevel_mod.segments = 3
    obj.data.materials.append(mat)
    if parent_obj is not None:
        parent(obj, parent_obj)
    return obj


def cylinder(name: str, radius: float, depth: float, location: tuple[float, float, float], rotation: tuple[float, float, float], mat, *, parent_obj=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    bevel_mod = obj.modifiers.new(name="EdgeSoftening", type="BEVEL")
    bevel_mod.width = min(radius * 0.12, 0.025)
    bevel_mod.segments = 2
    if parent_obj is not None:
        parent(obj, parent_obj)
    return obj


def _iter_fcurves(action):
    """Yield the fcurves of an Action across Blender versions.

    Blender <= 4.3 exposed ``Action.fcurves`` directly.  Blender >= 4.4 replaced that
    with *slotted actions*: the curves live under
    ``action.layers[*].strips[*].channelbags[*].fcurves`` and ``Action.fcurves`` no
    longer exists.

    This script called ``action.fcurves`` unguarded, so on Blender 5.x it died with
    ``AttributeError: 'Action' object has no attribute 'fcurves'`` before the GLB was
    ever exported - which is why ``assets/auriga_meter.glb`` did not exist.
    """
    legacy = getattr(action, "fcurves", None)
    if legacy is not None:
        for fc in legacy:
            yield fc
        return

    for layer in getattr(action, "layers", None) or []:
        for strip in getattr(layer, "strips", None) or []:
            bags = list(getattr(strip, "channelbags", None) or [])
            if not bags:
                # older 4.4-era builds expose channelbag(slot_id) instead of the collection
                getter = getattr(strip, "channelbag", None)
                if getter is not None:
                    for slot in getattr(action, "slots", None) or []:
                        try:
                            bag = getter(slot)
                        except Exception:
                            bag = None
                        if bag is not None:
                            bags.append(bag)
            for bag in bags:
                for fc in getattr(bag, "fcurves", None) or []:
                    yield fc


def linearize_action(obj) -> None:
    if not obj.animation_data or not obj.animation_data.action:
        return
    for curve in _iter_fcurves(obj.animation_data.action):
        for point in curve.keyframe_points:
            point.interpolation = "LINEAR"


def keyframe(obj, frame: int, *, location=None, rotation=None) -> None:
    if location is not None:
        obj.location = location
        obj.keyframe_insert("location", frame=frame)
    if rotation is not None:
        obj.rotation_euler = rotation
        obj.keyframe_insert("rotation_euler", frame=frame)


def build(args: argparse.Namespace) -> dict[str, object]:
    clear_scene()
    scene = bpy.context.scene
    scene.render.fps = args.fps
    scene.frame_start = 1
    scene.frame_end = 121

    shell = material("MAT_Auriga_Shell", (0.62, 0.66, 0.70, 1.0), metallic=0.55, roughness=0.28)
    dark = material("MAT_Auriga_Dark", (0.055, 0.065, 0.078, 1.0), metallic=0.18, roughness=0.36)
    glass = material("MAT_Auriga_Glass", (0.17, 0.31, 0.44, 1.0), metallic=0.05, roughness=0.12)
    accent = material("MAT_Auriga_Accent", (0.36, 0.43, 0.55, 1.0), metallic=0.72, roughness=0.22)

    root = empty("AURIGA_METER_ROOT")
    root["asset_id"] = "auriga_meter_v1"
    root["provenance"] = "original generic demonstration asset"
    root["units"] = "meters"
    root["timeline"] = "0-1 deterministic authored animation"

    base = rounded_box("BODY_BASE", (2.50, 0.52, 1.55), (0.0, -0.35, 0.0), shell, parent_obj=root, bevel=0.08)
    lower_insert = rounded_box("BODY_LOWER_INSERT", (2.15, 0.12, 1.25), (0.0, -0.64, 0.02), dark, parent_obj=root, bevel=0.05)

    lid = empty("LID_ASSEMBLY", root, (0.0, -0.06, -0.60))
    lid_shell = rounded_box("LID_SHELL", (2.50, 0.22, 1.38), (0.0, 0.0, 0.61), shell, parent_obj=lid, bevel=0.07)
    bezel = rounded_box("DISPLAY_BEZEL", (1.52, 0.07, 0.92), (0.0, 0.145, 0.62), dark, parent_obj=lid, bevel=0.045)
    display = rounded_box("DISPLAY_GLASS", (1.30, 0.045, 0.72), (0.0, 0.19, 0.62), glass, parent_obj=lid, bevel=0.035)

    side_port = rounded_box("SIDE_PORT", (0.48, 0.16, 0.12), (1.26, -0.30, 0.15), dark, parent_obj=root, bevel=0.025)
    control = cylinder("CONTROL_DIAL", 0.16, 0.10, (-1.29, -0.20, 0.18), (0.0, math.radians(90.0), 0.0), accent, parent_obj=root)
    hinge_left = cylinder("HINGE_L", 0.09, 0.32, (-0.88, -0.04, -0.58), (0.0, math.radians(90.0), 0.0), dark, parent_obj=root)
    hinge_right = cylinder("HINGE_R", 0.09, 0.32, (0.88, -0.04, -0.58), (0.0, math.radians(90.0), 0.0), dark, parent_obj=root)

    anchor_screen = empty("ANCHOR_screen", lid, (0.0, 0.30, 0.62))
    anchor_hinge = empty("ANCHOR_hinge", lid, (0.0, 0.05, 0.02))
    anchor_port = empty("ANCHOR_port", root, (1.36, -0.18, 0.18))
    for anchor in (anchor_screen, anchor_hinge, anchor_port):
        anchor["annotation_anchor"] = True

    keyframe(root, 1, rotation=(math.radians(4.5), 0.0, math.radians(-31.5)))
    keyframe(root, 34, rotation=(math.radians(4.5), 0.0, math.radians(-4.0)))
    keyframe(root, 80, rotation=(math.radians(4.5), 0.0, math.radians(8.0)))
    keyframe(root, 121, rotation=(math.radians(4.5), 0.0, math.radians(12.0)))

    keyframe(lid, 1, rotation=(0.0, 0.0, 0.0))
    keyframe(lid, 34, rotation=(0.0, 0.0, 0.0))
    keyframe(lid, 76, rotation=(math.radians(-60.0), 0.0, 0.0))
    keyframe(lid, 121, rotation=(math.radians(-60.0), 0.0, 0.0))

    keyframe(control, 1, rotation=(0.0, math.radians(90.0), 0.0))
    keyframe(control, 76, rotation=(0.0, math.radians(90.0), 0.0))
    keyframe(control, 121, rotation=(math.radians(360.0), math.radians(90.0), 0.0))

    for obj in (root, lid, control):
        linearize_action(obj)

    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.gltf(filepath=str(args.output), export_format="GLB", export_animations=True, export_extras=True, export_apply=True)

    if args.save_blend:
        blend_path = args.save_blend.resolve()
        blend_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    manifest = {
        "asset": "auriga_meter_v1",
        "output": str(args.output),
        "fps": args.fps,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "anchors": ["ANCHOR_screen", "ANCHOR_hinge", "ANCHOR_port"],
        "animated_nodes": ["AURIGA_METER_ROOT", "LID_ASSEMBLY", "CONTROL_DIAL"],
        "mesh_nodes": [base.name, lower_insert.name, lid_shell.name, bezel.name, display.name, side_port.name, control.name, hinge_left.name, hinge_right.name],
    }
    args.output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    args = parse_args()
    result = build(args)
    print("BUILD_OK", json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
