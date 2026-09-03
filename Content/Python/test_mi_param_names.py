"""Comprehensive MI texture parameter setting test.

Diagnose what's actually happening and find a working approach.
"""
import unreal

# Load MI and test textures
mi = unreal.load_asset('/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream')
parent = unreal.load_asset('/Game/Greybox_Kit/ZenTrim_Base4K')

test_tex_a = unreal.load_asset('/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_basecolor')
test_tex_n = unreal.load_asset('/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_normal')

print(f"MI loaded: {mi is not None}")
print(f"Parent loaded: {parent is not None}")
print(f"Test tex A: {test_tex_a is not None}, path: {test_tex_a.get_path_name() if test_tex_a else 'None'}")
print(f"Test tex N: {test_tex_n is not None}, path: {test_tex_n.get_path_name() if test_tex_n else 'None'}")

# Get parent's parameter names
print("\n=== Parent parameter names ===")
tex_names = unreal.MaterialEditingLibrary.get_texture_parameter_names(parent)
sca_names = unreal.MaterialEditingLibrary.get_scalar_parameter_names(parent)
vec_names = unreal.MaterialEditingLibrary.get_vector_parameter_names(parent)
print(f"Texture params ({len(tex_names)}): {tex_names}")
print(f"Scalar params ({len(sca_names)}): {sca_names[:20]}...")
print(f"Vector params ({len(vec_names)}): {vec_names[:20]}...")

# Check what's overridden on the MI
print("\n=== MI texture parameters (from MI arrays) ===")
for i in range(len(mi.texture_parameter_values)):
    tp = mi.texture_parameter_values[i]
    info = tp.parameter_info
    pv = tp.parameter_value
    name = info.name if info else f"p{i}"
    path = pv.get_path_name() if hasattr(pv, 'get_path_name') else '?'
    print(f"  [{i}] {name}: {path}")

print("\n=== MI scalar parameters ===")
for i in range(len(mi.scalar_parameter_values)):
    sp = mi.scalar_parameter_values[i]
    info = sp.parameter_info
    name = info.name if info else f"s{i}"
    print(f"  [{i}] {name}: {sp.value}")

# Now try the MEL set with the CORRECT param name from parent
print("\n=== Attempting MEL set with parent param names ===")
for tex_name in tex_names:
    tex_path = None
    if "BaseColor" in tex_name or "Albedo" in tex_name:
        tex_path = '/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_basecolor'
    elif "Normal" in tex_name:
        tex_path = '/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_normal'
    
    if not tex_path:
        continue
    
    tex_asset = unreal.load_asset(tex_path)
    if not tex_asset:
        print(f"  {tex_name}: texture not found")
        continue
    
    # Try MEL set
    try:
        result = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, tex_name, tex_asset)
        print(f"  {tex_name}: MEL set = {result}")
    except Exception as e:
        print(f"  {tex_name}: MEL set ERROR - {e}")
    
    # Try after that, verify
    found = False
    for i in range(len(mi.texture_parameter_values)):
        tp = mi.texture_parameter_values[i]
        info = tp.parameter_info
        if info and info.name == tex_name:
            pv = tp.parameter_value
            new_path = pv.get_path_name() if hasattr(pv, 'get_path_name') else '?'
            print(f"    → current value: {new_path}")
            found = True
            break
    if not found:
        print(f"    → param '{tex_name}' not in MI texture params")

# Also try with all parameter names from MI's own arrays
print("\n=== Attempting MEL set with MI's own param names ===")
for i in range(len(mi.texture_parameter_values)):
    tp = mi.texture_parameter_values[i]
    info = tp.parameter_info
    name = info.name if info else f"p{i}"
    pv = tp.parameter_value
    current_path = pv.get_path_name() if hasattr(pv, 'get_path_name') else '?'
    
    # Pick a new texture based on the param name
    tex_path = None
    if "BaseColor" in name or "Albedo" in name or "Color" in name:
        tex_path = '/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_basecolor'
    elif "Normal" in name:
        tex_path = '/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_normal'
    
    if not tex_path:
        print(f"  [{i}] {name}: skipping (no matching test texture)")
        continue
    
    tex_asset = unreal.load_asset(tex_path)
    if not tex_asset:
        print(f"  [{i}] {name}: texture not found")
        continue
    
    try:
        result = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, name, tex_asset)
        print(f"  [{i}] {name}: MEL set = {result} (was: {current_path})")
    except Exception as e:
        print(f"  [{i}] {name}: MEL set ERROR - {e}")
    
    # Verify after
    for j in range(len(mi.texture_parameter_values)):
        tp2 = mi.texture_parameter_values[j]
        info2 = tp2.parameter_info
        if info2 and info2.name == name:
            pv2 = tp2.parameter_value
            new_path = pv2.get_path_name() if hasattr(pv2, 'get_path_name') else '?'
            if new_path != current_path:
                print(f"    → CHANGED to: {new_path}")
            break
