"""Organize the durable Gaea lane in M_Master_Nikki_Landscape.

This is intentionally an editor-only, idempotent layout pass. It moves and labels
existing expressions; it does not change connections, material parameters, levels,
viewport state, or camera transforms. Run it through Monolith editor.run_python,
then save the one master package explicitly with editor.save_packages.
"""

import json
import unreal


MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape"


# A dedicated, empty band below the existing long-term triplanar/snow-detail lanes.
# X increases with signal flow; Y is spaced so the four mask lanes can be read as a
# small table in the material editor.
POSITIONS = {
    # One normalized UV authority.
    "MaterialExpressionWorldPosition_1": (-5200, 4200),
    "MaterialExpressionVectorParameter_13": (-5200, 4400),
    "MaterialExpressionVectorParameter_14": (-5200, 4600),
    "MaterialExpressionSubtract_5": (-4800, 4200),
    "MaterialExpressionDivide_3": (-4400, 4200),
    "MaterialExpressionComponentMask_0": (-4000, 4200),
    "MaterialExpressionSaturate_8": (-3600, 4200),
    # Whole-map color lanes, ordered by semantic layer.
    "MaterialExpressionStaticSwitchParameter_10": (-3200, 3400),
    "MaterialExpressionTextureSampleParameter2D_0": (-2800, 3400),
    "MaterialExpressionStaticSwitchParameter_11": (-3200, 3600),
    "MaterialExpressionTextureSampleParameter2D_4": (-2800, 3600),
    "MaterialExpressionStaticSwitchParameter_5": (-3200, 3800),
    "MaterialExpressionTextureSampleParameter2D_18": (-2800, 3800),
    "MaterialExpressionStaticSwitchParameter_7": (-3200, 4000),
    "MaterialExpressionTextureSampleParameter2D_6": (-2800, 4000),
    "MaterialExpressionStaticSwitchParameter_8": (-3200, 4200),
    "MaterialExpressionTextureSampleParameter2D_8": (-2800, 4200),
    "MaterialExpressionStaticSwitchParameter_9": (-3200, 4400),
    "MaterialExpressionTextureSampleParameter2D_11": (-2800, 4400),
    "MaterialExpressionStaticSwitchParameter_6": (-3200, 4600),
    "MaterialExpressionTextureSampleParameter2D_22": (-2800, 4600),
    # Exported mask gates and painted layer weights.
    "MaterialExpressionScalarParameter_39": (-3200, 5000),
    "MaterialExpressionTextureSampleParameter2D_19": (-2800, 5000),
    "MaterialExpressionLandscapeLayerSample_0": (-2400, 5000),
    "MaterialExpressionLinearInterpolate_6": (-2000, 5000),
    "MaterialExpressionMultiply_22": (-1600, 5000),
    "MaterialExpressionAdd_2": (-1200, 5000),
    "MaterialExpressionScalarParameter_40": (-3200, 5200),
    "MaterialExpressionTextureSampleParameter2D_20": (-2800, 5200),
    "MaterialExpressionLandscapeLayerSample_1": (-2400, 5200),
    "MaterialExpressionLinearInterpolate_7": (-2000, 5200),
    "MaterialExpressionMultiply_23": (-1600, 5200),
    "MaterialExpressionAdd_3": (-1200, 5200),
    "MaterialExpressionScalarParameter_41": (-3200, 5400),
    "MaterialExpressionTextureSampleParameter2D_21": (-2800, 5400),
    "MaterialExpressionScalarParameter_57": (-3200, 5600),
    "MaterialExpressionTextureSampleParameter2D_24": (-2800, 5600),
    "MaterialExpressionLandscapeLayerSample_4": (-2400, 5600),
    "MaterialExpressionLinearInterpolate_19": (-2000, 5600),
    "MaterialExpressionMultiply_45": (-1600, 5600),
    # Existing mud/path contribution and the final mask coverage sum.
    "MaterialExpressionLandscapeLayerSample_2": (-2400, 5800),
    "MaterialExpressionLandscapeLayerSample_3": (-2400, 6000),
    "MaterialExpressionAdd_4": (-1200, 5800),
    "MaterialExpressionAdd_12": (-800, 5600),
    "MaterialExpressionAdd_5": (-400, 5200),
    "MaterialExpressionSaturate_2": (0, 5200),
}


DESCRIPTIONS = {
    "MaterialExpressionWorldPosition_1": "GAEA PIPELINE | World position (cm)",
    "MaterialExpressionVectorParameter_13": "GAEA PIPELINE | Landscape min (cm)",
    "MaterialExpressionVectorParameter_14": "GAEA PIPELINE | Landscape size (cm)",
    "MaterialExpressionSubtract_5": "GAEA PIPELINE | Subtract landscape min",
    "MaterialExpressionDivide_3": "GAEA PIPELINE | Normalize to 0..1",
    "MaterialExpressionComponentMask_0": "GAEA PIPELINE | Keep world XY",
    "MaterialExpressionSaturate_8": "GAEA PIPELINE | SINGLE UV AUTHORITY (0..1)",
    "MaterialExpressionStaticSwitchParameter_10": "GAEA COLOR | Snow | whole-map UV gate",
    "MaterialExpressionTextureSampleParameter2D_0": "GAEA COLOR | Snow export",
    "MaterialExpressionStaticSwitchParameter_11": "GAEA COLOR | Water | whole-map UV gate",
    "MaterialExpressionTextureSampleParameter2D_4": "GAEA COLOR | Water export",
    "MaterialExpressionStaticSwitchParameter_5": "GAEA COLOR | Ground legacy | whole-map UV gate",
    "MaterialExpressionTextureSampleParameter2D_18": "GAEA COLOR | Ground legacy source",
    "MaterialExpressionStaticSwitchParameter_7": "GAEA COLOR | Ground | whole-map UV gate",
    "MaterialExpressionTextureSampleParameter2D_6": "GAEA COLOR | Ground export",
    "MaterialExpressionStaticSwitchParameter_8": "GAEA COLOR | Grass | whole-map UV gate",
    "MaterialExpressionTextureSampleParameter2D_8": "GAEA COLOR | Grass export",
    "MaterialExpressionStaticSwitchParameter_9": "GAEA COLOR | Rock | whole-map UV gate",
    "MaterialExpressionTextureSampleParameter2D_11": "GAEA COLOR | Rock export",
    "MaterialExpressionStaticSwitchParameter_6": "GAEA COLOR | Rock legacy | whole-map UV gate",
    "MaterialExpressionTextureSampleParameter2D_22": "GAEA COLOR | Rock legacy source",
    "MaterialExpressionScalarParameter_39": "GAEA MASK | Snow weight",
    "MaterialExpressionTextureSampleParameter2D_19": "GAEA MASK | Snow export",
    "MaterialExpressionLandscapeLayerSample_0": "GAEA MASK | Snow painted layer",
    "MaterialExpressionLinearInterpolate_6": "GAEA MASK | Snow export gate",
    "MaterialExpressionMultiply_22": "GAEA MASK | Snow coverage",
    "MaterialExpressionAdd_2": "GAEA MASK | Snow plus meso coverage",
    "MaterialExpressionScalarParameter_40": "GAEA MASK | Water weight",
    "MaterialExpressionTextureSampleParameter2D_20": "GAEA MASK | Water export",
    "MaterialExpressionLandscapeLayerSample_1": "GAEA MASK | Water painted layer",
    "MaterialExpressionLinearInterpolate_7": "GAEA MASK | Water export gate",
    "MaterialExpressionMultiply_23": "GAEA MASK | Water coverage",
    "MaterialExpressionAdd_3": "GAEA MASK | Water plus frost coverage",
    "MaterialExpressionScalarParameter_41": "GAEA MASK | Flow weight (reserved)",
    "MaterialExpressionTextureSampleParameter2D_21": "GAEA MASK | Flow export (reserved)",
    "MaterialExpressionScalarParameter_57": "GAEA MASK | Rock weight",
    "MaterialExpressionTextureSampleParameter2D_24": "GAEA MASK | Rock export",
    "MaterialExpressionLandscapeLayerSample_4": "GAEA MASK | Rock painted layer",
    "MaterialExpressionLinearInterpolate_19": "GAEA MASK | Rock export gate",
    "MaterialExpressionMultiply_45": "GAEA MASK | Rock coverage",
    "MaterialExpressionLandscapeLayerSample_2": "GAEA MASK | Mud painted layer",
    "MaterialExpressionLandscapeLayerSample_3": "GAEA MASK | Path painted layer",
    "MaterialExpressionAdd_4": "GAEA MASK | Mud plus Path coverage",
    "MaterialExpressionAdd_12": "GAEA MASK | Rock plus Mud/Path coverage",
    "MaterialExpressionAdd_5": "GAEA MASK | Final coverage sum",
    "MaterialExpressionSaturate_2": "GAEA MASK | Final coverage clamp",
}


def organize():
    material = unreal.load_asset(MASTER_PATH)
    if not material:
        raise RuntimeError("Unable to load " + MASTER_PATH)
    expressions = {e.get_name(): e for e in unreal.MaterialEditingLibrary.get_material_expressions(material)}
    moved = []
    missing = []
    for name, (x, y) in POSITIONS.items():
        expression = expressions.get(name)
        if not expression:
            missing.append(name)
            continue
        old = unreal.MaterialEditingLibrary.get_material_expression_node_position(expression)
        expression.set_editor_property("material_expression_editor_x", int(x))
        expression.set_editor_property("material_expression_editor_y", int(y))
        if name in DESCRIPTIONS:
            expression.set_editor_property("desc", DESCRIPTIONS[name])
        moved.append({"name": name, "old": list(old), "new": [int(x), int(y)]})

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.MaterialEditingLibrary.refresh_material_editor(material)
    result = {
        "master": MASTER_PATH,
        "moved_count": len(moved),
        "missing": missing,
        "connections_changed": False,
        "camera_touched": False,
        "material_dirty": True,
        "moved": moved,
    }
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    organize()
