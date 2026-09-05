"""Give the converged landscape master explicit Gaea Snow/Rock mask lanes.

The original graph called its Snow mask ``Gaea_SlopeMask`` and had no Rock
mask lane, even though the Glacier contract exports Snow, Water, and Rock
weightmaps.  This repair keeps the existing normalized UV and switches, makes
the Snow parameter semantic, and adds Rock coverage to the existing extended
layer coverage sum.  The Glacier instance supplies the actual exported maps.
"""

import unreal


MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape"
MI_PATH = "/Game/Gaea/Glacier/Materials/MI_Glacier_Landscape_Layered"
DEFAULT_MASK_PATH = "/Game/Textures/sbs_-_gradient_texture_pack_-_512x512/512x512/Basic/Horizontal_1_-_512x512.Horizontal_1_-_512x512"


def _expressions(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def _find(material, class_name=None, parameter_name=None, desc=None, name=None):
    for expression in _expressions(material):
        if class_name and expression.get_class().get_name() != class_name:
            continue
        if name and expression.get_name() != name:
            continue
        if parameter_name is not None:
            try:
                if str(expression.get_editor_property("parameter_name")) != parameter_name:
                    continue
            except Exception:
                continue
        if desc is not None:
            try:
                if str(expression.get_editor_property("desc")) != desc:
                    continue
            except Exception:
                continue
        return expression
    return None


def _connect(source, source_pin, target, target_pin):
    result = unreal.MaterialEditingLibrary.connect_material_expressions(
        source, source_pin, target, target_pin
    )
    if result is False:
        raise RuntimeError(
            "Could not connect %s.%s -> %s.%s"
            % (source.get_name(), source_pin, target.get_name(), target_pin)
        )


def _create(material, cls, x, y, desc=None):
    expression = unreal.MaterialEditingLibrary.create_material_expression(material, cls, x, y)
    if expression is None:
        raise RuntimeError("Could not create %s" % cls.__name__)
    if desc is not None:
        expression.set_editor_property("desc", desc)
    return expression


def run():
    material = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if material is None:
        raise RuntimeError("Missing landscape master: %s" % MASTER_PATH)

    # Preserve the existing graph, but give the exported Snow lane its real
    # semantic name.  Existing downstream connections stay attached to nodes.
    snow_mask = _find(material, "MaterialExpressionTextureSampleParameter2D", "Gaea_SlopeMask")
    snow_weight = _find(material, "MaterialExpressionScalarParameter", "Gaea_SlopeWeight")
    if snow_mask is None or snow_weight is None:
        raise RuntimeError("Existing Snow mask lane could not be resolved")
    snow_mask.set_editor_property("parameter_name", "Gaea_SnowMask")
    snow_weight.set_editor_property("parameter_name", "Gaea_SnowWeight")
    try:
        snow_mask.set_editor_property("group", "03 | Gaea Masks")
        snow_weight.set_editor_property("group", "03 | Gaea Masks")
        snow_weight.set_editor_property("default_value", 1.0)
    except Exception:
        pass

    normalized_uv = _find(material, "MaterialExpressionSaturate", desc="Gaea normalized UV clamp (0..1)")
    if normalized_uv is None:
        raise RuntimeError("Normalized Gaea UV clamp is missing")
    one = _find(material, "MaterialExpressionConstant", name="MaterialExpressionConstant_2")
    add4 = _find(material, "MaterialExpressionAdd", name="MaterialExpressionAdd_4")
    add5 = _find(material, "MaterialExpressionAdd", name="MaterialExpressionAdd_5")
    if one is None or add4 is None or add5 is None:
        raise RuntimeError("Existing extended coverage nodes could not be resolved")

    mask = _find(material, "MaterialExpressionTextureSampleParameter2D", "Gaea_RockMask")
    if mask is None:
        mask = _create(material, unreal.MaterialExpressionTextureSampleParameter2D, -3200, -400)
        mask.set_editor_property("parameter_name", "Gaea_RockMask")
        mask.set_editor_property("texture", unreal.EditorAssetLibrary.load_asset(DEFAULT_MASK_PATH))
        try:
            mask.set_editor_property("group", "03 | Gaea Masks")
            mask.set_editor_property("sort_priority", 42)
        except Exception:
            pass

    weight = _find(material, "MaterialExpressionScalarParameter", "Gaea_RockWeight")
    if weight is None:
        weight = _create(material, unreal.MaterialExpressionScalarParameter, -3200, -250)
        weight.set_editor_property("parameter_name", "Gaea_RockWeight")
        weight.set_editor_property("default_value", 1.0)
        try:
            weight.set_editor_property("group", "03 | Gaea Masks")
            weight.set_editor_property("sort_priority", 43)
        except Exception:
            pass

    layer = _find(material, "MaterialExpressionLandscapeLayerSample", "Rock")
    if layer is None:
        layer = _create(material, unreal.MaterialExpressionLandscapeLayerSample, -2900, -250)
        layer.set_editor_property("parameter_name", "Rock")

    lerp = _find(material, "MaterialExpressionLinearInterpolate", desc="Gaea Rock mask blend")
    if lerp is None:
        lerp = _create(material, unreal.MaterialExpressionLinearInterpolate, -2400, -250, "Gaea Rock mask blend")
    product = _find(material, "MaterialExpressionMultiply", desc="Gaea Rock layer coverage")
    if product is None:
        product = _create(material, unreal.MaterialExpressionMultiply, -2150, -250, "Gaea Rock layer coverage")
    coverage = _find(material, "MaterialExpressionAdd", desc="Gaea coverage plus Rock")
    if coverage is None:
        coverage = _create(material, unreal.MaterialExpressionAdd, -1850, -250, "Gaea coverage plus Rock")

    _connect(normalized_uv, "", mask, "UVs")
    _connect(one, "", lerp, "A")
    _connect(mask, "", lerp, "B")
    _connect(weight, "", lerp, "Alpha")
    _connect(layer, "", product, "A")
    _connect(lerp, "", product, "B")
    _connect(add4, "", coverage, "A")
    _connect(product, "", coverage, "B")
    _connect(coverage, "", add5, "B")

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, False)
    return {
        "master": MASTER_PATH,
        "snow_mask_parameter": "Gaea_SnowMask",
        "rock_mask_parameter": "Gaea_RockMask",
        "rock_weight_parameter": "Gaea_RockWeight",
        "normalized_uv": normalized_uv.get_name(),
        "coverage_node": coverage.get_name(),
    }


if __name__ == "__main__":
    print(run())
