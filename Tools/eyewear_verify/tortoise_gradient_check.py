"""Acceptance for 11.6 (COLOR_0 tortoise + lens gradient + sRGB round-trip).

GN output ships POSITION + NORMAL only, so COLOR_0 (CORNER FLOAT_COLOR,
exported as COLOR_0) is the only spatial shading channel. Checks:
  Col present as CORNER FLOAT_COLOR on every pair part output + front + lens;
  defaults are display-exact solids (frame/temples espresso, hinges
      champagne, lens uniform white);
  Tortoise=1 marbles the frame (variance + dark->honey range);
  custom gradient tints split the lens top/bottom;
  GLB round-trip: decoded COLOR_0 pinned against the sRGB authoring (the
      exporter linearizes on the way out — this records and pins it).
"""
import json
import math
import os
import struct
import sys

import bpy

_WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_WT, "deploy"))
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

MM = 0.001
OUT = {}
fails = []
RUN_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "..", "run_out_116")


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


def col_stats(m):
    """(domain, data_type, mean_rgb, std_r, min_r, max_r) for 'Col', or Nones."""
    try:
        ca = m.color_attributes.get("Col")
    except Exception:
        ca = None
    if ca is None:
        return (None, None, None, None, None, None)
    rs = [c.color[0] for c in ca.data]
    gs = [c.color[1] for c in ca.data]
    bs = [c.color[2] for c in ca.data]
    n = len(rs)
    mean = (sum(rs) / n, sum(gs) / n, sum(bs) / n)
    stdr = math.sqrt(sum((v - mean[0]) ** 2 for v in rs) / n)
    return (str(ca.domain), str(ca.data_type), mean, stdr, min(rs), max(rs))


def measure_col(tree):
    ev, m, ob, me = build_eval(tree)
    st = col_stats(m) if m is not None and len(m.vertices) else (None,) * 6
    release(ev, m, ob, me)
    return st


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


def front_finished(amount=1.0):
    """Front run through the tortoise writer alone (front-only marble stats).

    The pair's Frame output joins front + champagne hinges, so frame-wide
    min/max cannot pin the marble range. This wrapper replicates the pair's
    own front finish (same two subtrees, same link) for an isolated read.
    """
    fres = GROUP_BUILDERS["MEL_eyewear_front"]()
    front_sub = fres[0] if isinstance(fres, (tuple, list)) else fres
    tres = GROUP_BUILDERS["MEL_eyewear_tortoise"]()
    tor_sub = tres[0] if isinstance(tres, (tuple, list)) else tres
    wrap = bpy.data.node_groups.new("__frontfin__", "GeometryNodeTree")
    wgi = wrap.nodes.new("NodeGroupInput")
    wgo = wrap.nodes.new("NodeGroupOutput")
    wrap.interface.new_socket(name="Geometry", in_out="INPUT",
                              socket_type="NodeSocketGeometry")
    wrap.interface.new_socket(name="Geometry", in_out="OUTPUT",
                              socket_type="NodeSocketGeometry")
    gn_f = wrap.nodes.new("GeometryNodeGroup")
    gn_f.node_tree = front_sub
    gn_t = wrap.nodes.new("GeometryNodeGroup")
    gn_t.node_tree = tor_sub
    try:
        gn_t.inputs["Amount"].default_value = amount
    except Exception:
        pass
    wrap.links.new(wgi.outputs["Geometry"], gn_f.inputs["Geometry"])
    fout = gn_f.outputs["Geometry"]
    tin = None
    for s in gn_t.inputs:
        if s.name == "Geometry":
            tin = s
            break
    wrap.links.new(fout, tin)
    tout = None
    for s in gn_t.outputs:
        if s.name == "Geometry":
            tout = s
            break
    wrap.links.new(tout, wgo.inputs["Geometry"])
    return wrap


def setp(tree, name, val):
    for it in getattr(tree.interface, "items_tree", []):
        if getattr(it, "name", None) == name:
            try:
                it.default_value = val
                return True
            except Exception:
                pass
    return False


def close(a, b, tol=0.02):
    return abs(a - b) <= tol


ESPRESSO = (0.09, 0.055, 0.045)
CHAMP = (0.95, 0.80, 0.60)
WHITE = (0.90, 0.95, 1.00)

pair_t = get("MEL_eyewear_pair")
wraps = []
try:
    # ---- Col contract on every part output (Frame = front + hinges, so its
    # two-population pin lives below; temples/lenses assert exact solids) ----
    for part, want in (("TempleL", ESPRESSO), ("TempleR", ESPRESSO),
                       ("LensL", WHITE), ("LensR", WHITE)):
        w = part_tree(pair_t, part)
        wraps.append(w)
        dom, dt, mean, stdr, mn, mx = measure_col(w)
        chk(part + "-col-attr", dom == "CORNER" and dt == "FLOAT_COLOR",
            "%s %s" % (dom, dt))
        if mean:
            chk(part + "-col-solid",
                all(close(mean[i], want[i], 0.03) for i in range(3)) and stdr < 0.02,
                "mean=%s std=%.4f" % ([round(v, 4) for v in mean], stdr or -1))
    w = part_tree(pair_t, "Geometry")
    wraps.append(w)
    dom, dt, mean, stdr, mn, mx = measure_col(w)
    chk("assembled-col-attr", dom == "CORNER" and dt == "FLOAT_COLOR",
        "%s %s" % (dom, dt))

    # ---- Frame at defaults = espresso front + champagne hinges ----
    # (Frame joins both, so pin the two populations, not a single solid.)
    w = part_tree(pair_t, "Frame")
    wraps.append(w)
    dom, dt, mean, stdr, mn, mx = measure_col(w)
    chk("Frame-col-attr", dom == "CORNER" and dt == "FLOAT_COLOR",
        "%s %s" % (dom, dt))
    chk("frame-two-populations",
        (mn or 1.0) < 0.11 and (mx or 0.0) > 0.90 and (stdr or 0.0) > 0.05,
        "min=%.3f max=%.3f std=%.4f" % (mn or -1, mx or -1, stdr or -1))

    # ---- tortoise marbles the frame ----
    setp(pair_t, "Tortoise", 1.0)
    w = part_tree(pair_t, "Frame")
    wraps.append(w)
    dom, dt, mean, stdr, mn, mx = measure_col(w)
    chk("tortoise-variance", (stdr or 0.0) > 0.05, "std_r=%.4f" % (stdr or -1))
    chk("tortoise-dark-lows", (mn or 1.0) < 0.12, "min=%.3f" % (mn or -1))
    # temples stay solid while the frame marbles
    w = part_tree(pair_t, "TempleL")
    wraps.append(w)
    dom2, dt2, mean2, stdr2, mn2, mx2 = measure_col(w)
    chk("tortoise-temple-solid",
        mean2 is not None and all(close(mean2[i], ESPRESSO[i], 0.03) for i in range(3)),
        "mean=%s" % ([round(v, 4) for v in mean2] if mean2 else None))
    setp(pair_t, "Tortoise", 0.0)

    # ---- front-only marble range (hinge-excluded) ----
    wf = front_finished(1.0)
    wraps.append(wf)
    domf, dtf, meanf, stdrf, mnf, mxf = measure_col(wf)
    chk("tortoise-front-range", (mnf or 1.0) < 0.12 and (mxf or 0.0) > 0.60,
        "min=%.3f max=%.3f" % (mnf or -1, mxf or -1))

    # ---- gradient splits the lens (CORNER data read per loop, not per vert) ----
    front_lens = get("MEL_eyewear_lens")
    setp(front_lens, "Top Tint", (0.15, 0.15, 0.18, 1.0))
    setp(front_lens, "Bottom Tint", (0.90, 0.95, 1.00, 1.0))
    ev, m, ob, me = build_eval(front_lens)
    top, bot = [], []
    if m is not None and len(m.vertices):
        try:
            ca = m.color_attributes.get("Col")
        except Exception:
            ca = None
        if ca is not None:
            for i, lp in enumerate(m.loops):
                y = m.vertices[lp.vertex_index].co.y / MM
                r = ca.data[i].color[0]
                if y > 10.0:
                    top.append(r)
                elif y < -10.0:
                    bot.append(r)
    release(ev, m, ob, me)
    if top and bot:
        mt, mb = sum(top) / len(top), sum(bot) / len(bot)
        chk("gradient-split", mt < 0.30 and mb > 0.75, "top=%.3f bot=%.3f" % (mt, mb))
    else:
        chk("gradient-split", False, "no loops sampled")
finally:
    for w in wraps:
        try:
            bpy.data.node_groups.remove(w)
        except Exception:
            pass

def export_tree(tree, tag, path):
    for ob in list(bpy.data.objects):
        try:
            bpy.data.objects.remove(ob, do_unlink=True)
        except Exception:
            pass
    me = bpy.data.meshes.new("__x__")
    ob = bpy.data.objects.new("__xo__", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("m", "NODES")
    mod.node_group = tree
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(
        filepath=path, use_selection=True, export_format="GLB",
        export_apply=True, export_texcoords=True, export_normals=True)
    try:
        bpy.data.objects.remove(ob, do_unlink=True)
    except Exception:
        pass


def decode_glb_col(path):
    """{prim_index: (attr_names, (mean3, min0, max0) or None)} + prims + size."""
    with open(path, "rb") as f:
        data = f.read()
    magic, ver, ln = struct.unpack("<III", data[:12])
    assert magic == 0x46546C67, hex(magic)
    off, js, bn = 12, None, None
    while off < len(data):
        clen, ctype = struct.unpack("<II", data[off:off + 8])
        chunk = data[off + 8:off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            bn = chunk
        off += 8 + clen
    out = {}
    for pi, prim in enumerate(js["meshes"][0]["primitives"]):
        attrs = list(prim.get("attributes", {}).keys())
        stat = None
        ai = prim["attributes"].get("COLOR_0")
        if ai is not None:
            acc = js["accessors"][ai]
            bv = js["bufferViews"][acc["bufferView"]]
            start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
            n = acc["count"]
            comp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[acc["type"]]
            vals = struct.unpack("<%df" % (n * comp), bn[start:start + 4 * n * comp])
            r0 = [vals[i * comp] for i in range(n)]
            mean = tuple(sum(vals[i * comp + c] for i in range(n)) / n
                         for c in range(min(comp, 3)))
            stat = (mean, min(r0), max(r0))
        out[pi] = (attrs, stat)
    return out, len(js["meshes"][0]["primitives"]), os.path.getsize(path)


# ---- GLB round-trip: COLOR_0 survives export byte-exact ----
# Measured on this build: decoded COLOR_0 == authored values exactly (no
# linear conversion applied by the exporter here), VEC3, per-material
# primitives preserved. Pin that; any Blender upgrade that changes the
# color pipeline fails loudly instead of double-darkening silently.
try:
    os.makedirs(RUN_OUT, exist_ok=True)
    pair2 = get("MEL_eyewear_pair")
    export_tree(part_tree(pair2, "LensR"),
                "lens", os.path.join(RUN_OUT, "lens_white.glb"))
    prims, nprims, size = decode_glb_col(os.path.join(RUN_OUT, "lens_white.glb"))
    attrs0, stat0 = prims.get(0, ([], None))
    chk("glb-lens-file", size > 1000, "%d bytes" % size)
    chk("glb-lens-col", "COLOR_0" in attrs0, "%s" % (attrs0,))
    if stat0:
        chk("glb-lens-exact",
            all(abs(stat0[0][i] - WHITE[i]) <= 0.01 for i in range(3)),
            "mean=%s" % ([round(v, 4) for v in stat0[0]],))
    setp(pair2, "Tortoise", 1.0)
    export_tree(part_tree(pair2, "Frame"),
                "frame", os.path.join(RUN_OUT, "frame_tortoise.glb"))
    prims, nprims, size = decode_glb_col(os.path.join(RUN_OUT, "frame_tortoise.glb"))
    chk("glb-frame-file", size > 1000, "%d bytes" % size)
    chk("glb-frame-split", nprims == 2, "%d primitives" % nprims)
    TorMean = [p[1] for p in prims.values() if p[1] is not None]
    chk("glb-frame-col", all("COLOR_0" in p[0] for p in prims.values()),
        "%s" % ([p[0] for p in prims.values()],))
    if len(TorMean) == 2:
        lo = min(s[1] for s in TorMean)
        hi = max(s[2] for s in TorMean)
        chk("glb-frame-marble", lo < 0.15 and hi > 0.60,
            "min=%.3f max=%.3f" % (lo, hi))
except Exception as exc:
    chk("glb-roundtrip", False, "%s: %s" % (type(exc).__name__, exc))

print("CHECKCOUNT %d" % len(OUT))
print("RESULT %s  fails=%s" % ("PASS" if not fails else "FAIL", fails))
print("DONE")
