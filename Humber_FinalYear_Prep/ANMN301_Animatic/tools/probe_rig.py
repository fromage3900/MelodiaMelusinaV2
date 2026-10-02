
import bpy, sys, os
print("PROBE", bpy.data.filepath)
print("  objects:", len(bpy.data.objects), " meshes:", len(bpy.data.meshes),
      " armatures:", len(bpy.data.armatures), " materials:", len(bpy.data.materials))
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        print("  ARMATURE:", o.name, "bones=", len(o.data.bones),
              "scale=", tuple(round(v,4) for v in o.scale),
              "rot=", tuple(round(v,3) for v in o.rotation_euler))
        db = [b.name for b in o.data.bones if b.use_deform]
        print("    deform bones:", len(db), db[:14])
        for b in o.data.bones:
            if b.name in ("head_x","spine_02_x","c_head_x","c_neck_x"):
                print("    BONE %-14s deform=%s" % (b.name, b.use_deform))
meshes = [o for o in bpy.data.objects if o.type=='MESH']
print("  MESH objects:", len(meshes))
for o in sorted(meshes, key=lambda x: -len(x.data.vertices))[:10]:
    mods = [(m.type, getattr(m,'object',None).name if getattr(m,'object',None) else None) for m in o.modifiers]
    print("    %-34s verts=%-7d mats=%d mods=%s" % (o.name, len(o.data.vertices), len(o.data.materials), mods))
# shaders
imgs = [i for i in bpy.data.images if i.source in ('FILE','SEQUENCE')]
print("  image textures:", len(imgs), [i.name for i in imgs[:8]])
nz = [m for m in bpy.data.materials if m.use_nodes]
print("  node materials:", len(nz), [m.name for m in nz[:10]])
