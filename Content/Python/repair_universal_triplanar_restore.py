"""Restore the Universal Toon master to its pre-bridge BSDF routes.

The Substance-style triplanar nodes remain saved as an isolated, default-off
research branch. This repair only restores the four documented final Toon BSDF
inputs and does not delete the new function or parameters.
"""

import unreal


MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"


def find(expressions, name):
    for expression in expressions:
        if expression.get_name() == name:
            return expression
    raise RuntimeError(f"Missing expression: {name}")


def main():
    material = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not material:
        raise RuntimeError(f"Could not load {MASTER}")
    mel = unreal.MaterialEditingLibrary
    expressions = list(mel.get_material_expressions(material) or [])
    bsdf = find(expressions, "MaterialExpressionSubstrateToonBSDF_4")
    routes = {
        "BaseColor": "MaterialExpressionStaticSwitchParameter_10",
        "Roughness": "MaterialExpressionStaticSwitchParameter_11",
        "Normal": "MaterialExpressionStaticSwitchParameter_12",
        "EmissiveColor": "MaterialExpressionStaticSwitchParameter_13",
    }
    for pin, node_name in routes.items():
        source = find(expressions, node_name)
        if not mel.connect_material_expressions(source, "", bsdf, pin):
            raise RuntimeError(f"Could not restore {node_name} -> {pin}")
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    print("Restored Universal Toon BSDF routes:", routes)
    return routes


if __name__ == "__main__":
    main()
