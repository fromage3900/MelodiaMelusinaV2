"""
Surreal Islands — Blender mesh builder (companion to surreal_islands.py).

Builds 3 impossible-terrain island meshes then exports blend/FBX/PNG beauty.

  1) Inverted Pyramid Isle  40m — upside-down pyramid (top 40x40, apex 2m, drop 14m)
     Top is walkable plateau; 4 waterfall curtains fall from each edge (translucent)
  2) Ribbon Atoll          60m — thin loop torus (R=30m, width 5m, thick 1.6m)
     Waviness via lobe sine; gap inside navigable (~50m)
  3) Tiered Cloud Terrace  35m — 3 stacked discs (R14/10/6 @ y=18/26/34, 35m span in scene)
     Two arched bridges connect discs; soft cloud puffs underneath (ico spheres)

Scale: metres (UE import 1m = 100cm). Origin at world center; islands spread 70-90m apart.
Run:  blender --background --python Tools/Houdini/sea_above_reef/surreal_islands_blender.py
"""

import json
import math
import hashlib
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Matrix

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved/Audit/surreal_sweep/islands"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 20260828
SCHEMA = "melodia.surreal_islands.v1"

# palette — surreal SeaAbove dusk
WORLD = (0.025, 0.032, 0.055, 1.0)
KEY = (1.0, 0.92, 0.74)
FILL = (0.45, 0.78, 0.92)
RIM = (0.78, 0.88, 1.0)

def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.images):
        for item in list(block):
            if item.users == 0:
                try:
                    block.remove(item)
                except Exception:
                    pass

def new_material(name, color, roughness=0.65, metallic=0.0, alpha=1.0, emissive=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        try:
            bsdf.inputs["Roughness"].default_value = roughness
        except: pass
        try:
            bsdf.inputs["Metallic"].default_value = metallic
        except: pass
        if alpha < 1.0:
            try:
                bsdf.inputs["Alpha"].default_value = alpha
            except: pass
            mat.blend_method = 'BLEND'
        if emissive is not None and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emissive, 1.0)
            try:
                bsdf.inputs["Emission Strength"].default_value = 0.9
            except: pass
    return mat

def link_object(obj):
    try:
        bpy.context.collection.objects.link(obj)
    except Exception:
        try:
            bpy.context.scene.collection.objects.link(obj)
        except Exception:
            pass
    return obj

# ---------- ISLAND 1: Inverted Pyramid + Waterfalls ----------
def build_pyramid():
    """Inverted pyramid: top 40m square at y=22, apex at y=8 (14m drop)."""
    TOP = 20.0  # half 40
    APEX_HALF = 1.0
    Y_TOP = 22.0
    Y_APEX = 8.0
    verts = [
        Vector((-TOP, Y_TOP, -TOP)),
        Vector(( TOP, Y_TOP, -TOP)),
        Vector(( TOP, Y_TOP,  TOP)),
        Vector((-TOP, Y_TOP,  TOP)),
        Vector((-APEX_HALF, Y_APEX, -APEX_HALF)),
        Vector(( APEX_HALF, Y_APEX, -APEX_HALF)),
        Vector(( APEX_HALF, Y_APEX,  APEX_HALF)),
        Vector((-APEX_HALF, Y_APEX,  APEX_HALF)),
    ]
    faces = [
        (0,1,2,3),      # top plateau (walkable)
        (0,1,5,4),      # side -Z
        (1,2,6,5),      # side +X
        (2,3,7,6),      # side +Z
        (3,0,4,7),      # side -X
        (4,5,6,7),      # bottom tip cap
    ]
    mesh = bpy.data.meshes.new("SM_Surreal_InvertedPyramid_Mesh")
    # add subtle rock displacement to vertices (deterministic wobble)
    import random
    rng = random.Random(SEED + 11)
    for i in [0,1,2,3]:
        verts[i] += Vector((rng.uniform(-0.6,0.6), 0, rng.uniform(-0.6,0.6)))
    for i in [4,5,6,7]:
        verts[i] += Vector((rng.uniform(-0.25,0.25), rng.uniform(-0.4,0.4), rng.uniform(-0.25,0.25)))
    mesh.from_pydata([tuple(v) for v in verts], [], faces)
    mesh.update()
    # UVs: project from world
    obj = bpy.data.objects.new("SM_Surreal_InvertedPyramid", mesh)
    link_object(obj)
    # smooth + triangulate guard
    for p in mesh.polygons:
        p.use_smooth = True
    # solidify slightly via bevel modifier for nicer silhouette
    mod = obj.modifiers.new("Bevel", type='BEVEL')
    mod.width = 0.18
    mod.segments = 2
    # material
    rock = new_material("M_Surreal_PyramidRock", (0.62, 0.56, 0.52), roughness=0.82)
    mesh.materials.append(rock)
    # edge wear vertex color (bpy >= 4)
    try:
        col = mesh.color_attributes.new(name="Col", type='BYTE_COLOR', domain='POINT')
        for i, v in enumerate(mesh.vertices):
            # darker on lower apex
            t = max(0, (Y_TOP - v.co.y) / (Y_TOP - Y_APEX))
            c = 0.62 - 0.12*t
            col.data[i].color = (c, c*0.92, c*0.88, 1.0)
    except Exception:
        pass

    # waterfalls: 4 curtains falling from each top edge, thin translucent planes with waviness
    wf_mat = new_material("M_Surreal_Waterfall", (0.52, 0.78, 0.92), roughness=0.15, alpha=0.42, emissive=(0.18, 0.45, 0.78))
    # make waterfall slightly transparent via blend
    try:
        wf_mat.blend_method = 'BLEND'
        wf_mat.shadow_method = 'HASHED'
    except: pass
    waterfall_objs = []
    edges = [(0,1),(1,2),(2,3),(3,0)]
    FALL = 13.0
    for ei, (a,b) in enumerate(edges):
        va = verts[a]; vb = verts[b]
        mid = (va + vb) / 2
        # curtain mesh: quad strip down with waviness
        segs_h = 8  # vertical
        segs_w = 6  # along edge
        # build grid
        grid_verts = []; grid_faces = []
        edge_dir = (vb - va).normalized()
        edge_len = (vb - va).length
        for j in range(segs_h+1):
            tj = j / segs_h
            y = Y_TOP - tj * FALL
            # curtain flares outward slightly then straightens
            flare = math.sin(tj * math.pi) * 0.9
            # outward normal per edge
            if ei == 0: n = Vector((0,0,-1))
            elif ei == 1: n = Vector((1,0,0))
            elif ei == 2: n = Vector((0,0,1))
            else: n = Vector((-1,0,0))
            for i2 in range(segs_w+1):
                ti = i2 / segs_w
                p = va + edge_dir * (ti * edge_len)
                # wave along edge
                wave = 0.18*math.sin(ti*math.pi*3 + tj*2.3) + 0.12*math.sin(tj*5 + ei*1.1)
                pos = Vector((p.x + n.x*flare + wave*n.x*0.5, y, p.z + n.z*flare + wave*n.z*0.5))
                # jitter curtain not at top
                if j>0:
                    pos += Vector((rng.uniform(-0.08,0.08), 0, rng.uniform(-0.08,0.08)))
                grid_verts.append(pos)
        # faces
        for j in range(segs_h):
            for i2 in range(segs_w):
                a_ = j*(segs_w+1)+i2
                b_ = j*(segs_w+1)+i2+1
                c_ = (j+1)*(segs_w+1)+i2+1
                d_ = (j+1)*(segs_w+1)+i2
                grid_faces.append((a_, b_, c_, d_))
        wf_mesh = bpy.data.meshes.new(f"SM_Surreal_Waterfall_{ei}_Mesh")
        wf_mesh.from_pydata([tuple(v) for v in grid_verts], [], grid_faces)
        wf_mesh.update()
        for p in wf_mesh.polygons:
            p.use_smooth = True
        o = bpy.data.objects.new(f"SM_Surreal_Waterfall_{ei}", wf_mesh)
        wf_mesh.materials.append(wf_mat)
        link_object(o)
        waterfall_objs.append(o)

    # parent waterfalls to pyramid for FBX convenience (keep transform)
    for w in waterfall_objs:
        w.parent = obj

    obj.location = Vector((-70, 0, 0))
    for w in waterfall_objs:
        # waterfalls are children, so they inherit; adjust: they were built in world, now need local
        # simpler: clear parent then move waterfalls same offset
        w.parent = None
        w.location += Vector((-70, 0, 0))
    return obj, waterfall_objs


# ---------- ISLAND 2: Ribbon Atoll (60m loop) ----------
def build_ribbon():
    R = 30.0       # loop radius (60m diameter)
    WIDTH = 5.0    # ribbon width
    THICK = 1.55
    SEG = 64
    # slightly elliptical + wavy
    verts = []
    faces = []
    # cross-section: 4 verts per segment (bottom inner/outer, top inner/outer)
    # But we will make a swept rectangle tube (closed loop) with 4 verts per ring
    rings = []
    import random
    rng = random.Random(SEED + 22)
    for s in range(SEG):
        th = s / SEG * 2 * math.pi
        # lobed radius + random wobble
        r_var = R + 1.1*math.sin(3*th) + 0.6*math.sin(7*th + 0.8) + rng.uniform(-0.4, 0.4)
        y_var = 0.35*math.sin(2*th + 1.1)  # gentle undulation in height
        cx = r_var * math.cos(th)
        cz = r_var * math.sin(th)
        cy = 16.0 + y_var
        # frame: tangent around loop
        # tangent = derivative of circle (+ lobe) approx
        # radial direction outward
        rad = Vector((math.cos(th), 0, math.sin(th)))
        tan = Vector((-math.sin(th), 0, math.cos(th)))
        # cross // tan x up
        # build rectangle: inner/outer along rad, bottom/top along Y
        half_w = WIDTH/2
        # four corners in ring order
        p0 = Vector((cx - rad.x*half_w, cy - THICK/2, cz - rad.z*half_w))
        p1 = Vector((cx + rad.x*half_w, cy - THICK/2, cz + rad.z*half_w))
        p2 = Vector((cx + rad.x*half_w, cy + THICK/2, cz + rad.z*half_w))
        p3 = Vector((cx - rad.x*half_w, cy + THICK/2, cz - rad.z*half_w))
        rings.append((p0,p1,p2,p3))
    # faces: connect rings
    all_verts = []
    for ring in rings:
        for p in ring:
            all_verts.append(p)
    # build faces: each quad between rings for each side
    mesh_faces = []
    for s in range(SEG):
        ns = (s+1)%SEG
        base = s*4; nbase = ns*4
        # bottom (0-1)
        mesh_faces.append((base+0, nbase+0, nbase+1, base+1))
        # outer wall (1-2)
        mesh_faces.append((base+1, nbase+1, nbase+2, base+2))
        # top (2-3) — top is the walkable ribbon
        mesh_faces.append((base+2, nbase+2, nbase+3, base+3))
        # inner wall (3-0)
        mesh_faces.append((base+3, nbase+3, nbase+0, base+0))
    mesh = bpy.data.meshes.new("SM_Surreal_RibbonAtoll_Mesh")
    mesh.from_pydata([tuple(v) for v in all_verts], [], mesh_faces)
    mesh.update()
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new("SM_Surreal_RibbonAtoll", mesh)
    link_object(obj)
    # bevel for soft edges
    mod = obj.modifiers.new("Bevel", type='BEVEL')
    mod.width = 0.12
    mod.segments = 2
    # materials: top sand, sides rock
    sand = new_material("M_Surreal_RibbonSand", (0.78, 0.74, 0.62), roughness=0.88)
    rock = new_material("M_Surreal_RibbonRock", (0.55, 0.53, 0.50), roughness=0.82)
    mesh.materials.append(sand)
    mesh.materials.append(rock)
    # assign top faces to slot 0, sides/bottom to 1
    # top faces are every 3rd (index 2 of each set of 4)
    for i, poly in enumerate(mesh.polygons):
        # i %4 ==2 => top
        poly.material_index = 0 if (i % 4 == 2) else 1
    # position: east of center
    obj.location = Vector((35, 0, 38))
    # add mooring bollard / arch hint (small torus at one point for sail-through landmark)
    bpy.ops.mesh.primitive_torus_add(major_radius=2.2, minor_radius=0.22, major_segments=20, minor_segments=10,
                                     location=(obj.location + Vector((R+1.2, 2.0, 0))))
    arch = bpy.context.object
    arch.name = "SM_Surreal_RibbonArch"
    am = new_material("M_Surreal_Arch", (0.72, 0.66, 0.58), roughness=0.6)
    arch.data.materials.append(am)
    return obj

# ---------- ISLAND 3: Tiered Cloud Terrace (35m stacked discs + bridges) ----------
def disc_mesh(radius, thickness, seg=48):
    verts = []
    faces = []
    # two caps + side
    # bottom center + rim, top center + rim
    yb = -thickness/2; yt = thickness/2
    # centers
    verts.append(Vector((0, yb, 0)))  # 0 bottom center
    verts.append(Vector((0, yt, 0)))  # 1 top center
    # rims
    for i in range(seg):
        th = i/seg*2*math.pi
        x = radius*math.cos(th); z = radius*math.sin(th)
        verts.append(Vector((x, yb, z)))  # 2..2+seg-1 bottom rim
    for i in range(seg):
        th = i/seg*2*math.pi
        x = radius*math.cos(th); z = radius*math.sin(th)
        verts.append(Vector((x, yt, z)))  # 2+seg .. 2+2seg-1 top rim
    off_b = 2; off_t = 2+seg
    # bottom cap
    for i in range(seg):
        a = 0; b = off_b + i; c = off_b + (i+1)%seg
        faces.append((a,c,b))
    # top cap
    for i in range(seg):
        a = 1; b = off_t + i; c = off_t + (i+1)%seg
        faces.append((a,b,c))
    # side quads
    for i in range(seg):
        b0 = off_b + i; b1 = off_b + (i+1)%seg
        t0 = off_t + i; t1 = off_t + (i+1)%seg
        faces.append((b0,b1,t1,t0))
    return verts, faces

def build_terrace():
    discs = [
        {"r": 14.0, "y": 18.0, "thick": 1.8, "name": "T1_Base"},
        {"r": 10.0, "y": 26.5, "thick": 1.5, "name": "T2_Mid"},
        {"r": 6.5, "y": 34.5, "thick": 1.2, "name": "T3_Top"},
    ]
    disc_objs = []
    stone = new_material("M_Surreal_TerraceStone", (0.66, 0.64, 0.60), roughness=0.78)
    grass = new_material("M_Surreal_TerraceGrass", (0.42, 0.58, 0.38), roughness=0.92)
    for d in discs:
        verts, faces = disc_mesh(d["r"], d["thick"], seg=48)
        # add bevel noise to rim verts for organic edge
        import random
        rng = random.Random(SEED + 33)
        for v in verts[2:]:
            if abs(v.y) > 0.1:  # rim verts
                v.x += rng.uniform(-0.18, 0.18)
                v.z += rng.uniform(-0.18, 0.18)
        mesh = bpy.data.meshes.new(f"SM_Surreal_Terrace_{d['name']}_Mesh")
        mesh.from_pydata([tuple(v) for v in verts], [], faces)
        mesh.update()
        for p in mesh.polygons:
            p.use_smooth = True
        obj = bpy.data.objects.new(f"SM_Surreal_Terrace_{d['name']}", mesh)
        obj.location = Vector((0, d["y"], 0))
        # materials: top cap grass, rest stone
        mesh.materials.append(grass)
        mesh.materials.append(stone)
        # top cap faces are indices  seg .. 2*seg-1 (after bottom cap)
        seg = 48
        for i, poly in enumerate(mesh.polygons):
            # 0..seg-1 bottom, seg..2seg-1 top, rest side
            if seg <= i < 2*seg:
                poly.material_index = 0
            else:
                poly.material_index = 1
        link_object(obj)
        # bevel
        mod = obj.modifiers.new("Bevel", type='BEVEL')
        mod.width = 0.14
        mod.segments = 2
        disc_objs.append(obj)

    # bridges: arched boxes between discs
    bridges = []
    bridge_mat = new_material("M_Surreal_BridgeWood", (0.52, 0.38, 0.28), roughness=0.75)
    # bridge 1: base -> mid (offset to +X side)
    # Create via bmesh arched bridge
    def make_bridge(p0, p1, width=2.4, arch_h=1.2, name="Bridge"):
        mid = (p0 + p1)/2
        mid.y += arch_h
        # 3-point bezier
        segs = 14
        pts = []
        for i in range(segs+1):
            t = i/segs
            # quadratic bezier
            inv = 1-t
            pos = inv*inv*p0 + 2*inv*t*mid + t*t*p1
            pts.append(pos)
        # sweep width
        verts = []; faces=[]
        half_w = width/2
        for pt in pts:
            # perpendicular in XZ (bridge runs roughly along X or diagonal)
            # use horizontal direction
            # approximate perp as (-dz, dx) normalized in xz
            # we can just use Z as perp for simplicity (bridges along X)
            verts.append(pt + Vector((0,0,-half_w)))
            verts.append(pt + Vector((0,0, half_w)))
            # lower edge (thickness)
            verts.append(pt + Vector((0,-0.28,-half_w)))
            verts.append(pt + Vector((0,-0.28, half_w)))
        # faces: top strip + sides + bottom
        n = len(pts)
        for i in range(n-1):
            b = i*4
            nb = (i+1)*4
            # top
            faces.append((b+0, nb+0, nb+1, b+1))
            # bottom
            faces.append((b+2, b+3, nb+3, nb+2))
            # outer side
            faces.append((b+0, b+2, nb+2, nb+0))
            faces.append((b+1, nb+1, nb+3, b+3))
        mesh = bpy.data.meshes.new(f"SM_Surreal_{name}_Mesh")
        mesh.from_pydata([tuple(v) for v in verts], [], faces)
        mesh.update()
        for p in mesh.polygons:
            p.use_smooth = True
        obj = bpy.data.objects.new(f"SM_Surreal_{name}", mesh)
        mesh.materials.append(bridge_mat)
        link_object(obj)
        return obj

    b1 = make_bridge(Vector((10.5, 18.0, 0)), Vector((7.0, 26.5, 0)), width=2.6, arch_h=1.8, name="Bridge_BaseMid")
    b2 = make_bridge(Vector((-6.0, 26.5, 0)), Vector((-4.2, 34.5, 0)), width=2.0, arch_h=1.4, name="Bridge_MidTop")
    # rotate slightly for variety: b2 is left side so fine
    bridges = [b1, b2]

    # cloud puffs under each disc (icospheres, translucent)
    cloud_mat = new_material("M_Surreal_Cloud", (0.92, 0.94, 0.98), roughness=1.0, alpha=0.55)
    try:
        cloud_mat.blend_method = 'BLEND'
    except: pass
    import random
    rng = random.Random(SEED + 44)
    for d in discs:
        for k in range(3):
            ang = rng.uniform(0, 2*math.pi)
            rad = rng.uniform(0.2, 0.62) * d["r"]
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rng.uniform(1.2, 2.4),
                location=(Vector((rad*math.cos(ang), d["y"] - d["thick"]/2 - rng.uniform(0.6,1.8), rad*math.sin(ang)))))
            puff = bpy.context.object
            puff.name = f"SM_Surreal_Cloud_{d['name']}_{k}"
            puff.data.materials.append(cloud_mat)
            disc_objs.append(puff)

    # group position: west-south
    offset = Vector((68, 0, -32))
    for o in disc_objs + bridges:
        o.location += offset

    # return a parent empty for FBX grouping convenience
    bpy.ops.object.empty_add(location=offset)
    empty = bpy.context.object
    empty.name = "SM_Surreal_CloudTerrace_ROOT"
    for o in disc_objs + bridges:
        # keep world pos, set parent
        o.parent = empty
    # clear parent to keep transforms baked for FBX (we will join later for export, so keep)
    for o in disc_objs + bridges:
        o.parent = None
    bpy.data.objects.remove(empty)

    # combine top-level objects for return (use first disc as nominal)
    return disc_objs[0]

def setup_world():
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = WORLD
        bg.inputs[1].default_value = 1.0

def rig_and_render(center, diag, out_path, samples=128, size=1024):
    # lights
    def light(name, loc, color, energy, size_=2.0):
        data = bpy.data.lights.new(name, type="AREA")
        data.energy = energy
        data.color = color
        data.size = size_
        ob = bpy.data.objects.new(name, data)
        ob.location = loc
        link_object(ob)
        return ob
    d = max(diag, 1.0)
    light("Key", center + Vector((1.0,-1.1,1.0)).normalized()*d*1.05, KEY, 1400*d*d, 2.0*d)
    light("Fill", center + Vector((-1.2,-0.6,0.4)).normalized()*d*1.2, FILL, 600*d*d, 2.4*d)
    light("Rim", center + Vector((0.1,1.0,0.9)).normalized()*d*1.1, RIM, 800*d*d, 1.8*d)
    # camera
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 52
    cam_data.clip_start = 0.1
    cam_data.clip_end = 8000
    cam = bpy.data.objects.new("Cam", cam_data)
    dist = d*1.55 + 6
    direction = Vector((0.9,-1.15,0.55)).normalized()
    cam.location = center + direction * dist
    link_object(cam)
    target = bpy.data.objects.new("Target", None)
    target.location = center
    link_object(target)
    c = cam.constraints.new(type="TRACK_TO")
    c.target = target
    c.track_axis = 'TRACK_NEGATIVE_Z'
    c.up_axis = 'UP_Y'
    bpy.context.scene.camera = cam
    # render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.film_transparent = False
    scene.render.filepath = str(out_path)
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    setup_world()
    bpy.ops.render.render(write_still=True)
    # cleanup lights/cam for FBX cleanliness (keep meshes)
    for name in ("Key","Fill","Rim","Cam","Target"):
        ob = bpy.data.objects.get(name)
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)

def export_fbx(objects, path: Path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0] if objects else None
    # FBX export: metres, apply transform, mesh only
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
                             object_types={'MESH'}, use_mesh_modifiers=True, mesh_smooth_type='FACE',
                             axis_forward='-Z', axis_up='Y')
    print(f"[blender] FBX -> {path.name} ({path.stat().st_size} bytes)")

def main():
    clear_scene()
    print("[blender] building surreal islands...")

    pyramid, waterfalls = build_pyramid()
    ribbon = build_ribbon()
    terrace_root = build_terrace()

    # collect all mesh objects for blend stats
    all_mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
    print(f"[blender] mesh objects: {[o.name for o in all_mesh_objs]}")
    for o in all_mesh_objs:
        # apply modifiers visually for stats
        bpy.context.view_layer.update()

    # bounds
    def bbox_center_diag(objs):
        lo = Vector((1e9,1e9,1e9)); hi = Vector((-1e9,-1e9,-1e9))
        for ob in objs:
            if ob.type != 'MESH':
                continue
            for corner in ob.bound_box:
                w = ob.matrix_world @ Vector(corner)
                lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
        return (lo+hi)/2, (hi-lo).length

    center, diag = bbox_center_diag(all_mesh_objs)
    print(f"[blender] scene center {tuple(round(v,2) for v in center)} diag {diag:.2f}")

    # save blend
    blend_path = OUT_DIR / "Surreal_Islands.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"[blender] blend -> {blend_path.name} ({blend_path.stat().st_size} bytes)")

    # FBX exports: per island (group by proximity/name)
    pyramid_objs = [o for o in all_mesh_objs if "Pyramid" in o.name or "Waterfall" in o.name]
    ribbon_objs = [o for o in all_mesh_objs if "Ribbon" in o.name]
    terrace_objs = [o for o in all_mesh_objs if "Terrace" in o.name or "Bridge" in o.name or "Cloud" in o.name]

    export_fbx(pyramid_objs, OUT_DIR / "SM_Surreal_InvertedPyramid.fbx")
    export_fbx(ribbon_objs, OUT_DIR / "SM_Surreal_RibbonAtoll.fbx")
    export_fbx(terrace_objs, OUT_DIR / "SM_Surreal_CloudTerrace.fbx")

    # beauty render
    beauty_path = OUT_DIR / "Surreal_Islands_Beauty.png"
    rig_and_render(center, diag, beauty_path, samples=96, size=1024)
    print(f"[blender] beauty -> {beauty_path.name} ({beauty_path.stat().st_size} bytes)")

    # write islands_manifest.json (merge with masks fragment if present)
    frag_path = OUT_DIR / "_masks_manifest.json"
    masks_data = {}
    if frag_path.exists():
        masks_data = json.loads(frag_path.read_text(encoding="utf-8"))
    # mesh stats
    def mesh_stats(objs):
        verts = sum(len(o.data.vertices) for o in objs) if objs else 0
        polys = sum(len(o.data.polygons) for o in objs) if objs else 0
        return {"objects": len(objs), "vertices": verts, "polygons": polys,
                "names": [o.name for o in objs]}

    files = []
    for p in sorted(OUT_DIR.glob("*.*")):
        if p.name.startswith("_"):
            continue
        if p.suffix.lower() in (".png", ".fbx", ".blend", ".json"):
            if p.name == "islands_manifest.json":
                continue
            files.append({"name": p.stem, "path": f"Saved/Audit/surreal_sweep/islands/{p.name}",
                          "bytes": p.stat().st_size, "sha256": sha256_of(p)})

    manifest = {
        "schema": SCHEMA,
        "seed": SEED,
        "blender": bpy.app.version_string,
        " Houdini_heightfields_COP_masks": masks_data.get("houdini", {"note": "see surreal_islands.py"}),
        "masks": masks_data.get("masks", []),
        "islands": [
            {"id": "inverted_pyramid_isle", "name": "Inverted Pyramid Isle",
             "world_size": "40m top plateau, 14m drop, apex 2m",
             "floating_height": "22m top / 8m apex (14m cliff + waterfalls)",
             "special": "4 waterfall curtains off edges, translucency + waviness",
             "fbx": "Saved/Audit/surreal_sweep/islands/SM_Surreal_InvertedPyramid.fbx",
             "stats": mesh_stats(pyramid_objs)},
            {"id": "ribbon_atoll", "name": "Ribbon Atoll",
             "world_size": "60m loop diameter (R=30m), ribbon width 5m, thick 1.6m",
             "floating_height": "16m center, navigable interior ~50m",
             "special": "thin loop you can sail inside; 3-lobe warp + arch landmark",
             "fbx": "Saved/Audit/surreal_sweep/islands/SM_Surreal_RibbonAtoll.fbx",
             "stats": mesh_stats(ribbon_objs)},
            {"id": "tiered_cloud_terrace", "name": "Tiered Cloud Terrace",
             "world_size": "discs R14/10/6.5, span 35m inc. spread (tier heights 18/26.5/34.5)",
             "floating_height": "18m base to 35m top disc",
             "special": "3 stacked discs (grass tops) + 2 arched bridges + cloud puffs underneath",
             "fbx": "Saved/Audit/surreal_sweep/islands/SM_Surreal_CloudTerrace.fbx",
             "stats": mesh_stats(terrace_objs)},
        ],
        "exports": {
            "blend": "Saved/Audit/surreal_sweep/islands/Surreal_Islands.blend",
            "beauty": "Saved/Audit/surreal_sweep/islands/Surreal_Islands_Beauty.png",
        },
        "files": files,
        "ue_import": {"scale": "1 unit = 1m (FBX units); apply 100x if project is cm",
                      "nanite": True, "collision": "per-poly or UCX after audit",
                      "masks_sRGB": False},
        "notes": "Surreal Floating Archipelago — impossible terrain. Heightfields/COP masks baked at 1024; meshes impossible but game-navigable (pyramid plateau walkable, ribbon sail-through, terrace bridges walkable).",
    }
    with open(OUT_DIR / "islands_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[blender] manifest -> islands_manifest.json ({len(files)} files)")
    # remove frag
    # keep _masks_manifest.json for provenance

if __name__ == "__main__":
    main()
