# -*- coding: utf-8 -*-
"""Cute, usable SM_Orn replacements via pure bpy (no SurrealArch arch_type).

Generates:
  SM_Orn_VaultRibs      — crossing Bezier vault ribs + apex boss (not a room)
  SM_Orn_CorbelBracket  — S-curve vine bracket + shelf + scroll finial
  SM_Orn_CrownMolding   — ogee/cyma crown with scallop waves
  SM_Orn_TorusKnot      — soft trefoil knot with petal modulation

Run:
  blender --factory-startup -b -P Content/Python/blender_ornament_cute_replacements.py

Writes KitbashExport/OrnamentalMeshes/SM_Orn_*.fbx (+ Products/.../FBX copy).
"""
from __future__ import annotations

import math
import os
import shutil
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
OUT_DIR = ROOT / "KitbashExport" / "OrnamentalMeshes"
PRODUCT_FBX = ROOT / "Products" / "OrnamentKitbash" / "FBX"
TAU = math.tau


def log(msg: str) -> None:
    print(f"[cute-orn] {msg}", flush=True)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for b in list(block):
            if b.users == 0:
                block.remove(b)


def make_mat(name: str, color=(0.92, 0.78, 0.88, 1.0)) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.35
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.12
    return mat


# Soften bevels slightly for kitbash readability
def curve_from_points(
    name: str,
    points: list[tuple[float, float, float]],
    bevel: float = 0.035,
    resolution: int = 8,
    cyclic: bool = False,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 32
    curve.fill_mode = "FULL"
    curve.bevel_depth = bevel
    curve.bevel_resolution = max(resolution, 6)
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
    for o in objects:
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        if o.type == "CURVE":
            bpy.ops.object.convert(target="MESH")
    objs = [bpy.data.objects[o.name] for o in objects if o.name in bpy.data.objects]
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
    # Mild shade smooth
    bpy.ops.object.shade_smooth()
    return joined


def export_fbx(obj: bpy.types.Object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        apply_scale_options="FBX_SCALE_ALL",
        object_types={"MESH"},
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        path_mode="AUTO",
    )
    log(f"wrote {path} ({path.stat().st_size} bytes)")


# ── Vault ribs: cute crossing gothic arches ─────────────────────────────
def build_vault_ribs() -> bpy.types.Object:
    mat = make_mat("M_CuteVault", (0.88, 0.72, 0.95, 1.0))
    span = 2.4
    rise = 1.35
    depth = 2.4
    ribs = 5
    parts: list[bpy.types.Object] = []

    def arch(y0: float, axis: str) -> list[tuple[float, float, float]]:
        pts = []
        for i in range(33):
            t = i / 32.0
            # Pointed-ish arch: sine + slight cusp
            h = rise * math.sin(math.pi * t) ** 0.85
            if axis == "x":
                pts.append(((t - 0.5) * span, y0, h))
            else:
                pts.append((y0, (t - 0.5) * depth, h))
        return pts

    # Longitudinal + transverse ribs
    for i in range(ribs):
        y = (i / (ribs - 1) - 0.5) * depth * 0.85
        parts.append(curve_from_points(f"_rib_x_{i}", arch(y, "x"), bevel=0.045, resolution=6))
    for i in range(ribs):
        x = (i / (ribs - 1) - 0.5) * span * 0.85
        parts.append(curve_from_points(f"_rib_y_{i}", arch(x, "y"), bevel=0.045, resolution=6))

    # Diagonal groin accents (cuter)
    for sgn in (-1.0, 1.0):
        pts = []
        for i in range(29):
            t = i / 28.0
            x = (t - 0.5) * span * 0.9
            y = sgn * (t - 0.5) * depth * 0.9
            z = rise * math.sin(math.pi * t) ** 0.9 * 1.02
            pts.append((x, y, z))
        parts.append(curve_from_points(f"_diag_{sgn}", pts, bevel=0.032, resolution=5))

    # Apex boss — small flower ring
    boss_pts = []
    for i in range(48):
        a = TAU * i / 48
        r = 0.18 + 0.04 * math.sin(a * 6)
        boss_pts.append((math.cos(a) * r, math.sin(a) * r, rise + 0.02))
    parts.append(curve_from_points("_boss", boss_pts, bevel=0.028, resolution=5, cyclic=True))

    return mesh_join("SM_Orn_VaultRibs", parts, mat)


# ── Corbel: S-vine bracket ──────────────────────────────────────────────
def build_corbel() -> bpy.types.Object:
    mat = make_mat("M_CuteCorbel", (0.95, 0.82, 0.90, 1.0))
    parts: list[bpy.types.Object] = []

    # Main S-arm
    arm = []
    for i in range(40):
        t = i / 39.0
        # Ease-out S curve
        x = 0.55 * t
        z = 0.75 * (math.sin(t * math.pi * 0.5) * 0.75 + t * 0.25)
        y = 0.06 * math.sin(t * math.pi)  # slight sway
        arm.append((x, y, z))
    parts.append(curve_from_points("_arm", arm, bevel=0.038, resolution=6))

    # Inner scroll near wall
    scroll = []
    for i in range(28):
        t = i / 27.0
        a = math.pi * 1.4 * t
        r = 0.12 * (1.0 - 0.35 * t)
        scroll.append((-0.02 + math.cos(a) * r, 0.0, 0.08 + math.sin(a) * r))
    parts.append(curve_from_points("_scroll", scroll, bevel=0.022, resolution=5))

    # Shelf pad (cute rounded top)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.16, depth=0.05, location=(0.52, 0.0, 0.78))
    shelf = bpy.context.active_object
    shelf.name = "_shelf"
    shelf.rotation_euler = (math.pi / 2, 0, 0)
    shelf.scale = (1.35, 0.55, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    parts.append(shelf)

    # Tip finial sphere
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=0.055, location=(0.55, 0.0, 0.82))
    tip = bpy.context.active_object
    tip.name = "_tip"
    parts.append(tip)

    # Wall mount plate
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.02, 0.0, 0.22))
    plate = bpy.context.active_object
    plate.name = "_plate"
    plate.scale = (0.04, 0.22, 0.28)
    bpy.ops.object.transform_apply(scale=True)
    parts.append(plate)

    return mesh_join("SM_Orn_CorbelBracket", parts, mat)


# ── Crown molding: ogee + scallops ──────────────────────────────────────
def build_crown() -> bpy.types.Object:
    mat = make_mat("M_CuteCrown", (0.93, 0.86, 0.78, 1.0))
    length = 2.2
    # Cyma recta-ish profile (x=depth, z=height)
    profile = []
    for i in range(18):
        t = i / 17.0
        # Classic ogee: ease in/out
        x = 0.22 * (3 * t * t - 2 * t * t * t)
        z = 0.18 * t + 0.06 * math.sin(t * math.pi)
        profile.append((x, z))

    # Build as curve bevel object extruded along Y — use mesh loft for control
    verts: list[Vector] = []
    faces: list[tuple[int, int, int, int]] = []
    segs = 48
    n_prof = len(profile)
    for i in range(segs + 1):
        y = (i / segs - 0.5) * length
        # Scallop modulation along length (cute wave on face)
        wave = 1.0 + 0.06 * math.sin((i / segs) * math.pi * 7)
        for px, pz in profile:
            verts.append(Vector((px * wave, y, pz)))
    for i in range(segs):
        for j in range(n_prof - 1):
            a = i * n_prof + j
            b = a + 1
            c = (i + 1) * n_prof + j + 1
            d = (i + 1) * n_prof + j
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("CrownMesh")
    mesh.from_pydata([tuple(v) for v in verts], [], faces)
    mesh.update()
    obj = bpy.data.objects.new("SM_Orn_CrownMolding", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)

    # Soft bead along front lip
    bead = []
    for i in range(segs + 1):
        y = (i / segs - 0.5) * length
        bead.append((0.22, y, 0.02))
    bead_obj = curve_from_points("_bead", bead, bevel=0.018, resolution=4)
    joined = mesh_join("SM_Orn_CrownMolding", [obj, bead_obj], mat)
    return joined


# ── Torus knot: soft trefoil with petal pulse ───────────────────────────
def build_torus_knot() -> bpy.types.Object:
    mat = make_mat("M_CuteKnot", (0.78, 0.88, 1.0, 1.0))
    p, q = 3, 2
    R, r = 0.55, 0.22
    samples = 280
    pts = []
    for i in range(samples):
        t = TAU * i / samples
        # Petal modulation — Magical Girl soft pulse
        pulse = 1.0 + 0.08 * math.sin(t * 6)
        rr = r * pulse
        x = (R + rr * math.cos(q * t)) * math.cos(p * t)
        y = (R + rr * math.cos(q * t)) * math.sin(p * t)
        z = rr * math.sin(q * t) * 1.15
        pts.append((x, y, z))
    knot = curve_from_points("_knot", pts, bevel=0.048, resolution=7, cyclic=True)

    # Tiny center jewel
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.07, location=(0, 0, 0))
    jewel = bpy.context.active_object
    jewel.name = "_jewel"

    return mesh_join("SM_Orn_TorusKnot", [knot, jewel], mat)


def main() -> None:
    clear_scene()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PRODUCT_FBX.mkdir(parents=True, exist_ok=True)

    builders = (
        ("SM_Orn_VaultRibs", build_vault_ribs),
        ("SM_Orn_CorbelBracket", build_corbel),
        ("SM_Orn_CrownMolding", build_crown),
        ("SM_Orn_TorusKnot", build_torus_knot),
    )
    for name, fn in builders:
        log(f"building {name}")
        # Fresh empty-ish scene each time to avoid join pollution
        clear_scene()
        obj = fn()
        # Origin to geometry
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
        out = OUT_DIR / f"{name}.fbx"
        export_fbx(obj, out)
        dest = PRODUCT_FBX / f"{name}.fbx"
        shutil.copy2(out, dest)
        log(f"copied {dest}")

    log("done — 4 cute replacements exported")


if __name__ == "__main__":
    main()
