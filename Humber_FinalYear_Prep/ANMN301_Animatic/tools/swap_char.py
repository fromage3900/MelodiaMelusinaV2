"""Swap the untextured EXPORT_* character for the canonical rigged Melusina.

Reads the animatic working scene, removes the grey FBX-round-trip character,
appends character_rig + its meshes from the extracted canonical blend, aligns
it to the exact volume the grey one occupied, and renders shot 11 from
CAM_Intimate for comparison.

Writes a NEW file. Never touches the working scene.
"""
import bpy, os, math
from mathutils import Vector

ROOT = r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic"
CHAR = os.path.join(ROOT, "proxy", "MELUSINA_CHARACTER_rig43.blend")
OUT  = os.path.join(ROOT, "proxy", "SHOREWAKE_swap_test.blend")
CMP  = r"C:\Users\brenn\AppData\Local\Temp\animcheck\swap_canonical.png"

GREY = ("EXPORT_Body", "EXPORT_Shirt", "EXPORT_Skirt", "EXPORT_Boots")

def world_bounds(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ev.to_mesh_clear()
    return lo, hi

# ---- 1. record the target volume from the grey body BEFORE deleting it
grey = bpy.data.objects.get("EXPORT_Body")
lo0, hi0 = world_bounds(grey)
ctr0 = (lo0 + hi0) * 0.5
h0 = hi0.z - lo0.z
print("SWAP target lo=%s hi=%s height=%.4f" % (
    tuple(round(v,3) for v in lo0), tuple(round(v,3) for v in hi0), h0))

# ---- 2. remove the grey character
for n in GREY + ("MelusinaRig",):
    o = bpy.data.objects.get(n)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
print("SWAP grey removed")

# ---- 3. append the canonical character
with bpy.data.libraries.load(CHAR, link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
print("SWAP appending %d objects" % len(dst.objects))
rig = None
added = []
for o in dst.objects:
    if o is None:
        continue
    bpy.context.scene.collection.objects.link(o)
    added.append(o)
    if o.type == 'ARMATURE' and o.name == 'character_rig':
        rig = o
print("SWAP appended:", len(added), "rig:", rig.name if rig else None)
if rig is None:
    for o in added:
        if o.type == 'ARMATURE':
            rig = o
            print("SWAP fallback rig:", rig.name)
            break

# ---- 4. measure the canonical character in its own space
body = bpy.data.objects.get("Melusina")
lo1, hi1 = world_bounds(body)
ctr1 = (lo1 + hi1) * 0.5
h1 = hi1.z - lo1.z
print("SWAP canonical lo=%s hi=%s height=%.4f" % (
    tuple(round(v,3) for v in lo1), tuple(round(v,3) for v in hi1), h1))

# ---- 5. rotate 90 about Z (canonical X<->Y vs animatic), scale to target height
s = h0 / h1
rig.rotation_euler = (0.0, 0.0, math.radians(90.0))
rig.scale = (s, s, s)
bpy.context.view_layer.update()
print("SWAP applied rot=90Z scale=%.5f" % s)

# ---- 6. snap: feet to target feet, x/y centred on the grey character
lo2, hi2 = world_bounds(body)
ctr2 = (lo2 + hi2) * 0.5
delta = Vector((ctr0.x - ctr2.x, ctr0.y - ctr2.y, lo0.z - lo2.z))
rig.location = rig.location + delta
bpy.context.view_layer.update()
print("SWAP delta applied:", tuple(round(v,4) for v in delta))

# ---- 7. verify
lo3, hi3 = world_bounds(body)
print("SWAP final lo=%s hi=%s size=%s" % (
    tuple(round(v,3) for v in lo3), tuple(round(v,3) for v in hi3),
    tuple(round(v,3) for v in (hi3-lo3))))
print("SWAP target was size=%s" % (tuple(round(v,3) for v in (hi0-lo0)),))

# ---- 8. render shot 11's camera
scn = bpy.context.scene
scn.camera = bpy.data.objects.get("CAM_Intimate") or scn.camera
scn.render.resolution_x = 960
scn.render.resolution_y = 1080
scn.render.filepath = CMP
scn.frame_set(1)
print("SWAP rendering via", scn.camera.name)
bpy.ops.render.render(write_still=True)
print("SWAP RENDER DONE ->", CMP)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SWAP SAVED ->", OUT)
print("SWAP DONE")