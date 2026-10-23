"""A0 - Karma headless pipeline spike for the Endless Escher Citadel.

Proves: SOP geometry -> LOP sopimport -> Karma ROP -> PNG, in hython.
Discovers exact karma rop param names + whether Apprentice caps resolution.
Output: Saved/Audit/endless_citadel/karma_spike.png

Run: hython Tools/Houdini/endless_citadel/karma_spike.py
"""
from pathlib import Path

import hou

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
OUT = ROOT / "Saved" / "Audit" / "endless_citadel"
OUT.mkdir(parents=True, exist_ok=True)

scene = hou.node("/obj")

# --- geometry: marble box on a floor ---
geo = scene.createNode("geo", "spike_geo")
box = geo.createNode("box", "box1")
box.parmTuple("t").set((0, 1.0, 0))
box.parm("sizex").set(1.4)
box.parm("sizey").set(1.4)
box.parm("sizez").set(1.4)
floor = geo.createNode("grid", "floor")
floor.parm("sizex").set(20)
floor.parm("sizey").set(20)

# --- material: Karma PrincipledShader, marble-ish ---
try:
    shader = hou.node("/mat").createNode("principledshader", "marble_ps")
except Exception as exc1:
    print("[spike] /mat create failed:", exc1)
    shader = geo.createNode("principledshader", "marble_ps")
print("[spike] shader at:", shader.path())
shader.parm("basecolorr").set(0.92)
shader.parm("basecolorg").set(0.90)
shader.parm("basecolorb").set(0.95)
shader.parm("rough").set(0.25)
try:
    shader.parm("iridescence").set(1.0)
except Exception as exc:
    print("[spike] no iridescence parm:", exc)

mat = geo.createNode("material", "mat1")
mat.parm("shop_materialpath1").set(shader.path())
mat.setNextInput(box)
merge = geo.createNode("merge", "merge1")
merge.setNextInput(mat)
merge.setNextInput(floor)
geo.layoutChildren()

# --- lights ---
key = scene.createNode("hlight", "key_light")
key.parmTuple("t").set((4, 5, -3))
key.parm("light_colorr").set(0.55)
key.parm("light_colorg").set(0.65)
key.parm("light_colorb").set(1.0)
key.parm("light_intensity").set(2.0)

# --- camera ---
cam = scene.createNode("cam", "spike_cam")
cam.parmTuple("t").set((5, 2.6, -5))
cam.parmTuple("r").set((-18, 45, 0))

# --- LOP net ---
lopnet = scene.createNode("lopnet", "spike_lop")
sopimp = lopnet.createNode("sopimport", "sop_import")
sopimp.parm("soppath").set(geo.path())

# --- karma rop ---
out = hou.node("/out")
karma = out.createNode("karma", "spike_karma")
try:
    sopimp.setRenderFlag(True)
    print("[spike] sopimport render flag set")
except Exception as exc:
    print("[spike] render flag failed:", exc)
try:
    karma.setNextInput(lopnet)
    print("[spike] connected lopnet; inputs:", karma.inputs())
except Exception as exc:
    print("[spike] lopnet input failed:", exc)
    try:
        karma.setInput(0, sopimp, 0)
        print("[spike] connected sopimport via setInput; inputs:", karma.inputs())
    except Exception as exc2:
        print("[spike] sopimport input failed:", exc2)

karma.parm("camera").set(cam.path())
karma.parm("picture").set(str(OUT / "karma_spike.png"))
try:
    karma.parm("override_camerares").set(1)
    karma.parm("resolutionx").set(2560)
    karma.parm("resolutiony").set(1440)
    print("[spike] res override set")
except Exception as exc:
    print("[spike] res override failed:", exc)
try:
    karma.parm("samplesperpixel").set(32)
except Exception:
    pass

karma.render()
print("[spike] render() returned")

png = OUT / "karma_spike.png"
if png.exists():
    hdr = png.read_bytes()[:26]
    w = int.from_bytes(hdr[16:20], "big")
    h = int.from_bytes(hdr[20:24], "big")
    print(f"[spike] OK {png.name} {png.stat().st_size} bytes {w}x{h}")
else:
    print("[spike] NO OUTPUT FILE")
print("[spike] DONE")