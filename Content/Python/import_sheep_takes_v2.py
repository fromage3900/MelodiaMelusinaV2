"""Phase 2b: import baked takes onto ONE shared skeleton.

Strategy: import Idle take WITH mesh (creates MrSheepFinal/Tail skeletal meshes
+ their skeleton, 106 deform bones), then import the other 5 takes anim-only
bound to that exact skeleton asset.
Report: Saved/Audit/choral_sheep/takes_ue_import_report.json
"""
import json
import unreal

TAKE_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\takes"
DEST = "/Game/Melodia/Companions/ChoralSheep/Retarget"
REPORT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\takes_ue_import_report.json"
TAKES = ["Idle", "Walk", "WalkSlow", "Run", "Jump", "Death"]
rep = {"takes": {}}


def base_opts():
    o = unreal.FbxImportUI()
    o.import_as_skeletal = True
    o.import_animations = True
    o.import_materials = False
    o.import_textures = False
    return o


def run_import(take, with_mesh, skeleton=None, name=None):
    src = TAKE_DIR + "\\SK_Sheep_" + take + ".fbx"
    o = base_opts()
    o.import_mesh = with_mesh
    if skeleton is not None:
        o.skeleton = skeleton
    t = unreal.AssetImportTask()
    t.filename = src
    t.destination_path = DEST
    t.destination_name = name or ("SK_MrSheep_" + take)
    t.automated = True
    t.save = True
    t.replace_existing = True
    t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return [str(p) for p in (t.imported_object_paths or [])]


def main():
    # clean junk from earlier attempts
    for junk in ("MrSheepFinal", "MrSheepTail", "SK_MrSheep_Idle"):
        pkg = DEST + "/" + junk
        if unreal.EditorAssetLibrary.does_asset_exist(pkg):
            unreal.EditorAssetLibrary.delete_asset(pkg)

    rep["takes"]["Idle"] = {"made": run_import("Idle", True)}

    # find the skeleton created by the Idle import
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    ar.scan_paths_synchronous([DEST], force_rescan=True)
    skels = [a for a in ar.get_assets_by_class(
        unreal.TopLevelAssetPath("/Script/Engine", "Skeleton"), True)
        if str(a.package_name).startswith(DEST)]
    new_skels = [s for s in skels
                 if "ChoralSheep_Skeleton" not in str(s.package_name)
                 and "DonorSheep_Skeleton" not in str(s.package_name)]
    if not new_skels:
        rep["error"] = "no new skeleton found after Idle import"
        rep["all_skeletons"] = [str(s.package_name) for s in skels]
        open(REPORT, "w", encoding="utf-8").write(json.dumps(rep, indent=1))
        print("[takes2b] FAILED - no skeleton")
        return
    skel = new_skels[0].get_asset()
    rep["skeleton"] = str(new_skels[0].package_name)
    n_skel_bones = skel.get_editor_property("bone_tree") \
        if hasattr(skel, "bone_tree") else None

    for take in TAKES[1:]:
        try:
            rep["takes"][take] = {
                "made": run_import(take, False, skeleton=skel,
                                   name="A_Sheep_" + take)}
        except Exception as e:
            rep["takes"][take] = {"error": str(e)}

    anims = [str(a.package_name) for a in ar.get_assets_by_class(
        unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence"), True)
        if str(a.package_name).startswith(DEST)]
    rep["anim_sequences"] = sorted(anims)
    # verify each new anim's skeleton
    rep["anim_skeletons"] = {}
    for a in anims:
        if "/A_Sheep_" in a:
            seq = unreal.load_asset(a)
            if seq:
                s = seq.get_editor_property("skeleton")
                rep["anim_skeletons"][a] = s.get_path_name() if s else None
    open(REPORT, "w", encoding="utf-8").write(json.dumps(rep, indent=1))
    print("[takes2b] " + json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
