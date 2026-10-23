"""Diagnose why the citadel renders black. Opens the debug hip, checks
material coverage + light state, then renders a tiny test with/without headlight."""
import hou
from pathlib import Path

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
HIP = ROOT / "Saved" / "Audit" / "endless_citadel" / "citadel_debug.hip"
OUT = ROOT / "Saved" / "Audit" / "endless_citadel"

hou.hipFile.load(str(HIP))
geo = hou.node("/obj/citadel")
fm = geo.node("citadel_final")
fm.cook()
g = fm.geometry()

# per-material prim counts
from collections import Counter
mats = Counter()
for prim in g.prims():
    try:
        mats[prim.attribValue("shop_materialpath")] += 1
    except Exception:
        mats["<none>"] += 1
print("[diag] material coverage:", dict(mats))

# light enable states
for name in ("cit_key", "cit_rim", "cit_bio"):
    lg = hou.node("/obj/" + name)
    print(f"[diag] {name} enabled={lg.parm('light_enable').eval()} type={lg.parm('light_type').eval()} intensity={lg.parm('light_intensity').eval()}")

# object render flags
for flag_name in (hou.nodeFlag.Render, hou.nodeFlag.Display):
    try:
        print(f"[diag] geo flag {flag_name}:", geo.isGenericFlagSet(flag_name))
    except Exception as e:
        print("[diag] flag check err", e)

# tiny test render with the 3 lights
cam = hou.node("/obj/cit_cam_hero")
print("[diag] cam t:", cam.parmTuple("t").eval(), "r:", cam.parmTuple("r").eval())
m = hou.node("/out").createNode("ifd", "diag_render")
m.parm("camera").set(cam.path())
m.parm("vm_picture").set(str(OUT / "diag_test.png"))
m.parm("override_camerares").set(1)
m.parm("res_overridex").set(480)
m.parm("res_overridey").set(270)
m.parm("vm_samplesx").set(2)
m.parm("vm_samplesy").set(2)
m.render()
p = OUT / "diag_test.png"
print("[diag] test exists:", p.exists(), p.stat().st_size if p.exists() else 0)
print("[diag] DONE")