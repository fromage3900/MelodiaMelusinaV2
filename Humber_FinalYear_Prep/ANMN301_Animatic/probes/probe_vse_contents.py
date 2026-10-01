import bpy, sys
bpy.ops.wm.open_mainfile(filepath=r"P:/MelodiaMelusinaV2-Laptop/Humber_FinalYear_Prep/ANMN301_Animatic/SHOREWAKE_VSE_animatic_v04.blend")
sc=bpy.context.scene
print("P2 objects=%d" % len(sc.objects))
for o in sc.objects: print("P2  ", o.type, o.name)
se = sc.sequence_editor
print("P2 sequence_editor:", se)
if se:
    for s in se.strips_all if hasattr(se,'strips_all') else se.sequences:
        try: print("P2 strip", s.name, s.frame_final_start, s.frame_final_duration, s.type)
        except Exception as e: print("P2 strip ?", e)
