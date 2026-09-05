"""AAA Concert Harp for Melusina — Blender 5.2 Lookdev Build.

Art direction: "designed game characters first, believable anatomy second,
painterly realism last." Stylized, warm, storybook fantasy. Not photoreal.

Features:
- Bezier curves for body/neck/pillar (true curved topology)
- Subdivision surface for smooth silhouettes
- Procedural wood + gold + string materials
- Studio 3-point lighting + rim
- Beauty render + comparison sheet

Run: blender --factory-startup -b -P Tools/BlenderAddons/aaa_concert_harp_lookdev.py
"""
import bpy
import os
import math

repo = "C:/EnvironmentPortfolio/BS_GodFile"
out_dir = os.path.join(repo, "Exports", "MelusinaInstruments", "Lookdev")
os.makedirs(out_dir, exist_ok=True)

print("=== AAA Concert Harp — Lookdev Build ===")

# Clean scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

# ============================================================
# 1. HARP BODY (Bezier + Subdivision)
# ============================================================

def make_bezier_closed(points, loc=(0,0,0), depth=0.04):
    """Create a closed bezier curve from points, extruded for depth."""
    bpy.ops.curve.primitive_bezier_curve_add(location=loc)
    curve = bpy.context.active_object
    spline = curve.data.splines[0]
    spline.type = "BEZIER"
    
    # Add needed points
    while len(spline.bezier_points) < len(points):
        spline.bezier_points.add(count=1)
    
    for i, (co, hl, hr) in enumerate(points):
        p = spline.bezier_points[i]
        p.co = co
        p.handle_left = hl
        p.handle_right = hr
    
    curve.data.extrude = depth
    curve.data.bevel_depth = 0.003
    curve.data.bevel_resolution = 2
    return curve

# Soundboard profile (side view: elegant tapered arc)
soundboard_pts = [
    ((0, 0, 0), (-0.02, 0, 0), (0.02, 0, 0)),
    ((0.08, 0, 0.35), (0.05, 0, 0.25), (0.11, 0, 0.45)),
    ((0.14, 0, 0.75), (0.10, 0, 0.65), (0.18, 0, 0.85)),
    ((0.17, 0, 1.20), (0.13, 0, 1.10), (0.21, 0, 1.30)),
    ((0.18, 0, 1.55), (0.14, 0, 1.45), (0.22, 0, 1.65)),
]
sb = make_bezier_closed(soundboard_pts, depth=0.05)
sb.name = "Harp_Soundboard"

# Pillar (ornate column at base)
bpy.ops.curve.primitive_bezier_curve_add(location=(0.17, 0.025, 0))
pillar = bpy.context.active_object
pillar.name = "Harp_Pillar"
spline = pillar.data.splines[0]
spline.type = "BEZIER"
spline.bezier_points.add(count=3)
pts = spline.bezier_points
pts[0].co = (0, 0, 0); pts[0].handle_left = (-0.02, 0, 0); pts[0].handle_right = (0.02, 0, 0)
pts[1].co = (0, 0, 0.4); pts[1].handle_left = (-0.02, 0, 0.3); pts[1].handle_right = (0.02, 0, 0.5)
pts[2].co = (0, 0, 0.9); pts[2].handle_left = (-0.02, 0, 0.8); pts[2].handle_right = (0.02, 0, 1.0)
pts[3].co = (0, 0, 1.75); pts[3].handle_left = (-0.02, 0, 1.65); pts[3].handle_right = (0.02, 0, 1.85)
pillar.data.bevel_depth = 0.035
pillar.data.bevel_resolution = 6
pillar.data.fill_mode = "FULL"

# Neck (sweeping arc from pillar top to soundboard tip)
bpy.ops.curve.primitive_bezier_curve_add(location=(0.17, 0.025, 1.75))
neck = bpy.context.active_object
neck.name = "Harp_Neck"
spline = neck.data.splines[0]
spline.type = "BEZIER"
spline.bezier_points.add(count=4)
pts = spline.bezier_points
pts[0].co = (0, 0, 0)
pts[1].co = (-0.06, 0, 0.28)
pts[2].co = (-0.18, 0, 0.52)
pts[3].co = (-0.36, 0, 0.68)
pts[4].co = (-0.55, 0, 0.75)
neck.data.bevel_depth = 0.03
neck.data.bevel_resolution = 6
neck.data.fill_mode = "FULL"

# Capitol (decorative top cap)
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=16, ring_count=8, radius=0.04,
    location=(0.17, 0.025, 1.78)
)
capitol = bpy.context.active_object
capitol.name = "Harp_Capitol"
capitol.scale = (1.2, 1.0, 0.8)

# Base foot
bpy.ops.mesh.primitive_cylinder_add(
    vertices=16, radius=0.06, depth=0.04,
    location=(0.17, 0.025, -0.02)
)
foot = bpy.context.active_object
foot.name = "Harp_Foot"

# ============================================================
# 2. STRINGS (41 graduated, thin cylinders)
# ============================================================

strings = []
for i in range(41):
    t = i / 40.0
    length = 0.35 + t * 1.2
    y_pos = -0.06 + t * 0.12
    
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8, radius=0.0015 + t * 0.0008, depth=length,
        location=(0.03, y_pos, 0.05 + length/2)
    )
    string = bpy.context.active_object
    string.name = f"Harp_String_{i:02d}"
    strings.append(string)

print(f"[strings] created {len(strings)} strings")

# ============================================================
# 3. SUBDIVISION + SMOOTH
# ============================================================

for obj in [sb, pillar, neck, capitol, foot] + strings:
    bpy.context.view_layer.objects.active = obj
    if obj.type == "CURVE":
        bpy.ops.object.convert(target="MESH")
    bpy.ops.object.shade_smooth()

# ============================================================
# 4. MATERIALS (Procedural — stylized wood, gold, strings)
# ============================================================

def create_wood_material(name, base_color, grain_color):
    """Procedural wood with grain."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default
    nodes.clear()
    
    # Output
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)
    
    # Principled BSDF
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.6
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    
    # Wood grain texture
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-800, 0)
    
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-600, 0)
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    
    wave = nodes.new("ShaderNodeTexWave")
    wave.location = (-400, 0)
    wave.wave_type = "BANDS"
    wave.inputs["Scale"].default_value = 8.0
    wave.inputs["Distortion"].default_value = 0.5
    links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    
    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.location = (-200, 0)
    color_ramp.color_ramp.elements[0].color = (*grain_color, 1.0)
    color_ramp.color_ramp.elements[1].color = (*base_color, 1.0)
    links.new(wave.outputs["Fac"], color_ramp.inputs["Fac"])
    
    links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    
    return mat

def create_gold_material(name):
    """Procedural gold accent."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (0.83, 0.69, 0.22, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.25
    
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat

def create_string_material(name):
    """Procedural string (nylon/gut look)."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (0.95, 0.92, 0.85, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.4
    bsdf.inputs["Specular IOR Level"].default_value = 0.5
    
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat

# Create materials
wood_dark = create_wood_material("M_Harp_Wood_Dark", (0.35, 0.18, 0.08), (0.25, 0.12, 0.05))
wood_light = create_wood_material("M_Harp_Wood_Light", (0.55, 0.32, 0.15), (0.40, 0.22, 0.10))
gold = create_gold_material("M_Harp_Gold")
string_mat = create_string_material("M_Harp_Strings")

# Assign materials
sb.data.materials.append(wood_dark)
pillar.data.materials.append(wood_light)
neck.data.materials.append(wood_dark)
capitol.data.materials.append(gold)
foot.data.materials.append(wood_light)
for s in strings:
    s.data.materials.append(string_mat)

print("[materials] assigned procedural wood, gold, string materials")

# ============================================================
# 5. STUDIO LIGHTING (3-point + rim)
# ============================================================

# Key light (warm, top-left)
bpy.ops.object.light_add(type="AREA", location=(2, -1.5, 3))
key = bpy.context.active_object
key.name = "Light_Key"
key.data.energy = 150
key.data.size = 2.0
key.data.color = (1.0, 0.95, 0.9)
key.rotation_euler = (math.radians(45), math.radians(30), math.radians(-30))

# Fill light (cool, right)
bpy.ops.object.light_add(type="AREA", location=(-2, -1, 2))
fill = bpy.context.active_object
fill.name = "Light_Fill"
fill.data.energy = 80
fill.data.size = 1.5
fill.data.color = (0.9, 0.95, 1.0)
fill.rotation_euler = (math.radians(30), math.radians(-20), math.radians(45))

# Rim light (back, for silhouette separation)
bpy.ops.object.light_add(type="AREA", location=(0, 2.5, 1.5))
rim = bpy.context.active_object
rim.name = "Light_Rim"
rim.data.energy = 120
rim.data.size = 1.0
rim.data.color = (1.0, 0.9, 0.8)
rim.rotation_euler = (math.radians(60), math.radians(180), math.radians(0))

# Ambient fill
bpy.ops.object.light_add(type="AREA", location=(0, 0, 4))
ambient = bpy.context.active_object
ambient.name = "Light_Ambient"
ambient.data.energy = 40
ambient.data.size = 3.0
ambient.data.color = (0.8, 0.85, 0.9)

print("[lighting] studio 3-point + rim setup")

# ============================================================
# 6. CAMERA (framing the harp)
# ============================================================

# Harp is ~1.75m tall, centered around (0.17, 0.025, 0.8)
# Camera should look AT the harp center, closer for better framing
harp_center = (0.17, 0.025, 0.8)
bpy.ops.object.camera_add(location=(0.8, -0.6, 0.9))
cam = bpy.context.active_object
cam.name = "Camera_Harp"

# Point camera at harp center (strings span x=-0.6 to x=0.24, center ~x=-0.2)
from mathutils import Vector
harp_center = Vector((-0.1, 0.025, 0.8))
cam.location = Vector((-0.1, -1.2, 0.8))
direction = harp_center - cam.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot_quat.to_euler()

bpy.context.scene.camera = cam

# Camera settings
cam.data.lens = 35
cam.data.clip_end = 100

print(f"[camera] positioned at {cam.location}, looking at {harp_center}")

# ============================================================
# 7. RENDER SETTINGS
# ============================================================

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.cycles.samples = 256
scene.cycles.use_denoising = True
scene.render.filepath = os.path.join(out_dir, "harp_beauty_")
scene.render.image_settings.file_format = "PNG"

# Background (warm parchment, slightly darker for contrast)
scene.world.node_tree.nodes[1].inputs[0].default_value = (0.85, 0.82, 0.75, 1.0)

# Boost light energies
key.data.energy = 400
fill.data.energy = 200
rim.data.energy = 350
ambient.data.energy = 150

# Boost render samples
scene.cycles.samples = 512

print("[render] Cycles 1920x1080, 256 samples")

# ============================================================
# 8. CONVERT CURVES TO MESH + JOIN ALL PARTS
# ============================================================

# Convert all curves to mesh first
for obj in bpy.data.objects:
    if obj.type == "CURVE":
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.convert(target="MESH")

# JOIN all parts (only mesh objects)
bpy.ops.object.select_all(action="DESELECT")
mesh_objs = [o for o in bpy.data.objects if o.type == "MESH"]
for p in mesh_objs:
    p.select_set(True)
if mesh_objs:
    bpy.context.view_layer.objects.active = mesh_objs[0]
    bpy.ops.object.join()
    harp = bpy.context.active_object
    harp.name = "SM_Mus_Harp_Concert_Real"
    print(f"[join] final: {len(harp.data.vertices)} verts, {len(harp.data.polygons)} polys")

# ============================================================
# 9. RENDER BEAUTY
# ============================================================

bpy.ops.render.render(write_still=True)
print(f"[render] beauty -> {scene.render.filepath}0001.png")

# ============================================================
# 10. EXPORT FBX
# ============================================================

fbx_path = os.path.join(out_dir, "SM_Mus_Harp_Concert_Real.fbx")
bpy.ops.object.select_all(action="DESELECT")
harp.select_set(True)
bpy.context.view_layer.objects.active = harp
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=True,
    use_mesh_modifiers=True,
    apply_scale_options="FBX_SCALE_ALL",
    mesh_smooth_type="FACE",
)
print(f"[export] FBX -> {fbx_path}")

print("=== AAA Concert Harp Lookdev Build Complete ===")
