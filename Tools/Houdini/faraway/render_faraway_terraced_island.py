r"""render_faraway_terraced_island.py -- headless Mantra clay review of HDA_Faraway_TerracedIsland.

Follows Docs/Houdini/HYTHON_HEADLESS_RENDER_FACTS_2026-10-05.md: IFD ROP with vm_picture, explicit
vobject on a plain geo (object_merge of the HDA output), no shop material, Mantra only (the OpenGL
ROP segfaults headless here). Prim Cd colours the pieces so strata/treads/falls read in clay.

Usage: hython render_faraway_terraced_island.py --view hero|side|top [--w 800 --h 450]
Exit 0 only if a non-empty PNG is on disk. Verify by looking at the PNG.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
HDA = PROJECT_ROOT / "hda" / "HDA_Faraway_TerracedIsland_1.0.hda"
OUT = PROJECT_ROOT / "Saved" / "Audit" / "faraway_hda" / "terraced_island"

VIEWS = {  # name -> (camera position, look-at)
    "hero": ((95.0, 70.0, 105.0), (0.0, -6.0, 0.0)),
    "side": ((0.0, -4.0, 150.0), (0.0, -6.0, 0.0)),
    "top": ((1.0, 150.0, 1.0), (0.0, 0.0, 0.0)),
}

CD_WRANGLE = r"""
string p = s@piece;
vector c = {0.55,0.5,0.45};
if (p == "cliff") c = {0.62,0.46,0.34};
else if (p == "tread") c = {0.45,0.62,0.32};
else if (p == "plateau") c = {0.35,0.7,0.3};
else if (p == "underside") c = {0.38,0.36,0.42};
else if (p == "waterfall") c = {0.55,0.8,1.0};
if (p == "cliff") c *= 0.8 + 0.2 * (i@band % 2);
v@Cd = c;
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--view", default="hero", choices=sorted(VIEWS))
    ap.add_argument("--w", type=int, default=800)
    ap.add_argument("--h", type=int, default=450)
    ap.add_argument("--dist", type=float, default=1.0, help="scale the camera distance")
    a = ap.parse_args()
    import hou

    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / f"terraced_island_{a.view}.png"
    for extra in OUT.glob(f"{dst.name}*"):
        extra.unlink()
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.hda.installFile(str(HDA))
    obj = hou.node("/obj")
    inst = obj.createNode("HDA_Faraway_TerracedIsland", "island")
    inst.cook(force=True)

    clay = obj.createNode("geo", "clay")
    for c in clay.children():
        c.destroy()
    om = clay.createNode("object_merge", "grab")
    om.parm("objpath1").set(inst.node("output0").path())
    om.parm("xformtype").set(0)
    wr = clay.createNode("attribwrangle", "cd")
    wr.parm("class").set(1)
    wr.parm("snippet").set(CD_WRANGLE)
    wr.setInput(0, om)
    wr.setDisplayFlag(True)
    wr.setRenderFlag(True)
    inst.setDisplayFlag(False)

    pos, tgt = VIEWS[a.view]
    pos = tuple(tgt[i] + (pos[i] - tgt[i]) * a.dist for i in range(3))
    cam = obj.createNode("cam", "cam")
    fwd = hou.Vector3(tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]).normalized()
    up = hou.Vector3(0, 1, 0) if a.view != "top" else hou.Vector3(0, 0, -1)
    right = fwd.cross(up).normalized()
    nup = right.cross(fwd).normalized()
    m = hou.Matrix4(1)
    for col, v in enumerate((right, nup, -fwd)):
        pass
    rows = (right, nup, -fwd)
    for r in range(3):
        for c in range(3):
            m.setAt(r, c, rows[r][c])
    m.setAt(3, 0, pos[0]); m.setAt(3, 1, pos[1]); m.setAt(3, 2, pos[2])
    cam.setWorldTransform(m)
    cam.parm("resx").set(a.w)
    cam.parm("resy").set(a.h)
    cam.parm("focal").set(35.0)

    rop = hou.node("/out").createNode("ifd", "isl_render")
    rop.parm("vm_picture").set(str(dst))
    rop.parm("trange").set(0)
    rop.parm("camera").set(cam.path())
    rop.parm("vobject").set(clay.path())
    rop.parm("soho_autoheadlight").set(1)
    for pn, v in (("vm_samplesx", 3), ("vm_samplesy", 3)):
        if rop.parm(pn):
            rop.parm(pn).set(v)
    print(f"[R] {a.view}: {a.w}x{a.h} -> {dst}")
    rop.render()
    ok = dst.exists() and dst.stat().st_size > 0
    print(f"[R] {'RENDER OK' if ok else 'RENDER FAILED'}: {dst} {dst.stat().st_size if dst.exists() else -1} bytes")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
