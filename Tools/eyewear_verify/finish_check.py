"""Acceptance for 11.7 hero variants: Metal Frame switch + Frame Solid.

Metal Frame True routes front + temples to the metal material (hinges are
always metal); False restores acetate. Frame Solid tints the tortoise
writer base (blue probe distinguishes it from espresso/champagne). Widths,
symmetry and Col presence must hold in both finishes.
"""
import os
import sys

import bpy

_WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_WT, "deploy"))
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

MM = 0.001
OUT = {}
fails = []


def chk(tag, cond, detail=""):
    if not cond:
        fails.append("%s %s" % (tag, detail))
    OUT[tag] = {"pass": bool(cond), "detail": detail}
    print(("PASS " if cond else "FAIL ") + tag + ("  " + str(detail) if detail else ""))


def get(name):
    r = GROUP_BUILDERS[name]()
    return r[0] if isinstance(r, (tuple, list)) else r


def build_eval(tree):
    me = bpy.data.meshes.new("__b__")
    ob = bpy.data.objects.new("__o__", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("m", "NODES")
    mod.node_group = tree
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = ev.to_mesh()
    return ev, m, ob, me


def release(ev, m, ob, me):
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)


def stats(m):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(m)
    bm.verts.ensure_lookup_table()
    xs = [v.co.x for v in bm.verts]
    st = {"verts": len(bm.verts),
          "x": [(min(xs) / MM if xs else 0.0), (max(xs) / MM if xs else 0.0)],
          "mats": sorted({mt.name for mt in m.materials if mt})}
    bm.free()
    try:
        ca = m.color_attributes.get("Col")
        bs = [c.color[2] for c in ca.data] if ca is not None else []
        st["maxb"] = max(bs) if bs else -1.0
        st["hascol"] = ca is not None and str(ca.domain) == "CORNER"
    except Exception:
        st["maxb"] = -1.0
        st["hascol"] = False
    return st


def measure(tree):
    ev, m, ob, me = build_eval(tree)
    st = stats(m) if m is not None and len(m.vertices) else None
    release(ev, m, ob, me)
    return st


def measure_output(pair_tree, socket_name):
    wrap = bpy.data.node_groups.new("__part__", "GeometryNodeTree")
    wgi = wrap.nodes.new("NodeGroupInput")
    wgo = wrap.nodes.new("NodeGroupOutput")
    wrap.interface.new_socket(name="Geometry", in_out="INPUT",
                              socket_type="NodeSocketGeometry")
    wrap.interface.new_socket(name="Geometry", in_out="OUTPUT",
                              socket_type="NodeSocketGeometry")
    gn = wrap.nodes.new("GeometryNodeGroup")
    gn.node_tree = pair_tree
    try:
        src = gn.outputs[socket_name]
    except Exception:
        src = None
    if src is None:
        bpy.data.node_groups.remove(wrap)
        return None
    wrap.links.new(wgi.outputs["Geometry"], gn.inputs["Geometry"])
    wrap.links.new(src, wgo.inputs["Geometry"])
    st = measure(wrap)
    bpy.data.node_groups.remove(wrap)
    return st


def setp(tree, name, val):
    for it in getattr(tree.interface, "items_tree", []):
        if getattr(it, "name", None) == name:
            try:
                it.default_value = val
                return True
            except Exception:
                pass
    return False


pair_t = get("MEL_eyewear_pair")
chk("params-exist", setp(pair_t, "Metal Frame", False), "Metal Frame missing")

# ---- metal finish ----
setp(pair_t, "Metal Frame", True)
fr = measure_output(pair_t, "Frame")
chk("metal-frame-nonempty", fr is not None and fr["verts"] > 1000,
    "verts=%s" % (fr["verts"] if fr else None))
if fr:
    chk("metal-frame-mats", set(fr["mats"]) == {"MEL_mat_eyewear_metal"},
        "%s" % fr["mats"])
    w = fr["x"][1] - fr["x"][0]
    chk("metal-frame-width", abs(w - 134.0) <= 3.0, "got=%.3f" % w)
    chk("metal-frame-col", fr["hascol"], "Col missing")
tl = measure_output(pair_t, "TempleL")
if tl:
    chk("metal-temple-mats", set(tl["mats"]) == {"MEL_mat_eyewear_metal"},
        "%s" % tl["mats"])
asm = measure(pair_t)
if asm:
    chk("metal-asm-mats", set(asm["mats"]) == {"MEL_mat_eyewear_metal"},
        "%s" % asm["mats"])
    chk("metal-asm-sym", abs(asm["x"][0] + asm["x"][1]) <= 0.5, "x=%s" % (asm["x"],))

# ---- Frame Solid probe (blue is unambiguous vs espresso/champagne) ----
setp(pair_t, "Metal Frame", False)
for it in getattr(pair_t.interface, "items_tree", []):
    if getattr(it, "name", None) == "Frame Solid":
        try:
            it.default_value = (0.0, 0.0, 1.0, 1.0)
            chk("solid-param", True, "")
        except Exception as exc:
            chk("solid-param", False, str(exc)[:100])
        break
fr = measure_output(pair_t, "Frame")
if fr:
    chk("solid-blue", fr["maxb"] > 0.95, "maxb=%.3f" % fr["maxb"])
    chk("acetate-restored", set(fr["mats"]) == {"MEL_mat_eyewear_acetate",
                                                "MEL_mat_eyewear_metal"},
        "%s" % fr["mats"])

print("CHECKCOUNT %d" % len(OUT))
print("RESULT %s  fails=%s" % ("PASS" if not fails else "FAIL", fails))
print("DONE")
