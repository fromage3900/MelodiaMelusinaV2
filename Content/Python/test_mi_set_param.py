"""Test different approaches to set texture params on MI."""
import unreal

mi = unreal.load_asset('/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream')
tex = unreal.load_asset('/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_basecolor')

print(f"MI: {mi is not None}, Tex: {tex is not None}")
print(f"Tex path: {tex.get_path_name() if tex else 'None'}")

# Method 1: set_material_instance_texture_parameter_value with various names
print("\n=== Method 1: set_material_instance_texture_parameter_value ===")
for name in ["BaseColor", "Albedo", "BaseColorMap", "Normal", "NormalMap"]:
    try:
        result = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, name, tex)
        print(f"  {name}: {result}")
    except Exception as e:
        print(f"  {name}: ERROR - {e}")

# Method 2: set_editor_property
print("\n=== Method 2: set_editor_property ===")
for name in ["BaseColor", "Albedo", "BaseColorMap", "NormalMap", "Normal"]:
    try:
        # Try setting via editor property
        setattr(mi, name, tex)
        print(f"  {name}: setattr OK, value={getattr(mi, name, 'N/A')}")
    except Exception as e:
        print(f"  {name}: setattr FAIL - {e}")

# Method 3: set_material_instance_parameter_override (generic)
print("\n=== Method 3: set_material_instance_parameter_override ===")
for name in ["BaseColor", "Albedo", "NormalMap", "Normal"]:
    try:
        result = unreal.MaterialEditingLibrary.set_material_instance_parameter_override(mi, name, tex)
        print(f"  {name}: override {result}")
    except Exception as e:
        print(f"  {name}: ERROR - {e}")

# Method 4: Check what set_editor_properties accepts
print("\n=== Method 4: set_editor_properties batch ===")
try:
    props = {"BaseColor": tex, "Normal": tex}
    result = mi.set_editor_properties(**props)
    print(f"  Batch set: {result}")
except Exception as e:
    print(f"  Batch set FAIL: {e}")

# Method 5: Try clearing then setting
print("\n=== Method 5: clear then set ===")
for name in ["BaseColor", "Albedo"]:
    try:
        unreal.MaterialEditingLibrary.clear_instance_parameter(mi, name)
        result = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, name, tex)
        print(f"  {name}: clear+set = {result}")
    except Exception as e:
        print(f"  {name}: ERROR - {e}")
