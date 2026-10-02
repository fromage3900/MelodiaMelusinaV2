"""Extract the canonical Melusina character from FinalUERig43.blend.

Keeps: character_rig + every mesh deforming off it, plus the hair-strand
armatures and their meshes. Drops the other ~352 meshes (props, environment,
other figures). Packs every image so the result has no dependency on the dead
C:\\Users\\froma\\... paths the source file carries.

Nothing is written back to D:. Output is a new file under proxy/.
"""
import bpy, os, sys

SRC = r"D:\MelodiaMelusina\MelusinaFinalRig\FinalUERig43.blend"
OUT = r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic\proxy\MELUSINA_CHARACTER_rig43.blend"

RIG = 'character_rig'

def arm_target(o):
    for m in o.modifiers:
        if m.type == 'ARMATURE' and m.object:
            return m.object.name
    return None

# ---- 1. identify the keep set
rigs = set()
rigs.add(RIG)
for o in bpy.data.objects:
    if o.type == 'ARMATURE' and o.name.startswith('SHP_Armature'):
        rigs.add(o.name)

keep_mesh = set()
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    t = arm_target(o)
    if t in rigs:
        keep_mesh.add(o.name)
    elif o.parent and o.parent.name in rigs:
        keep_mesh.add(o.name)

# children of kept meshes that are themselves meshes (eyebrow/lash pairs)
changed = True
while changed:
    changed = False
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name not in keep_mesh and o.parent and o.parent.name in keep_mesh:
            keep_mesh.add(o.name)
            changed = True

keep_objs = set(rigs) | keep_mesh
print("EXTRACT rigs kept:", sorted(rigs))
print("EXTRACT meshes kept:", len(keep_mesh))
print("EXTRACT total objects kept:", len(keep_objs), "of", len(bpy.data.objects))

# ---- 2. delete everything else
doomed = [o for o in bpy.data.objects if o.name not in keep_objs]
print("EXTRACT deleting:", len(doomed))
for o in doomed:
    bpy.data.objects.remove(o, do_unlink=True)
print("EXTRACT objects remaining:", len(bpy.data.objects))

# ---- 3. pack every image so nothing depends on a dead path
packed = 0
for i in bpy.data.images:
    if i.source in ('FILE', 'SEQUENCE') and not i.packed_file:
        try:
            i.pack()
            packed += 1
        except Exception as e:
            print("EXTRACT pack FAILED", i.name, e)
print("EXTRACT newly packed:", packed)
still = [i.name for i in bpy.data.images if i.source in ('FILE','SEQUENCE') and not i.packed_file]
print("EXTRACT still unpacked:", len(still), still[:8])

# ---- 4. drop orphaned data
for _ in range(6):
    removed = 0
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images,
                 bpy.data.armatures, bpy.data.curves, bpy.data.node_groups,
                 bpy.data.cameras, bpy.data.lights, bpy.data.collections):
        for blk in list(coll):
            if blk.users == 0:
                coll.remove(blk)
                removed += 1
    if not removed:
        break
print("EXTRACT after purge: objects=%d meshes=%d mats=%d imgs=%d armatures=%d" % (
    len(bpy.data.objects), len(bpy.data.meshes), len(bpy.data.materials),
    len(bpy.data.images), len(bpy.data.armatures)))

# ---- 5. put the rig at world origin, standing on Z=0
rig = bpy.data.objects[RIG]
print("EXTRACT rig loc:", tuple(round(v,4) for v in rig.location),
      "rot:", tuple(round(v,4) for v in rig.rotation_euler),
      "scale:", tuple(round(v,4) for v in rig.scale))

# ---- 6. save
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("EXTRACT SAVED ->", OUT)
print("EXTRACT size:", os.path.getsize(OUT))
print("EXTRACT DONE")