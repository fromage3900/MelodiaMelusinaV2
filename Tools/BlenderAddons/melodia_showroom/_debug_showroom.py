import bpy, math, mathutils

showroom_dir = "C:/EnvironmentPortfolio/BS_GodFile/Tools/MelodiaProceduralStudio/GeneratedScenes/showroom"
out_obj = showroom_dir + "/terrain.obj"

# import OBJ manually via bmesh to avoid operator
import bmesh
from bpy_extras.io_utils import ImportHelper

mesh = bpy.data.meshes.new("Terrain")
obj = bpy.data.objects.new("Showroom_Terrain", mesh)
bpy.context.collection.objects.link(obj)

verts = []
faces = []
colors = []
with open(out_obj, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "v":
            x = float(parts[1])
            y = float(parts[2])
            z = float(parts[3])
            verts.append((x, y, z))
            if len(parts) >= 7:
                colors.append((float(parts[4]), float(parts[5]), float(parts[6]), 1.0))
            else:
                colors.append((0.5, 0.5, 0.5, 1.0))
        elif parts[0] == "f":
            idxs = [int(p.split("/")[0]) - 1 for p in parts[1:]]
            faces.append(idxs)

bm = bmesh.new()
for v in verts:
    bm.verts.new(v)
bm.verts.ensure_lookup_table()
for f in faces:
    try:
        bm.faces.new([bm.verts[i] for i in f])
    except Exception:
        pass
bm.to_mesh(mesh)
bm.free()
mesh.update()

if colors:
    attr = mesh.color_attributes.new(name="AuraColor", type='FLOAT_COLOR', domain='CORNER')
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            vidx = mesh.loops[loop_idx].vertex_index
            if vidx < len(colors):
                attr.data[loop_idx].color = colors[vidx]

# compute bounds
world_coords = [obj.matrix_world @ mathutils.Vector(v) for v in verts]
xs = [v.x for v in world_coords]
ys = [v.y for v in world_coords]
zs = [v.z for v in world_coords]
print("BOUNDS_X=" + str(min(xs)) + "," + str(max(xs)))
print("BOUNDS_Y=" + str(min(ys)) + "," + str(max(ys)))
print("BOUNDS_Z=" + str(min(zs)) + "," + str(max(zs)))

centre = mathutils.Vector(((min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2))
size = mathutils.Vector((max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)))
span = max(size)
print("CENTRE=" + str(centre))
print("SIZE=" + str(size))
print("SPAN=" + str(span))

# camera placement like _frame_scene
cam_data = bpy.data.cameras.new("SR_Camera")
cam_data.lens = 50
cam_data.clip_end = span * 20
cam = bpy.data.objects.new("SR_Camera", cam_data)
bpy.context.collection.objects.link(cam)

fov = 2 * math.atan((cam_data.sensor_width * 0.5) / cam_data.lens)
dist = (max(size.x, size.z * 1.4) * 0.5) / math.tan(fov * 0.5) * 1.25
cam.location = (centre.x - span * 0.28, centre.y - dist * 0.82, centre.z + span * 0.42)
direction = centre - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam
print("CAM=" + str(cam.location))
print("CAM_ROT=" + str(cam.rotation_euler))

# lights
unit = span * span
for name, energy, colour, loc in (
    ("SR_Key", unit * 2.2, (1.0, 0.94, 0.86), (centre.x + span * 0.6, centre.y - span * 0.75, centre.z + span * 0.7)),
    ("SR_Fill", unit * 0.55, (0.62, 0.75, 1.0), (centre.x - span * 0.8, centre.y - span * 0.5, centre.z + span * 0.25)),
    ("SR_Rim", unit * 1.5, (1.0, 0.55, 0.85), (centre.x, centre.y + span * 0.85, centre.z + span * 0.55)),
    ("SR_Back", unit * 0.8, (0.85, 0.85, 0.90), (centre.x, centre.y + span * 1.1, centre.z + span * 0.2)),
):
    data = bpy.data.lights.new(name, type='AREA')
    data.energy = energy
    data.color = colour
    data.size = span * 0.55
    o = bpy.data.objects.new(name, data)
    o.location = loc
    bpy.context.collection.objects.link(o)
    d = centre - mathutils.Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

# material via color attribute
mat = bpy.data.materials.new("M_ShowroomAura")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial')
bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
col = nt.nodes.new('ShaderNodeVertexColor')
col.layer_name = "AuraColor"
lum = nt.nodes.new('ShaderNodeRGBToBW')
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.45
ramp.color_ramp.elements[1].position = 0.95
nt.links.new(col.outputs['Color'], bsdf.inputs['Base Color'])
nt.links.new(col.outputs['Color'], lum.inputs['Color'])
nt.links.new(lum.outputs['Val'], ramp.inputs['Fac'])
if 'Emission Color' in bsdf.inputs:
    nt.links.new(col.outputs['Color'], bsdf.inputs['Emission Color'])
if 'Emission Strength' in bsdf.inputs:
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Emission Strength'])
nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
obj.data.materials.append(mat)

# render scene
scene = bpy.context.scene
scene.render.filepath = showroom_dir + "/debug_showroom.png"
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.render.film_transparent = False
bpy.ops.render.render(write_still=True)
print("RENDER_WRITTEN=" + scene.render.filepath)
