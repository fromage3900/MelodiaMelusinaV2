"""ZenTrim misuse fix — v3 with robust texture param setting.

Tests multiple approaches to set texture parameters on MIs.
"""
import unreal

mi_path = "/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream"
mi = unreal.load_asset(mi_path)
tex_a = unreal.load_asset("/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_basecolor")
tex_n = unreal.load_asset("/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_normal")

print(f"MI: {mi is not None}")
print(f"TexA: {tex_a is not None}, path: {tex_a.get_path_name() if tex_a else 'None'}")
print(f"TexN: {tex_n is not None}, path: {tex_n.get_path_name() if tex_n else 'None'}")

# Build map of param name -> current value from MI's own arrays
print("\n=== Current MI texture params (from MI arrays) ===")
mi_tex_params = {}
for i in range(len(mi.texture_parameter_values)):
    tp = mi.texture_parameter_values[i]
    info = tp.parameter_info
    pv = tp.parameter_value
    name = info.name if info else f"param_{i}"
    path = pv.get_path_name() if hasattr(pv, 'get_path_name') else '?'
    mi_tex_params[name] = path
    print(f"  {name}: {path}")

print("\n=== Current MI scalar params ===")
for i in range(len(mi.scalar_parameter_values)):
    sp = mi.scalar_parameter_values[i]
    info = sp.parameter_info
    name = info.name if info else f"scalar_{i}"
    print(f"  {name}: {sp.value}")

print("\n=== Attempting texture swaps ===")

# Approach 1: set via set_editor_property
print("\n--- Approach 1: set_editor_property ---")
for target_name, tex_asset in [("Albedo", tex_a), ("NormalMap", tex_n)]:
    if target_name in mi_tex_params:
        # Try set_editor_property on the MI directly
        try:
            setattr(mi, target_name, tex_asset)
            # Verify
            val = getattr(mi, target_name, None)
            if val and hasattr(val, 'get_path_name'):
                new_path = val.get_path_name()
                print(f"  {target_name}: setattr OK -> {new_path}")
            else:
                print(f"  {target_name}: setattr returned {val}")
        except Exception as e:
            print(f"  {target_name}: setattr FAIL - {e}")
    else:
        print(f"  {target_name}: not in MI texture params")

# Approach 2: MEL set_material_instance_texture_parameter_value
print("\n--- Approach 2: MEL set_material_instance_texture_parameter_value ---")
for target_name, tex_asset in [("Albedo", tex_a), ("NormalMap", tex_n)]:
    try:
        result = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
            mi, target_name, tex_asset
        )
        print(f"  {target_name}: MEL set {'OK' if result else 'FAIL'}")
    except Exception as e:
        print(f"  {target_name}: MEL set ERROR - {e}")

# Approach 3: MEL set_material_instance_parameter_override (generic)
print("\n--- Approach 3: MEL set_material_instance_parameter_override ---")
for target_name, tex_asset in [("Albedo", tex_a), ("NormalMap", tex_n)]:
    try:
        result = unreal.MaterialEditingLibrary.set_material_instance_parameter_override(
            mi, target_name, tex_asset
        )
        print(f"  {target_name}: override {'OK' if result else 'FAIL'}")
    except Exception as e:
        print(f"  {target_name}: override ERROR - {e}")

# Approach 4: Check if MEL methods need the param to exist first
print("\n--- Approach 4: MEL set with force ---")
for target_name, tex_asset in [("Albedo", tex_a), ("NormalMap", tex_n)]:
    try:
        # Try clearing first
        unreal.MaterialEditingLibrary.clear_all_material_instance_parameters(mi)
        # Then set
        result = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
            mi, target_name, tex_asset
        )
        print(f"  {target_name}: clear+set {'OK' if result else 'FAIL'}")
    except Exception as e:
        print(f"  {target_name}: clear+set ERROR - {e}")

# Save and verify
print("\n=== Saving and verifying ===")
unreal.EditorAssetLibrary.save_loaded_asset(mi)
print("Saved.")

# Reload and check
mi2 = unreal.load_asset(mi_path)
print("\n=== After save - MI texture params ===")
for i in range(len(mi2.texture_parameter_values)):
    tp = mi2.texture_parameter_values[i]
    info = tp.parameter_info
    pv = tp.parameter_value
    name = info.name if info else f"param_{i}"
    path = pv.get_path_name() if hasattr(pv, 'get_path_name') else '?'
    print(f"  {name}: {path}")
