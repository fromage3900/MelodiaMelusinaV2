# -*- coding: utf-8 -*-
"""Regenerate Melodia Musical Ornament Kitbash FBXs.

Prefers SurrealArch GeoNodes when the addon is loaded; otherwise pure-bpy
celestial sheet-music builders (Batch N language).

Writes:
  KitbashExport/MusicalOrnamentalMeshes/SM_Orn_*.fbx
  Products/MusicalOrnamentKitbash/FBX/
  Saved/Audit/musical_ornament_bake_manifest.json

Run:
  blender --factory-startup -b -P Tools/regenerate_musical_ornaments_surreal_arch.py
  # or exec inside live Blender / MCP
"""
from __future__ import annotations

import json
import math
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "KitbashExport" / "MusicalOrnamentalMeshes"
PRODUCT_FBX = ROOT / "Products" / "MusicalOrnamentKitbash" / "FBX"
STATUS_PATH = ROOT / "Saved" / "Audit" / "musical_ornament_bake_manifest.json"
TAU = math.tau

# name → (surreal_arch_type | None, overrides, bpy_fallback_key)
SPECS = [
    ("SM_Orn_TrebleClef", "TREBLE_CLEF", {
        "clef_size": 1.8,
        "clef_thickness": 0.055,
        "clef_curls": 1.4,
    }, "treble_clef"),
    ("SM_Orn_NoteHead", "NOTE_HEAD", {
        "note_kind": "QUARTER",
        "note_size": 0.45,
        "note_stem_len": 1.35,
    }, "note_head"),
    ("SM_Orn_NoteBeam", "NOTE_HEAD", {
        "note_kind": "QUARTER",
        "note_size": 0.38,
        "note_stem_len": 1.1,
    }, "note_beam"),
    ("SM_Orn_SheetMusicRail", "SHEET_MUSIC_RAIL", {}, "sheet_music_rail"),
    ("SM_Orn_MusicalCorner", "FILIGREE_PANEL", {
        "filigree_style": "ARTNOUVEAU_VINE",
        "filigree_width": 1.2,
        "filigree_height": 1.2,
        "filigree_thickness": 0.02,
        "filigree_density": 0.7,
        "filigree_include_frame": True,
    }, "musical_corner"),
    ("SM_Orn_MusicalDivider", None, {}, "musical_divider"),
    ("SM_Orn_PearlJewel", None, {}, "pearl_jewel"),
]


def log(msg: str) -> None:
    print(f"[musical-orn] {msg}", flush=True)


def surreal_available() -> bool:
    try:
        bpy.ops.mesh.primitive_cube_add(size=0.05, location=(50, 50, 50))
        obj = bpy.context.active_object
        ok = hasattr(obj, "surreal_arch_props")
        bpy.data.objects.remove(obj, do_unlink=True)
        return ok
    except Exception:
        return False


def clear_regen_objects() -> None:
    for o in list(bpy.data.objects):
        if o.name.startswith("SM_Orn_") or o.name.startswith("_morn_"):
            bpy.data.objects.remove(o, do_unlink=True)


def make_mat(name: str, color=(0.95, 0.88, 0.55, 1.0)) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.32
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.35
    return mat


def curve_from_points(
    name: str,
    points: list[tuple[float, float, float]],
    bevel: float = 0.03,
    resolution: int = 6,
    cyclic: bool = False,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 24
    curve.fill_mode = "FULL"
    curve.bevel_depth = bevel
    curve.bevel_resolution = resolution
    spline = curve.splines.new("NURBS")
    spline.points.add(len(points) - 1)
    for i, (x, y, z) in enumerate(points):
        spline.points[i].co = (x, y, z, 1.0)
    spline.use_endpoint_u = True
    spline.order_u = min(4, len(points))
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return obj


def mesh_join(name: str, objects: list[bpy.types.Object], mat: bpy.types.Material) -> bpy.types.Object:
    for o in list(objects):
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        if o.type == "CURVE":
            bpy.ops.object.convert(target="MESH")
    objs = [bpy.data.objects[o.name] for o in objects if o.name in bpy.data.objects]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = name
    if joined.data.materials:
        joined.data.materials[0] = mat
    else:
        joined.data.materials.append(mat)
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    return joined


def _uv_sphere(name: str, radius: float, loc=(0, 0, 0), segs=24) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=segs, ring_count=segs // 2)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def _torus(name: str, major: float, minor: float, loc=(0, 0, 0)) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major, minor_radius=minor, location=loc,
        major_segments=36, minor_segments=12,
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def build_treble_clef() -> bpy.types.Object:
    mat = make_mat("M_MusicalGold", (1.0, 0.9, 0.4, 1.0))
    # Spiral body (approximate G-clef)
    pts = []
    for i in range(48):
        t = i / 47.0
        ang = t * TAU * 2.2 + 0.6
        r = 0.15 + 0.55 * (1.0 - abs(t - 0.55) * 1.1)
        x = math.cos(ang) * r
        z = (t - 0.5) * 2.2 + math.sin(ang * 0.5) * 0.08
        pts.append((x, 0.0, z))
    body = curve_from_points("_morn_clef_body", pts, bevel=0.048, resolution=5)
    # Descending stem curl
    stem = curve_from_points(
        "_morn_clef_stem",
        [(0.05, 0, -0.9), (0.12, 0, -1.35), (0.35, 0, -1.55), (0.55, 0, -1.35)],
        bevel=0.04,
    )
    jewel = _uv_sphere("_morn_clef_jewel", 0.12, loc=(0.05, 0, 0.35), segs=16)
    return mesh_join("SM_Orn_TrebleClef", [body, stem, jewel], mat)


def build_note_head(name: str = "SM_Orn_NoteHead", with_flag: bool = True) -> bpy.types.Object:
    mat = make_mat("M_MusicalPearl", (0.94, 0.86, 0.94, 1.0))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, 0), segments=20, ring_count=12)
    head = bpy.context.active_object
    head.name = "_morn_head"
    head.scale = (1.35, 1.0, 0.85)
    bpy.ops.object.transform_apply(scale=True)
    # Stem
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=1.2, location=(0.18, 0, 0.55))
    stem = bpy.context.active_object
    stem.name = "_morn_stem"
    parts = [head, stem]
    if with_flag:
        flag = curve_from_points(
            "_morn_flag",
            [(0.18, 0, 1.1), (0.45, 0, 1.0), (0.55, 0, 0.75), (0.35, 0, 0.65)],
            bevel=0.028,
        )
        parts.append(flag)
    return mesh_join(name, parts, mat)


def build_note_beam() -> bpy.types.Object:
    mat = make_mat("M_MusicalCyan", (0.4, 0.85, 1.0, 1.0))
    left = build_note_head("_morn_left", with_flag=False)
    left.location.x = -0.35
    bpy.ops.object.select_all(action="DESELECT")
    right = build_note_head("_morn_right", with_flag=False)
    right.location.x = 0.35
    # Beam bar
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.05))
    beam = bpy.context.active_object
    beam.name = "_morn_beam"
    beam.scale = (0.85, 0.06, 0.05)
    bpy.ops.object.transform_apply(scale=True)
    return mesh_join("SM_Orn_NoteBeam", [left, right, beam], mat)


def build_sheet_music_rail() -> bpy.types.Object:
    mat = make_mat("M_MusicalStaff", (1.0, 0.9, 0.45, 1.0))
    parts: list[bpy.types.Object] = []
    length = 3.2
    gap = 0.18
    for i in range(5):
        z = (i - 2) * gap
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, z))
        line = bpy.context.active_object
        line.name = f"_morn_staff_{i}"
        line.scale = (length / 2, 0.02, 0.012)
        bpy.ops.object.transform_apply(scale=True)
        parts.append(line)
    # Bar lines
    for x in (-1.4, 0.0, 1.4):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0, 0))
        bar = bpy.context.active_object
        bar.name = f"_morn_bar_{x}"
        bar.scale = (0.02, 0.02, gap * 2.2)
        bpy.ops.object.transform_apply(scale=True)
        parts.append(bar)
    # Note pearls on middle line
    for x in (-0.9, -0.2, 0.55, 1.1):
        pearl = _uv_sphere(f"_morn_n_{x}", 0.07, loc=(x, 0, 0), segs=12)
        parts.append(pearl)
    return mesh_join("SM_Orn_SheetMusicRail", parts, mat)


def build_musical_corner() -> bpy.types.Object:
    mat = make_mat("M_MusicalCorner", (1.0, 0.9, 0.4, 1.0))
    # L arms
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.35, 0, 0.06))
    h = bpy.context.active_object
    h.name = "_morn_arm_h"
    h.scale = (0.55, 0.04, 0.05)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.06, 0, 0.35))
    v = bpy.context.active_object
    v.name = "_morn_arm_v"
    v.scale = (0.05, 0.04, 0.55)
    bpy.ops.object.transform_apply(scale=True)
    # Clef scroll quarter-arc
    pts = []
    for i in range(20):
        t = i / 19.0
        ang = math.pi * 0.5 + t * math.pi * 0.85
        r = 0.55 - t * 0.15
        pts.append((math.cos(ang) * r + 0.15, 0.0, math.sin(ang) * r + 0.15))
    scroll = curve_from_points("_morn_scroll", pts, bevel=0.028)
    jewel = _uv_sphere("_morn_cj", 0.08, loc=(0.22, 0, 0.22), segs=14)
    # Dotted trail
    trail_parts = []
    for i in range(5):
        p = _uv_sphere(f"_morn_dot_{i}", 0.035 - i * 0.004, loc=(0.45 + i * 0.12, 0, 0.12 + i * 0.08), segs=10)
        trail_parts.append(p)
    return mesh_join("SM_Orn_MusicalCorner", [h, v, scroll, jewel, *trail_parts], mat)


def build_musical_divider() -> bpy.types.Object:
    mat = make_mat("M_MusicalDiv", (1.0, 0.43, 0.7, 1.0))
    parts: list[bpy.types.Object] = []
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    bar = bpy.context.active_object
    bar.name = "_morn_div_bar"
    bar.scale = (1.6, 0.03, 0.025)
    bpy.ops.object.transform_apply(scale=True)
    parts.append(bar)
    for x in (-1.0, -0.35, 0.35, 1.0):
        n = _uv_sphere(f"_morn_dn_{x}", 0.06, loc=(x, 0, -0.02), segs=12)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.35, location=(x + 0.05, 0, 0.15))
        st = bpy.context.active_object
        st.name = f"_morn_dst_{x}"
        parts.extend([n, st])
    # Center jewel
    parts.append(_uv_sphere("_morn_div_jewel", 0.09, loc=(0, 0, 0.02), segs=14))
    parts.append(_torus("_morn_div_ring", 0.12, 0.018, loc=(0, 0, 0.02)))
    return mesh_join("SM_Orn_MusicalDivider", parts, mat)


def build_pearl_jewel() -> bpy.types.Object:
    mat = make_mat("M_MusicalPearlJewel", (0.95, 0.92, 0.98, 1.0))
    pearl = _uv_sphere("_morn_pearl", 0.35, segs=28)
    ring = _torus("_morn_pring", 0.42, 0.035)
    gold = make_mat("M_MusicalGoldRing", (1.0, 0.9, 0.4, 1.0))
    # Inner cyan spark
    spark = _uv_sphere("_morn_spark", 0.12, segs=16)
    cyan = make_mat("M_MusicalCyanSpark", (0.4, 0.85, 1.0, 1.0))
    joined = mesh_join("SM_Orn_PearlJewel", [pearl, ring, spark], mat)
    # Re-assign materials roughly via slots
    if len(joined.data.materials) < 2:
        joined.data.materials.append(gold)
        joined.data.materials.append(cyan)
    return joined


BPY_BUILDERS = {
    "treble_clef": build_treble_clef,
    "note_head": lambda: build_note_head("SM_Orn_NoteHead", True),
    "note_beam": build_note_beam,
    "sheet_music_rail": build_sheet_music_rail,
    "musical_corner": build_musical_corner,
    "musical_divider": build_musical_divider,
    "pearl_jewel": build_pearl_jewel,
}


def generate_surreal(name: str, arch_type: str, overrides: dict) -> bpy.types.Object | None:
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    if not hasattr(obj, "surreal_arch_props"):
        bpy.data.objects.remove(obj, do_unlink=True)
        return None
    props = obj.surreal_arch_props
    try:
        props.arch_type = arch_type
    except Exception as exc:
        log(f"SKIP arch_type {arch_type}: {exc}")
        bpy.data.objects.remove(obj, do_unlink=True)
        return None
    props.apply_modifiers = True
    for k, v in overrides.items():
        if hasattr(props, k):
            try:
                setattr(props, k, v)
            except Exception as exc:
                log(f"WARN set {k}: {exc}")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        result = bpy.ops.surreal_arch.generate()
    except Exception as exc:
        log(f"FAIL surreal generate {name}: {exc}")
        bpy.data.objects.remove(obj, do_unlink=True)
        return None
    if "FINISHED" not in result:
        bpy.data.objects.remove(obj, do_unlink=True)
        return None
    for mod in list(obj.modifiers):
        if mod.type == "NODES" and mod.name.startswith("SurrealArch"):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                pass
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    # NoteBeam: duplicate for beamed pair when SurrealArch only makes one note
    if name == "SM_Orn_NoteBeam":
        bpy.ops.object.duplicate()
        twin = bpy.context.active_object
        twin.location.x += 0.55
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.275, 0, twin.dimensions.z * 0.45))
        beam = bpy.context.active_object
        beam.scale = (0.4, 0.04, 0.03)
        bpy.ops.object.transform_apply(scale=True)
        mat = make_mat("M_MusicalCyan", (0.4, 0.85, 1.0, 1.0))
        return mesh_join(name, [obj, twin, beam], mat)
    obj.name = name
    return obj


def export_fbx(obj: bpy.types.Object, path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
        bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        zmin = min(v.z for v in bbox)
        obj.location.z -= zmin
    except Exception:
        pass
    tmp = ROOT / "Saved" / "Audit" / f"_tmp_{obj.name}.fbx"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    try:
        bpy.ops.export_scene.fbx(
            filepath=str(tmp),
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_NONE",
            axis_forward="-Y",
            axis_up="Z",
            mesh_smooth_type="FACE",
            use_mesh_modifiers=True,
            object_types={"MESH"},
            add_leaf_bones=False,
        )
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                pass
        shutil.copy2(tmp, path)
        log(f"exported {path} ({path.stat().st_size} bytes)")
        return True
    except Exception as exc:
        log(f"FAIL export {path}: {exc}")
        return False


def run() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PRODUCT_FBX.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)

    use_surreal = surreal_available()
    log(f"SurrealArch available={use_surreal}")
    clear_regen_objects()

    results = []
    for name, arch_type, overrides, fallback_key in SPECS:
        log(f"=== {name}")
        obj = None
        source = "bpy_fallback"
        if use_surreal and arch_type:
            obj = generate_surreal(name, arch_type, overrides)
            if obj is not None:
                source = f"surreal:{arch_type}"
        if obj is None:
            builder = BPY_BUILDERS[fallback_key]
            obj = builder()
            obj.name = name
            source = "bpy_fallback"
        ok = export_fbx(obj, OUT_DIR / f"{name}.fbx")
        if ok:
            try:
                shutil.copy2(OUT_DIR / f"{name}.fbx", PRODUCT_FBX / f"{name}.fbx")
            except Exception as exc:
                log(f"WARN product copy: {exc}")
        results.append({
            "name": name,
            "ok": ok,
            "source": source,
            "verts": len(obj.data.vertices) if obj and obj.type == "MESH" else 0,
            "path": str(OUT_DIR / f"{name}.fbx") if ok else None,
        })
        obj.hide_viewport = True
        obj.hide_render = True

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product_id": "melodia-musical-ornament-kitbash-v1",
        "ok": sum(1 for r in results if r["ok"]),
        "fail": sum(1 for r in results if not r["ok"]),
        "out_dir": str(OUT_DIR),
        "product_fbx": str(PRODUCT_FBX),
        "results": results,
    }
    STATUS_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    log(f"done {summary['ok']}/{len(results)} → {STATUS_PATH}")
    return summary


if __name__ == "__main__":
    run()
    # Headless Blender often hangs on quit of large scenes; force exit after bake.
    if "--" in sys.argv or any(a == "-b" for a in sys.argv):
        try:
            bpy.ops.wm.quit_blender()
        except Exception:
            pass
