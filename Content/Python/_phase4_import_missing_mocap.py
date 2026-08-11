"""Phase 4.0: Import 8 missing FBXs as source anims + batch retarget to Melusina.
Run via MCP editor_query(run_python) in the running editor.
"""
import unreal
import os
import json
import sys

LOCAL_FBX_DIR = r"G:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap"
SRC_SKELETON = "/Game/Melodia/Mocap/Source/SK_MocapSource_Skeleton.SK_MocapSource_Skeleton"
SRC_MESH = "/Game/Melodia/Mocap/Source/SK_MocapSource.SK_MocapSource"
RTG = "/Game/Melodia/Mocap/RTG_Mocap_to_Melusina"
OUT_DIR = "/Game/Melodia/Characters/Melusina/Animations/Mocap"
REPORT = r"G:/EnvironmentPortfolio/BS_GodFile/Saved/Melodia/retarget_report_phase4.json"

# Takes we need to import (FBX name -> desired A_Src_ name)
MISSING_TAKES = [
    ("Crumping.fbx", "A_Src_Crumping"),
    ("Curtsee.fbx", "A_Src_Curtsee"),
    ("Dodge_002.fbx", "A_Src_Dodge_002"),
    ("Duck.fbx", "A_Src_Duck"),
    ("LittleDance_002.fbx", "A_Src_LittleDance_002"),
    ("RunCycle.fbx", "A_Src_RunCycle"),
    ("Stab_001.fbx", "A_Src_Stab_001"),
    ("Twirl.fbx", "A_Src_Twirl"),
]

def import_source_anim(fbx_path, dest_name):
    """Import FBX as animation on source skeleton without creating new assets."""
    # Build import task
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx_path)
    task.set_editor_property("destination_path", "/Game/Melodia/Mocap/Source/Anims")
    task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("automated", True)

    # Configure as animation-only import onto the source skeleton
    options = unreal.FbxImportUI()
    skeleton = unreal.load_asset(SRC_SKELETON)
    options.set_editor_property("skeleton", skeleton)
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_animations", True)
    # Set the source mesh reference
    src_mesh = unreal.load_asset(SRC_MESH)
    if src_mesh:
        options.set_editor_property("skeletal_mesh", src_mesh)

    task.set_editor_property("options", options)

    # Execute
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    try:
        asset_tools.import_asset_tasks([task])
        imported = task.get_editor_property("imported_object_paths")
        if imported:
            unreal.log(f"[Phase4] Imported: {imported[0]}")
            return imported[0]
        else:
            unreal.log_warning(f"[Phase4] No object paths for {dest_name}")
            return None
    except Exception as e:
        unreal.log_error(f"[Phase4] Import failed for {dest_name}: {e}")
        return None


def retarget_remaining():
    """Batch retarget only the newly imported A_Src_* files."""
    rtg = unreal.load_asset(RTG)
    sm = unreal.load_asset(SRC_MESH)
    tm = unreal.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina.SK_Melusina")

    # Ensure skeleton rebind
    tgt_skel = unreal.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton")
    try:
        bound = unreal.MelodiaAssetRepairLibrary.set_skeletal_mesh_skeleton(tm, tgt_skel)
        unreal.log(f"[Phase4] Skeleton rebind: {bound}")
    except Exception as e:
        unreal.log_warning(f"[Phase4] C++ rebind unavailable: {e}")

    # Auto-map chains
    rtgc = unreal.IKRetargeterController.get_controller(rtg)
    rtgc.auto_map_chains(unreal.AutoMapChainType.EXACT, False)
    unreal.EditorAssetLibrary.save_asset(RTG, False)

    # List only new source anims
    all_src = unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Mocap/Source/Anims", False, False)
    new_prefixes = [name for _, name in MISSING_TAKES]
    targets = [a for a in all_src if any(a.split(".")[0].endswith(p.replace("A_Src_", "")) for p in new_prefixes)]

    report = []
    for sp in targets:
        stem = sp.split("/")[-1].split(".")[0]
        unreal.log(f"[Phase4] Retargeting {sp}")
        try:
            ad = unreal.EditorAssetLibrary.find_asset_data(sp)
            inp = unreal.IKRetargetBatchOperationInputs()
            inp.set_editor_property("assets_to_retarget", [ad])
            inp.set_editor_property("source_mesh", sm)
            inp.set_editor_property("target_mesh", tm)
            inp.set_editor_property("ik_retarget_asset", rtg)
            inp.set_editor_property("target_path", OUT_DIR)
            inp.set_editor_property("search", "A_Src_")
            inp.set_editor_property("replace", "A_Mocap_")
            inp.set_editor_property("overwrite_existing_files", True)
            inp.set_editor_property("use_source_path", False)
            created = unreal.IKRetargetBatchOperation().run_batch_retarget(inp) or []
            entry = {"src": stem, "created": [], "ok": False, "skeleton": None}
            for c in created:
                obj = unreal.AssetRegistryHelpers.get_asset(c)
                if obj:
                    unreal.EditorAssetLibrary.save_loaded_asset(obj)
                    sk = obj.get_editor_property("skeleton")
                    entry["skeleton"] = sk.get_name() if sk else None
                    entry["ok"] = sk is not None
                    entry["created"].append(str(c.package_name))
            report.append(entry)
        except Exception as exc:
            error_str = str(exc)[:120]
            report.append({"src": stem, "error": error_str, "ok": False})
            unreal.log_error(f"[Phase4] Retarget error for {stem}: {exc}")

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as fh:
        json.dump(report, fh, indent=1)
    ok = sum(1 for r in report if r.get("ok"))
    total = len(report)
    unreal.log(f"[Phase4] Retarget complete: {ok}/{total} clips OK")
    return report


def main():
    unreal.log("=" * 60)
    unreal.log("[Phase4] Starting missing mocap import + retarget")
    unreal.log("=" * 60)

    # Step 1: Import each missing FBX
    imported = []
    for fbx_name, dest_name in MISSING_TAKES:
        fbx_path = os.path.join(LOCAL_FBX_DIR, fbx_name)
        if not os.path.exists(fbx_path):
            unreal.log_warning(f"[Phase4] FBX not found: {fbx_path}")
            continue
        result = import_source_anim(fbx_path, dest_name)
        if result:
            imported.append(dest_name)

    unreal.log(f"[Phase4] Imported {len(imported)}/{len(MISSING_TAKES)} source animations")

    # Step 2: Batch retarget
    if imported:
        report = retarget_remaining()
        success = sum(1 for r in report if r.get("ok"))
        unreal.log(f"[Phase4] Retargeted {success}/{len(report)} animations successfully")
    else:
        unreal.log_warning("[Phase4] Nothing to retarget")

    unreal.log("[Phase4] Phase 4.0 complete")
    return True


main()
