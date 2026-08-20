import sys
import unreal

# Required Substrate and Material libs
mat_edit = unreal.MaterialEditingLibrary
asset_lib = unreal.EditorAssetLibrary

MAT_PATH = "/Game/EnvSandbox/Materials/Masters/M_Character_Toon_FaceSDF"
PROFILE_PATH = "/Game/EnvSandbox/Materials/ToonProfiles/TP_Character"

SDF_HLSL = """// Calculate DOT product against light vector
float NdotL = dot(normalize(LightVector), ForwardVector);
float LightAngle = acos(NdotL) / 3.14159;

// Sample the 2D Face SDF texture
float SDF = Texture2DSample(SDFTexture, SDFTextureSampler, UV).r;

// Tweak threshold using SDF strength/tiling
float shadow = step(SDF, saturate(LightAngle * FaceSDF_Strength));

return shadow;
"""

def create_face_sdf_master():
    # 1. Create or load the Material
    if asset_lib.does_asset_exist(MAT_PATH):
        material = asset_lib.load_asset(MAT_PATH)
    else:
        factory = unreal.MaterialFactoryNew()
        material = asset_lib.create_asset(MAT_PATH, "", unreal.Material, factory)
        
    material.set_editor_property("bUsesSubstrate", True)
    
    # 2. Add Toon Profile
    profile = asset_lib.load_asset(PROFILE_PATH)
    if not profile:
        unreal.log_warning(f"Could not load toon profile {PROFILE_PATH}")
    
    # 3. Create Substrate Toon BSDF Node
    toon_bsdf = mat_edit.create_material_expression(material, unreal.MaterialExpressionSubstrateToonBSDF, 400, 0)
    if profile:
        toon_bsdf.set_editor_property("toon_profile", profile)
        
    # 4. Create SDF Custom Node
    custom_sdf = mat_edit.create_material_expression(material, unreal.MaterialExpressionCustom, -100, 100)
    custom_sdf.set_editor_property("code", SDF_HLSL)
    custom_sdf.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT_1)
    
    input_lv = unreal.CustomInput()
    input_lv.set_editor_property("input_name", "LightVector")
    input_fw = unreal.CustomInput()
    input_fw.set_editor_property("input_name", "ForwardVector")
    input_tex = unreal.CustomInput()
    input_tex.set_editor_property("input_name", "SDFTexture")
    input_uv = unreal.CustomInput()
    input_uv.set_editor_property("input_name", "UV")
    input_str = unreal.CustomInput()
    input_str.set_editor_property("input_name", "FaceSDF_Strength")
    
    custom_sdf.set_editor_property("inputs", [input_lv, input_fw, input_tex, input_uv, input_str])
    
    # 5. Connect Front Material
    mat_edit.connect_material_property(toon_bsdf, "", unreal.MaterialProperty.MP_FRONT_MATERIAL)
    
    # Compile
    mat_edit.recompile_material(material)
    asset_lib.save_loaded_asset(material, only_if_is_dirty=False)
    
    unreal.log(f"Successfully generated {MAT_PATH} for Melusina's Face SDF!")

if __name__ == "__main__":
    create_face_sdf_master()
