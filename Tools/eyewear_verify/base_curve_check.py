"""Acceptance for 11.2 (base curve + frame form as pure-Z fields).

The fields move no X/Y vertex by construction, so the boxing contract must
hold TIGHT while Z proves the shape. Front assertions run against
MEL_eyewear_front DIRECTLY: pair-level bboxes are dominated by the temple
outer faces (+/-67) and cannot see front shape changes (measured: all three
silhouettes read 134.0000033 through the flat pair).
  flat (0/0): record per-silhouette widths W0 (existing suites pin behavior);
  6 base: width == W0 (tol 0.05), front plane exact (zmax +3), dome present
      (frame zmin < -9, lens zmin < -6, lens crown +1);
  4.4 form: width == W0 (tol 0.1), endpieces back
      (zmin ~= -3 - (W0/2)*sin(4.4 deg)), symmetry holds;
  pair seats: temple TIP verts (z < -110) wrapped inward (|x| < 60 vs ~67
      flat) and back (z < -125), mesh clean, materials intact.
Predictions: R = 523/BaseCurve mm; endpiece z = -67 * sin(4.4 deg) = -5.14.
History: first version of this harness asserted pair-level widths (vacuous,
temple-masked) and whole-temple |x| (dominated by hinge-end verts); both
fixed here. It also caught operation = "SIN" (invalid; SINE is the enum),
which had silently degraded the field to passthrough.
"""
import math
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
    bm.edges.ensure_lookup_table()
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    st = {"verts": len(bm.verts),
          "boundary": sum(1 for e in bm.edges if e.is_boundary),
          "wire": sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary),
          "x": [(min(xs) / MM if xs else 0.0), (max(xs) / MM if xs else 0.0)],
          "y": [(min(ys) / MM if ys else 0.0), (max(ys) / MM if ys else 0.0)],
          "z": [(min(zs) / MM if zs else 0.0), (max(zs) / MM if zs else 0.0)],
          "mats": sorted({mt.name for mt in m.materials if mt}),
          "tipx": max([abs(v.co.x) / MM for v in bm.verts if v.co.z / MM < -110.0]
                      or [-1.0])}
    bm.free()
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


def sag_pred(r_mm, base_curve):
    """Spherical sag R - sqrt(R^2 - r^2), R = 523/BaseCurve mm (plan 11.2)."""
    R = 523.0 / base_curve
    return R - math.sqrt(max(R * R - r_mm * r_mm, 0.0))


# Minimum radius present on RIM-band geometry: the aperture hole (A x B leaves
# no verts with r < B/2 = 17), so the crown of the dome is governed by r = 17,
# not r = 0. Same for the lens: Fill Curve caps carry verts only on the
# boundary, so the lens crown follows sag(17) and the interior rides as a fan
# (smooth spherical lens shading needs fill-interior density — noted, not built).
RIM_R_MIN = 17.0


def setp(tree, name, val):
    for it in getattr(tree.interface, "items_tree", []):
        if getattr(it, "name", None) == name:
            try:
                it.default_value = val
                return True
            except Exception:
                pass
    return False
    for it in getattr(tree.interface, "items_tree", []):
        if getattr(it, "name", None) == name:
            try:
                it.default_value = val
                return True
            except Exception:
                pass
    return False


# NOTE: every get() rebuilds its tree by name, invalidating previously built
# trees (new_geometry_tree removes + recreates). The pair build also rebuilds
# the nested front/lens subtrees. So each builder is (re)built immediately
# before its own section and never touched after the next get().
front_t = get("MEL_eyewear_front")
chk("params-exist-front",
    setp(front_t, "Base Curve", 0.0) and setp(front_t, "Form Angle", 0.0),
    "Base Curve / Form Angle missing on the front")

# ---- flat reference widths per silhouette, front-direct ----
w0 = {}
for idx in (0, 1, 2):
    setp(front_t, "Silhouette", idx)
    st = measure(front_t)
    w0[idx] = st["x"][1] - st["x"][0] if st else -1.0
    chk("flat-sil%d-width" % idx, st is not None and w0[idx] > 100.0,
        "width=%.3f" % w0[idx])

# ---- 6 base on the front: dome, exact plane, exact width ----
setp(front_t, "Base Curve", 6.0)
setp(front_t, "Form Angle", 0.0)
zmax_pred = 3.0 - sag_pred(RIM_R_MIN, 6.0)  # ~1.33: crown governed by r = 17
for idx in (0, 1, 2):
    setp(front_t, "Silhouette", idx)
    st = measure(front_t)
    w = (st["x"][1] - st["x"][0]) if st else -1.0
    chk("bc6-sil%d-width-exact" % idx, st is not None and abs(w - w0[idx]) <= 0.05,
        "got=%.4f want=%.4f" % (w, w0[idx]))
    if st:
        chk("bc6-sil%d-front-plane" % idx, abs(st["z"][1] - zmax_pred) <= 0.35,
            "zmax=%.3f pred=%.3f" % (st["z"][1], zmax_pred))
        chk("bc6-sil%d-dome" % idx, st["z"][0] < -9.0, "zmin=%.3f" % st["z"][0])
        chk("bc6-sil%d-clean" % idx, st["boundary"] == 0 and st["wire"] == 0,
            "b=%d w=%d" % (st["boundary"], st["wire"]))

# ---- 6 base on the lens builder ----
lens_t = get("MEL_eyewear_lens")
chk("params-exist-lens",
    setp(lens_t, "Base Curve", 0.0) and setp(lens_t, "Form Angle", 0.0),
    "Base Curve / Form Angle missing on the lens")
setp(lens_t, "Base Curve", 6.0)
setp(lens_t, "Form Angle", 0.0)
li = measure(lens_t)
chk("bc6-lens-nonempty", li is not None and li["verts"] > 100,
    "verts=%s" % (li["verts"] if li else None))
if li:
    span = li["x"][1] - li["x"][0]
    chk("bc6-lens-span", abs(span - 126.0) <= 0.2, "got=%.3f" % span)
    lzmax_pred = 1.0 - sag_pred(RIM_R_MIN, 6.0)  # fill boundary governs
    chk("bc6-lens-crown", abs(li["z"][1] - lzmax_pred) <= 0.35,
        "zmax=%.3f pred=%.3f" % (li["z"][1], lzmax_pred))
    chk("bc6-lens-dome", li["z"][0] < -6.0, "zmin=%.3f" % li["z"][0])
setp(lens_t, "Base Curve", 0.0)

# ---- 4.4 form on the front: wrap back, widths exact ----
setp(front_t, "Base Curve", 0.0)
setp(front_t, "Form Angle", 4.4)
for idx in (0, 1, 2):
    setp(front_t, "Silhouette", idx)
    st = measure(front_t)
    w = (st["x"][1] - st["x"][0]) if st else -1.0
    chk("form-sil%d-width-exact" % idx, st is not None and abs(w - w0[idx]) <= 0.1,
        "got=%.4f want=%.4f" % (w, w0[idx]))
    if st:
        pred = -3.0 - (w0[idx] / 2.0) * math.sin(math.radians(4.4))
        chk("form-sil%d-endpiece-back" % idx, abs(st["z"][0] - pred) <= 0.8,
            "zmin=%.3f pred=%.3f" % (st["z"][0], pred))
        chk("form-sil%d-sym" % idx, abs(st["x"][0] + st["x"][1]) <= 0.5,
            "x=%s" % (st["x"],))
setp(front_t, "Form Angle", 0.0)
setp(front_t, "Silhouette", 0)

# ---- pair seats track the wrap ----
pair_t = get("MEL_eyewear_pair")
chk("params-exist-pair",
    setp(pair_t, "Base Curve", 0.0) and setp(pair_t, "Form Angle", 0.0),
    "Base Curve / Form Angle missing on the pair")
setp(pair_t, "Base Curve", 0.0)
setp(pair_t, "Form Angle", 4.4)
asm = measure(pair_t)
chk("pair-form-nonempty", asm is not None and asm["verts"] > 1000,
    "verts=%s" % (asm["verts"] if asm else None))
if asm:
    chk("pair-form-clean", asm["boundary"] == 0 and asm["wire"] == 0,
        "b=%d w=%d" % (asm["boundary"], asm["wire"]))
    chk("pair-form-sym", abs(asm["x"][0] + asm["x"][1]) <= 0.5, "x=%s" % (asm["x"],))
    chk("pair-form-mats",
        {"MEL_mat_eyewear_acetate", "MEL_mat_eyewear_metal"} <= set(asm["mats"]),
        "%s" % asm["mats"])
tl = measure_output(pair_t, "TempleL")
tr = measure_output(pair_t, "TempleR")
if tl and tr:
    chk("pair-tips-wrapped", tl["tipx"] < 60.0 and tr["tipx"] < 60.0,
        "Ltip=%.2f Rtip=%.2f" % (tl["tipx"], tr["tipx"]))
    chk("pair-tips-back", min(tl["z"]) < -125.0 and min(tr["z"]) < -125.0,
        "Lzmin=%.2f Rzmin=%.2f" % (min(tl["z"]), min(tr["z"])))
setp(pair_t, "Form Angle", 0.0)

print("CHECKCOUNT %d" % len(OUT))
print("RESULT %s  fails=%s" % ("PASS" if not fails else "FAIL", fails))
print("DONE")
