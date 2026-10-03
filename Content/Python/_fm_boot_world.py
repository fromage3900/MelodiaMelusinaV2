import unreal, json
EAL = unreal.EditorAssetLibrary
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
cands = [
    "/Game/ZenForestTest",
    "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SakuraTerrace/L_Gaea_SakuraTerrace_WP",
    "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SakuraTerrace/L_Gaea_SakuraTerrace",
    "/Game/Melodia/Levels/Opening/L_MelusinaShowcase",
]
out = {"exists": {}, "load_attempts": []}
for c in cands:
    out["exists"][c] = EAL.does_asset_exist(c)
for c in cands:
    if not out["exists"].get(c):
        continue
    try:
        ok = LES.load_level(c)
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        out["load_attempts"].append({"path": c, "ok": bool(ok), "world": w.get_path_name() if w else None})
        if w:
            break
    except Exception as e:
        out["load_attempts"].append({"path": c, "err": str(e)})
# try LoadingAndSavingUtils
try:
    for c in cands:
        if out["exists"].get(c):
            unreal.EditorLoadingAndSavingUtils.load_map(c)
            w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
            out["load_map"] = {"path": c, "world": w.get_path_name() if w else None}
            if w:
                break
except Exception as e:
    out["load_map_err"] = str(e)
print("BOOT " + json.dumps(out))
