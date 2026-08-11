"""Remove only the temporary Universal Triplanar Pro bridge nodes.

The function asset and authoring script are intentionally retained. The
universal master is restored to the exact pre-bridge expression topology after
the failed direct integration experiment.
"""

import unreal


MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
NAMES = {
    "MaterialExpressionStaticSwitchParameter_18",
    "MaterialExpressionScalarParameter_94",
    "MaterialExpressionScalarParameter_95",
    "MaterialExpressionScalarParameter_96",
    "MaterialExpressionScalarParameter_97",
    "MaterialExpressionScalarParameter_98",
    "MaterialExpressionScalarParameter_99",
    "MaterialExpressionScalarParameter_100",
    "MaterialExpressionVectorParameter_18",
    "MaterialExpressionVectorParameter_19",
    "MaterialExpressionVectorParameter_20",
    "MaterialExpressionMaterialFunctionCall_7",
    "MaterialExpressionWorldPosition_4",
    "MaterialExpressionVertexNormalWS_1",
    "MaterialExpressionLinearInterpolate_27",
    "MaterialExpressionStaticSwitch_0",
    "MaterialExpressionDotProduct_3",
    "MaterialExpressionConstant3Vector_7",
    "MaterialExpressionLinearInterpolate_28",
}


def main():
    material = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not material:
        raise RuntimeError(f"Could not load {MASTER}")
    mel = unreal.MaterialEditingLibrary
    expressions = list(mel.get_material_expressions(material) or [])
    removed = []
    for expression in expressions:
        if expression.get_name() in NAMES:
            mel.delete_material_expression(material, expression)
            removed.append(expression.get_name())
    # Reassert the stable routes even after deletion, in case the editor kept
    # a stale pin reference while removing the temporary nodes.
    expressions = list(mel.get_material_expressions(material) or [])
    lookup = {e.get_name(): e for e in expressions}
    bsdf = lookup["MaterialExpressionSubstrateToonBSDF_4"]
    for pin, source_name in {
        "BaseColor": "MaterialExpressionStaticSwitchParameter_10",
        "Roughness": "MaterialExpressionStaticSwitchParameter_11",
        "Normal": "MaterialExpressionStaticSwitchParameter_12",
        "EmissiveColor": "MaterialExpressionStaticSwitchParameter_13",
    }.items():
        if not mel.connect_material_expressions(lookup[source_name], "", bsdf, pin):
            raise RuntimeError(f"Could not restore {source_name} -> {pin}")
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    print(f"Removed {len(removed)} temporary bridge nodes; restored universal master")
    print("Removed:", removed)
    return removed


if __name__ == "__main__":
    main()
