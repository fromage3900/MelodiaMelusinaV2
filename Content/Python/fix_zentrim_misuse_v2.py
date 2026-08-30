"""Fix ZenTrim misuse on 2 NikkiHero MIs - using correct param names.

Actual param names found: Albedo, NormalMap, BaseColor, Normal, Roughness, Metallic, Height

MI_NikkiHero_SakuraDream: ZenTrim_Base4K_BaseColor + T_Soil_Normal -> KB3D_ATL_BrickStoneCleanA_*
MI_NikkiHero_SakuraDream_IntegratedV1: same -> KB3D_ATL_BrickStoneCleanB_*
"""
import unreal

# KB3D_ATL textures for variant A and B
TEX_A = {
    "BaseColor": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_basecolor",
    "Normal": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_normal",
    "Roughness": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_roughness",
    "Metallic": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_metallic",
    "Height": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_height",
}
TEX_B = {
    "BaseColor": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_basecolor",
    "Normal": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_normal",
    "Roughness": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_roughness",
    "Metallic": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_metallic",
    "Height": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_height",
}

# Alternate param names to try (the MI might use different naming)
ALT_NAMES = {
    "BaseColor": ["BaseColor", "Albedo", "BaseColorMap"],
    "Normal": ["Normal", "NormalMap", "NormalMapTexture"],
    "Roughness": ["Roughness", "RoughnessMap"],
    "Metallic": ["Metallic", "MetallicMap"],
    "Height": ["Height", "HeightMap", "HeightMapTexture"],
}

def find_param_name(mi, candidates):
    """Try to find which param name actually exists in the MI."""
    for name in candidates:
        # Check if this is a texture param
        try:
            val = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi, name)
            if val is not None:
                return name, 'texture'
        except:
            pass
        # Check if scalar
        try:
            val = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, name)
            # Returns a value even if not overridden (gets default)
            # But we can check if it's overridden
            overridden = unreal.MaterialEditingLibrary.is_material_instance_parameter_overridden(mi, name)
            if overridden:
                return name, 'scalar'
        except:
            pass
    return None, None

def fix_mi(mi_path, tex_map, label):
    mi = unreal.load_asset(mi_path)
    if mi is None:
        print(f"  FAIL: could not load {mi_path}")
        return False
    
    print(f"\n=== Fixing {label} ===")
    
    # First, show all current params
    tex_names = unreal.MaterialEditingLibrary.get_texture_parameter_names(mi)
    sca_names = unreal.MaterialEditingLibrary.get_scalar_parameter_names(mi)
    vec_names = unreal.MaterialEditingLibrary.get_vector_parameter_names(mi)
    print(f"  Texture params: {tex_names}")
    print(f"  Scalar params: {sca_names}")
    print(f"  Vector params: {vec_names}")
    
    # Also show via MI's own arrays
    tparams = mi.texture_parameter_values
    print(f"  MI texture params ({len(tparams)}):")
    for i in range(len(tparams)):
        tp = tparams[i]
        info = tp.parameter_info
        pv = tp.parameter_value
        path = pv.get_path_name() if hasattr(pv, 'get_path_name') else '?'
        print(f"    [{i}] {info.name if info else '?'} = {path}")
    
    # Try to set each texture
    for target_name, tex_path in tex_map.items():
        candidates = ALT_NAMES.get(target_name, [target_name])
        found_name, param_type = find_param_name(mi, candidates)
        
        if found_name is None:
            print(f"  {target_name}: param not found in MI (tried {candidates})")
            continue
        
        tex_asset = unreal.load_asset(tex_path)
        if tex_asset is None:
            print(f"  {target_name}: could not load texture {tex_path}")
            continue
        
        if param_type == 'texture':
            result = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, found_name, tex_asset)
            print(f"  {target_name} ({found_name}, texture): {'OK' if result else 'FAIL'}")
        elif param_type == 'scalar':
            # For scalar params, we can't set a texture - skip
            print(f"  {target_name} ({found_name}, scalar): can't set texture on scalar param")
        else:
            # Try set_material_instance_parameter_override as fallback
            result = unreal.MaterialEditingLibrary.set_material_instance_parameter_override(mi, found_name, tex_asset)
            print(f"  {target_name} ({found_name}, override): {'OK' if result else 'FAIL'}")
    
    # Save
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    print(f"  Saved")
    return True

fix_mi(
    "/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream",
    TEX_A,
    "MI_NikkiHero_SakuraDream"
)
fix_mi(
    "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1",
    TEX_B,
    "MI_NikkiHero_SakuraDream_IntegratedV1"
)
print("\n=== Done ===")
