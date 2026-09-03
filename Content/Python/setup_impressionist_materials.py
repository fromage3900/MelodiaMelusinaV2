"""Build UE 5.8 Substrate Toon impressionist materials for BS_GodFile.

All masters wire MaterialExpressionSubstrateToonBSDF -> Front Material (NOT Default Lit,
NOT legacy BaseColor-only output). Brushstroke, impasto, wetness, and temporal animation
feed Toon BSDF inputs (BaseColor, Roughness, Normal) plus WorldPositionOffset.

Run in editor (Python Editor Script Plugin enabled):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_impressionist_materials.py"

Requires r.Substrate=True in Config/DefaultEngine.ini and an editor restart after first
enabling Substrate.
"""
from __future__ import annotations

import unreal

MATERIALS_ROOT = "/Game/EnvSandbox/Materials"
IMPRESSIONIST_ROOT = f"{MATERIALS_ROOT}/Impressionist"
MASTER_DIR = f"{IMPRESSIONIST_ROOT}/Masters"
INST_DIR = f"{IMPRESSIONIST_ROOT}/Instances"
PROFILE_DIR = f"{MATERIALS_ROOT}/ToonProfiles"

MASTER_OBJECT = f"{MASTER_DIR}/M_Master_Impressionist_Toon"
MASTER_LANDSCAPE = f"{MASTER_DIR}/M_Master_Impressionist_Toon_Landscape"

TOON_PROFILES = [
    "TP_Impressionist_Dry",
    "TP_Impressionist_Wet",
    "TP_Impressionist_Impasto",
]

IMPRESSIONIST_INSTANCES = [
    {
        "name": "MI_Impressionist_Meadow_Dry",
        "parent": MASTER_OBJECT,
        "profile": "TP_Impressionist_Dry",
        "color_low": (0.12, 0.18, 0.08, 1.0),
        "color_mid": (0.35, 0.52, 0.22, 1.0),
        "color_high": (0.72, 0.82, 0.45, 1.0),
        "brush_scale": 0.045,
        "stroke_strength": 0.55,
        "impasto_strength": 0.35,
        "impasto_height": 0.025,
        "wetness": 0.0,
        "temporal_strength": 0.12,
        "wind_speed": 0.15,
        "dry_roughness": 0.78,
        "wet_roughness": 0.35,
        "noise_scale": 1.2,
        "smear_strength": 0.2,
        "ink_intensity": 0.0,
        "normal_strength": 1.2,
    },
    {
        "name": "MI_Impressionist_Field_Wet",
        "parent": MASTER_OBJECT,
        "profile": "TP_Impressionist_Wet",
        "color_low": (0.05, 0.10, 0.18, 1.0),
        "color_mid": (0.18, 0.38, 0.55, 1.0),
        "color_high": (0.55, 0.78, 0.92, 1.0),
        "brush_scale": 0.038,
        "stroke_strength": 0.65,
        "impasto_strength": 0.45,
        "impasto_height": 0.035,
        "wetness": 0.72,
        "temporal_strength": 0.22,
        "wind_speed": 0.35,
        "dry_roughness": 0.70,
        "wet_roughness": 0.22,
        "noise_scale": 1.8,
        "smear_strength": 0.55,
        "ink_intensity": 0.65,
        "normal_strength": 1.8,
    },
    {
        "name": "MI_Impressionist_Stone_Impasto",
        "parent": MASTER_OBJECT,
        "profile": "TP_Impressionist_Impasto",
        "color_low": (0.08, 0.08, 0.12, 1.0),
        "color_mid": (0.32, 0.34, 0.38, 1.0),
        "color_high": (0.78, 0.80, 0.82, 1.0),
        "brush_scale": 0.055,
        "stroke_strength": 0.82,
        "impasto_strength": 0.88,
        "impasto_height": 0.06,
        "wetness": 0.15,
        "temporal_strength": 0.08,
        "wind_speed": 0.05,
        "dry_roughness": 0.82,
        "wet_roughness": 0.45,
        "noise_scale": 0.8,
        "smear_strength": 0.15,
        "ink_intensity": 0.2,
        "normal_strength": 2.5,
    },
    {
        "name": "MI_Impressionist_Landscape_Grass",
        "parent": MASTER_LANDSCAPE,
        "profile": "TP_Impressionist_Dry",
        "color_low": (0.10, 0.16, 0.06, 1.0),
        "color_mid": (0.28, 0.48, 0.18, 1.0),
        "color_high": (0.62, 0.75, 0.32, 1.0),
        "brush_scale": 0.028,
        "stroke_strength": 0.48,
        "impasto_strength": 0.28,
        "impasto_height": 0.018,
        "wetness": 0.1,
        "temporal_strength": 0.18,
        "wind_speed": 0.25,
        "dry_roughness": 0.80,
        "wet_roughness": 0.40,
        "noise_scale": 2.0,
        "smear_strength": 0.35,
        "ink_intensity": 0.15,
        "normal_strength": 1.0,
    },
]


def _ensure_directory(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _asset_path(folder: str, name: str) -> str:
    return f"{folder}/{name}.{name}"


def _save_package(asset) -> None:
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)


def _try_set_editor_property(obj, name: str, value) -> None:
    try:
        if hasattr(obj, "has_editor_property") and obj.has_editor_property(name):
            obj.set_editor_property(name, value)
    except Exception:
        pass


def _create_expression(material, expression_class, x: int, y: int):
    return unreal.MaterialEditingLibrary.create_material_expression(
        material, expression_class, x, y
    )


def _connect(from_expr, from_output: str, to_expr, to_input: str) -> None:
    unreal.MaterialEditingLibrary.connect_material_expressions(
        from_expr, from_output, to_expr, to_input
    )


def _connect_unary(from_expr, to_expr) -> None:
    """Wire single-input nodes (Sine/Abs/Cosine/etc.) using UE 5.8 pin names."""
    material = to_expr.get_outer()
    pin_names = list(
        unreal.MaterialEditingLibrary.get_material_expression_input_names(to_expr)
    )
    candidates: list[str] = []
    for pin in pin_names + ["", "None"]:
        if pin not in candidates:
            candidates.append(pin)

    for pin in candidates:
        if unreal.MaterialEditingLibrary.connect_material_expressions(
            from_expr, "", to_expr, pin
        ):
            if material:
                wired = list(
                    unreal.MaterialEditingLibrary.get_inputs_for_material_expression(
                        material, to_expr
                    )
                )
                if wired and wired[0] == from_expr:
                    return
            else:
                return

    # MCP-style direct struct connect fallback (Input->Connect).
    try:
        input_prop = to_expr.get_editor_property("input")
        input_prop.connect(0, from_expr)
        if material:
            material.modify()
        return
    except Exception as exc:
        raise RuntimeError(
            f"Could not connect unary input on {type(to_expr).__name__}"
        ) from exc


def _connect_front_material(material, from_expr, from_output: str = "") -> None:
    unreal.MaterialEditingLibrary.connect_material_property(
        from_expr,
        from_output,
        unreal.MaterialProperty.MP_FRONT_MATERIAL,
    )


def _connect_material_output(material, from_expr, prop: unreal.MaterialProperty, from_output: str = "") -> None:
    unreal.MaterialEditingLibrary.connect_material_property(from_expr, from_output, prop)


def _connect_toon_pin(toon_bsdf, expr, pin_names: tuple[str, ...]) -> bool:
    for pin in pin_names:
        try:
            _connect(expr, "", toon_bsdf, pin)
            return True
        except Exception:
            continue
    return False


def _scalar_param(material, name: str, default: float, group: str, x: int, y: int):
    node = _create_expression(material, unreal.MaterialExpressionScalarParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("group", group)
    node.set_editor_property("default_value", default)
    return node


def _vector_param(material, name: str, default: tuple[float, float, float, float], group: str, x: int, y: int):
    node = _create_expression(material, unreal.MaterialExpressionVectorParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("group", group)
    node.set_editor_property("default_value", unreal.LinearColor(*default))
    return node


def create_impressionist_profiles() -> dict[str, unreal.ToonProfile]:
    _ensure_directory(PROFILE_DIR)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.ToonProfileFactory()
    profiles: dict[str, unreal.ToonProfile] = {}

    for profile_name in TOON_PROFILES:
        path = _asset_path(PROFILE_DIR, profile_name)
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            profiles[profile_name] = unreal.load_asset(path)
            unreal.log(f"[Impressionist] reusing profile {path}")
            continue

        profile = asset_tools.create_asset(
            profile_name, PROFILE_DIR, unreal.ToonProfile, factory
        )
        if not profile:
            raise RuntimeError(f"Failed to create ToonProfile {profile_name}")
        profiles[profile_name] = profile
        _save_package(profile)
        unreal.log(f"[Impressionist] created profile {path}")

    return profiles


def _build_impressionist_graph(
    material: unreal.Material,
    default_profile: unreal.ToonProfile,
    *,
    landscape: bool = False,
) -> None:
    """Core impressionist logic -> Substrate Toon BSDF -> Front Material."""

    # --- Parameters ---
    color_low = _vector_param(material, "ColorRampLow", (0.12, 0.18, 0.08, 1.0), "Palette", -1800, -200)
    color_mid = _vector_param(material, "ColorRampMid", (0.35, 0.52, 0.22, 1.0), "Palette", -1800, -40)
    color_high = _vector_param(material, "ColorRampHigh", (0.72, 0.82, 0.45, 1.0), "Palette", -1800, 120)

    brush_scale = _scalar_param(material, "BrushScale", 0.045, "Brush", -1800, 280)
    stroke_strength = _scalar_param(material, "StrokeStrength", 0.55, "Brush", -1800, 400)
    brush_dir = _vector_param(material, "BrushDirection", (1.0, 0.3, 0.0, 0.0), "Brush", -1800, 520)

    impasto_strength = _scalar_param(material, "ImpastoStrength", 0.35, "Impasto", -1800, 680)
    impasto_height = _scalar_param(material, "ImpastoHeight", 0.025, "Impasto", -1800, 800)
    normal_strength = _scalar_param(material, "NormalStrength", 1.5, "Impasto", -1800, 920)

    wetness = _scalar_param(material, "Wetness", 0.0, "Surface", -1800, 1040)
    dry_roughness = _scalar_param(material, "DryRoughness", 0.78, "Surface", -1800, 1160)
    wet_roughness = _scalar_param(material, "WetRoughness", 0.35, "Surface", -1800, 1280)
    ink_intensity = _scalar_param(material, "InkIntensity", 0.0, "Surface", -1800, 1400)
    ink_color = _vector_param(material, "InkColor", (0.05, 0.08, 0.15, 1.0), "Surface", -1800, 1520)
    pooling_strength = _scalar_param(material, "PoolingStrength", 0.5, "Surface", -1800, 1640)
    boil_intensity = _scalar_param(material, "BoilIntensity", 0.0, "Animation", -1800, 1760)
    uv_scale = _scalar_param(material, "UVScale", 1.0, "UV", -1800, 1880)

    temporal_strength = _scalar_param(material, "TemporalStrength", 0.12, "Animation", -1800, 2000)
    wind_speed = _scalar_param(material, "WindSpeed", 0.15, "Animation", -1800, 2120)
    noise_scale = _scalar_param(material, "NoiseScale", 1.5, "Animation", -1800, 2240)
    smear_strength = _scalar_param(material, "SmearStrength", 0.3, "Animation", -1800, 2360)

    # --- World / landscape coordinates ---
    if landscape:
        layer_coords = _create_expression(
            material, unreal.MaterialExpressionLandscapeLayerCoords, -1500, 300
        )
        _try_set_editor_property(layer_coords, "mapping_scale", 2048.0)
        sample_xy = layer_coords
    else:
        world_pos = _create_expression(material, unreal.MaterialExpressionWorldPosition, -1500, 300)
        sample_xy = _create_expression(material, unreal.MaterialExpressionComponentMask, -1300, 300)
        sample_xy.set_editor_property("r", True)
        sample_xy.set_editor_property("g", True)
        sample_xy.set_editor_property("b", False)
        sample_xy.set_editor_property("a", False)
        _connect(world_pos, "", sample_xy, "")

    uv_scaled_xy = _create_expression(material, unreal.MaterialExpressionMultiply, -1180, 300)
    _connect(sample_xy, "", uv_scaled_xy, "A")
    _connect(uv_scale, "", uv_scaled_xy, "B")

    # Directional brush UV: dot(xy, normalize(BrushDirection.xy))
    brush_dir_xy = _create_expression(material, unreal.MaterialExpressionComponentMask, -1300, 520)
    brush_dir_xy.set_editor_property("r", True)
    brush_dir_xy.set_editor_property("g", True)
    brush_dir_xy.set_editor_property("b", False)
    brush_dir_xy.set_editor_property("a", False)
    _connect(brush_dir, "", brush_dir_xy, "")

    dot_stroke = _create_expression(material, unreal.MaterialExpressionDotProduct, -1100, 400)
    _connect(uv_scaled_xy, "", dot_stroke, "A")
    _connect(brush_dir_xy, "", dot_stroke, "B")

    scaled_stroke = _create_expression(material, unreal.MaterialExpressionMultiply, -920, 400)
    _connect(dot_stroke, "", scaled_stroke, "A")
    _connect(brush_scale, "", scaled_stroke, "B")

    # Temporal smear: add Time * WindSpeed
    time_node = _create_expression(material, unreal.MaterialExpressionTime, -1100, 560)
    wind_mul = _create_expression(material, unreal.MaterialExpressionMultiply, -920, 560)
    _connect(time_node, "", wind_mul, "A")
    _connect(wind_speed, "", wind_mul, "B")

    animated_stroke = _create_expression(material, unreal.MaterialExpressionAdd, -740, 460)
    _connect(scaled_stroke, "", animated_stroke, "A")
    _connect(wind_mul, "", animated_stroke, "B")

    # Cross-hatch stroke pattern
    sin_stroke = _create_expression(material, unreal.MaterialExpressionSine, -560, 400)
    sin_stroke.set_editor_property("period", 1.0)
    _connect_unary(animated_stroke, sin_stroke)

    abs_stroke = _create_expression(material, unreal.MaterialExpressionAbs, -380, 400)
    _connect_unary(sin_stroke, abs_stroke)

    perp_mul = _create_expression(material, unreal.MaterialExpressionMultiply, -740, 620)
    const_1_3 = _create_expression(material, unreal.MaterialExpressionConstant, -920, 680)
    const_1_3.set_editor_property("r", 1.3)
    _connect(scaled_stroke, "", perp_mul, "A")
    _connect(const_1_3, "", perp_mul, "B")

    cos_perp = _create_expression(material, unreal.MaterialExpressionCosine, -560, 620)
    cos_perp.set_editor_property("period", 1.0)
    _connect_unary(perp_mul, cos_perp)

    abs_perp = _create_expression(material, unreal.MaterialExpressionAbs, -380, 620)
    _connect_unary(cos_perp, abs_perp)

    stroke_mul = _create_expression(material, unreal.MaterialExpressionMultiply, -200, 480)
    _connect(abs_stroke, "", stroke_mul, "A")
    _connect(abs_perp, "", stroke_mul, "B")

    stroke_scaled = _create_expression(material, unreal.MaterialExpressionMultiply, -20, 480)
    _connect(stroke_mul, "", stroke_scaled, "A")
    _connect(stroke_strength, "", stroke_scaled, "B")

    # Color mixing: Low -> Mid -> High via stroke mask
    lerp_lm = _create_expression(material, unreal.MaterialExpressionLinearInterpolate, 180, 320)
    _connect(color_low, "", lerp_lm, "A")
    _connect(color_mid, "", lerp_lm, "B")
    _connect(stroke_scaled, "", lerp_lm, "Alpha")

    lerp_lmh = _create_expression(material, unreal.MaterialExpressionLinearInterpolate, 380, 320)
    _connect(lerp_lm, "", lerp_lmh, "A")
    _connect(color_high, "", lerp_lmh, "B")
    _connect(stroke_scaled, "", lerp_lmh, "Alpha")

    # Temporal color boil
    temporal_mod = _create_expression(material, unreal.MaterialExpressionMultiply, 180, 560)
    _connect(stroke_scaled, "", temporal_mod, "A")
    _connect(temporal_strength, "", temporal_mod, "B")

    temporal_sine = _create_expression(material, unreal.MaterialExpressionSine, 380, 560)
    temporal_sine.set_editor_property("period", 1.0)
    _connect_unary(wind_mul, temporal_sine)

    temporal_offset = _create_expression(material, unreal.MaterialExpressionMultiply, 560, 520)
    _connect(temporal_sine, "", temporal_offset, "A")
    _connect(temporal_mod, "", temporal_offset, "B")

    # MF_TemporalNoise analogue: world-position FBm driver (NoiseScale × WorldXY + Time)
    noise_vec = _create_expression(material, unreal.MaterialExpressionConstant3Vector, -1100, 720)
    noise_vec.set_editor_property("constant", unreal.LinearColor(0.7, 1.3, 0.0))
    noise_vec_xy = _create_expression(material, unreal.MaterialExpressionComponentMask, -920, 720)
    noise_vec_xy.set_editor_property("r", True)
    noise_vec_xy.set_editor_property("g", True)
    noise_vec_xy.set_editor_property("b", False)
    noise_vec_xy.set_editor_property("a", False)
    _connect(noise_vec, "", noise_vec_xy, "")

    noise_dot = _create_expression(material, unreal.MaterialExpressionDotProduct, -740, 700)
    _connect(uv_scaled_xy, "", noise_dot, "A")
    _connect(noise_vec_xy, "", noise_dot, "B")

    noise_scaled = _create_expression(material, unreal.MaterialExpressionMultiply, -560, 700)
    _connect(noise_dot, "", noise_scaled, "A")
    _connect(noise_scale, "", noise_scaled, "B")

    noise_phase = _create_expression(material, unreal.MaterialExpressionAdd, -380, 680)
    _connect(noise_scaled, "", noise_phase, "A")
    _connect(wind_mul, "", noise_phase, "B")

    world_noise = _create_expression(material, unreal.MaterialExpressionSine, -200, 680)
    world_noise.set_editor_property("period", 1.0)
    _connect_unary(noise_phase, world_noise)

    world_temporal_mod = _create_expression(material, unreal.MaterialExpressionMultiply, 0, 680)
    _connect(world_noise, "", world_temporal_mod, "A")
    _connect(temporal_strength, "", world_temporal_mod, "B")

    color_step1 = _create_expression(material, unreal.MaterialExpressionAdd, 760, 300)
    _connect(lerp_lmh, "", color_step1, "A")
    _connect(temporal_offset, "", color_step1, "B")

    color_with_temporal = _create_expression(material, unreal.MaterialExpressionAdd, 960, 300)
    _connect(color_step1, "", color_with_temporal, "A")
    _connect(world_temporal_mod, "", color_with_temporal, "B")

    # MF_VolumetricInkAccumulation analogue: pool ink in stroke valleys when wet
    stroke_inverse = _create_expression(material, unreal.MaterialExpressionOneMinus, 180, 720)
    _connect_unary(stroke_scaled, stroke_inverse)

    ink_wet = _create_expression(material, unreal.MaterialExpressionMultiply, 380, 740)
    _connect(stroke_inverse, "", ink_wet, "A")
    _connect(wetness, "", ink_wet, "B")

    ink_alpha = _create_expression(material, unreal.MaterialExpressionMultiply, 560, 740)
    _connect(ink_wet, "", ink_alpha, "A")
    _connect(ink_intensity, "", ink_alpha, "B")

    ink_pool = _create_expression(material, unreal.MaterialExpressionMultiply, 720, 740)
    _connect(ink_alpha, "", ink_pool, "A")
    _connect(pooling_strength, "", ink_pool, "B")

    final_color = _create_expression(material, unreal.MaterialExpressionLinearInterpolate, 960, 340)
    _connect(color_with_temporal, "", final_color, "A")
    _connect(ink_color, "", final_color, "B")
    _connect(ink_pool, "", final_color, "Alpha")

    # Impasto height -> WPO along vertex normal
    impasto_h = _create_expression(material, unreal.MaterialExpressionMultiply, 180, 760)
    _connect(stroke_scaled, "", impasto_h, "A")
    _connect(impasto_strength, "", impasto_h, "B")

    height_scale = _create_expression(material, unreal.MaterialExpressionMultiply, 380, 760)
    _connect(impasto_h, "", height_scale, "A")
    _connect(impasto_height, "", height_scale, "B")

    vertex_normal = _create_expression(material, unreal.MaterialExpressionVertexNormalWS, 560, 820)
    wpo = _create_expression(material, unreal.MaterialExpressionMultiply, 760, 780)
    _connect(height_scale, "", wpo, "A")
    _connect(vertex_normal, "", wpo, "B")

    # Wetness-driven roughness + temporal noise ripple (LIE Tier 1)
    rough_lerp = _create_expression(material, unreal.MaterialExpressionLinearInterpolate, 760, 980)
    _connect(dry_roughness, "", rough_lerp, "A")
    _connect(wet_roughness, "", rough_lerp, "B")
    _connect(wetness, "", rough_lerp, "Alpha")

    rough_temporal = _create_expression(material, unreal.MaterialExpressionMultiply, 960, 1000)
    const_rough_temp = _create_expression(material, unreal.MaterialExpressionConstant, 960, 1080)
    const_rough_temp.set_editor_property("r", 0.1)
    _connect(world_temporal_mod, "", rough_temporal, "A")
    _connect(const_rough_temp, "", rough_temporal, "B")

    rough_final = _create_expression(material, unreal.MaterialExpressionAdd, 1140, 980)
    _connect(rough_lerp, "", rough_final, "A")
    _connect(rough_temporal, "", rough_final, "B")

    # Normal perturbation: impasto relief + paint smear (MF_ImpastoEmulation + MF_PaintSmearing)
    impasto_normal = _create_expression(material, unreal.MaterialExpressionMultiply, 560, 900)
    _connect(impasto_h, "", impasto_normal, "A")
    _connect(normal_strength, "", impasto_normal, "B")

    smear_mod = _create_expression(material, unreal.MaterialExpressionMultiply, 760, 900)
    _connect(world_noise, "", smear_mod, "A")
    _connect(smear_strength, "", smear_mod, "B")

    normal_alpha = _create_expression(material, unreal.MaterialExpressionAdd, 960, 900)
    _connect(impasto_normal, "", normal_alpha, "A")
    _connect(smear_mod, "", normal_alpha, "B")

    pixel_normal = _create_expression(material, unreal.MaterialExpressionPixelNormalWS, 560, 1040)
    normal_perturb = _create_expression(material, unreal.MaterialExpressionLinearInterpolate, 1140, 960)
    flat_normal = _create_expression(material, unreal.MaterialExpressionConstant3Vector, 560, 1160)
    flat_normal.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0))
    _connect(flat_normal, "", normal_perturb, "A")
    _connect(pixel_normal, "", normal_perturb, "B")
    _connect(normal_alpha, "", normal_perturb, "Alpha")

    # --- Substrate Toon BSDF (required output path) ---
    toon_bsdf = _create_expression(
        material, unreal.MaterialExpressionSubstrateToonBSDF, 1040, 480
    )
    toon_bsdf.set_editor_property("toon_profile", default_profile)

    if not _connect_toon_pin(toon_bsdf, final_color, ("BaseColor", "DiffuseColor")):
        raise RuntimeError("Could not connect BaseColor to SubstrateToonBSDF")

    if not _connect_toon_pin(toon_bsdf, rough_final, ("Roughness",)):
        unreal.log_warning("[Impressionist] Roughness pin not found on SubstrateToonBSDF — tune in editor")

    if not _connect_toon_pin(toon_bsdf, normal_perturb, ("Normal", "TangentNormal", "NormalMap")):
        unreal.log_warning("[Impressionist] Normal pin not found on SubstrateToonBSDF — tune in editor")

    _connect_front_material(material, toon_bsdf)
    _connect_material_output(material, wpo, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)


def _create_master(
    asset_name: str,
    folder: str,
    default_profile: unreal.ToonProfile,
    *,
    landscape: bool = False,
) -> str:
    _ensure_directory(folder)
    master_path = _asset_path(folder, asset_name)
    if unreal.EditorAssetLibrary.does_asset_exist(master_path):
        unreal.log_warning(f"[Impressionist] rebuilding {master_path}")
        unreal.EditorAssetLibrary.delete_asset(master_path)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = asset_tools.create_asset(
        asset_name, folder, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not material:
        raise RuntimeError(f"Failed to create {asset_name}")

    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    _try_set_editor_property(material, "bUsesSubstrate", True)

    if landscape:
        _try_set_editor_property(material, "bUsedWithLandscape", True)
        _try_set_editor_property(material, "bUsedWithLandscapeGrass", True)

    _build_impressionist_graph(material, default_profile, landscape=landscape)

    unreal.MaterialEditingLibrary.recompile_material(material)
    _save_package(material)
    unreal.log(f"[Impressionist] built master {folder}/{asset_name} (SubstrateToonBSDF -> Front Material)")
    return f"{folder}/{asset_name}"


def _set_instance_vector(instance, name: str, rgba: tuple[float, float, float, float]) -> None:
    color = unreal.LinearColor(*rgba)
    if hasattr(unreal.MaterialEditingLibrary, "set_material_instance_vector_parameter_value"):
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(instance, name, color)
    else:
        instance.set_vector_parameter_value_editor_only(name, color)


def _set_instance_scalar(instance, name: str, value: float) -> None:
    if hasattr(unreal.MaterialEditingLibrary, "set_material_instance_scalar_parameter_value"):
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, name, value)
    else:
        instance.set_scalar_parameter_value_editor_only(name, value)


def _set_instance_toon_profile(instance, profile: unreal.ToonProfile) -> None:
    _try_set_editor_property(instance, "toon_profile", profile)
    _try_set_editor_property(instance, "override_toon_profile", True)


def build_instances(profiles: dict[str, unreal.ToonProfile]) -> list[str]:
    _ensure_directory(INST_DIR)
    created: list[str] = []

    for spec in IMPRESSIONIST_INSTANCES:
        inst_path = _asset_path(INST_DIR, spec["name"])
        if unreal.EditorAssetLibrary.does_asset_exist(inst_path):
            unreal.EditorAssetLibrary.delete_asset(inst_path)

        parent = unreal.load_asset(spec["parent"])
        instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            spec["name"],
            INST_DIR,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew(),
        )
        if not instance:
            raise RuntimeError(f"Failed to create {spec['name']}")

        unreal.MaterialEditingLibrary.set_material_instance_parent(instance, parent)
        _set_instance_vector(instance, "ColorRampLow", spec["color_low"])
        _set_instance_vector(instance, "ColorRampMid", spec["color_mid"])
        _set_instance_vector(instance, "ColorRampHigh", spec["color_high"])
        _set_instance_scalar(instance, "BrushScale", spec["brush_scale"])
        _set_instance_scalar(instance, "StrokeStrength", spec["stroke_strength"])
        _set_instance_scalar(instance, "ImpastoStrength", spec["impasto_strength"])
        _set_instance_scalar(instance, "ImpastoHeight", spec["impasto_height"])
        _set_instance_scalar(instance, "Wetness", spec["wetness"])
        _set_instance_scalar(instance, "TemporalStrength", spec["temporal_strength"])
        _set_instance_scalar(instance, "WindSpeed", spec["wind_speed"])
        _set_instance_scalar(instance, "DryRoughness", spec["dry_roughness"])
        _set_instance_scalar(instance, "WetRoughness", spec["wet_roughness"])
        _set_instance_scalar(instance, "NormalStrength", spec["normal_strength"])
        _set_instance_scalar(instance, "InkIntensity", spec["ink_intensity"])
        _set_instance_scalar(instance, "NoiseScale", spec["noise_scale"])
        _set_instance_scalar(instance, "SmearStrength", spec["smear_strength"])
        _set_instance_toon_profile(instance, profiles[spec["profile"]])

        _save_package(instance)
        created.append(inst_path)
        unreal.log(f"[Impressionist] created {inst_path} -> {spec['profile']}")

    return created


def build_all() -> None:
    unreal.log("=== BS_GodFile Impressionist Toon build start ===")
    for folder in (IMPRESSIONIST_ROOT, MASTER_DIR, INST_DIR, PROFILE_DIR):
        _ensure_directory(folder)

    profiles = create_impressionist_profiles()
    object_master = _create_master(
        "M_Master_Impressionist_Toon",
        MASTER_DIR,
        profiles["TP_Impressionist_Dry"],
        landscape=False,
    )
    landscape_master = _create_master(
        "M_Master_Impressionist_Toon_Landscape",
        MASTER_DIR,
        profiles["TP_Impressionist_Dry"],
        landscape=True,
    )
    instances = build_instances(profiles)

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("=== BS_GodFile Impressionist Toon build complete ===")
    unreal.log(f"Object master: {object_master}  [SubstrateToonBSDF -> Front Material]")
    unreal.log(f"Landscape master: {landscape_master}  [SubstrateToonBSDF -> Front Material]")
    for path in instances:
        unreal.log(f"  Instance: {path}")


if __name__ == "__main__":
    build_all()
