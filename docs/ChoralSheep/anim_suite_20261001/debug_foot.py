"""Debug foot tracking on SK_Sheep_Walk: is the foot-vertex selection right, and does
the foot actually swing forward/back relative to the body? Read-only."""
import os

import bpy
import numpy as np

SRC = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\choralsheep_Takes_v4_20260910.blend"
bpy.ops.wm.open_mainfile(filepath=SRC, load_ui=False)
sc = bpy.context.scene
rig = max((o for o in sc.objects if o.type == "ARMATURE"), key=lambda o: len(o.data.bones))
body = max((o for o in sc.objects if o.type == "MESH" and len(o.vertex_groups) > 10),
           key=lambda o: len(o.data.vertices))
print("BODY", body.name, flush=True)

# what do the foot-ish vertex groups look like?
vg_names = {g.index: g.name for g in body.vertex_groups}
footish = sorted(n for n in vg_names.values() if "foot" in n.lower() or "toe" in n.lower())
print("FOOTISH_GROUPS", footish, flush=True)

# dominant-group foot masks
dom = ["" for _ in body.data.vertices]
for v in body.data.vertices:
    if v.groups:
        dom[v.index] = vg_names[max(v.groups, key=lambda g: g.weight).group]
for label, pat in (("foot_l", lambda g: g.startswith(("foot", "toes")) and "l" in g.lower()),
                   ("foot_r", lambda g: g.startswith(("foot", "toes")) and "r" in g.lower()),
                   ("any_foot", lambda g: g.startswith(("foot", "toes")))):
    m = np.array([pat(g) for g in dom])
    print("MASK", label, "verts=%d" % int(m.sum()), flush=True)

# deform foot bones
deform_feet = [b.name for b in rig.data.bones if b.use_deform and ("foot" in b.name.lower() or "toe" in b.name.lower())]
print("DEFORM_FOOT_BONES", deform_feet, flush=True)


def ev():
    rig.update_tag()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    e = body.evaluated_get(dg)
    me = e.to_mesh()
    m = len(me.vertices)
    a = np.empty(m * 3)
    me.vertices.foreach_get("co", a)
    e.to_mesh_clear()
    return a.reshape(m, 3)


act = bpy.data.actions["SK_Sheep_Walk"]
rig.animation_data.action = act
any_foot = np.array([g.startswith(("foot", "toes")) for g in dom])
body_fwd = []
foot_fwd = []
bone_fwd = []
fb = rig.pose.bones.get(deform_feet[0]) if deform_feet else None
for f in range(0, 65, 4):
    sc.frame_set(f)
    a = ev()
    body_fwd.append(float(a[:, 1].mean()))
    foot_fwd.append(float(a[any_foot, 1].mean()))
    if fb is not None:
        bone_fwd.append(float((rig.matrix_world @ fb.matrix @ __import__("mathutils").Vector((0, 0, 0))).y))
print("FRAME bodyY footY boneY", flush=True)
for i, f in enumerate(range(0, 65, 4)):
    print(f, round(body_fwd[i] * 100, 2), round(foot_fwd[i] * 100, 2),
          (round(bone_fwd[i] * 100, 2) if bone_fwd else "-"), flush=True)
print("FOOT_Y_RANGE_cm", round((max(foot_fwd) - min(foot_fwd)) * 100, 2), flush=True)
print("BODY_Y_RANGE_cm", round((max(body_fwd) - min(body_fwd)) * 100, 2), flush=True)
os._exit(0)
