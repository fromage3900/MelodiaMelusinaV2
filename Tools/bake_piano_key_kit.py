"""Bake the AAA piano key kit (white key, black key, keybed slab) as FBX for the walkway keyboard.

Run headless (Blender 5.2):
  blender --background --python Tools/bake_piano_key_kit.py -- [out_dir]

Meshes are authored at the walkway profile's real size (pcg_piano_walkway.WALKWAY_DIMS: white 110x360x30 cm,
black 64x220x36 cm) so the keyboard's size-to-mesh scaling stays 1:1 and bevels are never stretched.
Two material slots per key: 0 = body (ivory / ebony instance), 1 = accent (gold inlay / gloss panel).
UV0 is a planar top projection (u = across, v = along). Staging only: nothing is written into Content/.
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv and len(sys.argv) > sys.argv.index("--") + 1 else ROOT / "Saved" / "Staging" / "PianoKey_AAA"
OUT.mkdir(parents=True, exist_ok=True)

W_W, W_D, W_H = 1.10, 3.60, 0.30          # white key (m)
B_W, B_D, B_H = 0.64, 2.20, 0.36          # black key (m)
BEVEL = 0.018


def frustum(bm, w_bot, d_bot, w_top, d_top, h, z0=0.0, mat=0):
    """Axis-aligned frustum centred on XY, base at z0."""
    pts = [(-w_bot / 2, -d_bot / 2, z0), (w_bot / 2, -d_bot / 2, z0), (w_bot / 2, d_bot / 2, z0), (-w_bot / 2, d_bot / 2, z0),
           (-w_top / 2, -d_top / 2, z0 + h), (w_top / 2, -d_top / 2, z0 + h), (w_top / 2, d_top / 2, z0 + h), (-w_top / 2, d_top / 2, z0 + h)]
    v = [bm.verts.new(p) for p in pts]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    out = []
    for f in faces:
        fc = bm.faces.new([v[i] for i in f])
        fc.material_index = mat
        out.append(fc)
    return out


def bevel_all(bm, width=BEVEL, segments=3):
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=width, segments=segments, profile=0.55, affect="EDGES")


def planar_uv(bm, w, d):
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for l in f.loops:
            l[uv].uv = (l.vert.co.x / w + 0.5, l.vert.co.y / d + 0.5)


def white_key():
    bm = bmesh.new()
    frustum(bm, W_W, W_D, W_W, W_D, W_H, z0=-W_H / 2, mat=0)
    bevel_all(bm, BEVEL * 1.4, 4)
    # gold inlay: thin frame inset on the top face, proud of the surface by 4 mm
    inset, thick, top = 0.07, 0.014, W_H / 2
    bars = [((W_W - 2 * inset), thick, 0.0, (W_D / 2 - inset)), ((W_W - 2 * inset), thick, 0.0, -(W_D / 2 - inset)),
            (thick, (W_D - 2 * inset), (W_W / 2 - inset), 0.0), (thick, (W_D - 2 * inset), -(W_W / 2 - inset), 0.0)]
    for bw, bd, cx, cy in bars:
        fs = frustum(bm, bw, bd, bw * 0.9, bd * 0.9, 0.004, z0=top - 0.001, mat=1)
        bmesh.ops.translate(bm, verts=list({v for f in fs for v in f.verts}), vec=Vector((cx, cy, 0.0)))
    planar_uv(bm, W_W, W_D)
    return bm


def black_key():
    bm = bmesh.new()
    frustum(bm, B_W, B_D, B_W * 0.72, B_D * 0.9, B_H, z0=-B_H / 2, mat=0)
    bevel_all(bm, BEVEL * 1.2, 4)
    top = B_H / 2
    frustum(bm, B_W * 0.46, B_D * 0.70, B_W * 0.40, B_D * 0.64, 0.004, z0=top - 0.002, mat=1)   # gloss panel
    planar_uv(bm, B_W, B_D)
    return bm


def keybed():
    bm = bmesh.new()
    frustum(bm, 1.0, 1.0, 1.0, 1.0, 0.12, z0=-0.06, mat=0)   # unit slab; scaled by the keyboard to the run length
    bevel_all(bm, 0.01, 2)
    planar_uv(bm, 1.0, 1.0)
    return bm


def make(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for mname in ("Body", "Accent"):
        me.materials.append(bpy.data.materials.get(name + "_" + mname) or bpy.data.materials.new(name + "_" + mname))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    return ob


report = {"blender": bpy.app.version_string, "meshes": {}}
for name, builder in (("SM_PianoKey_AAA_White", white_key), ("SM_PianoKey_AAA_Black", black_key), ("SM_PianoKey_AAA_Keybed", keybed)):
    ob = make(name, builder())
    me = ob.data
    xs, ys, zs = [v.co.x for v in me.vertices], [v.co.y for v in me.vertices], [v.co.z for v in me.vertices]
    report["meshes"][name] = {"verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons),
                              "bounds_cm": {"x": [round(min(xs) * 100, 2), round(max(xs) * 100, 2)], "y": [round(min(ys) * 100, 2), round(max(ys) * 100, 2)],
                                            "z": [round(min(zs) * 100, 2), round(max(zs) * 100, 2)]}}
    bpy.ops.export_scene.fbx(filepath=str(OUT / (name + ".fbx")), use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Y", axis_up="Z", mesh_smooth_type="FACE", add_leaf_bones=False)
    print("BAKED", name, report["meshes"][name])
(OUT / "bake_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("REPORT", OUT / "bake_report.json")
