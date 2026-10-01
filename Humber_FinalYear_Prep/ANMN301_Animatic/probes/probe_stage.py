"""What is actually being RENDERED as the character?

Measured so far:
  * the bone matrix DOES rotate (row0 = 0.9895, 0.1419 after a 1.4 rad Z turn)
  * EXPORT_Body does not move a single vertex - mean identical to 5 dp
  * the binding is intact (164/164 groups, 55852 weighted verts, 0 empty)
  * EXPORT_Body xspan is only 0.46 wide against a 2.0 zspan

That combination means the rendered character is probably NOT EXPORT_Body. The
panels show an untextured white mannequin; a rigged, textured Melusina would not
look like that. This enumerates every mesh in the stage blend with its size, so
the actual subject is identified by measurement instead of assumption.
"""
import bpy

bpy.ops.wm.open_mainfile(
    filepath=r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep"
             r"\ANMN301_Animatic\proxy\SHOREWAKE_proxy_v30_perch.blend")
sc = bpy.context.scene

print("STAGE objects=%d" % len(sc.objects))
for o in sc.objects:
    if o.type == 'MESH':
        d = o.dimensions
        print("STAGE mesh %-22s verts=%-6d dims=%s parent=%s"
              % (o.name, len(o.data.vertices),
                 [round(v, 2) for v in d], o.parent.name if o.parent else None))
        mods = [(m.type, getattr(m, 'object', None).name
                 if getattr(m, 'object', None) else None) for m in o.modifiers]
        if mods:
            print("STAGE      modifiers=%s" % mods)
        print("STAGE      materials=%s"
              % [ms.material.name if ms.material else None
                 for ms in o.material_slots][:4])
    elif o.type == 'ARMATURE':
        print("STAGE armature %-18s bones=%d" % (o.name, len(o.data.bones)))
    elif o.type == 'CAMERA':
        print("STAGE camera   %-18s loc=%s"
              % (o.name, [round(v, 2) for v in o.location]))

# Which mesh is closest to a human-scale figure near the hull?
print("STAGE --- human-scale candidates (0.5 < height < 3.0) ---")
for o in sc.objects:
    if o.type != 'MESH':
        continue
    h = o.dimensions.z
    if 0.5 < h < 3.0:
        print("STAGE CANDIDATE %-22s h=%.2f w=%.2f d=%.2f verts=%d"
              % (o.name, h, o.dimensions.x, o.dimensions.y,
                 len(o.data.vertices)))