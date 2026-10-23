"""Gate: LOCK_chamber_steps (spec gates 1-4, 6). Reads the BUILT .hdalc."""
import json
import hou

PATH = r"C:\EnvironmentPortfolio\BS_GodFile\Tools\Poitou\hda\poitou_layout_live.hdalc"
hou.hda.installFile(PATH)
obj = hou.node("/obj")
geo = obj.createNode("geo", "lockgate")
inst = geo.createNode("poitou_layout_live_v6", "live")
inst.allowEditingOfContents()
base = inst.path()

out = {"hda": PATH, "checks": [], "pass": True}
def check(name, ok, detail=""):
    out["checks"].append({"name": name, "ok": bool(ok), "detail": str(detail)[:220]})
    if not ok:
        out["pass"] = False

lk = hou.node(base + "/LOCK_chamber_steps")
check("lock_wrample_present", lk is not None)
check("lock_compiles", lk is not None and not lk.errors(), lk.errors() if lk else "missing")

EXPECTED = ["lock_chamber", "lock_gate", "lock_coping", "lock_steps", "lock_sill",
            "jetty_deck", "jetty_piles", "lockhouse_wall", "lockhouse_roof",
            "lock_bollard", "lock_lamp", "lock_quoin", "lock_bridge",
            "lock_garland", "lock_bow", "lock_doily"]
gen = hou.node(base + "/output_generated")
g = gen.geometry()
prims = g.prims() if g is not None else []
groups = set()
for pr in prims:
    for grp in pr.groups():
        groups.add(grp.name())
for grp in EXPECTED:
    n = sum(1 for pr in prims if grp in [gg.name() for gg in pr.groups()])
    check("group_%s" % grp, n > 0, "%d prims" % n)

# chamber width: coping centroids sit at +/-(hw + THK/2) from the site
def centroid(pr):
    vs = pr.vertices()
    c = hou.Vector3(0, 0, 0)
    for v in vs:
        c += v.point().position()
    return c / len(vs)
cope = [pr for pr in prims if "lock_coping" in [gg.name() for gg in pr.groups()]]
from collections import Counter
_tally = Counter()
for pr in prims:
    for gg in pr.groups():
        _tally[gg.name()] += 1
print("GROUP_TALLY " + json.dumps({k: _tally[k] for k in sorted(_tally) if k.startswith("lock_") or k.startswith("jetty_") or k.startswith("lockhouse")}))
print("COPE_N %d" % len(cope))
A = B = None
if len(cope) >= 2:
    pts = [centroid(pr) for pr in cope]
    print("PTS_N %d FIRST %s" % (len(pts), pts[0]))
    # split the two runs by distance: farthest pair defines the axis
    best = (0.0, None, None)
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            try:
                d = (pts[i] - pts[j]).length()
            except Exception:
                continue
            if d > best[0]:
                best = (d, pts[i], pts[j])
    print("BEST_SPAN %.3f" % best[0])
    if best[1] is None or best[2] is None or best[0] < 1e-6:
        check("chamber_width_4.8", False, "degenerate coping span %.3f" % best[0])
        A = B = None
    else:
        run_span, A, B = best
    # wall separation by PCA: the runs dominate the variance, so the
    # principal axis IS the run direction and its perpendicular is the
    # true wall normal (no diagonal-pair tilt)
    import math
    if A is None:
        pass  # degenerate case already recorded as FAIL above
    else:
        xs = [p[0] for p in pts]
        zs = [p[2] for p in pts]
        npt = len(pts)
        mx = sum(xs) / npt
        mz = sum(zs) / npt
        cxx = sum((x - mx) ** 2 for x in xs) / npt
        czz = sum((z - mz) ** 2 for z in zs) / npt
        cxz = sum((x - mx) * (z - mz) for x, z in zip(xs, zs)) / npt
        ang = 0.5 * math.atan2(2 * cxz, cxx - czz)
        nx, nz = -math.sin(ang), math.cos(ang)
        s = sorted([(p[0] - mx) * nx + (p[2] - mz) * nz for p in pts])
        print("PROJ " + " ".join("%.2f" % v for v in s))
        sep = (s[-1] - s[0]) - (1.35 + 2*0.06)
        check("chamber_width_4.8", abs(sep - (4.8 + 1.35)) < 0.2,
              "wall-centre separation %.3f (expect 6.15 = 4.8 + 2x0.675)" % sep)
else:
    check("chamber_width_4.8", False, "fewer than 2 coping prims")

# piano steps: distinct notes == lock_steps_n
steps = [pr for pr in prims if "lock_steps" in [gg.name() for gg in pr.groups()]]
notes = sorted(set(pr.attribValue("note") for pr in steps))
check("steps_notes_7", notes == list(range(7)), "notes=%s" % notes)

# parm_drive: 7 -> 5 treads must shrink lock_steps
def step_prims():
    gg = hou.node(base + "/output_generated").geometry()
    return sum(1 for pr in gg.prims() if "lock_steps" in [g2.name() for g2 in pr.groups()])
n7 = step_prims()
inst.parm("lock_steps_n").set(5)
n5 = step_prims()
check("parm_drive_steps", n5 < n7, "7treads=%d 5treads=%d" % (n7, n5))
inst.parm("lock_steps_n").set(7)
# lock_on kills all lock output
inst.parm("lock_on").set(0)
gg = hou.node(base + "/output_generated").geometry()
left = sum(1 for pr in gg.prims()
           for g2 in pr.groups()
           if g2.name().startswith("lock_") or g2.name().startswith("jetty_") or g2.name().startswith("lockhouse"))
check("lock_on_kills", left == 0, "remaining=%d" % left)
inst.parm("lock_on").set(1)

# the tail bridge decks above the chamber coping it crosses
def _maxy(group):
    ps = [pr for pr in prims if group in [x.name() for x in pr.groups()]]
    if not ps:
        return None
    return max(centroid(pr)[1] for pr in ps)
_bmax = _maxy("lock_bridge")
_cmax = _maxy("lock_chamber")
check("bridge_above_coping",
      _bmax is not None and _cmax is not None and _bmax > _cmax + 0.2,
      "bridge maxy=%.2f chamber maxy=%.2f" % (_bmax or -999, _cmax or -999))

import os
_receipt = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\PoitouConvergence_20261020\lock_gate.json"
os.makedirs(os.path.dirname(_receipt), exist_ok=True)
with open(_receipt, "w", encoding="utf-8") as _fh:
    json.dump(out, _fh, indent=1)
print("RECEIPT " + _receipt)

# site sanity: the chamber sits on the bief (x in the hundreds), never
# collapsed to the origin
site_ok = True
site_detail = ""
if cope and A is not None:
    mid = (A + B) * 0.5
    site_ok = (mid - hou.Vector3(0, 0, 0)).length() > 100.0
    site_detail = "mid-chamber %s" % mid
check("site_on_bief", site_ok, site_detail)

# winding sentinel (UE clockwise-front): the highest sill prims are top
# faces, so their geometric normals must point +y. Catches any future
# kit winding flip at the grammar root.
def _nrm3(pr):
    vs = [v.point().position() for v in list(pr.vertices())[:3]]
    n = (vs[1] - vs[0]).cross(vs[2] - vs[0])
    return n / max(1e-9, n.length())
sill_prs = [pr for pr in prims if "lock_sill" in [x.name() for x in pr.groups()]]
if sill_prs:
    topy = max(centroid(pr)[1] for pr in sill_prs)
    tops = [pr for pr in sill_prs if abs(centroid(pr)[1] - topy) < 1e-6]
    ups = [_nrm3(pr)[1] > 0.9 for pr in tops]
    check("winding_cw_front", len(ups) > 0 and all(ups),
          "%d/%d sill-top faces point +y" % (sum(ups), len(ups)))
else:
    check("winding_cw_front", False, "no sill prims")

print(json.dumps(out, indent=1))
