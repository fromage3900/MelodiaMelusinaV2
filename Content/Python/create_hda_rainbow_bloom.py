"""Create hda/RainbowBloom_1.0.hda and a cooked FBX via hython.

Rainbow flower field for L_MelusinaMorning: 7 ROYGBIV bands, golden-angle
phyllotaxis, Chladni keep, same seed/radii as recipes/morning_rainbow_bloom.v1.json.

Houdini Y-up metres. Houdini Engine converts to UE Z-up cm on cook.
FBX is a fallback pretty-win if the Engine license is not checked out.

    hython Content/Python/create_hda_rainbow_bloom.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HDA = ROOT / "hda" / "RainbowBloom_1.0.hda"
DEFAULT_FBX = ROOT / "Saved" / "Houdini" / "RainbowBloom" / "RainbowBloom_3900.fbx"
RECEIPT = ROOT / "Saved" / "Audit" / "houdini_rainbow_bloom_2026-09-17.json"

# Matches recipes/morning_rainbow_bloom.v1.json
TINTS = (
    (1.00, 0.18, 0.22),
    (1.00, 0.45, 0.10),
    (1.00, 0.80, 0.20),
    (0.35, 0.95, 0.45),
    (0.30, 0.55, 1.00),
    (0.45, 0.30, 0.95),
    (0.75, 0.35, 1.00),
)

PETAL_SNIPPET = r"""
// Petal sheet in local metres (Houdini Y-up). Called on a grid of points.
float u = (float)@ptnum / max(1, npoints(0)-1);
float v = @P.z;  // unused; rebuild from ptnum on a 12x8 grid
int cols = 12;
int rows = 8;
int col = @ptnum % cols;
int row = @ptnum / cols;
float su = (float)col / (cols-1) * 2.0 - 1.0;   // -1..1 across
float sv = (float)row / (rows-1);               // 0 tip .. 1 base
float width = (1.0 - sv) * 0.06 * (1.0 - abs(su)*0.35);
@P = set(su * width, sv * 0.18, 0.02 * sin(sv * 3.14159) + 0.01 * su * su);
@N = set(0, 0, 1);
@uv = set((su+1)*0.5, sv, 0);
"""

PYTHON_POINTS = r'''
import hou, math, random
node = hou.pwd()
geo = node.geometry()
c = hou.node("../controls")
seed = int(c.evalParm("seed"))
band_count = int(c.evalParm("bandCount"))
r0 = float(c.evalParm("innerRadiusM"))
width = float(c.evalParm("bandWidthM"))
density = float(c.evalParm("densityPerM2"))
golden = float(c.evalParm("goldenAngle"))
jitter = float(c.evalParm("radialJitterM"))
sector_c = float(c.evalParm("sectorCenterDeg"))
sector_h = float(c.evalParm("sectorHalfDeg"))
s_lo = float(c.evalParm("scaleLo"))
s_hi = float(c.evalParm("scaleHi"))
thresh = float(c.evalParm("chladniThreshold"))
up = float(c.evalParm("upOffsetM"))
tints = [
    (1.00, 0.18, 0.22), (1.00, 0.45, 0.10), (1.00, 0.80, 0.20),
    (0.35, 0.95, 0.45), (0.30, 0.55, 1.00), (0.45, 0.30, 0.95), (0.75, 0.35, 1.00),
]
geo.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
geo.addAttrib(hou.attribType.Point, "pscale", 1.0)
geo.addAttrib(hou.attribType.Point, "N", (0.0, 1.0, 0.0))
geo.addAttrib(hou.attribType.Point, "band", 0)
geo.addAttrib(hou.attribType.Point, "hue_seed", 0.0)
sector_frac = max(0.001, min(1.0, sector_h / 180.0))
span = 2.0 * math.radians(sector_h)
theta0 = math.radians(sector_c) - span * 0.5
rng = random.Random(seed)
for b in range(band_count):
    r_in = r0 + b * width
    r_out = r_in + width
    area = math.pi * (r_out * r_out - r_in * r_in) * sector_frac
    n_target = max(1, int(round(area * density)))
    phase = rng.random() * 2.0 * math.pi
    mode_n, mode_m = 2 + b, 3 + b
    for i in range(n_target):
        t = (i + 0.5) / float(n_target)
        r = math.sqrt(r_in * r_in + t * (r_out * r_out - r_in * r_in))
        r += (rng.random() * 2.0 - 1.0) * jitter
        theta = phase + i * golden
        theta = theta0 + (theta % (2.0 * math.pi)) / (2.0 * math.pi) * span
        x = r * math.cos(theta)
        z = r * math.sin(theta)
        plate = 50.0
        u = max(0.0, min(1.0, x / plate + 0.5))
        v = max(0.0, min(1.0, z / plate + 0.5))
        fig = abs(math.cos(mode_n * math.pi * u) * math.cos(mode_m * math.pi * v)
                  - math.cos(mode_m * math.pi * u) * math.cos(mode_n * math.pi * v))
        weight = 1.0 - max(0.0, min(1.0, fig))
        keep_p = max(thresh, weight * weight)
        if rng.random() > keep_p:
            continue
        pt = geo.createPoint()
        pt.setPosition(hou.Vector3(x, up, z))
        tint = tints[b % len(tints)]
        pt.setAttribValue("Cd", tint)
        sc = s_lo + rng.random() * (s_hi - s_lo)
        pt.setAttribValue("pscale", sc * 0.12)
        yaw = rng.random() * 2.0 * math.pi
        pt.setAttribValue("N", (math.sin(yaw), 0.0, math.cos(yaw)))
        pt.setAttribValue("band", b)
        pt.setAttribValue("hue_seed", (b + 0.5) / float(band_count))
'''


def _build(geo, hou):
    for child in geo.children():
        try:
            child.destroy()
        except Exception:
            pass

    controls = geo.createNode("null", "controls")
    group = controls.parmTemplateGroup()
    group.append(hou.IntParmTemplate("seed", "Seed", 1, default_value=(3900,), min=1, max=9999999))
    group.append(hou.IntParmTemplate("bandCount", "Band Count", 1, default_value=(7,), min=1, max=12))
    group.append(hou.FloatParmTemplate("innerRadiusM", "Inner Radius (m)", 1, default_value=(10.0,), min=0.1, max=80))
    group.append(hou.FloatParmTemplate("bandWidthM", "Band Width (m)", 1, default_value=(2.0,), min=0.2, max=20))
    group.append(hou.FloatParmTemplate("densityPerM2", "Density / m2", 1, default_value=(6.5,), min=0.1, max=40))
    group.append(hou.FloatParmTemplate("goldenAngle", "Phyllotaxis Angle (rad)", 1, default_value=(2.399963,)))
    group.append(hou.FloatParmTemplate("radialJitterM", "Radial Jitter (m)", 1, default_value=(0.18,)))
    group.append(hou.FloatParmTemplate("sectorCenterDeg", "Sector Center Deg", 1, default_value=(0.0,), min=-180, max=180))
    group.append(hou.FloatParmTemplate("sectorHalfDeg", "Sector Half Width Deg", 1, default_value=(40.0,), min=1, max=180))
    group.append(hou.FloatParmTemplate("scaleLo", "Scale Lo", 1, default_value=(1.8,)))
    group.append(hou.FloatParmTemplate("scaleHi", "Scale Hi", 1, default_value=(3.2,)))
    group.append(hou.FloatParmTemplate("chladniThreshold", "Chladni Threshold", 1, default_value=(0.35,)))
    group.append(hou.FloatParmTemplate("upOffsetM", "Up Offset (m)", 1, default_value=(0.04,)))
    controls.setParmTemplateGroup(group)

    empty = geo.createNode("null", "empty_points")
    pysop = geo.createNode("python", "phyllotaxis_chladni")
    pysop.parm("python").set(PYTHON_POINTS)
    pysop.setInput(0, empty)

    grid = geo.createNode("grid", "petal_grid")
    grid.parm("rows").set(8)
    grid.parm("cols").set(12)
    grid.parm("sizex").set(0.12)
    grid.parm("sizey").set(0.18)
    grid.parm("orient").set(0)  # XY

    petal = geo.createNode("attribwrangle", "shape_petal")
    petal.parm("class").set(0)
    petal.parm("snippet").set(PETAL_SNIPPET)
    petal.setInput(0, grid)

    fuse = geo.createNode("polyfill", "petal_fill")
    try:
        fuse.setInput(0, petal)
    except Exception:
        fuse = geo.createNode("divide", "petal_fill")
        fuse.setInput(0, petal)

    copy = geo.createNode("copytopoints::2.0", "copy_petals")
    copy.setInput(0, fuse)
    copy.setInput(1, pysop)
    try:
        copy.parm("pack").set(0)
        copy.parm("usetargetvattr").set(0)
    except Exception:
        pass

    color = geo.createNode("attribpromote", "keep_cd")
    try:
        color.parm("inname").set("Cd")
        color.parm("outclass").set(1)  # point
        color.setInput(0, copy)
        last = color
    except Exception:
        last = copy

    out_node = geo.createNode("output", "output0")
    out_node.setInput(0, last)
    out_node.setDisplayFlag(True)
    out_node.setRenderFlag(True)
    geo.layoutChildren()
    return pysop, out_node


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_HDA)
    parser.add_argument("--fbx", type=Path, default=DEFAULT_FBX)
    parser.add_argument("--no-hda", action="store_true")
    parser.add_argument("--no-fbx", action="store_true")
    args = parser.parse_args()

    try:
        import hou
    except ImportError as e:
        print(f"[HDA] hou not available: {e}", file=sys.stderr)
        return 2

    receipt = {
        "schema": "melodia.houdini_rainbow_bloom.v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "houdini": hou.applicationVersionString(),
        "hda": str(args.out).replace("\\", "/"),
        "fbx": str(args.fbx).replace("\\", "/"),
    }

    obj = hou.node("/obj")
    existing = hou.node("/obj/RainbowBloom_Template")
    if existing:
        existing.destroy()
    geo = obj.createNode("geo", "RainbowBloom_Template")
    wrangle, out_node = _build(geo, hou)

    npts = 0
    nprims = 0
    try:
        pysop, out_node = wrangle, out_node  # names: wrangle is actually pysop
    except Exception:
        pass
    try:
        wrangle.cook(force=True)
        g = wrangle.geometry()
        npts = len(g.points()) if g else 0
    except Exception as e:
        receipt["point_count_error"] = str(e)[:300]
        receipt["point_errors"] = list(wrangle.errors()) if hasattr(wrangle, "errors") else []
    try:
        out_node.cook(force=True)
        og = out_node.geometry()
        npts = len(og.points()) if og else npts
        nprims = len(og.prims()) if og else 0
        if og and npts:
            bgeo = args.fbx.with_suffix(".bgeo.sc")
            bgeo.parent.mkdir(parents=True, exist_ok=True)
            og.saveToFile(str(bgeo))
            receipt["bgeo"] = str(bgeo).replace("\\", "/")
            receipt["bgeo_bytes"] = bgeo.stat().st_size
            objp = args.fbx.with_suffix(".obj")
            try:
                og.saveToFile(str(objp))
                receipt["obj"] = str(objp).replace("\\", "/")
                receipt["obj_bytes"] = objp.stat().st_size
            except Exception as e:
                receipt["obj_error"] = str(e)[:200]
    except Exception as e:
        receipt["output_cook_error"] = str(e)[:300]
    receipt["point_count"] = npts
    receipt["prim_count"] = nprims

    if not args.no_hda:
        out: Path = args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            os.remove(out)
        try:
            geo_node = hou.node("/obj/RainbowBloom_Template")
            geo_node.createDigitalAsset(
                name="RainbowBloom",
                hda_file_name=str(out),
                description="Melodia Morning rainbow bloom (phyllotaxis + Chladni petals)",
            )
            receipt["hda_bytes"] = out.stat().st_size
            receipt["hda_ok"] = True
        except Exception as e:
            receipt["hda_ok"] = False
            receipt["hda_error"] = str(e)[:400]

    if not args.no_fbx:
        fbx: Path = args.fbx
        fbx.parent.mkdir(parents=True, exist_ok=True)
        try:
            outnet = hou.node("/out")
            if outnet is None:
                outnet = hou.node("/").createNode("ropnet", "out")
            fbxnode = outnet.createNode("filmboxfbx", "rainbow_fbx")
            fbxnode.parm("sopoutput").set(str(fbx).replace("\\", "/"))
            fbxnode.parm("startnode").set("/obj/RainbowBloom_Template")
            try:
                fbxnode.parm("convertunits").set(True)
            except Exception:
                pass
            fbxnode.render()
            receipt["fbx_ok"] = fbx.exists()
            receipt["fbx_bytes"] = fbx.stat().st_size if fbx.exists() else 0
        except Exception as e:
            receipt["fbx_ok"] = False
            receipt["fbx_error"] = str(e)[:400]

    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if receipt.get("hda_ok") or receipt.get("fbx_ok") else 1


if __name__ == "__main__":
    sys.exit(main())
