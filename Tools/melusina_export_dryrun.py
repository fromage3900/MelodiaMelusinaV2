"""H9 dry run: ARP Unreal FBX export of contract parts into a staging folder. Never saves the blend.

Usage: blender -b <working.blend> --python Tools/melusina_export_dryrun.py -- [part ...]
"""
import bpy, json, os, sys

CONTRACT = "C:/EnvironmentPortfolio/BS_GodFile/Tools/melusina_export_contract.json"
STAGE = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Staging/MelusinaExport_20260925/"

c = json.load(open(CONTRACT))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
parts = argv or ["body", "skirt"]
os.makedirs(STAGE, exist_ok=True)
scn = bpy.context.scene
scn.arp_engine_type = "UNREAL"
print(f"ARP_SETTINGS units_x100={scn.arp_units_x100} global_scale={scn.arp_global_scale} unit_scale={scn.unit_settings.scale_length}")
scn.arp_units_x100 = True  # UE expects cm; the reference V2 exports were x100
scn.unit_settings.scale_length = 1.0  # ARP skips x100 unless unit scale is 1.0 (in-memory; blend never saved)
# SK_Melusina_Skeleton keeps ARP names (root_x, neck_x, index1_base_l); Mannequin mode renames/reparents.
print("ARP_NAMING", {k: getattr(scn, k) for k in ("arp_export_rig_type", "arp_ue4", "arp_rename_for_ue",
      "arp_mannequin_axes", "arp_ge_export_metacarp", "arp_full_facial", "arp_keep_bend_bones")})
scn.arp_export_rig_type = "UNIVERSAL"
scn.arp_ue4 = False
scn.arp_rename_for_ue = True
scn.arp_ge_export_metacarp = True
rig = bpy.data.objects[c["rig"]]
report = {}
for part in parts:
    objs = [bpy.data.objects[n] for n in c["parts"][part]["objects"] if n in bpy.data.objects]
    missing = [n for n in c["parts"][part]["objects"] if n not in bpy.data.objects]
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in [rig] + objs:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = rig
    path = STAGE + f"SK_Melusina_V2_{part.capitalize()}.fbx"
    try:
        res = bpy.ops.arp.arp_export_fbx_panel("EXEC_DEFAULT", filepath=path)
        ok = "FINISHED" in res and os.path.exists(path)
    except Exception as e:  # report, keep going
        res, ok = str(e), False
    report[part] = {"ok": ok, "result": str(res), "missing": missing,
                    "bytes": os.path.getsize(path) if os.path.exists(path) else 0}
    print(f"EXPORT {part} {report[part]}")
json.dump(report, open(STAGE + "dryrun_report.json", "w"), indent=1)
print("DRYRUN_DONE")
sys.stdout.flush(); os._exit(0)  # ARP leaves threads that hang -b exit
