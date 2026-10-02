"""Quick structural probe of choral_sheep_Takes_v4_20260910.blend (read-only)."""
import os

import bpy

SRC = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\choralsheep_Takes_v4_20260910.blend"
bpy.ops.wm.open_mainfile(filepath=SRC, load_ui=False)
sc = bpy.context.scene

print("ARMATURES", [(o.name, len(o.data.bones)) for o in sc.objects if o.type == "ARMATURE"], flush=True)
print("MESHES", [(o.name, len(o.data.vertices), len(o.vertex_groups)) for o in sc.objects if o.type == "MESH"], flush=True)
for act in bpy.data.actions:
    bones = set()
    kr = []
    for l in act.layers:
        for st in l.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    kr.append(fc.keyframe_points[0].co[0])
                    kr.append(fc.keyframe_points[-1].co[0])
                    if 'pose.bones["' in fc.data_path:
                        bones.add(fc.data_path.split('pose.bones["')[1].split('"')[0])
    sample = sorted(bones)[:8]
    print("ACTION", act.name, "span=(%s,%s)" % (min(kr) if kr else None, max(kr) if kr else None),
          "bones=%d sample=%s" % (len(bones), sample), flush=True)
os._exit(0)
