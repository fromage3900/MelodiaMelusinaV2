"""Verify Melusina instance texture references are valid."""
import unreal
EAL = unreal.EditorAssetLibrary

cello_path = "/Game/EnvSandbox/Materials/Instances/MelusinaReal/M_Master_Toon_Universal/MI_M_Master_Toon_Universal_Cello"
mi = unreal.load_asset(cello_path)
if mi:
    print(f"Parent: {mi.get_editor_property('parent').get_name() if mi.get_editor_property('parent') else 'NONE'}")
    print(f"Class: {mi.get_class().get_name()}")
    
    # Check texture parameter values
    try:
        textures = mi.get_editor_property("texture_parameter_values") or []
        for t in textures:
            name = str(t.get_editor_property("parameter_name"))
            tex = t.get_editor_property("parameter_value")
            tex_path = tex.get_path_name() if tex else "MISSING"
            exists = EAL.does_asset_exist(tex_path) if tex else False
            print(f"  TEX {name}: {tex_path.split('/')[-1] if tex else 'NONE'} valid={exists}")
    except Exception as ex:
        print(f"  Error: {str(ex)[:100]}")
    
    # Check scalar values for emissive-related
    try:
        scalars = mi.get_editor_property("scalar_parameter_values") or []
        for s in scalars:
            name = str(s.get_editor_property("parameter_name"))
            if any(x in name.lower() for x in ["emissive", "glow", "bloom", "global"]):
                val = s.get_editor_property("parameter_value")
                print(f"  SCALAR {name} = {val}")
    except:
        pass
else:
    print("INSTANCE NOT FOUND")
