# Applies the FULL_PLAN section-3 lighting rework + scene hygiene to the live blend.
# Backup -> edit -> save -> verify render. This is the ONE sanctioned scene edit
# (builder-style: backup first, write-open check, save, verify).
import os
import shutil
import time

import bpy
from mathutils import Vector

BLEND = r"P:/MelodiaMelusinaV2-Laptop/Saved/MelusinasHouse/FlowerBrooch.blend"
BK = r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/brooch_lab/backups"

# write-open check (the read-only-attribute lesson)
if not os.access(BLEND, os.W_OK):
    os.chmod(BLEND, 0o666)
    print("chmod 0o666 applied")

stamp = time.strftime("%Y%m%d_%H%M%S")
shutil.copy2(BLEND, os.path.join(BK, "FlowerBrooch_preScenePolish_%s.blend" % stamp))
print("backup written: preScenePolish_%s" % stamp)

scn = bpy.context.scene

# 1) delete the Lab cards, the old rim, the front fill, and the temp junk
for name in ("_LAB_panel_front", "_LAB_panel_right", "_LAB_rim", "_LAB_fill", "temp_obj"):
    ob = bpy.data.objects.get(name)
    if ob is None:
        print("skip (absent):", name)
        continue
    bpy.data.objects.remove(ob, do_unlink=True)
    print("removed:", name)

# 2) permanent matte floor
floor = bpy.data.objects.get("_LAB_floor")
if floor is None:
    import bmesh
    me = bpy.data.meshes.new("_LAB_floor")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=8)
    bm.to_mesh(me)
    bm.free()
    floor = bpy.data.objects.new("_LAB_floor", me)
    scn.collection.objects.link(floor)
    floor.location = (0, 0, -0.06)
mat = bpy.data.materials.get("_LAB_floor_mat")
if mat is None:
    mat = bpy.data.materials.new("_LAB_floor_mat")
    mat.use_nodes = True
b = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
b.inputs['Base Color'].default_value = (0.02, 0.02, 0.025, 1)
b.inputs['Roughness'].default_value = 0.9
floor.data.materials.clear()
floor.data.materials.append(mat)
print("floor set")

# 3) relight per spec
AIM = Vector((0.0, 0.0, 0.45))


def light(name, ltype, energy, loc, color, size=None):
    ld = bpy.data.lights.get(name) or bpy.data.lights.new(name, ltype)
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, ld)
    if ob.name not in scn.objects:
        scn.collection.objects.link(ob)
    ld.type = ltype
    ld.energy = energy
    ld.color = color
    if size and ltype == 'AREA':
        ld.size = size
    ob.location = loc
    ob.rotation_euler = (AIM - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return ob


light("_LAB_key", 'AREA', 200, (0.85, -1.05, 1.72), (1.0, 0.93, 0.82), 1.5)
light("_LAB_rimL", 'AREA', 320, (-0.95, 0.85, 1.05), (1.0, 0.85, 0.60), 0.35)
light("_LAB_rimR", 'SPOT', 420, (0.95, 0.85, 0.90), (0.75, 0.80, 1.00))
light("_LAB_under", 'AREA', 90, (0.4, -0.5, -0.08), (1.0, 0.95, 0.9), 0.8)
if "_LAB_spark" not in scn.objects:
    light("_LAB_spark", 'POINT', 16, (0.3, -0.4, 0.9), (1.0, 1.0, 1.0))
scn.objects["_LAB_spark"].hide_render = False
print("relit")

# 4) camera authority
scn.camera = bpy.data.objects["LAB_Cam"]

# 5) save
bpy.ops.wm.save_mainfile()
print("SAVED", bpy.data.filepath)

# 6) verify render from the scene camera
scn.render.resolution_x, scn.render.resolution_y = 1200, 900
if scn.render.engine == 'CYCLES':
    scn.cycles.samples = min(scn.cycles.samples, 64)
    scn.cycles.use_denoising = True
scn.render.filepath = r"P:/MelodiaMelusinaV2-Laptop/Saved/Audit/scene_relight_applied.png"
bpy.ops.render.render(write_still=True)
print("verify render written")
print("census:", sorted(o.name for o in scn.objects))
