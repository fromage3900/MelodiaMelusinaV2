"""Phase 2: import 6 baked takes into UE, bound to SK_ChoralSheep_Skeleton.

Each take FBX re-exports MrSheepFinal + tail + rig with one baked action.
We import mesh=False + animations=True so the anims land on the SAME skeleton
already in /Game/Melodia/Companions/ChoralSheep/Retarget/.
Report: Saved/Audit/choral_sheep/takes_ue_import_report.json
Run: python Tools/ue_run_python.py --file Saved/_tmp_import_sheep_takes.py
"""
import json
import unreal

TAKE_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\takes"
DEST = "/Game/Melodia/Companions/ChoralSheep/Retarget"
SKELETON = DEST + "/SK_ChoralSheep_Skeleton"
REPORT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\takes_ue_import_report.json"
TAKES = ["Idle", "Walk", "WalkSlow", "Run", "Jump", "Death"]
rep = {"skeleton": SKELETON, "takes": {}}


def import_take(take):
    src = TAKE_DIR + "\\SK_Sheep_" + take + ".fbx"
    o = unreal.FbxImportUI()
    o.import_mesh = False          # anim only onto the existing skeleton
    o.import_as_skeletal = True
    o.import_animations = True
    o.import_materials = False
    o.import_textures = False
    o.skeleton = unreal.load_asset(SKELETON)  # bind anims to OUR skeleton
    if o.skeleton is None:
        return {"error": "skeleton not found: " + SKELETON}
    t = unreal.AssetImportTask()
    t.filename = src
    t.destination_path = DEST
    t.destination_name = "A_Sheep_" + take
    t.automated = True
    t.save = True
    t.replace_existing = True
    t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    made = [str(p) for p in (t.imported_object_paths or [])]
    return {"made": made}


def main():
    # purge junk static meshes from first failed pass (no anims were made)
    for junk in ("MrSheepFinal", "MrSheepTail"):
        pkg = DEST + "/" + junk
        if unreal.EditorAssetLibrary.does_asset_exist(pkg):
            unreal.EditorAssetLibrary.delete_asset(pkg)
            rep.setdefault("purged", []).append(pkg)
    for take in TAKES:
        try:
            rep["takes"][take] = import_take(take)
        except Exception as e:
            rep["takes"][take] = {"error": str(e)}
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    anims = [str(a.package_name) for a in
             ar.get_assets_by_class(unreal.TopLevelAssetPath(
                 "/Script/Engine", "AnimSequence"), True)
             if str(a.package_name).startswith(DEST)]
    rep["anim_sequences_in_retarget"] = sorted(anims)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(json.dumps(rep, indent=1))
    print("[takes-import] " + json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
