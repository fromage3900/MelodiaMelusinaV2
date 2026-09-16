"""Acceptance for 11.4 (weld) + 11.5 (five named outputs + materials).

Asserts ARITHMETIC on realized geometry, not looks:
  assembled pair keeps the 134.000-class boxing contract, has no boundary or
  wire edges, and no longer carries doubled seam verts;
  Frame/TempleL/TempleR/LensL/LensR exist as group outputs, are non-empty,
  sit where the boxing system says, and carry the delivery materials;
  Silhouette 0/1/2 all satisfy the boxing contract through the pair.
"""
import sys

import bpy

sys.path.insert(0, "P:/MelodiaMelusinaV2-Laptop/deploy")
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
    seen = {}
    doubled = 0
    for v in bm.verts:
        key = (round(v.co.x, 5), round(v.co.y, 5), round(v.co.z, 5))
        if key in seen:
            doubled += 1
        else:
            seen[key] = 1
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    st = {"verts": len(bm.verts),
          "boundary": sum(1 for e in bm.edges if e.is_boundary),
          "wire": sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary),
          "doubled": doubled,
          "x": [(min(xs) / MM if xs else 0.0), (max(xs) / MM if xs else 0.0)],
          "y": [(min(ys) / MM if ys else 0.0), (max(ys) / MM if ys else 0.0)],
          "z": [(min(zs) / MM if zs else 0.0), (max(zs) / MM if zs else 0.0)],
          "mats": sorted({mt.name for mt in m.materials if mt})}
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

# ---- interface contract ----
want_out = {"Geometry", "Frame", "TempleL", "TempleR", "LensL", "LensR"}
got_out = {it.name for it in pair_t.interface.items_tree if it.in_out == "OUTPUT"}
chk("outputs-exist", want_out <= got_out, "missing=%s" % sorted(want_out - got_out))

# ---- assembled ----
asm = measure(pair_t)
chk("assembled-nonempty", asm is not None and asm["verts"] > 1000,
    "verts=%s" % (asm["verts"] if asm else None))
if asm:
    w = asm["x"][1] - asm["x"][0]
    chk("assembled-width", abs(w - 134.0) <= 3.0, "got=%.3f" % w)
    chk("assembled-symmetry", abs(asm["x"][0] + asm["x"][1]) <= 0.5,
        "x=%s" % asm["x"])
    chk("assembled-no-boundary", asm["boundary"] == 0, "%d" % asm["boundary"])
    chk("assembled-no-wire", asm["wire"] == 0, "%d" % asm["wire"])
    chk("assembled-no-doubles", asm["doubled"] == 0, "%d doubled" % asm["doubled"])
    chk("assembled-welded-size", asm["verts"] < 5500, "verts=%d" % asm["verts"])
    chk("assembled-mats", {"MEL_mat_eyewear_acetate", "MEL_mat_eyewear_metal"} <= set(asm["mats"]),
        "%s" % asm["mats"])

# ---- parts ----
frame = measure_output(pair_t, "Frame")
chk("frame-nonempty", frame is not None and frame["verts"] > 1000,
    "verts=%s" % (frame["verts"] if frame else None))
if frame:
    w = frame["x"][1] - frame["x"][0]
    chk("frame-width", abs(w - 134.0) <= 3.0, "got=%.3f" % w)
    chk("frame-mats", {"MEL_mat_eyewear_acetate", "MEL_mat_eyewear_metal"} <= set(frame["mats"]),
        "%s" % frame["mats"])

tl = measure_output(pair_t, "TempleL")
tr = measure_output(pair_t, "TempleR")
for tag, st, side in (("templeL", tl, 1), ("templeR", tr, -1)):
    chk(tag + "-nonempty", st is not None and st["verts"] > 100,
        "verts=%s" % (st["verts"] if st else None))
    if st:
        chk(tag + "-side", min(s * side for s in st["x"]) > -0.5, "x=%s" % st["x"])
        chk(tag + "-reach", min(st["z"]) < -100.0, "zmin=%.2f" % min(st["z"]))
        chk(tag + "-mat", "MEL_mat_eyewear_acetate" in st["mats"], "%s" % st["mats"])
if tl and tr:
    wl = tl["x"][1] - tl["x"][0]
    wr = tr["x"][1] - tr["x"][0]
    chk("temples-mirror", abs(wl - wr) <= 0.5, "L=%.3f R=%.3f" % (wl, wr))
    chk("temples-seated-symmetric",
        abs((tl["x"][0] + tl["x"][1]) + (tr["x"][0] + tr["x"][1])) <= 1.0,
        "L=%s R=%s" % (tl["x"], tr["x"]))

ll = measure_output(pair_t, "LensL")
lr = measure_output(pair_t, "LensR")
for tag, st in (("lensL", ll), ("lensR", lr)):
    chk(tag + "-nonempty", st is not None and st["verts"] > 100,
        "verts=%s" % (st["verts"] if st else None))
    if st:
        chk(tag + "-width-A", abs((st["x"][1] - st["x"][0]) - 54.0) <= 1.5,
            "got=%.3f" % (st["x"][1] - st["x"][0]))
        chk(tag + "-mat", "MEL_mat_eyewear_lens" in st["mats"], "%s" % st["mats"])
if ll and lr:
    span = lr["x"][1] - ll["x"][0]
    chk("lens-span-2A+DBL", abs(span - 126.0) <= 1.0, "got=%.3f" % span)
    chk("lens-halves-sign", ll["x"][1] <= 0.5 and lr["x"][0] >= -0.5,
        "L=%s R=%s" % (ll["x"], lr["x"]))

# ---- silhouettes through the pair ----
for idx in (0, 1, 2):
    setp(pair_t, "Silhouette", idx)
    st = measure(pair_t)
    ok = st is not None and abs((st["x"][1] - st["x"][0]) - 134.0) <= 3.0
    chk("silhouette-%d-boxing" % idx, ok,
        "width=%s" % ((st["x"][1] - st["x"][0]) if st else None))
setp(pair_t, "Silhouette", 0)

print("CHECKCOUNT %d" % len(OUT))
print("RESULT %s  fails=%s" % ("PASS" if not fails else "FAIL", fails))
print("DONE")


