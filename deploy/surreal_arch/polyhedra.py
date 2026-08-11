# -*- coding: utf-8 -*-
"""Polyhedra mesh builders — Kepler-Poinsot, Platonic, Archimedean, compounds."""

from __future__ import annotations

import math

import bpy
import bmesh

PHI = (1.0 + math.sqrt(5.0)) / 2.0


def _bm_to_mesh(bm, name: str):
    mesh = bpy.data.meshes.new(name=name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _scale_coords(coords, size: float):
    return [(c[0] * size, c[1] * size, c[2] * size) for c in coords]


def _build_from_verts_faces(verts, faces, name: str, size: float = 1.0):
    bm = bmesh.new()
    bm_verts = [bm.verts.new(v) for v in _scale_coords(verts, size)]
    bm.verts.ensure_lookup_table()
    for f in faces:
        try:
            bm.faces.new([bm_verts[i] for i in f])
        except Exception:
            pass
    bm.normal_update()
    return _bm_to_mesh(bm, name)


def build_dodecahedron_bmesh(bm, size=1.0):
    inv = 1.0 / PHI
    coords = [
        (-1, -1, -1), (-1, -1, 1), (-1, 1, -1), (-1, 1, 1),
        (1, -1, -1), (1, -1, 1), (1, 1, -1), (1, 1, 1),
        (0, -inv, -PHI), (0, -inv, PHI),
        (0, inv, -PHI), (0, inv, PHI),
        (-inv, -PHI, 0), (-inv, PHI, 0),
        (inv, -PHI, 0), (inv, PHI, 0),
        (-PHI, 0, -inv), (-PHI, 0, inv),
        (PHI, 0, -inv), (PHI, 0, inv),
    ]
    bm_verts = [bm.verts.new((c[0] * size, c[1] * size, c[2] * size)) for c in coords]
    bm.verts.ensure_lookup_table()
    pent_faces = [
        [0, 8, 10, 2, 16], [0, 16, 17, 1, 12], [0, 12, 14, 4, 8],
        [4, 14, 5, 19, 18], [4, 18, 6, 10, 8], [5, 14, 12, 1, 9],
        [3, 17, 16, 2, 13], [3, 13, 15, 7, 11], [3, 11, 9, 1, 17],
        [7, 15, 6, 18, 19], [7, 19, 5, 9, 11], [2, 10, 6, 15, 13],
    ]
    for f in pent_faces:
        try:
            bm.faces.new([bm_verts[i] for i in f])
        except Exception:
            pass
    bm.normal_update()
    return bm_verts


def build_kepler_poinsot(kind: str, size: float = 1.0):
    bm = bmesh.new()
    if kind == "SSDC":
        build_dodecahedron_bmesh(bm, size=size)
        res = bmesh.ops.poke(bm, faces=bm.faces[:])
        for v in res["verts"]:
            length = v.co.length
            if length > 1e-6:
                v.co *= (size * 2.5) / length
    elif kind == "GD":
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=size, calc_uvs=False)
        res = bmesh.ops.poke(bm, faces=bm.faces[:])
        for v in res["verts"]:
            length = v.co.length
            if length > 1e-6:
                v.co *= (size * 0.45) / length
    elif kind == "GSDC":
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=size, calc_uvs=False)
        res = bmesh.ops.poke(bm, faces=bm.faces[:])
        for v in res["verts"]:
            length = v.co.length
            if length > 1e-6:
                v.co *= (size * 2.8) / length
    elif kind == "GI":
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=size, calc_uvs=False)
        for push in (1.55, 1.7):
            res = bmesh.ops.poke(bm, faces=bm.faces[:])
            for v in res["verts"]:
                length = v.co.length
                if length > 1e-6:
                    v.co *= (size * push) / length
    else:
        bm.free()
        raise ValueError(f"Unknown Kepler kind: {kind}")
    bm.normal_update()
    return _bm_to_mesh(bm, f"KeplerPoinsot_{kind}")


def build_tetrahedron(size: float = 1.0):
    s = size * 1.2
    verts = [(s, s, s), (s, -s, -s), (-s, s, -s), (-s, -s, s)]
    faces = [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]]
    return _build_from_verts_faces(verts, faces, "Platonic_TET", size)


def build_cube(size: float = 1.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size * 2.0)
    bm.normal_update()
    return _bm_to_mesh(bm, "Platonic_CUBE")


def build_octahedron(size: float = 1.0):
    verts = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    faces = [
        [0, 2, 4], [2, 1, 4], [1, 3, 4], [3, 0, 4],
        [2, 0, 5], [1, 2, 5], [3, 1, 5], [0, 3, 5],
    ]
    return _build_from_verts_faces(verts, faces, "Platonic_OCT", size)


def build_dodecahedron(size: float = 1.0):
    bm = bmesh.new()
    build_dodecahedron_bmesh(bm, size=size)
    return _bm_to_mesh(bm, "Platonic_DODEC")


def build_icosahedron(size: float = 1.0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=size, calc_uvs=False)
    bm.normal_update()
    return _bm_to_mesh(bm, "Platonic_ICOS")


def build_cuboctahedron(size: float = 1.0):
    verts = [
        (1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0),
        (1, 0, 1), (1, 0, -1), (-1, 0, 1), (-1, 0, -1),
        (0, 1, 1), (0, 1, -1), (0, -1, 1), (0, -1, -1),
    ]
    faces = [
        [0, 4, 8], [0, 8, 6], [0, 6, 5], [0, 5, 4],
        [1, 5, 11], [1, 11, 10], [1, 10, 4], [1, 4, 5],
        [2, 8, 9], [2, 9, 7], [2, 7, 6], [2, 6, 8],
        [3, 7, 11], [3, 11, 10], [3, 10, 6], [3, 6, 7],
        [8, 4, 10], [9, 8, 10], [9, 10, 11], [7, 9, 11],
    ]
    return _build_from_verts_faces(verts, faces, "Archimedean_CUBOCTA", size * 0.7)


def build_truncated_icosahedron(size: float = 1.0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=size, calc_uvs=False)
    bmesh.ops.beautify_fill(bm, faces=bm.faces[:])
    bm.normal_update()
    return _bm_to_mesh(bm, "Archimedean_TRUNC_ICOS")


def build_rhombicuboctahedron(size: float = 1.0):
    s = 1.0 + math.sqrt(2.0)
    verts = []
    for i in (-1, 1):
        for j in (-1, 1):
            for k in (-1, 1):
                verts.append((i * s, j, k))
            verts.append((i, j * s, k))
            verts.append((i, j, k * s))
    faces = [
        [0, 8, 10, 2], [2, 10, 18, 4], [4, 18, 12, 6], [6, 12, 8, 0],
        [1, 3, 11, 9], [5, 7, 15, 13], [16, 17, 19, 18], [20, 21, 23, 22],
    ]
    # Use convex hull for robust face set
    bm = bmesh.new()
    for v in _scale_coords(verts, size * 0.45):
        bm.verts.new(v)
    bm.verts.ensure_lookup_table()
    try:
        bmesh.ops.convex_hull(bm, input=bm.verts[:])
    except Exception:
        pass
    bm.normal_update()
    return _bm_to_mesh(bm, "Archimedean_RHOMBICUBOCTA")


def build_stella_octangula(size: float = 1.0):
    verts = [
        (1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1),
        (-1, -1, -1), (-1, 1, 1), (1, -1, 1), (1, 1, -1),
    ]
    faces = [
        [0, 2, 1], [0, 1, 3], [0, 3, 2],
        [4, 5, 6], [4, 6, 7], [4, 7, 5],
        [5, 2, 6], [6, 2, 7], [7, 2, 5],
    ]
    return _build_from_verts_faces(verts, faces, "Compound_STELLA_OCTANGULA", size * 0.8)


def build_rhombic_dodecahedron(size: float = 1.0):
    verts = [
        (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
        (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1),
        (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1),
    ]
    faces = [
        [0, 6, 2, 10], [0, 8, 4, 6], [0, 7, 8, 6], [0, 10, 4, 8],
        [1, 12, 2, 10], [1, 11, 12, 10], [1, 13, 11, 12], [1, 13, 12, 2],
        [3, 9, 4, 8], [3, 13, 9, 8], [3, 9, 13, 1], [3, 1, 2, 9],
        [5, 7, 6, 8], [5, 11, 7, 6], [5, 11, 6, 10], [5, 10, 2, 11],
    ]
    bm = bmesh.new()
    for v in _scale_coords(verts, size * 0.9):
        bm.verts.new(v)
    bm.verts.ensure_lookup_table()
    try:
        bmesh.ops.convex_hull(bm, input=bm.verts[:])
    except Exception:
        for f in faces:
            try:
                bm.faces.new([bm.verts[i] for i in f])
            except Exception:
                pass
    bm.normal_update()
    return _bm_to_mesh(bm, "Compound_RHOMBIC_DODEC")


POLYHEDRA_REGISTRY = {
    "SSDC": {"label": "Small Stellated Dodecahedron", "group": "kepler", "emoji": "⭐", "build": lambda s: build_kepler_poinsot("SSDC", s)},
    "GD": {"label": "Great Dodecahedron", "group": "kepler", "emoji": "🔶", "build": lambda s: build_kepler_poinsot("GD", s)},
    "GSDC": {"label": "Great Stellated Dodecahedron", "group": "kepler", "emoji": "✦", "build": lambda s: build_kepler_poinsot("GSDC", s)},
    "GI": {"label": "Great Icosahedron", "group": "kepler", "emoji": "✸", "build": lambda s: build_kepler_poinsot("GI", s)},
    "TET": {"label": "Tetrahedron", "group": "platonic", "emoji": "🔺", "build": build_tetrahedron},
    "CUBE": {"label": "Cube", "group": "platonic", "emoji": "⬛", "build": build_cube},
    "OCT": {"label": "Octahedron", "group": "platonic", "emoji": "💎", "build": build_octahedron},
    "DODEC": {"label": "Dodecahedron", "group": "platonic", "emoji": "⬡", "build": build_dodecahedron},
    "ICOS": {"label": "Icosahedron", "group": "platonic", "emoji": "🔷", "build": build_icosahedron},
    "CUBOCTA": {"label": "Cuboctahedron", "group": "archimedean", "emoji": "🔘", "build": build_cuboctahedron},
    "TRUNC_ICOS": {"label": "Truncated Icosahedron", "group": "archimedean", "emoji": "⚽", "build": build_truncated_icosahedron},
    "RHOMBICUBOCTA": {"label": "Rhombicuboctahedron", "group": "archimedean", "emoji": "🔳", "build": build_rhombicuboctahedron},
    "STELLA_OCTANGULA": {"label": "Stella Octangula", "group": "compound", "emoji": "✡", "build": build_stella_octangula},
    "RHOMBIC_DODEC": {"label": "Rhombic Dodecahedron", "group": "compound", "emoji": "♦", "build": build_rhombic_dodecahedron},
}

GROUP_LABELS = {
    "kepler": "Kepler–Poinsot",
    "platonic": "Platonic Solids",
    "archimedean": "Archimedean",
    "compound": "Compounds",
}


def spawn_polyhedron(context, kind: str, label: str | None = None):
    """Spawn a polyhedron at the 3D cursor."""
    entry = POLYHEDRA_REGISTRY.get(kind)
    if not entry:
        raise ValueError(f"Unknown polyhedron kind: {kind}")
    size = 1.0
    active = context.active_object
    if active and hasattr(active, "surreal_arch_props"):
        size = max(0.2, getattr(active.surreal_arch_props, "base_radius", 1.0))
    mesh = entry["build"](size)
    obj_name = label or entry["label"].replace(" ", "")
    obj = bpy.data.objects.new(obj_name, mesh)
    context.collection.objects.link(obj)
    obj.location = context.scene.cursor.location.copy()
    try:
        for poly in obj.data.polygons:
            poly.use_smooth = False
    except Exception:
        pass
    try:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj
    except Exception:
        pass
    return obj
