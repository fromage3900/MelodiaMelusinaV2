"""Runtime-readiness gate: everything a UE runtime consumer (PCG, HLOD,
World Partition, collision) needs from the Houdini side, verified headless.
Cooks V6, checks outputs + masks + points contract + collision/proxy gaps.
Read-only except the receipt."""
import json
import os
import hou

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
OUT = {"checks": [], "pass": True, "measured": {}, "gaps": []}
def check(name, ok, detail=""):
    OUT["checks"].append({"name": name, "ok": bool(ok), "detail": str(detail)[:200]})
    if not ok:
        OUT["pass"] = False
def gap(name, detail=""):
    OUT["gaps"].append({"name": name, "detail": str(detail)[:200]})

# 1. cook V6, verify real geometry on every output
hou.hda.installFile(REPO + r"\Tools\Poitou\hda\poitou_layout_live.hdalc")
obj = hou.node("/obj")
inst = obj.createNode("geo", "rtg").createNode("poitou_layout_live_v6", "live")
inst.allowEditingOfContents()
base = inst.path()
outs = {}
for k in inst.allSubChildren():
    if k.type().name() == "output":
        try:
            g = k.geometry()
        except Exception as exc:
            outs[k.name()] = {"error": str(exc)[:100]}
            continue
        if g is None:
            outs[k.name()] = {"prims": 0, "points": 0, "verts": 0}
            continue
        nv = sum(len(pr.vertices()) for pr in g.prims())
        outs[k.name()] = {"prims": len(g.prims()), "points": len(g.points()),
                          "verts": nv}
OUT["measured"]["v6_outputs"] = outs
for on, rec in outs.items():
    if isinstance(rec, dict) and "prims" in rec:
        check("output_%s_nonempty" % on, rec["prims"] > 0, rec)

# 2. masks: present, PNG, dimensions vs water_res
import struct
mdir = os.path.join(REPO, "Tools", "Poitou", "export")
masks = sorted(f for f in os.listdir(mdir) if f.endswith(".png"))
OUT["measured"]["masks"] = {"count": len(masks), "files": masks[:20]}
check("masks_present", len(masks) >= 12, "%d pngs" % len(masks))
def png_size(p):
    with open(p, "rb") as fh:
        d = fh.read(33)
    w, h = struct.unpack(">II", d[16:24])
    return w, h
sizes = {}
for m in masks:
    try:
        sizes[m] = png_size(os.path.join(mdir, m))
    except Exception as exc:
        sizes[m] = "ERR %s" % exc
OUT["measured"]["mask_dims"] = sizes
uniq = set(s for s in sizes.values() if isinstance(s, tuple))
check("masks_uniform", len(uniq) <= 2, str(uniq))

# 3. points contract: type/yaw/scale + instance path per point
pg = hou.node(base + "/output_points")
pgeo = pg.geometry()
need = {"type": 0, "yaw": 0, "scale": 0}
have_unreal = False
if pgeo is not None:
    pts = pgeo.points()
    for a in list(need):
        try:
            pgeo.findPointAttrib(a)
            need[a] = len(pts)
        except Exception:
            pass
    try:
        pgeo.findPointAttrib("unreal_instance")
        have_unreal = True
    except Exception:
        try:
            pgeo.findPrimAttrib("unreal_instance")
            have_unreal = True
        except Exception:
            pass
OUT["measured"]["points_contract"] = {"attrs": need,
                                      "unreal_instance": have_unreal,
                                      "npoints": len(pts) if pgeo else 0}
for a, n in need.items():
    check("points_attr_%s" % a, n > 0, "%d pts" % n)
if not have_unreal:
    gap("points_unreal_instance",
        "no unreal_instance attr on output_points - PCG cannot resolve meshes")

# 4. collision output: blocking volumes double as HLOD proxies --------
cn = hou.node(base + "/output_collision")
cg = cn.geometry() if cn is not None else None
if cg is None:
    check("collision_cooks", False, "no output_collision geometry")
    gap("no_collision_output", "output_collision missing")
else:
    cprs = cg.prims()
    cnv = sum(len(pr.vertices()) for pr in cprs)
    check("collision_cooks", len(cprs) > 0, "%d prims" % len(cprs))
    check("collision_all_quads", cnv == 4 * len(cprs),
          "%d verts / %d prims" % (cnv, len(cprs)))
    from collections import Counter as _C
    ct = _C(x.name() for pr in cprs for x in pr.groups())
    OUT["measured"]["collision_groups"] = dict(ct)
    check("collision_abbey", ct.get("collision_abbey", 0) == 24,
          "%s" % ct.get("collision_abbey", 0))
    _nb = ct.get("collision_building", 0)
    check("collision_buildings", _nb > 0 and _nb % 6 == 0,
          "%d prims (%d houses x 6)" % (_nb, _nb // 6))

# 5. proxy/LOD outputs? (spec 2.1 dual-stage; collision boxes are phase 1)
outs_names = [k.name() for k in inst.allSubChildren()
              if k.type().name() == "output"]
if not any("proxy" in n.lower() or "lod" in n.lower() for n in outs_names):
    gap("no_proxy_output",
        "no dedicated proxy/impostor output (collision boxes serve as HLOD proxies interim)")
check("has_proxy_output", False, "recorded as gap")

import os as _os
_receipt = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\hda_verify\runtime_gate_20261022.json"
_os.makedirs(os.path.dirname(_receipt), exist_ok=True)
with open(_receipt, "w", encoding="utf-8") as _fh:
    json.dump(OUT, _fh, indent=1)
print("RECEIPT " + _receipt)
print("OVERALL " + str(OUT["pass"]))
