"""Acceptance for 8.5 (UVMap + export gate).

MEL_eyewear_uv writes a dominant-axis box projection (smooth triplanar
weights, bbox-normalized) to CORNER FLOAT2 'UVMap' -> TEXCOORD_0.
melodia_eyewear_export_gate exports every part with export_apply=True and
asserts: non-empty AND TEXCOORD_0 AND COLOR_0 AND tri/byte budgets. The
export_apply=False 176-byte empty file fails this gate by construction.
Runs the gate twice: flat defaults and the editorial set
(Tortoise 1 / 6 base / 4.4 form / smoky gradient).
"""
import os
import sys

import bpy

sys.path.insert(0, "P:/MelodiaMelusinaV2-Laptop/deploy")
from surreal_arch.melodia_gn import eyewear as EW  # noqa: E402
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

OUT = {}
fails = []
RUN_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "..", "run_out_gate")


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


def uv_stats(m):
    """(domain, data_type, (umin, umax, vmin, vmax)) for UVMap, Nones if absent."""
    try:
        at = m.attributes.get("UVMap")
    except Exception:
        at = None
    if at is None:
        return (None, None, None)
    us, vs = [], []
    for i in range(len(at.data)):
        v = at.data[i].vector
        us.append(v[0])
        vs.append(v[1])
    return (str(at.domain), str(at.data_type),
            (min(us), max(us), min(vs), max(vs)))


def part_tree(pair_tree, socket_name):
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
    return wrap


pair_t = get("MEL_eyewear_pair")
wraps = []
try:
    for part in ("Frame", "TempleL", "TempleR", "LensL", "LensR"):
        w = part_tree(pair_t, part)
        wraps.append(w)
        ev, m, ob, me = build_eval(w)
        dom, dt, rng = uv_stats(m) if m is not None and len(m.vertices) else (None, None, None)
        release(ev, m, ob, me)
        chk(part + "-uv-attr", dom == "CORNER" and dt == "FLOAT2",
            "%s %s" % (dom, dt))
        if rng:
            ok = rng[0] >= -0.01 and rng[1] <= 1.01 and rng[2] >= -0.01 and rng[3] <= 1.01
            chk(part + "-uv-range", ok,
                "u=[%.3f, %.3f] v=[%.3f, %.3f]" % rng)
finally:
    for w in wraps:
        try:
            bpy.data.node_groups.remove(w)
        except Exception:
            pass

# ---- the gate itself, flat then editorial ----
os.makedirs(RUN_OUT, exist_ok=True)
try:
    rep = EW.melodia_eyewear_export_gate(os.path.join(RUN_OUT, "flat"))
    chk("gate-flat", True,
        "%s" % ({k: (v["bytes"], v["tris"]) for k, v in rep.items()},))
except AssertionError as exc:
    chk("gate-flat", False, str(exc)[:300])

try:
    hero_params = {"Silhouette": 0, "Tortoise": 1.0, "Base Curve": 6.0,
                   "Form Angle": 4.4, "Metal Frame": False}
    hero = EW.melodia_eyewear_hero_export(os.path.join(RUN_OUT, "hero"),
                                          hero_tag="hero", params=hero_params)
    want = {"MEL_eyewear_Frame", "MEL_eyewear_TempleL", "MEL_eyewear_TempleR",
            "MEL_eyewear_LensL", "MEL_eyewear_LensR",
            "ANCHOR_lens", "ANCHOR_hinge", "ANCHOR_bridge"}
    chk("hero-nodes", want <= set(hero["nodes"]), "%s" % hero["nodes"])
    chk("hero-budgets", hero["tris"] < 150000 and hero["bytes"] < 3 * 1024 * 1024,
        "tris=%d bytes=%d" % (hero["tris"], hero["bytes"]))
except AssertionError as exc:
    chk("hero-combined", False, str(exc)[:300])

try:
    rep = EW.melodia_eyewear_export_gate(
        os.path.join(RUN_OUT, "editorial"),
        params={"Tortoise": 1.0, "Base Curve": 6.0, "Form Angle": 4.4,
                "Top Tint": (0.15, 0.15, 0.18, 1.0),
                "Bottom Tint": (0.90, 0.95, 1.00, 1.0)})
    chk("gate-editorial", True,
        "%s" % ({k: (v["bytes"], v["tris"]) for k, v in rep.items()},))
    total_tris = sum(v["tris"] for v in rep.values())
    total_bytes = sum(v["bytes"] for v in rep.values())
    chk("gate-budgets", total_tris < 150000 and total_bytes < 3 * 1024 * 1024,
        "tris=%d bytes=%d" % (total_tris, total_bytes))
except AssertionError as exc:
    chk("gate-editorial", False, str(exc)[:300])

print("CHECKCOUNT %d" % len(OUT))
print("RESULT %s  fails=%s" % ("PASS" if not fails else "FAIL", fails))
print("DONE")
