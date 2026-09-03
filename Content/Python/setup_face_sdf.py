import unreal


MATERIAL_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
GROUP_NAME = "09 | Character"
PARAM_NAMES = [
    "FaceSDF_Texture",
    "FaceSDF_Strength",
    "FaceSDF_Tiling",
    "bFaceSDF_UV1",
    "SkinSSS_Strength",
    "SkinSSS_Color",
    "SkinSSS_Radius",
]

SKINSSS_HLSL = """// Fake SSS via wrap lighting — shifts the shadow terminator toward the light
// Wider wrap = more light bleeds through thin geometry
float wrap = 1.0 + SkinSSSRadius;
float sss = saturate((NdotL + SkinSSSRadius) / (wrap * wrap));
return lerp(NdotL, sss, SkinSSSStrength);"""


def parameter_exists(material: unreal.Material, name: str) -> bool:
    existing = {p for p in material.get_parameter_names()}
    return name in existing


def get_existing_params(material: unreal.Material) -> set:
    return {p for p in material.get_parameter_names()}


def create_scalar_param(
    material: unreal.Material,
    name: str,
    default: float,
    min_val: float,
    max_val: float,
    group: str,
    x: int,
    y: int,
) -> unreal.MaterialExpressionScalarParameter:
    expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, x, y
    )
    expr.set_editor_property("parameter_name", name)
    expr.set_editor_property("default_value", default)
    expr.set_editor_property("slider_min", min_val)
    expr.set_editor_property("slider_max", max_val)
    expr.set_editor_property("group", group)
    return expr


def create_texture_param(
    material: unreal.Material,
    name: str,
    group: str,
    x: int,
    y: int,
) -> unreal.MaterialExpressionTextureObjectParameter:
    expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureObjectParameter, x, y
    )
    expr.set_editor_property("parameter_name", name)
    expr.set_editor_property("group", group)
    return expr


def create_static_bool_param(
    material: unreal.Material,
    name: str,
    default: bool,
    group: str,
    x: int,
    y: int,
) -> unreal.MaterialExpressionStaticBoolParameter:
    expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionStaticBoolParameter, x, y
    )
    expr.set_editor_property("parameter_name", name)
    expr.set_editor_property("default_value", default)
    expr.set_editor_property("group", group)
    return expr


def create_vector_param(
    material: unreal.Material,
    name: str,
    default: tuple,
    group: str,
    x: int,
    y: int,
) -> unreal.MaterialExpressionVectorParameter:
    expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, x, y
    )
    expr.set_editor_property("parameter_name", name)
    expr.set_editor_property("default_value", unreal.LinearColor(*default))
    expr.set_editor_property("group", group)
    return expr


def create_skinsss_node(
    material: unreal.Material,
    x: int,
    y: int,
) -> unreal.MaterialExpressionCustom:
    expr = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionCustom, x, y
    )
    expr.set_editor_property("code", SKINSSS_HLSL)
    expr.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT_1)

    input_ndotl = unreal.CustomInput()
    input_ndotl.set_editor_property("input_name", "NdotL")

    input_strength = unreal.CustomInput()
    input_strength.set_editor_property("input_name", "SkinSSSStrength")

    input_radius = unreal.CustomInput()
    input_radius.set_editor_property("input_name", "SkinSSSRadius")

    expr.set_editor_property("inputs", [input_ndotl, input_strength, input_radius])
    return expr


def main():
    asset_lib = unreal.EditorAssetLibrary()
    mat_edit = unreal.MaterialEditingLibrary

    material = asset_lib.load_asset(MATERIAL_PATH)
    if material is None:
        unreal.log_error("[FaceSDF] Material not found: {}".format(MATERIAL_PATH))
        return

    if not isinstance(material, unreal.Material):
        unreal.log_error("[FaceSDF] Asset is not a Material: {}".format(MATERIAL_PATH))
        return

    existing = get_existing_params(material)
    created = []

    x_offset = -900
    y_offset = 0

    # --- Parameters ---

    if "FaceSDF_Texture" not in existing:
        create_texture_param(material, "FaceSDF_Texture", GROUP_NAME, x_offset, y_offset)
        created.append("FaceSDF_Texture")
        y_offset += 400

    if "FaceSDF_Strength" not in existing:
        create_scalar_param(material, "FaceSDF_Strength", 0.0, 0.0, 1.0, GROUP_NAME, x_offset, y_offset)
        created.append("FaceSDF_Strength")
        y_offset += 400

    if "FaceSDF_Tiling" not in existing:
        create_scalar_param(material, "FaceSDF_Tiling", 1.0, 0.1, 10.0, GROUP_NAME, x_offset, y_offset)
        created.append("FaceSDF_Tiling")
        y_offset += 400

    if "bFaceSDF_UV1" not in existing:
        create_static_bool_param(material, "bFaceSDF_UV1", True, GROUP_NAME, x_offset, y_offset)
        created.append("bFaceSDF_UV1")
        y_offset += 400

    if "SkinSSS_Strength" not in existing:
        create_scalar_param(material, "SkinSSS_Strength", 0.0, 0.0, 1.0, GROUP_NAME, x_offset, y_offset)
        created.append("SkinSSS_Strength")
        y_offset += 400

    if "SkinSSS_Color" not in existing:
        create_vector_param(material, "SkinSSS_Color", (1.0, 0.35, 0.25, 1.0), GROUP_NAME, x_offset, y_offset)
        created.append("SkinSSS_Color")
        y_offset += 400

    if "SkinSSS_Radius" not in existing:
        create_scalar_param(material, "SkinSSS_Radius", 0.3, 0.0, 1.0, GROUP_NAME, x_offset, y_offset)
        created.append("SkinSSS_Radius")
        y_offset += 400

    # --- Custom HLSL node ---
    custom_node = create_skinsss_node(material, x_offset, y_offset)
    created.append("SkinSSS (Custom HLSL node)")

    if created:
        mat_edit.rebuild_material_editing_data(material)

    # Print summary
    unreal.log("=" * 60)
    unreal.log("[FaceSDF + SkinSSS] Setup complete for: {}".format(MATERIAL_PATH))
    unreal.log("")
    if created:
        unreal.log("Created/added:")
        for item in created:
            unreal.log("  - {}".format(item))
    else:
        unreal.log("All parameters and the Custom HLSL node already exist — nothing was added.")

    unreal.log("")
    unreal.log(
        "Face SDF: requires the face mesh to have UV channel 1 set up with the SDF face layout. "
        "The SDF texture replaces standard shadow on the face region."
    )
    unreal.log(
        "SkinSSS: wire the output to wherever NdotL is used in the Toon BSDF "
        "or multiply it into the diffuse ramp."
    )
    unreal.log("=" * 60)


if __name__ == "__main__":
    main()
