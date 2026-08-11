import unreal

tp_path = "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina.TP_Melusina"
tp = unreal.EditorAssetLibrary.load_asset(tp_path)
settings = tp.get_editor_property("Settings")

dr = settings.get_editor_property("DiffuseRamp")
print(f"to_dict: {dr.to_dict()}")
print(f"to_tuple: {dr.to_tuple()}")
print(f"export_text: {dr.export_text()}")