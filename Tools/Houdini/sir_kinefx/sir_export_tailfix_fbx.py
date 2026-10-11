"""Sir v5 tailfix FBX export-only pass (Blender 5.2 headless).

The weight fix + blend save already happened (tailfix_export_report.json:
657 fixed, 0 still zero-exportable, blend saved). That run's ARP panel call
failed because `read_factory_settings` had unloaded the user extension
mid-session. This pass opens the SAVED fixed blend directly (no factory
reset) and re-runs the same ARP export panel.

  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" \
      --background --python Tools/Houdini/sir_kinefx/sir_export_tailfix_fbx.py
"""
import bpy
import addon_utils
import json
import os
import traceback

REPO = r"C:/EnvironmentPortfolio/BS_GodFile"
AUDIT = REPO + "/Saved/Audit/SirMelodious_FlightUnit_20261003"
FIXED_BLEND = AUDIT + "/arp/SirMelodious_ARP_CrestTie_v5_tailfix.blend"
OUT_FBX = AUDIT + "/exports/ue_arp/SKM_SirMelodious_ARP_CrestTie_v5_tailfix.fbx"
REPORT = REPO + "/Saved/Audit/sirmelodious_kinefx_doctor/reweight/tailfix_export_fbx_report.json"

rep = {"schema": "melodia.sir_tailfix_export_fbx.v1", "status": "EXCEPTION"}


def ensure_arp():
    if hasattr(bpy.types.Scene, "arp_engine_type"):
        return True
    for mod in ("bl_ext.user_default.auto_rig_pro", "auto_rig_pro"):
        try:
            addon_utils.enable(mod, default_set=False, persistent=False)
        except Exception:
            continue
        if hasattr(bpy.types.Scene, "arp_engine_type"):
            return True
    return False


try:
    if not os.path.exists(FIXED_BLEND):
        raise RuntimeError("fixed blend missing: %s" % FIXED_BLEND)
    bpy.ops.wm.open_mainfile(filepath=FIXED_BLEND)
    rep["arp_loaded"] = ensure_arp()
    rep["scene_has_arp"] = hasattr(bpy.types.Scene, "arp_engine_type")
    if not rep["scene_has_arp"]:
        raise RuntimeError("ARP panel unavailable in this session")

    rig = bpy.data.objects["SirMelodious_rig"]
    meshes = [o for o in bpy.data.objects if o.type == "MESH"
              and any(m.type == "ARMATURE" and m.object == rig
                      for m in o.modifiers)]
    rep["mesh_count"] = len(meshes)

    sc = bpy.context.scene
    sc.arp_engine_type = "UNREAL"
    sc.arp_export_rig_type = "UNIVERSAL"
    sc.arp_ge_sel_only = True
    sc.arp_global_scale = 1.0

    for o in bpy.data.objects:
        try:
            o.hide_set(False)
            o.hide_viewport = False
        except Exception:
            pass
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in meshes + [rig]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = rig

    sc.arp_bake_anim = False
    sc.arp_ge_fp = OUT_FBX
    r = bpy.ops.arp.arp_export_fbx_panel("EXEC_DEFAULT", filepath=OUT_FBX)
    rep["arp_ret"] = list(r)
    rep["fbx"] = os.path.exists(OUT_FBX)
    rep["fbx_mb"] = round(os.path.getsize(OUT_FBX) / 1e6, 2) if os.path.exists(OUT_FBX) else 0
    rep["status"] = "DONE"
except Exception:
    rep["trace"] = traceback.format_exc()[-2500:]

json.dump(rep, open(REPORT, "w"), indent=1)
print("__SIR_TAILFIX_FBX__" + json.dumps({"status": rep.get("status"),
                                          "fbx": rep.get("fbx"),
                                          "mb": rep.get("fbx_mb")}))
