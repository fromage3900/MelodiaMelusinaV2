"""Verify eyewear builders — registration, build, material slots."""
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
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return co


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
    co = measure(tree)
    chk("%s builds mesh" % name, len(co) > 0, "verts=%d" % len(co))

print()
print("C. Assembled pair")
tree = get("MEL_eyewear_pair")
co = measure(tree)
xs = [c[0] for c in co]
w = max(xs) - min(xs) if co else 0
chk("pair width ~134 mm", abs(w - 134.0) < 1.0, "w=%.2f" % w)

print()
print("D. Hero builder")
tree = get("MEL_eyewear_hero")
co = measure(tree)
chk("hero builds mesh", len(co) > 0, "verts=%d" % len(co))

print()
print("E. Silhouette variants (front builder)")
for idx, label in ((0, "rect"), (1, "panto"), (2, "cat-eye")):
    tree = get("MEL_eyewear_front")
    for it in tree.interface.items_tree:
        if getattr(it, "name", None) == "Silhouette" and getattr(it, "in_out", None) == "INPUT":
            it.default_value = idx
    co = measure(tree)
    chk("silhouette %s (%d) builds" % (label, idx), len(co) > 0, "verts=%d" % len(co))

print()
print("RESULT %s" % ("PASS" if not fails else "FAIL"))
for f in fails:
    print("  - %s" % f)
print("DONE")
