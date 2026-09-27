"""Read-only: posed vs rest world matrices of character_rig bones (the extracted bust is the EVALUATED/posed mesh)."""
import bpy, json
OUT = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\ue_export_v4\melusina_pose_dump_v4.json"
ob = bpy.data.objects["character_rig"]; mw = ob.matrix_world
R = {"frame": bpy.context.scene.frame_current, "action": ob.animation_data.action.name if ob.animation_data and ob.animation_data.action else None,
     "pose_position": ob.data.pose_position, "bones": {}}
for pb in ob.pose.bones:
    b = pb.bone
    if not b.use_deform and b.name not in ("head.x", "neck.x", "c_head.x", "c_neck.x"): continue
    R["bones"][b.name] = {"rest": [list(r) for r in (mw @ b.matrix_local)], "pose": [list(r) for r in (mw @ pb.matrix)],
                          "parent": b.parent.name if b.parent else None, "deform": b.use_deform}
json.dump(R, open(OUT, "w"), indent=1)
import mathutils
def d(n):
    x = R["bones"].get(n)
    if not x: return None
    a = mathutils.Matrix(x["rest"]); p = mathutils.Matrix(x["pose"]); dl = a.inverted() @ p
    return [round(v, 4) for v in p.translation], [round(v, 4) for v in a.translation], [round(v, 2) for v in dl.to_euler()], round(dl.translation.length, 4)
for n in ("root.x", "spine_03.x", "neck.x", "head.x", "c_head.x"): print("V4UE-POSE", n, d(n))
print("V4UE-POSE n_deform", len(R["bones"]), "frame", R["frame"], "action", R["action"], R["pose_position"])
