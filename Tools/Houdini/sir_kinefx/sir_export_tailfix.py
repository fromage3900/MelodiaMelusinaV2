"""Sir Melodious v5 tailfix export (Blender 5.2 headless, staging only).

Owner-directed 2026-10-07: the 657 tail verts of SirMelodiousBody that ship
ZERO-weighted in the v5 UE export (their only real groups are ARP bend
helpers + unit groups, which the ARP exporter drops) are rebuilt here AT THE
SOURCE, then re-exported through the same ARP panel the v4/v5/v6 exports
used.

Method (hython-verified 2026-10-07):
  * the export's 66-bone set is read from the v5 FBX itself (no hardcoded
    bone list);
  * a source vertex is in the fix set when its total weight to exported
    bones < 1e-6 (Blender pass + hython pass: exactly 657 of 3892);
  * ARP bend helpers are mapped to their exported equivalents:
    c_root_bend.x -> root.x, c_spine_01_bend.x -> spine_01.x,
    c_spine_02_bend.x -> spine_02.x, c_waist_bend.x -> spine_01.x;
  * unit groups (Group / Group.001 / featherdirectionj) are left untouched
    (they never export; removing them would be an unneeded edit);
  * weights are top-4 clamped and normalised.

Outputs (staging only, nothing in Content/, nothing overwritten):
  arp/SirMelodious_ARP_CrestTie_v5_tailfix.blend   (edited copy of v5)
  exports/ue_arp/SKM_SirMelodious_ARP_CrestTie_v5_tailfix.fbx
  reweight/tailfix_export_report.json

2026-10-08 two-pass note: the ORIGINAL recorded run applied the fix + saved
the blend, then failed the export step because the factory reset above unloads
the ARP user extension (`sc.arp_engine_type` AttributeError); the FBX was
exported by sir_export_tailfix_fbx.py opening the SAVED blend directly. This
file now reloads ARP after the reset so one run can complete end-to-end.

  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" \
      --background --python Tools/Houdini/sir_kinefx/sir_export_tailfix.py
"""
import addon_utils
import bpy
import json
import os
import shutil
import traceback

REPO = r"C:/EnvironmentPortfolio/BS_GodFile"
AUDIT = REPO + "/Saved/Audit/SirMelodious_FlightUnit_20261003"
SRC_BLEND = AUDIT + "/arp/SirMelodious_ARP_CrestTie_v5.blend"
OUT_BLEND = AUDIT + "/arp/SirMelodious_ARP_CrestTie_v5_tailfix.blend"
V5_FBX = AUDIT + "/exports/ue_arp/SKM_SirMelodious_ARP_CrestTie_v5.fbx"
OUT_FBX = AUDIT + "/exports/ue_arp/SKM_SirMelodious_ARP_CrestTie_v5_tailfix.fbx"
OUT_DIR = REPO + "/Saved/Audit/sirmelodious_kinefx_doctor/reweight"
REPORT = OUT_DIR + "/tailfix_export_report.json"

HELPER_MAP = {
    "c_root_bend.x": "root.x",
    "c_spine_01_bend.x": "spine_01.x",
    "c_spine_02_bend.x": "spine_02.x",
    "c_waist_bend.x": "spine_01.x",
}
RIG_NAME = "SirMelodious_rig"
MAX_INF = 4


def ensure_arp():
    """Reload the ARP user extension when it is not in this session (the
    factory reset unloads it). Pattern proven by sir_export_tailfix_fbx.py."""
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


rep = {"schema": "melodia.sir_tailfix_export.v1", "status": "EXCEPTION",
       "src_blend": SRC_BLEND, "out_blend": OUT_BLEND, "out_fbx": OUT_FBX,
       "meshes": {}}

try:
    # --- 1) exported bone set from the v5 export itself -----------------------
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ensure_arp()  # the reset unloads the ARP extension; bring it back
    bpy.ops.import_scene.fbx(filepath=V5_FBX)
    rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    exportable = set(b.name for b in rig.data.bones)
    rep["exportable_bones"] = len(exportable)

    # --- 2) edit a COPY of the source blend -----------------------------------
    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    shutil.copy2(SRC_BLEND, OUT_BLEND)
    bpy.ops.wm.open_mainfile(filepath=OUT_BLEND)
    rep["source_blend"] = True

    rig = bpy.data.objects.get(RIG_NAME)
    if rig is None:
        raise RuntimeError("rig %s not found in source blend" % RIG_NAME)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"
              and any(m.type == "ARMATURE" and m.object == rig
                      for m in o.modifiers)]
    rep["mesh_count"] = len(meshes)

    for o in meshes:
        vg = o.vertex_groups
        fix = {}
        for v in o.data.vertices:
            exp_sum = 0.0
            mapped = {}
            for g in v.groups:
                gname = vg[g.group].name
                if gname in exportable:
                    exp_sum += g.weight
                elif gname in HELPER_MAP:
                    tgt = HELPER_MAP[gname]
                    if tgt in exportable:
                        mapped[tgt] = mapped.get(tgt, 0.0) + g.weight
            if exp_sum < 1e-6:
                # even a vert with no mapped help is recorded; fallback below
                fix[v.index] = mapped
        fallback = 0
        for i, weights in fix.items():
            if not weights:
                weights = {"root.x": 1.0}
                fallback += 1
            # remove any existing bend-helper influence on this vert only
            for hs in HELPER_MAP:
                if hs in vg:
                    vg[hs].remove([i])
            items = sorted(weights.items(), key=lambda kv: -kv[1])[:MAX_INF]
            s = sum(w for _, w in items) or 1.0
            for name, w in items:
                target = vg.get(name) or vg.new(name=name)
                target.add([i], w / s, "REPLACE")
        # recount after the edit
        still = 0
        for v in o.data.vertices:
            if sum(g.weight for g in v.groups
                   if vg[g.group].name in exportable) < 1e-6:
                still += 1
        rep["meshes"][o.name] = {"fixed": len(fix), "fallback_root": fallback,
                                 "still_zero_exportable": still}

    total_fixed = sum(m["fixed"] for m in rep["meshes"].values())
    total_still = sum(m["still_zero_exportable"] for m in rep["meshes"].values())
    rep["fixed_total"] = total_fixed
    rep["still_zero_total"] = total_still
    if total_still != 0:
        raise RuntimeError("post-edit zero-exportable verts remain: %d" % total_still)

    # --- 3) save the fixed blend ----------------------------------------------
    old = bpy.data.actions.get("SirMelodious_rigAction")
    if old:
        bpy.data.actions.remove(old)
    if rig.animation_data:
        rig.animation_data.action = None
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    rep["blend_saved"] = os.path.exists(OUT_BLEND)

    # --- 4) ARP export, same panel/settings as arp_export_headless.py ---------
    sc = bpy.context.scene
    if not ensure_arp():
        # Fix + blend save above already succeeded; record the skip instead of
        # failing the run. Export-only pass: sir_export_tailfix_fbx.py.
        rep["arp_export_skipped"] = "arp_unavailable_after_factory_reset"
        rep["status"] = "FIXED_NO_FBX"
    else:
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

os.makedirs(OUT_DIR, exist_ok=True)
json.dump(rep, open(REPORT, "w"), indent=1)
print("__SIR_TAILFIX__" + json.dumps({"status": rep.get("status"),
                                      "fixed": rep.get("fixed_total"),
                                      "still": rep.get("still_zero_total"),
                                      "fbx_mb": rep.get("fbx_mb")}))
