"""Author the Gemstone Master Material (M_Master_Gemstone) with Nikki MFs and Creative Trees.

Architectural Contract (Melodia AAA Standard):
  1. Shading Model: Unreal Engine 5.8 Substrate (SubstrateToonBSDF / FrontMaterial).
  2. Modular Material Function (MF_) paradigm with strictly clamped parameters,
     grouped neatly for Material Instance editing, with neutral defaults (0 = bypass).
  3. Nikki MFs Integrated:
     - MF_NikkiTwinkleIris  (iridescent twinkle + pastel sheen)
     - MF_NikkiPastelGrade  (kawaii pastel grade + sakura lift + dream bloom)
     - MF_NikkiStickerShade (sticker / anime-cel stepped quantization)
     - MF_NikkiSparkle      (view-dependent star sparkle glints)
  4. Creative Node Trees:
     - MF_GemstoneInternalFacet (3-slice Voronoi crystal facet parallax refraction)
     - MF_GemstoneDispersion    (physical Abbe chromatic wavelength splitting / diamond fire)
     - MF_GemstoneAbsorption    (Beer-Lambert volumetric depth extinction)
     - MF_GemstoneCymatics      (Chladni nodal standing wave harmonic lattice)
     - Temporal Stylization     (MF_WaterTemporalStyle_v7 quantized 12/24fps stepping + MPC pulse)
  5. Audio Parameter Bus:
     - MPC_Melodia_Palette (BeatPulse, BeatPhase, Mid, GlobalReactivity)

Run inside UE Editor via Monolith (editor_query:run_python):
  import author_gemstone_master
  import importlib
  importlib.reload(author_gemstone_master)
  author_gemstone_master.build_all()
"""
from __future__ import annotations

import unreal

MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
FUNCTION_DIR = "/Game/EnvSandbox/Materials/Functions"
SCRATCH_DIR = "/Game/EnvSandbox/Materials/_Scratch"
INSTANCES_DIR = "/Game/EnvSandbox/Materials/Instances/Gemstone"
MPC_PALETTE = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
MPC_CYMATICS = "/Game/Melodia/Cymatics/MPC_Cymatics_Driver"

TAG = "GemX:"


def _get(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _set(obj, name, value):
    obj.set_editor_property(name, value)


def _log(msg: str):
    unreal.log(f"[Gemstone Master] {msg}")


def _exprs(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def _fexprs(function):
    return list(unreal.MaterialEditingLibrary.get_material_function_expressions(function) or [])


def _find_tag(exprs, key):
    wanted = TAG + key
    for e in exprs:
        if str(_get(e, "desc", "")) == wanted:
            return e
    return None


def _mk_node(material, cls, key, x, y):
    node = _find_tag(_exprs(material), key)
    if node:
        return node, False
    node = unreal.MaterialEditingLibrary.create_material_expression(material, cls, x, y)
    _set(node, "desc", TAG + key)
    return node, True


def _mk_fnode(function, cls, key, x, y):
    node = _find_tag(_fexprs(function), key)
    if node:
        return node, False
    node = unreal.MaterialEditingLibrary.create_material_expression_in_function(function, cls, x, y)
    _set(node, "desc", TAG + key)
    return node, True


def _connect(source, output_name, target, input_name):
    if not unreal.MaterialEditingLibrary.connect_material_expressions(source, output_name, target, input_name):
        raise RuntimeError(f"Connection failed: {source.get_name()}:{output_name} -> {target.get_name()}:{input_name}")


def _scalar_param(material, name, default, group, x, y, smin=0.0, smax=1.0, key=None):
    node, _ = _mk_node(material, unreal.MaterialExpressionScalarParameter, key or name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", float(default))
    if smin is not None:
        _set(node, "slider_min", float(smin))
    if smax is not None:
        _set(node, "slider_max", float(smax))
    return node


def _vector_param(material, name, rgba, group, x, y, key=None):
    node, _ = _mk_node(material, unreal.MaterialExpressionVectorParameter, key or name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", unreal.LinearColor(*rgba))
    return node


# ─────────────────────────────────────────────────────────────────────────────
# 1. Specialized Gemstone Material Functions
# ─────────────────────────────────────────────────────────────────────────────

FACET_HLSL = r"""
// 3-slice Voronoi internal crystal facet parallax refraction
float3 V = normalize(ViewVector);
float3 N = normalize(Normal);
float eta = 1.0 / max(IOR, 1.001);
float3 R = refract(-V, N, eta);
if (dot(R, R) < 0.001) R = reflect(-V, N);

float facetAcc = 0.0;
float depthSteps = 3.0;
float totalWeight = 0.0;

for (float step = 1.0; step <= 3.0; step += 1.0)
{
    float d = (step / depthSteps) * FacetDepth;
    float2 sampleUV = UV + R.xy * d;
    float2 gv = sampleUV * max(FacetFrequency, 0.5);
    float2 cell = floor(gv);
    float2 f = frac(gv);
    
    float minDist = 8.0;
    for (int y = -1; y <= 1; y++)
    {
        for (int x = -1; x <= 1; x++)
        {
            float2 neighbor = float2(x, y);
            float2 p = cell + neighbor;
            float2 h = frac(sin(float2(dot(p, float2(127.1, 311.7)), dot(p, float2(269.5, 183.3)))) * 43758.5453);
            float2 pt = neighbor + (h - 0.5) * saturate(FacetJitter);
            float dist = length(pt - f);
            if (dist < minDist) minDist = dist;
        }
    }
    
    float mask = pow(saturate(1.0 - minDist), max(FacetSharpness, 0.5));
    float w = 1.0 / step;
    facetAcc += mask * w;
    totalWeight += w;
}

return saturate((facetAcc / max(totalWeight, 0.001)) * FacetIntensity);
"""

DISPERSION_HLSL = r"""
// Abbe wavelength splitting (diamond fire)
float3 V = normalize(ViewVector);
float3 N = normalize(Normal);
float NdotV = saturate(dot(N, V));
float grazing = pow(1.0 - NdotV, max(FresnelPower, 1.0));

float spread = max(DispersionSpread, 0.001);
float etaR = 1.0 / max(IOR - spread, 1.001);
float etaG = 1.0 / max(IOR, 1.001);
float etaB = 1.0 / max(IOR + spread, 1.001);

float3 rR = refract(-V, N, etaR);
float3 rG = refract(-V, N, etaG);
float3 rB = refract(-V, N, etaB);

float devR = saturate(dot(rR, -V));
float devG = saturate(dot(rG, -V));
float devB = saturate(dot(rB, -V));

float3 rainbow = float3(
    pow(devR, 6.0) * 1.6,
    pow(devG, 8.0) * 1.3,
    pow(devB, 10.0) * 1.9
);

float hue = frac(NdotV * 2.5 + 0.15);
float3 spec = saturate(float3(
    abs(hue * 6.0 - 3.0) - 1.0,
    2.0 - abs(hue * 6.0 - 2.0),
    2.0 - abs(hue * 6.0 - 4.0)
));

return BaseColor + (rainbow + spec * grazing) * DispersionIntensity;
"""

ABSORPTION_HLSL = r"""
// Beer-Lambert volumetric depth extinction
float3 V = normalize(ViewVector);
float3 N = normalize(Normal);
float NdotV = saturate(dot(N, V));

float pathLength = (1.0 / max(NdotV, 0.12)) * max(DepthScale, 0.1);
float3 sigma = max(1.0 - AbsorptionColor, 0.05) * max(Density, 0.0);
float3 transmittance = exp(-sigma * pathLength);

return lerp(BaseColor * AbsorptionColor * 0.35, BaseColor, transmittance);
"""

CYMATICS_HLSL = r"""
// Chladni 2D nodal standing wave interference pattern inside crystal lattice
float2 p = (UV - 0.5) * 2.0;
float r = length(p);

float n = max(HarmonicOrder, 1.0);
float m = n + 2.0;
float k = max(Frequency, 0.5) * 3.14159;

float wave1 = cos(n * k * p.x) * cos(m * k * p.y);
float wave2 = cos(m * k * p.x) * cos(n * k * p.y);
float chladni = abs(wave1 - wave2);

float nodal = smoothstep(0.14, 0.0, chladni) * (1.0 - smoothstep(0.85, 1.15, r));
return NodalTint * nodal * saturate(Strength + AudioPulse * 0.6);
"""

SPARKLE_HLSL = r"""
// Procedural 4-point diamond star sparkle glint
float mask = saturate(SparkleMask);
float thresh = clamp(SparkleThreshold, 0.05, 0.98);
float over = saturate((mask - thresh) / (1.0 - thresh));

float2 st = frac(UV * 12.0) - 0.5;
float r = length(st);
float flareX = saturate(1.0 - abs(st.x) * 18.0) * saturate(1.0 - abs(st.y) * 2.5);
float flareY = saturate(1.0 - abs(st.y) * 18.0) * saturate(1.0 - abs(st.x) * 2.5);
float star = max(flareX, flareY) + saturate(1.0 - r * 5.0) * 0.5;

float3 glint = SparkleColor * (over * over * max(SparkleIntensity, 0.0) * (0.35 + 0.65 * star));
return BaseColor + glint;
"""


def _create_custom_mf(name: str, description: str, inputs: list, hlsl: str, output_is_float: bool = False) -> unreal.MaterialFunction:
    """Create or update a Material Function with Custom HLSL expression."""
    path = f"{FUNCTION_DIR}/{name}"
    function = unreal.EditorAssetLibrary.load_asset(path)
    if function is None:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        function = tools.create_asset(name, FUNCTION_DIR, unreal.MaterialFunction, unreal.MaterialFunctionFactoryNew())
    if function is None:
        raise RuntimeError(f"Could not load or create {path}")

    unreal.MaterialEditingLibrary.delete_all_material_expressions_in_function(function)

    fn_inputs = {}
    for i, (iname, itype) in enumerate(inputs):
        node, _ = _mk_fnode(function, unreal.MaterialExpressionFunctionInput, f"In_{iname}", -1500, -500 + i * 140)
        _set(node, "input_name", iname)
        _set(node, "input_type", itype)
        _set(node, "sort_priority", i)
        fn_inputs[iname] = node

    custom, _ = _mk_fnode(function, unreal.MaterialExpressionCustom, "CustomNode", -500, 0)
    _set(custom, "description", description)
    _set(custom, "code", hlsl)
    out_type = unreal.CustomMaterialOutputType.CMOT_FLOAT1 if output_is_float else unreal.CustomMaterialOutputType.CMOT_FLOAT3
    _set(custom, "output_type", out_type)

    ci_list = []
    for iname, _ in inputs:
        c = unreal.CustomInput()
        _set(c, "input_name", iname)
        ci_list.append(c)
    _set(custom, "inputs", ci_list)

    for iname in fn_inputs:
        _connect(fn_inputs[iname], "", custom, iname)

    out, _ = _mk_fnode(function, unreal.MaterialExpressionFunctionOutput, "OutputNode", 300, 0)
    _set(out, "output_name", "Result" if output_is_float or name != "MF_NikkiSparkle" else "Color")
    _connect(custom, "", out, "")

    unreal.MaterialEditingLibrary.update_material_function(function)
    unreal.EditorAssetLibrary.save_loaded_asset(function)
    _log(f"Compiled and saved {name}")
    return function


def build_gemstone_material_functions() -> dict:
    f3 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3
    f2 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR2
    f1 = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR

    facets = _create_custom_mf(
        "MF_GemstoneInternalFacet",
        "3-slice Voronoi internal crystal facet parallax refraction",
        [
            ("UV", f2),
            ("Normal", f3),
            ("ViewVector", f3),
            ("FacetDepth", f1),
            ("FacetFrequency", f1),
            ("FacetSharpness", f1),
            ("FacetJitter", f1),
            ("FacetIntensity", f1),
            ("IOR", f1),
        ],
        FACET_HLSL,
        output_is_float=True,
    )

    dispersion = _create_custom_mf(
        "MF_GemstoneDispersion",
        "Physical Abbe wavelength dispersion splitting (diamond fire)",
        [
            ("Normal", f3),
            ("ViewVector", f3),
            ("BaseColor", f3),
            ("IOR", f1),
            ("DispersionSpread", f1),
            ("DispersionIntensity", f1),
            ("FresnelPower", f1),
        ],
        DISPERSION_HLSL,
        output_is_float=False,
    )

    absorption = _create_custom_mf(
        "MF_GemstoneAbsorption",
        "Beer-Lambert volumetric depth extinction for gemstone body color",
        [
            ("BaseColor", f3),
            ("AbsorptionColor", f3),
            ("Density", f1),
            ("DepthScale", f1),
            ("Normal", f3),
            ("ViewVector", f3),
        ],
        ABSORPTION_HLSL,
        output_is_float=False,
    )

    cymatics = _create_custom_mf(
        "MF_GemstoneCymatics",
        "Chladni 2D nodal standing wave interference pattern in crystal lattice",
        [
            ("UV", f2),
            ("Frequency", f1),
            ("HarmonicOrder", f1),
            ("AudioPulse", f1),
            ("Strength", f1),
            ("NodalTint", f3),
        ],
        CYMATICS_HLSL,
        output_is_float=False,
    )

    # Ensure MF_NikkiSparkle is also repaired and up-to-date
    sparkle = _create_custom_mf(
        "MF_NikkiSparkle",
        "Nikki procedural 4-point star sparkle glint",
        [
            ("BaseColor", f3),
            ("UV", f2),
            ("SparkleMask", f1),
            ("SparkleIntensity", f1),
            ("SparkleThreshold", f1),
            ("SparkleColor", f3),
        ],
        SPARKLE_HLSL,
        output_is_float=False,
    )

    return {
        "facets": facets,
        "dispersion": dispersion,
        "absorption": absorption,
        "cymatics": cymatics,
        "sparkle": sparkle,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Master Material: M_Master_Gemstone
# ─────────────────────────────────────────────────────────────────────────────

def build_gemstone_master(functions: dict) -> unreal.Material:
    """Build M_Master_Gemstone under /Game/EnvSandbox/Materials/Masters/."""
    full_path = f"{MASTER_DIR}/M_Master_Gemstone"
    material = unreal.EditorAssetLibrary.load_asset(full_path)
    if material is None:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        material = tools.create_asset("M_Master_Gemstone", MASTER_DIR, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Failed to create asset at {full_path}")

    MEL = unreal.MaterialEditingLibrary
    MEL.delete_all_material_expressions(material)

    # ── Geometry & View Vectors ──
    wp, _ = _mk_node(material, unreal.MaterialExpressionWorldPosition, "WorldPos", -4200, 200)
    vn, _ = _mk_node(material, unreal.MaterialExpressionVertexNormalWS, "VertexNorm", -4200, 360)
    cam_v, _ = _mk_node(material, unreal.MaterialExpressionCameraVectorWS, "CamVec", -4200, 520)
    uv_coord, _ = _mk_node(material, unreal.MaterialExpressionTextureCoordinate, "TexCoord", -4200, 680)

    # ── MPC Audio Bus ──
    mpc_palette_asset = unreal.EditorAssetLibrary.load_asset(MPC_PALETTE)
    beat_pulse, _ = _mk_node(material, unreal.MaterialExpressionCollectionParameter, "MPC_BeatPulse", -4200, 900)
    if mpc_palette_asset:
        _set(beat_pulse, "collection", mpc_palette_asset)
        _set(beat_pulse, "parameter_name", "BeatPulse")

    beat_phase, _ = _mk_node(material, unreal.MaterialExpressionCollectionParameter, "MPC_BeatPhase", -4200, 1060)
    if mpc_palette_asset:
        _set(beat_phase, "collection", mpc_palette_asset)
        _set(beat_phase, "parameter_name", "BeatPhase")

    # ── Column 01 | Base & Optical ──
    g_base = "01 | Base & Optical"
    base_tint = _vector_param(material, "BaseTint", (0.85, 0.94, 1.0, 1.0), g_base, -3800, -600)
    base_ior = _scalar_param(material, "GemIndexRefraction", 1.77, g_base, -3800, -420, 1.3, 2.8)
    base_rough = _scalar_param(material, "Roughness", 0.02, g_base, -3800, -280, 0.001, 1.0)
    base_metal = _scalar_param(material, "Metallic", 0.0, g_base, -3800, -140, 0.0, 1.0)
    norm_strength = _scalar_param(material, "NormalStrength", 1.0, g_base, -3800, 0, 0.0, 2.0)

    norm_tex, _ = _mk_node(material, unreal.MaterialExpressionTextureSampleParameter2D, "NormalMap", -3800, 160)
    _set(norm_tex, "parameter_name", "NormalMap")
    _set(norm_tex, "group", g_base)
    neutral_norm = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Textures/Utility/T_Neutral_Normal")
    if neutral_norm:
        _set(norm_tex, "texture", neutral_norm)

    fnorm, _ = _mk_node(material, unreal.MaterialExpressionLinearInterpolate, "NormalFlatten", -3400, 160)
    neutral_flat, _ = _mk_node(material, unreal.MaterialExpressionConstant3Vector, "FlatNormV", -3600, 320)
    _set(neutral_flat, "constant", unreal.LinearColor(0, 0, 1, 0))
    _connect(neutral_flat, "", fnorm, "A")
    _connect(norm_tex, "RGB", fnorm, "B")
    _connect(norm_strength, "", fnorm, "Alpha")

    # Current working color
    curr_color = base_tint

    # ── Column 02 | Temporal Stylization ──
    g_temporal = "02 | Temporal Stylization"
    t_rate = _scalar_param(material, "TemporalFrameRate", 24.0, g_temporal, -3800, 1040, 6.0, 60.0)
    t_blend = _scalar_param(material, "TemporalBlend", 0.15, g_temporal, -3800, 1180, 0.0, 1.0)
    t_raw, _ = _mk_node(material, unreal.MaterialExpressionTime, "RawTime", -3800, 1320)

    t_fn = unreal.EditorAssetLibrary.load_asset(f"{FUNCTION_DIR}/MF_WaterTemporalStyle_v7")
    t_call, _ = _mk_node(material, unreal.MaterialExpressionMaterialFunctionCall, "TemporalCall", -3400, 1000)
    if t_fn:
        _set(t_call, "material_function", t_fn)
        _connect(t_raw, "", t_call, "Time")
        _connect(t_rate, "", t_call, "TemporalRate")
        _connect(t_blend, "", t_call, "TemporalBlend")

    stylized_time, _ = _mk_node(material, unreal.MaterialExpressionStaticSwitchParameter, "TemporalSwitch", -3100, 1000)
    _set(stylized_time, "parameter_name", "bTemporalStylize_Active")
    _set(stylized_time, "group", g_temporal)
    _set(stylized_time, "default_value", True)
    _connect(t_call, "StylizedTime", stylized_time, "True")
    _connect(t_raw, "", stylized_time, "False")

    # ── Column 03 | Volumetric Absorption (Beer-Lambert) ──
    g_abs = "03 | Volumetric Absorption"
    abs_color = _vector_param(material, "AbsorptionColor", (0.12, 0.48, 0.82, 1.0), g_abs, -3000, -440)
    abs_density = _scalar_param(material, "AbsorptionDensity", 2.2, g_abs, -3000, -280, 0.0, 10.0)
    abs_depth = _scalar_param(material, "AbsorptionDepthScale", 1.0, g_abs, -3000, -140, 0.1, 5.0)

    abs_call, _ = _mk_node(material, unreal.MaterialExpressionMaterialFunctionCall, "AbsorptionCall", -2600, -400)
    _set(abs_call, "material_function", functions["absorption"])
    _connect(curr_color, "", abs_call, "BaseColor")
    _connect(abs_color, "", abs_call, "AbsorptionColor")
    _connect(abs_density, "", abs_call, "Density")
    _connect(abs_depth, "", abs_call, "DepthScale")
    _connect(fnorm, "", abs_call, "Normal")
    _connect(cam_v, "", abs_call, "ViewVector")

    abs_out, _ = _mk_node(material, unreal.MaterialExpressionStaticSwitchParameter, "AbsorptionGate", -2300, -400)
    _set(abs_out, "parameter_name", "bAbsorption_Active")
    _set(abs_out, "group", g_abs)
    _set(abs_out, "default_value", True)
    _connect(abs_call, "Result", abs_out, "True")
    _connect(curr_color, "", abs_out, "False")
    curr_color = abs_out

    # ── Column 04 | Internal Facet Parallax ──
    g_facet = "04 | Internal Facets"
    facet_depth = _scalar_param(material, "FacetDepth", 0.45, g_facet, -2600, 340, 0.0, 2.0)
    facet_freq = _scalar_param(material, "FacetFrequency", 4.0, g_facet, -2600, 480, 1.0, 16.0)
    facet_sharp = _scalar_param(material, "FacetSharpness", 3.5, g_facet, -2600, 620, 1.0, 10.0)
    facet_jitter = _scalar_param(material, "FacetJitter", 0.35, g_facet, -2600, 760, 0.0, 1.0)
    facet_intens = _scalar_param(material, "FacetIntensity", 0.8, g_facet, -2600, 900, 0.0, 2.0)

    facet_call, _ = _mk_node(material, unreal.MaterialExpressionMaterialFunctionCall, "FacetCall", -2200, 400)
    _set(facet_call, "material_function", functions["facets"])
    _connect(uv_coord, "", facet_call, "UV")
    _connect(fnorm, "", facet_call, "Normal")
    _connect(cam_v, "", facet_call, "ViewVector")
    _connect(facet_depth, "", facet_call, "FacetDepth")
    _connect(facet_freq, "", facet_call, "FacetFrequency")
    _connect(facet_sharp, "", facet_call, "FacetSharpness")
    _connect(facet_jitter, "", facet_call, "FacetJitter")
    _connect(facet_intens, "", facet_call, "FacetIntensity")
    _connect(base_ior, "", facet_call, "IOR")

    facet_tint, _ = _mk_node(material, unreal.MaterialExpressionMultiply, "FacetColorMod", -1800, 200)
    _connect(curr_color, "", facet_tint, "A")
    _connect(facet_call, "Result", facet_tint, "B")

    facet_add, _ = _mk_node(material, unreal.MaterialExpressionAdd, "FacetColorAdd", -1600, 100)
    _connect(curr_color, "", facet_add, "A")
    _connect(facet_tint, "", facet_add, "B")

    facet_out, _ = _mk_node(material, unreal.MaterialExpressionStaticSwitchParameter, "FacetGate", -1400, 100)
    _set(facet_out, "parameter_name", "bInternalFacets_Active")
    _set(facet_out, "group", g_facet)
    _set(facet_out, "default_value", True)
    _connect(facet_add, "", facet_out, "True")
    _connect(curr_color, "", facet_out, "False")
    curr_color = facet_out

    # ── Column 05 | Abbe Chromatic Dispersion (Diamond Fire) ──
    g_disp = "05 | Abbe Dispersion"
    disp_spread = _scalar_param(material, "DispersionSpread", 0.045, g_disp, -1800, -460, 0.0, 0.2)
    disp_intens = _scalar_param(material, "DispersionIntensity", 0.85, g_disp, -1800, -320, 0.0, 3.0)
    disp_power = _scalar_param(material, "DispersionFresnelPower", 3.0, g_disp, -1800, -180, 1.0, 8.0)

    disp_call, _ = _mk_node(material, unreal.MaterialExpressionMaterialFunctionCall, "DispersionCall", -1400, -400)
    _set(disp_call, "material_function", functions["dispersion"])
    _connect(fnorm, "", disp_call, "Normal")
    _connect(cam_v, "", disp_call, "ViewVector")
    _connect(curr_color, "", disp_call, "BaseColor")
    _connect(base_ior, "", disp_call, "IOR")
    _connect(disp_spread, "", disp_call, "DispersionSpread")
    _connect(disp_intens, "", disp_call, "DispersionIntensity")
    _connect(disp_power, "", disp_call, "FresnelPower")

    disp_out, _ = _mk_node(material, unreal.MaterialExpressionStaticSwitchParameter, "DispersionGate", -1100, -400)
    _set(disp_out, "parameter_name", "bDispersion_Active")
    _set(disp_out, "group", g_disp)
    _set(disp_out, "default_value", True)
    _connect(disp_call, "Result", disp_out, "True")
    _connect(curr_color, "", disp_out, "False")
    curr_color = disp_out

    # ── Column 06 | Nikki Twinkle Iris (Iridescence & Pastel Sheen) ──
    g_iris = "06 | Nikki Iridescence"
    iris_sheen = _scalar_param(material, "NikkiFabricSheen", 0.45, g_iris, -1000, 340, 0.0, 1.0)
    iris_irid = _scalar_param(material, "NikkiIridescence", 2.5, g_iris, -1000, 480, 0.0, 8.0)
    iris_scale = _scalar_param(material, "NikkiTwinkleScale", 1.2, g_iris, -1000, 620, 0.01, 8.0)
    iris_amount = _scalar_param(material, "NikkiTwinkleAmount", 0.25, g_iris, -1000, 760, 0.0, 1.0)
    iris_tint = _vector_param(material, "NikkiIrisTint", (0.9, 0.95, 1.0, 1.0), g_iris, -1000, 900)

    twinkle_fn = unreal.EditorAssetLibrary.load_asset(f"{FUNCTION_DIR}/MF_NikkiTwinkleIris")
    iris_call, _ = _mk_node(material, unreal.MaterialExpressionMaterialFunctionCall, "TwinkleIrisCall", -650, 400)
    if twinkle_fn:
        _set(iris_call, "material_function", twinkle_fn)
        _connect(curr_color, "", iris_call, "BaseColor")
        _connect(fnorm, "", iris_call, "Normal")
        _connect(wp, "", iris_call, "WorldPosition")
        _connect(iris_sheen, "", iris_call, "Sheen")
        _connect(iris_irid, "", iris_call, "Iridescence")
        _connect(iris_scale, "", iris_call, "TwinkleScale")
        _connect(iris_amount, "", iris_call, "TwinkleAmount")
        _connect(iris_tint, "", iris_call, "Tint")

    iris_out, _ = _mk_node(material, unreal.MaterialExpressionStaticSwitchParameter, "TwinkleIrisGate", -350, 200)
    _set(iris_out, "parameter_name", "bNikkiTwinkleIris_Active")
    _set(iris_out, "group", g_iris)
    _set(iris_out, "default_value", True)
    _connect(iris_call, "Color", iris_out, "True")
    _connect(curr_color, "", iris_out, "False")
    curr_color = iris_out

    # ── Column 07 | Nikki Pastel Grade ──
    g_pastel = "07 | Nikki Pastel Grade"
    pas_str = _scalar_param(material, "NikkiPastelStrength", 0.4, g_pastel, -300, -460, 0.0, 1.0)
    pas_lift = _scalar_param(material, "NikkiPastelLift", 0.08, g_pastel, -300, -320, 0.0, 0.5)
    pas_mid = _scalar_param(material, "NikkiPastelPosMid", 0.5, g_pastel, -300, -180, 0.05, 0.95)
    pas_bloom = _scalar_param(material, "NikkiPastelBloom", 0.2, g_pastel, -300, -40, 0.0, 1.0)
    pas_low = _vector_param(material, "NikkiPastelRampLow", (0.75, 0.85, 0.95, 1.0), g_pastel, -300, 100)
    pas_mcol = _vector_param(material, "NikkiPastelRampMid", (0.92, 0.96, 1.0, 1.0), g_pastel, -300, 240)
    pas_high = _vector_param(material, "NikkiPastelRampHigh", (1.0, 1.0, 1.0, 1.0), g_pastel, -300, 380)

    lum_w, _ = _mk_node(material, unreal.MaterialExpressionConstant3Vector, "PastelLumW", -300, 520)
    _set(lum_w, "constant", unreal.LinearColor(0.299, 0.587, 0.114, 0))
    lum_dot, _ = _mk_node(material, unreal.MaterialExpressionDotProduct, "PastelLumDot", -100, 520)
    _connect(curr_color, "", lum_dot, "A")
    _connect(lum_w, "", lum_dot, "B")

    pastel_fn = unreal.EditorAssetLibrary.load_asset(f"{FUNCTION_DIR}/MF_NikkiPastelGrade")
    pas_call, _ = _mk_node(material, unreal.MaterialExpressionMaterialFunctionCall, "PastelGradeCall", 100, -200)
    if pastel_fn:
        _set(pas_call, "material_function", pastel_fn)
        _connect(curr_color, "", pas_call, "BaseColor")
        _connect(lum_dot, "", pas_call, "Mask")
        _connect(pas_low, "", pas_call, "RampLow")
        _connect(pas_mcol, "", pas_call, "RampMid")
        _connect(pas_high, "", pas_call, "RampHigh")
        _connect(pas_mid, "", pas_call, "RampPosMid")
        _connect(pas_str, "", pas_call, "Strength")
        _connect(pas_lift, "", pas_call, "PastelLift")
        _connect(pas_bloom, "", pas_call, "Bloom")

    pas_out, _ = _mk_node(material, unreal.MaterialExpressionStaticSwitchParameter, "PastelGradeGate", 400, -200)
    _set(pas_out, "parameter_name", "bNikkiPastelGrade_Active")
    _set(pas_out, "group", g_pastel)
    _set(pas_out, "default_value", True)
    _connect(pas_call, "Color", pas_out, "True")
    _connect(curr_color, "", pas_out, "False")
    curr_color = pas_out

    # ── Column 08 | Nikki Sticker / Anime Cel Shading ──
    g_sticker = "08 | Nikki Sticker Shade"
    stk_bands = _scalar_param(material, "NikkiStickerBandCount", 4.0, g_sticker, 400, 340, 1.0, 8.0)
    stk_soft = _scalar_param(material, "NikkiStickerBandSoftness", 0.85, g_sticker, 400, 480, 0.0, 1.0)
    stk_str = _scalar_param(material, "NikkiStickerStrength", 0.35, g_sticker, 400, 620, 0.0, 1.0)
    stk_col = _vector_param(material, "NikkiStickerShadeColor", (0.65, 0.72, 0.88, 1.0), g_sticker, 400, 760)

    sticker_fn = unreal.EditorAssetLibrary.load_asset(f"{FUNCTION_DIR}/MF_NikkiStickerShade")
    stk_call, _ = _mk_node(material, unreal.MaterialExpressionMaterialFunctionCall, "StickerShadeCall", 700, 300)
    if sticker_fn:
        _set(stk_call, "material_function", sticker_fn)
        _connect(curr_color, "", stk_call, "BaseColor")
        _connect(lum_dot, "", stk_call, "Mask")
        _connect(stk_bands, "", stk_call, "BandCount")
        _connect(stk_soft, "", stk_call, "BandSoftness")
        _connect(stk_col, "", stk_call, "ShadeColor")
        _connect(stk_str, "", stk_call, "Strength")

    stk_out, _ = _mk_node(material, unreal.MaterialExpressionStaticSwitchParameter, "StickerShadeGate", 1000, 200)
    _set(stk_out, "parameter_name", "bNikkiStickerShade_Active")
    _set(stk_out, "group", g_sticker)
    _set(stk_out, "default_value", False)
    _connect(stk_call, "Color", stk_out, "True")
    _connect(curr_color, "", stk_out, "False")
    curr_color = stk_out

    # ── Column 09 | Star Sparkle Glint ──
    g_sparkle = "09 | Star Sparkle Glint"
    spk_intens = _scalar_param(material, "SparkleIntensity", 1.8, g_sparkle, 1000, -460, 0.0, 5.0)
    spk_thresh = _scalar_param(material, "SparkleThreshold", 0.82, g_sparkle, 1000, -320, 0.1, 1.0)
    spk_color = _vector_param(material, "SparkleColor", (1.0, 1.0, 1.0, 1.0), g_sparkle, 1000, -180)

    spk_mask, _ = _mk_node(material, unreal.MaterialExpressionDotProduct, "SparkleMaskDot", 1000, -40)
    _connect(fnorm, "", spk_mask, "A")
    _connect(cam_v, "", spk_mask, "B")

    spk_call, _ = _mk_node(material, unreal.MaterialExpressionMaterialFunctionCall, "SparkleCall", 1300, -300)
    _set(spk_call, "material_function", functions["sparkle"])
    _connect(curr_color, "", spk_call, "BaseColor")
    _connect(uv_coord, "", spk_call, "UV")
    _connect(spk_mask, "", spk_call, "SparkleMask")
    _connect(spk_intens, "", spk_call, "SparkleIntensity")
    _connect(spk_thresh, "", spk_call, "SparkleThreshold")
    _connect(spk_color, "", spk_call, "SparkleColor")

    spk_out, _ = _mk_node(material, unreal.MaterialExpressionStaticSwitchParameter, "SparkleGate", 1600, -300)
    _set(spk_out, "parameter_name", "bNikkiSparkle_Active")
    _set(spk_out, "group", g_sparkle)
    _set(spk_out, "default_value", True)
    _connect(spk_call, "Color", spk_out, "True")
    _connect(curr_color, "", spk_out, "False")
    curr_color = spk_out

    # ── Column 10 | Cymatics Nodal Resonance & Emissive ──
    g_cym = "10 | Cymatics & Emissive"
    cym_freq = _scalar_param(material, "CymaticsFrequency", 6.0, g_cym, 1300, 540, 1.0, 32.0)
    cym_order = _scalar_param(material, "CymaticsHarmonicOrder", 4.0, g_cym, 1300, 680, 1.0, 8.0)
    cym_str = _scalar_param(material, "CymaticsStrength", 0.3, g_cym, 1300, 820, 0.0, 1.0)
    cym_tint = _vector_param(material, "CymaticsNodalTint", (0.6, 0.9, 1.0, 1.0), g_cym, 1300, 960)

    cym_call, _ = _mk_node(material, unreal.MaterialExpressionMaterialFunctionCall, "CymaticsCall", 1600, 600)
    _set(cym_call, "material_function", functions["cymatics"])
    _connect(uv_coord, "", cym_call, "UV")
    _connect(cym_freq, "", cym_call, "Frequency")
    _connect(cym_order, "", cym_call, "HarmonicOrder")
    _connect(beat_pulse, "", cym_call, "AudioPulse")
    _connect(cym_str, "", cym_call, "Strength")
    _connect(cym_tint, "", cym_call, "NodalTint")

    cym_zero, _ = _mk_node(material, unreal.MaterialExpressionConstant3Vector, "CymZero", 1600, 840)
    _set(cym_zero, "constant", unreal.LinearColor(0, 0, 0, 0))

    cym_out, _ = _mk_node(material, unreal.MaterialExpressionStaticSwitchParameter, "CymaticsGate", 1900, 600)
    _set(cym_out, "parameter_name", "bCymatics_Active")
    _set(cym_out, "group", g_cym)
    _set(cym_out, "default_value", True)
    _connect(cym_call, "Result", cym_out, "True")
    _connect(cym_zero, "", cym_out, "False")

    emiss_floor = _scalar_param(material, "EmissiveFloor", 0.05, g_cym, 1600, 200, 0.0, 1.0)
    emiss_floor_mul, _ = _mk_node(material, unreal.MaterialExpressionMultiply, "EmissiveFloorMul", 1900, 100)
    _connect(curr_color, "", emiss_floor_mul, "A")
    _connect(emiss_floor, "", emiss_floor_mul, "B")

    emiss_add, _ = _mk_node(material, unreal.MaterialExpressionAdd, "EmissiveCombine", 2200, 200)
    _connect(emiss_floor_mul, "", emiss_add, "A")
    _connect(cym_out, "", emiss_add, "B")

    # ── Final Substrate Toon BSDF Integration ──
    bsdf, _ = _mk_node(material, unreal.MaterialExpressionSubstrateToonBSDF, "SubstrateToonBSDF", 2600, 0)
    _connect(curr_color, "", bsdf, "BaseColor")
    _connect(base_metal, "", bsdf, "Metallic")
    _connect(base_rough, "", bsdf, "Roughness")
    _connect(fnorm, "", bsdf, "Normal")
    _connect(emiss_add, "", bsdf, "EmissiveColor")

    # Connect to Root FrontMaterial
    MEL.connect_material_property(bsdf, "", unreal.MaterialProperty.MP_FRONT_MATERIAL)

    MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    _log(f"Successfully compiled and saved {full_path}")
    return material


# ─────────────────────────────────────────────────────────────────────────────
# 3. Derive Hero Gemstone Material Instances
# ─────────────────────────────────────────────────────────────────────────────

def create_gemstone_instances(master_material: unreal.Material) -> list:
    """Create curated Material Instances for Melusina regalia and portfolio lookdev."""
    instances_def = [
        {
            "name": "MI_Gemstone_Aquamarine_Circlet",
            "scalars": {
                "GemIndexRefraction": 1.58,
                "Roughness": 0.018,
                "FacetDepth": 0.55,
                "FacetFrequency": 5.0,
                "FacetSharpness": 4.0,
                "DispersionSpread": 0.038,
                "DispersionIntensity": 0.9,
                "AbsorptionDensity": 2.5,
                "NikkiFabricSheen": 0.55,
                "NikkiIridescence": 3.0,
                "SparkleIntensity": 2.2,
                "EmissiveFloor": 0.08,
            },
            "vectors": {
                "BaseTint": (0.82, 0.96, 1.0, 1.0),
                "AbsorptionColor": (0.08, 0.55, 0.85, 1.0),
                "NikkiIrisTint": (0.85, 0.98, 1.0, 1.0),
                "CymaticsNodalTint": (0.5, 0.95, 1.0, 1.0),
            },
        },
        {
            "name": "MI_Gemstone_VoidOrchid_Earrings",
            "scalars": {
                "GemIndexRefraction": 1.77,
                "Roughness": 0.022,
                "FacetDepth": 0.65,
                "FacetFrequency": 6.0,
                "FacetSharpness": 3.8,
                "DispersionSpread": 0.052,
                "DispersionIntensity": 1.1,
                "AbsorptionDensity": 3.2,
                "NikkiFabricSheen": 0.6,
                "NikkiIridescence": 3.5,
                "SparkleIntensity": 2.5,
                "EmissiveFloor": 0.12,
            },
            "vectors": {
                "BaseTint": (0.92, 0.82, 1.0, 1.0),
                "AbsorptionColor": (0.35, 0.12, 0.65, 1.0),
                "NikkiIrisTint": (1.0, 0.85, 0.95, 1.0),
                "CymaticsNodalTint": (0.85, 0.6, 1.0, 1.0),
            },
        },
        {
            "name": "MI_Gemstone_CelestialDiamond",
            "scalars": {
                "GemIndexRefraction": 2.42,
                "Roughness": 0.012,
                "FacetDepth": 0.75,
                "FacetFrequency": 8.0,
                "FacetSharpness": 5.0,
                "DispersionSpread": 0.075,
                "DispersionIntensity": 1.8,
                "AbsorptionDensity": 0.6,
                "NikkiFabricSheen": 0.4,
                "NikkiIridescence": 4.5,
                "SparkleIntensity": 3.0,
                "EmissiveFloor": 0.05,
            },
            "vectors": {
                "BaseTint": (0.98, 0.99, 1.0, 1.0),
                "AbsorptionColor": (0.85, 0.92, 1.0, 1.0),
                "NikkiIrisTint": (1.0, 1.0, 1.0, 1.0),
                "CymaticsNodalTint": (0.9, 0.95, 1.0, 1.0),
            },
        },
        {
            "name": "MI_Gemstone_RosyQuartz_Chladni",
            "scalars": {
                "GemIndexRefraction": 1.54,
                "Roughness": 0.035,
                "FacetDepth": 0.4,
                "FacetFrequency": 4.0,
                "FacetSharpness": 2.8,
                "DispersionSpread": 0.025,
                "DispersionIntensity": 0.6,
                "AbsorptionDensity": 1.8,
                "NikkiFabricSheen": 0.7,
                "NikkiIridescence": 2.0,
                "SparkleIntensity": 1.5,
                "EmissiveFloor": 0.15,
                "CymaticsStrength": 0.6,
            },
            "vectors": {
                "BaseTint": (1.0, 0.88, 0.92, 1.0),
                "AbsorptionColor": (0.95, 0.4, 0.55, 1.0),
                "NikkiIrisTint": (1.0, 0.8, 0.9, 1.0),
                "CymaticsNodalTint": (1.0, 0.75, 0.85, 1.0),
            },
        },
    ]

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    created_instances = []

    for item in instances_def:
        iname = item["name"]
        ipath = f"{INSTANCES_DIR}/{iname}"
        inst = unreal.EditorAssetLibrary.load_asset(ipath)
        if inst is None:
            inst = tools.create_asset(iname, INSTANCES_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        if inst is None:
            _log(f"Failed to create instance {iname}")
            continue

        unreal.MaterialEditingLibrary.set_material_instance_parent(inst, master_material)

        for sname, sval in item.get("scalars", {}).items():
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, sname, float(sval))

        for vname, vval in item.get("vectors", {}).items():
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(inst, vname, unreal.LinearColor(*vval))

        unreal.MaterialEditingLibrary.update_material_instance(inst)
        unreal.EditorAssetLibrary.save_loaded_asset(inst)
        _log(f"Configured and saved instance {iname}")
        created_instances.append(ipath)

    return created_instances


def build_all() -> dict:
    """Entry point: builds MFs, Master, and Instances."""
    _log("Starting Gemstone Master Authoring Pipeline...")
    functions = build_gemstone_material_functions()
    master = build_gemstone_master(functions)
    instances = create_gemstone_instances(master)
    _log(f"Authoring Complete! Master: {master.get_path_name()}, Instances: {len(instances)}")
    return {
        "master": master.get_path_name(),
        "instances": instances,
    }


if __name__ == "__main__":
    build_all()
