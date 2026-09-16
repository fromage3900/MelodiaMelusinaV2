"""Phase 1: import donor sheep takes + MrSheep mesh into UE for retarget.

Imports (via AssetTools, idempotent — skips assets that already exist):
  donor FBX (mesh + 6 anim takes) -> /Game/Melodia/Companions/ChoralSheep/Retarget/SK_DonorSheep
  sheep FBX (MrSheepFinal + tail) -> /Game/Melodia/Companions/ChoralSheep/Retarget/SK_ChoralSheep
Report: Saved/Audit/choral_sheep/donor_import_report.json
Run: python Tools/ue_run_python.py --file Saved/_tmp_import_sheep_donor.py
"""
import json
import unreal

DONOR_FBX = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\donor_quaternius\SK_DonorSheep_AllTakes.fbx"
SHEEP_FBX = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Exports\ChoralSheep\SK_ChoralSheep_WeightFix.fbx"
DEST = "/Game/Melodia/Companions/ChoralSheep/Retarget"
REPORT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\donor_import_report.json"
rep = {"dest": DEST, "imports": {}}


def fbx_opts(with_anims):
    o = unreal.FbxImportUI()
    for k, v in (("import_mesh", True), ("import_as_skeletal", True),
                 ("import_animations", with_anims),
                 ("import_materials", False), ("import_textures", False),
                 ("automated_import_should_detect_type", False)):
        try:
            o.set_editor_property(k, v)
        except Exception:
            pass
    return o


def import_fbx(src, name, with_anims):
    pkg = DEST + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(pkg):
        return {"status": "exists", "package": pkg}
    t = unreal.AssetImportTask()
    t.filename = src
    t.destination_path = DEST
    t.destination_name = name
    t.automated = True
    t.save = True
    t.replace_existing = False
    t.options = fbx_opts(with_anims)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    ok = unreal.EditorAssetLibrary.does_asset_exist(pkg)
    return {"status": "imported" if ok else "FAILED", "package": pkg}


def describe_skeletal_mesh(pkg):
    try:
        sm = unreal.EditorAssetLibrary.load_asset(pkg)
        if sm is None:
            return {"loaded": False}
        skel = sm.get_editor_property("skeleton")
        bones = [b.name for b in skel.get_editor_property("bones")] \
            if skel else []
        return {"loaded": True, "bones": len(bones),
                "skeleton": skel.get_path_name() if skel else None}
    except Exception as e:
        return {"loaded": False, "error": str(e)}


def main():
    rep["imports"]["donor"] = import_fbx(DONOR_FBX, "SK_DonorSheep", True)
    rep["imports"]["sheep"] = import_fbx(SHEEP_FBX, "SK_ChoralSheep", False)
    rep["donor_mesh"] = describe_skeletal_mesh(DEST + "/SK_DonorSheep")
    rep["sheep_mesh"] = describe_skeletal_mesh(DEST + "/SK_ChoralSheep")
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    anims = [str(a.package_name) for a in
             ar.get_assets_by_class(unreal.TopLevelAssetPath("/Script/Engine",
                                                             "AnimSequence"), True)
             if str(a.package_name).startswith(DEST)]
    rep["anim_sequences"] = sorted(anims)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(json.dumps(rep, indent=1))
    print("[sheep-import] " + json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
