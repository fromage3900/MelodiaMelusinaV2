"""Re-test: does rotating an arm bone move EXPORT_Body?

The earlier `BONES_DO_NOTHING` verdict measured X extent across ALL 11 meshes,
including the skiff hull, which is metres wide. An arm rotating at the shoulder
moves one limb inside that span, so min/max never changed and the test reported
a false negative. The binding probe then proved the skin is intact (164 vertex
groups, 55852 weighted verts, 0 empty groups).

This measures the BODY mesh only, and compares MEAN vertex position as well as
extent - a rotation about the shoulder changes the mean even when the span does
not.
"""
import bpy

bpy.ops.wm.open_mainfile(
    filepath=r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep"
             r"\ANMN301_Animatic\proxy\SHOREWAKE_proxy_v02_storyboard.blend")
sc = bpy.context.scene
arm = [o for o in sc.objects if o.type == 'ARMATURE'][0]
body = sc.objects.get("EXPORT_Body")


def body_verts():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    mw = body.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    if not pts:
        return None
    n = len(pts)
    return {
        "n": n,
        "mean": [round(sum(p[i] for p in pts) / n, 5) for i in range(3)],
        "xspan": (round(min(p.x for p in pts), 4), round(max(p.x for p in pts), 4)),
        "zspan": (round(min(p.z for p in pts), 4), round(max(p.z for p in pts), 4)),
    }


rest = body_verts()
print("ARM2 rest  %s" % rest)

for b, z in (("c_arm_fk_l", 1.4), ("c_arm_fk_r", -1.4)):
    arm.pose.bones[b].rotation_euler = (0.0, 0.0, z)
bpy.context.view_layer.update()
posed = body_verts()
print("ARM2 posed %s" % posed)

moved = (rest["mean"] != posed["mean"]) or (rest["xspan"] != posed["xspan"])
print("ARM2 VERDICT %s" % ("BONES_DRIVE_BODY" if moved else "BONES_DO_NOTHING"))

pb = arm.pose.bones["c_arm_fk_l"]
print("ARM2 c_arm_fk_l rotation_euler = %s"
      % [round(v, 3) for v in pb.rotation_euler])
print("ARM2 c_arm_fk_l matrix row0 = %s"
      % [round(pb.matrix[0][i], 4) for i in range(4)])
mod = [x for x in body.modifiers if x.type == 'ARMATURE'][0]
print("ARM2 modifier preserve_volume=%s show_viewport=%s show_render=%s"
      % (mod.use_deform_preserve_volume, mod.show_viewport, mod.show_render))
print("ARM2 rig show_in_front=%s hide_render=%s"
      % (arm.show_in_front, arm.hide_render))