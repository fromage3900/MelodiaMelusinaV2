"""Sir v5 tailfix KineFX verification (hython, headless, staging only).

Proves the tailfix FBX actually carries the fix: import both the original v5
and the tailfix FBX, count zero-capture-weight points on every mesh, and
report bbox/bone counts. Expectation: v5 body = 657 zero, tailfix = 0.

  hython Tools/Houdini/sir_kinefx/sir_tailfix_verify.py
"""
import hou
import json

REPO = "C:/EnvironmentPortfolio/BS_GodFile"
AUDIT = REPO + "/Saved/Audit/SirMelodious_FlightUnit_20261003"
V5 = AUDIT + "/exports/ue_arp/SKM_SirMelodious_ARP_CrestTie_v5.fbx"
FIX = AUDIT + "/exports/ue_arp/SKM_SirMelodious_ARP_CrestTie_v5_tailfix.fbx"
OUT = REPO + "/Saved/Audit/sirmelodious_kinefx_doctor/reweight/tailfix_verify_kinefx.json"


def scan(fbx_path):
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.hipFile.importFBX(fbx_path)
    obj = hou.node("/obj")
    sub = [c for c in obj.children() if c.type().name() == "subnet"][0]
    out = {"meshes": {}, "bones": 0}
    joints = [c for c in sub.allSubChildren()
              if c.type().name() in ("bone", "null")]
    out["bones"] = len(joints)
    for gnode in sub.children():
        if gnode.type().name() != "geo":
            continue
        cap = None
        for c in gnode.children():
            if c.type().name() == "capture":
                cap = c
                break
        if cap is None:
            continue
        g = cap.geometry()
        pts = g.points()
        if not pts:
            continue
        n = len(pts[0].attribValue("boneCapture")) // 2
        zero = 0
        for p in pts:
            v = p.attribValue("boneCapture")
            if sum(v[i + 1] for i in range(0, len(v), 2)) < 1e-6:
                zero += 1
        bb = g.boundingBox()
        out["meshes"][gnode.name()] = {
            "points": len(pts),
            "zero_capture": zero,
            "slots": n,
            "bbox_min": [round(v, 1) for v in bb.minvec()],
            "bbox_max": [round(v, 1) for v in bb.maxvec()],
        }
    return out


v5 = scan(V5)
fix = scan(FIX)

zeros_before = sum(m["zero_capture"] for m in v5["meshes"].values())
zeros_after = sum(m["zero_capture"] for m in fix["meshes"].values())
body_v5 = v5["meshes"].get("SirMelodiousBody", {})
body_fix = fix["meshes"].get("SirMelodiousBody", {})

rep = {
    "schema": "melodia.sir_tailfix_verify.v1",
    "v5": v5, "tailfix": fix,
    "zeros_before": zeros_before, "zeros_after": zeros_after,
    "pass": (zeros_before == 657 and zeros_after == 0
             and v5["bones"] == fix["bones"]
             and body_v5.get("points") == body_fix.get("points")),
    "note": "fix binds the 657 previously-zero tail points to exported "
            "root/spine bones at source; geometry and bone set unchanged. "
            "This makes the tail FOLLOW the body. True tail wag still "
            "needs the spline/bbone chain exported as deform bones.",
}
json.dump(rep, open(OUT, "w"), indent=1)
print("VERIFY", json.dumps({"before": zeros_before, "after": zeros_after,
                            "bones_v5": v5["bones"], "bones_fix": fix["bones"],
                            "body_pts": [body_v5.get("points"), body_fix.get("points")],
                            "pass": rep["pass"]}))
