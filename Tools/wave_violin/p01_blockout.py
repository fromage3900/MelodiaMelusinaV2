# -*- coding: utf-8 -*-
"""p01 — blockout: readable Night Reel silhouette from primitives. Idempotent."""
import bpy, json, math, os
from mathutils import Vector, Matrix

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
COLL = "ME_WaveViolin_Assemblies"
log = lambda m: print(f"[vr-p01] {m}", flush=True)

def link_to(ob, cname=COLL):
    for c in list(ob.users_collection): c.objects.unlink(ob)
    bpy.data.collections[cname].objects.link(ob)

def cube(name, size, loc, scale=(1,1,1)):
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    ob = bpy.context.active_object; ob.name = name; ob.scale = scale
    link_to(ob); return ob

def cyl(name, r, depth, loc, rot=(0,0,0), verts=24):
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    ob = bpy.context.active_object; ob.name = name
    link_to(ob); return ob

def sph(name, r, loc, seg=16):
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg//2)
    ob = bpy.context.active_object; ob.name = name; link_to(ob)
    bpy.ops.object.shade_smooth()
    return ob

# --- body: hourglass from 3 cylinders + waist (blockout; p02 refines curves) ---
body_up = cyl("ME_WaveViolin_UpperBout", 0.10, 0.055, (0, 0, 0.22), (math.radians(90),0,0))
body_lo = cyl("ME_WaveViolin_LowerBout", 0.115, 0.055, (0, 0, -0.16), (math.radians(90),0,0))
waist   = cube("ME_WaveViolin_Waist", 1, (0,0,0.03), (0.075, 0.028, 0.18))
for b in (body_up, body_lo, waist):
    m = b.modifiers.new("ME_Bevel","BEVEL"); m.width = 0.006; m.segments = 2

# belly plate (cymatics target later)
belly = cube("ME_WaveViolin_BellyPlate", 1, (0, -0.030, 0.02), (0.105, 0.004, 0.40))
mb = belly.modifiers.new("ME_Bevel","BEVEL"); mb.width = 0.01; mb.segments = 3

# neck / fingerboard
cube("ME_WaveViolin_Neck", 1, (0, 0.01, 0.42), (0.022, 0.012, 0.24))
fb = cube("ME_WaveViolin_Fingerboard", 1, (0, -0.005, 0.46), (0.024, 0.012, 0.26))
# scroll pommel: torus spiral proxy
old = bpy.data.objects.get("ME_WaveViolin_Scroll")
if old: bpy.data.objects.remove(old, do_unlink=True)
bpy.ops.mesh.primitive_torus_add(major_radius=0.035, minor_radius=0.011, location=(0, 0.012, 0.60),
                                 rotation=(math.radians(90),0,0), major_segments=24, minor_segments=10)
scr = bpy.context.active_object; scr.name = "ME_WaveViolin_Scroll"; link_to(scr)
bpy.ops.object.shade_smooth()

# bridge hub + tailpiece
sph("ME_WaveViolin_BridgeHub", 0.030, (0, -0.028, 0.05))
cube("ME_WaveViolin_Tailpiece", 1, (0, -0.005, -0.42), (0.020, 0.010, 0.09))
# f-hole vents (thin dark slots; p02 reworks as curves)
for s in (-1, 1):
    cube(f"ME_WaveViolin_FHole_{'L' if s<0 else 'R'}", 1, (s*0.055, -0.033, -0.02), (0.006, 0.003, 0.10))

# strings x4 (thin cylinders along fingerboard; emissive lane p04)
for i, x in enumerate((-0.014, -0.005, 0.004, 0.013)):
    st = cyl(f"ME_WaveViolin_String_{i+1}", 0.0012, 0.86, (x, -0.020, 0.24), (math.radians(90),0,0), verts=6)
    for c in list(st.users_collection): c.objects.unlink(st)
    bpy.data.collections["ME_WaveViolin_Strings"].objects.link(st)

# pegs (pearl)
for i, y in enumerate((0.55, 0.60)):
    for s in (-1, 1):
        cyl(f"ME_WaveViolin_Peg_{'L' if s<0 else 'R'}{i}", 0.006, 0.045, (s*0.032, y-0.11+0.11, 0.0), (0, math.radians(90), 0))

tri = 0
for o in bpy.data.objects:
    if o.type == "MESH":
        ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = ev.to_mesh(); tri += sum(len(p.vertices)-2 for p in me.polygons); ev.to_mesh_clear()

scn = bpy.context.scene
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
scn.render.filepath = os.path.join(OUT, "p01_blockout.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_mainfile()
rep = {"phase":"p01","ok":True,"objects":len(bpy.data.objects),"tris":tri,"plate":scn.render.filepath}
json.dump(rep, open(os.path.join(OUT,"p01_report.json"),"w"), indent=1)
log(f"done tris={tri}")
