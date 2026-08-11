import unreal

tp_path = "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina.TP_Melusina"
tp = unreal.EditorAssetLibrary.load_asset(tp_path)
settings = tp.get_editor_property("Settings")

dr = settings.get_editor_property("DiffuseRamp")

# Try to access the ColorCurves array
for i in range(4):
    curve_name = f"ColorCurves[{i}]"
    try:
        curve = dr.get_editor_property(curve_name)
        print(f"ColorCurves[{i}] type: {type(curve)}")
        print(f"  dir: {[m for m in dir(curve) if not m.startswith('_')]}")
        # Try to get keys
        keys = curve.get_editor_property("Keys")
        print(f"  Keys: {keys}")
        if keys:
            for k in keys:
                print(f"    Key: Time={k.Time}, Value={k.Value}")
    except Exception as e:
        print(f"  Error accessing {curve_name}: {e}")