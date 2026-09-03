import unreal

MATERIAL_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

PARAMETERS = [
    {"name": "bGemstone_Active",    "type": "StaticBool", "default": False,                     "group": "06 | Gemstone"},
    {"name": "IOR",                 "type": "Scalar",     "default": 2.42, "min": 1.0, "max": 3.0,   "group": "06 | Gemstone"},
    {"name": "Dispersion",          "type": "Scalar",     "default": 0.044,"min": 0.0, "max": 0.12,  "group": "06 | Gemstone"},
    {"name": "GemstoneTint",        "type": "Vector",     "default": (1,1,1,1),                     "group": "06 | Gemstone"},
    {"name": "GemstoneRoughness",   "type": "Scalar",     "default": 0.02, "min": 0.0, "max": 1.0,  "group": "06 | Gemstone"},
    {"name": "GlintIntensity",      "type": "Scalar",     "default": 0.0,  "min": 0.0, "max": 2.0,  "group": "06 | Gemstone"},
    {"name": "GlintScale",          "type": "Scalar",     "default": 16.0, "min": 1,   "max": 128,  "group": "06 | Gemstone"},
    {"name": "ChromaticStrength",   "type": "Scalar",     "default": 0.1,  "min": 0.0, "max": 1.0,  "group": "06 | Gemstone"},
]

HLSL_CODE = """float r = saturate(Rim + Disp);
float g = saturate(Rim);
float b = saturate(Rim - Disp);
return float3(r*r, g*g, b*b);
"""


def main():
    asset_lib = unreal.EditorAssetLibrary()
    if not asset_lib.does_asset_exist(MATERIAL_PATH):
        unreal.log_error(f"Material not found at {MATERIAL_PATH}")
        return

    mat = asset_lib.load_asset(MATERIAL_PATH)
    unreal.log(f"Gemstone lane: Loaded material {MATERIAL_PATH}")

    mel = unreal.MaterialEditingLibrary
    existing_expressions = mel.get_material_expressions(mat)
    existing_names = {e.get_editor_property("name") or e.get_editor_property("parameter_name") for e in existing_expressions}

    created = []
    for param in PARAMETERS:
        pname = param["name"]
        if pname in existing_names:
            unreal.log(f"  Skipped {pname} — already exists")
            continue

        if param["type"] == "StaticBool":
            expr = mel.create_material_expression(mat, unreal.MaterialExpressionStaticBoolParameter, -500, 0)
            expr.set_editor_property("parameter_name", pname)
            expr.set_editor_property("default_value", param["default"])
            expr.set_editor_property("group", param["group"])
        elif param["type"] == "Scalar":
            expr = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -500, 0)
            expr.set_editor_property("parameter_name", pname)
            expr.set_editor_property("default_value", param["default"])
            expr.set_editor_property("slider_min", param["min"])
            expr.set_editor_property("slider_max", param["max"])
            expr.set_editor_property("group", param["group"])
        elif param["type"] == "Vector":
            expr = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -500, 0)
            expr.set_editor_property("parameter_name", pname)
            c = param["default"]
            expr.set_editor_property("default_value", unreal.LinearColor(c[0], c[1], c[2], c[3]))
            expr.set_editor_property("group", param["group"])

        created.append(pname)

    if created:
        unreal.log(f"Gemstone lane: Created parameters: {', '.join(created)}")
    else:
        unreal.log("Gemstone lane: All parameters already exist")

    # Custom HLSL node — "GemstoneDispersion"
    existing_hlsl = [e for e in existing_expressions
                     if e.get_editor_property("name") == "GemstoneDispersion" or
                     (hasattr(e, "get_name") and e.get_name() == "GemstoneDispersion")]
    if existing_hlsl:
        unreal.log("  HLSL node GemstoneDispersion already exists — skipping")
    else:
        hlsl_node = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, -500, 0)
        hlsl_node.set_editor_property("name", "GemstoneDispersion")
        hlsl_node.set_editor_property("code", HLSL_CODE)
        hlsl_node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        hlsl_node.set_editor_property("description", "Gemstone chromatic dispersion")

        rim_input = unreal.CustomInput()
        rim_input.set_editor_property("input_name", "Rim")
        disp_input = unreal.CustomInput()
        disp_input.set_editor_property("input_name", "Disp")
        hlsl_node.set_editor_property("inputs", [rim_input, disp_input])

        unreal.log("  Created Custom HLSL node: GemstoneDispersion")

    mel.rebuild_material_editing_data(mat)
    asset_lib.save_asset(MATERIAL_PATH)
    unreal.log(f"Gemstone lane: Material saved to {MATERIAL_PATH}")
    unreal.log("Gemstone lane: IOR-based F0 compensation, chromatic dispersion, and Glint integration still need manual wiring in the material graph editor")


if __name__ == "__main__":
    main()
