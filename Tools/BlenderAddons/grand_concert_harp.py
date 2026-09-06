"""Grand Concert Harp — AAA Lookdev for Melusina.

Proper concert harp proportions: ~1.8m tall, ~0.9m wide curve.
Ornate carved soundboard, gold leaf decorations, 47 strings.

Run: blender --factory-startup -b -P Tools/BlenderAddons/grand_concert_harp.py
"""
import bpy
import os
import math
from mathutils import Vector

repo = "C:/EnvironmentPortfolio/BS_GodFile"
out_dir = os.path.join(repo, "Exports", "MelusinaInstruments", "Lookdev")
os.makedirs(out_dir, exist_ok=True)

print("=== Grand Concert Harp — AAA Lookdev ===")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

# ============================================================
# 1. SOUNDBOARD (Large tapered slab with carved rosettes)
# ============================================================

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
soundboard = bpy.context.active_object
soundboard.name = "Harp_Soundboard"
soundboard.scale = (0.45, 0.04, 0.9)  # Wide, thin, tall

# Add subdivision for smooth carving
bpy.context.view_layer.objects.active = soundboard
bpy.ops.object.modifier_add(type='SUBSURF')
soundboard.modifiers["Subdivision"].levels = 3
soundboard.modifiers["Subdivision"].render_levels = 4

# Add displacement for carved rosettes
bpy.ops.object.modifier_add(type='DISPLACE')
disp = soundboard.modifiers["Displace"]
disp.strength = 0.02
disp.mid_level = 0.5

# Create rosette texture
rosette_tex = bpy.data.textures.new("Rosette", "VORONOI")
rosette_tex.noise_scale = 2.0
disp.texture = rosette_tex

# Apply modifiers
bpy.ops.object.modifier_apply(modifier="Subdivision")
bpy.ops.object.modifier_apply(modifier="Displace")

print(f"[soundboard] created: {len(soundboard.data.vertices)} verts")

# ============================================================
# 2. PILLAR (Ornate column with gold rings)
# ============================================================

bpy.ops.mesh.primitive_cylinder_add(
    vertices=32, radius=0.06, depth=1.8,
    location=(0.4, 0.02, 0.9)
)
pillar = bpy.context.active_object
pillar.name = "Harp_Pillar"

# Add decorative rings
for i in range(5):
    z_pos = 0.3 + i * 0.35
    bpy.ops.mesh.primitive_torus_add(
        major_segments=24, minor_segments=8,
        location=(0.4, 0.02, z_pos),
        major_radius=0.07, minor_radius=0.008
    )
    ring = bpy.context.active_object
    ring.name = f"Harp_Pillar_Ring_{i}"

# Pillar capital (top ornament)
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=32, ring_count=16, radius=0.05,
    location=(0.4, 0.02, 1.82)
)
capital = bpy.context.active_object
capital.name = "Harp_Pillar_Capital"
capital.scale = (1.2, 1.0, 0.8)

print(f"[pillar] created with {len(pillar.data.vertices)} verts")

# ============================================================
# 3. NECK (Sweeping S-curve with carvings)
# ============================================================

bpy.ops.curve.primitive_bezier_curve_add(location=(0.4, 0.02, 1.8))
neck = bpy.context.active_object
neck.name = "Harp_Neck"

spline = neck.data.splines[0]
spline.type = "BEZIER"
spline.bezier_points.add(count=5)

pts = spline.bezier_points
pts[0].co = (0, 0, 0)
pts[0].handle_left = (-0.05, 0, 0)
pts[0].handle_right = (0.05, 0, 0)

pts[1].co = (-0.08, 0, 0.35)
pts[1].handle_left = (-0.12, 0, 0.25)
pts[1].handle_right = (-0.04, 0, 0.45)

pts[2].co = (-0.22, 0, 0.65)
pts[2].handle_left = (-0.26, 0, 0.55)
pts[2].handle_right = (-0.18, 0, 0.75)

pts[3].co = (-0.40, 0, 0.85)
pts[3].handle_left = (-0.44, 0, 0.75)
pts[3].handle_right = (-0.36, 0, 0.95)

pts[4].co = (-0.55, 0, 0.95)
pts[4].handle_left = (-0.59, 0, 0.85)
pts[4].handle_right = (-0.51, 0, 1.05)

pts[5].co = (-0.65, 0, 1.0)
pts[5].handle_left = (-0.69, 0, 0.90)
pts[5].handle_right = (-0.61, 0, 1.10)

neck.data.bevel_depth = 0.035
neck.data.bevel_resolution = 8
neck.data.fill_mode = "FULL"

# Convert to mesh
bpy.context.view_layer.objects.active = neck
neck.select_set(True)
bpy.ops.object.convert(target="MESH")
bpy.ops.object.modifier_add(type='SUBSURF')
neck.modifiers["Subdivision"].levels = 3

print(f"[neck] created: {len(neck.data.vertices)} verts")

# ============================================================
# 4. CAPITOL (Decorative top)
# ============================================================

bpy.ops.mesh.primitive_uv_sphere_add(
    segments=32, ring_count=16, radius=0.04,
    location=(0.4, 0.02, 1.85)
)
capitol = bpy.context.active_object
capitol.name = "Harp_Capitol"
capitol.scale = (1.3, 1.0, 0.7)

# Finial (top ornament)
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=16, ring_count=8, radius=0.02,
    location=(0.4, 0.02, 1.9)
)
finial = bpy.context.active_object
finial.name = "Harp_Finial"

print("[capitol] created")

# ============================================================
# 5. STRINGS (47 graduated, thin cylinders)
# ============================================================

strings = []
for i in range(47):
    t = i / 46.0
    length = 0.4 + t * 1.3
    y_pos = -0.15 + t * 0.30
    
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8, radius=0.001 + t * 0.0005, depth=length,
        location=(0.05, y_pos, 0.05 + length/2)
    )
    string = bpy.context.active_object
    string.name = f"Harp_String_{i:02d}"
    strings.append(string)

print(f"[strings] created {len(strings)} strings")

# ============================================================
# 6. BASE FOOT
# ============================================================

bpy.ops.mesh.primitive_cylinder_add(
    vertices=32, radius=0.08, depth=0.04,
    location=(0.4, 0.02, -0.02)
)
foot = bpy.context.active_object
foot.name = "Harp_Foot"

# Base ring
bpy.ops.mesh.primitive_torus_add(
    major_segments=24, minor_segments=8,
    location=(0.4, 0.02, 0.0),
    major_radius=0.09, minor_radius=0.01
)
base_ring = bpy.context.active_object
base_ring.name = "Harp_Base_Ring"

print("[base] created")

# ============================================================
# 7. AAA MATERIALS
# ============================================================

def create_wood_material(name, base_color, grain_color, roughness=0.5):
    """Procedural wood with subsurface scattering."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Subsurface Weight"].default_value = 0.15
    bsdf.inputs["Subsurface Radius"].default_value = (0.8, 0.4, 0.2)
    
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-600, 0)
    
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-400, 0)
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    
    wave = nodes.new("ShaderNodeTexWave")
    wave.location = (-200, 0)
    wave.wave_type = "BANDS"
    wave.inputs["Scale"].default_value = 15.0
    wave.inputs["Distortion"].default_value = 0.4
    links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    
    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.location = (0, 0)
    color_ramp.color_ramp.elements[0].color = (*grain_color, 1.0)
    color_ramp.color_ramp.elements[1].color = (*base_color, 1.0)
    links.new(wave.outputs["Fac"], color_ramp.inputs["Fac"])
    
    links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    
    return mat

def create_gold_material(name):
    """Metallic gold leaf."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (0.85, 0.65, 0.13, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.95
    bsdf.inputs["Roughness"].default_value = 0.2
    bsdf.inputs["Anisotropic"].default_value = 0.3
    
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat

def create_string_material(name):
    """Anisotropic nylon string."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (0.92, 0.88, 0.78, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Anisotropic"].default_value = 0.5
    
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat

# Create materials
wood_dark = create_wood_material("M_Harp_Wood_Dark", (0.35, 0.18, 0.08), (0.22, 0.11, 0.05))
wood_light = create_wood_material("M_Harp_Wood_Light", (0.50, 0.28, 0.12), (0.35, 0.18, 0.08))
gold = create_gold_material("M_Harp_Gold")
string_mat = create_string_material("M_Harp_Strings")

# Assign materials
soundboard.data.materials.append(wood_dark)
pillar.data.materials.append(wood_light)
neck.data.materials.append(wood_dark)
capitol.data.materials.append(gold)
finial.data.materials.append(gold)
foot.data.materials.append(wood_light)
base_ring.data.materials.append(gold)
for ring in [obj for obj in bpy.data.objects if "Pillar_Ring" in obj.name]:
    ring.data.materials.append(gold)
for s in strings:
    s.data.materials.append(string_mat)

print("[materials] assigned AAA materials")

# ============================================================
# 8. STUDIO LIGHTING (HDRI + 3-point + rim)
# ============================================================

bpy.ops.object.light_add(type="AREA", location=(2.5, -2.0, 3.5))
key = bpy.context.active_object
key.data.energy = 600
key.data.size = 3.0
key.data.color = (1.0, 0.95, 0.9)

bpy.ops.object.light_add(type="AREA", location=(-2.0, -1.5, 2.5))
fill = bpy.context.active_object
fill.data.energy = 300
fill.data.size = 2.5
fill.data.color = (0.9, 0.95, 1.0)

bpy.ops.object.light_add(type="AREA", location=(0, 3.0, 2.0))
rim = bpy.context.active_object
rim.data.energy = 500
rim.data.size = 2.0
rim.data.color = (1.0, 0.9, 0.8)

bpy.ops.object.light_add(type="AREA", location=(0, 0, 4))
ambient = bpy.context.active_object
ambient.data.energy = 200
ambient.data.size = 5.0
ambient.data.color = (0.85, 0.88, 0.95)

print("[lighting] studio 3-point + rim setup")

# ============================================================
# 9. CAMERA (framing the harp properly)
# ============================================================

harp_center = Vector((0.1, 0.02, 0.9))
bpy.ops.object.camera_add(location=(1.5, -2.0, 1.2))
cam = bpy.context.active_object
cam.name = "Camera_Harp"

direction = harp_center - cam.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot_quat.to_euler()

bpy.context.scene.camera = cam
cam.data.lens = 35
cam.data.clip_end = 100

print(f"[camera] positioned at {cam.location}")

# ============================================================
# 10. RENDER SETTINGS (4K Cycles)
# ============================================================

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.render.resolution_x = 3840
scene.render.resolution_y = 2160
scene.render.resolution_percentage = 100
scene.cycles.samples = 1024
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.render.filepath = os.path.join(out_dir, "harp_grand_")
scene.render.image_settings.file_format = "PNG"
scene.world.node_tree.nodes[1].inputs[0].default_value = (0.88, 0.85, 0.78, 1.0)

print("[render] Cycles 4K, 1024 samples")

# ============================================================
# 11. JOIN ALL PARTS
# ============================================================

bpy.ops.object.select_all(action="DESELECT")
all_parts = [soundboard, pillar, neck, capitol, finial, foot, base_ring] + \
            [obj for obj in bpy.data.objects if "Pillar_Ring" in obj.name] + \
            strings
for obj in all_parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = soundboard
bpy.ops.object.join()
harp = bpy.context.active_object
harp.name = "SM_Mus_Harp_Concert_Real_Grand"

print(f"[join] final: {len(harp.data.vertices)} verts, {len(harp.data.polygons)} polys")

# ============================================================
# 12. RENDER BEAUTY
# ============================================================

bpy.ops.render.render(write_still=True)
print(f"[render] beauty -> {scene.render.filepath}0001.png")

# ============================================================
# 13. EXPORT FBX
# ============================================================

fbx_path = os.path.join(out_dir, "SM_Mus_Harp_Concert_Real_Grand.fbx")
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

print("=== Grand Concert Harp — AAA Lookdev Complete ===")
