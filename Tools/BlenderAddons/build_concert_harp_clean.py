"""Build Melusina's Concert Harp — clean triple-A bezier topology in Blender 5.2.

Each part is a separate mesh object parented to an empty — clean topology throughout.
Exports FBX with all parts.

Run: blender --factory-startup -b -P Tools/BlenderAddons/build_concert_harp_clean.py
"""
import bpy
import os

repo = "C:/EnvironmentPortfolio/BS_GodFile"
out_dir = os.path.join(repo, "Exports", "MelusinaInstruments")
os.makedirs(out_dir, exist_ok=True)

print("=== Building Concert Harp (Clean Bezier Topology) ===")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

parts = []

# === SOUNDBOARD: Extruded bezier curve ===
bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
sb = bpy.context.active_object
sb.name = "Harp_Soundboard"

spline = sb.data.splines[0]
spline.type = "BEZIER"
spline.bezier_points.add(count=3)
pts = spline.bezier_points
pts[0].co = (0, 0, 0)
pts[1].co = (0.12, 0, 0.45)
pts[2].co = (0.20, 0, 0.95)
pts[3].co = (0.24, 0, 1.55)

sb.data.extrude = 0.06
sb.data.bevel_depth = 0.005
sb.data.bevel_resolution = 2

bpy.context.view_layer.objects.active = sb
sb.select_set(True)
bpy.ops.object.convert(target="MESH")
parts.append(sb)
print(f"[soundboard] created")

# === PILLAR: Bezier circle profile extruded ===
bpy.ops.curve.primitive_bezier_circle_add(location=(0.24, 0.03, 0))
pil = bpy.context.active_object
pil.name = "Harp_Pillar"
pil.data.extrude = 1.75
pil.data.bevel_depth = 0.002

bpy.context.view_layer.objects.active = pil
pil.select_set(True)
bpy.ops.object.convert(target="MESH")
parts.append(pil)
print(f"[pillar] created")

# === NECK: Bezier curve with bevel ===
bpy.ops.curve.primitive_bezier_curve_add(location=(0.24, 0.03, 1.75))
neck = bpy.context.active_object
neck.name = "Harp_Neck"

spline = neck.data.splines[0]
spline.type = "BEZIER"
spline.bezier_points.add(count=4)
pts = spline.bezier_points
pts[0].co = (0, 0, 0)
pts[1].co = (-0.08, 0, 0.3)
pts[2].co = (-0.22, 0, 0.55)
pts[3].co = (-0.42, 0, 0.72)
pts[4].co = (-0.6, 0, 0.78)

neck.data.bevel_depth = 0.035
neck.data.bevel_resolution = 6

bpy.context.view_layer.objects.active = neck
neck.select_set(True)
bpy.ops.object.convert(target="MESH")
parts.append(neck)
print(f"[neck] created")

# === STRINGS: 41 thin bezier curves ===
for i in range(41):
    t = i / 40.0
    length = 0.4 + t * 1.1
    y_pos = -0.08 + t * 0.16
    
    bpy.ops.curve.primitive_bezier_curve_add(location=(0.05, y_pos, 0.05))
    string = bpy.context.active_object
    string.name = f"Harp_String_{i:02d}"
    
    spline = string.data.splines[0]
    spline.type = "BEZIER"
    p = spline.bezier_points
    p[0].co = (0, 0, 0)
    p[1].co = (-0.5 - t * 0.1, 0, length)
    
    string.data.bevel_depth = 0.002
    string.data.bevel_resolution = 2
    
    bpy.context.view_layer.objects.active = string
    string.select_set(True)
    bpy.ops.object.convert(target="MESH")
    parts.append(string)

print(f"[strings] created 41 strings")

# === EXPORT as multi-mesh FBX ===
bpy.ops.object.select_all(action="SELECT")
for p in parts:
    p.select_set(True)

# Parent all to empty
bpy.ops.object.empty_add(type="ARROWS", location=(0, 0, 0))
empty = bpy.context.active_object
empty.name = "SM_Mus_Harp_Concert_Real"

for p in parts:
    p.parent = empty

fbx_path = os.path.join(out_dir, "SM_Mus_Harp_Concert_Real.fbx")
bpy.ops.object.select_all(action="SELECT")

bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=True,
    use_mesh_modifiers=True,
    apply_scale_options="FBX_SCALE_ALL",
    mesh_smooth_type="FACE",
)
print(f"[export] FBX -> {fbx_path}")

# Verify
total_verts = sum(len(p.data.vertices) for p in parts if p.type == "MESH")
total_polys = sum(len(p.data.polygons) for p in parts if p.type == "MESH")
print(f"[verify] total: {total_verts} verts, {total_polys} polys across {len(parts)} parts")
print("=== Concert Harp build complete ===")
