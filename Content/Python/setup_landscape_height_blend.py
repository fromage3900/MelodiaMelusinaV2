"""Build M_Master_Toon_Landscape_HeightBlend — toon landscape with height-map layer competition.

Run (editor):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_landscape_height_blend.py"

Headless:
  python Content/Python/setup_landscape_height_blend.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

MASTER_NAME = "M_Master_Toon_Landscape_HeightBlend"
INST_DIR = "/Game/EnvSandbox/Materials/Instances/Landscape"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "landscape_height_blend.json"
WAT = "/Engine/Functions/Engine_MaterialFunctions02/Texturing/WorldAlignedTexture"
WAN = "/Engine/Functions/Engine_MaterialFunctions02/Texturing/WorldAlignedNormal"

MF_HEIGHT_COMPETE = "/Game/EnvSandbox/Materials/Functions/MF_LandscapeHeightCompete.MF_LandscapeHeightCompete"
MF_NORMAL_ADJUST = "/Game/EnvSandbox/Materials/Functions/MF_NormalAdjust.MF_NormalAdjust"
MF_NIKKI_DREAM = "/Game/EnvSandbox/Materials/Functions/MF_NikkiDreamGrade.MF_NikkiDreamGrade"
MF_NIKKI_RIM = "/Game/EnvSandbox/Materials/Functions/MF_NikkiRimGlow.MF_NikkiRimGlow"
MF_NIKKI_SPARKLE = "/Game/EnvSandbox/Materials/Functions/MF_NikkiSparkle.MF_NikkiSparkle"
MF_NIKKI_IRID = "/Game/EnvSandbox/Materials/Functions/MF_NikkiIridescenceSheen.MF_NikkiIridescenceSheen"
MF_SHADOW_FLOWER = "/Game/EnvSandbox/Materials/Functions/MF_ShadowFlowerProject.MF_ShadowFlowerProject"
MPC_SAKURA = "/Game/EnvSandbox/VFX/MPC/MPC_SakuraDream"
# Canonical runtime audio-reactivity bus.  Shared with gameplay presentation
# systems; syntax for the grandmaster Melodia collection.
MPC_PORTFOLIO_AUDIO = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
LAYER_NAMES = ("Rock", "Grass", "Mud", "Path")
BASE_LAYER_NAMES = ("Rock", "Grass", "Mud")

INSTANCES = [
    {
        "name": "MI_Landscape_CliffGrass",
        "profile": "TP_Stone",
        "vectors": {"RockTint": (0.42, 0.40, 0.38, 1.0), "GrassTint": (0.32, 0.48, 0.22, 1.0), "MudTint": (0.28, 0.22, 0.16, 1.0)},
        "scalars": {"SlopeSharpness": 4.0, "HeightBlendStrength": 2.5, "GrassAmount": 0.65, "MudAmount": 0.25, "MacroStrength": 0.45, "TriplanarTiling": 280.0},
    },
    {
        "name": "MI_Landscape_Meadow",
        "profile": "TP_Foliage",
        "vectors": {"RockTint": (0.50, 0.46, 0.40, 1.0), "GrassTint": (0.38, 0.58, 0.24, 1.0), "MudTint": (0.34, 0.26, 0.18, 1.0)},
        "scalars": {"SlopeSharpness": 2.2, "HeightBlendStrength": 1.8, "GrassAmount": 0.85, "MudAmount": 0.15, "MacroStrength": 0.35, "TriplanarTiling": 220.0},
    },
    {
        "name": "MI_Landscape_SnowAlpine",
        "profile": "TP_Default",
        "vectors": {"RockTint": (0.38, 0.40, 0.44, 1.0), "GrassTint": (0.55, 0.58, 0.52, 1.0), "MudTint": (0.30, 0.28, 0.26, 1.0), "SnowTint": (0.92, 0.95, 0.98, 1.0)},
        "scalars": {"SlopeSharpness": 5.0, "HeightBlendStrength": 3.0, "GrassAmount": 0.35, "MudAmount": 0.10, "SnowStrength": 0.75, "SnowUpBias": 2.4, "TriplanarTiling": 320.0},
    },
    {
        "name": "MI_Landscape_SakuraGarden",
        "profile": "TP_Foliage",
        "vectors": {
            "RockTint": (0.50, 0.46, 0.40, 1.0),
            "GrassTint": (0.40, 0.52, 0.28, 1.0),
            "MudTint": (0.24, 0.30, 0.16, 1.0),
            "ShadowDreamTint": (0.58, 0.48, 0.72, 1.0),
            "ShadowFlowerColor": (0.92, 0.58, 0.75, 1.0),
        },
        "scalars": {
            "SlopeSharpness": 2.0, "HeightBlendStrength": 1.7, "GrassAmount": 0.88, "MudAmount": 0.20,
            "MacroStrength": 0.30, "SnowStrength": 0.0, "TriplanarTiling": 210.0,
            "PastelLift": 0.22, "DreamSaturation": 0.18, "SparkleIntensity": 0.35,
            "SparkleThreshold": 0.42, "RimIntensity": 0.18, "Iridescence": 0.12,
            "ShadowDreamStrength": 0.42,
            "ShadowFlowerStrength": 0.55,
            "ShadowFlowerScale": 6.5,
            "ShadowFlowerScaleFine": 13.0,
            "ShadowFlowerPulseStrength": 0.18,
            "ShadowContactBoost": 0.22,
        },
    },
    {
        "name": "MI_Landscape_ForestFloor",
        "profile": "TP_Foliage",
        "vectors": {"RockTint": (0.40, 0.38, 0.34, 1.0), "GrassTint": (0.28, 0.46, 0.20, 1.0), "MudTint": (0.22, 0.18, 0.14, 1.0)},
        "scalars": {
            "SlopeSharpness": 2.5, "HeightBlendStrength": 2.0, "GrassAmount": 0.92, "MudAmount": 0.18,
            "MacroStrength": 0.55, "MacroScale": 0.0004, "RockMacroStrength": 0.72,
            "GrassMacroStrength": 1.0, "MudMacroStrength": 0.64, "PathMacroStrength": 0.48,
            "Wetness": 0.35, "WetRoughness": 0.55, "TriplanarTiling": 240.0,
            "TriplanarBlend": 0.45, "TriplanarSlopeStart": 0.42, "TriplanarSlopeEnd": 0.76,
            "NearDetailStrength": 0.0, "FarAtmosphereStrength": 0.05, "FarAtmosphereStart": 9000.0,
            "FarAtmosphereEnd": 28000.0, "WonderStrength": 0.0, "WonderSparkleBoost": 0.0,
        },
    },
    {
        "name": "MI_Landscape_CoastalCliff",
        "profile": "TP_Stone",
        "vectors": {"RockTint": (0.48, 0.46, 0.44, 1.0), "GrassTint": (0.34, 0.50, 0.28, 1.0), "MudTint": (0.30, 0.24, 0.18, 1.0)},
        "scalars": {"SlopeSharpness": 6.0, "HeightBlendStrength": 3.2, "GrassAmount": 0.35, "MudAmount": 0.12, "MacroStrength": 0.40, "NormalStrength": 1.25, "TriplanarTiling": 300.0},
    },
    {
        "name": "MI_Landscape_PondBank",
        "profile": "TP_Foliage",
        "vectors": {
            "RockTint": (0.46, 0.44, 0.40, 1.0), "GrassTint": (0.32, 0.50, 0.26, 1.0),
            "MudTint": (0.26, 0.22, 0.16, 1.0), "RimColor": (0.75, 0.88, 0.92, 1.0),
            "ShadowDreamTint": (0.48, 0.55, 0.72, 1.0),
            "ShadowFlowerColor": (0.88, 0.62, 0.78, 1.0),
        },
        "scalars": {
            "Wetness": 0.55, "ShoreWetnessBoost": 0.4, "MudAmount": 0.35, "GrassAmount": 0.45,
            "PastelLift": 0.15, "RimIntensity": 0.28, "SparkleIntensity": 0.25,
            "SlopeSharpness": 2.4, "HeightBlendStrength": 2.0, "MacroStrength": 0.38, "TriplanarTiling": 200.0,
            "ShadowDreamStrength": 0.35,
            "ShadowFlowerStrength": 0.38,
            "ShadowFlowerScale": 5.5,
            "ShadowFlowerPulseStrength": 0.12,
        },
    },
    {
        "name": "MI_Landscape_DesertArid",
        "profile": "TP_Stone",
        "vectors": {
            "RockTint": (0.62, 0.52, 0.38, 1.0),
            "GrassTint": (0.48, 0.44, 0.32, 1.0),
            "MudTint": (0.40, 0.34, 0.24, 1.0),
        },
        "scalars": {
            "GrassAmount": 0.12, "MudAmount": 0.08, "MacroStrength": 0.5,
            "SlopeSharpness": 3.5, "HeightBlendStrength": 2.8, "TriplanarTiling": 360.0,
        },
    },
    {
        "name": "MI_Landscape_VolcanicRock",
        "profile": "TP_Stone",
        "vectors": {
            "RockTint": (0.22, 0.20, 0.20, 1.0),
            "GrassTint": (0.28, 0.32, 0.22, 1.0),
            "MudTint": (0.18, 0.14, 0.12, 1.0),
        },
        "scalars": {
            "GrassAmount": 0.08, "MudAmount": 0.22, "NormalStrength": 1.4,
            "SlopeSharpness": 7.0, "HeightBlendStrength": 3.5, "TriplanarTiling": 340.0,
        },
    },
    {
        "name": "MI_Landscape_UrbanCobble",
        "profile": "TP_Stone",
        "vectors": {
            "RockTint": (0.46, 0.44, 0.42, 1.0),
            "GrassTint": (0.36, 0.40, 0.30, 1.0),
            "MudTint": (0.38, 0.34, 0.30, 1.0),
            "PathTint": (0.52, 0.50, 0.48, 1.0),
        },
        "scalars": {
            "GrassAmount": 0.15, "MudAmount": 0.25, "PathWearStrength": 0.65,
            "MacroStrength": 0.3, "TriplanarTiling": 180.0,
        },
    },
    {
        "name": "MI_Landscape_WetlandMud",
        "profile": "TP_Foliage",
        "vectors": {
            "RockTint": (0.36, 0.34, 0.30, 1.0),
            "GrassTint": (0.30, 0.42, 0.24, 1.0),
            "MudTint": (0.24, 0.20, 0.14, 1.0),
        },
        "scalars": {
            "GrassAmount": 0.55, "MudAmount": 0.72, "Wetness": 0.75, "WetRoughness": 0.45,
            "MacroStrength": 0.42, "TriplanarTiling": 200.0,
        },
    },
]


def _layer_tex():
    import portfolio_landscape_textures as lt

    layers: dict[str, dict[str, list[str]]] = {}
    for name in LAYER_NAMES:
        if name == "Path":
            continue
        layers[name] = lt.resolve_layer_textures(name)
    layers["Path"] = lt.resolve_layer_textures("Path")
    return layers


def build(*, force: bool = False) -> str:
    import unreal
    import material_lib as lib
    import portfolio_texture_catalog as catalog
    import setup_material_functions as mf_mod

    mf_mod.build_all(force=force)
    layer_tex = _layer_tex()

    def static_sw(m, name, group, x, y, default=False):
        s = lib.create_expression(m, unreal.MaterialExpressionStaticSwitchParameter, x, y)
        s.set_editor_property("parameter_name", name)
        s.set_editor_property("group", group)
        s.set_editor_property("default_value", default)
        return s

    def painted_sw(m, x, y, true_e, false_e):
        # Landscape actors should paint correctly without an MI-side switch flip;
        # the has-paint fallback still selects procedural output on empty terrain.
        sw = static_sw(m, "bUsePaintedLayers", "Blend", x, y, True)
        lib.connect_static_switch(sw, true_e, false_e)
        return sw

    def wire_tex(expr, candidates):
        path = lib.resolve_texture_path(candidates)
        if path:
            lib.set_expression_texture(expr, path)

    def mf_call(m, path, x, y):
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            return None
        c = lib.create_expression(m, unreal.MaterialExpressionMaterialFunctionCall, x, y)
        c.set_editor_property("material_function", unreal.load_asset(path))
        return c

    def sample_triplanar(m, tex_expr, tiling, tag, x, y):
        fn = WAN if "Nrm" in tag else WAT
        call = mf_call(m, fn, x, y)
        if not call:
            const = lib.create_expression(m, unreal.MaterialExpressionConstant3Vector, x + 200, y)
            const.set_editor_property("constant", unreal.LinearColor(0.5, 0.5, 0.5, 1.0))
            return const
        lib.connect(tex_expr, "Texture", call, "TextureObject")
        lib.connect(tiling, "", call, "TextureSize")
        return call

    def sample_layer(m, tex_expr, tag, x, y, uv_blend):
        tri = sample_triplanar(m, tex_expr, tri_tiling, tag, x, y)
        uv_s = lib.create_expression(m, unreal.MaterialExpressionTextureSample, x + 180, y)
        lib.connect(tex_expr, "Texture", uv_s, "Texture")
        lib.connect(layer_uv, "", uv_s, "UVs")
        blend = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, x + 360, y)
        lib.connect(tri, "", blend, "A")
        lib.connect(uv_s, "", blend, "B")
        lib.connect(uv_blend, "", blend, "Alpha")
        return blend

    def edge_detect_scalar(m, source, x, y):
        """Derivative edge magnitude for optional stylization lanes.

        Kept local because this builder must not depend on an editor-only helper
        that may be absent from material_lib in a production commandlet run.
        """
        ddx = lib.create_expression(m, unreal.MaterialExpressionDDX, x, y - 50)
        ddy = lib.create_expression(m, unreal.MaterialExpressionDDY, x, y + 50)
        lib.connect_unary(source, ddx)
        lib.connect_unary(source, ddy)
        abs_x = lib.create_expression(m, unreal.MaterialExpressionAbs, x + 160, y - 50)
        abs_y = lib.create_expression(m, unreal.MaterialExpressionAbs, x + 160, y + 50)
        lib.connect(ddx, "", abs_x, "Input")
        lib.connect(ddy, "", abs_y, "Input")
        edge_add = lib.create_expression(m, unreal.MaterialExpressionAdd, x + 320, y)
        lib.connect(abs_x, "", edge_add, "A")
        lib.connect(abs_y, "", edge_add, "B")
        edge = lib.create_expression(m, unreal.MaterialExpressionSaturate, x + 480, y)
        lib.connect(edge_add, "", edge, "Input")
        return edge

    lib.ensure_directory(lib.MASTER_DIR)
    lib.ensure_directory(INST_DIR)
    path = lib.asset_path(lib.MASTER_DIR, MASTER_NAME)
    exists = unreal.EditorAssetLibrary.does_asset_exist(path)
    force = force or os.environ.get("BS_MASTER_FORCE", "").lower() in ("1", "true", "yes")
    force = force or any("force" in str(a).lower() for a in sys.argv)
    if exists and not force:
        unreal.log_warning(f"[LandscapeHB] {path} exists — use --force")
        return path

    m = unreal.load_asset(path) if exists and force else None
    if m:
        # A force rebuild clears the graph.  Preserve a recoverable, date-stamped
        # asset before making that irreversible editor-side change.
        backup_name = f"{MASTER_NAME}_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        source_package = path.rsplit(".", 1)[0]
        backup_package = f"{lib.MASTER_DIR}/{backup_name}"
        if not unreal.EditorAssetLibrary.duplicate_asset(source_package, backup_package):
            raise RuntimeError(f"Landscape backup failed: {backup_package}")
        unreal.log(f"[LandscapeHB] backup created: {backup_package}")
        lib.clear_material_graph(m)
    else:
        m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            MASTER_NAME, lib.MASTER_DIR, unreal.Material, unreal.MaterialFactoryNew()
        )
    if not m:
        raise RuntimeError("create_asset failed")

    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    lib.try_set_editor_property(m, "bUsesSubstrate", True)
    lib.try_set_editor_property(m, "bUsedWithLandscape", True)
    lib.try_set_editor_property(m, "bUsedWithLandscapeGrass", True)

    profiles = lib.create_toon_profiles(["TP_Default", "TP_Stone", "TP_Foliage"])
    px, py = -2200, -200
    rock_tint = lib.vector_param(m, "RockTint", "Palette", (0.44, 0.41, 0.38, 1.0), px, py)
    grass_tint = lib.vector_param(m, "GrassTint", "Palette", (0.30, 0.48, 0.20, 1.0), px, py + 120)
    mud_tint = lib.vector_param(m, "MudTint", "Palette", (0.28, 0.22, 0.16, 1.0), px, py + 240)
    path_tint = lib.vector_param(m, "PathTint", "Palette", (0.58, 0.54, 0.48, 1.0), px, py + 360)
    snow_tint = lib.vector_param(m, "SnowTint", "Snow", (0.92, 0.95, 0.98, 1.0), px, py + 480)
    tri_tiling = lib.scalar_param(m, "TriplanarTiling", "Triplanar", 256.0, px, py + 620)
    tri_blend = lib.scalar_param(m, "TriplanarBlend", "Triplanar", 0.0, px, py + 680)
    tri_slope_start = lib.scalar_param(m, "TriplanarSlopeStart", "Triplanar", 0.35, px, py + 740)
    tri_slope_end = lib.scalar_param(m, "TriplanarSlopeEnd", "Triplanar", 0.72, px, py + 800)
    uv_scale = lib.scalar_param(m, "LandscapeUVScale", "UV", 1.0, px, py + 740)
    slope_sharp = lib.scalar_param(m, "SlopeSharpness", "Blend", 3.0, px, py + 860)
    height_blend = lib.scalar_param(m, "HeightBlendStrength", "Blend", 2.0, px, py + 980)
    grass_amt = lib.scalar_param(m, "GrassAmount", "Blend", 0.6, px, py + 1100)
    mud_amt = lib.scalar_param(m, "MudAmount", "Blend", 0.25, px, py + 1220)
    macro_str = lib.scalar_param(m, "MacroStrength", "Macro", 0.4, px, py + 1340)
    macro_scale = lib.scalar_param(m, "MacroScale", "Macro", 0.0004, px, py + 1460)
    rock_macro = lib.scalar_param(m, "RockMacroStrength", "Macro", 1.0, px, py + 1520)
    grass_macro = lib.scalar_param(m, "GrassMacroStrength", "Macro", 1.0, px, py + 1580)
    mud_macro = lib.scalar_param(m, "MudMacroStrength", "Macro", 1.0, px, py + 1640)
    path_macro = lib.scalar_param(m, "PathMacroStrength", "Macro", 1.0, px, py + 1700)
    snow_str = lib.scalar_param(m, "SnowStrength", "Snow", 0.0, px, py + 1580)
    snow_bias = lib.scalar_param(m, "SnowUpBias", "Snow", 2.2, px, py + 1700)
    roughness_s = lib.scalar_param(m, "Roughness", "Surface", 0.82, px, py + 1820)
    rock_rough = lib.scalar_param(m, "RockRoughness", "Surface", 0.88, px, py + 1940)
    grass_rough = lib.scalar_param(m, "GrassRoughness", "Surface", 0.78, px, py + 2060)
    mud_rough = lib.scalar_param(m, "MudRoughness", "Surface", 0.92, px, py + 2180)
    normal_str = lib.scalar_param(m, "NormalStrength", "Surface", 1.0, px, py + 2300)
    wetness = lib.scalar_param(m, "Wetness", "Surface", 0.0, px, py + 2420)
    wet_rough = lib.scalar_param(m, "WetRoughness", "Surface", 0.45, px, py + 2540)
    shore_wet_boost = lib.scalar_param(m, "ShoreWetnessBoost", "Shore", 0.0, px, py + 2660)
    shore_darken = lib.scalar_param(m, "ShoreColorDarken", "Shore", 0.0, px, py + 2780)
    water_align = lib.scalar_param(m, "WaterPaletteAlign", "Shore", 0.0, px, py + 2900)
    water_tint = lib.vector_param(m, "WaterAlignTint", "Shore", (0.55, 0.72, 0.78, 1.0), px, py + 3020)
    path_wear = lib.scalar_param(m, "PathWearStrength", "Path", 0.0, px, py + 3140)
    path_edge_strength = lib.scalar_param(m, "PathEdgeStrength", "Path", 0.0, px, py + 3200)
    path_mask = lib.texture_param(m, "PathMask", "Path", px, py + 3260)
    wire_tex(path_mask, layer_tex.get("Path", {}).get("Albedo", catalog.MASTER_TEXTURE_DEFAULTS.get("Albedo", [])))
    dream_tint = lib.vector_param(m, "DreamTint", "Nikki", (1.0, 0.85, 0.92, 1.0), px, py + 3380)
    rim_color = lib.vector_param(m, "RimColor", "Nikki", (0.70, 0.85, 1.0, 1.0), px, py + 3500)
    spark_color = lib.vector_param(m, "SparkleColor", "Nikki", (1.0, 0.95, 0.80, 1.0), px, py + 3620)
    irid_tint = lib.vector_param(m, "IridescenceTint", "Nikki", (0.80, 0.60, 1.0, 1.0), px, py + 3740)
    sheen_tint = lib.vector_param(m, "SheenTint", "Nikki", (1.0, 1.0, 1.0, 1.0), px, py + 3860)
    spark_mask = lib.texture_param(m, "SparkleMask", "Nikki", px, py + 3980)
    wire_tex(spark_mask, catalog.MASTER_TEXTURE_DEFAULTS["SparkleMask"])
    pastel = lib.scalar_param(m, "PastelLift", "Nikki", 0.0, px, py + 4100)
    dream_sat = lib.scalar_param(m, "DreamSaturation", "Nikki", 0.0, px, py + 4220)
    dream_con = lib.scalar_param(m, "DreamContrast", "Nikki", 0.0, px, py + 4340)
    shadow_lift = lib.scalar_param(m, "DreamShadowLift", "Nikki", 0.0, px, py + 4460)
    rim_width = lib.scalar_param(m, "RimWidth", "Nikki", 1.0, px, py + 4580)
    rim_int = lib.scalar_param(m, "RimIntensity", "Nikki", 0.0, px, py + 4700)
    glow_int = lib.scalar_param(m, "GlowIntensity", "Nikki", 0.0, px, py + 4820)
    bloom = lib.scalar_param(m, "BloomBoost", "Nikki", 0.0, px, py + 4940)
    spark_int = lib.scalar_param(m, "SparkleIntensity", "Nikki", 0.0, px, py + 5060)
    spark_thresh = lib.scalar_param(m, "SparkleThreshold", "Nikki", 0.0, px, py + 5180)
    irid = lib.scalar_param(m, "Iridescence", "Nikki", 0.0, px, py + 5300)
    irid_pow = lib.scalar_param(m, "IridescencePower", "Nikki", 1.0, px, py + 5420)
    fabric_sheen = lib.scalar_param(m, "FabricSheen", "Nikki", 0.0, px, py + 5540)
    nikki_fast_sw = static_sw(m, "bNikkiFast", "Nikki", px, py + 5660, False)
    nikki_hero_sw = static_sw(m, "bNikkiHero", "Nikki", px, py + 5780, False)

    # Kept at zero by default so upgrading the master does not change existing
    # landscape instances.  Showcase instances can opt in after visual review.
    audio_reactive_strength = lib.scalar_param(m, "AudioReactiveStrength", "13 | Audio Reactive", 0.0, px, py + 5900)
    detail_normal = lib.texture_param(m, "DetailNormal", "14 | Distance Detail", px, py + 6020)
    wire_tex(detail_normal, catalog.MASTER_TEXTURE_DEFAULTS.get("DetailNormal", []))
    detail_strength = lib.scalar_param(m, "NearDetailStrength", "14 | Distance Detail", 0.0, px, py + 6140)
    near_start = lib.scalar_param(m, "NearDetailStart", "14 | Distance Detail", 0.0, px, py + 6260)
    near_end = lib.scalar_param(m, "NearDetailEnd", "14 | Distance Detail", 2500.0, px, py + 6380)
    far_atmo_strength = lib.scalar_param(m, "FarAtmosphereStrength", "15 | Distance Atmosphere", 0.0, px, py + 6500)
    far_atmo_start = lib.scalar_param(m, "FarAtmosphereStart", "15 | Distance Atmosphere", 8000.0, px, py + 6620)
    far_atmo_end = lib.scalar_param(m, "FarAtmosphereEnd", "15 | Distance Atmosphere", 30000.0, px, py + 6740)
    far_atmo_color = lib.vector_param(m, "FarAtmosphereColor", "15 | Distance Atmosphere", (0.62, 0.72, 0.82, 1.0), px, py + 6860)
    wonder_strength = lib.scalar_param(m, "WonderStrength", "16 | Wonder Mask", 0.0, px, py + 6980)
    wonder_palette = lib.vector_param(m, "WonderPalette", "16 | Wonder Mask", (0.92, 0.72, 0.88, 1.0), px, py + 7100)
    wonder_sparkle = lib.scalar_param(m, "WonderSparkleBoost", "16 | Wonder Mask", 0.0, px, py + 7220)
    hero_tier = static_sw(m, "bLandscapeHeroTier", "17 | Quality Tier", px, py + 7340, False)
    fast_tier = static_sw(m, "bLandscapeFastTier", "17 | Quality Tier", px, py + 7460, False)
    debug_masks = static_sw(m, "bLandscapeDebugMasks", "18 | Debug", px, py + 7580, False)
    debug_height = static_sw(m, "bLandscapeDebugHeight", "18 | Debug", px, py + 7700, False)
    debug_path = static_sw(m, "bLandscapeDebugPath", "18 | Debug", px, py + 7820, False)
    debug_slope = static_sw(m, "bLandscapeDebugSlope", "18 | Debug", px, py + 7940, False)
    debug_distance = static_sw(m, "bLandscapeDebugDistance", "18 | Debug", px, py + 8060, False)
    debug_wonder = static_sw(m, "bLandscapeDebugWonder", "18 | Debug", px, py + 8180, False)

    # ---- Madoka graph (landscape) ----
    madoka_glow = lib.scalar_param(m, "MadokaGlowAmount", "Madoka", 0.0, px, py + 5900)
    madoka_radial_bands = lib.scalar_param(m, "MadokaRadialBands", "Madoka", 3.0, px, py + 6020)
    madoka_radial_speed = lib.scalar_param(m, "MadokaRadialSpeed", "Madoka", 0.0, px, py + 6140)
    madoka_emissive_bright = lib.scalar_param(m, "MadokaEmissiveBrightness", "Madoka", 0.0, px, py + 6260)
    madoka_cute_bias = lib.scalar_param(m, "MadokaCuteBias", "Madoka", 0.5, px, py + 6380)
    madoka_vein_emissive = lib.scalar_param(m, "MadokaVeinEmissive", "Madoka", 0.0, px, py + 6500)
    witch_wallpaper_scale = lib.scalar_param(m, "WitchBarrierWallpaperScale", "Madoka", 4.0, px, py + 6620)
    witch_maze_tightness = lib.scalar_param(m, "WitchBarrierMazeTightness", "Madoka", 0.5, px, py + 6740)
    witch_phase_speed = lib.scalar_param(m, "WitchBarrierPhaseSpeed", "Madoka", 0.45, px, py + 6860)

    # ---- Itto graph (landscape) ----
    itto_pattern_scale = lib.scalar_param(m, "IttoPatternScale", "Itto", 3.0, px, py + 6980)
    itto_crack_depth = lib.scalar_param(m, "IttoCrackDepth", "Itto", 0.0, px, py + 7100)
    itto_wear_amount = lib.scalar_param(m, "IttoWearAmount", "Itto", 0.0, px, py + 7220)
    itto_breakup = lib.scalar_param(m, "IttoBreakupAmount", "Itto", 0.0, px, py + 7340)
    itto_erosion = lib.scalar_param(m, "IttoErosionStrength", "Itto", 0.0, px, py + 7460)
    itto_wear_depth = lib.scalar_param(m, "IttoWearDepth", "Itto", 0.0, px, py + 7580)
    itto_ink = lib.scalar_param(m, "IttoInkStrength", "Itto", 0.0, px, py + 7700)

    shadow_dream_tint = lib.vector_param(
        m, "ShadowDreamTint", "ShadowDream", (0.48, 0.42, 0.62, 1.0), px, py + 7820,
    )
    shadow_dream_str = lib.scalar_param(m, "ShadowDreamStrength", "ShadowDream", 0.0, px, py + 6020)
    shadow_contact = lib.scalar_param(m, "ShadowContactBoost", "ShadowDream", 0.0, px, py + 6140)
    flower_str = lib.scalar_param(m, "ShadowFlowerStrength", "FlowerShadow", 0.0, px, py + 6260)
    flower_scale = lib.scalar_param(m, "ShadowFlowerScale", "FlowerShadow", 6.0, px, py + 6380)
    flower_scale_fine = lib.scalar_param(m, "ShadowFlowerScaleFine", "FlowerShadow", 12.0, px, py + 6500)
    flower_col = lib.vector_param(
        m, "ShadowFlowerColor", "FlowerShadow", (0.92, 0.55, 0.72, 1.0), px, py + 6620,
    )
    flower_pulse_str = lib.scalar_param(m, "ShadowFlowerPulseStrength", "FlowerShadow", 0.0, px, py + 6740)
    flower_mask = lib.texture_param(m, "ShadowFlowerMask", "FlowerShadow", px, py + 6860)
    wire_tex(flower_mask, ["/Game/Sakura/T_Sakura_Petal.T_Sakura_Petal"])

    layer_coords = lib.create_expression(m, unreal.MaterialExpressionLandscapeLayerCoords, -2000, -80)
    layer_uv = lib.create_expression(m, unreal.MaterialExpressionMultiply, -1800, -80)
    lib.connect(layer_coords, "", layer_uv, "A")
    lib.connect(uv_scale, "", layer_uv, "B")
    b_landscape_uv = static_sw(m, "bUseLandscapeUV", "UV", -2000, -200, False)
    uv_one = lib.create_expression(m, unreal.MaterialExpressionConstant, -1800, -200)
    uv_one.set_editor_property("r", 1.0)
    uv_zero = lib.create_expression(m, unreal.MaterialExpressionConstant, -1800, -120)
    uv_zero.set_editor_property("r", 0.0)
    uv_blend_sw = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, -1600, -160)
    lib.connect(uv_zero, "", uv_blend_sw, "A")
    lib.connect(uv_one, "", uv_blend_sw, "B")
    lib.connect(b_landscape_uv, "", uv_blend_sw, "Alpha")

    layer_samples: dict[str, dict] = {}
    path_layer_sample: dict | None = None
    for i, (layer, tex) in enumerate(layer_tex.items()):
        yy = 400 + i * 420
        alb = lib.texture_param(m, f"{layer}_Albedo", "Textures", -2000, yy)
        wire_tex(alb, tex["Albedo"])
        nrm = lib.texture_param(m, f"{layer}_Normal", "Textures", -2000, yy + 80)
        wire_tex(nrm, tex["Normal"])
        hgt = lib.texture_param(m, f"{layer}_Height", "Textures", -2000, yy + 160)
        wire_tex(hgt, tex["Height"])
        orm = lib.texture_param(m, f"{layer}_ORM", "Textures", -2000, yy + 240)
        wire_tex(orm, tex.get("ORM") or catalog.MASTER_TEXTURE_DEFAULTS["ORM"])
        alb_s = sample_layer(m, alb, f"{layer}_Alb", -1600, yy, uv_blend_sw)
        nrm_s = sample_layer(m, nrm, f"{layer}_Nrm", -1600, yy + 120, uv_blend_sw)
        hgt_s = sample_layer(m, hgt, f"{layer}_Hgt", -1600, yy + 240, uv_blend_sw)
        orm_s = sample_layer(m, orm, f"{layer}_ORM", -1600, yy + 360, uv_blend_sw)
        if layer == "Path":
            path_layer_sample = {"color": alb_s, "normal": nrm_s, "height": hgt_s, "orm": orm_s}
            continue
        tint_map = {"Rock": rock_tint, "Grass": grass_tint, "Mud": mud_tint}
        tinted = lib.create_expression(m, unreal.MaterialExpressionMultiply, -1200, yy)
        lib.connect(alb_s, "", tinted, "A")
        lib.connect(tint_map[layer], "", tinted, "B")
        weights = lib.create_expression(m, unreal.MaterialExpressionConstant3Vector, -1200, yy + 200)
        weights.set_editor_property("constant", unreal.LinearColor(0.30, 0.59, 0.11, 1.0))
        h_dot = lib.create_expression(m, unreal.MaterialExpressionDotProduct, -1040, yy + 200)
        lib.connect(hgt_s, "", h_dot, "A")
        lib.connect(weights, "", h_dot, "B")
        layer_samples[layer] = {"color": tinted, "normal": nrm_s, "height": h_dot, "albedo_param": alb, "normal_param": nrm, "orm": orm_s}

    compete = mf_call(m, MF_HEIGHT_COMPETE, -900, 520)
    grass_alpha_pin, mud_alpha_pin = "GrassAlpha", "MudAlpha"
    if compete:
        lib.connect(layer_samples["Rock"]["height"], "", compete, "RockHeight")
        lib.connect(layer_samples["Grass"]["height"], "", compete, "GrassHeight")
        lib.connect(layer_samples["Mud"]["height"], "", compete, "MudHeight")
        lib.connect(height_blend, "", compete, "HeightBlendStrength")
        lib.connect(grass_amt, "", compete, "GrassAmount")
        lib.connect(mud_amt, "", compete, "MudAmount")

    path_sample = lib.create_expression(m, unreal.MaterialExpressionTextureSample, -500, 820)
    lib.connect(path_mask, "Texture", path_sample, "Texture")
    path_tex_w = lib.create_expression(m, unreal.MaterialExpressionMultiply, -300, 820)
    lib.connect(path_sample, "R", path_tex_w, "A")
    lib.connect(path_wear, "", path_tex_w, "B")

    layer_weights: dict[str, object] = {}
    for i, lname in enumerate(LAYER_NAMES):
        ls = lib.create_expression(m, unreal.MaterialExpressionLandscapeLayerSample, -500, 980 + i * 80)
        ls.set_editor_property("parameter_name", lname)
        layer_weights[lname] = ls
    # Independent overlay: it is intentionally excluded from base weight
    # normalization so magical clearings never erase Rock/Grass/Mud paint.
    wonder_mask = lib.create_expression(m, unreal.MaterialExpressionLandscapeLayerSample, -500, 1360)
    wonder_mask.set_editor_property("parameter_name", "Wonder")
    paint_sum = layer_weights[BASE_LAYER_NAMES[0]]
    for i in range(1, len(BASE_LAYER_NAMES)):
        add = lib.create_expression(m, unreal.MaterialExpressionAdd, -300, 980 + i * 80)
        lib.connect(paint_sum, "", add, "A")
        lib.connect(layer_weights[BASE_LAYER_NAMES[i]], "", add, "B")
        paint_sum = add

    eps = lib.create_expression(m, unreal.MaterialExpressionConstant, -120, 1100)
    eps.set_editor_property("r", 0.001)
    paint_safe = lib.create_expression(m, unreal.MaterialExpressionAdd, 80, 1020)
    lib.connect(paint_sum, "", paint_safe, "A")
    lib.connect(eps, "", paint_safe, "B")
    paint_mul = lib.create_expression(m, unreal.MaterialExpressionMultiply, 80, 900)
    lib.connect(paint_sum, "", paint_mul, "A")
    scale50 = lib.create_expression(m, unreal.MaterialExpressionConstant, -120, 900)
    scale50.set_editor_property("r", 50.0)
    lib.connect(scale50, "", paint_mul, "B")
    has_paint = lib.create_expression(m, unreal.MaterialExpressionSaturate, 260, 1020)
    lib.connect(paint_mul, "", has_paint, "Input")

    path_add = lib.create_expression(m, unreal.MaterialExpressionAdd, -120, 820)
    lib.connect(layer_weights["Path"], "", path_add, "A")
    lib.connect(path_tex_w, "", path_add, "B")
    path_fac = lib.create_expression(m, unreal.MaterialExpressionSaturate, 80, 820)
    lib.connect(path_add, "", path_fac, "Input")
    path_inv = lib.create_expression(m, unreal.MaterialExpressionOneMinus, 260, 820)
    lib.connect(path_fac, "", path_inv, "Input")

    path_mud = lib.create_expression(m, unreal.MaterialExpressionAdd, 80, 700)
    lib.connect(layer_weights["Path"], "", path_mud, "A")
    lib.connect(layer_weights["Mud"], "", path_mud, "B")
    shore_mask = lib.create_expression(m, unreal.MaterialExpressionSaturate, 260, 700)
    lib.connect(path_mud, "", shore_mask, "Input")

    if compete:
        grass_base = lib.create_expression(m, unreal.MaterialExpressionMultiply, -120, 520)
        lib.connect(compete, grass_alpha_pin, grass_base, "A")
        lib.connect(path_inv, "", grass_base, "B")
        mud_alpha = compete
    else:
        diff_gr = lib.create_expression(m, unreal.MaterialExpressionSubtract, -900, 500)
        lib.connect(layer_samples["Grass"]["height"], "", diff_gr, "A")
        lib.connect(layer_samples["Rock"]["height"], "", diff_gr, "B")
        diff_gm = lib.create_expression(m, unreal.MaterialExpressionSubtract, -900, 640)
        lib.connect(layer_samples["Grass"]["height"], "", diff_gm, "A")
        lib.connect(layer_samples["Mud"]["height"], "", diff_gm, "B")
        mod_gr = lib.create_expression(m, unreal.MaterialExpressionMultiply, -700, 500)
        lib.connect(diff_gr, "", mod_gr, "A")
        lib.connect(height_blend, "", mod_gr, "B")
        mod_gm = lib.create_expression(m, unreal.MaterialExpressionMultiply, -700, 640)
        lib.connect(diff_gm, "", mod_gm, "A")
        lib.connect(height_blend, "", mod_gm, "B")
        alpha_grass = lib.create_expression(m, unreal.MaterialExpressionClamp, -500, 500)
        lib.connect(mod_gr, "", alpha_grass, "Input")
        alpha_mud = lib.create_expression(m, unreal.MaterialExpressionClamp, -500, 640)
        lib.connect(mod_gm, "", alpha_mud, "Input")
        grass_amt_mul = lib.create_expression(m, unreal.MaterialExpressionMultiply, -300, 500)
        lib.connect(alpha_grass, "", grass_amt_mul, "A")
        lib.connect(grass_amt, "", grass_amt_mul, "B")
        mud_alpha = lib.create_expression(m, unreal.MaterialExpressionMultiply, -300, 640)
        lib.connect(alpha_mud, "", mud_alpha, "A")
        lib.connect(mud_amt, "", mud_alpha, "B")
        grass_base = lib.create_expression(m, unreal.MaterialExpressionMultiply, -120, 500)
        lib.connect(grass_amt_mul, "", grass_base, "A")
        lib.connect(path_inv, "", grass_base, "B")
        mud_alpha_pin = ""

    one_g = lib.create_expression(m, unreal.MaterialExpressionConstant, 440, 480)
    one_g.set_editor_property("r", 1.0)
    layer_scale_g = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 440, 560)
    lib.connect(one_g, "", layer_scale_g, "A")
    lib.connect(layer_weights["Grass"], "", layer_scale_g, "B")
    lib.connect(has_paint, "", layer_scale_g, "Alpha")
    grass_scale = painted_sw(m, 620, 520, layer_scale_g, one_g)
    grass_final = lib.create_expression(m, unreal.MaterialExpressionMultiply, 800, 520)
    lib.connect(grass_base, "", grass_final, "A")
    lib.connect(grass_scale, "", grass_final, "B")
    # A soft edge complements the hard Path paint.  At zero strength this is
    # precisely the former grass mask; positive values only clear edge foliage.
    path_edge_inv = lib.create_expression(m, unreal.MaterialExpressionOneMinus, 800, 620)
    lib.connect(path_fac, "", path_edge_inv, "Input")
    path_edge_shape = lib.create_expression(m, unreal.MaterialExpressionMultiply, 980, 620)
    lib.connect(path_fac, "", path_edge_shape, "A")
    lib.connect(path_edge_inv, "", path_edge_shape, "B")
    path_edge = lib.create_expression(m, unreal.MaterialExpressionMultiply, 1160, 620)
    lib.connect(path_edge_shape, "", path_edge, "A")
    lib.connect(path_edge_strength, "", path_edge, "B")
    path_clear_sat = lib.create_expression(m, unreal.MaterialExpressionSaturate, 1520, 620)
    lib.connect(path_edge, "", path_clear_sat, "Input")
    grass_path_inv = lib.create_expression(m, unreal.MaterialExpressionOneMinus, 1700, 620)
    lib.connect(path_clear_sat, "", grass_path_inv, "Input")
    grass_path_mask = lib.create_expression(m, unreal.MaterialExpressionMultiply, 1880, 620)
    lib.connect(grass_final, "", grass_path_mask, "A")
    lib.connect(grass_path_inv, "", grass_path_mask, "B")
    grass_final = grass_path_mask

    def proc_lerp3(col_a, col_b, col_c, x, y):
        ab = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, x, y)
        lib.connect(col_a, "", ab, "A")
        lib.connect(col_b, "", ab, "B")
        lib.connect(grass_final, "", ab, "Alpha")
        out = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, x + 200, y)
        lib.connect(ab, "", out, "A")
        lib.connect(col_c, "", out, "B")
        if compete and mud_alpha_pin:
            lib.connect(mud_alpha, mud_alpha_pin, out, "Alpha")
        else:
            lib.connect(mud_alpha, "", out, "Alpha")
        return out

    proc_col = proc_lerp3(layer_samples["Rock"]["color"], layer_samples["Grass"]["color"], layer_samples["Mud"]["color"], -100, 520)
    proc_nrm = proc_lerp3(layer_samples["Rock"]["normal"], layer_samples["Grass"]["normal"], layer_samples["Mud"]["normal"], -100, 760)

    # ---- Itto: truchet + cracks + curvature wear + ink (after proc_col) ----
    itto_wxy = lib.create_expression(m, unreal.MaterialExpressionWorldPosition, px + 1600, py + 7140)
    itto_uv = lib.create_expression(m, unreal.MaterialExpressionComponentMask, px + 1800, py + 7140)
    itto_uv.set_editor_property("r", True)
    itto_uv.set_editor_property("g", True)
    itto_uv.set_editor_property("b", False)
    itto_uv.set_editor_property("a", False)
    lib.connect_unary(itto_wxy, itto_uv)
    itto_noise = lib.create_expression(m, unreal.MaterialExpressionNoise, px + 2000, py + 7140)
    lib.connect(itto_uv, "", itto_noise, "Position")
    itto_ns = lib.create_expression(m, unreal.MaterialExpressionMultiply, px + 2200, py + 7140)
    lib.connect(itto_noise, "", itto_ns, "A")
    lib.connect(itto_pattern_scale, "", itto_ns, "B")
    itto_nsat = lib.create_expression(m, unreal.MaterialExpressionSaturate, px + 2400, py + 7140)
    lib.connect(itto_ns, "", itto_nsat, "Input")
    itto_cracks = edge_detect_scalar(m, itto_nsat, px + 2600, py + 7140)
    itto_crack_mask = lib.create_expression(m, unreal.MaterialExpressionMultiply, px + 2800, py + 7140)
    lib.connect(itto_cracks, "", itto_crack_mask, "A")
    lib.connect(itto_crack_depth, "", itto_crack_mask, "B")
    itto_curve_abs = lib.create_expression(m, unreal.MaterialExpressionAbs, px + 2000, py + 7400)
    lib.connect(layer_samples["Rock"]["normal"], "", itto_curve_abs, "Input")
    itto_csub = lib.create_expression(m, unreal.MaterialExpressionSubtract, px + 2200, py + 7400)
    lib.connect(itto_curve_abs, "", itto_csub, "A")
    itto_csub_const = lib.create_expression(m, unreal.MaterialExpressionConstant, px + 2200, py + 7500)
    itto_csub_const.set_editor_property("r", 0.5)
    lib.connect(itto_csub_const, "", itto_csub, "B")
    itto_cabs = lib.create_expression(m, unreal.MaterialExpressionAbs, px + 2400, py + 7400)
    lib.connect(itto_csub, "", itto_cabs, "Input")
    itto_wear = lib.create_expression(m, unreal.MaterialExpressionMultiply, px + 2600, py + 7400)
    lib.connect(itto_cabs, "", itto_wear, "A")
    lib.connect(itto_wear_amount, "", itto_wear, "B")
    itto_height_add = lib.create_expression(m, unreal.MaterialExpressionAdd, px + 2800, py + 7300)
    lib.connect(itto_crack_mask, "", itto_height_add, "A")
    lib.connect(itto_wear, "", itto_height_add, "B")
    itto_height_scaled = lib.create_expression(m, unreal.MaterialExpressionMultiply, px + 3000, py + 7300)
    lib.connect(itto_height_add, "", itto_height_scaled, "A")
    itto_h_scale = lib.create_expression(m, unreal.MaterialExpressionConstant, px + 3000, py + 7400)
    itto_h_scale.set_editor_property("r", 0.08)
    lib.connect(itto_h_scale, "", itto_height_scaled, "B")
    itto_bu = lib.create_expression(m, unreal.MaterialExpressionMultiply, px + 2600, py + 7580)
    lib.connect(itto_height_scaled, "", itto_bu, "A")
    lib.connect(itto_breakup, "", itto_bu, "B")
    itto_ink_l = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, px + 2800, py + 7580)
    lib.connect(proc_col, "", itto_ink_l, "A")
    lib.connect(layer_samples["Rock"]["color"], "", itto_ink_l, "B")
    lib.connect(itto_bu, "", itto_ink_l, "Alpha")
    proc_col = itto_ink_l

    def norm_w(w, y):
        d = lib.create_expression(m, unreal.MaterialExpressionDivide, 440, y)
        lib.connect(w, "", d, "A")
        lib.connect(paint_safe, "", d, "B")
        return d

    norm = {n: norm_w(layer_weights[n], 1180 + i * 60) for i, n in enumerate(BASE_LAYER_NAMES)}

    def paint_wsum(vals, y):
        acc = None
        for i, (nm, val) in enumerate(vals):
            term = lib.create_expression(m, unreal.MaterialExpressionMultiply, 640, y + i * 50)
            lib.connect(norm[nm], "", term, "A")
            lib.connect(val, "", term, "B")
            if acc is None:
                acc = term
            else:
                add = lib.create_expression(m, unreal.MaterialExpressionAdd, 820, y + i * 50)
                lib.connect(acc, "", add, "A")
                lib.connect(term, "", add, "B")
                acc = add
        return acc

    one_c = lib.create_expression(m, unreal.MaterialExpressionConstant, 440, 780)
    one_c.set_editor_property("r", 1.0)
    dark_sub = lib.create_expression(m, unreal.MaterialExpressionSubtract, 440, 860)
    lib.connect(one_c, "", dark_sub, "A")
    lib.connect(shore_darken, "", dark_sub, "B")
    mud_dark_mul = lib.create_expression(m, unreal.MaterialExpressionMultiply, 620, 780)
    lib.connect(layer_samples["Mud"]["color"], "", mud_dark_mul, "A")
    lib.connect(dark_sub, "", mud_dark_mul, "B")
    mud_paint_col = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 800, 700)
    lib.connect(layer_samples["Mud"]["color"], "", mud_paint_col, "A")
    lib.connect(mud_dark_mul, "", mud_paint_col, "B")
    lib.connect(shore_mask, "", mud_paint_col, "Alpha")

    paint_col = paint_wsum(
        [("Rock", layer_samples["Rock"]["color"]), ("Grass", layer_samples["Grass"]["color"]),
         ("Mud", mud_paint_col)], 1280)
    paint_nrm = paint_wsum(
        [("Rock", layer_samples["Rock"]["normal"]), ("Grass", layer_samples["Grass"]["normal"]),
         ("Mud", layer_samples["Mud"]["normal"])], 1480)

    def pbr_roughness(sample, legacy_value, x, y):
        rough_channel = lib.create_expression(m, unreal.MaterialExpressionComponentMask, x, y)
        rough_channel.set_editor_property("r", False)
        rough_channel.set_editor_property("g", True)
        rough_channel.set_editor_property("b", False)
        rough_channel.set_editor_property("a", False)
        lib.connect(sample, "", rough_channel, "Input")
        scaled = lib.create_expression(m, unreal.MaterialExpressionMultiply, x + 160, y)
        lib.connect(rough_channel, "", scaled, "A")
        lib.connect(legacy_value, "", scaled, "B")
        sw = static_sw(m, "bUseLayerORM", "05 | Surface", x + 320, y, False)
        lib.connect_static_switch(sw, scaled, legacy_value)
        return sw

    rock_rough_pbr = pbr_roughness(layer_samples["Rock"]["orm"], rock_rough, 720, 1740)
    grass_rough_pbr = pbr_roughness(layer_samples["Grass"]["orm"], grass_rough, 720, 1840)
    mud_rough_pbr = pbr_roughness(layer_samples["Mud"]["orm"], mud_rough, 720, 1940)
    path_rough_pbr = pbr_roughness(
        path_layer_sample["orm"] if path_layer_sample else layer_samples["Rock"]["orm"], roughness_s, 720, 2040,
    )
    paint_rough = paint_wsum(
        [("Rock", rock_rough_pbr), ("Grass", grass_rough_pbr), ("Mud", mud_rough_pbr)], 1680)

    col_blend = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 900, 560)
    lib.connect(proc_col, "", col_blend, "A")
    lib.connect(paint_col, "", col_blend, "B")
    lib.connect(has_paint, "", col_blend, "Alpha")
    col_out = painted_sw(m, 1100, 560, col_blend, proc_col)
    path_color = lib.create_expression(m, unreal.MaterialExpressionMultiply, 1280, 560)
    lib.connect(path_layer_sample["color"] if path_layer_sample else path_tint, "", path_color, "A")
    lib.connect(path_tint, "", path_color, "B")
    path_col_blend = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 1460, 560)
    lib.connect(col_out, "", path_col_blend, "A")
    lib.connect(path_color, "", path_col_blend, "B")
    lib.connect(path_fac, "", path_col_blend, "Alpha")
    col_out = path_col_blend
    nrm_blend = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 900, 800)
    lib.connect(proc_nrm, "", nrm_blend, "A")
    lib.connect(paint_nrm, "", nrm_blend, "B")
    lib.connect(has_paint, "", nrm_blend, "Alpha")
    nrm_out = painted_sw(m, 1100, 800, nrm_blend, proc_nrm)
    path_nrm_blend = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 1280, 800)
    lib.connect(nrm_out, "", path_nrm_blend, "A")
    lib.connect(path_layer_sample["normal"] if path_layer_sample else layer_samples["Rock"]["normal"], "", path_nrm_blend, "B")
    lib.connect(path_fac, "", path_nrm_blend, "Alpha")
    nrm_out = path_nrm_blend

    nrm_adj = mf_call(m, MF_NORMAL_ADJUST, 1320, 800)
    if nrm_adj:
        one_layer = lib.create_expression(m, unreal.MaterialExpressionConstant, 1120, 920)
        one_layer.set_editor_property("r", 1.0)
        pow_one = lib.create_expression(m, unreal.MaterialExpressionConstant, 1120, 840)
        pow_one.set_editor_property("r", 1.0)
        lib.connect(nrm_out, "", nrm_adj, "Normal")
        lib.connect(normal_str, "", nrm_adj, "NormalStrength")
        lib.connect(pow_one, "", nrm_adj, "NormalPower")
        lib.connect(one_layer, "", nrm_adj, "LayerNormalStrength")
        nrm_final = nrm_adj
    else:
        nrm_final = nrm_out

    # Shared camera-distance bands. They gate optional detail rather than opacity,
    # so terrain remains stable across LODs and never inherits mesh dither behavior.
    distance_wp = lib.create_expression(m, unreal.MaterialExpressionWorldPosition, 1320, 1120)
    distance_cam = lib.create_expression(m, unreal.MaterialExpressionCameraPositionWS, 1320, 1220)
    distance_vec = lib.create_expression(m, unreal.MaterialExpressionSubtract, 1500, 1160)
    lib.connect(distance_wp, "", distance_vec, "A")
    lib.connect(distance_cam, "", distance_vec, "B")
    distance_len = lib.create_expression(m, unreal.MaterialExpressionLength, 1680, 1160)
    lib.connect(distance_vec, "", distance_len, "Input")
    near_sub = lib.create_expression(m, unreal.MaterialExpressionSubtract, 1860, 1120)
    lib.connect(distance_len, "", near_sub, "A")
    lib.connect(near_start, "", near_sub, "B")
    near_span = lib.create_expression(m, unreal.MaterialExpressionSubtract, 1860, 1220)
    lib.connect(near_end, "", near_span, "A")
    lib.connect(near_start, "", near_span, "B")
    near_norm = lib.create_expression(m, unreal.MaterialExpressionDivide, 2040, 1120)
    lib.connect(near_sub, "", near_norm, "A")
    lib.connect(near_span, "", near_norm, "B")
    near_sat = lib.create_expression(m, unreal.MaterialExpressionSaturate, 2220, 1120)
    lib.connect(near_norm, "", near_sat, "Input")
    near_weight = lib.create_expression(m, unreal.MaterialExpressionOneMinus, 2400, 1120)
    lib.connect(near_sat, "", near_weight, "Input")
    detail_uv = lib.create_expression(m, unreal.MaterialExpressionMultiply, 1500, 1360)
    lib.connect(layer_uv, "", detail_uv, "A")
    detail_tiling = lib.create_expression(m, unreal.MaterialExpressionConstant, 1320, 1400)
    detail_tiling.set_editor_property("r", 8.0)
    lib.connect(detail_tiling, "", detail_uv, "B")
    detail_sample = lib.create_expression(m, unreal.MaterialExpressionTextureSample, 1680, 1360)
    lib.try_set_editor_property(detail_sample, "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    lib.connect(detail_normal, "Texture", detail_sample, "Texture")
    lib.connect(detail_uv, "", detail_sample, "UVs")
    detail_gate = lib.create_expression(m, unreal.MaterialExpressionMultiply, 1860, 1360)
    lib.connect(near_weight, "", detail_gate, "A")
    lib.connect(detail_strength, "", detail_gate, "B")
    detail_nrm = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 2040, 1320)
    lib.connect(nrm_final, "", detail_nrm, "A")
    lib.connect(detail_sample, "", detail_nrm, "B")
    lib.connect(detail_gate, "", detail_nrm, "Alpha")
    nrm_final = detail_nrm

    pnorm = lib.create_expression(m, unreal.MaterialExpressionPixelNormalWS, 300, 340)
    up = lib.create_expression(m, unreal.MaterialExpressionConstant3Vector, 300, 480)
    up.set_editor_property("constant", unreal.LinearColor(0, 0, 1, 1))
    slope_dot = lib.create_expression(m, unreal.MaterialExpressionDotProduct, 500, 400)
    lib.connect(pnorm, "", slope_dot, "A")
    lib.connect(up, "", slope_dot, "B")
    slope_inv = lib.create_expression(m, unreal.MaterialExpressionOneMinus, 680, 400)
    lib.connect(slope_dot, "", slope_inv, "Input")
    slope_pow = lib.create_expression(m, unreal.MaterialExpressionPower, 860, 400)
    lib.connect(slope_inv, "", slope_pow, "Base")
    lib.connect(slope_sharp, "", slope_pow, "Exp")
    # The existing general UV/triplanar mode remains intact.  This optional lane
    # adds world-aligned rock only on steep surfaces, preventing grass/path paint
    # from losing its authored UV direction.
    tri_slope_sub = lib.create_expression(m, unreal.MaterialExpressionSubtract, 860, 500)
    lib.connect(slope_inv, "", tri_slope_sub, "A")
    lib.connect(tri_slope_start, "", tri_slope_sub, "B")
    tri_slope_span = lib.create_expression(m, unreal.MaterialExpressionSubtract, 680, 540)
    lib.connect(tri_slope_end, "", tri_slope_span, "A")
    lib.connect(tri_slope_start, "", tri_slope_span, "B")
    tri_slope_norm = lib.create_expression(m, unreal.MaterialExpressionDivide, 1040, 500)
    lib.connect(tri_slope_sub, "", tri_slope_norm, "A")
    lib.connect(tri_slope_span, "", tri_slope_norm, "B")
    tri_slope_mask = lib.create_expression(m, unreal.MaterialExpressionSaturate, 1200, 500)
    lib.connect(tri_slope_norm, "", tri_slope_mask, "Input")
    tri_rock_raw = sample_triplanar(m, layer_samples["Rock"]["albedo_param"], tri_tiling, "RockAlb", 1040, 620)
    tri_rock_tinted = lib.create_expression(m, unreal.MaterialExpressionMultiply, 1220, 620)
    lib.connect(tri_rock_raw, "", tri_rock_tinted, "A")
    lib.connect(rock_tint, "", tri_rock_tinted, "B")
    tri_rock_weight = lib.create_expression(m, unreal.MaterialExpressionMultiply, 1380, 520)
    lib.connect(tri_slope_mask, "", tri_rock_weight, "A")
    lib.connect(tri_blend, "", tri_rock_weight, "B")
    rock_surface = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 1560, 560)
    lib.connect(layer_samples["Rock"]["color"], "", rock_surface, "A")
    lib.connect(tri_rock_tinted, "", rock_surface, "B")
    lib.connect(tri_rock_weight, "", rock_surface, "Alpha")
    cliff_col = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 1040, 560)
    lib.connect(col_out, "", cliff_col, "A")
    lib.connect(rock_surface, "", cliff_col, "B")
    lib.connect(slope_pow, "", cliff_col, "Alpha")

    wp = lib.create_expression(m, unreal.MaterialExpressionWorldPosition, 300, 900)
    macro_mul = lib.create_expression(m, unreal.MaterialExpressionMultiply, 500, 900)
    lib.connect(wp, "", macro_mul, "A")
    ms = lib.create_expression(m, unreal.MaterialExpressionConstant, 300, 1000)
    ms.set_editor_property("r", 0.002)
    lib.connect(ms, "", macro_mul, "B")
    macro_mul2 = lib.create_expression(m, unreal.MaterialExpressionMultiply, 700, 900)
    lib.connect(macro_mul, "", macro_mul2, "A")
    lib.connect(macro_scale, "", macro_mul2, "B")
    macro_noise = lib.create_expression(m, unreal.MaterialExpressionNoise, 900, 900)
    lib.connect(macro_mul2, "", macro_noise, "Position")
    macro_g = lib.create_expression(m, unreal.MaterialExpressionMultiply, 1100, 900)
    lib.connect(macro_noise, "", macro_g, "A")
    lib.connect(macro_str, "", macro_g, "B")
    macro_layer_mix_a = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 1100, 980)
    lib.connect(rock_macro, "", macro_layer_mix_a, "A")
    lib.connect(grass_macro, "", macro_layer_mix_a, "B")
    lib.connect(grass_final, "", macro_layer_mix_a, "Alpha")
    macro_layer_mix_b = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 1280, 980)
    lib.connect(macro_layer_mix_a, "", macro_layer_mix_b, "A")
    lib.connect(mud_macro, "", macro_layer_mix_b, "B")
    lib.connect(mud_alpha, mud_alpha_pin, macro_layer_mix_b, "Alpha")
    macro_layer_mix_c = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 1460, 980)
    lib.connect(macro_layer_mix_b, "", macro_layer_mix_c, "A")
    lib.connect(path_macro, "", macro_layer_mix_c, "B")
    lib.connect(path_fac, "", macro_layer_mix_c, "Alpha")
    macro_layered = lib.create_expression(m, unreal.MaterialExpressionMultiply, 1280, 1040)
    lib.connect(macro_g, "", macro_layered, "A")
    lib.connect(macro_layer_mix_c, "", macro_layered, "B")
    macro_col = lib.create_expression(m, unreal.MaterialExpressionAdd, 1300, 860)
    lib.connect(cliff_col, "", macro_col, "A")
    lib.connect(macro_layered, "", macro_col, "B")

    snow_dot = lib.create_expression(m, unreal.MaterialExpressionDotProduct, 1100, 1040)
    lib.connect(pnorm, "", snow_dot, "A")
    lib.connect(up, "", snow_dot, "B")
    snow_sat = lib.create_expression(m, unreal.MaterialExpressionSaturate, 1280, 1040)
    lib.connect(snow_dot, "", snow_sat, "Input")
    snow_pow = lib.create_expression(m, unreal.MaterialExpressionPower, 1460, 1040)
    lib.connect(snow_sat, "", snow_pow, "Base")
    lib.connect(snow_bias, "", snow_pow, "Exp")
    snow_amt = lib.create_expression(m, unreal.MaterialExpressionMultiply, 1640, 1040)
    lib.connect(snow_pow, "", snow_amt, "A")
    lib.connect(snow_str, "", snow_amt, "B")
    final_col = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 1820, 900)
    lib.connect(macro_col, "", final_col, "A")
    lib.connect(snow_tint, "", final_col, "B")
    lib.connect(snow_amt, "", final_col, "Alpha")

    water_lerp = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 2000, 900)
    lib.connect(final_col, "", water_lerp, "A")
    lib.connect(water_tint, "", water_lerp, "B")
    water_fac = lib.create_expression(m, unreal.MaterialExpressionMultiply, 1820, 1000)
    lib.connect(shore_mask, "", water_fac, "A")
    lib.connect(water_align, "", water_fac, "B")
    lib.connect(water_fac, "", water_lerp, "Alpha")

    dream = mf_call(m, MF_NIKKI_DREAM, 2180, 880)
    nikki_col = water_lerp
    if dream:
        lib.connect(water_lerp, "", dream, "BaseColor")
        lib.connect(pastel, "", dream, "PastelLift")
        lib.connect(dream_tint, "", dream, "DreamTint")
        lib.connect(dream_sat, "", dream, "DreamSaturation")
        lib.connect(dream_con, "", dream, "DreamContrast")
        lib.connect(shadow_lift, "", dream, "DreamShadowLift")
        nikki_col = dream
    rim = mf_call(m, MF_NIKKI_RIM, 2380, 880)
    if rim:
        lib.connect(nikki_col, "", rim, "BaseColor")
        lib.connect(nrm_final, "", rim, "Normal")
        lib.connect(rim_color, "", rim, "RimColor")
        lib.connect(rim_int, "", rim, "RimIntensity")
        lib.connect(rim_width, "", rim, "RimWidth")
        lib.connect(glow_int, "", rim, "GlowIntensity")
        lib.connect(bloom, "", rim, "BloomBoost")
        nikki_col = rim
    nikki_fast_col = nikki_col
    pulse = lib.collection_scalar(m, MPC_SAKURA, "SparklePulse", 2180, 1040)
    audio_global = lib.collection_scalar(m, MPC_PORTFOLIO_AUDIO, "GlobalReactivity", 2180, 1160)
    if not audio_global:
        raise RuntimeError(
            "Landscape audio-reactivity requires "
            "MPC_Melodia_Palette.GlobalReactivity"
        )
    audio_weighted = lib.create_expression(m, unreal.MaterialExpressionMultiply, 2360, 1160)
    lib.connect(audio_global, "", audio_weighted, "A")
    lib.connect(audio_reactive_strength, "", audio_weighted, "B")
    combined_pulse = lib.create_expression(m, unreal.MaterialExpressionAdd, 2540, 1040)
    lib.connect(pulse, "", combined_pulse, "A")
    lib.connect(audio_weighted, "", combined_pulse, "B")
    pulse_clamped = lib.create_expression(m, unreal.MaterialExpressionSaturate, 2720, 1040)
    lib.connect(combined_pulse, "", pulse_clamped, "Input")
    wonder_sparkle_weight = lib.create_expression(m, unreal.MaterialExpressionMultiply, 2720, 1140)
    lib.connect(wonder_mask, "", wonder_sparkle_weight, "A")
    lib.connect(wonder_sparkle, "", wonder_sparkle_weight, "B")
    sparkle_base = lib.create_expression(m, unreal.MaterialExpressionAdd, 2860, 1140)
    lib.connect(spark_int, "", sparkle_base, "A")
    lib.connect(wonder_sparkle_weight, "", sparkle_base, "B")
    spark_eff = lib.create_expression(m, unreal.MaterialExpressionMultiply, 2900, 1040)
    lib.connect(sparkle_base, "", spark_eff, "A")
    lib.connect(pulse_clamped, "", spark_eff, "B")
    sparkle = mf_call(m, MF_NIKKI_SPARKLE, 2560, 880)
    if sparkle:
        lib.connect(nikki_col, "", sparkle, "BaseColor")
        lib.connect(layer_uv, "", sparkle, "UV")
        lib.connect(spark_mask, "Texture", sparkle, "SparkleMask")
        lib.connect(spark_eff, "", sparkle, "SparkleIntensity")
        lib.connect(spark_thresh, "", sparkle, "SparkleThreshold")
        lib.connect(spark_color, "", sparkle, "SparkleColor")
        nikki_col = sparkle
    irid_mf = mf_call(m, MF_NIKKI_IRID, 2760, 880)
    if irid_mf:
        lib.connect(nikki_col, "", irid_mf, "BaseColor")
        lib.connect(nrm_final, "", irid_mf, "Normal")
        lib.connect(irid, "", irid_mf, "Iridescence")
        lib.connect(irid_tint, "", irid_mf, "IridescenceTint")
        lib.connect(irid_pow, "", irid_mf, "IridescencePower")
        lib.connect(fabric_sheen, "", irid_mf, "FabricSheen")
        lib.connect(sheen_tint, "", irid_mf, "SheenTint")
        nikki_col = irid_mf

    nikki_hero_col = nikki_col
    lib.connect_static_switch(nikki_fast_sw, nikki_fast_col, water_lerp)
    lib.connect_static_switch(nikki_hero_sw, nikki_hero_col, nikki_fast_sw)
    nikki_col = nikki_hero_sw

    # ---- Madoka full chain (after nikki hero color) ----
    emissive_zero = lib.create_expression(m, unreal.MaterialExpressionConstant3Vector, px + 1400, py + 5480)
    emissive_zero.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    emissive = emissive_zero
    madoka_wxy = lib.create_expression(m, unreal.MaterialExpressionWorldPosition, px + 1600, py + 5480)
    madoka_uv = lib.create_expression(m, unreal.MaterialExpressionComponentMask, px + 1800, py + 5480)
    madoka_uv.set_editor_property("r", True)
    madoka_uv.set_editor_property("g", True)
    madoka_uv.set_editor_property("b", False)
    madoka_uv.set_editor_property("a", False)
    lib.connect_unary(madoka_wxy, madoka_uv)
    madoka_vor = lib.create_expression(m, unreal.MaterialExpressionNoise, px + 2000, py + 5480)
    lib.connect(madoka_uv, "", madoka_vor, "Position")
    madoka_vor_s = lib.create_expression(m, unreal.MaterialExpressionMultiply, px + 2200, py + 5480)
    lib.connect(madoka_vor, "", madoka_vor_s, "A")
    lib.connect(witch_wallpaper_scale, "", madoka_vor_s, "B")
    madoka_vor_sat = lib.create_expression(m, unreal.MaterialExpressionSaturate, px + 2400, py + 5480)
    lib.connect(madoka_vor_s, "", madoka_vor_sat, "Input")
    madoka_veins = edge_detect_scalar(m, madoka_vor_sat, px + 2600, py + 5480)
    madoka_vm = lib.create_expression(m, unreal.MaterialExpressionMultiply, px + 2800, py + 5480)
    lib.connect(madoka_veins, "", madoka_vm, "A")
    lib.connect(madoka_vein_emissive, "", madoka_vm, "B")
    madoka_cute = lib.create_expression(m, unreal.MaterialExpressionConstant3Vector, px + 2000, py + 5680)
    madoka_cute.set_editor_property("constant", unreal.LinearColor(0.92, 0.55, 0.88, 1.0))
    madoka_corrupt = lib.create_expression(m, unreal.MaterialExpressionConstant3Vector, px + 2000, py + 5780)
    madoka_corrupt.set_editor_property("constant", unreal.LinearColor(0.55, 0.12, 0.18, 1.0))
    madoka_cmix = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, px + 2200, py + 5680)
    lib.connect(madoka_cute, "", madoka_cmix, "A")
    lib.connect(madoka_corrupt, "", madoka_cmix, "B")
    lib.connect(madoka_cute_bias, "", madoka_cmix, "Alpha")
    madoka_dist = lib.create_expression(m, unreal.MaterialExpressionDistance, px + 2000, py + 5980)
    madoka_rc = lib.create_expression(m, unreal.MaterialExpressionConstant2Vector, px + 2000, py + 6080)
    madoka_rc.set_editor_property("r", 0.5)
    madoka_rc.set_editor_property("g", 0.5)
    lib.connect(madoka_uv, "", madoka_dist, "A")
    lib.connect(madoka_rc, "", madoka_dist, "B")
    madoka_ds = lib.create_expression(m, unreal.MaterialExpressionMultiply, px + 2200, py + 5980)
    lib.connect(madoka_dist, "", madoka_ds, "A")
    lib.connect(madoka_radial_bands, "", madoka_ds, "B")
    madoka_sin = lib.create_expression(m, unreal.MaterialExpressionSine, px + 2400, py + 5980)
    madoka_sin.set_editor_property("period", 1.0)
    lib.connect(madoka_ds, "", madoka_sin, "Input")
    madoka_abs = lib.create_expression(m, unreal.MaterialExpressionAbs, px + 2600, py + 5980)
    lib.connect(madoka_sin, "", madoka_abs, "Input")
    madoka_ring = lib.create_expression(m, unreal.MaterialExpressionMultiply, px + 2800, py + 5980)
    lib.connect(madoka_abs, "", madoka_ring, "A")
    lib.connect(madoka_glow, "", madoka_ring, "B")
    madoka_cadd = lib.create_expression(m, unreal.MaterialExpressionAdd, px + 2600, py + 5680)
    lib.connect(madoka_cmix, "", madoka_cadd, "A")
    lib.connect(madoka_ring, "", madoka_cadd, "B")
    madoka_cfinal = madoka_cadd
    madoka_emi = lib.create_expression(m, unreal.MaterialExpressionAdd, px + 3000, py + 5480)
    lib.connect(emissive, "", madoka_emi, "A")
    lib.connect(madoka_vm, "", madoka_emi, "B")
    emissive = madoka_emi
    madoka_cblend = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, px + 3000, py + 5640)
    lib.connect(nikki_hero_col, "", madoka_cblend, "A")
    lib.connect(madoka_cfinal, "", madoka_cblend, "B")
    lib.connect(madoka_glow, "", madoka_cblend, "Alpha")
    nikki_hero_col = madoka_cblend
    lib.connect_static_switch(nikki_hero_sw, nikki_hero_col, nikki_fast_sw)
    nikki_col = nikki_hero_sw

    wp_sf = lib.create_expression(m, unreal.MaterialExpressionWorldPosition, 2600, 1200)
    wxy_sf = lib.create_expression(m, unreal.MaterialExpressionComponentMask, 2760, 1200)
    wxy_sf.set_editor_property("r", True)
    wxy_sf.set_editor_property("g", True)
    wxy_sf.set_editor_property("b", False)
    wxy_sf.set_editor_property("a", False)
    lib.connect(wp_sf, "", wxy_sf, "")
    shadow_amt = lib.create_expression(m, unreal.MaterialExpressionSaturate, 2920, 1200)
    lib.connect(shadow_dream_str, "", shadow_amt, "Input")
    sf_mf = mf_call(m, MF_SHADOW_FLOWER, 2600, 1360)
    if sf_mf:
        lib.connect(wxy_sf, "", sf_mf, "WorldXY")
        lib.connect(flower_mask, "Texture", sf_mf, "ShadowMask")
        lib.connect(shadow_amt, "", sf_mf, "ShadowAmount")
        lib.connect(flower_scale, "", sf_mf, "Scale")
        lib.connect(flower_scale_fine, "", sf_mf, "ScaleFine")
        const_rot = lib.create_expression(m, unreal.MaterialExpressionConstant, 2440, 1360)
        const_rot.set_editor_property("r", 0.35)
        lib.connect(const_rot, "", sf_mf, "Rotation")
        const_jit = lib.create_expression(m, unreal.MaterialExpressionConstant, 2440, 1460)
        const_jit.set_editor_property("r", 0.2)
        lib.connect(const_jit, "", sf_mf, "Jitter")
        lib.connect(flower_col, "", sf_mf, "FlowerColor")
        lib.connect(flower_str, "", sf_mf, "Strength")
        const_soft = lib.create_expression(m, unreal.MaterialExpressionConstant, 2440, 1560)
        const_soft.set_editor_property("r", 0.45)
        lib.connect(const_soft, "", sf_mf, "Softness")
        const_dark = lib.create_expression(m, unreal.MaterialExpressionConstant, 2440, 1660)
        const_dark.set_editor_property("r", 0.32)
        lib.connect(const_dark, "", sf_mf, "AlbedoDarken")
        pulse_sf = lib.collection_scalar(m, MPC_SAKURA, "SparklePulse", 2440, 1760)
        lib.connect(pulse_sf, "", sf_mf, "Pulse")
        lib.connect(flower_pulse_str, "", sf_mf, "PulseStrength")
        one_sf = lib.create_expression(m, unreal.MaterialExpressionConstant, 3080, 1320)
        one_sf.set_editor_property("r", 1.0)
        darken_fac = lib.create_expression(m, unreal.MaterialExpressionMultiply, 3080, 1400)
        lib.connect(sf_mf, "", darken_fac, "A")
        dark_sub = lib.create_expression(m, unreal.MaterialExpressionSubtract, 3240, 1320)
        lib.connect(one_sf, "", dark_sub, "A")
        lib.connect(darken_fac, "", dark_sub, "B")
        nikki_dark = lib.create_expression(m, unreal.MaterialExpressionMultiply, 3400, 1280)
        lib.connect(nikki_col, "", nikki_dark, "A")
        lib.connect(dark_sub, "", nikki_dark, "B")
        nikki_col = nikki_dark

    # Wonder is a dedicated paint overlay.  It can lift a small authored clearing
    # without participating in the weight-blended base-surface competition.
    wonder_weight_raw = lib.create_expression(m, unreal.MaterialExpressionMultiply, 3580, 1280)
    lib.connect(wonder_mask, "", wonder_weight_raw, "A")
    lib.connect(wonder_strength, "", wonder_weight_raw, "B")
    wonder_weight = lib.create_expression(m, unreal.MaterialExpressionSaturate, 3760, 1280)
    lib.connect(wonder_weight_raw, "", wonder_weight, "Input")
    hero_wonder_col = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 3940, 1280)
    lib.connect(nikki_col, "", hero_wonder_col, "A")
    lib.connect(wonder_palette, "", hero_wonder_col, "B")
    lib.connect(wonder_weight, "", hero_wonder_col, "Alpha")
    standard_wonder_col = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 3940, 1400)
    lib.connect(water_lerp, "", standard_wonder_col, "A")
    lib.connect(wonder_palette, "", standard_wonder_col, "B")
    lib.connect(wonder_weight, "", standard_wonder_col, "Alpha")
    lib.connect_static_switch(hero_tier, hero_wonder_col, standard_wonder_col)
    tier_col = hero_tier
    # Fast retains the authored base blend but omits the optional presentation lanes.
    lib.connect_static_switch(fast_tier, cliff_col, tier_col)
    tier_col = fast_tier

    far_sub = lib.create_expression(m, unreal.MaterialExpressionSubtract, 4120, 1280)
    lib.connect(distance_len, "", far_sub, "A")
    lib.connect(far_atmo_start, "", far_sub, "B")
    far_span = lib.create_expression(m, unreal.MaterialExpressionSubtract, 4120, 1380)
    lib.connect(far_atmo_end, "", far_span, "A")
    lib.connect(far_atmo_start, "", far_span, "B")
    far_norm = lib.create_expression(m, unreal.MaterialExpressionDivide, 4300, 1280)
    lib.connect(far_sub, "", far_norm, "A")
    lib.connect(far_span, "", far_norm, "B")
    far_sat = lib.create_expression(m, unreal.MaterialExpressionSaturate, 4480, 1280)
    lib.connect(far_norm, "", far_sat, "Input")
    far_weight = lib.create_expression(m, unreal.MaterialExpressionMultiply, 4660, 1280)
    lib.connect(far_sat, "", far_weight, "A")
    lib.connect(far_atmo_strength, "", far_weight, "B")
    far_col = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 4840, 1280)
    lib.connect(tier_col, "", far_col, "A")
    lib.connect(far_atmo_color, "", far_col, "B")
    lib.connect(far_weight, "", far_col, "Alpha")

    # Compile-time debug views: enable exactly one switch in an MI when auditing
    # paint.  They never alter a shipping permutation while all switches are off.
    debug_weights_col = lib.connect_append3_from_scalars(layer_weights["Grass"], layer_weights["Mud"], path_fac, m, 4840, 1460)
    def debug_color(mask, color, x, y):
        tint = lib.create_expression(m, unreal.MaterialExpressionConstant3Vector, x, y)
        tint.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
        out = lib.create_expression(m, unreal.MaterialExpressionMultiply, x + 160, y)
        lib.connect(mask, "", out, "A")
        lib.connect(tint, "", out, "B")
        return out
    debug_height_col = debug_color(grass_final, (1.0, 1.0, 1.0), 4840, 1560)
    debug_path_col = debug_color(path_fac, (1.0, 0.62, 0.15), 4840, 1660)
    debug_slope_col = debug_color(tri_slope_mask, (0.25, 0.65, 1.0), 4840, 1760)
    debug_distance_col = debug_color(near_weight, (0.25, 1.0, 0.45), 4840, 1860)
    debug_wonder_col = debug_color(wonder_mask, (1.0, 0.25, 0.75), 4840, 1960)
    lib.connect_static_switch(debug_wonder, debug_wonder_col, far_col)
    debug_col = debug_wonder
    lib.connect_static_switch(debug_distance, debug_distance_col, debug_col)
    debug_col = debug_distance
    lib.connect_static_switch(debug_slope, debug_slope_col, debug_col)
    debug_col = debug_slope
    lib.connect_static_switch(debug_path, debug_path_col, debug_col)
    debug_col = debug_path
    lib.connect_static_switch(debug_height, debug_height_col, debug_col)
    debug_col = debug_height
    lib.connect_static_switch(debug_masks, debug_weights_col, debug_col)
    nikki_col = debug_masks

    proc_rough = proc_lerp3(rock_rough, grass_rough, mud_rough, 900, 960)
    rough_blend = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 1100, 960)
    lib.connect(proc_rough, "", rough_blend, "A")
    lib.connect(paint_rough, "", rough_blend, "B")
    lib.connect(has_paint, "", rough_blend, "Alpha")
    rough_out = painted_sw(m, 1280, 960, rough_blend, proc_rough)
    path_rough_blend = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 1460, 960)
    lib.connect(rough_out, "", path_rough_blend, "A")
    lib.connect(path_rough_pbr, "", path_rough_blend, "B")
    lib.connect(path_fac, "", path_rough_blend, "Alpha")
    rough_out = path_rough_blend
    shore_wet = lib.create_expression(m, unreal.MaterialExpressionMultiply, 1460, 1040)
    lib.connect(shore_mask, "", shore_wet, "A")
    lib.connect(shore_wet_boost, "", shore_wet, "B")
    total_wet = lib.create_expression(m, unreal.MaterialExpressionAdd, 1640, 1000)
    lib.connect(wetness, "", total_wet, "A")
    lib.connect(shore_wet, "", total_wet, "B")
    wet_sat = lib.create_expression(m, unreal.MaterialExpressionSaturate, 1820, 1000)
    lib.connect(total_wet, "", wet_sat, "Input")
    rough_wet = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 2000, 960)
    lib.connect(rough_out, "", rough_wet, "A")
    lib.connect(wet_rough, "", rough_wet, "B")
    lib.connect(wet_sat, "", rough_wet, "Alpha")
    rough_final = rough_wet
    path_edge_rough = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, 2180, 1040)
    lib.connect(rough_final, "", path_edge_rough, "A")
    path_edge_target = lib.create_expression(m, unreal.MaterialExpressionConstant, 2000, 1120)
    path_edge_target.set_editor_property("r", 0.64)
    lib.connect(path_edge_target, "", path_edge_rough, "B")
    lib.connect(path_edge, "", path_edge_rough, "Alpha")
    rough_final = path_edge_rough
    itto_rough_add = lib.create_expression(m, unreal.MaterialExpressionAdd, px + 3000, py + 7880)
    lib.connect(rough_final, "", itto_rough_add, "A")
    lib.connect(itto_bu, "", itto_rough_add, "B")
    rough_final = itto_rough_add

    toon = lib.create_expression(m, unreal.MaterialExpressionSubstrateToonBSDF, 3000, 700)
    lib.try_set_editor_property(toon, "toon_profile", profiles["TP_Default"])
    lib.connect_toon_pin(toon, nikki_col, ("BaseColor", "DiffuseColor"))
    lib.connect_toon_pin(toon, rough_final, ("Roughness",))
    lib.connect_toon_pin(toon, nrm_final, ("Normal",))
    lib.connect_front_material(m, toon)

    grass_out_cls = getattr(unreal, "MaterialExpressionLandscapeGrassOutput", None)
    if grass_out_cls:
        grass_vis = lib.create_expression(m, unreal.MaterialExpressionMultiply, 2800, 1100)
        lib.connect(layer_samples["Grass"]["color"], "", grass_vis, "A")
        lib.connect(grass_final, "", grass_vis, "B")
        gout = lib.create_expression(m, grass_out_cls, 3000, 1100)
        for pin in ("Grass", "Input", "Color"):
            if lib.connect(grass_vis, "", gout, pin):
                break

    unreal.MaterialEditingLibrary.recompile_material(m)
    lib.save_package(m)

    for spec in INSTANCES:
        mi = lib.create_material_instance(spec["name"], INST_DIR, path)
        if spec.get("profile") in profiles:
            lib.set_instance_toon_profile(mi, profiles[spec["profile"]])
        for n, v in spec.get("vectors", {}).items():
            lib.set_instance_vector(mi, n, v)
        for n, v in spec.get("scalars", {}).items():
            lib.set_instance_scalar(mi, n, v)
        for n, v in spec.get("switches", {}).items():
            lib.set_instance_static_switch(mi, n, bool(v))
        lib.save_package(mi)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": path,
        "instances": [s["name"] for s in INSTANCES],
        "count": len(INSTANCES),
        "folder": INST_DIR,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"LANDSCAPE_HB_OK {path} instances={len(INSTANCES)} -> {REPORT}")
    return path


def main():
    try:
        import unreal  # noqa: F401
        build()
        return 0
    except ImportError:
        import subprocess

        root = Path(__file__).resolve().parents[2]
        ue = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
        if not ue.exists():
            print(f"ERROR: {ue}")
            return 1
        os.environ.setdefault("BS_MASTER_FORCE", "1")
        cmd = [
            str(ue), str(root / "BS_GodFile.uproject"),
            f"-ExecutePythonScript={(root / 'Content/Python/setup_landscape_height_blend.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi",
            "-DisablePlugins=Monolith",
            f"-log={root / 'Saved/Logs/setup_landscape_height_blend.log'}",
        ]
        return subprocess.run(cmd, cwd=str(root)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
