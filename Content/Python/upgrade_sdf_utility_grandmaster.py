"""Additive grandmaster utility layer for M_SDF_UtilityToolkit.

This script is intentionally idempotent. It never clears the existing graph,
deletes expressions, changes existing parameter defaults, or edits engine
assets. It adds tagged nodes and parameters, then reconnects only the three
documented material outputs: World Position Offset, Toon BaseColor, and Toon
Normal.
"""

from __future__ import annotations

import unreal


MATERIAL_PATH = "/Game/EnvSandbox/Materials/SDF/M_SDF_UtilityToolkit"
INSTANCE_DIR = "/Game/EnvSandbox/Materials/SDF/Instances"
TAG_PREFIX = "GMUtility:"


def _log(message: str) -> None:
    unreal.log(f"[SDF Grandmaster] {message}")


def _expressions(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def _get_prop(obj, name: str, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _set_prop(obj, name: str, value) -> None:
    obj.set_editor_property(name, value)


def _find_tag(material, key: str):
    tag = TAG_PREFIX + key
    for expression in _expressions(material):
        if str(_get_prop(expression, "desc", "")) == tag:
            return expression
    return None


def _find_parameter(material, name: str):
    for expression in _expressions(material):
        if str(_get_prop(expression, "parameter_name", "")) == name:
            return expression
    return None


def _find_named(material, name: str):
    for expression in _expressions(material):
        if expression.get_name() == name:
            return expression
    return None


def _create_node(material, cls, key: str, x: int, y: int):
    existing = _find_tag(material, key)
    if existing:
        return existing, False
    node = unreal.MaterialEditingLibrary.create_material_expression(material, cls, x, y)
    if not node:
        raise RuntimeError(f"Could not create material expression {cls.__name__} ({key})")
    _set_prop(node, "desc", TAG_PREFIX + key)
    return node, True


def _parameter(material, cls, name: str, group: str, default, key: str, x: int, y: int):
    existing = _find_parameter(material, name)
    if existing:
        return existing, False
    node, created = _create_node(material, cls, key, x, y)
    _set_prop(node, "parameter_name", name)
    _set_prop(node, "group", group)
    _set_prop(node, "default_value", default)
    return node, created


def _custom(material, key: str, description: str, code: str, inputs, x: int, y: int, output_type=None):
    node, created = _create_node(material, unreal.MaterialExpressionCustom, key, x, y)
    _set_prop(node, "description", description)
    _set_prop(node, "code", code)
    _set_prop(node, "output_type", output_type or unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    custom_inputs = []
    for input_name in inputs:
        custom_input = unreal.CustomInput()
        _set_prop(custom_input, "input_name", input_name)
        custom_inputs.append(custom_input)
    _set_prop(node, "inputs", custom_inputs)
    return node, created


def _connect(source, output, target, input_name) -> None:
    if not unreal.MaterialEditingLibrary.connect_material_expressions(
        source, output, target, input_name
    ):
        raise RuntimeError(
            f"Could not connect {source.get_name()}:{output} -> "
            f"{target.get_name()}:{input_name}"
        )


def _connect_property(source, output, prop) -> None:
    unreal.MaterialEditingLibrary.connect_material_property(source, output, prop)


def _set_transform_local_to_world(node) -> None:
    _set_prop(
        node,
        "transform_source_type",
        unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL,
    )
    _set_prop(node, "transform_type", unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)


def _create_scalar(material, name, default, group, key, x, y):
    return _parameter(
        material,
        unreal.MaterialExpressionScalarParameter,
        name,
        group,
        float(default),
        key,
        x,
        y,
    )[0]


def _create_vector(material, name, default, group, key, x, y):
    return _parameter(
        material,
        unreal.MaterialExpressionVectorParameter,
        name,
        group,
        unreal.LinearColor(*default),
        key,
        x,
        y,
    )[0]


def _add(material, key, a, b, x, y):
    node, _ = _create_node(material, unreal.MaterialExpressionAdd, key, x, y)
    _connect(a, "", node, "A")
    _connect(b, "", node, "B")
    return node


def _multiply(material, key, a, b, x, y):
    node, _ = _create_node(material, unreal.MaterialExpressionMultiply, key, x, y)
    _connect(a, "", node, "A")
    _connect(b, "", node, "B")
    return node


def _subtract(material, key, a, b, x, y):
    node, _ = _create_node(material, unreal.MaterialExpressionSubtract, key, x, y)
    _connect(a, "", node, "A")
    _connect(b, "", node, "B")
    return node


def _divide(material, key, a, b, x, y):
    node, _ = _create_node(material, unreal.MaterialExpressionDivide, key, x, y)
    _connect(a, "", node, "A")
    _connect(b, "", node, "B")
    return node


def _floor(material, key, source, x, y):
    node, _ = _create_node(material, unreal.MaterialExpressionFloor, key, x, y)
    _connect(source, "", node, "")
    return node


def _lerp(material, key, a, b, alpha, x, y):
    node, _ = _create_node(material, unreal.MaterialExpressionLinearInterpolate, key, x, y)
    _connect(a, "", node, "A")
    _connect(b, "", node, "B")
    _connect(alpha, "", node, "Alpha")
    return node


def _build_wpo(material, utility_nodes):
    group = "Grandmaster Utility | Placement"
    offset = _create_vector(material, "UtilityWPOOffsetXYZ", (0, 0, 0, 0), group, "ParamWPOOffsetXYZ", 2300, 1100)
    offset_x = _create_scalar(material, "UtilityWPOOffsetX", 0, group, "ParamWPOOffsetX", 2300, 1120)
    offset_y = _create_scalar(material, "UtilityWPOOffsetY", 0, group, "ParamWPOOffsetY", 2300, 1240)
    offset_z = _create_scalar(material, "UtilityWPOOffsetZ", 0, group, "ParamWPOOffsetZ", 2300, 1360)
    space = _create_scalar(material, "UtilityWPOOffsetSpace", 0, group, "ParamWPOOffsetSpace", 2300, 1220)
    axis = _create_vector(material, "UtilityWPOAxisMask", (1, 1, 1, 0), group, "ParamWPOAxisMask", 2300, 1340)
    silhouette = _create_scalar(material, "UtilitySilhouetteExpand", 0, group, "ParamSilhouetteExpand", 2300, 1460)
    normal_offset = _create_scalar(material, "UtilityWPONormalOffset", 0, group, "ParamWPONormalOffset", 2300, 1520)
    snap_grid = _create_scalar(material, "UtilityVertexSnapGrid", 1, group, "ParamVertexSnapGrid", 2300, 1580)
    snap_strength = _create_scalar(material, "UtilityVertexSnapStrength", 0, group, "ParamVertexSnapStrength", 2300, 1700)
    jitter_amp = _create_scalar(material, "UtilityWPOJitterAmplitude", 0, group, "ParamWPOJitterAmplitude", 2300, 1820)
    jitter_freq = _create_scalar(material, "UtilityWPOJitterFrequency", 1, group, "ParamWPOJitterFrequency", 2300, 1940)
    jitter_speed = _create_scalar(material, "UtilityWPOJitterSpeed", 0, group, "ParamWPOJitterSpeed", 2300, 2060)
    jitter_axis = _create_vector(material, "UtilityWPOJitterAxisMask", (1, 1, 1, 0), group, "ParamWPOJitterAxisMask", 2300, 2180)
    hard_limit = _create_scalar(material, "UtilityWPOHardLimit", 100, group, "ParamWPOHardLimit", 2300, 2300)
    transform_strength = _create_scalar(material, "UtilityWPOTransformStrength", 0, group, "ParamWPOTransformStrength", 2300, 2420)
    transform_pivot = _create_vector(material, "UtilityWPOPivotLocal", (0, 0, 0, 0), group, "ParamWPOPivotLocal", 2300, 2540)
    transform_scale = _create_vector(material, "UtilityWPOScaleXYZ", (1, 1, 1, 0), group, "ParamWPOScaleXYZ", 2300, 2660)
    transform_rotation = _create_vector(material, "UtilityWPORotationXYZ", (0, 0, 0, 0), group, "ParamWPORotationXYZ", 2300, 2780)

    axis_offset = _multiply(material, "WPOAxisMaskedOffset", offset, axis, 2700, 1160)
    scalar_offset, _ = _custom(
        material,
        "WPOScalarOffsetHLSL",
        "Grandmaster WPO: explicit X/Y/Z scalar offset",
        "return float3(X, Y, Z);",
        ("X", "Y", "Z"),
        2700,
        1000,
    )
    _connect(offset_x, "", scalar_offset, "X")
    _connect(offset_y, "", scalar_offset, "Y")
    _connect(offset_z, "", scalar_offset, "Z")
    scalar_masked, _ = _custom(
        material,
        "WPOScalarMaskedOffsetHLSL",
        "Grandmaster WPO: scalar XYZ offset respects axis mask",
        "return Offset * AxisMask;",
        ("Offset", "AxisMask"),
        2900,
        1120,
    )
    _connect(scalar_offset, "", scalar_masked, "Offset")
    _connect(axis, "", scalar_masked, "AxisMask")
    normal_delta = _multiply(material, "WPONormalOffsetMultiply", utility_nodes["normal_ws"], normal_offset, 2900, 1520)
    local_offset, _ = _create_node(material, unreal.MaterialExpressionTransform, "WPOLocalOffsetToWorld", 2900, 1280)
    _set_transform_local_to_world(local_offset)
    _connect(axis_offset, "", local_offset, "")

    world_pos, _ = _create_node(material, unreal.MaterialExpressionWorldPosition, "WPOWorldPosition", 2500, 2600)
    local_pos, _ = _create_node(material, unreal.MaterialExpressionLocalPosition, "WPOLocalPosition", 2500, 3100)
    world_grid = _divide(material, "WPOWorldGridDivide", world_pos, snap_grid, 2750, 2500)
    world_grid_floor = _floor(material, "WPOWorldGridFloor", world_grid, 2950, 2500)
    world_grid_pos = _multiply(material, "WPOWorldGridPosition", world_grid_floor, snap_grid, 3150, 2500)
    world_snap_delta = _subtract(material, "WPOWorldSnapDelta", world_grid_pos, world_pos, 3350, 2500)
    local_grid = _divide(material, "WPOLocalGridDivide", local_pos, snap_grid, 2750, 3000)
    local_grid_floor = _floor(material, "WPOLocalGridFloor", local_grid, 2950, 3000)
    local_grid_pos = _multiply(material, "WPOLocalGridPosition", local_grid_floor, snap_grid, 3150, 3000)
    local_snap_delta = _subtract(material, "WPOLocalSnapDelta", local_grid_pos, local_pos, 3350, 3000)
    local_snap_world, _ = _create_node(material, unreal.MaterialExpressionTransform, "WPOLocalSnapToWorld", 3550, 3000)
    _set_transform_local_to_world(local_snap_world)
    _connect(local_snap_delta, "", local_snap_world, "")
    local_transform_delta, _ = _custom(
        material,
        "WPOLocalTransformHLSL",
        "Grandmaster WPO: local pivot scale + XYZ rotation",
        """float3 p = LocalPosition - PivotLocal;
float strength = saturate(TransformStrength);
float3 scale = lerp(float3(1, 1, 1), ScaleXYZ, strength);
float3 radians = RotationXYZ * 0.01745329252;
float3 q = p * scale;
float sx = sin(radians.x);
float cx = cos(radians.x);
float sy = sin(radians.y);
float cy = cos(radians.y);
float sz = sin(radians.z);
float cz = cos(radians.z);
float3 rx = float3(q.x, q.y * cx - q.z * sx, q.y * sx + q.z * cx);
float3 ry = float3(rx.x * cy + rx.z * sy, rx.y, -rx.x * sy + rx.z * cy);
float3 rz = float3(ry.x * cz - ry.y * sz, ry.x * sz + ry.y * cz, ry.z);
return (rz - p) * strength;""",
        ("LocalPosition", "PivotLocal", "ScaleXYZ", "RotationXYZ", "TransformStrength"),
        3650,
        3400,
    )
    _connect(local_pos, "XYZ", local_transform_delta, "LocalPosition")
    _connect(transform_pivot, "", local_transform_delta, "PivotLocal")
    _connect(transform_scale, "", local_transform_delta, "ScaleXYZ")
    _connect(transform_rotation, "", local_transform_delta, "RotationXYZ")
    _connect(transform_strength, "", local_transform_delta, "TransformStrength")
    local_transform_world, _ = _create_node(material, unreal.MaterialExpressionTransform, "WPOLocalTransformToWorld", 3900, 3400)
    _set_transform_local_to_world(local_transform_world)
    _connect(local_transform_delta, "", local_transform_world, "")

    time_node = utility_nodes.get("time")
    if time_node is None:
        time_node, _ = _create_node(material, unreal.MaterialExpressionTime, "GrandmasterTime", 2450, 3800)
        utility_nodes["time"] = time_node
    jitter, _ = _custom(
        material,
        "WPOJitterHLSL",
        "Grandmaster WPO: seeded vertex jitter",
        """float3 phase = Position * max(Frequency, 0.0001) + Time * Speed;\nfloat3 n = float3(sin(phase.x), cos(phase.y + 1.37), sin(phase.z + 2.71));\nreturn n * Amplitude * AxisMask;""",
        ("Position", "Amplitude", "Frequency", "Speed", "AxisMask", "Time"),
        3000,
        3700,
    )
    _connect(world_pos, "XYZ", jitter, "Position")
    _connect(jitter_amp, "", jitter, "Amplitude")
    _connect(jitter_freq, "", jitter, "Frequency")
    _connect(jitter_speed, "", jitter, "Speed")
    _connect(jitter_axis, "", jitter, "AxisMask")
    _connect(time_node, "", jitter, "Time")

    original_wpo = _find_named(material, "MaterialExpressionMultiply_27")
    if original_wpo is None:
        current_wpo = unreal.MaterialEditingLibrary.get_material_property_input_node(
            material, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET
        )
        if current_wpo and current_wpo is not _find_tag(material, "WPOGrandmasterFinal"):
            original_wpo = current_wpo
    if original_wpo is None:
        original_wpo, _ = _create_node(material, unreal.MaterialExpressionConstant3Vector, "WPOOriginalFallback", 3000, 4300)
        _set_prop(original_wpo, "constant", unreal.LinearColor(0, 0, 0, 0))

    final_wpo, _ = _custom(
        material,
        "WPOGrandmasterFinal",
        "Grandmaster WPO: original pulse + placement + snap + jitter + clamp",
        """float3 selectedOffset = lerp(OffsetWorld, OffsetLocalWorld, saturate(SpaceMode));\nfloat3 selectedSnap = lerp(SnapWorld, SnapLocalWorld, saturate(SpaceMode));\nfloat3 total = OriginalWPO + selectedOffset + ScalarOffset + NormalOffset + NormalWS * Silhouette + selectedSnap * SnapStrength + TransformDeltaWorld + Jitter;\nfloat limit = max(HardLimit, 0.0001);\nfloat magnitude = length(total);\nreturn magnitude > limit ? total * (limit / magnitude) : total;""",
        ("OriginalWPO", "OffsetWorld", "OffsetLocalWorld", "SpaceMode", "ScalarOffset", "NormalOffset", "SnapWorld", "SnapLocalWorld", "SnapStrength", "NormalWS", "Silhouette", "TransformDeltaWorld", "Jitter", "HardLimit"),
        3950,
        1800,
    )
    _connect(original_wpo, "", final_wpo, "OriginalWPO")
    _connect(axis_offset, "", final_wpo, "OffsetWorld")
    _connect(local_offset, "", final_wpo, "OffsetLocalWorld")
    _connect(space, "", final_wpo, "SpaceMode")
    _connect(scalar_masked, "", final_wpo, "ScalarOffset")
    _connect(normal_delta, "", final_wpo, "NormalOffset")
    _connect(world_snap_delta, "", final_wpo, "SnapWorld")
    _connect(local_snap_world, "", final_wpo, "SnapLocalWorld")
    _connect(snap_strength, "", final_wpo, "SnapStrength")
    _connect(utility_nodes["normal_ws"], "", final_wpo, "NormalWS")
    _connect(silhouette, "", final_wpo, "Silhouette")
    _connect(local_transform_world, "", final_wpo, "TransformDeltaWorld")
    _connect(jitter, "", final_wpo, "Jitter")
    _connect(hard_limit, "", final_wpo, "HardLimit")
    _connect_property(final_wpo, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)


def _build_uv(material, utility_sample):
    group = "Grandmaster Utility | Motion"
    scroll = _create_vector(material, "UtilityUVScrollXY", (0, 0, 0, 0), group, "ParamUVScrollXY", 2150, -1250)
    wobble_strength = _create_scalar(material, "UtilityUVWobbleStrength", 0, group, "ParamUVWobbleStrength", 2150, -1130)
    wobble_scale = _create_scalar(material, "UtilityUVWobbleScale", 1, group, "ParamUVWobbleScale", 2150, -1010)
    wobble_speed = _create_scalar(material, "UtilityUVWobbleSpeed", 0, group, "ParamUVWobbleSpeed", 2150, -890)
    quantize_steps = _create_scalar(material, "UtilityUVQuantizeSteps", 0, group, "ParamUVQuantizeSteps", 2150, -770)
    tiling_node = _find_named(material, "MaterialExpressionMultiply_16")
    if not tiling_node:
        inputs = list(unreal.MaterialEditingLibrary.get_inputs_for_material_expression(material, utility_sample) or [])
        tiling_node = inputs[0] if inputs else None
    if not tiling_node:
        raise RuntimeError("Could not locate the existing UtilityNoiseTiling UV anchor")
    time_node, _ = _create_node(material, unreal.MaterialExpressionTime, "UVGrandmasterTime", 2350, -620)
    uv_motion, _ = _custom(
        material,
        "UtilityUVMotionHLSL",
        "Grandmaster utility UV scroll + wobble",
        "float2 moved = UV + ScrollXY.xy * Time + sin(UV * max(WobbleScale, 0.0001) + Time * WobbleSpeed) * WobbleStrength;\nfloat steps = max(QuantizeSteps, 0.0);\nreturn steps > 1.0 ? floor(moved * steps + 0.5) / steps : moved;",
        ("UV", "ScrollXY", "Time", "WobbleStrength", "WobbleScale", "WobbleSpeed", "QuantizeSteps"),
        2950,
        -1050,
        unreal.CustomMaterialOutputType.CMOT_FLOAT2,
    )
    _connect(tiling_node, "", uv_motion, "UV")
    _connect(scroll, "", uv_motion, "ScrollXY")
    _connect(time_node, "", uv_motion, "Time")
    _connect(wobble_strength, "", uv_motion, "WobbleStrength")
    _connect(wobble_scale, "", uv_motion, "WobbleScale")
    _connect(wobble_speed, "", uv_motion, "WobbleSpeed")
    _connect(quantize_steps, "", uv_motion, "QuantizeSteps")
    _connect(uv_motion, "", utility_sample, "UVs")


def _build_surface(material, utility_nodes):
    toon = utility_nodes["toon"]
    color_source = utility_nodes["color_source"]
    normal_source = utility_nodes["normal_source"]
    steps = _find_parameter(material, "RetroColorSteps")
    if not steps:
        raise RuntimeError("Existing RetroColorSteps parameter is missing")
    group = "Grandmaster Utility | Retro"
    dither_strength = _create_scalar(material, "RetroDitherStrength", 0, group, "ParamRetroDitherStrength", 2250, -300)
    dither_scale = _create_scalar(material, "RetroDitherScale", 1, group, "ParamRetroDitherScale", 2250, -180)
    fog_strength = _create_scalar(material, "RetroFogStrength", 0, group, "ParamRetroFogStrength", 2250, -60)
    fog_start = _create_scalar(material, "RetroFogStart", 1000, group, "ParamRetroFogStart", 2250, 60)
    fog_end = _create_scalar(material, "RetroFogEnd", 10000, group, "ParamRetroFogEnd", 2250, 180)
    fog_color = _create_vector(material, "RetroFogColor", (0.04, 0.07, 0.12, 1), group, "ParamRetroFogColor", 2250, 300)
    rim_strength = _create_scalar(material, "RetroRimStrength", 0, group, "ParamRetroRimStrength", 2250, 420)
    rim_power = _create_scalar(material, "RetroRimPower", 4, group, "ParamRetroRimPower", 2250, 540)
    screen, _ = _create_node(material, unreal.MaterialExpressionScreenPosition, "RetroScreenPosition", 2500, -650)
    camera, _ = _create_node(material, unreal.MaterialExpressionCameraPositionWS, "RetroCameraPosition", 2500, -520)
    world, _ = _create_node(material, unreal.MaterialExpressionWorldPosition, "RetroWorldPosition", 2500, -390)
    retro_color, _ = _custom(
        material,
        "RetroColorHLSL",
        "Grandmaster retro dither + distance haze",
        """float3 c = Color;\nfloat2 pixel = floor(ScreenUV * max(DitherScale, 0.0001) * 1024.0);\nfloat hash = frac(sin(dot(pixel, float2(12.9898, 78.233))) * 43758.5453);\nfloat safeSteps = max(Steps, 1.0);\nfloat3 quantized = floor(c * safeSteps + hash - 0.5) / safeSteps;\nc = lerp(c, saturate(quantized), saturate(DitherStrength));\nfloat distanceToCamera = distance(WorldPosition, CameraPosition);\nfloat fog = smoothstep(FogStart, max(FogStart + 0.001, FogEnd), distanceToCamera) * saturate(FogStrength);\nreturn lerp(c, FogColor, saturate(fog));""",
        ("Color", "ScreenUV", "Steps", "DitherStrength", "DitherScale", "WorldPosition", "CameraPosition", "FogStart", "FogEnd", "FogStrength", "FogColor"),
        4150,
        -380,
    )
    _connect(color_source, "", retro_color, "Color")
    _connect(screen, "ViewportUV", retro_color, "ScreenUV")
    _connect(steps, "", retro_color, "Steps")
    _connect(dither_strength, "", retro_color, "DitherStrength")
    _connect(dither_scale, "", retro_color, "DitherScale")
    _connect(world, "XYZ", retro_color, "WorldPosition")
    _connect(camera, "", retro_color, "CameraPosition")
    _connect(fog_start, "", retro_color, "FogStart")
    _connect(fog_end, "", retro_color, "FogEnd")
    _connect(fog_strength, "", retro_color, "FogStrength")
    _connect(fog_color, "", retro_color, "FogColor")

    fresnel, _ = _create_node(material, unreal.MaterialExpressionFresnel, "RetroRimFresnel", 4150, 40)
    _connect(rim_power, "", fresnel, "ExponentIn")
    _connect(utility_nodes["normal_ws"], "", fresnel, "Normal")
    rim_mul = _multiply(material, "RetroRimStrengthMultiply", fresnel, rim_strength, 4400, 40)
    rim_tint = _find_parameter(material, "UtilityTint")
    if not rim_tint:
        raise RuntimeError("Existing UtilityTint parameter is missing")
    rim_color = _multiply(material, "RetroRimTintMultiply", rim_mul, rim_tint, 4600, 40)
    final_color = _add(material, "RetroRimColorAdd", retro_color, rim_color, 4800, -220)
    _connect(final_color, "", toon, "BaseColor")

    normal_steps = _create_scalar(material, "RetroNormalSteps", 4, group, "ParamRetroNormalSteps", 2250, 700)
    normal_strength = _create_scalar(material, "RetroNormalQuantizationStrength", 0, group, "ParamRetroNormalQuantizationStrength", 2250, 820)
    quantized_normal, _ = _custom(
        material,
        "RetroNormalQuantizeHLSL",
        "Grandmaster retro normal quantization",
        """float safeSteps = max(Steps, 1.0);\nfloat3 quantized = normalize(round(Normal * safeSteps) / safeSteps);\nreturn lerp(Normal, quantized, saturate(Strength));""",
        ("Normal", "Steps", "Strength"),
        4150,
        640,
    )
    _connect(normal_source, "", quantized_normal, "Normal")
    _connect(normal_steps, "", quantized_normal, "Steps")
    _connect(normal_strength, "", quantized_normal, "Strength")
    _connect(quantized_normal, "", toon, "Normal")


def _build_instance(name: str, parent, scalar_values=None, vector_values=None):
    scalar_values = scalar_values or {}
    vector_values = vector_values or {}
    path = f"{INSTANCE_DIR}/{name}.{name}"
    instance = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if not instance:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        instance = tools.create_asset(name, INSTANCE_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        if not instance:
            raise RuntimeError(f"Could not create {path}")
    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, parent)
    for parameter_name, value in scalar_values.items():
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, parameter_name, float(value))
    for parameter_name, value in vector_values.items():
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(instance, parameter_name, unreal.LinearColor(*value))
    unreal.MaterialEditingLibrary.update_material_instance(instance)
    unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
    _log(f"saved instance {path}")
    return path


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MATERIAL_PATH):
        raise RuntimeError(f"Missing target material: {MATERIAL_PATH}")
    material = unreal.EditorAssetLibrary.load_asset(MATERIAL_PATH)
    if not material:
        raise RuntimeError(f"Could not load target material: {MATERIAL_PATH}")

    expressions = _expressions(material)
    toon = next((e for e in expressions if type(e).__name__ == "MaterialExpressionSubstrateToonBSDF"), None)
    utility_sample = next((e for e in expressions if str(_get_prop(e, "parameter_name", "")) == "UtilityNoiseTexture"), None)
    color_source = _find_named(material, "MaterialExpressionLinearInterpolate_6")
    normal_source = _find_named(material, "MaterialExpressionTextureSampleParameter2D_6")
    if not toon or not utility_sample or not color_source or not normal_source:
        raise RuntimeError("Target graph anchors are incomplete; aborting without mutation")

    normal_ws, _ = _create_node(material, unreal.MaterialExpressionVertexNormalWS, "GrandmasterVertexNormalWS", 2300, 3400)
    utility_nodes = {
        "toon": toon,
        "utility_sample": utility_sample,
        "color_source": color_source,
        "normal_source": normal_source,
        "normal_ws": normal_ws,
    }

    _build_wpo(material, utility_nodes)
    _build_uv(material, utility_sample)
    _build_surface(material, utility_nodes)

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    _log("master compiled and saved")

    _build_instance(
        "MI_SDF_Utility_MelusinaCorneas",
        material,
        scalar_values={
            "UtilityWPOOffsetSpace": 1,
            "UtilityWPOHardLimit": 100,
            "UtilityWPOOffsetX": 0,
            "UtilityWPOOffsetY": 0,
            "UtilityWPOOffsetZ": 0,
            "UtilityWPONormalOffset": 0,
            "UtilityVertexSnapStrength": 0,
            "UtilityWPOJitterAmplitude": 0,
            "UtilityWPOTransformStrength": 0,
        },
        vector_values={
            "UtilityWPOOffsetXYZ": (0, 0, 0, 0),
            "UtilityWPOAxisMask": (1, 1, 1, 0),
        },
    )
    _build_instance(
        "MI_SDF_Utility_RetroArcade",
        material,
        scalar_values={
            "RetroColorSteps": 4,
            "RetroPosterizeStrength": 0.75,
            "RetroDitherStrength": 0.35,
            "RetroDitherScale": 1.0,
            "RetroNormalQuantizationStrength": 0.25,
            "RetroNormalSteps": 4,
            "UtilityVertexSnapStrength": 0.65,
        },
    )
    _build_instance(
        "MI_SDF_Utility_WaterDressing",
        material,
        scalar_values={
            "UtilityUVWobbleStrength": 0.025,
            "UtilityUVWobbleScale": 3.0,
            "UtilityUVWobbleSpeed": 0.45,
            "RetroRimStrength": 0.1,
            "RetroRimPower": 3.0,
        },
    )

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    _log("grandmaster utility upgrade complete")


if __name__ == "__main__":
    main()
