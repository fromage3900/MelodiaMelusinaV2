"""Non-destructive Living Storybook upgrade for the restored Landscape master.

The script works on a duplicate candidate, never clears a material graph, and
promotes the candidate to the active package path only after recompilation.
The Global Distance Field lane remains mesh-side; this Landscape only uses an
analytic, Wonder-painted SDF mask.
"""

from __future__ import annotations

import unreal

import material_lib as lib
import portfolio_landscape_textures as terrain_textures


MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
FUNCTION_DIR = "/Game/EnvSandbox/Materials/Functions"
ACTIVE = f"{MASTER_DIR}/M_Master_Toon_Landscape_HeightBlend"
CHECKPOINT_BASE = f"{MASTER_DIR}/M_Master_Toon_Landscape_HeightBlend_AUTHORED_RESTORED_20260729"
CANDIDATE_BASE = f"{MASTER_DIR}/M_Master_Toon_Landscape_HeightBlend_LIVING_STORYBOOK_WORK_20260729"

SDF_FUNCTION = f"{FUNCTION_DIR}/MF_LandscapeStorybookSDF"
DISTANCE_FUNCTION = f"{FUNCTION_DIR}/MF_LandscapeDistanceBands"
MACRO_FUNCTION = f"{FUNCTION_DIR}/MF_LandscapeMacroVariation"

GROUP_BLEND = "03 | Landscape Blend"
GROUP_PBR = "04 | Layer PBR"
GROUP_MACRO = "05 | Macro Detail"
GROUP_DISTANCE = "06 | Distance Bands"
GROUP_WONDER = "07 | Wonder Storybook SDF"
GROUP_QUALITY = "08 | Landscape Quality"
GROUP_DEBUG = "99 | Landscape Debug"


def asset_path(package_path: str) -> str:
    return f"{package_path}.{package_path.rsplit('/', 1)[-1]}"


def unique_path(base: str) -> str:
    if not unreal.EditorAssetLibrary.does_asset_exist(base):
        return base
    index = 2
    while unreal.EditorAssetLibrary.does_asset_exist(f"{base}_{index:02d}"):
        index += 1
    return f"{base}_{index:02d}"


def duplicate_material(source_path: str, destination_path: str) -> unreal.Material:
    source = unreal.EditorAssetLibrary.load_asset(source_path)
    if not isinstance(source, unreal.Material):
        raise RuntimeError(f"Expected material source: {source_path}")
    folder, name = destination_path.rsplit("/", 1)
    copied = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name, folder, source)
    if not isinstance(copied, unreal.Material):
        raise RuntimeError(f"Could not duplicate {source_path} -> {destination_path}")
    unreal.EditorAssetLibrary.save_loaded_asset(copied)
    return copied


def function_input(function, name: str, x: int, y: int, default: float):
    node = lib.create_expression(function, unreal.MaterialExpressionFunctionInput, x, y)
    node.set_editor_property("input_name", name)
    try:
        node.set_editor_property("input_type", unreal.FunctionInputType.FIT1)
    except Exception:
        pass
    for property_name in ("preview_value", "preview_value_float"):
        try:
            node.set_editor_property(property_name, default)
            break
        except Exception:
            pass
    return node


def function_output(function, source, output_name: str, x: int, y: int):
    node = lib.create_expression(function, unreal.MaterialExpressionFunctionOutput, x, y)
    node.set_editor_property("output_name", output_name)
    lib.connect(source, "", node, "")
    return node


def create_function(name: str, builder) -> unreal.MaterialFunction:
    path = f"{FUNCTION_DIR}/{name}"
    existing = unreal.EditorAssetLibrary.load_asset(asset_path(path))
    if isinstance(existing, unreal.MaterialFunction):
        return existing
    unreal.EditorAssetLibrary.make_directory(FUNCTION_DIR)
    function = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, FUNCTION_DIR, unreal.MaterialFunction, unreal.MaterialFunctionFactoryNew()
    )
    if not isinstance(function, unreal.MaterialFunction):
        raise RuntimeError(f"Unable to create material function {path}")
    builder(function)
    if hasattr(unreal.MaterialEditingLibrary, "recompile_material_function"):
        unreal.MaterialEditingLibrary.recompile_material_function(function)
    unreal.EditorAssetLibrary.save_loaded_asset(function)
    return function


def build_storybook_sdf(function):
    world = lib.create_expression(function, unreal.MaterialExpressionWorldPosition, -1300, 0)
    xy = lib.create_expression(function, unreal.MaterialExpressionComponentMask, -1140, 0)
    xy.set_editor_property("r", True); xy.set_editor_property("g", True)
    xy.set_editor_property("b", False); xy.set_editor_property("a", False)
    lib.connect(world, "", xy, "Input")
    scale = function_input(function, "Scale", -1300, 150, 0.00045)
    scaled = lib.create_expression(function, unreal.MaterialExpressionMultiply, -960, 0)
    lib.connect(xy, "", scaled, "A"); lib.connect(scale, "", scaled, "B")
    cell = lib.create_expression(function, unreal.MaterialExpressionFrac, -780, 0)
    lib.connect_unary(scaled, cell)
    radius = function_input(function, "Radius", -780, 160, 0.19)
    softness = function_input(function, "Softness", -780, 270, 0.05)

    distances = []
    for index, (cx, cy) in enumerate(((0.50, 0.32), (0.68, 0.50), (0.50, 0.68), (0.32, 0.50))):
        center = lib.create_expression(function, unreal.MaterialExpressionConstant2Vector, -600, index * 100)
        center.set_editor_property("r", cx); center.set_editor_property("g", cy)
        distance = lib.create_expression(function, unreal.MaterialExpressionDistance, -420, index * 100)
        lib.connect(cell, "", distance, "A"); lib.connect(center, "", distance, "B")
        distances.append(distance)

    union = distances[0]
    for index, distance in enumerate(distances[1:], 1):
        minimum = lib.create_expression(function, unreal.MaterialExpressionMin, -200 + index * 130, 80)
        lib.connect(union, "", minimum, "A"); lib.connect(distance, "", minimum, "B")
        union = minimum
    signed = lib.create_expression(function, unreal.MaterialExpressionSubtract, 280, 80)
    lib.connect(radius, "", signed, "A"); lib.connect(union, "", signed, "B")
    normalized = lib.create_expression(function, unreal.MaterialExpressionDivide, 480, 80)
    lib.connect(signed, "", normalized, "A"); lib.connect(softness, "", normalized, "B")
    mask = lib.create_expression(function, unreal.MaterialExpressionSaturate, 680, 80)
    lib.connect_unary(normalized, mask)
    function_output(function, mask, "Mask", 880, 80)


def build_distance_bands(function):
    world = lib.create_expression(function, unreal.MaterialExpressionWorldPosition, -1200, 0)
    camera = lib.create_expression(function, unreal.MaterialExpressionCameraPositionWS, -1200, 100)
    distance = lib.create_expression(function, unreal.MaterialExpressionDistance, -980, 0)
    lib.connect(world, "", distance, "A"); lib.connect(camera, "", distance, "B")
    near_start = function_input(function, "NearStart", -1200, 250, 0.0)
    near_end = function_input(function, "NearEnd", -1200, 350, 2500.0)
    far_start = function_input(function, "FarStart", -1200, 450, 8000.0)
    far_end = function_input(function, "FarEnd", -1200, 550, 30000.0)

    near_num = lib.create_expression(function, unreal.MaterialExpressionSubtract, -760, 0)
    near_den = lib.create_expression(function, unreal.MaterialExpressionSubtract, -760, 100)
    lib.connect(distance, "", near_num, "A"); lib.connect(near_start, "", near_num, "B")
    lib.connect(near_end, "", near_den, "A"); lib.connect(near_start, "", near_den, "B")
    near_div = lib.create_expression(function, unreal.MaterialExpressionDivide, -560, 0)
    lib.connect(near_num, "", near_div, "A"); lib.connect(near_den, "", near_div, "B")
    near_sat = lib.create_expression(function, unreal.MaterialExpressionSaturate, -360, 0)
    lib.connect_unary(near_div, near_sat)
    near_weight = lib.create_expression(function, unreal.MaterialExpressionOneMinus, -160, 0)
    lib.connect_unary(near_sat, near_weight)

    far_num = lib.create_expression(function, unreal.MaterialExpressionSubtract, -760, 220)
    far_den = lib.create_expression(function, unreal.MaterialExpressionSubtract, -760, 320)
    lib.connect(distance, "", far_num, "A"); lib.connect(far_start, "", far_num, "B")
    lib.connect(far_end, "", far_den, "A"); lib.connect(far_start, "", far_den, "B")
    far_div = lib.create_expression(function, unreal.MaterialExpressionDivide, -560, 220)
    lib.connect(far_num, "", far_div, "A"); lib.connect(far_den, "", far_div, "B")
    far_weight = lib.create_expression(function, unreal.MaterialExpressionSaturate, -360, 220)
    lib.connect_unary(far_div, far_weight)
    function_output(function, near_weight, "NearWeight", 120, 0)
    function_output(function, far_weight, "FarWeight", 120, 220)


def build_macro_variation(function):
    world = lib.create_expression(function, unreal.MaterialExpressionWorldPosition, -1000, 0)
    xy = lib.create_expression(function, unreal.MaterialExpressionComponentMask, -820, 0)
    xy.set_editor_property("r", True); xy.set_editor_property("g", True)
    xy.set_editor_property("b", False); xy.set_editor_property("a", False)
    lib.connect(world, "", xy, "Input")
    scale = function_input(function, "Scale", -1000, 160, 0.0004)
    seed = function_input(function, "Seed", -1000, 260, 0.0)
    scaled = lib.create_expression(function, unreal.MaterialExpressionMultiply, -620, 0)
    lib.connect(xy, "", scaled, "A"); lib.connect(scale, "", scaled, "B")
    seeded = lib.create_expression(function, unreal.MaterialExpressionAdd, -420, 0)
    lib.connect(scaled, "", seeded, "A"); lib.connect(seed, "", seeded, "B")
    noise = lib.create_expression(function, unreal.MaterialExpressionNoise, -220, 0)
    lib.connect(seeded, "", noise, "Position")
    mask = lib.create_expression(function, unreal.MaterialExpressionSaturate, 0, 0)
    lib.connect_unary(noise, mask)
    function_output(function, mask, "Mask", 180, 0)


def material_expressions(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def find_parameter(material, name: str):
    for expr in material_expressions(material):
        if "Parameter" not in type(expr).__name__:
            continue
        try:
            if str(expr.get_editor_property("parameter_name")) == name:
                return expr
        except Exception:
            pass
    return None


def scalar(material, name: str, group: str, default: float, x: int, y: int):
    existing = find_parameter(material, name)
    return existing if existing else lib.scalar_param(material, name, group, default, x, y)


def vector(material, name: str, group: str, default, x: int, y: int):
    existing = find_parameter(material, name)
    return existing if existing else lib.vector_param(material, name, group, default, x, y)


def static_switch(material, name: str, group: str, default: bool, x: int, y: int):
    existing = find_parameter(material, name)
    if existing:
        return existing
    node = lib.create_expression(material, unreal.MaterialExpressionStaticSwitchParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("group", group)
    node.set_editor_property("default_value", default)
    return node


def texture_parameter(material, name: str, group: str, fallback_paths, x: int, y: int):
    existing = find_parameter(material, name)
    if existing:
        return existing
    node = lib.texture_param(material, name, group, x, y)
    resolved = lib.resolve_texture_path(fallback_paths)
    if resolved:
        lib.set_expression_texture(node, resolved)
    return node


def function_call(material, function_path: str, x: int, y: int):
    function = unreal.EditorAssetLibrary.load_asset(asset_path(function_path))
    if not isinstance(function, unreal.MaterialFunction):
        raise RuntimeError(f"Missing function {function_path}")
    node = lib.create_expression(material, unreal.MaterialExpressionMaterialFunctionCall, x, y)
    node.set_editor_property("material_function", function)
    return node


def constant(material, value: float, x: int, y: int):
    node = lib.create_expression(material, unreal.MaterialExpressionConstant, x, y)
    node.set_editor_property("r", value)
    return node


def multiply(material, a, b, x: int, y: int, a_out: str = "", b_out: str = ""):
    node = lib.create_expression(material, unreal.MaterialExpressionMultiply, x, y)
    lib.connect(a, a_out, node, "A"); lib.connect(b, b_out, node, "B")
    return node


def add(material, a, b, x: int, y: int, a_out: str = "", b_out: str = ""):
    node = lib.create_expression(material, unreal.MaterialExpressionAdd, x, y)
    lib.connect(a, a_out, node, "A"); lib.connect(b, b_out, node, "B")
    return node


def lerp(material, a, b, alpha, x: int, y: int, alpha_out: str = ""):
    node = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, x, y)
    lib.connect(a, "", node, "A"); lib.connect(b, "", node, "B"); lib.connect(alpha, alpha_out, node, "Alpha")
    return node


def component_r(material, source, x: int, y: int):
    node = lib.create_expression(material, unreal.MaterialExpressionComponentMask, x, y)
    node.set_editor_property("r", True); node.set_editor_property("g", False)
    node.set_editor_property("b", False); node.set_editor_property("a", False)
    lib.connect(source, "", node, "Input")
    return node


def input_mapping(material, expression):
    pins = list(unreal.MaterialEditingLibrary.get_material_expression_input_names(expression) or [])
    inputs = list(unreal.MaterialEditingLibrary.get_inputs_for_material_expression(material, expression) or [])
    return {pin: inputs[index] for index, pin in enumerate(pins) if index < len(inputs)}


def patch_candidate(material):
    expressions = material_expressions(material)
    toon = next((expr for expr in expressions if "SubstrateToonBSDF" in type(expr).__name__), None)
    if not toon:
        raise RuntimeError("Landscape candidate has no Substrate Toon BSDF")
    inputs = input_mapping(material, toon)
    base_source = inputs.get("BaseColor")
    roughness_source = inputs.get("Roughness")
    normal_source = inputs.get("Normal")
    emissive_source = inputs.get("EmissiveColor")
    if not all((base_source, roughness_source, normal_source, emissive_source)):
        raise RuntimeError("Landscape candidate is missing one or more authored Toon BSDF inputs")

    layer_samples = {}
    for expression in expressions:
        if "LandscapeLayerSample" not in type(expression).__name__:
            continue
        try:
            layer_samples[str(expression.get_editor_property("parameter_name"))] = expression
        except Exception:
            pass
    for layer in ("Rock", "Grass", "Mud", "Path"):
        if layer not in layer_samples:
            raise RuntimeError(f"Landscape candidate is missing its {layer} paint layer")
    wonder = layer_samples.get("Wonder")
    if not wonder:
        wonder = lib.create_expression(material, unreal.MaterialExpressionLandscapeLayerSample, 8400, 1640)
        wonder.set_editor_property("parameter_name", "Wonder")

    # Direct material parameters are intentionally neutral; existing instances
    # keep their established look until a zone or capture profile opts in.
    macro_strength = scalar(material, "MacroVariationStrength", GROUP_MACRO, 0.0, 7200, 200)
    macro_scale = scalar(material, "MacroScale", GROUP_MACRO, 0.0004, 7200, 280)
    macro_seed = scalar(material, "MacroSeed", GROUP_MACRO, 0.0, 7200, 360)
    rock_macro = scalar(material, "RockMacroStrength", GROUP_MACRO, 0.72, 7200, 440)
    grass_macro = scalar(material, "GrassMacroStrength", GROUP_MACRO, 1.0, 7200, 520)
    mud_macro = scalar(material, "MudMacroStrength", GROUP_MACRO, 0.64, 7200, 600)
    path_macro = scalar(material, "PathMacroStrength", GROUP_MACRO, 0.48, 7200, 680)
    macro_low = vector(material, "MacroTintLow", GROUP_MACRO, (0.92, 0.95, 0.90, 1.0), 7200, 760)
    macro_high = vector(material, "MacroTintHigh", GROUP_MACRO, (1.05, 1.02, 1.08, 1.0), 7200, 840)

    near_strength = scalar(material, "NearDetailStrength", GROUP_DISTANCE, 0.0, 7200, 980)
    near_start = scalar(material, "NearDetailStart", GROUP_DISTANCE, 0.0, 7200, 1060)
    near_end = scalar(material, "NearDetailEnd", GROUP_DISTANCE, 2500.0, 7200, 1140)
    detail_tiling = scalar(material, "DetailTiling", GROUP_DISTANCE, 0.006, 7200, 1220)
    detail_normal = texture_parameter(
        material, "DetailNormal", GROUP_DISTANCE,
        terrain_textures.resolve_layer_textures("Grass")["Normal"], 7200, 1300,
    )
    far_strength = scalar(material, "FarAtmosphereStrength", GROUP_DISTANCE, 0.0, 7200, 1380)
    far_start = scalar(material, "FarAtmosphereStart", GROUP_DISTANCE, 8000.0, 7200, 1460)
    far_end = scalar(material, "FarAtmosphereEnd", GROUP_DISTANCE, 30000.0, 7200, 1540)
    far_color = vector(material, "FarAtmosphereColor", GROUP_DISTANCE, (0.62, 0.72, 0.82, 1.0), 7200, 1620)

    path_edge = scalar(material, "PathEdgeStrength", GROUP_BLEND, 0.0, 7200, 1780)
    path_roughness = scalar(material, "PathRoughnessDarken", GROUP_BLEND, 0.12, 7200, 1860)

    wonder_strength = scalar(material, "WonderStrength", GROUP_WONDER, 0.0, 7200, 2020)
    wonder_palette = vector(material, "WonderPalette", GROUP_WONDER, (0.92, 0.72, 0.88, 1.0), 7200, 2100)
    wonder_sparkle = scalar(material, "WonderSparkleBoost", GROUP_WONDER, 0.0, 7200, 2180)
    sdf_scale = scalar(material, "StorybookSDFScale", GROUP_WONDER, 0.00045, 7200, 2260)
    sdf_radius = scalar(material, "StorybookSDFRadius", GROUP_WONDER, 0.19, 7200, 2340)
    sdf_softness = scalar(material, "StorybookSDFSoftness", GROUP_WONDER, 0.05, 7200, 2420)
    audio_strength = scalar(material, "AudioReactiveStrength", GROUP_WONDER, 0.0, 7200, 2500)

    hero = static_switch(material, "bLandscapeHeroTier", GROUP_QUALITY, False, 7200, 2660)
    fast = static_switch(material, "bLandscapeFastTier", GROUP_QUALITY, False, 7200, 2740)
    use_orm = static_switch(material, "bUseLayerORM", GROUP_PBR, False, 7200, 2820)
    debug_masks = static_switch(material, "bLandscapeDebugMasks", GROUP_DEBUG, False, 7200, 2900)
    for name, y in (("bLandscapeDebugHeight", 2980), ("bLandscapeDebugPath", 3060),
                    ("bLandscapeDebugSlope", 3140), ("bLandscapeDebugDistance", 3220),
                    ("bLandscapeDebugWonder", 3300)):
        static_switch(material, name, GROUP_DEBUG, False, 7200, y)

    macro_call = function_call(material, MACRO_FUNCTION, 7600, 200)
    lib.connect(macro_scale, "", macro_call, "Scale"); lib.connect(macro_seed, "", macro_call, "Seed")
    macro_layer = add(
        material,
        add(material, multiply(material, layer_samples["Rock"], rock_macro, 7800, 380),
            multiply(material, layer_samples["Grass"], grass_macro, 8000, 380), 8200, 380),
        add(material, multiply(material, layer_samples["Mud"], mud_macro, 7800, 470),
            multiply(material, layer_samples["Path"], path_macro, 8000, 470), 8200, 470),
        8400, 420,
    )
    macro_alpha = multiply(material, multiply(material, macro_call, macro_layer, 8600, 360, "Mask"), macro_strength, 8800, 360)
    macro_tint = lerp(material, macro_low, macro_high, macro_call, 8600, 520, "Mask")
    macro_color = multiply(material, base_source, macro_tint, 8800, 520)
    after_macro = lerp(material, base_source, macro_color, macro_alpha, 9000, 520)

    distance_call = function_call(material, DISTANCE_FUNCTION, 7600, 1040)
    for pin, node in (("NearStart", near_start), ("NearEnd", near_end), ("FarStart", far_start), ("FarEnd", far_end)):
        lib.connect(node, "", distance_call, pin)
    far_alpha = multiply(material, distance_call, far_strength, 7800, 1240, "FarWeight")
    after_far = lerp(material, after_macro, far_color, far_alpha, 8000, 1240)

    sdf_call = function_call(material, SDF_FUNCTION, 7600, 2040)
    for pin, node in (("Scale", sdf_scale), ("Radius", sdf_radius), ("Softness", sdf_softness)):
        lib.connect(node, "", sdf_call, pin)
    wonder_mask = multiply(material, wonder, sdf_call, 7800, 2200, "Mask")
    wonder_mask = multiply(material, wonder_mask, wonder_strength, 8000, 2200)
    zero = constant(material, 0.0, 7800, 2320)
    hero_wonder = static_switch(material, "bLandscapeHeroTier", GROUP_QUALITY, False, 8200, 2320)
    lib.connect(wonder_mask, "", hero_wonder, "True"); lib.connect(zero, "", hero_wonder, "False")
    quality_wonder = static_switch(material, "bLandscapeFastTier", GROUP_QUALITY, False, 8400, 2320)
    lib.connect(zero, "", quality_wonder, "True"); lib.connect(hero_wonder, "", quality_wonder, "False")
    after_wonder = lerp(material, after_far, wonder_palette, quality_wonder, 8600, 2200)

    audio = lib.collection_scalar(material, "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette", "GlobalReactivity", 7600, 2580)
    sakura = lib.collection_scalar(material, "/Game/EnvSandbox/VFX/MPC/MPC_SakuraDream", "SparklePulse", 7600, 2660)
    audio_mix = add(material, audio or zero, sakura or zero, 7800, 2620)
    audio_mix = lib.create_expression(material, unreal.MaterialExpressionSaturate, 8000, 2620)
    lib.connect_unary(add(material, audio or zero, sakura or zero, 7900, 2700), audio_mix)
    sparkle_mask = multiply(material, multiply(material, quality_wonder, wonder_sparkle, 8200, 2580), audio_strength, 8400, 2580)
    sparkle_mask = multiply(material, sparkle_mask, audio_mix, 8600, 2580)
    sparkle_color = multiply(material, wonder_palette, sparkle_mask, 8800, 2580)
    after_emissive = add(material, emissive_source, sparkle_color, 9000, 2580)

    # Near detail is optional and sample-safe: CC0 grass normal remains the
    # default until authored maps arrive, while its strength remains zero.
    world = lib.create_expression(material, unreal.MaterialExpressionWorldPosition, 7600, 3420)
    detail_xy = lib.create_expression(material, unreal.MaterialExpressionComponentMask, 7800, 3420)
    detail_xy.set_editor_property("r", True); detail_xy.set_editor_property("g", True)
    detail_xy.set_editor_property("b", False); detail_xy.set_editor_property("a", False)
    lib.connect(world, "", detail_xy, "Input")
    detail_uv = multiply(material, detail_xy, detail_tiling, 8000, 3420)
    detail_sample = lib.create_expression(material, unreal.MaterialExpressionTextureSample, 8200, 3420)
    lib.connect(detail_normal, "Texture", detail_sample, "Texture")
    lib.connect(detail_uv, "", detail_sample, "Coordinates")
    near_alpha = multiply(material, distance_call, near_strength, 8400, 3420, "NearWeight")
    after_normal = lerp(material, normal_source, detail_sample, near_alpha, 8600, 3420)

    path_darken = multiply(material, layer_samples["Path"], path_edge, 7600, 3660)
    path_darken = multiply(material, path_darken, path_roughness, 7800, 3660)
    after_roughness = lib.create_expression(material, unreal.MaterialExpressionSubtract, 8000, 3660)
    lib.connect(roughness_source, "", after_roughness, "A"); lib.connect(path_darken, "", after_roughness, "B")

    # PBR lane: texture nodes are neutral until bUseLayerORM is enabled. Height
    # is the temporary fallback; authored ORM maps replace these per parameter.
    orm_sources = {}
    for index, layer in enumerate(("Rock", "Grass", "Mud", "Path")):
        tex = texture_parameter(material, f"{layer}_ORM", GROUP_PBR, terrain_textures.resolve_layer_textures(layer)["Height"], 7200, 3860 + index * 100)
        sample = lib.create_expression(material, unreal.MaterialExpressionTextureSample, 7400, 3860 + index * 100)
        lib.connect(tex, "Texture", sample, "Texture")
        orm_sources[layer] = component_r(material, sample, 7600, 3860 + index * 100)
    orm_rough = add(material,
        add(material, multiply(material, orm_sources["Rock"], layer_samples["Rock"], 7800, 3920),
            multiply(material, orm_sources["Grass"], layer_samples["Grass"], 8000, 3920), 8200, 3920),
        add(material, multiply(material, orm_sources["Mud"], layer_samples["Mud"], 7800, 4020),
            multiply(material, orm_sources["Path"], layer_samples["Path"], 8000, 4020), 8200, 4020),
        8400, 3980,
    )
    roughness_switch = static_switch(material, "bUseLayerORM", GROUP_PBR, False, 8600, 3980)
    lib.connect(orm_rough, "", roughness_switch, "True"); lib.connect(after_roughness, "", roughness_switch, "False")

    # Debug view is deliberately a single neutral switch: RGB shows Wonder,
    # Path, and far-band masks without changing terrain paint ownership.
    debug_color = lib.connect_append3_from_scalars(wonder, layer_samples["Path"], distance_call, material, 9000, 4060)
    debug_switch = static_switch(material, "bLandscapeDebugMasks", GROUP_DEBUG, False, 9400, 4060)
    lib.connect(debug_color, "", debug_switch, "True"); lib.connect(after_wonder, "", debug_switch, "False")

    lib.connect(debug_switch, "", toon, "BaseColor")
    lib.connect(after_normal, "", toon, "Normal")
    lib.connect(roughness_switch, "", toon, "Roughness")
    lib.connect(after_emissive, "", toon, "EmissiveColor")
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)


def main():
    create_function("MF_LandscapeStorybookSDF", build_storybook_sdf)
    create_function("MF_LandscapeDistanceBands", build_distance_bands)
    create_function("MF_LandscapeMacroVariation", build_macro_variation)

    candidate_path = unique_path(CANDIDATE_BASE)
    candidate = duplicate_material(ACTIVE, candidate_path)
    patch_candidate(candidate)

    checkpoint_path = unique_path(CHECKPOINT_BASE)
    duplicate_material(ACTIVE, checkpoint_path)
    if not unreal.EditorAssetLibrary.delete_asset(ACTIVE):
        raise RuntimeError(f"Could not promote candidate because active package could not be removed: {ACTIVE}")
    duplicate_material(candidate_path, ACTIVE)
    unreal.log(f"[LivingStorybook] Candidate promoted: {candidate_path} -> {ACTIVE}")
    unreal.log(f"[LivingStorybook] Checkpoint retained: {checkpoint_path}")


main()
