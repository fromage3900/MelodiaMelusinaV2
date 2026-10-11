"""Probe the Painter-exported sheep mesh: UV layers, materials, sizes."""
import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(
    filepath=r"C:/EnvironmentPortfolio/BS_GodFile/Docs/Audits/HandpaintPrep_2026-09-23/MelusinaSmartMaterial/exports/MrSheep/mesh/choralsheep_painter_mesh.fbx")

for ob in bpy.context.scene.objects:
    if ob.type == "MESH":
        me = ob.data
        print("OBJ %r verts=%d tris=%d" % (ob.name, len(me.vertices),
                                           len(me.polygons)))
        print("   uv_layers:", [l.name for l in me.uv_layers],
              "active:", me.uv_layers.active.name if me.uv_layers.active else None)
        print("   materials:", [m.name if m else None for m in me.materials])
        if me.uv_layers:
            uv = me.uv_layers[0].data
            n = len(uv)
            sample = [uv[i].uv for i in range(0, min(n, 500), 50)]
            us = [s[0] for s in sample]
            vs = [s[1] for s in sample]
            print("   u: %.3f..%.3f  v: %.3f..%.3f  (n=%d)" %
                  (min(us), max(us), min(vs), max(vs), n))
print("PROBE-UV-DONE")
