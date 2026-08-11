"""Add the neutral-by-default, Rock-only triplanar lane without rebuilding Landscape."""

import unreal

import material_lib as lib


MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
ACTIVE = f"{MASTER_DIR}/M_Master_Toon_Landscape_HeightBlend"
WORK_BASE = f"{MASTER_DIR}/M_Master_Toon_Landscape_HeightBlend_TRIPLANAR_WORK_20260729"
CHECKPOINT_BASE = f"{MASTER_DIR}/M_Master_Toon_Landscape_HeightBlend_LIVING_STORYBOOK_PRETRIPLANAR_20260729"
# UE 5.8 ships the supported WorldAlignedTexture function in the 01 library;
# the similarly named 02 path is a legacy redirect target and is absent from
# the headless Asset Registry.
WORLD_ALIGNED_TEXTURE = "/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture.WorldAlignedTexture"
GROUP = "02 | Rock Projection"


def unique_path(base):
    if not unreal.EditorAssetLibrary.does_asset_exist(base):
        return base
    index = 2
    while unreal.EditorAssetLibrary.does_asset_exist(f"{base}_{index:02d}"):
        index += 1
    return f"{base}_{index:02d}"


def duplicate(source_path, destination_path):
    source = unreal.EditorAssetLibrary.load_asset(source_path)
    folder, name = destination_path.rsplit("/", 1)
    copied = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name, folder, source)
    if not copied:
        raise RuntimeError(f"Duplicate failed: {source_path} -> {destination_path}")
    unreal.EditorAssetLibrary.save_loaded_asset(copied)
    return copied


def expressions(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def parameter(material, name):
    for expression in expressions(material):
        if "Parameter" not in type(expression).__name__:
            continue
        try:
            if str(expression.get_editor_property("parameter_name")) == name:
                return expression
        except Exception:
            pass
    return None


def scalar(material, name, default, y):
    existing = parameter(material, name)
    if existing:
        return existing
    return lib.scalar_param(material, name, GROUP, default, 10400, y)


def input_mapping(material, expression):
    names = list(unreal.MaterialEditingLibrary.get_material_expression_input_names(expression) or [])
    inputs = list(unreal.MaterialEditingLibrary.get_inputs_for_material_expression(material, expression) or [])
    return {name: inputs[index] for index, name in enumerate(names) if index < len(inputs)}


def patch(material):
    all_expressions = expressions(material)
    rock_texture = parameter(material, "Rock_Albedo")
    rock_tint = parameter(material, "RockTint")
    debug_switch = parameter(material, "bLandscapeDebugMasks")
    rock_layer = next((expr for expr in all_expressions if "LandscapeLayerSample" in type(expr).__name__ and str(expr.get_editor_property("parameter_name")) == "Rock"), None)
    if not all((rock_texture, rock_tint, debug_switch, rock_layer)):
        raise RuntimeError("Missing Rock texture/tint/layer or final debug switch")

    debug_inputs = input_mapping(material, debug_switch)
    base_color = debug_inputs.get("False")
    if not base_color:
        raise RuntimeError("Could not preserve the pre-debug BaseColor chain")

    tiling = scalar(material, "TriplanarTiling", 256.0, 0)
    blend = scalar(material, "TriplanarBlend", 0.0, 80)
    slope_start = scalar(material, "TriplanarSlopeStart", 0.35, 160)
    slope_end = scalar(material, "TriplanarSlopeEnd", 0.72, 240)

    world_aligned = unreal.EditorAssetLibrary.load_asset(WORLD_ALIGNED_TEXTURE)
    if not world_aligned:
        raise RuntimeError(f"Missing engine WorldAlignedTexture function: {WORLD_ALIGNED_TEXTURE}")
    projection = lib.create_expression(material, unreal.MaterialExpressionMaterialFunctionCall, 10600, 60)
    projection.set_editor_property("material_function", world_aligned)
    lib.connect(rock_texture, "Texture", projection, "TextureObject")
    lib.connect(tiling, "", projection, "TextureSize")
    tri_tinted = lib.create_expression(material, unreal.MaterialExpressionMultiply, 10800, 60)
    lib.connect(projection, "", tri_tinted, "A"); lib.connect(rock_tint, "", tri_tinted, "B")

    normal = lib.create_expression(material, unreal.MaterialExpressionPixelNormalWS, 10600, 340)
    up = lib.create_expression(material, unreal.MaterialExpressionConstant3Vector, 10600, 440)
    up.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 0.0))
    dot = lib.create_expression(material, unreal.MaterialExpressionDotProduct, 10800, 340)
    lib.connect(normal, "", dot, "A"); lib.connect(up, "", dot, "B")
    steepness = lib.create_expression(material, unreal.MaterialExpressionOneMinus, 11000, 340)
    lib.connect_unary(dot, steepness)
    start_sub = lib.create_expression(material, unreal.MaterialExpressionSubtract, 11200, 340)
    span = lib.create_expression(material, unreal.MaterialExpressionSubtract, 11200, 440)
    lib.connect(steepness, "", start_sub, "A"); lib.connect(slope_start, "", start_sub, "B")
    lib.connect(slope_end, "", span, "A"); lib.connect(slope_start, "", span, "B")
    normalized = lib.create_expression(material, unreal.MaterialExpressionDivide, 11400, 340)
    lib.connect(start_sub, "", normalized, "A"); lib.connect(span, "", normalized, "B")
    slope_mask = lib.create_expression(material, unreal.MaterialExpressionSaturate, 11600, 340)
    lib.connect_unary(normalized, slope_mask)
    weight = lib.create_expression(material, unreal.MaterialExpressionMultiply, 11800, 340)
    lib.connect(slope_mask, "", weight, "A"); lib.connect(rock_layer, "", weight, "B")
    weighted_blend = lib.create_expression(material, unreal.MaterialExpressionMultiply, 12000, 340)
    lib.connect(weight, "", weighted_blend, "A"); lib.connect(blend, "", weighted_blend, "B")
    final_color = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, 12200, 180)
    lib.connect(base_color, "", final_color, "A"); lib.connect(tri_tinted, "", final_color, "B")
    lib.connect(weighted_blend, "", final_color, "Alpha")
    lib.connect(final_color, "", debug_switch, "False")

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)


def main():
    candidate_path = unique_path(WORK_BASE)
    candidate = duplicate(ACTIVE, candidate_path)
    patch(candidate)
    checkpoint = unique_path(CHECKPOINT_BASE)
    duplicate(ACTIVE, checkpoint)
    if not unreal.EditorAssetLibrary.delete_asset(ACTIVE):
        raise RuntimeError(f"Unable to promote triplanar candidate: {ACTIVE}")
    duplicate(candidate_path, ACTIVE)
    unreal.log(f"[LandscapeTriplanar] promoted={candidate_path} checkpoint={checkpoint}")


main()
