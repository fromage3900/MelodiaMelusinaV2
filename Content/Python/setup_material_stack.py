import unreal

MATERIAL_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

def layer_two_params():
    return [
        ("bStackLayer2_Active", "StaticBool", False, None, None, None),
        ("Stack2_Albedo", "Texture2D", None, None, None, None),
        ("Stack2_Normal", "Texture2D", None, None, None, None),
        ("Stack2_ORM", "Texture2D", None, None, None, None),
        ("Stack2_Tiling", "Scalar", 1.0, 0.1, 10.0, None),
        ("Stack2_Blend", "Scalar", 0.5, 0.0, 1.0, None),
        ("Stack2_Metallic", "Scalar", 0.0, 0.0, 1.0, None),
        ("Stack2_Roughness", "Scalar", 0.5, 0.0, 1.0, None),
    ]

def layer_three_params():
    return [
        ("bStackLayer3_Active", "StaticBool", False, None, None, None),
        ("Stack3_Albedo", "Texture2D", None, None, None, None),
        ("Stack3_Normal", "Texture2D", None, None, None, None),
        ("Stack3_Tiling", "Scalar", 1.0, 0.1, 10.0, None),
        ("Stack3_Metallic", "Scalar", 1.0, 0.0, 1.0, None),
        ("Stack3_Roughness", "Scalar", 0.1, 0.0, 1.0, None),
    ]

def main():
    unreal.log("=== Material Stack Setup ===")

    material = unreal.load_asset(name=MATERIAL_PATH)
    if material is None:
        unreal.log_error("Material not found: {}".format(MATERIAL_PATH))
        return

    unreal.log("Material loaded: {}".format(MATERIAL_PATH))

    editing_lib = unreal.MaterialEditingLibrary
    existing_params = {p.get_name() for p in material.get_parameters()}

    all_params = layer_two_params() + layer_three_params()

    created_count = 0
    skipped_count = 0

    for name, param_type, default_val, min_val, max_val, group in all_params:
        if name in existing_params:
            unreal.log("SKIP (already exists): {}".format(name))
            skipped_count += 1
            continue

        if param_type == "StaticBool":
            param = editing_lib.add_static_switch_parameter_to_material(
                material=material,
                parameter_name=name,
                default_value=default_val,
                group=unreal.ParameterGroupInfo(bIsNewGroup=False, groupName="07 | Material Stack")
            )
            unreal.log("CREATED StaticBool param: {}".format(name))

        elif param_type == "Texture2D":
            param = editing_lib.add_material_texture_parameter(
                material=material,
                parameter_name=name,
                default_value=None,
                group=unreal.ParameterGroupInfo(bIsNewGroup=False, groupName="07 | Material Stack")
            )
            tex_expr = editing_lib.create_material_expression(
                material=material,
                expression_class=unreal.MaterialExpressionTextureObjectParameter,
                node_pos_x=0,
                node_pos_y=0
            )
            tex_expr.set_editor_property("parameter_name", name)
            tex_expr.set_editor_property("group", "07 | Material Stack")
            unreal.log("CREATED Texture2D param + TextureObjectParameter expr: {}".format(name))

        elif param_type == "Scalar":
            param = editing_lib.add_material_scalar_parameter(
                material=material,
                parameter_name=name,
                default_value=default_val,
                apply_min=True,
                apply_max=True,
                min_value=min_val,
                max_value=max_val,
                group=unreal.ParameterGroupInfo(bIsNewGroup=False, groupName="07 | Material Stack")
            )
            unreal.log("CREATED Scalar param: {} (default={}, range={}-{})".format(name, default_val, min_val, max_val))

        created_count += 1

    unreal.log("=== Summary ===")
    unreal.log("Created: {} params".format(created_count))
    unreal.log("Skipped (already exist): {} params".format(skipped_count))

    editing_lib.rebuild_material_instance_editors(material)
    editing_lib.update_material_instance(material.get_material_instance())
    unreal.EditorAssetLibrary.save_asset(MATERIAL_PATH)
    unreal.log("Saved: {}".format(MATERIAL_PATH))

    unreal.log("NOTE: Material stack: layer blending and texture wiring requires manual graph editing. "
               "The parameters exist but the Multiply/Lerp chains connecting them to the main "
               "color/normal/roughness outputs need manual wiring.")

if __name__ == "__main__":
    main()
