import unreal

MATERIAL_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

PARAMETERS = [
    {"name": "DreamIntensity",   "type": "Scalar", "default": 1.0, "min": 0.0, "max": 2.0, "group": "08 Nikki Dream"},
    {"name": "DreamComposition", "type": "Scalar", "default": 0.0, "min": 0.0, "max": 2.0, "group": "08 Nikki Dream"},
    {"name": "DreamThreshold",   "type": "Scalar", "default": 0.0, "min": 0.0, "max": 1.0, "group": "08 Nikki Dream"},
    {"name": "DreamWarmth",      "type": "Vector", "default": (1.0, 0.85, 0.70, 1.0), "group": "08 Nikki Dream"},
]

HLSL_CODE = """float luma = dot(DreamColor, float3(0.2126, 0.7152, 0.0722));
if (luma < Threshold) return BaseColor;
float3 result;
int mode = (int)round(Composition);
if (mode == 0) result = BaseColor + DreamColor * DreamIntensity;
else if (mode == 1) result = max(BaseColor, DreamColor * DreamIntensity);
else result = 1.0 - (1.0 - BaseColor) * (1.0 - DreamColor * DreamIntensity);
return result;"""


def main():
    mat = unreal.load_asset(MATERIAL_PATH)
    if mat is None:
        print(f"Material not found at {MATERIAL_PATH}")
        return False

    print(f"Loaded {MATERIAL_PATH}")

    mel = unreal.MaterialEditingLibrary

    # Gather existing parameter names from graph expressions
    existing_params = set()
    for expr in (mel.get_material_expressions(mat) or []):
        for prop in ("parameter_name", "ParameterName"):
            try:
                val = expr.get_editor_property(prop)
                if val:
                    existing_params.add(str(val))
            except Exception:
                pass

    created_params = []
    for p in PARAMETERS:
        pname = p["name"]
        if pname in existing_params:
            print(f"  Skipped {pname} \u2014 already exists")
            continue

        if p["type"] == "Scalar":
            mel.set_scalar_parameter_editor_info(mat, pname, p["min"], p["max"], p["group"])
            mel.set_material_instance_scalar_parameter_value(mat, pname, p["default"])
            created_params.append(pname)
        elif p["type"] == "Vector":
            c = p["default"]
            mel.set_vector_parameter_editor_info(mat, pname, p["group"])
            mel.set_material_instance_vector_parameter_value(mat, pname, unreal.LinearColor(c[0], c[1], c[2], c[3]))
            created_params.append(pname)

    if created_params:
        print(f"  Created parameters: {', '.join(created_params)}")
    else:
        print("  No new parameters needed")

    # Custom HLSL node — "DreamCompositor"
    existing_hlsl = [e for e in (mel.get_material_expressions(mat) or [])
                     if type(e).__name__ == "MaterialExpressionCustom"
                     and e.get_editor_property("name") == "DreamCompositor"]
    if existing_hlsl:
        print("  HLSL node DreamCompositor already exists \u2014 skipping")
    else:
        hlsl_node = mel.create_material_expression(mat, unreal.MaterialExpressionCustom)
        hlsl_node.set_editor_property("name", "DreamCompositor")
        hlsl_node.set_editor_property("code", HLSL_CODE)
        hlsl_node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        hlsl_node.set_editor_property("description", "Unified dream glow compositor \u2014 additive/max/screen blend")

        inputs = []
        for inp_name in ("DreamColor", "BaseColor", "DreamIntensity", "Composition", "Threshold"):
            ci = unreal.CustomInput()
            ci.set_editor_property("input_name", inp_name)
            ci.set_editor_property("input", unreal.MaterialExpressionInput())
            inputs.append(ci)
        hlsl_node.set_editor_property("inputs", inputs)

        print("  Created Custom HLSL node: DreamCompositor")

    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MATERIAL_PATH, only_if_is_dirty=False)
    print(f"Saved {MATERIAL_PATH}")
    return True


if __name__ == "__main__":
    ok = main()
    print("Done" if ok else "Failed")
