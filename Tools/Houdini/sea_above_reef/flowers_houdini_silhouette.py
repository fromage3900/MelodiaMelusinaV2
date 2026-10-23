#!/usr/bin/env hython
"""Cos_FlowerSpring — Houdini silhouette pass: radial rotating crown + fairy flower wings.

Generates deterministic geometry (SEED 20260831) via Python SOPs in hython:

  FS_Crown  — radial crown: 14 petal blades around a band, each petal carries
              p@rotPhase (0..1) for UE WPO rotation driving, warm-spring Cd ramp
              (gold -> peach), 7 diadem gems (pearl octahedra).
  FS_Wings  — 4 fairy wings (2 fore, 2 hind mirrored): membrane fans with
              alpha-gradient Cd (blush -> pearl), 5 vein tubes per wing,
              9 small flower petals along the outer edge per wing,
              p@wingPhase for flutter driving.

Outputs (Saved/Audit/melusina_lookdev/flowers_outfit/):
  FS_Crown.fbx/.obj, FS_Wings.fbx/.obj, flowers_houdini_manifest.json

Run: hython Tools/Houdini/sea_above_reef/flowers_houdini_silhouette.py
"""
import json
import math
from pathlib import Path

import hou

PROJECT = Path("C:/EnvironmentPortfolio/BS_GodFile")
OUT = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "flowers_outfit"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260831

# warm-spring palette (contrast to shorewake seafoam/teal)
GOLD = (0.91, 0.72, 0.29)
PEACH = (1.00, 0.70, 0.48)
BLUSH = (0.95, 0.63, 0.66)
PEARL = (1.00, 0.96, 0.90)
SPRING = (0.66, 0.85, 0.42)

CROWN_SCRIPT = r'''
import hou, math, random
geo = hou.pwd().geometry()
rng = random.Random(20260831)

geo.addAttrib(hou.attribType.Point, "Cd", (0.0, 0.0, 0.0))
geo.addAttrib(hou.attribType.Point, "rotPhase", 0.0)
geo.addAttrib(hou.attribType.Point, "petalU", 0.0)
geo.addAttrib(hou.attribType.Point, "petalV", 0.0)

def poly(*pts):
    f = geo.createPolygon(); f.setIsClosed(True)
    for p in pts: f.addVertex(p)
    return f

GOLD=(0.91,0.72,0.29); PEACH=(1.0,0.70,0.48); PEARL=(1.0,0.96,0.90)
N_PETALS=14; R_BAND=17.0; TUBE=1.6; PET_L=9.0; PET_W=4.5; TILT=math.radians(25)

def lerp(a,b,t): return a+(b-a)*t
def mixc(c1,c2,t): return tuple(lerp(c1[i],c2[i],t) for i in range(3))

# --- band: torus-ellipse ring of quads (Z-up, worn on head) ------------------
SEGS=64
band_pts=[]
for i in range(SEGS):
    a=2*math.pi*i/SEGS
    band_pts.append(geo.createPoint())
    p=band_pts[-1]
    p.setPosition(hou.Vector3(R_BAND*math.cos(a), R_BAND*math.sin(a), 0.0))
    p.setAttribValue("Cd", GOLD)
for i in range(SEGS):
    a0=2*math.pi*i/SEGS; a1=2*math.pi*((i+1)%SEGS)/SEGS
    # two rings (inner/outer) as flat band
    p0=geo.createPoint(); p0.setPosition(hou.Vector3((R_BAND-TUBE)*math.cos(a0),(R_BAND-TUBE)*math.sin(a0),0.0)); p0.setAttribValue("Cd",GOLD)
    p1=geo.createPoint(); p1.setPosition(hou.Vector3((R_BAND+TUBE)*math.cos(a0),(R_BAND+TUBE)*math.sin(a0),0.0)); p1.setAttribValue("Cd",mixc(GOLD,PEACH,0.4))
    p2=geo.createPoint(); p2.setPosition(hou.Vector3((R_BAND+TUBE)*math.cos(a1),(R_BAND+TUBE)*math.sin(a1),0.0)); p2.setAttribValue("Cd",mixc(GOLD,PEACH,0.4))
    p3=geo.createPoint(); p3.setPosition(hou.Vector3((R_BAND-TUBE)*math.cos(a1),(R_BAND-TUBE)*math.sin(a1),0.0)); p3.setAttribValue("Cd",GOLD)
    poly(p0,p1,p2,p3)

# --- radial petals, each with rotPhase for UE WPO rotation -------------------
for k in range(N_PETALS):
    a=2*math.pi*k/N_PETALS
    phase=k/N_PETALS
    col=mixc(GOLD,PEACH,k%2)
    # petal: 6x4 grid, curved up, tilted outward, cupped
    rows,cols=6,4
    grid=[[None]*cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            u=r/(rows-1); v=c/(cols-1)
            rad=R_BAND+TUBE+u*PET_L
            ang=a+(v-0.5)*(PET_W/rad)
            z=math.sin(u*math.pi*0.9)*3.2 - u*u*1.2   # curve up then tip back
            p=geo.createPoint()
            p.setPosition(hou.Vector3(rad*math.cos(ang), rad*math.sin(ang), z))
            p.setAttribValue("Cd", mixc(col, PEARL, u*u))
            p.setAttribValue("rotPhase", phase)
            p.setAttribValue("petalU", u)
            p.setAttribValue("petalV", v)
            grid[r][c]=p
    for r in range(rows-1):
        for c in range(cols-1):
            poly(grid[r][c],grid[r][c+1],grid[r+1][c+1],grid[r+1][c])

# --- diadem gems: 7 pearl octahedra on band top ------------------------------
for k in range(7):
    a=2*math.pi*k/7
    cx,cy=(R_BAND)*math.cos(a),(R_BAND)*math.sin(a)
    s=0.9
    verts=[]
    for dx,dy,dz in [(0,0,s),(0,0,-s),(s,0,0),(-s,0,0),(0,s,0),(0,-s,0)]:
        p=geo.createPoint(); p.setPosition(hou.Vector3(cx+dx,cy+dy,dz+0.6))
        p.setAttribValue("Cd",PEARL); verts.append(p)
    for tri in [(0,2,4),(0,4,3),(0,3,5),(0,5,2),(1,4,2),(1,3,4),(1,5,3),(1,2,5)]:
        f=geo.createPolygon(); f.setIsClosed(True)
        for vi in tri: f.addVertex(verts[vi])
'''

WING_SCRIPT = r'''
import hou, math, random
geo = hou.pwd().geometry()
rng = random.Random(20260831)

geo.addAttrib(hou.attribType.Point, "Cd", (0.0, 0.0, 0.0))
geo.addAttrib(hou.attribType.Point, "wingPhase", 0.0)
geo.addAttrib(hou.attribType.Point, "edgeU", 0.0)

def poly(*pts):
    f = geo.createPolygon(); f.setIsClosed(True)
    for p in pts: f.addVertex(p)
    return f

BLUSH=(0.95,0.63,0.66); PEARL=(1.0,0.96,0.90); GOLD=(0.91,0.72,0.29); SPRING=(0.66,0.85,0.42)
def lerp(a,b,t): return a+(b-a)*t
def mixc(c1,c2,t): return tuple(lerp(c1[i],c2[i],t) for i in range(3))

def wing(sign, fore, origin):
    span=34.0 if fore else 22.0
    width=15.0 if fore else 10.0
    phase=(0.0 if fore else 0.5)+(0.0 if sign>0 else 0.25)
    # outline: petal-wing superellipse r(t)
    T=48
    outline=[]
    for i in range(T):
        t=i/(T-1)
        ang=math.pi*t  # half-circle sweep
        r=span*(0.35+0.65*math.sin(ang*0.5))*(1.0-0.25*t)
        x=math.cos(ang)*r*sign
        y=math.sin(ang)*r*0.45
        outline.append((origin[0]+x, origin[1]+y, origin[2]+(1.5 if fore else 0.8)))
    # membrane: fan triangles from root to outline ring with Cd gradient
    root=geo.createPoint(); root.setPosition(hou.Vector3(*origin))
    root.setAttribValue("Cd",mixc(BLUSH,PEARL,0.2)); root.setAttribValue("wingPhase",phase)
    ring=[]
    for (x,y,z) in outline:
        p=geo.createPoint(); p.setPosition(hou.Vector3(x,y,z))
        p.setAttribValue("Cd",mixc(BLUSH,PEARL,0.85))
        p.setAttribValue("wingPhase",phase)
        p.setAttribValue("edgeU",1.0)
        ring.append(p)
    for i in range(len(ring)-1):
        f=geo.createPolygon(); f.setIsClosed(False)
        f.addVertex(root); f.addVertex(ring[i]); f.addVertex(ring[i+1])
    # membrane fill: quad strips between rows
    ROWS=6
    rows_pts=[]
    for row in range(ROWS+1):
        u=row/ROWS
        rowpts=[]
        for i,(rp) in enumerate(ring):
            rp_pos=rp.position()
            pos=hou.Vector3(origin[0]*(1-u)+rp_pos[0]*u, origin[1]*(1-u)+rp_pos[1]*u, origin[2]*(1-u)+rp_pos[2]*u)
            pos+=hou.Vector3(0,0,math.sin(u*math.pi)*0.8)
            q=geo.createPoint(); q.setPosition(pos)
            q.setAttribValue("Cd",mixc(BLUSH,PEARL,u)); q.setAttribValue("wingPhase",phase)
            rowpts.append(q)
        rows_pts.append(rowpts)
    for row in range(ROWS):
        for i in range(len(ring)-1):
            a0=rows_pts[row][i]; a1=rows_pts[row][i+1]
            b1=rows_pts[row+1][i+1]; b0=rows_pts[row+1][i]
            f=geo.createPolygon(); poly(a0,a1,b1,b0)
    # veins: 5 radial tubes per wing
    for k in range(5):
        idx=int((k+0.5)/5*(len(ring)-1))
        tip=ring[idx].position()
        mid=hou.Vector3(origin)*0.5+tip*0.5
        p0=geo.createPoint(); p0.setPosition(hou.Vector3(origin[0],origin[1],origin[2]+0.15))
        p1=geo.createPoint(); p1.setPosition(hou.Vector3(mid[0],mid[1],mid[2]+0.25))
        p2=geo.createPoint(); p2.setPosition(hou.Vector3(tip[0],tip[1],tip[2]+0.2))
        p0.setAttribValue("Cd",GOLD); p1.setAttribValue("Cd",mixc(GOLD,SPRING,0.5)); p2.setAttribValue("Cd",SPRING)
        f=geo.createPolygon(); f.setIsClosed(False)
        f.addVertex(p0); f.addVertex(p1); f.addVertex(p2)
    # flower petals along outer edge (outer 40%)
    PET=9
    for k in range(PET):
        t=0.6+0.4*k/(PET-1)
        idx=int(t*(len(ring)-1))
        bp=ring[idx].position()
        s=1.1 if fore else 0.8
        col=mixc(GOLD,BLUSH,k%2)
        verts=[]
        for dx,dy in [(0,0),(s,s*1.8),(-s,s*1.8)]:
            p=geo.createPoint()
            p.setPosition(hou.Vector3(bp[0]+dx*sign,bp[1]+dy,bp[2]+0.5))
            p.setAttribValue("Cd",col); p.setAttribValue("wingPhase",phase)
            verts.append(p)
        f=geo.createPolygon(); poly(verts[0],verts[1],verts[2])

wing(+1, True,  (1.2, -3.0, 8.0))    # fore R
wing(-1, True,  (-1.2, -3.0, 8.0))   # fore L
wing(+1, False, (1.0, -1.5, 5.5))    # hind R
wing(-1, False, (-1.0, -1.5, 5.5))   # hind L
'''


def build_network(name, script, origin):
    obj = hou.node("/obj")
    sop = obj.createNode("geo", name)
    sop.moveToGoodPosition()
    py = sop.createNode("python", "GEN")
    py.parm("python").set(script.strip())
    py.setDisplayFlag(True)
    py.setRenderFlag(True)
    # transform to cm (character scale)
    xform = sop.createNode("xform", "to_cm")
    xform.parm("scale").set(1.0)
    xform.setInput(0, py)
    xform.setDisplayFlag(True)
    xform.setRenderFlag(True)
    return sop, xform


outputs = {}
for name, script in (("FS_Crown", CROWN_SCRIPT), ("FS_Wings", WING_SCRIPT)):
    sop, disp = build_network(name, script, OUT)
    # cook the generator first, then export
    gen = sop.node("GEN")
    try:
        gen.cook(force=True)
    except Exception as exc:
        print("[dbg]", name, "cook raised:", exc)
    print("[dbg]", name, "GEN errors:", gen.errors())
    g = gen.geometry()
    print("[dbg]", name, "pts:", len(g.points()) if g else "NO GEOMETRY")
    rop = sop.createNode("rop_geometry")
    rop.setInput(0, disp)
    rop.parm("sopoutput").set(str(OUT / f"{name}.obj").replace("\\", "/"))
    rop.parm("trange").set(0)
    rop.parm("execute").pressButton()
    print("[dbg]", name, "ROP errors:", rop.errors())
    outputs[name + ".obj"] = (OUT / f"{name}.obj").exists()

hou.hipFile.clear(suppress_save_prompt=True)
(OUT / "flowers_houdini_manifest.json").write_text(json.dumps({
    "schema": "melodia.flowerspring_houdini.v1",
    "seed": SEED,
    "pieces": {
        "FS_Crown": {"petals": 14, "band_radius_cm": 17.0, "gems": 7,
                     "rotation_driver": "p@rotPhase 0..1 for UE WPO spin"},
        "FS_Wings": {"wings": 4, "fore_span_cm": 34.0, "hind_span_cm": 22.0,
                     "veins_per_wing": 5, "edge_petals_per_wing": 9,
                     "flutter_driver": "p@wingPhase"},
    },
    "palette": {"gold": GOLD, "peach": PEACH, "blush": BLUSH, "pearl": PEARL, "spring": SPRING},
    "outputs": outputs,
    "houdini": hou.applicationVersionString(),
}, indent=1), encoding="utf-8")
print("HOUDINI_DONE " + json.dumps(outputs))
