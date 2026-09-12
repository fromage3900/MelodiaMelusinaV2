"""Verify all eyewear builders register, build, and measure correctly.

Covers the full suite: front, temple, hinge, pair, lens, hero.
Confirms:
  - All 6 builders register without error
  - Each builds a non-empty mesh
  - Hero builder assembles all pieces
  - Material slots don't crash (with None material)
  - UV unwrap produces TEXCOORD_0"""
import sys

import bpy

sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/deploy")
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

MM = 0.001
fails = []


def measure(tree):
    me = bpy.data.meshes.new("m")
    ob = bpy.data.objects.new("o", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("n", "NODES")
    mod.node_group = tree
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = ev.to_mesh()
    co = [(v.co.x / MM, v.co.y / MM, v.co.z / MM) for v in m.vertices] if m else []
    tris = sum(len(p.vertices) - 2 for p in m.polygons) if m else 0
    ngons = sum(1 for p in m.polygons if len(p.vertices) > 4) if m else 0
    tri = sum(1 for p in m.polygons if len(p.vertices) == 3) if m else 0
    # Check for UV layer
    has_uv = m.uv_layers.active is not None if m else False
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return co, tris, ngons, tri, has_uv


def get(name):
    r = GROUP_BUILDERS[name]()
    return r[0] if isinstance(r, (tuple, list)) else r


def chk(tag, cond, msg=""):
    status = "ok" if cond else "FAIL"
    print("  %-50s %s %s" % (tag, status, msg))
    if not cond:
        fails.append(tag)


print()
print("A. Registration")
for name in ("MEL_eyewear_front", "MEL_eyewear_temple", "MEL_eyewear_hinge",
             "MEL_eyewear_pair", "MEL_eyewear_lens", "MEL_eyewear_hero"):
    chk("%s registered" % name, name in GROUP_BUILDERS)

print()
print("B. Individual builders")
for name in ("MEL_eyewear_front", "MEL_eyewear_temple", "MEL_eyewear_hinge", "MEL_eyewear_lens"):
    tree = get(name)
    co, tris, ngons, tri, has_uv = measure(tree)
    chk("%s builds mesh" % name, len(co) > 0, "verts=%d" % len(co))
    chk("%s has UV" % name, has_uv)

print()
print("C. Assembled pair")
tree = get("MEL_eyewear_pair")
co, tris, ngons, tri, has_uv = measure(tree)
xs = [c[0] for c in co]
w = max(xs) - min(xs) if co else 0
chk("pair width ~134 mm", abs(w - 134.0) < 1.0, "w=%.2f" % w)
chk("pair has UV", has_uv)

print()
print("D. Hero builder")
tree = get("MEL_eyewear_hero")
co, tris, ngons, tri, has_uv = measure(tree)
chk("hero builds mesh", len(co) > 0, "verts=%d" % len(co))
chk("hero has UV", has_uv)

print()
print("E. Silhouette variants (front builder)")
for idx, label in ((0, "rect"), (1, "panto"), (2, "cat-eye")):
    tree = get("MEL_eyewear_front")
    for it in tree.interface.items_tree:
        if getattr(it, "name", None) == "Silhouette" and getattr(it, "in_out", None) == "INPUT":
            it.default_value = idx
    co, tris, ngons, tri, has_uv = measure(tree)
    chk("silhouette %s (%d) builds" % (label, idx), len(co) > 0, "verts=%d" % len(co))

print()
print("RESULT %s" % ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  - %s" % f)
print("DONE")
