"""Gate 2 FINAL (single receipt): abbey pins + bay/structural drive + decay
geometric drive; stained-glass pins + note/mode geometric drive.
Writes receipt itself. Expected: everything PASS except sg_drive
(parms unwired in the current HDA build - queued rebuild)."""
import hashlib
import json
import os
import hou

OUT = {"gate": "melodia.hda_gate2.v1", "checks": [], "pass": True,
       "measured": {}}
def check(name, ok, detail=""):
    OUT["checks"].append({"name": name, "ok": bool(ok),
                          "detail": str(detail)[:220]})
    if not ok:
        OUT["pass"] = False

def snap(node):
    if hasattr(node, "geometry"):
        g = node.geometry()
    else:
        g = None
        try:
            kids = node.allSubChildren()
        except Exception:
            kids = []
        for k in kids:
            if k.type().name() == "output":
                try:
                    g = k.geometry()
                except Exception:
                    g = None
                break
    if g is None:
        return None
    pts = sorted((round(p.position()[0], 4), round(p.position()[1], 4),
                  round(p.position()[2], 4)) for p in g.points())
    nprims = len(g.prims())
    bb = g.boundingBox()
    return {"points": len(pts), "prims": nprims,
            "hash": hashlib.sha256(repr(pts).encode()).hexdigest()[:16],
            "bbox": [[round(v, 3) for v in bb.minvec()],
                     [round(v, 3) for v in bb.maxvec()]]}

obj = hou.node("/obj")

# abbey
hou.hda.installFile(r"C:\EnvironmentPortfolio\BS_GodFile\hda\HDA_Poitou_AbbeyBuilder_1.0.hda")
ainst = obj.createNode("HDA_Poitou_AbbeyBuilder", "abbey")
a0 = snap(ainst)
OUT["measured"]["abbey_default"] = a0
check("abbey_cooks", a0 is not None and a0["prims"] > 0, a0)
if a0 is not None:
    check("abbey_pins", a0["points"] == 512 and a0["prims"] == 336,
          "measured=%s registry=512/336" % a0)
ainst.parm("bay_count").set(4)
a4 = snap(ainst)
OUT["measured"]["abbey_bays4"] = a4
if a0 is not None and a4 is not None:
    check("abbey_drive_bays", (a0["points"], a0["prims"]) != (a4["points"], a4["prims"]),
          "default=%s bays4=%s" % (a0, a4))
ainst.parm("bay_count").set(8)
ainst.parm("decay_intensity").set(0.9)
a9 = snap(ainst)
OUT["measured"]["abbey_decay09"] = a9
if a0 is not None and a9 is not None:
    check("abbey_drive_decay", a0["hash"] != a9["hash"],
          "default=%s decay09=%s" % (a0, a9))

# stained glass
hou.hda.installFile(r"C:\EnvironmentPortfolio\BS_GodFile\Content\HDA\MelodiaStainedGlassWindow_1.0.hda")
sg = obj.createNode("geo", "gate2_sg")
sinst = sg.createNode("melodia::stained_glass_window", "live")
s0 = snap(sinst)
OUT["measured"]["sg_default"] = s0
check("sg_cooks", s0 is not None and s0["prims"] > 0, s0)
if s0 is not None:
    check("sg_pins", s0["points"] == 232 and s0["prims"] == 348,
          "measured=%s registry=232/348" % s0)
sinst.parm("note").set(4)
sinst.parm("mode_n").set(3)
sinst.parm("mode_m").set(4)
s1 = snap(sinst)
OUT["measured"]["sg_driven"] = s1
if s0 is not None and s1 is not None:
    check("sg_drive", s0["hash"] != s1["hash"],
          "default=%s driven=%s (FAIL expected: parms unwired, rebuild queued)" % (s0, s1))

receipt = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\hda_verify\gate2_20261022.json"
os.makedirs(os.path.dirname(receipt), exist_ok=True)
with open(receipt, "w", encoding="utf-8") as fh:
    json.dump(OUT, fh, indent=1)
print("RECEIPT " + receipt)
print(json.dumps([c["name"] + "=" + str(c["ok"]) for c in OUT["checks"]], indent=0))
print("OVERALL " + str(OUT["pass"]))
