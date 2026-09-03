"""Procedural mathematical StaticMesh generators for Cosmic Orrery + portfolio pillars.

Uses UE 5.8 GeometryScript (DynamicMesh → bake StaticMesh). Pure-Python math
works offline; mesh bake requires editor / UnrealEditor-Cmd.

Run (headless):
  py Content/Python/run_math_structures_cmd.py
  py Content/Python/run_math_structures_cmd.py --structure TorusKnot_2_3
  py Content/Python/run_math_structures_cmd.py --run 1

Hard boundaries: no master materials, no ZenForestTest, instances-only policy elsewhere.
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Sequence

MATH_DIR = "/Game/EnvSandbox/Meshes/MathStructures"
ORRERY_DIR = "/Game/EnvSandbox/Meshes/Orrery"
AUDIT_PATH = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "geometryscript_meshes.json"

PHI = (1.0 + math.sqrt(5.0)) / 2.0


@dataclass
class StructureSpec:
    key: str
    asset_name: str
    folder: str
    pillar: str
    description: str
    params: dict
    run_group: int = 1

    @property
    def asset_path(self) -> str:
        return f"{self.folder}/{self.asset_name}"


@dataclass
class BakeReport:
    key: str
    asset_path: str
    status: str
    triangle_count: int = 0
    error: str = ""


STRUCTURES: dict[str, StructureSpec] = {
    "TorusKnot_2_3": StructureSpec(
        "TorusKnot_2_3",
        "SM_Math_TorusKnot_2_3",
        ORRERY_DIR,
        "CosmicOrrery",
        "Torus knot (2,3) tube rail",
        {"p": 2, "q": 3, "R": 800.0, "r": 200.0, "tube": 25.0, "samples": 360},
        run_group=1,
    ),
    "Epitrochoid_Ring": StructureSpec(
        "Epitrochoid_Ring",
        "SM_Math_Epitrochoid_Ring",
        ORRERY_DIR,
        "CosmicOrrery",
        "Epitrochoid flat orbital ring",
        {"R": 600.0, "r": 150.0, "d": 120.0, "tube": 18.0, "samples": 480},
        run_group=1,
    ),
    "Icosahedron": StructureSpec(
        "Icosahedron",
        "SM_Math_Icosahedron",
        MATH_DIR,
        "CosmicOrrery",
        "Golden-ratio icosahedron planet mount",
        {"radius": 80.0},
        run_group=1,
    ),
    "MobiusStrip": StructureSpec(
        "MobiusStrip",
        "SM_Math_MobiusStrip",
        MATH_DIR,
        "CosmicOrrery",
        "Möbius strip ribbon",
        {"major": 400.0, "width": 60.0, "u_steps": 96, "v_steps": 8},
        run_group=1,
    ),
    "Armillary_Nested": StructureSpec(
        "Armillary_Nested",
        "SM_Math_Armillary_Nested",
        ORRERY_DIR,
        "CosmicOrrery",
        "Three orthogonal tori + equator ring",
        {"radii": [1200.0, 900.0, 600.0], "tube": 16.0},
        run_group=2,
    ),
    "LissajousRail_3_2_1": StructureSpec(
        "LissajousRail_3_2_1",
        "SM_Math_LissajousRail_3_2_1",
        MATH_DIR,
        "BaroqueGrotto",
        "3D Lissajous curve rail",
        {"scale": 500.0, "tube": 14.0, "samples": 400},
        run_group=2,
    ),
    "FibonacciSphere_Anchors": StructureSpec(
        "FibonacciSphere_Anchors",
        "SM_Math_FibonacciSphere_Anchors",
        MATH_DIR,
        "CosmicOrrery",
        "Vogel spiral anchor spheres",
        {"count": 64, "sphere_radius": 300.0, "anchor_radius": 8.0},
        run_group=2,
    ),
    "Gyroid_Patch": StructureSpec(
        "Gyroid_Patch",
        "SM_Math_Gyroid_Patch",
        MATH_DIR,
        "CosmicOrrery",
        "Gyroid isosurface patch (marching cubes)",
        {"bounds": 2.0, "resolution": 22},
        run_group=3,
    ),
    "GeodesicDome": StructureSpec(
        "GeodesicDome",
        "SM_Math_GeodesicDome",
        MATH_DIR,
        "CosmicOrrery",
        "Icosphere subdivision-2 dome",
        {"radius": 400.0, "subdiv": 2},
        run_group=3,
    ),
    "Kepler_Orbit_A": StructureSpec(
        "Kepler_Orbit_A",
        "SM_Math_Kepler_Orbit_A",
        ORRERY_DIR,
        "CosmicOrrery",
        "Elliptical orbit tube",
        {"a": 1000.0, "e": 0.35, "tube": 15.0, "samples": 360},
        run_group=3,
    ),
    "StellatedIcosahedron": StructureSpec(
        "StellatedIcosahedron",
        "SM_Math_StellatedIcosahedron",
        MATH_DIR,
        "CosmicOrrery",
        "Stellated icosahedron crystal mount",
        {"radius": 90.0, "stellate": 0.35},
        run_group=4,
    ),
    "TrefoilKnot": StructureSpec(
        "TrefoilKnot",
        "SM_Math_TrefoilKnot",
        MATH_DIR,
        "CosmicOrrery",
        "Trefoil knot tube",
        {"scale": 350.0, "tube": 12.0, "samples": 320},
        run_group=4,
    ),
    "EnneperPetal": StructureSpec(
        "EnneperPetal",
        "SM_Math_EnneperPetal",
        MATH_DIR,
        "SakuraDream",
        "Enneper minimal surface petal",
        {"extent": 1.2, "u_steps": 48, "v_steps": 48},
        run_group=4,
    ),
    "Sierpinski_Tet3": StructureSpec(
        "Sierpinski_Tet3",
        "SM_Math_Sierpinski_Tet3",
        MATH_DIR,
        "CosmicOrrery",
        "Sierpinski tetrahedron depth 3",
        {"edge": 600.0, "depth": 3},
        run_group=5,
    ),
}

BUILDERS: dict[str, Callable[[StructureSpec], tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]]] = {}


def _register(key: str):
    def deco(fn):
        BUILDERS[key] = fn
        return fn
    return deco


# --- Pure math: point / mesh generation ---------------------------------------

def _torus_knot_points(p: int, q: int, R: float, r: float, samples: int) -> list[tuple[float, float, float]]:
    pts: list[tuple[float, float, float]] = []
    for i in range(samples):
        t = (2.0 * math.pi * i) / samples
        ct, st = math.cos(t), math.sin(t)
        cq, sq = math.cos(q * t), math.sin(q * t)
        radial = R + r * cq
        x = radial * math.cos(p * t)
        y = radial * math.sin(p * t)
        z = r * sq
        pts.append((x, y, z))
    return pts


def _epitrochoid_points(R: float, r: float, d: float, samples: int) -> list[tuple[float, float, float]]:
    pts: list[tuple[float, float, float]] = []
    for i in range(samples):
        theta = (2.0 * math.pi * i) / samples
        x = (R + r) * math.cos(theta) - d * math.cos((R + r) * theta / r)
        y = (R + r) * math.sin(theta) - d * math.sin((R + r) * theta / r)
        pts.append((x, y, 0.0))
    return pts


def _lissajous_points(scale: float, samples: int) -> list[tuple[float, float, float]]:
    pts: list[tuple[float, float, float]] = []
    for i in range(samples):
        t = (2.0 * math.pi * i) / samples
        pts.append((scale * math.sin(3 * t), scale * math.sin(2 * t), scale * math.sin(t)))
    return pts


def _trefoil_points(scale: float, samples: int) -> list[tuple[float, float, float]]:
    pts: list[tuple[float, float, float]] = []
    for i in range(samples):
        t = (2.0 * math.pi * i) / samples
        x = scale * (math.sin(t) + 2 * math.sin(2 * t))
        y = scale * (math.cos(t) - 2 * math.cos(2 * t))
        z = scale * (-math.sin(3 * t))
        pts.append((x, y, z))
    return pts


def _kepler_orbit_points(a: float, e: float, samples: int) -> list[tuple[float, float, float]]:
    pts: list[tuple[float, float, float]] = []
    for i in range(samples):
        theta = (2.0 * math.pi * i) / samples
        r = a * (1.0 - e * e) / (1.0 + e * math.cos(theta))
        pts.append((r * math.cos(theta), r * math.sin(theta), 0.0))
    return pts


def _tube_along_polyline(
    points: Sequence[tuple[float, float, float]],
    tube_radius: float,
    sides: int = 8,
    closed: bool = True,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Build triangle mesh for a tube following a polyline (cm units)."""
    if len(points) < 2:
        return [], []

    verts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []
    n_pts = len(points)
    segments = n_pts if closed else n_pts - 1

    rings: list[list[int]] = []
    for i in range(n_pts):
        p = points[i]
        prev_i = (i - 1) % n_pts
        next_i = (i + 1) % n_pts
        if not closed and i == 0:
            tangent = _sub(points[1], points[0])
        elif not closed and i == n_pts - 1:
            tangent = _sub(points[-1], points[-2])
        else:
            tangent = _sub(points[next_i], points[prev_i])
        tangent = _normalize(tangent)
        if abs(tangent[2]) < 0.9:
            up = (0.0, 0.0, 1.0)
        else:
            up = (0.0, 1.0, 0.0)
        right = _normalize(_cross(tangent, up))
        up2 = _normalize(_cross(right, tangent))
        ring: list[int] = []
        for s in range(sides):
            ang = (2.0 * math.pi * s) / sides
            offset = (
                tube_radius * (math.cos(ang) * right[0] + math.sin(ang) * up2[0]),
                tube_radius * (math.cos(ang) * right[1] + math.sin(ang) * up2[1]),
                tube_radius * (math.cos(ang) * right[2] + math.sin(ang) * up2[2]),
            )
            verts.append((p[0] + offset[0], p[1] + offset[1], p[2] + offset[2]))
            ring.append(len(verts) - 1)
        rings.append(ring)

    for seg in range(segments):
        a = rings[seg]
        b = rings[(seg + 1) % n_pts]
        for s in range(sides):
            s2 = (s + 1) % sides
            i0, i1, i2, i3 = a[s], a[s2], b[s2], b[s]
            tris.append((i0, i1, i2))
            tris.append((i0, i2, i3))
    return verts, tris


def _icosahedron_verts(radius: float) -> list[tuple[float, float, float]]:
  raw = [
      (-1, PHI, 0), (1, PHI, 0), (-1, -PHI, 0), (1, -PHI, 0),
      (0, -1, PHI), (0, 1, PHI), (0, -1, -PHI), (0, 1, -PHI),
      (PHI, 0, -1), (PHI, 0, 1), (-PHI, 0, -1), (-PHI, 0, 1),
  ]
  faces = [
      (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
      (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
      (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
      (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
  ]
  scale = radius / math.sqrt(1 + PHI * PHI)
  verts = [(x * scale, y * scale, z * scale) for x, y, z in raw]
  return verts, faces  # type: ignore[return-value]


def _mobius_strip_mesh(major: float, width: float, u_steps: int, v_steps: int):
    verts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []
    for ui in range(u_steps):
        u = (2.0 * math.pi * ui) / u_steps
        for vi in range(v_steps):
            v = width * ((vi / (v_steps - 1)) - 0.5)
            cu, su = math.cos(u), math.sin(u)
            half_v = v / 2.0
            x = (major + half_v * math.cos(u / 2.0)) * cu
            y = (major + half_v * math.cos(u / 2.0)) * su
            z = half_v * math.sin(u / 2.0)
            verts.append((x, y, z))
    for ui in range(u_steps):
        u_next = (ui + 1) % u_steps
        for vi in range(v_steps - 1):
            i0 = ui * v_steps + vi
            i1 = ui * v_steps + vi + 1
            i2 = u_next * v_steps + vi + 1
            i3 = u_next * v_steps + vi
            tris.append((i0, i1, i2))
            tris.append((i0, i2, i3))
    return verts, tris


def _enneper_mesh(extent: float, u_steps: int, v_steps: int):
    verts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []
    scale = 120.0
    for ui in range(u_steps):
        u = -extent + (2 * extent * ui) / (u_steps - 1)
        for vi in range(v_steps):
            v = -extent + (2 * extent * vi) / (v_steps - 1)
            x = scale * (u - (u ** 3) / 3.0 + u * v * v)
            y = scale * (v - (v ** 3) / 3.0 + v * u * u)
            z = scale * (u * u - v * v)
            verts.append((x, y, z))
    for ui in range(u_steps - 1):
        for vi in range(v_steps - 1):
            i0 = ui * v_steps + vi
            i1 = i0 + 1
            i2 = i0 + v_steps + 1
            i3 = i0 + v_steps
            tris.append((i0, i1, i2))
            tris.append((i0, i2, i3))
    return verts, tris


def _gyroid_mesh(bounds: float, resolution: int):
    """Voxel-shell gyroid: f = sin x cos y + sin y cos z + sin z cos x ≈ 0."""

    def f(x, y, z):
        return math.sin(x) * math.cos(y) + math.sin(y) * math.cos(z) + math.sin(z) * math.cos(x)

    step = (2 * bounds) / resolution
    scale = 80.0  # cm
    half = step * scale * 0.45
    verts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []

    def add_cube(cx, cy, cz):
        base = len(verts)
        verts.extend([
            (cx - half, cy - half, cz - half), (cx + half, cy - half, cz - half),
            (cx + half, cy + half, cz - half), (cx - half, cy + half, cz - half),
            (cx - half, cy - half, cz + half), (cx + half, cy - half, cz + half),
            (cx + half, cy + half, cz + half), (cx - half, cy + half, cz + half),
        ])
        faces = (
            (0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6),
            (0, 4, 5), (0, 5, 1), (2, 6, 7), (2, 7, 3),
            (0, 3, 7), (0, 7, 4), (1, 5, 6), (1, 6, 2),
        )
        tris.extend((a + base, b + base, c + base) for a, b, c in faces)

    for iz in range(resolution):
        z = -bounds + (iz + 0.5) * step
        for iy in range(resolution):
            y = -bounds + (iy + 0.5) * step
            for ix in range(resolution):
                x = -bounds + (ix + 0.5) * step
                if abs(f(x, y, z)) < 0.22:
                    add_cube(x * scale, y * scale, z * scale)
    return verts, tris


def _icosphere(radius: float, subdiv: int):
    verts, faces = _icosahedron_verts(1.0)
    verts = [tuple(v) for v in verts]  # type: ignore[assignment]
    for _ in range(subdiv):
        new_faces: list[tuple[int, int, int]] = []
        midpoint_cache: dict[tuple[int, int], int] = {}

        def midpoint(i, j):
            key = (min(i, j), max(i, j))
            if key in midpoint_cache:
                return midpoint_cache[key]
            a, b = verts[i], verts[j]
            m = _normalize(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2))
            midpoint_cache[key] = len(verts)
            verts.append(m)
            return midpoint_cache[key]

        for i0, i1, i2 in faces:
            a = midpoint(i0, i1)
            b = midpoint(i1, i2)
            c = midpoint(i2, i0)
            new_faces.extend([(i0, a, c), (i1, b, a), (i2, c, b), (a, b, c)])
        faces = new_faces
    verts = [_scale(v, radius) for v in verts]
    tris = list(faces)
    return verts, tris


def _sierpinski_tet(edge: float, depth: int):
    verts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []
    h = edge * math.sqrt(2.0 / 3.0)
    base = [
        (0.0, 0.0, 0.0),
        (edge, 0.0, 0.0),
        (edge / 2, h, 0.0),
        (edge / 2, h / 3, edge * math.sqrt(6) / 3),
    ]

    def recurse(a, b, c, d, level):
        if level == 0:
            i0, i1, i2, i3 = len(verts), len(verts) + 1, len(verts) + 2, len(verts) + 3
            verts.extend([a, b, c, d])
            for face in ((i0, i1, i2), (i0, i2, i3), (i0, i3, i1), (i1, i3, i2)):
                tris.append(face)
            return
        ab = _mid(a, b)
        ac = _mid(a, c)
        ad = _mid(a, d)
        bc = _mid(b, c)
        bd = _mid(b, d)
        cd = _mid(c, d)
        recurse(a, ab, ac, ad, level - 1)
        recurse(ab, b, bc, bd, level - 1)
        recurse(ac, bc, c, cd, level - 1)
        recurse(ad, bd, cd, d, level - 1)

    recurse(*base, depth)
    centered = _center_mesh(verts, tris)
    return centered


def _fibonacci_sphere_merged(count: int, sphere_radius: float, anchor_radius: float):
    verts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []
    golden = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(count):
        y = 1.0 - (2.0 * i) / max(count - 1, 1)
        r = math.sqrt(max(0.0, 1.0 - y * y))
        theta = golden * i
        cx = sphere_radius * r * math.cos(theta)
        cz = sphere_radius * r * math.sin(theta)
        cy = sphere_radius * y
        sv, st = _icosphere(anchor_radius, 1)
        offset = len(verts)
        verts.extend((cx + x, cy + y, cz + z) for x, y, z in sv)
        tris.extend((a + offset, b + offset, c + offset) for a, b, c in st)
    return verts, tris


def _stellated_icosahedron(radius: float, stellate: float):
    verts, faces = _icosahedron_verts(radius)
    verts = list(verts)
    tris: list[tuple[int, int, int]] = []
    for i0, i1, i2 in faces:
        a, b, c = verts[i0], verts[i1], verts[i2]
        center = ((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3, (a[2] + b[2] + c[2]) / 3)
        edge = math.dist(a, b)
        tip = _scale(_normalize(center), radius * (1.0 + stellate))
        base = len(verts)
        verts.extend([a, b, c, tip])
        tris.extend([(base, base + 1, base + 3), (base + 1, base + 2, base + 3), (base + 2, base, base + 3)])
    return verts, tris


# --- Builders registered to STRUCTURES keys -----------------------------------

@_register("TorusKnot_2_3")
def _build_torus_knot(spec: StructureSpec):
    p = spec.params
    pts = _torus_knot_points(p["p"], p["q"], p["R"], p["r"], p["samples"])
    return _tube_along_polyline(pts, p["tube"])


@_register("Epitrochoid_Ring")
def _build_epitrochoid(spec: StructureSpec):
    p = spec.params
    pts = _epitrochoid_points(p["R"], p["r"], p["d"], p["samples"])
    return _tube_along_polyline(pts, p["tube"])


@_register("Icosahedron")
def _build_icosahedron(spec: StructureSpec):
    verts, faces = _icosahedron_verts(spec.params["radius"])
    return list(verts), list(faces)


@_register("MobiusStrip")
def _build_mobius(spec: StructureSpec):
    p = spec.params
    return _mobius_strip_mesh(p["major"], p["width"], p["u_steps"], p["v_steps"])


@_register("LissajousRail_3_2_1")
def _build_lissajous(spec: StructureSpec):
    p = spec.params
    pts = _lissajous_points(p["scale"], p["samples"])
    return _tube_along_polyline(pts, p["tube"])


@_register("TrefoilKnot")
def _build_trefoil(spec: StructureSpec):
    p = spec.params
    pts = _trefoil_points(p["scale"], p["samples"])
    return _tube_along_polyline(pts, p["tube"])


@_register("Kepler_Orbit_A")
def _build_kepler(spec: StructureSpec):
    p = spec.params
    pts = _kepler_orbit_points(p["a"], p["e"], p["samples"])
    return _tube_along_polyline(pts, p["tube"])


@_register("Gyroid_Patch")
def _build_gyroid(spec: StructureSpec):
    p = spec.params
    return _gyroid_mesh(p["bounds"], p["resolution"])


@_register("GeodesicDome")
def _build_geodesic(spec: StructureSpec):
    p = spec.params
    return _icosphere(p["radius"], p["subdiv"])


@_register("EnneperPetal")
def _build_enneper(spec: StructureSpec):
    p = spec.params
    return _enneper_mesh(p["extent"], p["u_steps"], p["v_steps"])


@_register("FibonacciSphere_Anchors")
def _build_fibonacci(spec: StructureSpec):
    p = spec.params
    return _fibonacci_sphere_merged(p["count"], p["sphere_radius"], p["anchor_radius"])


@_register("Sierpinski_Tet3")
def _build_sierpinski(spec: StructureSpec):
    p = spec.params
    return _sierpinski_tet(p["edge"], p["depth"])


@_register("StellatedIcosahedron")
def _build_stellated(spec: StructureSpec):
    p = spec.params
    return _stellated_icosahedron(p["radius"], p["stellate"])


@_register("Armillary_Nested")
def _build_armillary(spec: StructureSpec):
    """Merged torus primitives — requires UE; fallback = three orthogonal rings as polylines."""
    p = spec.params
    all_verts: list[tuple[float, float, float]] = []
    all_tris: list[tuple[int, int, int]] = []
    for idx, major in enumerate(p["radii"]):
        samples = 180
        for axis in range(3):
            pts = []
            for i in range(samples):
                t = (2 * math.pi * i) / samples
                c, s = major * math.cos(t), major * math.sin(t)
                if axis == 0:
                    pts.append((0, c, s))
                elif axis == 1:
                    pts.append((c, 0, s))
                else:
                    pts.append((c, s, 0))
            v, t = _tube_along_polyline(pts, p["tube"])
            off = len(all_verts)
            all_verts.extend(v)
            all_tris.extend((a + off, b + off, c + off) for a, b, c in t)
    return all_verts, all_tris


# --- UE bake ------------------------------------------------------------------

def _ensure_dirs(unreal, *paths: str) -> None:
    for path in paths:
        if not unreal.EditorAssetLibrary.does_directory_exist(path):
            unreal.EditorAssetLibrary.make_directory(path)


def _mesh_basic_edit_api(unreal):
    """Resolve GeometryScript mesh edit module (naming varies by UE minor version)."""
    for name in dir(unreal):
        if "basicedit" not in name.lower():
            continue
        mod = getattr(unreal, name)
        if hasattr(mod, "append_buffers_to_mesh"):
            return mod
    for name in (
        "GeometryScript_MeshBasicEdit",
        "GeometryScript_MeshBasicEditFunctions",
        "GeometryScript_MeshEdits",
    ):
        if hasattr(unreal, name):
            mod = getattr(unreal, name)
            if hasattr(mod, "append_buffers_to_mesh"):
                return mod
    raise AttributeError("GeometryScript append_buffers_to_mesh API not found")


def _finalize_static_mesh(unreal, dm, asset_path: str, tri_count: int, key: str) -> BakeReport:
    unreal.GeometryScript_Normals.recompute_normals(
        dm, unreal.GeometryScriptCalculateNormalsOptions())
    out = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        dm, asset_path, out)
    unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
    return BakeReport(key, asset_path, "baked", tri_count)


def _transform_between(p0, p1) -> "unreal.Transform":
    import unreal
    import math as _math
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    length = _math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-4:
        return unreal.Transform(unreal.Vector(*p0), unreal.Rotator(0, 0, 0), unreal.Vector(1, 1, 1))
    rot = unreal.MathLibrary.make_rot_from_z(unreal.Vector(dx / length, dy / length, dz / length))
    mid = unreal.Vector((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2)
    return unreal.Transform(mid, rot, unreal.Vector(1, 1, 1))


def _bake_polyline_tube(
    points: Sequence[tuple[float, float, float]],
    tube_radius: float,
    asset_path: str,
    *,
    closed: bool = True,
    force: bool = False,
) -> BakeReport:
    import unreal

    key = asset_path.rsplit("/", 1)[-1]
    if not force and unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return BakeReport(key, asset_path, "skipped_exists")
    _ensure_dirs(unreal, asset_path.rsplit("/", 1)[0])

    dm = unreal.new_object(unreal.DynamicMesh)
    prim_opts = unreal.GeometryScriptPrimitiveOptions()
    gs = unreal.GeometryScript_Primitives
    segments = len(points) if closed else len(points) - 1
    for i in range(segments):
        p0 = points[i]
        p1 = points[(i + 1) % len(points)]
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        dz = p1[2] - p0[2]
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if length < 1e-3:
            continue
        xform = _transform_between(p0, p1)
        gs.append_capsule(
            dm, prim_opts, xform, tube_radius, length, 5, 10, 4,
            unreal.GeometryScriptPrimitiveOriginMode.CENTER, None)
    return _finalize_static_mesh(unreal, dm, asset_path, segments, key)


def _bake_sphere(asset_path: str, radius: float, *, force: bool = False) -> BakeReport:
    import unreal

    key = asset_path.rsplit("/", 1)[-1]
    if not force and unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return BakeReport(key, asset_path, "skipped_exists")
    _ensure_dirs(unreal, asset_path.rsplit("/", 1)[0])
    dm = unreal.new_object(unreal.DynamicMesh)
    prim_opts = unreal.GeometryScriptPrimitiveOptions()
    xform = unreal.Transform()
    unreal.GeometryScript_Primitives.append_sphere_lat_long(
        dm, prim_opts, xform, radius, 16, 24,
        unreal.GeometryScriptPrimitiveOriginMode.CENTER, None)
    return _finalize_static_mesh(unreal, dm, asset_path, 16 * 24 * 2, key)


def _bake_triangle_mesh(
    vertices: Sequence[tuple[float, float, float]],
    triangles: Sequence[tuple[int, int, int]],
    asset_path: str,
    *,
    force: bool = False,
) -> BakeReport:
    import unreal

    key = asset_path.rsplit("/", 1)[-1]
    if not force and unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return BakeReport(key, asset_path, "skipped_exists")

    folder = asset_path.rsplit("/", 1)[0]
    _ensure_dirs(unreal, folder)

    dm = unreal.new_object(unreal.DynamicMesh)
    gsb = _mesh_basic_edit_api(unreal)
    buffers = unreal.GeometryScriptSimpleMeshBuffers()
    buffers.vertices = [unreal.Vector(x, y, z) for x, y, z in vertices]
    buffers.triangles = [unreal.IntVector(a, b, c) for a, b, c in triangles]
    buffers.uv0 = [unreal.Vector2D(0.0, 0.0) for _ in vertices]
    gsb.append_buffers_to_mesh(dm, buffers, 0, False)
    return _finalize_static_mesh(unreal, dm, asset_path, len(triangles), key)


_TUBE_KEYS = {"TorusKnot_2_3", "Epitrochoid_Ring", "LissajousRail_3_2_1", "TrefoilKnot", "Kepler_Orbit_A"}


def build_structure(key: str, *, force: bool = False) -> BakeReport:
    spec = STRUCTURES[key]
    try:
        import unreal  # noqa: F401
    except ImportError:
        return BakeReport(key, spec.asset_path, "pending_ue", error="not in editor")

    if key == "Icosahedron":
        return _bake_sphere(spec.asset_path, spec.params["radius"], force=force)

    if key in _TUBE_KEYS:
        builder = BUILDERS.get(key)
        if not builder:
            return BakeReport(key, spec.asset_path, "error", error="no builder")
        p = spec.params
        if key == "TorusKnot_2_3":
            pts = _torus_knot_points(p["p"], p["q"], p["R"], p["r"], p["samples"])
            return _bake_polyline_tube(pts, p["tube"], spec.asset_path, force=force)
        if key == "Epitrochoid_Ring":
            pts = _epitrochoid_points(p["R"], p["r"], p["d"], p["samples"])
            return _bake_polyline_tube(pts, p["tube"], spec.asset_path, force=force)
        if key == "LissajousRail_3_2_1":
            pts = _lissajous_points(p["scale"], p["samples"])
            return _bake_polyline_tube(pts, p["tube"], spec.asset_path, closed=False, force=force)
        if key == "TrefoilKnot":
            pts = _trefoil_points(p["scale"], p["samples"])
            return _bake_polyline_tube(pts, p["tube"], spec.asset_path, force=force)
        if key == "Kepler_Orbit_A":
            pts = _kepler_orbit_points(p["a"], p["e"], p["samples"])
            return _bake_polyline_tube(pts, p["tube"], spec.asset_path, force=force)

    builder = BUILDERS.get(key)
    if not builder:
        return BakeReport(key, spec.asset_path, "error", error="no builder")
    verts, tris = builder(spec)
    if not verts or not tris:
        return BakeReport(key, spec.asset_path, "error", error="empty mesh")
    return _bake_triangle_mesh(verts, tris, spec.asset_path, force=force)


def build_run_group(group: int, *, force: bool = False) -> list[BakeReport]:
    reports = []
    for key, spec in STRUCTURES.items():
        if spec.run_group == group:
            reports.append(build_structure(key, force=force))
    return reports


def build_all(*, force: bool = False) -> list[BakeReport]:
    return [build_structure(k, force=force) for k in STRUCTURES]


def write_audit(reports: Iterable[BakeReport], run_note: str = "") -> Path:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "run_note": run_note,
        "structures": {
            r.key: {
                "asset_path": r.asset_path,
                "status": r.status,
                "triangle_count": r.triangle_count,
                "error": r.error,
            }
            for r in reports
        },
        "catalog": "Docs/GEOMETRYSCRIPT_MATH_CATALOG.md",
    }
    AUDIT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return AUDIT_PATH


# --- Vector helpers -----------------------------------------------------------

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _normalize(v):
    mag = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if mag < 1e-8:
        return (0.0, 0.0, 1.0)
    return (v[0] / mag, v[1] / mag, v[2] / mag)


def _scale(v, s):
    return (v[0] * s, v[1] * s, v[2] * s)


def _mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)


def _center_mesh(verts, tris):
    if not verts:
        return verts, tris
    cx = sum(v[0] for v in verts) / len(verts)
    cy = sum(v[1] for v in verts) / len(verts)
    cz = sum(v[2] for v in verts) / len(verts)
    return [(v[0] - cx, v[1] - cy, v[2] - cz) for v in verts], tris


def _parse_args(argv: list[str]) -> dict:
    out = {"structure": None, "run": 1, "all": False, "force": False, "dry": False}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--structure" and i + 1 < len(argv):
            out["structure"] = argv[i + 1]
            i += 2
        elif arg == "--run" and i + 1 < len(argv):
            out["run"] = int(argv[i + 1])
            i += 2
        elif arg == "--all":
            out["all"] = True
            i += 1
        elif arg == "--force":
            out["force"] = True
            i += 1
        elif arg == "--dry":
            out["dry"] = True
            i += 1
        else:
            i += 1
    return out


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    if args["dry"]:
        reports = [
            BakeReport(k, STRUCTURES[k].asset_path, "dry_run", triangle_count=0)
            for k in (STRUCTURES if args["all"] else [s.key for s in STRUCTURES.values() if s.run_group == args["run"]])
        ]
        path = write_audit(reports, run_note="dry_run")
        print(json.dumps({"audit": str(path), "reports": [r.__dict__ for r in reports]}, indent=2))
        return 0

    if args["structure"]:
        reports = [build_structure(args["structure"], force=args["force"])]
    elif args["all"]:
        reports = build_all(force=args["force"])
    else:
        reports = build_run_group(args["run"], force=args["force"])

    path = write_audit(reports, run_note=f"run_group_{args['run']}")
    print(json.dumps({"audit": str(path), "reports": [r.__dict__ for r in reports]}, indent=2))
    passed = all(r.status in ("baked", "skipped_exists") for r in reports)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
