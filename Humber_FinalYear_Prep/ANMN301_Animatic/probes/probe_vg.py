"""Is the Melusina mesh actually bound to the rig?

PROVEN ALREADY: rotating c_arm_fk_l / c_arm_fk_r leaves the world-space X extent
of every mesh byte-for-byte identical (`BONES_DO_NOTHING`). So the pose dict is
not the problem - the bones do not reach the geometry.

Two candidate causes, and they need different fixes:
  (a) the mesh has vertex groups but they are all weight 0 / empty, so the
      Armature modifier deforms nothing;
  (b) there are no vertex groups at all, and the modifier is a no-op.

Prints the numbers for both rather than assuming.
"""
import bpy

bpy.ops.wm.open_mainfile(
    filepath=r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep"
             r"\ANMN301_Animatic\proxy\SHOREWAKE_proxy_v02_storyboard.blend")
sc = bpy.context.scene
arm = [o for o in sc.objects if o.type == 'ARMATURE'][0]
bonenames = {b.name for b in arm.data.bones}

for m in [o for o in sc.objects
          if o.type == 'MESH' and any(x.type == 'ARMATURE' for x in o.modifiers)]:
    mod = [x for x in m.modifiers if x.type == 'ARMATURE'][0]
    print("VG %-14s mod.object=%s vgroups=%d verts=%d"
          % (m.name, mod.object.name if mod.object else None,
             len(m.vertex_groups), len(m.data.vertices)))
    vgnames = {g.name for g in m.vertex_groups}
    print("VG   vgroups matching bone names: %d / %d vgroups"
          % (len(vgnames & bonenames), len(vgnames)))
    if not m.vertex_groups:
        print("VG   NO_VERTEX_GROUPS -> modifier is a no-op")
        continue
    total_weighted = 0
    zero_weight_groups = 0
    for g in m.vertex_groups:
        n = 0
        for v in m.data.vertices:
            for ge in v.groups:
                if ge.group == g.index and ge.weight > 0.0:
                    n += 1
        if n == 0:
            zero_weight_groups += 1
        total_weighted += n
    print("VG   verts with weight>0 across all groups: %d" % total_weighted)
    print("VG   groups with ZERO weighted verts: %d / %d"
          % (zero_weight_groups, len(m.vertex_groups)))
    if total_weighted == 0:
        print("VG   BINDING_ABSENT -> pose cannot move this mesh")
    else:
        print("VG   binding present")