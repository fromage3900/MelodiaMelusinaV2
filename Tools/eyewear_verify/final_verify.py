"""Final eyewear verification — writes clean numbers to JSON, nothing to stdout
except one line per check, so a repeating stream cannot garble the result.
"""
import json
import os
import sys

import bpy

_WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_WT, "deploy"))
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

R = os.path.join(_WT, "Saved", "Audit", "eyewear")
MM = 0.001
OUT = {}
fails = []


def measure(tree):
    me = bpy.data.meshes.new("__b__")
    ob = bpy.data.objects.new("__o__", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("m", "NODES")
    mod.node_group = tree
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = ev.to_mesh()
    d = None
    if m is not None and len(m.vertices):
        xs = [v.co.x for v in m.vertices]
        ys = [v.co.y for v in m.vertices]
        zs = [v.co.z for v in m.vertices]
        d = {"verts": len(m.vertices),
             "tris": sum(len(p.vertices) - 2 for p in m.polygons),
             "x": [round(min(xs) / MM, 3), round(max(xs) / MM, 3)],
             "y": [round(min(ys) / MM, 3), round(max(ys) / MM, 3)],
             "z": [round(min(zs) / MM, 3), round(max(zs) / MM, 3)]}
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return d


def get(name):
    r = GROUP_BUILDERS[name]()
    return r[0] if isinstance(r, (tuple, list)) else r


def chk(tag, got, want, tol):
    ok = abs(got - want) <= tol
    if not ok:
        fails.append("%s got %.3f want %.3f" % (tag, got, want))
    OUT.setdefault("checks", {})[tag] = {"got": round(got, 3), "want": want,
                                         "tol": tol, "pass": ok}
    return ok


# ---- pair ----
pair_t = get("MEL_eyewear_pair")
pi = measure(pair_t)
OUT["pair"] = pi
if pi:
    w = pi["x"][1] - pi["x"][0]
    chk("pair width", w, 134.0, 3.0)
    chk("pair symmetry", abs(pi["x"][0] + pi["x"][1]), 0.0, 0.5)
    chk("pair depth (temple reach)", pi["z"][1] - pi["z"][0], 126.2, 6.0)
    chk("pair height (drop + frame)", pi["y"][1] - pi["y"][0], 49.9, 6.0)

# ---- temple alone, folded and mirrored ----
tt = get("MEL_eyewear_temple")
ti = measure(tt)
OUT["temple_open"] = ti
if ti:
    chk("temple reach (-Z)", ti["z"][1] - ti["z"][0], 123.2, 3.0)
    chk("temple inner face x_min", ti["x"][0], 0.5, 0.6)


def setp(tree, name, val):
    for it in getattr(tree.interface, "items_tree", []):
        if getattr(it, "name", None) == name:
            try:
                it.default_value = val
                return True
            except Exception:
                pass
    return False


setp(tt, "Fold Angle", 90.0)
tf = measure(tt)
OUT["temple_folded90"] = tf
if tf:
    chk("folded X reach", tf["x"][1] - tf["x"][0], 123.2, 6.0)
    chk("folded Z collapse", tf["z"][1] - tf["z"][0], 4.5, 1.5)
setp(tt, "Fold Angle", 0.0)

# ---- hinge ----
ht = get("MEL_eyewear_hinge")
hi = measure(ht)
OUT["hinge"] = hi
if hi:
    chk("hinge stack on axis (Y)", hi["y"][1] - hi["y"][0], 7.5, 0.4)
    chk("hinge diameter X", hi["x"][1] - hi["x"][0], 2.8, 0.3)

# ---- lens ----
lt = get("MEL_eyewear_lens")
li = measure(lt)
OUT["lens"] = li
if li:
    chk("lens pair span (2A + DBL)", li["x"][1] - li["x"][0], 126.0, 1.0)
    chk("lens symmetry", abs(li["x"][0] + li["x"][1]), 0.0, 0.5)
    chk("lens height (B)", li["y"][1] - li["y"][0], 34.0, 1.5)
    chk("lens thickness", li["z"][1] - li["z"][0], 2.0, 0.8)
    chk("lens centred on Z=0", abs(li["z"][0] + li["z"][1]), 0.0, 0.3)

OUT["fails"] = fails
OUT["result"] = "PASS" if not fails else "FAIL"
json.dump(OUT, open(R + "/final_verify.json", "w"), indent=1)

print("CHECKCOUNT %d" % len(OUT.get("checks", {})))
print("PAIR verts=%s tris=%s x=%s z=%s" % (pi["verts"], pi["tris"], pi["x"], pi["z"]) if pi else "PAIR NONE")
print("LENS verts=%s tris=%s x=%s y=%s z=%s" % (li["verts"], li["tris"], li["x"], li["y"], li["z"]) if li else "LENS NONE")
print("RESULT %s  fails=%s" % (OUT["result"], fails))
print("DONE")
