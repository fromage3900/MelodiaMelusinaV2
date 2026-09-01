#!/usr/bin/env hython
"""Cos_FlowerSpring — skirt silhouette pass v2 (detailed Houdini pipeline).

Redo of the 2026-08-31 v1 result (owner QA: "ugly — play with skirt silhouette
more"). v2 authors everything in DRESS UNITS (meters, Z-up) so no unit hack is
needed downstream, and plays the silhouette with four authored moves:

  1. Hem flare      — radial push below the waist with a cubic ease curve
  2. Train          — hi-lo asymmetry: back-hem extension with smooth falloff
  3. Petal overskirt— procedural ring of cupped, drooping petal panels around
                      the waist (the flower motif carried into the silhouette)
  4. Fold ridges    — radial sine ridges + fbm near the hem, seam-safe

Three presets are authored per run so the owner can pick a silhouette:
  cascade — deep flare + long train + 16 long petals
  tulip   — tucked hem, petals cup up, no train
  bloom   — wide horizontal ruffle, petals flare outward flat

Inputs : Saved/Audit/melusina_lookdev/flowers_outfit/passA2_skirt_panels.obj
Outputs: FS_SkirtDraped_<preset>.obj  (+ .fbx via Blender assembly pass)
         flowerspring_skirt_silhouette_manifest.json

Run: hython Tools/Houdini/sea_above_reef/flowerspring_skirt_silhouette.py
"""
import json
import math
from pathlib import Path

import hou

PROJECT = Path("C:/EnvironmentPortfolio/BS_GodFile")
OUT = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "flowers_outfit"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260831
SRC = OUT / "passA2_skirt_panels.obj"

PRESETS = {
    #            flare  train   petals  pet_len  pet_droop  pet_cup  ridge
    "cascade": dict(flare=0.42, train=0.34, petals=16, pet_len=0.46, pet_droop=0.55, pet_cup=0.10, ridge=0.020),
    "tulip":   dict(flare=0.18, train=0.00, petals=14, pet_len=0.34, pet_droop=-0.40, pet_cup=0.16, ridge=0.012),
    "bloom":   dict(flare=0.55, train=0.10, petals=18, pet_len=0.28, pet_droop=0.05, pet_cup=0.03, ridge=0.030),
}

SKIRT_SCRIPT = r'''
import hou, math

geo = hou.pwd().geometry()
P = __PRESET_JSON__

# ---- read source geometry (already imported upstream via File SOP merge) ----
geo.addAttrib(hou.attribType.Point, "Cd", (0.0, 0.0, 0.0))
geo.addAttrib(hou.attribType.Point, "layer", 0.0)
geo.addAttrib(hou.attribType.Point, "silhouetteU", 0.0)   # 0 waist .. 1 hem

PEACH=(1.0,0.70,0.48); BLUSH=(0.95,0.63,0.66); CREAM=(1.0,0.95,0.84); GOLD=(0.91,0.72,0.29)
def mixc(c1,c2,t): return tuple(c1[i]+(c2[i]-c1[i])*t for i in range(3))

# ---- silhouette frame from source bounds -----------------------------------
pts = geo.points()
if not pts:
    raise hou.Error("no source points")
zs = [p.position()[2] for p in pts]
xs = [p.position()[0] for p in pts]
ys = [p.position()[1] for p in pts]
z_min, z_max = min(zs), max(zs)
x_min, x_max = min(xs), max(xs)
y_min, y_max = min(ys), max(ys)
waist_z = z_max - (z_max - z_min) * 0.30      # top 30% band is the bodice/waist
hem_z = z_min
fall = max(waist_z - hem_z, 1e-4)
cx, cy = (x_min + x_max) * 0.5, (y_min + y_max) * 0.5
r_waist = 0.5 * min(x_max - x_min, y_max - y_min) * 0.5 + 0.12

# ---- move 1+2+4: flare / train / ridges on the source panels ---------------
for p in pts:
    x, y, z = p.position()
    below = max(0.0, (waist_z - z) / fall)          # 0 waist .. 1 hem
    u = below
    # radial distance from center axis
    dx, dy = x - cx, y - cy
    rad = math.sqrt(dx*dx + dy*dy)
    nx, ny = (dx / rad if rad > 1e-6 else 0.0), (dy / rad if rad > 1e-6 else 0.0)
    # move 1: cubic-ease flare
    flare = P["flare"] * (u ** 1.6)
    newx, newy = cx + dx * (1.0 + flare), cy + dy * (1.0 + flare)
    # move 2: hi-lo train — back hem (y > 0) drops, eased around the sides
    if P["train"] > 0.0:
        backness = max(0.0, (y - cy) / max(abs(y_max - cy), 1e-4))
        drop = P["train"] * (u ** 2.2) * (backness ** 1.5) * fall
        z -= drop
    # move 4: fold ridges — radial sine near hem, fading at waist
    ridge = math.sin((math.atan2(dy, dx)) * 22.0 + u * 3.0)
    ridge *= P["ridge"] * (u ** 2.0)
    newx += nx * ridge
    newy += ny * ridge
    # subtle fbm wobble for authored-cloth feel (deterministic)
    w = (math.sin(x * 37.0 + y * 23.0 + z * 11.0) * math.sin(x * 13.0 - y * 41.0)) * 0.006 * u
    p.setPosition(hou.Vector3(newx + nx * w, newy + ny * w, z))
    p.setAttribValue("Cd", mixc(PEACH, CREAM, u * 0.7))
    p.setAttribValue("silhouetteU", u)

# ---- move 3: petal overskirt ring (procedural, cupped, drooping) -----------
def petal_surface(a_center):
    """Cupped petal panel: u along length (waist->hem), v across width."""
    L = P["pet_len"]; W = P["pet_len"] * 0.62
    NU, NV = 10, 7
    grid = [[None] * (NV + 1) for _ in range(NU + 1)]
    for iu in range(NU + 1):
        u = iu / NU
        for iv in range(NV + 1):
            v = iv / NV
            ang = a_center + (v - 0.5) * (W / (r_waist + L * u))
            rad = r_waist * 0.92 + L * u
            # droop: +down as petals fall; negative tucks them up (tulip)
            droop = P["pet_droop"] * L * (u ** 1.8)
            # cup: cross-section lifts the edges of the petal
            cup = P["pet_cup"] * L * math.sin(v * math.pi) * (0.3 + 0.7 * u)
            # longitudinal curl: tips roll under/over
            curl = math.sin(u * math.pi * 0.85) * L * 0.18
            zz = waist_z - 0.02 - u * L * 0.55 - droop + cup + curl
            # gentle wave along the width so petals do not read flat
            wave = math.sin(v * math.pi * 2.0 + a_center * 3.0) * L * 0.04 * u
            px = cx + rad * math.cos(ang)
            py = cy + rad * math.sin(ang)
            p = geo.createPoint()
            p.setPosition(hou.Vector3(px, py, zz + wave))
            col = mixc(BLUSH, GOLD, 0.5 + 0.5 * math.sin(a_center * 2.0))
            p.setAttribValue("Cd", mixc(col, CREAM, u * 0.5))
            p.setAttribValue("layer", 2.0)
            p.setAttribValue("silhouetteU", u)
            grid[iu][iv] = p
    for iu in range(NU):
        for iv in range(NV):
            f = geo.createPolygon(); f.setIsClosed(True)
            for pt in (grid[iu][iv], grid[iu][iv+1], grid[iu+1][iv+1], grid[iu+1][iv]):
                f.addVertex(pt)

N_PET = int(P["petals"])
for k in range(N_PET):
    a = 2 * math.pi * (k + 0.5) / N_PET + 0.13   # half-step offset vs panel seams
    petal_surface(a)
'''

def build_and_export(preset: str) -> dict:
    obj = hou.node("/obj")
    sop = obj.createNode("geo", f"skirt_{preset}")
    sop.moveToGoodPosition()

    file_sop = sop.createNode("file", "IN_SKIRT")
    file_sop.parm("file").set(str(SRC).replace("\\", "/"))

    gen = sop.createNode("python", "SILHOUETTE_V2")
    gen.parm("python").set(SKIRT_SCRIPT.replace("__PRESET_JSON__", json.dumps(PRESETS[preset])))
    gen.setInput(0, file_sop)
    gen.setDisplayFlag(True)
    gen.setRenderFlag(True)

    gen.cook(force=True)
    errs = gen.errors()
    if errs:
        print(f"[{preset}] GEN errors: {errs}")
    g = gen.geometry()
    print(f"[{preset}] points: {len(g.points()) if g else 'NONE'}")

    rop = sop.createNode("rop_geometry")
    rop.setInput(0, gen)
    rop.parm("sopoutput").set(str(OUT / f"FS_SkirtDraped_{preset}.obj").replace("\\", "/"))
    rop.parm("trange").set(0)
    rop.parm("execute").pressButton()
    ok = (OUT / f"FS_SkirtDraped_{preset}.obj").exists()
    print(f"[{preset}] ROP errors: {rop.errors()} written={ok}")
    return {"preset": preset, "points": len(g.points()) if g else 0,
            "obj": f"FS_SkirtDraped_{preset}.obj", "written": ok, "errors": errs}

results = {}
for preset in PRESETS:
    results[preset] = build_and_export(preset)

hou.hipFile.clear(suppress_save_prompt=True)
(OUT / "flowerspring_skirt_silhouette_manifest.json").write_text(json.dumps({
    "schema": "melodia.flowerspring_skirt_silhouette.v2",
    "seed": SEED,
    "source": "passA2_skirt_panels.obj",
    "units": "meters (dress-native, no unit correction)",
    "silhouette_moves": ["hem_flare_cubic", "hilo_train", "petal_overskirt_ring",
                          "radial_fold_ridges", "fbm_wobble"],
    "presets": PRESETS,
    "results": results,
    "houdini": hou.applicationVersionString(),
}, indent=1), encoding="utf-8")
print("SKIRT_SILHOUETTE_DONE " + json.dumps({k: v["written"] for k, v in results.items()}))
