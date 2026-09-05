"""Clamp normalized Gaea UVs before every whole-landscape sample.

The Gaea exports are one 0..1 image for the authored landscape.  The existing
graph already derives world-space normalized coordinates from the landscape
actor bounds, but it fed those coordinates directly into wrap-addressed
texture samples.  A small amount of world-position drift at a tile edge could
therefore wrap the image and look like tiling.  This edit inserts one shared
Saturate node after the XY component mask and routes all Gaea-coordinate
consumers through it; layer-coordinate fallbacks remain untouched.
"""

import unreal


MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape"


def _expressions(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def _find(material, class_name, name):
    for expression in _expressions(material):
        if expression.get_class().get_name() != class_name:
            continue
        if expression.get_name() == name:
            return expression
    return None


def _connect(source, source_pin, target, target_pin):
    result = unreal.MaterialEditingLibrary.connect_material_expressions(
        source, source_pin, target, target_pin
    )
    # UE Python returns None on a successful connection in some 5.8 builds;
    # only an explicit False is failure.
    if result is False:
        raise RuntimeError(
            "Could not connect %s.%s -> %s.%s"
            % (source.get_name(), source_pin, target.get_name(), target_pin)
        )


def run():
    material = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if material is None:
        raise RuntimeError("Missing landscape master: %s" % MASTER_PATH)

    component = _find(material, "MaterialExpressionComponentMask", "MaterialExpressionComponentMask_0")
    if component is None:
        raise RuntimeError("Missing normalized Gaea ComponentMask_0")

    # Reuse the node if this repair is rerun.  A description is less brittle
    # than relying on the generated expression suffix.
    saturate = next(
        (
            expression
            for expression in _expressions(material)
            if expression.get_class().get_name() == "MaterialExpressionSaturate"
            and "Gaea normalized UV clamp" in str(expression.get_editor_property("desc"))
        ),
        None,
    )
    if saturate is None:
        saturate = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionSaturate, -11600, -520
        )
        saturate.set_editor_property("desc", "Gaea normalized UV clamp (0..1)")

    _connect(component, "", saturate, "")

    # All current consumers of ComponentMask_0 are either normalized Gaea
    # coordinates (True branches and the frost/SDF map) or their fallback
    # layer coordinates.  Preserve every fallback and replace only the
    # normalized input side.
    consumer_names = [
        "MaterialExpressionStaticSwitchParameter_5",
        "MaterialExpressionStaticSwitchParameter_6",
        "MaterialExpressionStaticSwitchParameter_7",
        "MaterialExpressionStaticSwitchParameter_8",
        "MaterialExpressionStaticSwitchParameter_9",
        "MaterialExpressionStaticSwitchParameter_10",
        "MaterialExpressionStaticSwitchParameter_11",
        "MaterialExpressionTextureSampleParameter2D_19",
        "MaterialExpressionTextureSampleParameter2D_20",
        "MaterialExpressionTextureSampleParameter2D_21",
        "MaterialExpressionTextureSampleParameter2D_23",
    ]
    rewired = []
    for name in consumer_names:
        target = _find(material, name.split("_")[0], name)
        if target is None:
            # The split above is intentionally not used for class lookup in
            # the normal path; fall back to an exact generated class prefix.
            target = next((e for e in _expressions(material) if e.get_name() == name), None)
        if target is None:
            raise RuntimeError("Missing normalized Gaea consumer: %s" % name)
        # TextureSampleParameter2D exposes its coordinate input as UVs in UE
        # Python (the Monolith graph serializer calls the same pin
        # Coordinates); static switches use their literal True branch.
        pin = "UVs" if "TextureSampleParameter2D" in target.get_class().get_name() else "True"
        _connect(saturate, "", target, pin)
        rewired.append(name)

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, False)
    return {
        "material": MASTER_PATH,
        "clamp_node": saturate.get_name(),
        "rewired_consumers": rewired,
    }


if __name__ == "__main__":
    print(run())
