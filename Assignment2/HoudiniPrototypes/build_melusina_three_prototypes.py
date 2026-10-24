"""spike: true
Headless Houdini sketch set for three Melusina cathedral systems.

Creates one inspectable HIP with three independent, parameterized SOP graphs:
  1) resonant Gothic tracery (Chladni-mode ornament, static architecture)
  2) gravity-ordered fountain cascade (baked presentation geometry)
  3) walkable silk bridge (static deck/collision candidate plus wind-shaped veil)

These are review prototypes, not production HDAs or UE-ready assets. Coordinates
are metres, Z-up. No production Content/ or shared editor state is touched.
Run with Houdini 22 Hython from the BS_GodFile project root.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import hou


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
HIP_PATH = OUT / "Melusina_Three_Houdini_Prototypes.hip"
MANIFEST_PATH = OUT / "prototype_manifest.json"
SCHEMA = "melodia.houdini_three_prototypes.spike.v1"


COMMON = r'''import math
import hou

geo = hou.pwd().geometry()
name_attrib = geo.addAttrib(hou.attribType.Prim, "name", "")

def v_add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def v_sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def v_mul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def v_dot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def v_cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def v_norm(a):
    d = math.sqrt(v_dot(a, a))
    return (a[0]/d, a[1]/d, a[2]/d) if d > 1e-10 else (1.0, 0.0, 0.0)

def point(co):
    p = geo.createPoint()
    p.setPosition(hou.Vector3(co))
    return p

def face(coords, role):
    prim = geo.createPolygon()
    for co in coords:
        prim.addVertex(point(co))
    prim.setAttribValue(name_attrib, role)
    return prim

def box(center, size, role):
    x, y, z = center
    sx, sy, sz = (size[0]*0.5, size[1]*0.5, size[2]*0.5)
    p = [
        (x-sx,y-sy,z-sz),(x+sx,y-sy,z-sz),(x+sx,y+sy,z-sz),(x-sx,y+sy,z-sz),
        (x-sx,y-sy,z+sz),(x+sx,y-sy,z+sz),(x+sx,y+sy,z+sz),(x-sx,y+sy,z+sz),
    ]
    for ids in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
        face([p[i] for i in ids], role)

def tube(path, radius, role, sides=8, closed=False):
    if len(path) < 2: return
    rings = []
    for i, center in enumerate(path):
        before = path[i-1] if i > 0 else path[i]
        after = path[(i+1) % len(path)] if (closed or i+1 < len(path)) else path[i]
        tangent = v_norm(v_sub(after, before))
        ref = (0.0, 0.0, 1.0) if abs(v_dot(tangent, (0.0,0.0,1.0))) < 0.88 else (0.0,1.0,0.0)
        u = v_norm(v_cross(tangent, ref))
        v = v_norm(v_cross(tangent, u))
        ring = []
        for j in range(sides):
            a = 2.0*math.pi*j/sides
            ring.append(point(v_add(center, v_mul(v_add(v_mul(u, math.cos(a)), v_mul(v, math.sin(a))), radius))))
        rings.append(ring)
    n = len(rings) if closed else len(rings)-1
    for i in range(n):
        nxt = (i+1) % len(rings)
        for j in range(sides):
            k = (j+1) % sides
            prim = geo.createPolygon()
            for p in (rings[i][j], rings[i][k], rings[nxt][k], rings[nxt][j]):
                prim.addVertex(p)
            prim.setAttribValue(name_attrib, role)
    if not closed:
        for ring, reverse in ((rings[0], True), (rings[-1], False)):
            prim = geo.createPolygon()
            order = list(reversed(ring)) if reverse else ring
            for p in order: prim.addVertex(p)
            prim.setAttribValue(name_attrib, role)

def grid_surface(point_fn, u_steps, v_steps, role):
    for i in range(u_steps):
        u0, u1 = i/u_steps, (i+1)/u_steps
        for j in range(v_steps):
            v0, v1 = j/v_steps, (j+1)/v_steps
            face([point_fn(u0,v0), point_fn(u1,v0), point_fn(u1,v1), point_fn(u0,v1)], role)

def disc(center, radius, z, role, segments=48):
    c = (center[0], center[1], z)
    for i in range(segments):
        a0 = 2.0*math.pi*i/segments
        a1 = 2.0*math.pi*(i+1)/segments
        face([c, (center[0]+radius*math.cos(a0),center[1]+radius*math.sin(a0),z),
                 (center[0]+radius*math.cos(a1),center[1]+radius*math.sin(a1),z)], role)

def ring_surface(center, profile, role, segments=48):
    rings = []
    for radius, height in profile:
        r = max(0.025, radius)
        rings.append([point((center[0]+r*math.cos(2.0*math.pi*j/segments),
                             center[1]+r*math.sin(2.0*math.pi*j/segments),
                             center[2]+height)) for j in range(segments)])
    for i in range(len(rings)-1):
        for j in range(segments):
            k = (j+1) % segments
            prim = geo.createPolygon()
            for p in (rings[i][j],rings[i][k],rings[i+1][k],rings[i+1][j]): prim.addVertex(p)
            prim.setAttribValue(name_attrib, role)

def sphere_mesh(center, radius, role, latitudes=16, longitudes=32):
    rings=[]
    for i in range(latitudes+1):
        phi=math.pi*i/latitudes
        ring=[]
        for j in range(longitudes):
            theta=2.0*math.pi*j/longitudes
            ring.append(point((center[0]+radius*math.sin(phi)*math.cos(theta),
                               center[1]+radius*math.sin(phi)*math.sin(theta),
                               center[2]+radius*math.cos(phi))))
        rings.append(ring)
    for i in range(latitudes):
        for j in range(longitudes):
            k=(j+1)%longitudes
            prim=geo.createPolygon()
            for p in (rings[i][j],rings[i][k],rings[i+1][k],rings[i+1][j]): prim.addVertex(p)
            prim.setAttribValue(name_attrib,role)

def ribbon_path(path, width, role, center=None):
    for i in range(len(path)-1):
        a,b=path[i],path[i+1]
        tangent=v_norm(v_sub(b,a))
        mid=v_mul(v_add(a,b),0.5)
        reference=(0.0,1.0,0.0) if center is None else v_norm(v_sub(mid,center))
        side=v_norm(v_cross(tangent,reference))
        half=v_mul(side,width*0.5)
        face([v_add(a,half),v_add(b,half),v_sub(b,half),v_sub(a,half)],role)
'''


TRACERY = r'''
width = hou.pwd().parm("window_width").eval()
height = hou.pwd().parm("window_height").eval()
m = int(hou.pwd().parm("mode_m").eval())
n = int(hou.pwd().parm("mode_n").eval())
frame = hou.pwd().parm("frame_radius").eval()
half = width*0.5
spring = height*0.62
rise = height-spring

def arch_x(z, inset=0.0):
    w = max(0.0, half-inset)
    if z <= spring: return w
    q = max(0.0, min(1.0, (z-spring)/max(0.001,rise)))
    return w*math.sqrt(max(0.0,1.0-q*q))

outline = [(-half,0.0,0.0),(-half,0.0,spring)]
for i in range(1,33):
    a = math.pi*0.5*i/32
    outline.append((-half*math.cos(a),0.0,spring+rise*math.sin(a)))
for i in range(1,33):
    a = math.pi*0.5*(32-i)/32
    outline.append((half*math.cos(a),0.0,spring+rise*math.sin(a)))
outline.append((half,0.0,0.0))
outline.append((-half,0.0,0.0))
tube(outline, frame, "stone_frame", 12)

inner = []
inset = frame*2.2
inner.append((-half+inset,0.0,0.15))
inner.append((-half+inset,0.0,spring))
for i in range(1,29):
    a = math.pi*0.5*i/28
    inner.append((-(half-inset)*math.cos(a),0.0,spring+(rise-inset)*math.sin(a)))
for i in range(1,29):
    a = math.pi*0.5*(28-i)/28
    inner.append(((half-inset)*math.cos(a),0.0,spring+(rise-inset)*math.sin(a)))
inner.extend([(half-inset,0.0,0.15),(-half+inset,0.0,0.15)])
tube(inner, frame*0.68, "gold_came", 8)

# Thin glass panels stay inside the pointed arch. Separate role tags make later
# material assignment explicit without baking any material dependency here.
def glass_point(u,v):
    x = -half + width*u
    z = 0.15 + (height-0.3)*v
    return (x,0.045,z)
for i in range(40):
    for j in range(64):
        u0,u1=i/40,(i+1)/40
        v0,v1=j/64,(j+1)/64
        xm=-half+width*(u0+u1)*0.5
        zm=0.15+(height-0.3)*(v0+v1)*0.5
        if abs(xm) <= arch_x(zm, frame*2.0):
            face([glass_point(u0,v0),glass_point(u1,v0),glass_point(u1,v1),glass_point(u0,v1)],"opal_glass")

# Pointed lancets and the central medallion are structural, while the mode
# contour is an authored static mesh intended for a UE material/beat response.
for x in (-width*0.28, 0.0, width*0.28):
    top = spring + rise*math.sqrt(max(0.0,1.0-(abs(x)/half)**2))
    tube([(x,0.0,0.18),(x,0.0,min(spring,top-0.3)),
          (x*0.72,0.0,top-0.2),(x*0.35,0.0,top-0.05),(0.0,0.0,top)], frame*0.54,"stone_mullion",8)

nx,nz=72,112
xs=[-half+i*width/nx for i in range(nx+1)]
zs=[0.15+j*(height-0.3)/nz for j in range(nz+1)]
def field(x,z):
    xx=(x+half)/width
    zz=(z-0.15)/(height-0.3)
    return math.sin(m*math.pi*xx)*math.cos(n*math.pi*zz)-math.cos(n*math.pi*xx)*math.sin(m*math.pi*zz)
def add_mode_segment(a,b):
    dx=b[0]-a[0]; dz=b[1]-a[1]
    length=max(1e-8,math.sqrt(dx*dx+dz*dz))
    px=-dz/length*0.022; pz=dx/length*0.022
    face([(a[0]+px,0.018,a[1]+pz),(b[0]+px,0.018,b[1]+pz),
          (b[0]-px,0.018,b[1]-pz),(a[0]-px,0.018,a[1]-pz)],"cymatic_lead")
for i in range(nx):
    for j in range(nz):
        corners=[(xs[i],zs[j]),(xs[i+1],zs[j]),(xs[i+1],zs[j+1]),(xs[i],zs[j+1])]
        vals=[field(*p) for p in corners]
        crossings=[]
        for e0,e1 in ((0,1),(1,2),(2,3),(3,0)):
            a,b=vals[e0],vals[e1]
            if (a<0.0 and b>=0.0) or (a>=0.0 and b<0.0):
                t=a/(a-b)
                crossings.append((corners[e0][0]+t*(corners[e1][0]-corners[e0][0]),
                                  corners[e0][1]+t*(corners[e1][1]-corners[e0][1])))
        pairs=[]
        if len(crossings)==2: pairs=[(crossings[0],crossings[1])]
        elif len(crossings)==4: pairs=[(crossings[0],crossings[1]),(crossings[2],crossings[3])]
        for a,b in pairs:
            zm=(a[1]+b[1])*0.5; xm=(a[0]+b[0])*0.5
            if abs(xm)<=arch_x(zm,frame*1.5): add_mode_segment(a,b)

# Layer six Lissajous ribbons into the upper rose. The integer frequency pairs
# give each strand a distinct woven cadence while mode_m/mode_n still drive the
# separate Chladni nodal lead network.
lissajous_count=int(hou.pwd().parm("lissajous_count").eval())
lissajous_pairs=[(1,2),(2,3),(3,2),(2,5),(5,2),(3,4),(4,3),(4,5)]
rx=width*0.19; rz=rise*0.23; zc=spring+rise*0.51
for index,(a,b) in enumerate(lissajous_pairs[:lissajous_count]):
    phase=index*0.37
    path=[]
    for j in range(193):
        t=2.0*math.pi*j/192
        x=rx*math.sin(a*t+phase)
        z=zc+rz*math.sin(b*t)
        path.append((x,-0.055-index*0.004,z))
    ribbon_path(path,0.052,"lissajous_ribbon")
    tube([(x,y-0.018,z) for x,y,z in path],0.016,"lissajous_filament",6)
'''


FOUNTAIN = r'''
count = int(hou.pwd().parm("basin_count").eval())
drop = hou.pwd().parm("stage_drop").eval()
water_width = hou.pwd().parm("water_width").eval()
ripple = hou.pwd().parm("ripple_amp").eval()
ribbon_count = int(hou.pwd().parm("flow_ribbon_count").eval())
spacing=7.2
profile=[(0.12,0.08),(1.35,0.08),(1.8,0.28),(2.15,1.15),(2.38,1.55),
         (2.22,1.62),(1.92,1.12),(1.45,0.38),(0.12,0.30)]
levels=[]
for i in range(count):
    y=i*spacing
    z=-i*drop
    center=(0.0,y,z)
    ring_surface(center,profile,"carved_basin",56)
    disc((0.0,y),1.5,z+0.52,"receiving_pool",48)
    levels.append(z+1.62)
    # Fluted buttress ribs tie each bowl into a central pier.
    for k in range(12):
        a=2.0*math.pi*k/12
        x=1.92*math.cos(a); yy=y+1.92*math.sin(a)
        tube([(x,yy,z+0.22),(x*1.06, y+(yy-y)*1.06,z+0.92),(x*1.12,y+(yy-y)*1.12,z+1.42)],0.075,"fluted_support",7)

# A crown spout feeds an upper bowl through a short fan of arcing streams.
top=(0.0,0.0,levels[0])
for k in range(10):
    a=2.0*math.pi*k/10
    path=[]
    for j in range(25):
        t=j/24
        r=0.3+1.34*t
        z=top[2]+1.6*math.sin(math.pi*t)-0.24*t
        path.append((r*math.cos(a),r*math.sin(a),z))
    tube(path,0.055,"fountain_jet",6)

# Each waterfall is a static, rippled sheet with a provable descending route.
# The sheet is intentionally art-directed; the manifest labels where a future
# UE water material/Niagara presentation may animate it.
for i in range(count-1):
    y0=i*spacing+2.25
    z0=levels[i]-0.08
    z1=levels[i+1]+0.25
    fall=z0-z1
    if fall<=0.0: raise hou.NodeError("Water path must descend into each receiver")
    y1=(i+1)*spacing-0.75
    def sheet(u,v,y0=y0,y1=y1,z0=z0,fall=fall,i=i):
        x=(u-0.5)*water_width
        z=z0-fall*v
        y=y0+(y1-y0)*v + ripple*math.sin(6.0*math.pi*u+1.7*v+i)*math.sin(math.pi*v)
        return (x,y,z)
    grid_surface(sheet,20,42,"falling_water_sheet")
    # Narrow Lissajous stream-ribbons ride the falling sheet as luminous
    # filaments; the larger sheet itself stays static and gives UE a stable base.
    ratios=[(2,3),(3,4),(4,5),(5,6),(6,7),(7,5),(5,7),(7,6)]
    for strand,(fa,fb) in enumerate(ratios[:ribbon_count]):
        phase=strand*0.83+i*0.47
        path=[]
        for j in range(193):
            u=j/192
            envelope=math.sin(math.pi*u)
            x=(strand-(ribbon_count-1)*0.5)*water_width*0.13 + water_width*0.11*math.sin(2.0*math.pi*fa*u+phase)*envelope
            y=y0+(y1-y0)*u
            z=z0-fall*u + 0.16*math.sin(2.0*math.pi*fb*u+phase)*envelope
            path.append((x,y,z))
        ribbon_path(path,0.115,"lissajous_flow_ribbon")
        tube(path,0.03,"lissajous_flow_filament",6)
    # Carved side rails keep the water course visibly attached to stone.
    for side in (-1,1):
        tube([(side*water_width*0.56,y0,z0-0.12),
              (side*water_width*0.56,y0+0.8,z0-fall*0.42),
              (side*water_width*0.56,y1,z1-0.12)],0.11,"spillway_coping",8)

if any(levels[i+1] >= levels[i] for i in range(len(levels)-1)):
    raise hou.NodeError("Hydraulic elevations are not monotonically descending")
'''


BRIDGE = r'''
span=hou.pwd().parm("span").eval()
deck_width=hou.pwd().parm("deck_width").eval()
rise=hou.pwd().parm("arch_rise").eval()
wind=hou.pwd().parm("wind_amplitude").eval()
base=4.0

def profile(u):
    return base+rise*4.0*u*(1.0-u)
def local_width(u):
    return deck_width+2.6*math.exp(-((u-0.5)/0.105)**2)

# Broad continuous deck, flared into a central listening/turning court.
def deck(u,v):
    x=span*u
    y=(v-0.5)*local_width(u)
    z=profile(u)
    return (x,y,z)
grid_surface(deck,64,10,"walkable_deck")

# Separate underside slab and the two stone ribs make the walkable route legible.
def underside(u,v):
    x=span*u
    y=(v-0.5)*local_width(u)
    z=profile(u)-0.34
    return (x,y,z)
grid_surface(underside,64,6,"deck_underside")
for side in (-1,1):
    path=[]
    arch=[]
    for i in range(65):
        u=i/64
        y=side*(local_width(u)*0.5+0.12)
        path.append((span*u,y,profile(u)+0.05))
        arch.append((span*u,y,1.0+3.5*4.0*u*(1.0-u)))
    tube(path,0.11,"gold_guardrail",10)
    tube(arch,0.22,"stone_support_arch",12)
    for i in range(17):
        u=i/16
        y=side*(local_width(u)*0.5+0.12)
        z=profile(u)+0.58
        box((span*u,y,z),(0.22,0.22,1.0),"tracery_post")

# Three constrained silk veils span between anchor towers. The still image is
# baked geometry; a future Vellum study can replace the analytic rest shape.
for layer in range(3):
    offset=(layer-1)*1.4
    def veil(u,v,layer=layer,offset=offset):
        x=span*u
        y=(v-0.5)*(deck_width+4.4)+offset
        sag=2.0*math.sin(math.pi*u)
        gust=wind*math.sin(5.0*math.pi*u+layer*1.3)*math.sin(math.pi*v)
        z=13.0-sag+gust-layer*0.72
        return (x,y,z)
    for i in range(72):
        u0,u1=i/72,(i+1)/72
        for j in range(6):
            v0,v1=j/6,(j+1)/6
            # Keep an oculus over the listening court so the suspended focal
            # orb reads through the veil instead of being buried under cloth.
            opening_u=(u0+u1)*0.5-0.5
            opening_v=(v0+v1)*0.5-(0.5-offset/(deck_width+4.4))
            if (opening_u/0.17)**2+(opening_v/0.42)**2 < 1.0:
                continue
            face([veil(u0,v0),veil(u1,v0),veil(u1,v1),veil(u0,v1)],"aeolian_silk_veil")
    for side in (-1,1):
        line=[]
        for i in range(65):
            u=i/64
            y=side*(deck_width*0.5+2.3)+offset
            line.append((span*u,y,13.0-2.0*math.sin(math.pi*u)-layer*0.72))
        tube(line,0.045,"silk_edge_cord",7)

# The midpoint ring and inlaid radial lines declare the view/interaction focus.
cx=span*0.5; cz=profile(0.5)+0.08
focus=[(cx+3.2*math.cos(2.0*math.pi*i/96),3.2*math.sin(2.0*math.pi*i/96),cz) for i in range(97)]
tube(focus,0.085,"listening_court_ring",10,closed=True)
for k in range(16):
    a=2.0*math.pi*k/16
    tube([(cx+2.6*math.cos(a),2.6*math.sin(a),cz+0.035),
          (cx+3.2*math.cos(a),3.2*math.sin(a),cz+0.035)],0.025,"court_inlay",6)

# Suspended harmonic orb gives the expanded deck a clear focal destination
# while remaining above the traversable floor envelope.
orb_center=(cx,0.0,8.25)
tube([(cx,0.0,9.58),(cx,0.0,8.82)],0.055,"orb_suspension",8)
sphere_mesh(orb_center,0.82,"resonance_orb",20,40)
halo_xy=[(cx+1.22*math.cos(2.0*math.pi*i/96),1.22*math.sin(2.0*math.pi*i/96),orb_center[2]) for i in range(97)]
halo_xz=[(cx+1.22*math.cos(2.0*math.pi*i/96),0.0,orb_center[2]+1.22*math.sin(2.0*math.pi*i/96)) for i in range(97)]
tube(halo_xy,0.045,"orb_halo",8,closed=True)
tube(halo_xz,0.045,"orb_halo",8,closed=True)

# A woven Lissajous cage turns the orb into a readable musical focal point.
# Each parameterized strand uses a distinct integer frequency pair and phase;
# the broad ribbon catches light while its slim center filament preserves form.
orbit_count=int(hou.pwd().parm("orbital_ribbon_count").eval())
orbit_modes=[(1,2,1),(2,3,2),(3,2,1),(2,5,3),(5,2,4),(3,4,2),(4,3,5),(4,5,3)]
for index,(fa,fb,fc) in enumerate(orbit_modes[:orbit_count]):
    phase=index*0.41
    rx=1.55+0.12*index
    ry=1.28+0.10*index
    rz=0.44+0.06*(index%3)
    path=[]
    for j in range(257):
        t=2.0*math.pi*j/256
        x=cx+rx*math.sin(fa*t+phase)
        y=ry*math.sin(fb*t+phase*0.73)
        z=orb_center[2]+rz*math.sin(fc*t+phase*1.37)
        path.append((x,y,z))
    ribbon_path(path,0.09,"lissajous_orbit_ribbon",orb_center)
    tube(path,0.026,"lissajous_orbit_filament",6,closed=True)

# Endpoint gate towers are the bridge's connection sockets for modular assembly.
for x in (0.0,span):
    for side in (-1,1):
        y=side*(deck_width*0.5+2.45)
        box((x,y,8.5),(1.25,1.25,9.0),"bridge_gate_pier")
        cap=[(x+0.88*math.cos(2.0*math.pi*i/32),y+0.88*math.sin(2.0*math.pi*i/32),13.3) for i in range(33)]
        tube(cap,0.13,"pier_crown",8,closed=True)
'''


PROTOTYPES = [
    {
        "name": "01_ResonantTracery",
        "label": "01 - Resonant Tracery",
        "kind": "tracery",
        "code": TRACERY,
        "params": [
            hou.FloatParmTemplate("window_width", "Window Width (m)", 1, default_value=(6.0,)),
            hou.FloatParmTemplate("window_height", "Window Height (m)", 1, default_value=(10.0,)),
            hou.IntParmTemplate("mode_m", "Chladni Mode M", 1, default_value=(5,)),
            hou.IntParmTemplate("mode_n", "Chladni Mode N", 1, default_value=(3,)),
            hou.IntParmTemplate("lissajous_count", "Lissajous Ribbon Count", 1, default_value=(8,), min=2, max=8),
            hou.FloatParmTemplate("frame_radius", "Frame Radius (m)", 1, default_value=(0.12,)),
        ],
        "drive": ("mode_m", 6),
        "proof": "static lancet/rose tracery with eight frequency-paired Lissajous ribbons and a driven Chladni contour; no geometry motion at runtime",
    },
    {
        "name": "02_GravityFountainCascade",
        "label": "02 - Gravity Fountain Cascade",
        "kind": "fountain",
        "code": FOUNTAIN,
        "params": [
            hou.IntParmTemplate("basin_count", "Basin Count", 1, default_value=(3,), min=2, max=4),
            hou.FloatParmTemplate("stage_drop", "Drop per Stage (m)", 1, default_value=(2.6,), min=0.5, max=6.0),
            hou.FloatParmTemplate("water_width", "Water Sheet Width (m)", 1, default_value=(2.4,), min=0.5, max=5.0),
            hou.FloatParmTemplate("ripple_amp", "Art-directed Ripple (m)", 1, default_value=(0.08,), min=0.0, max=0.4),
            hou.IntParmTemplate("flow_ribbon_count", "Lissajous Flow Ribbon Count", 1, default_value=(8,), min=2, max=8),
        ],
        "drive": ("stage_drop", 3.1),
        "proof": "tiered carved basins, spout jets, descending sheets and eight Lissajous ribbons per spill; sheets are static presentation geometry",
    },
    {
        "name": "03_AeolianSilkBridge",
        "label": "03 - Aeolian Silk Bridge",
        "kind": "bridge",
        "code": BRIDGE,
        "params": [
            hou.FloatParmTemplate("span", "Bridge Span (m)", 1, default_value=(28.0,), min=10.0, max=60.0),
            hou.FloatParmTemplate("deck_width", "Walkable Width (m)", 1, default_value=(3.8,), min=2.0, max=8.0),
            hou.FloatParmTemplate("arch_rise", "Deck Crown Rise (m)", 1, default_value=(1.4,), min=0.0, max=4.0),
            hou.FloatParmTemplate("wind_amplitude", "Baked Veil Gust (m)", 1, default_value=(0.35,), min=0.0, max=1.0),
            hou.IntParmTemplate("orbital_ribbon_count", "Orbital Lissajous Ribbons", 1, default_value=(8,), min=3, max=8),
        ],
        "drive": ("wind_amplitude", 0.58),
        "proof": "static walkable deck, three wind-shaped veils, central oculus, suspended focus and seven frequency-paired Lissajous orbit ribbons; Vellum remains a later bake comparison",
    },
]


def add_parameters(node, templates):
    group = node.parmTemplateGroup()
    for template in templates:
        group.append(template)
    node.setParmTemplateGroup(group)


def geometry_signature(geometry):
    digest = hashlib.sha256()
    points = geometry.points()
    for point in points:
        p = point.position()
        digest.update(struct.pack("!I3d", point.number(), round(p[0], 6), round(p[1], 6), round(p[2], 6)))
    bounds = [round(float(v), 4) for v in geometry.boundingBox().sizevec()]
    roles = {}
    name = geometry.findPrimAttrib("name")
    if name:
        for prim in geometry.prims():
            role = prim.attribValue(name)
            roles[role] = roles.get(role, 0) + 1
    return {
        "points": len(points),
        "primitives": len(geometry.prims()),
        "bbox_size_m": bounds,
        "position_sha256_16": digest.hexdigest()[:16],
        "primitive_roles": roles,
    }


def write_obj(geometry, path):
    points = geometry.points()
    prims = geometry.prims()
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# spike: true | Melusina three-system Houdini prototype | metres Z-up\n")
        for point in points:
            p = point.position()
            handle.write(f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")
        name = geometry.findPrimAttrib("name")
        previous = None
        for prim in prims:
            role = prim.attribValue(name) if name else "prototype"
            if role != previous:
                handle.write(f"g {role}\n")
                previous = role
            ids = [vertex.point().number()+1 for vertex in prim.vertices()]
            if len(ids) >= 3:
                handle.write("f " + " ".join(str(i) for i in ids) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    obj = hou.node("/obj")
    for node in list(obj.children()):
        if node.name().startswith("PROTO_"):
            node.destroy()

    records = []
    for index, spec in enumerate(PROTOTYPES):
        container = obj.createNode("geo", "PROTO_" + spec["name"])
        container.setComment("spike: true | " + spec["proof"])
        container.setUserData("spike", "true")
        container.setPosition(hou.Vector2(index*600, 0))
        for child in list(container.children()):
            child.destroy()
        python = container.createNode("python", "build_" + spec["kind"])
        add_parameters(python, spec["params"])
        python.parm("python").set(COMMON + "\n" + spec["code"])
        out = container.createNode("null", "OUT_" + spec["kind"].upper())
        out.setInput(0, python)
        out.setDisplayFlag(True)
        out.setRenderFlag(True)
        python.setPosition(hou.Vector2(0, 0))
        out.setPosition(hou.Vector2(200, 0))
        out.setColor(hou.Color((0.24, 0.50, 0.70)))
        out.setUserData("spike", "true")

        python.cook(force=True)
        out.cook(force=True)
        base = geometry_signature(out.geometry())
        errors = list(python.errors()) + list(out.errors())
        if errors:
            raise RuntimeError(f"{spec['name']} default cook errors: {errors}")
        if base["points"] < 100 or base["primitives"] < 50:
            raise RuntimeError(f"{spec['name']} produced too little geometry: {base}")

        parm_name, driven_value = spec["drive"]
        parm = python.parm(parm_name)
        default_value = parm.eval()
        parm.set(driven_value)
        python.cook(force=True)
        out.cook(force=True)
        driven = geometry_signature(out.geometry())
        if driven["position_sha256_16"] == base["position_sha256_16"]:
            raise RuntimeError(f"{spec['name']} control {parm_name} did not move geometry")
        parm.set(default_value)
        python.cook(force=True)
        out.cook(force=True)
        restored = geometry_signature(out.geometry())
        if restored["position_sha256_16"] != base["position_sha256_16"]:
            raise RuntimeError(f"{spec['name']} did not restore its pinned default geometry")
        write_obj(out.geometry(), OUT / f"{spec['name']}.obj")
        records.append({
            "id": spec["name"],
            "spike": True,
            "concept": spec["proof"],
            "network": f"/obj/{container.name()}",
            "output": f"{out.path()}",
            "default": base,
            "driven_parameter": {"name": parm_name, "tested_value": driven_value, "geometry": driven},
            "restored_default_hash_matches": restored["position_sha256_16"] == base["position_sha256_16"],
            "errors": errors,
            "obj": str((OUT / f"{spec['name']}.obj").resolve()),
        })

    hou.hipFile.save(str(HIP_PATH))

    # Reopen the saved artifact in the same headless session and force each
    # authored graph to cook again. This is a persistence check, not a UE gate.
    hou.hipFile.load(str(HIP_PATH), suppress_save_prompt=True)
    for record in records:
        container = hou.node(record["network"])
        if container is None:
            raise RuntimeError(f"Saved HIP is missing {record['network']}")
        python = next((child for child in container.children() if child.type().name() == "python"), None)
        output = hou.node(record["output"])
        if python is None or output is None:
            raise RuntimeError(f"Saved HIP graph is incomplete: {record['id']}")
        python.cook(force=True)
        output.cook(force=True)
        errors = list(python.errors()) + list(output.errors())
        reopened = geometry_signature(output.geometry())
        if errors:
            raise RuntimeError(f"{record['id']} reopen recook errors: {errors}")
        if reopened["position_sha256_16"] != record["default"]["position_sha256_16"]:
            raise RuntimeError(f"{record['id']} saved default changed after reopen")
        record["saved_hip_reopen_recook"] = {
            "passed": True,
            "points": reopened["points"],
            "primitives": reopened["primitives"],
            "position_sha256_16": reopened["position_sha256_16"],
            "errors": errors,
        }
    report = {
        "schema": SCHEMA,
        "spike": True,
        "engine": f"Houdini {hou.applicationVersionString()}",
        "license_category": hou.licenseCategory().name(),
        "units": "metres",
        "axis": "Z-up",
        "outputs": records,
        "hip": str(HIP_PATH.resolve()),
        "limitations": [
            "Offline Hython SOP prototypes only; no Houdini Engine or UE import/cook/PIE proof.",
            "Fountain sheets and silk veils are baked static presentation meshes, not runtime solvers.",
            "No collision, UV, material, capsule-clearance, performance, or full route acceptance yet.",
        ],
    }
    MANIFEST_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"overall":"PASS","hip":str(HIP_PATH),"license":report["license_category"],
                      "prototypes":[{"id":r["id"],"points":r["default"]["points"],
                      "primitives":r["default"]["primitives"],
                                     "driver":r["driven_parameter"]["name"],
                                     "restored":r["restored_default_hash_matches"],
                                     "reopen_recook":r["saved_hip_reopen_recook"]["passed"]} for r in records]}, indent=2))


if __name__ == "__main__":
    main()
