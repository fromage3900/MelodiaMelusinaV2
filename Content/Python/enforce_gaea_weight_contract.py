"""Make Gaea mask blend weights safe at the master graph boundary.

Instance values are still audited and repaired separately, but every exported
weight is clamped here as well. This prevents a stray instance override (for
example 4.56) from driving a Lerp outside 0..1 and suppressing the whole
extended-layer branch. The utility is idempotent and never touches a level,
viewport, or camera.
"""

import json
import unreal


MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape"

LANES = {
    "Snow": {
        "scalar": "Gaea_SnowWeight",
        "target": "MaterialExpressionLinearInterpolate_6",
        "position": (-2400, 4800),
    },
    "Water": {
        "scalar": "Gaea_WaterWeight",
        "target": "MaterialExpressionLinearInterpolate_7",
        "position": (-2400, 5100),
    },
    "Rock": {
        "scalar": "Gaea_RockWeight",
        "target": "MaterialExpressionLinearInterpolate_19",
        "position": (-2400, 5500),
    },
    "Flow": {
        "scalar": "Gaea_FlowWeight",
        "target": "MaterialExpressionLinearInterpolate_10",
        "position": (-2400, 5300),
    },
}


def _expressions(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def _find_by_name(expressions, name):
    return next((expression for expression in expressions if expression.get_name() == name), None)


def _find_scalar(expressions, parameter):
    for expression in expressions:
        if expression.get_class().get_name() != "MaterialExpressionScalarParameter":
            continue
        try:
            if str(expression.get_editor_property("parameter_name")) == parameter:
                return expression
        except Exception:
            pass
    return None


def _find_clamp(expressions, lane):
    marker = "%s weight clamp" % lane
    for expression in expressions:
        if expression.get_class().get_name() != "MaterialExpressionSaturate":
            continue
        try:
            if marker in str(expression.get_editor_property("desc")):
                return expression
        except Exception:
            pass
    return None


def _connect(source, target, pin=""):
    result = unreal.MaterialEditingLibrary.connect_material_expressions(source, "", target, pin)
    if result is False:
        raise RuntimeError("Could not connect %s -> %s.%s" % (source.get_name(), target.get_name(), pin))


def run():
    material = unreal.load_asset(MASTER_PATH) or unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if material is None:
        raise RuntimeError("Missing landscape master: %s" % MASTER_PATH)
    expressions = _expressions(material)
    result = {"master": MASTER_PATH, "lanes": {}, "camera_touched": False, "level_touched": False}
    for lane, spec in LANES.items():
        scalar = _find_scalar(expressions, spec["scalar"])
        target = _find_by_name(expressions, spec["target"])
        if scalar is None or target is None:
            raise RuntimeError("Missing %s weight or target" % lane)
        clamp = _find_clamp(expressions, lane)
        created = False
        if clamp is None:
            clamp = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionSaturate, spec["position"][0], spec["position"][1]
            )
            if clamp is None:
                raise RuntimeError("Could not create %s weight clamp" % lane)
            created = True
        clamp.set_editor_property("desc", "GAEA MASK | %s weight clamp (0..1)" % lane)
        clamp.set_editor_property("material_expression_editor_x", int(spec["position"][0]))
        clamp.set_editor_property("material_expression_editor_y", int(spec["position"][1]))
        _connect(scalar, clamp)
        _connect(clamp, target, "Alpha")
        result["lanes"][lane] = {
            "scalar": scalar.get_name(),
            "clamp": clamp.get_name(),
            "target": target.get_name(),
            "created": created,
        }
        expressions = _expressions(material)

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, False)
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    run()
