import unreal, json
out = {}
out["has_LES"] = hasattr(unreal, "LandscapeEditorSubsystem")
out["has_ImportHelper"] = hasattr(unreal, "LandscapeImportHelper")
out["has_Landscape"] = hasattr(unreal, "Landscape")
if hasattr(unreal, "LandscapeEditorSubsystem"):
    sub = unreal.get_editor_subsystem(unreal.LandscapeEditorSubsystem)
    out["LES_methods"] = [m for m in dir(sub) if not m.startswith("_")][:80]
out["ELL_land"] = [m for m in dir(unreal.EditorLevelLibrary) if "land" in m.lower() or "Land" in m]
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
out["LevelEd"] = [m for m in dir(les) if not m.startswith("_") and any(k in m.lower() for k in ("level","new","save","load","open"))][:50]
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
out["world"] = w.get_path_name() if w else None
# Does level asset exist
out["lvl_exists"] = unreal.EditorAssetLibrary.does_asset_exist("/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype")
print("API " + json.dumps(out, default=str)[:8000])
