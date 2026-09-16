"""Phase 3: import SK_MrSheep_AllTakes.fbx (proven donor-style path:
mesh + skeleton + NLA takes in ONE file). Then purge junk statics.
Report: Saved/Audit/choral_sheep/takes_final_report.json
"""
import json
import unreal

SRC = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\takes\SK_MrSheep_AllTakes.fbx"
DEST = "/Game/Melodia/Companions/ChoralSheep/Retarget"
REPORT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\takes_final_report.json"
rep = {}

# purge junk statics from failed passes
for junk in ("MrSheepFinal", "MrSheepTail", "SK_MrSheep_Idle",
             "SK_MrSheep_Idle_Skeleton"):
    pkg = DEST + "/" + junk
    if unreal.EditorAssetLibrary.does_asset_exist(pkg):
        unreal.EditorAssetLibrary.delete_asset(pkg)
        rep.setdefault("purged", []).append(pkg)

o = unreal.FbxImportUI()
o.import_mesh = True
o.import_as_skeletal = True
o.import_animations = True
o.import_materials = False
o.import_textures = False
t = unreal.AssetImportTask()
t.filename = SRC
t.destination_path = DEST
t.destination_name = "SK_MrSheep"
t.automated = True
t.save = True
t.replace_existing = True
t.options = o
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
rep["made"] = [str(p) for p in (t.imported_object_paths or [])]

# rename ugly anims SK_MrSheepSK_Sheep_X -> A_Sheep_X
RENAMES = {
    "SK_MrSheepSK_Sheep_Idle": "A_Sheep_Idle",
    "SK_MrSheepSK_Sheep_Walk": "A_Sheep_Walk",
    "SK_MrSheepSK_Sheep_WalkSlow": "A_Sheep_WalkSlow",
    "SK_MrSheepSK_Sheep_Run": "A_Sheep_Run",
    "SK_MrSheepSK_Sheep_Jump": "A_Sheep_Jump",
    "SK_MrSheepSK_Sheep_Death": "A_Sheep_Death",
}
rep["renamed"] = {}
for old, new in RENAMES.items():
    old_pkg = DEST + "/" + old
    if unreal.EditorAssetLibrary.does_asset_exist(old_pkg):
        ok = unreal.EditorAssetLibrary.rename_asset(old_pkg, DEST + "/" + new)
        rep["renamed"][new] = bool(ok)

ar = unreal.AssetRegistryHelpers.get_asset_registry()
ar.scan_paths_synchronous([DEST], force_rescan=True)
assets = ar.get_assets_by_path(DEST, recursive=True)
rep["inventory"] = [(str(a.asset_class_path.asset_name), str(a.package_name))
                    for a in assets]
# verify anim skeleton binding
rep["anim_check"] = {}
for cls, pkg in rep["inventory"]:
    if cls == "AnimSequence" and ("SK_MrSheep" in pkg or "/A_Sheep_" in pkg):
        seq = unreal.load_asset(pkg)
        sk = seq.get_editor_property("skeleton")
        rep["anim_check"][pkg] = {
            "skeleton": sk.get_path_name() if sk else None,
            "length": seq.get_editor_property("sequence_length") if seq else None,
        }
open(REPORT, "w", encoding="utf-8").write(json.dumps(rep, indent=1))
print("[takes-final] " + json.dumps(rep, indent=1))
