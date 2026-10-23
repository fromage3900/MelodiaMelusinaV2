"""Surreal Prop Reliquary — 5 impossible handhelds (Blender 5.2).

Props (meters, 1 unit = 1m):
 1) Memory Oar 2.2m — half wood half crystal
 2) Sorrow Lantern 1.1m cage + floating filament
 3) Tide Chest 0.9m barnacle chest that breathes (shape key + armature)
 4) Conch Horn 0.9m logarithmic spiral
 5) Star Compass floating brass rings (armillary)

Run headless:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python Tools/Houdini/sea_above_reef/surreal_prop_blender.py -- --out C:/EnvironmentPortfolio/BS_GodFile/surreal_sweep_wave2/props
"""
import sys, os, math, json, hashlib
from pathlib import Path

# parse --
argv = sys.argv
if "--" in argv:
    idx = argv.index("--")
    extra = argv[idx+1:]
else:
    extra=[]
out_dir = Path("C:/EnvironmentPortfolio/BS_GodFile/surreal_sweep_wave2/props")
for i,a in enumerate(extra):
    if a=="--out" and i+1 < len(extra):
        out_dir = Path(extra[i+1])
out_dir.mkdir(parents=True, exist_ok=True)

import bpy
import bmesh
from mathutils import Vector, Matrix

# clean scene
def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # ensure scene units = meters
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.length_unit = 'METERS'
    sc.unit_settings.scale_length = 1.0

clean()

tex_dir = out_dir
def load_tex(name):
    p = tex_dir / name
    if p.exists():
        img = bpy.data.images.load(str(p), check_existing=True)
        img.colorspace_settings.name = 'sRGB' if 'Albedo' in name else 'Non-Color'
        return img
    return None

imgs = {
    "brass_albedo": load_tex("T_RelicBrass_Albedo.png"),
    "brass_normal": load_tex("T_RelicBrass_Normal.png"),
    "brass_rough": load_tex("T_RelicBrass_Roughness.png"),
    "wax_albedo": load_tex("T_WeepingWax_Albedo.png"),
    "shell_albedo": load_tex("T_PearlescentShell_Albedo.png"),
    "wood_albedo": load_tex("T_DrownedWood_Albedo.png"),
    "wood_normal": load_tex("T_DrownedWood_Normal.png"),
}

def make_mat(name, base_color=(0.8,0.8,0.8,1), metallic=0, roughness=0.5, transmission=0, emission_color=None, img_albedo=None, img_normal=None, img_rough=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (400,0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0,0)
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if transmission>0:
        # Blender 4.x pricipled has Transmission Weight
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = transmission
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = transmission
        bsdf.inputs["IOR"].default_value = 1.45
    if emission_color:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_color
            bsdf.inputs["Emission Strength"].default_value = 3.0
        else:
            # fallback emission node
            pass
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    # texture nodes
    x = -400
    y = 300
    if img_albedo:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = img_albedo
        tn.location = (x, y)
        y -= 280
        nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
        # tex coord + mapping for tiling
        tc = nt.nodes.new("ShaderNodeTexCoord")
        tc.location = (x-300, y+200)
        # we just use UV; keep simple
    if img_normal and "Normal" in bsdf.inputs:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = img_normal
        tn.location = (x, y-80)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.location = (x+200, -120)
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if img_rough and "Roughness" in bsdf.inputs:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = img_rough
        tn.location = (x, y-360)
        nt.links.new(tn.outputs["Color"], bsdf.inputs["Roughness"])
    return mat

# materials
mat_brass = make_mat("M_RelicBrass", base_color=(0.78,0.65,0.42,1), metallic=0.95, roughness=0.38, img_albedo=imgs["brass_albedo"], img_normal=imgs["brass_normal"], img_rough=imgs["brass_rough"])
mat_wood = make_mat("M_DrownedWood", base_color=(0.36,0.29,0.20,1), roughness=0.82, img_albedo=imgs["wood_albedo"], img_normal=imgs["wood_normal"])
mat_wax = make_mat("M_WeepingWax", base_color=(0.96,0.94,0.88,1), roughness=0.55, transmission=0.15, img_albedo=imgs["wax_albedo"])
mat_shell = make_mat("M_PearlShell", base_color=(0.96,0.94,0.92,1), metallic=0.05, roughness=0.22, img_albedo=imgs["shell_albedo"])
mat_crystal = make_mat("M_Crystal", base_color=(0.72,0.88,0.98,1), metallic=0, roughness=0.04, transmission=0.92)
mat_crystal.blend_method = 'BLEND'
# tune transmission
mat_glass = make_mat("M_LanternGlass", base_color=(1,1,1,1), roughness=0.08, transmission=0.95)
mat_glass.blend_method = 'BLEND'
mat_filament = make_mat("M_Filament", base_color=(1,0.78,0.35,1), roughness=0.5, emission_color=(1,0.82,0.35,1))
mat_barnacle = make_mat("M_Barnacle", base_color=(0.82,0.80,0.76,1), roughness=0.9)
mat_dark_brass = make_mat("M_DarkBrass", base_color=(0.52,0.45,0.32,1), metallic=0.9, roughness=0.45)

def new_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col

def create_mesh_obj(name, verts, faces, uvs=None, collection=None, mat=None):
    mesh = bpy.data.meshes.new(name+"_Mesh")
    mesh.from_pydata(verts, [], faces)
    if uvs:
        uv_layer = mesh.uv_layers.new(name="UVMap")
        # faces assumed quads/tris; need per-loop uv
        # fallback planar projection if count mismatch
        pass
    mesh.update()
    # smart UV project if no UVs
    obj = bpy.data.objects.new(name, mesh)
    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.scene.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj

def apply_transform(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)

# ---------- PROP 1: Memory Oar 2.2m ----------
col_oar = new_collection("MemoryOar")
# shaft: cylinder along Y, length 2.2
# We'll build shaft as two segments wood vs crystal splitting at 1.1m
# Use bmesh for cylinder
def build_cylinder_along_Y(name, radius, length, segs=16, cap=True, col=None, mat=None, z_offset=0):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=segs, radius1=radius, radius2=radius, depth=length)
    # cone depth along Z by default; rotate to Y
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(90),3,'X'))
    # translate so bottom at 0
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, length/2, 0))
    bm.verts.ensure_lookup_table()
    # translate in world
    if z_offset!=0:
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0,0,z_offset))
    mesh = bpy.data.meshes.new(name+"_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    (col or bpy.context.scene.collection).objects.link(obj)
    if mat: obj.data.materials.append(mat)
    # uv
    # simple cube projection
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.cube_project(cube_size=0.3)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)
    return obj

# shaft wood half (0 to 1.1)
oar_shaft_wood = build_cylinder_along_Y("OarShaft_Wood", 0.028, 1.10, segs=18, col=col_oar, mat=mat_wood)
# shaft crystal half (1.1 to 1.75) thinner transition
oar_shaft_crystal = build_cylinder_along_Y("OarShaft_Crystal", 0.024, 0.70, segs=18, col=col_oar, mat=mat_crystal)
oar_shaft_crystal.location.y = 1.10
# blade crystal: flattened box with taper, faceted crystal look
bm = bmesh.new()
# blade dimensions 0.55 long (Y), 0.20 wide (X), 0.025 thick (Z), tapered point
verts = [
    (-0.02,0, -0.012), (0.02,0,-0.012), (0.02,0,0.012), (-0.02,0,0.012), # shaft end quad
    (-0.11,0.55, -0.010), (0.11,0.55,-0.010), (0.11,0.55,0.010), (-0.11,0.55,0.010), # tip wide
]
faces = [(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(0,3,2,1),(4,5,6,7)]
# offset Y to 1.75
for v in verts:
    v = list(v)
verts = [(x, y+1.75, z) for x,y,z in verts]
mesh = bpy.data.meshes.new("OarBlade_Mesh")
mesh.from_pydata(verts, [], faces)
mesh.update()
for p in mesh.polygons: p.use_smooth=True
obj_blade = bpy.data.objects.new("OarBlade", mesh)
col_oar.objects.link(obj_blade)
obj_blade.data.materials.append(mat_crystal)
# add faceted crystal edge: bevel modifier
mod = obj_blade.modifiers.new("Bevel", 'BEVEL')
mod.width = 0.006
mod.segments = 2
# crystal growth: small icosphere cluster at transition (where wood meets crystal)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.04, location=(0,1.10,0))
crystal_knot = bpy.context.view_layer.objects.active
crystal_knot.name="OarCrystalGrowth"
crystal_knot.data.materials.clear()
crystal_knot.data.materials.append(mat_crystal)
col_oar.objects.link(crystal_knot)
# unlink from scene collection
bpy.context.scene.collection.objects.unlink(crystal_knot)
# add overall empty for oar
empty_oar = bpy.data.objects.new("MemoryOar_Root", None)
empty_oar.empty_display_type='ARROWS'
col_oar.objects.link(empty_oar)
for o in list(col_oar.objects):
    if o!=empty_oar and o.parent is None:
        o.parent = empty_oar

# ---------- PROP 2: Sorrow Lantern 1.1m ----------
col_lan = new_collection("SorrowLantern")
# base plate
bm=bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co.x*=0.28; v.co.y*=0.28; v.co.z*=0.05
bmesh.ops.translate(bm, verts=bm.verts, vec=(0,0,0.025))
mesh=bpy.data.meshes.new("LanternBase_Mesh")
bm.to_mesh(mesh); bm.free()
obj_base=bpy.data.objects.new("LanternBase", mesh)
col_lan.objects.link(obj_base)
obj_base.data.materials.append(mat_brass)
# top cap similar but smaller, at height 1.05
bm=bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co.x*=0.24; v.co.y*=0.24; v.co.z*=0.04
bmesh.ops.translate(bm, verts=bm.verts, vec=(0,0,1.05))
mesh=bpy.data.meshes.new("LanternTop_Mesh")
bm.to_mesh(mesh); bm.free()
obj_top=bpy.data.objects.new("LanternTop", mesh)
col_lan.objects.link(obj_top)
obj_top.data.materials.append(mat_brass)
# 4 vertical struts: cylinders at corners
for sx in (-0.11, 0.11):
    for sy in (-0.11, 0.11):
        o=build_cylinder_along_Y(f"LanternStrut_{sx}_{sy}", 0.012, 1.02, segs=8, col=col_lan, mat=mat_dark_brass)
        # reorient: cylinder along Y currently; need along Z
        o.rotation_euler.x = math.radians(-90)
        o.location = (sx, sy, 0.03)
        # scale already along Y=1.02 translates to Z after rotation
# glass panels 4 sides thin cubes
for i, (axis, sign) in enumerate([(0,1),(0,-1),(1,1),(1,-1)]):
    bm=bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    # thin wall
    if axis==0:
        scale=(0.01,0.20,0.90)
    else:
        scale=(0.20,0.01,0.90)
    for v in bm.verts:
        v.co.x*=scale[0]; v.co.y*=scale[1]; v.co.z*=scale[2]
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0,0,0.55))
    if axis==0:
        off = (sign*0.115, 0, 0)
    else:
        off = (0, sign*0.115, 0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=off)
    mesh=bpy.data.meshes.new(f"LanternGlass_{i}_Mesh")
    bm.to_mesh(mesh); bm.free()
    obj=bpy.data.objects.new(f"LanternGlass_{i}", mesh)
    col_lan.objects.link(obj)
    obj.data.materials.append(mat_glass)
    obj.data.materials.append(mat_wax) # wax drips second slot? keep glass
# floating filament: curve spiral inside
curve = bpy.data.curves.new("FilamentCurve", 'CURVE')
curve.dimensions='3D'
spline = curve.splines.new('BEZIER')
spline.bezier_points.add(7)
for i, pt in enumerate(spline.bezier_points):
    t = i/7
    ang = t*math.pi*4
    r = 0.025 + t*0.015
    x = math.cos(ang)*r
    y = math.sin(ang)*r
    z = 0.45 + t*0.35 + math.sin(t*math.pi*2)*0.02
    pt.co = Vector((x,y,z))
    pt.handle_left = pt.co + Vector((-0.02,0,0))
    pt.handle_right = pt.co + Vector((0.02,0,0))
    pt.handle_left_type='AUTO'
    pt.handle_right_type='AUTO'
curve.bevel_depth = 0.003
curve.bevel_resolution = 3
obj_curve = bpy.data.objects.new("LanternFilament", curve)
col_lan.objects.link(obj_curve)
obj_curve.data.materials.append(mat_filament)
# add little emissive icosphere floating slightly off-center (no connection)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.015, location=(0.02, -0.01, 0.68))
fil_glow = bpy.context.view_layer.objects.active
fil_glow.name="FilamentGlow"
fil_glow.data.materials.clear()
fil_glow.data.materials.append(mat_filament)
col_lan.objects.link(fil_glow)
bpy.context.scene.collection.objects.unlink(fil_glow)
# weeping wax drips on top cap
for i in range(6):
    ang = i/6*math.pi*2
    x = math.cos(ang)*0.09
    y = math.sin(ang)*0.09
    bpy.ops.mesh.primitive_cone_add(radius1=0.018, radius2=0, depth=0.08, location=(x,y,1.02))
    d=bpy.context.view_layer.objects.active
    d.name=f"WaxDrip_{i}"
    d.rotation_euler.x = math.pi
    d.data.materials.clear()
    d.data.materials.append(mat_wax)
    col_lan.objects.link(d)
    bpy.context.scene.collection.objects.unlink(d)

empty_lan = bpy.data.objects.new("SorrowLantern_Root", None)
empty_lan.empty_display_type='ARROWS'
col_lan.objects.link(empty_lan)
for o in list(col_lan.objects):
    if o!=empty_lan and o.parent is None:
        o.parent = empty_lan
empty_lan.location = (2.5,0,0)  # offset to avoid overlap in overview

# ---------- PROP 3: Tide Chest ----------
col_chest = new_collection("TideChest")
# chest body
bm=bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co.x*=0.90; v.co.y*=0.55; v.co.z*=0.45
bmesh.ops.translate(bm, verts=bm.verts, vec=(0,0,0.225))
mesh=bpy.data.meshes.new("ChestBody_Mesh")
bm.to_mesh(mesh); bm.free()
obj_body=bpy.data.objects.new("ChestBody", mesh)
col_chest.objects.link(obj_body)
obj_body.data.materials.append(mat_wood)
# lid: half cylinder + box
bm=bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co.x*=0.92; v.co.y*=0.57; v.co.z*=0.08
bmesh.ops.translate(bm, verts=bm.verts, vec=(0,0,0.49))
# add slight arch via displace top verts
for v in bm.verts:
    if v.co.z>0.49:
        v.co.z += 0.06*math.cos(v.co.x*1.8)
mesh=bpy.data.meshes.new("ChestLid_Mesh")
bm.to_mesh(mesh); bm.free()
obj_lid=bpy.data.objects.new("ChestLid", mesh)
col_chest.objects.link(obj_lid)
obj_lid.data.materials.append(mat_wood)
# brass bands
for z in (0.15, 0.32):
    bm=bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x*=0.94; v.co.y*=0.59; v.co.z*=0.02
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0,0,z))
    mesh=bpy.data.meshes.new(f"ChestBand_{z}_Mesh")
    bm.to_mesh(mesh); bm.free()
    b=bpy.data.objects.new(f"ChestBand_{z}", mesh)
    col_chest.objects.link(b)
    b.data.materials.append(mat_brass)
# barnacles: cluster on chest
import random
random.seed(20260829+99)
for i in range(22):
    x = random.uniform(-0.40,0.40)
    y = random.uniform(-0.22,0.22) + (0.28 if random.random()>0.5 else -0.28)*0.15
    z = random.uniform(0.08,0.42)
    # snap to surface: if on side, adjust
    # simple: place on top/side randomly
    r = random.uniform(0.025,0.055)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=(x,y,z))
    b=bpy.context.view_layer.objects.active
    b.name=f"Barnacle_{i:02d}"
    # squash
    b.scale = (1,1,0.7)
    b.data.materials.clear()
    b.data.materials.append(mat_barnacle)
    # add inner dark pit
    col_chest.objects.link(b)
    bpy.context.scene.collection.objects.unlink(b)
# brass lock
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0,0.28,0.26))
lock=bpy.context.view_layer.objects.active
lock.name="ChestLock"
lock.scale=(0.10,0.02,0.12)
lock.data.materials.clear()
lock.data.materials.append(mat_brass)
col_chest.objects.link(lock)
bpy.context.scene.collection.objects.unlink(lock)
# breathing shape key on lid + body (scale Z)
# add shape key to lid
obj_lid.shape_key_add(name="Basis")
sk = obj_lid.shape_key_add(name="Breathe")
for v in obj_lid.data.vertices:
    # push lid up + expand slightly
    sk.data[v.index].co = v.co + Vector((0,0,0.025)) + Vector((v.co.x*0.015, v.co.y*0.015,0))
sk.value = 0.5
# armature for breathing (single bone)
bpy.ops.object.armature_add(enter_editmode=False, location=(0,0,0.2))
arm = bpy.context.view_layer.objects.active
arm.name="ChestBreathArm"
col_chest.objects.link(arm)
bpy.context.scene.collection.objects.unlink(arm)
arm.parent = obj_body  # just parenting for organization
# hide armature from render? keep
empty_chest = bpy.data.objects.new("TideChest_Root", None)
empty_chest.empty_display_type='ARROWS'
col_chest.objects.link(empty_chest)
for o in list(col_chest.objects):
    if o!=empty_chest and o.parent is None:
        o.parent = empty_chest
empty_chest.location = (5.0,0,0)

# ---------- PROP 4: Conch Horn 0.9m ----------
col_horn = new_collection("ConchHorn")
# build logarithmic spiral curve 0.9m long along Y then curl
curve2 = bpy.data.curves.new("ConchSpiralCurve", 'CURVE')
curve2.dimensions='3D'
curve2.bevel_depth = 0.01
curve2.bevel_resolution = 4
curve2.use_fill_caps = True
spline = curve2.splines.new('POLY')
pts = []
turns = 3.2
n=80
for i in range(n+1):
    t = i/n
    ang = t*math.pi*2*turns
    # log spiral radius grows outward
    r = 0.018 * math.exp(0.65*t*turns*0.6)
    # spiral in XZ plane curled, then extend forward in Y for mouthpiece
    x = math.cos(ang)*r
    z = math.sin(ang)*r
    y = t*0.55  # length along Y ~0.55 spiral, plus mouthpiece 0.35 = 0.9 total
    # tilt so bell opens upward
    z += t*0.08
    pts.append((x,y,z,1))
# poly spline
spline.points.add(len(pts)-1)
for i, (x,y,z,w) in enumerate(pts):
    spline.points[i].co = (x,y,z,w)
# taper bevel via taper object? simple: set bevel depth varying via radius? use points radius
for i,p in enumerate(spline.points):
    t=i/n
    p.radius = 0.6 + t*2.2  # bell flares
obj_spiral = bpy.data.objects.new("ConchSpiral", curve2)
col_horn.objects.link(obj_spiral)
obj_spiral.data.materials.append(mat_shell)
# mouthpiece: small brass cylinder at start
bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=0.08, location=(pts[0][0], pts[0][1]-0.04, pts[0][2]))
mp=bpy.context.view_layer.objects.active
mp.name="ConchMouthpiece"
mp.rotation_euler.x = math.radians(90)
mp.data.materials.clear()
mp.data.materials.append(mat_brass)
col_horn.objects.link(mp)
bpy.context.scene.collection.objects.unlink(mp)
# barnacle + brass ring on horn
for i in range(3):
    t = 0.5 + i*0.15
    idx = int(t*n)
    x,y,z,w = pts[idx]
    bpy.ops.mesh.primitive_torus_add(major_radius=0.02+t*0.04, minor_radius=0.006, location=(x,y,z))
    rng=bpy.context.view_layer.objects.active
    rng.name=f"ConchBrassRing_{i}"
    rng.rotation_euler.x = math.radians(90)
    rng.data.materials.clear()
    rng.data.materials.append(mat_brass)
    col_horn.objects.link(rng)
    bpy.context.scene.collection.objects.unlink(rng)

empty_horn = bpy.data.objects.new("ConchHorn_Root", None)
empty_horn.empty_display_type='ARROWS'
col_horn.objects.link(empty_horn)
for o in list(col_horn.objects):
    if o!=empty_horn and o.parent is None:
        o.parent = empty_horn
empty_horn.location = (7.5,0,0)
empty_horn.rotation_euler.z = math.radians(45)

# ---------- PROP 5: Star Compass ----------
col_comp = new_collection("StarCompass")
# base disc brass
bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.025, location=(0,0,0))
disc=bpy.context.view_layer.objects.active
disc.name="CompassDisc"
disc.data.materials.clear()
disc.data.materials.append(mat_brass)
col_comp.objects.link(disc)
bpy.context.scene.collection.objects.unlink(disc)
# central dome (glass/crystal)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(0,0,0.04))
dome=bpy.context.view_layer.objects.active
dome.name="CompassDome"
dome.data.materials.clear()
dome.data.materials.append(mat_crystal)
col_comp.objects.link(dome)
bpy.context.scene.collection.objects.unlink(dome)
# floating brass rings: 3 nested tori gimbals
rings = []
for i, (major, minor, rot) in enumerate([
    (0.22,0.012,(0,0,0)),
    (0.26,0.010,(math.radians(90),0,0)),
    (0.30,0.008,(0,math.radians(90),0)),
]):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, location=(0,0,0.08))
    t=bpy.context.view_layer.objects.active
    t.name=f"CompassRing_{i}"
    t.rotation_euler = rot
    t.data.materials.clear()
    t.data.materials.append(mat_brass)
    # add small notch/star markers
    col_comp.objects.link(t)
    bpy.context.scene.collection.objects.unlink(t)
    rings.append(t)
# star markers on rings (small icospheres)
for i in range(8):
    ang=i/8*math.pi*2
    x=math.cos(ang)*0.30
    y=math.sin(ang)*0.30
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.012, location=(x,y,0.08))
    s=bpy.context.view_layer.objects.active
    s.name=f"StarMarker_{i}"
    s.data.materials.clear()
    s.data.materials.append(mat_filament)
    col_comp.objects.link(s)
    bpy.context.scene.collection.objects.unlink(s)
# needle
bm=bmesh.new()
bmesh.ops.create_cube(bm, size=1)
for v in bm.verts:
    v.co.x*=0.015; v.co.y*=0.18; v.co.z*=0.004
bmesh.ops.translate(bm, verts=bm.verts, vec=(0,0.04,0))
mesh=bpy.data.meshes.new("CompassNeedle_Mesh")
bm.to_mesh(mesh); bm.free()
needle=bpy.data.objects.new("CompassNeedle", mesh)
col_comp.objects.link(needle)
needle.location.z=0.03
needle.rotation_euler.z = math.radians(32)
needle.data.materials.append(mat_filament)
# add floating animation hint: empty with constraint? just separate collection offset
empty_comp = bpy.data.objects.new("StarCompass_Root", None)
empty_comp.empty_display_type='ARROWS'
col_comp.objects.link(empty_comp)
for o in list(col_comp.objects):
    if o!=empty_comp and o.parent is None:
        o.parent = empty_comp
empty_comp.location = (10.0,0,0.6)

# ---------- Scene overview & lighting ----------
# sun + fill
bpy.ops.object.light_add(type='SUN', location=(5, -5, 8))
sun=bpy.context.view_layer.objects.active
sun.data.energy = 5.0
bpy.ops.object.light_add(type='AREA', location=(0, -3, 2))
area=bpy.context.view_layer.objects.active
area.data.energy = 80
area.data.size = 3
# camera overview
bpy.ops.object.camera_add(location=(5, -8, 3.5), rotation=(math.radians(68),0,math.radians(12)))
cam=bpy.context.view_layer.objects.active
bpy.context.scene.camera = cam

# ---------- Save blend & export FBX per prop ----------
blend_path = out_dir / "SurrealProps.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
print(f"[props] blend -> {blend_path}")

# FBX exports per prop (select only that collection's objects)
import os
roots = {
    "MemoryOar": empty_oar,
    "SorrowLantern": empty_lan,
    "TideChest": empty_chest,
    "ConchHorn": empty_horn,
    "StarCompass": empty_comp,
}
fbx_files=[]
for name, root in roots.items():
    bpy.ops.object.select_all(action='DESELECT')
    # select hierarchy
    def select_hier(obj):
        obj.select_set(True)
        for child in obj.children:
            select_hier(child)
    # root is empty with parented objects, but some objects are children via parent link; ensure select
    # also select all objects in collection
    col = bpy.data.collections.get(root.users_collection[0].name if root.users_collection else name)
    # fallback: select by parent
    select_hier(root)
    # also include objects whose parent is root (already) plus loose ones in col
    for o in bpy.data.collections[root.users_collection[0].name].objects if root.users_collection else []:
        o.select_set(True)
    fbx_path = out_dir / f"{name}.fbx"
    bpy.ops.export_scene.fbx(filepath=str(fbx_path), use_selection=True, apply_scale_options='FBX_SCALE_ALL', object_types={'MESH','EMPTY','ARMATURE','OTHER'}, bake_anim=False, axis_forward='-Z', axis_up='Y')
    fbx_files.append(str(fbx_path))
    print(f"[props] fbx -> {fbx_path.name} ({os.path.getsize(str(fbx_path))} bytes)")

# quick Eevee preview render per prop (centered)
# setup render
scene = bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in dir(bpy.types) else 'BLENDER_EEVEE'
scene.render.resolution_x=1024
scene.render.resolution_y=1024
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG'
tex_previews=[]
for name, root in roots.items():
    # frame camera on root
    loc = root.matrix_world.translation if hasattr(root.matrix_world,'translation') else root.location
    # move camera to look at prop
    cam.location = (loc.x, loc.y - 1.8, loc.z + 0.9)
    # point at loc
    direction = loc - cam.location
    # simple look-at via track
    bpy.context.view_layer.update()
    # quick: set camera rotation to look at
    # compute yaw/pitch
    dx, dy, dz = direction.x, direction.y, direction.z
    yaw = math.atan2(dx, dy)  # not precise but ok
    pitch = math.atan2(dz, math.sqrt(dx*dx+dy*dy))
    cam.rotation_euler = (math.radians(55), 0, yaw)
    scene.render.filepath = str(out_dir / f"Preview_{name}.png")
    try:
        bpy.ops.render.render(write_still=True)
        tex_previews.append(f"Preview_{name}.png")
        print(f"[props] preview -> Preview_{name}.png")
    except Exception as e:
        print(f"[props] preview {name} failed: {e}")

# manifest
manifest = {
    "schema": "surreal.props.reliquary.v1",
    "generator": "surreal_prop_blender.py (Blender 5.2 + reef_common tiling textures)",
    "textures": {
        "size": 1024,
        "tiling": "reef_common lattice-periodic",
        "files": [p.name for p in out_dir.glob("T_*.png")],
    },
    "props": [
        {"id":"memory_oar","name":"Memory Oar","length_m":2.2,"desc":"half wood half crystal oar","collection":"MemoryOar","root":"MemoryOar_Root","fbx":"MemoryOar.fbx","materials":["M_DrownedWood","M_Crystal"]},
        {"id":"sorrow_lantern","name":"Sorrow Lantern","height_m":1.1,"desc":"cage with floating filament, weeping wax drips","collection":"SorrowLantern","root":"SorrowLantern_Root","fbx":"SorrowLantern.fbx","materials":["M_RelicBrass","M_LanternGlass","M_Filament","M_WeepingWax"]},
        {"id":"tide_chest","name":"Tide Chest","size_m":[0.9,0.55,0.53],"desc":"barnacle chest that breathes (shape key Breathe + armature)","collection":"TideChest","root":"TideChest_Root","fbx":"TideChest.fbx","materials":["M_DrownedWood","M_RelicBrass","M_Barnacle"]},
        {"id":"conch_horn","name":"Conch Horn","length_m":0.9,"desc":"logarithmic spiral you can blow, brass rings","collection":"ConchHorn","root":"ConchHorn_Root","fbx":"ConchHorn.fbx","materials":["M_PearlShell","M_RelicBrass"]},
        {"id":"star_compass","name":"Star Compass","diameter_m":0.6,"desc":"floating brass gimbal rings, crystal dome","collection":"StarCompass","root":"StarCompass_Root","fbx":"StarCompass.fbx","materials":["M_RelicBrass","M_Crystal","M_Filament"]},
    ],
    "blend": blend_path.name,
    "fbx": [Path(p).name for p in fbx_files],
    "previews": tex_previews,
    "contact_sheet": "_ContactSheet_Textures.png",
}
with open(out_dir / "props_manifest.json","w",encoding="utf-8") as f:
    json.dump(manifest,f,indent=2)
print(f"[props] manifest -> {out_dir / 'props_manifest.json'}")
