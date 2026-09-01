#!/usr/bin/env hython
"""Cos_FlowerSpring — crown + wings rebuild v2 (detailed Houdini pipeline).

Redo of the 2026-08-31 v1 pieces (owner QA: crown read as a jagged paper ring,
wings read as a flat sawtooth slab). v2 changes the authoring model:

  * DRESS UNITS (meters, Z-up) — pieces drop onto the dress with no scaling.
  * Crown: lathe band with rounded cross-section, petal panels built as
    parametric surfaces with longitudinal curl + cross-section cup + twist and
    CLOSED SHELLS (front + back + rim, ~2 mm stock), faceted gems in bezels,
    per-petal planar UVs.
  * Wings: membranes from a polar parametric grid shaped by a smooth-scallop
    outline (cosine scallops, NOT triangle teeth), with membrane thickness,
    tapered vein strips, smooth rim cups, radial UVs, wingPhase attributes.
  * Anchors authored in place: crown at head height/rotation-center, wing
    roots behind the shoulder blades.

Outputs -> Saved/Audit/melusina_lookdev/flowers_outfit/
  FS_Crown_v2.obj, FS_Wings_v2.obj, flowerspring_crown_wings_v2_manifest.json

Run: hython Tools/Houdini/sea_above_reef/flowerspring_crown_wings_v2.py
"""
import json
import math
from pathlib import Path

import hou

PROJECT = Path("C:/EnvironmentPortfolio/BS_GodFile")
OUT = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "flowers_outfit"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260831

CROWN_SCRIPT = r'''
import hou, math

geo = hou.pwd().geometry()
geo.addAttrib(hou.attribType.Point, "Cd", (0.0, 0.0, 0.0))
geo.addAttrib(hou.attribType.Point, "rotPhase", 0.0)
geo.addAttrib(hou.attribType.Point, "petalU", 0.0)
geo.addAttrib(hou.attribType.Vertex, "uv", hou.Vector3(0.0, 0.0, 0.0))
geo.addAttrib(hou.attribType.Point, "piece", 0.0)   # 0 band, 1 petal, 2 gem

GOLD=(0.91,0.72,0.29); PEACH=(1.0,0.70,0.48); PEARL=(1.0,0.96,0.90); BLUSH=(0.95,0.63,0.66)
def mixc(c1,c2,t): return tuple(c1[i]+(c2[i]-c1[i])*t for i in range(3))
def poly(pts, closed=True, uvs=None):
    f = geo.createPolygon(); f.setIsClosed(closed)
    for i, p in enumerate(pts):
        vtx = f.addVertex(p)
        if uvs is not None:
            vtx.setAttribValue("uv", hou.Vector3(uvs[i][0], uvs[i][1], 0.0))
    return f

# ---- frame: head-top in dress space ----------------------------------------
HEAD_C = hou.Vector3(0.0, -0.02, 1.52)     # dress head center (meters)
R_BAND = 0.105                              # sits on the hair, not floating
BAND_R = 0.014                              # rounded tube radius
N_PET  = 12
PET_L  = 0.055                              # petal length (5.5 cm)
PET_TWIST = math.radians(18)
STOCK  = 0.002                              # shell thickness

def lathed_band():
    """Tube lathe with rounded cross-section: rings of the tube profile."""
    SEGS, RSEG = 64, 8
    rings = []
    for i in range(SEGS):
        a = 2*math.pi*i/SEGS
        ring = []
        for j in range(RSEG):
            b = 2*math.pi*j/RSEG
            rr = R_BAND + BAND_R*math.cos(b)
            zz = BAND_R*math.sin(b)
            p = geo.createPoint()
            p.setPosition(HEAD_C + hou.Vector3(rr*math.cos(a), rr*math.sin(a), zz))
            p.setAttribValue("Cd", mixc(GOLD, PEACH, 0.25+0.25*math.sin(b)))
            p.setAttribValue("piece", 0.0)
            ring.append(p)
        rings.append(ring)
    for i in range(SEGS):
        i2 = (i+1) % SEGS
        for j in range(RSEG-1):
            j2 = j+1
            u0, u1 = i/SEGS, (i+1)/SEGS
            v0, v1 = j/RSEG, (j+1)/RSEG
            poly([rings[i][j], rings[i][j2], rings[i2][j2], rings[i2][j]],
                 uvs=[(u0,v0),(u0,v1),(u1,v1),(u1,v0)])

def shell(front, back, front_uv):
    """Closed shell from a front grid + mirrored back grid (same topology)."""
    nr, nc = len(front), len(front[0])
    for r in range(nr-1):
        for c in range(nc-1):
            u0, u1 = front_uv[r][c], front_uv[r][c+1]
            v0, v1 = front_uv[r][c], front_uv[r+1][c]
            poly([front[r][c], front[r][c+1], front[r+1][c+1], front[r+1][c]],
                 uvs=[u0, u1, front_uv[r+1][c+1], front_uv[r+1][c]])
            poly([back[r][c], back[r+1][c], back[r+1][c+1], back[r][c+1]],
                 uvs=[v0, front_uv[r+1][c], front_uv[r+1][c+1], u1])
    for c in range(nc-1):
        poly([front[0][c], back[0][c], back[0][c+1], front[0][c+1]],
             uvs=[front_uv[0][c], front_uv[0][c], front_uv[0][c+1], front_uv[0][c+1]])
        poly([front[-1][c], front[-1][c+1], back[-1][c+1], back[-1][c]],
             uvs=[front_uv[-1][c], front_uv[-1][c+1], front_uv[-1][c+1], front_uv[-1][c]])
    for r in range(nr-1):
        poly([front[r][0], front[r+1][0], back[r+1][0], back[r][0]],
             uvs=[front_uv[r][0], front_uv[r+1][0], front_uv[r+1][0], front_uv[r][0]])
        poly([front[r][-1], back[r][-1], back[r+1][-1], front[r+1][-1]],
             uvs=[front_uv[r][-1], front_uv[r][-1], front_uv[r+1][-1], front_uv[r+1][-1]])

def petal(a_center, k):
    """Cupped, curled, twisted petal as a closed parametric shell."""
    NU, NV = 9, 6
    W = PET_L*0.72
    front = [[None]*(NV+1) for _ in range(NU+1)]
    back  = [[None]*(NV+1) for _ in range(NU+1)]
    fuv   = [[None]*(NV+1) for _ in range(NU+1)]
    col = mixc(GOLD, PEACH, (k % 3)/2.0)
    for iu in range(NU+1):
        u = iu/NU
        for iv in range(NV+1):
            v = iv/NV
            width = W*math.sin(math.pi*min(1.0, 0.15+0.85*u))**0.7
            ang = a_center + (v-0.5)*(width/max(R_BAND, 1e-4)) + PET_TWIST*u
            rad = R_BAND + PET_L*u
            z = 0.028*math.sin(u*math.pi*0.85) - 0.020*u*u      # rise then tip back
            cup = 0.016*math.sin(v*math.pi)*(0.25+0.75*u)        # cross-section cup
            px = HEAD_C[0] + rad*math.cos(ang)
            py = HEAD_C[1] + rad*math.sin(ang)
            pz = HEAD_C[2] + z + cup
            mid = hou.Vector3(px, py, pz)
            nrm = hou.Vector3(-math.sin(ang)*0.35, math.cos(ang)*0.35, 1.0).normalized()
            fp = geo.createPoint(); fp.setPosition(mid + nrm*STOCK*0.5)
            bp = geo.createPoint(); bp.setPosition(mid - nrm*STOCK*0.5)
            cuv = mixc(col, PEARL, u*u*0.8)
            for p in (fp, bp):
                p.setAttribValue("Cd", cuv)
                p.setAttribValue("rotPhase", k/N_PET)
                p.setAttribValue("petalU", u)
                p.setAttribValue("piece", 1.0)
            front[iu][iv] = fp; back[iu][iv] = bp
            # per-petal uv island
            u0 = k/N_PET; u1 = (k+1)/N_PET
            fuv[iu][iv] = (u0 + (u1-u0)*u, v)
    shell(front, back, fuv)

def gem(k):
    """Faceted gem in a gold bezel cup, sitting on the band."""
    a_center = 2*math.pi*k/7 + 0.22
    s = 0.009
    cx, cy = HEAD_C[0]+R_BAND*math.cos(a_center), HEAD_C[1]+R_BAND*math.sin(a_center)
    cz = HEAD_C[2] + 0.004
    # gem island in uv: small box reserved at u ~ k/7 band bottom
    gu, gv = k/7.0, 0.0
    bez = []
    for i in range(10):
        b = 2*math.pi*i/10
        p = geo.createPoint()
        p.setPosition(hou.Vector3(cx+s*1.35*math.cos(b), cy+s*1.35*math.sin(b), cz-0.004))
        p.setAttribValue("Cd", mixc(GOLD, PEACH, 0.5)); p.setAttribValue("piece", 0.0)
        bez.append(p)
    base = geo.createPoint()
    base.setPosition(hou.Vector3(cx, cy, cz-0.004))
    base.setAttribValue("Cd", mixc(GOLD, PEACH, 0.5)); base.setAttribValue("piece", 0.0)
    for i in range(10):
        poly([base, bez[i], bez[(i+1) % 10]],
             uvs=[(gu+0.05,gv+0.05),(gu+0.1*i/10,gv),(gu+0.1*(i+1)/10,gv)])
    # gem: low-profile brilliant (octahedral top + pavilion)
    top = geo.createPoint(); top.setPosition(hou.Vector3(cx, cy, cz+s*0.9))
    top.setAttribValue("Cd", PEARL); top.setAttribValue("piece", 2.0)
    girdle = []
    for i in range(8):
        b = 2*math.pi*i/8
        p = geo.createPoint()
        p.setPosition(hou.Vector3(cx+s*math.cos(b), cy+s*math.sin(b), cz))
        p.setAttribValue("Cd", mixc(PEARL, BLUSH, 0.3)); p.setAttribValue("piece", 2.0)
        girdle.append(p)
    tip = geo.createPoint(); tip.setPosition(hou.Vector3(cx, cy, cz-s*0.7))
    tip.setAttribValue("Cd", PEARL); tip.setAttribValue("piece", 2.0)
    for i in range(8):
        poly([top, girdle[i], girdle[(i+1) % 8]],
             uvs=[(gu+0.05,gv+0.1),(gu+0.08*i/8,gv+0.15),(gu+0.08*(i+1)/8,gv+0.15)])
        poly([tip, girdle[(i+1) % 8], girdle[i]],
             uvs=[(gu+0.05,gv),(gu+0.08*(i+1)/8,gv+0.15),(gu+0.08*i/8,gv+0.15)])

lathed_band()
for k in range(N_PET):
    petal(2*math.pi*(k+0.5)/N_PET, k)
for k in range(7):
    gem(k)
'''

WING_SCRIPT = r'''
import hou, math

geo = hou.pwd().geometry()
geo.addAttrib(hou.attribType.Point, "Cd", (0.0, 0.0, 0.0))
geo.addAttrib(hou.attribType.Point, "wingPhase", 0.0)
geo.addAttrib(hou.attribType.Point, "edgeU", 0.0)
geo.addAttrib(hou.attribType.Vertex, "uv", hou.Vector3(0.0, 0.0, 0.0))
geo.addAttrib(hou.attribType.Point, "piece", 0.0)   # 0 membrane, 1 vein, 2 rim cup

BLUSH=(0.95,0.63,0.66); PEARL=(1.0,0.96,0.90); GOLD=(0.91,0.72,0.29); SPRING=(0.66,0.85,0.42)
def mixc(c1,c2,t): return tuple(c1[i]+(c2[i]-c1[i])*t for i in range(3))
def poly(pts, closed=True, uvs=None):
    f = geo.createPolygon(); f.setIsClosed(closed)
    for i, p in enumerate(pts):
        vtx = f.addVertex(p)
        if uvs is not None:
            vtx.setAttribValue("uv", hou.Vector3(uvs[i][0], uvs[i][1], 0.0))
    return f

# anchors: behind the shoulder blades (dress space, meters)
BACK_Y = 0.16
ANCHOR = {"fore_R": hou.Vector3( 0.055, BACK_Y, 1.24),
          "fore_L": hou.Vector3(-0.055, BACK_Y, 1.24),
          "hind_R": hou.Vector3( 0.045, BACK_Y+0.02, 1.16),
          "hind_L": hou.Vector3(-0.045, BACK_Y+0.02, 1.16)}
SPAN = {"fore": 0.36, "hind": 0.24}
SCALLOPS = {"fore": 7, "hind": 5}
SCALLOP_AMP = 0.055          # smooth cosine scallops (NOT triangle teeth)
STOCK = 0.0012               # membrane thickness

def wing_shape(t):
    """Outline radius factor: full near root, tapered lobe to the tip."""
    return 0.30 + 0.70*math.sin(math.pi*min(1.0, 0.12+0.88*t)**0.8)*(1.0-0.35*t)

def membrane(name, side, kind):
    sign = 1.0 if side == "R" else -1.0
    anchor = ANCHOR[kind+"_"+side]
    span = SPAN[kind]
    ns = SCALLOPS[kind]
    phase = 0.0 if kind == "fore" else 0.5
    if side == "L":
        phase += 0.25
    # sweep direction: outward + upward + back
    dir0 = hou.Vector3(sign*0.92, 0.28, 0.55).normalized()
    up   = hou.Vector3(0.0, 0.0, 1.0)
    # local frame
    right = hou.Vector3(0.0, 1.0, 0.0).cross(dir0).normalized()
    if right.dot(up) < 0: right = -right
    realup = dir0.cross(right).normalized()

    NU, NV = 20, 30
    grid = [[None]*(NV+1) for _ in range(NU+1)]
    for iu in range(NU+1):
        u = iu/NU                     # radial 0..1
        for iv in range(NV+1):
            v = iv/NV                 # sweep 0..1 (root arc to tip)
            sweep = math.pi*0.92*v
            shape = wing_shape(v)
            r = span*u*shape
            scallop = 1.0 - SCALLOP_AMP*(1.0-abs(math.sin(v*math.pi*ns)))*u
            r *= scallop
            # camber: membrane bows back and ripples gently
            camber = math.sin(u*math.pi)*0.018 - 0.02*u*u
            ripple = math.sin(v*math.pi*2.0 + u*6.0)*0.004*u
            pos = anchor + dir0*(r*math.cos(sweep*0.5)) \
                       + right*(r*math.sin(sweep - math.pi*0.46)) \
                       + realup*(camber + ripple)
            col = mixc(BLUSH, PEARL, 0.15+0.75*u)
            p = geo.createPoint()
            p.setPosition(pos)
            p.setAttribValue("Cd", col)
            p.setAttribValue("wingPhase", phase)
            p.setAttribValue("edgeU", u)
            p.setAttribValue("piece", 0.0)
            grid[iu][iv] = (p, u, v)
    # double-sided membrane with slight thickness at the root
    for iu in range(NU):
        for iv in range(NV):
            a, ua, va = grid[iu][iv]
            b, ub, vb = grid[iu][iv+1]
            c, uc, vc = grid[iu+1][iv+1]
            d, ud, vd = grid[iu+1][iv]
            poly([a, b, c, d], uvs=[(ua,va),(ub,vb),(uc,vc),(ud,vd)])
            poly([a, d, c, b], uvs=[(ua,va),(ud,vd),(uc,vc),(ub,vb)])   # reversed winding
    # veins: tapered strips along radial lines (piece 1)
    N_VEINS = 6
    for k in range(N_VEINS):
        vline = k/(N_VEINS-1)
        for iu in range(NU):
            u0, u1 = iu/NU, (iu+1)/NU
            w0 = 0.0035*(1.0-u0) + 0.0006
            w1 = 0.0035*(1.0-u1) + 0.0006
            def grid_at(uu, off):
                vv = min(1.0, max(0.0, vline + off))
                p0, _, _ = grid[int(round(uu*NU))][int(round(vv*NV))]
                return p0.position()
            pa = grid_at(u0, -w0); pb = grid_at(u0, w0)
            pc = grid_at(u1, -w1); pd = grid_at(u1, w1)
            A = geo.createPoint(); A.setPosition(pa)
            B = geo.createPoint(); B.setPosition(pb)
            C = geo.createPoint(); C.setPosition(pc)
            D = geo.createPoint(); D.setPosition(pd)
            col = mixc(GOLD, SPRING, u0)
            for p in (A, B, C, D):
                p.setAttribValue("Cd", col)
                p.setAttribValue("wingPhase", phase)
                p.setAttribValue("piece", 1.0)
            # vein uv island: reserved strip at v < 0 (below membrane island)
            poly([A, B, D, C], uvs=[(0.5+vline*0.15, -0.05-u0*0.4),
                                     (0.5+vline*0.15+0.02, -0.05-u0*0.4),
                                     (0.5+vline*0.15+0.02, -0.05-u1*0.4),
                                     (0.5+vline*0.15, -0.05-u1*0.4)])
    # rim cups: small smooth cups along the outer 45% of the edge (piece 2)
    N_CUPS = 9
    for k in range(N_CUPS):
        v = 0.55 + 0.45*k/(N_CUPS-1)
        anchor_pt = grid[NU][int(round(v*NV))][0]
        pos = anchor_pt.position()
        s = 0.012 if kind == "fore" else 0.009
        ring = []
        for i in range(8):
            b = 2*math.pi*i/8
            rr = s*(0.75 + 0.25*math.cos(b))
            p = geo.createPoint()
            p.setPosition(pos + realup*(0.002 + s*0.5*math.cos(b)) + right*(rr*math.sin(b)))
            col = mixc(GOLD, BLUSH, k % 2)
            p.setAttribValue("Cd", col)
            p.setAttribValue("wingPhase", phase)
            p.setAttribValue("piece", 2.0)
            ring.append(p)
        for i in range(8):
            poly([ring[i], ring[(i+1) % 8], anchor_pt],
                 uvs=[(1.05+k*0.03+i/8*0.02, -0.05),(1.05+k*0.03+(i+1)/8*0.02, -0.05),
                       (1.05+k*0.03+0.01, -0.02)])

for side in ("R", "L"):
    for kind in ("fore", "hind"):
        membrane(kind+"_"+side, side, kind)
'''

def build_and_export(name: str, script: str) -> dict:
    obj = hou.node("/obj")
    sop = obj.createNode("geo", name)
    sop.moveToGoodPosition()
    gen = sop.createNode("python", "GEN_V2")
    gen.parm("python").set(script.strip())
    gen.setDisplayFlag(True)
    gen.setRenderFlag(True)
    try:
        gen.cook(force=True)
    except Exception as exc:
        print(f"[{name}] cook raised: {exc}")
        print(f"[{name}] SOP errors: {gen.errors()}")
        raise
    errs = gen.errors()
    if errs:
        print(f"[{name}] GEN errors: {errs}")
    g = gen.geometry()
    npts = len(g.points()) if g else 0
    nprims = len(g.prims()) if g else 0
    print(f"[{name}] points: {npts} prims: {nprims}")
    rop = sop.createNode("rop_geometry")
    rop.setInput(0, gen)
    rop.parm("sopoutput").set(str(OUT / f"{name}.obj").replace("\\", "/"))
    rop.parm("trange").set(0)
    rop.parm("execute").pressButton()
    ok = (OUT / f"{name}.obj").exists()
    print(f"[{name}] ROP errors: {rop.errors()} written={ok}")
    return {"obj": f"{name}.obj", "written": ok, "points": npts, "prims": nprims, "errors": errs}

results = {
    "FS_Crown_v2": build_and_export("FS_Crown_v2", CROWN_SCRIPT),
    "FS_Wings_v2": build_and_export("FS_Wings_v2", WING_SCRIPT),
}

hou.hipFile.clear(suppress_save_prompt=True)
(OUT / "flowerspring_crown_wings_v2_manifest.json").write_text(json.dumps({
    "schema": "melodia.flowerspring_crown_wings.v2",
    "seed": SEED,
    "units": "meters (dress-native; head center (0,-0.02,1.52), wing anchors behind shoulder blades)",
    "pieces": {
        "FS_Crown_v2": {"band": "lathed rounded tube R=0.105m", "petals": 12,
                         "petal_build": "closed parametric shell: curl + cup + twist, 2mm stock",
                         "gems": 7, "gem_build": "faceted brilliant in bezel",
                         "uv": "per-petal planar + band lathe"},
        "FS_Wings_v2": {"wings": 4, "fore_span_m": 0.36, "hind_span_m": 0.24,
                         "membrane": "polar grid, smooth cosine scallops (no triangle teeth)",
                         "veins_per_wing": 6, "vein_build": "tapered strips",
                         "rim": "9 smooth cups per wing",
                         "anchor": "behind shoulder blades, y=+0.16 (back)"},
    },
    "fixes_vs_v1": ["dress-meter units (no 0.0065 scale hack)",
                     "closed shells instead of flat single-sided quads",
                     "smooth scallop edge instead of sawtooth triangles",
                     "wings anchored on the back, not the waist",
                     "crown sized to head, not floating at collar"],
    "results": results,
    "houdini": hou.applicationVersionString(),
}, indent=1), encoding="utf-8")
print("CROWN_WINGS_V2_DONE " + json.dumps({k: v["written"] for k, v in results.items()}))
