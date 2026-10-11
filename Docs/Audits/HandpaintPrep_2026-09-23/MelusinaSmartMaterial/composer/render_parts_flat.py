"""Flat-color-per-part render: identify which mesh object is which body part.

Melodia / Melusina only. No Grok*.
"""
import bpy
import sys
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
fbx, outpath = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)

PALETTE = [(1, 0, 0), (0, 1, 0), (0.15, 0.3, 1), (1, 0.85, 0),
           (1, 0, 1), (0, 1, 1), (1, 0.5, 0), (0.5, 0, 1)]
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for i, ob in enumerate(meshes):
    mat = bpy.data.materials.new("flat_%d" % i)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = tuple(PALETTE[i % len(PALETTE)]) + (1,)
    emit.inputs["Strength"].default_value = 1.0
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    print("PART %d = %s -> %s" % (i, ob.name, PALETTE[i % len(PALETTE)]))

lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
for ob in meshes:
    for c in ob.bound_box:
        w = ob.matrix_world @ Vector(c)
        lo = Vector((min(lo[j], w[j]) for j in range(3)))
        hi = Vector((max(hi[j], w[j]) for j in range(3)))
center = (lo + hi) / 2
size = max((hi - lo).length, 1e-3)

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
direction = Vector((0.9, -1.0, 0.45)).normalized()
cam.location = center + direction * size * 1.35
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

scn = bpy.context.scene
scn.render.engine = "CYCLES"
try:
    scn.cycles.device = "CPU"
    scn.cycles.samples = 16
    scn.cycles.use_denoising = False
except Exception:
    pass
scn.view_settings.view_transform = "Standard"
scn.render.resolution_x = 512
scn.render.resolution_y = 512
scn.render.image_settings.file_format = "PNG"
scn.render.filepath = outpath
bpy.ops.render.render(write_still=True)
print("done:", outpath)
