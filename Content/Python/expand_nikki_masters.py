"""Expand the Nikki masters into the project's proprietary fabric master.

Identity: M_Master_Nikki / M_Master_Nikki_Landscape become the kawaii fabric
master family - the ONLY materials in the project that use these three unique
functions:

  MF_NikkiPastelGrade   - cute pastel grade (lift + sakura ramp + dream bloom)
  MF_NikkiStickerShade  - sticker/anime-cel flattening for soft squishy cloth
  MF_NikkiTwinkleIris   - iridescent twinkle + pastel fabric sheen

Also promotes the masters from _Scratch to production Masters/, swaps the v1
color-only MF_Triplanar for the substance-style Pro projection (reusing
MF_Triplanar_LandscapePro - rotation/offset/axis weights/breakup, gated
default-OFF), adds the ShadowDream family (mirroring the universal master's
pattern), and tunes kawaii fabric defaults.

Every node created here is tagged ``NikkiX:`` so reruns are deterministic.

Run in the UE editor (Monolith run_python):
  import expand_nikki_masters as e; e.main()
"""
from __future__ import annotations

import unreal

FUNCTION_DIR = "/Game/EnvSandbox/Materials/Functions"
MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
SCRATCH = "/Game/EnvSandbox/Materials/_Scratch"
PRO_FN = "/Game/EnvSandbox/Materials/Functions/MF_Triplanar_LandscapePro"
TAG = "NikkiX:"


def _get(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _set(obj, name, value):
    obj.set_editor_property(name, value)


def _log(message):
    unreal.log(f"[Nikki Expand] {message}")


def _exprs(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def _fexprs(function):
    return list(unreal.MaterialEditingLibrary.get_material_function_expressions(function) or [])


def _param(material, name):
    for e in _exprs(material):
        if str(_get(e, "parameter_name", "")) == name:
            return e
    return None


def _find_tag(exprs, key):
    wanted = TAG + key
    for e in exprs:
        if str(_get(e, "desc", "")) == wanted:
            return e
    return None


def _mk_master(material, cls, key, x, y):
    node = _find_tag(_exprs(material), key)
    if node:
        return node, False
    node = unreal.MaterialEditingLibrary.create_material_expression(material, cls, x, y)
    _set(node, "desc", TAG + key)
    return node, True


def _mk_fn(function, cls, key, x, y):
    node = _find_tag(_fexprs(function), key)
    if node:
        return node, False
    node = unreal.MaterialEditingLibrary.create_material_expression_in_function(function, cls, x, y)
    _set(node, "desc", TAG + key)
    return node, True


def _connect(source, output, target, input_name):
    if not unreal.MaterialEditingLibrary.connect_material_expressions(source, output, target, input_name):
        raise RuntimeError(f"connect failed: {source.get_name()}:{output} -> {target.get_name()}:{input_name}")


def _wiring(material, expr):
    names = list(unreal.MaterialEditingLibrary.get_material_expression_input_names(expr) or [])
    inputs = list(unreal.MaterialEditingLibrary.get_inputs_for_material_expression(material, expr) or [])
    return {n: inputs[i] for i, n in enumerate(names) if i < len(inputs) and inputs[i] is not None}


def _same(a, b):
    """Name-based identity: UE Python wrappers for one native node are not `is`-equal."""
    return a is not None and b is not None and a.get_name() == b.get_name()


def _find_tintmul(material):
    for e in _exprs(material):
        if type(e).__name__ == "MaterialExpressionMultiply":
            w = _wiring(material, e)
            b = w.get("B")
            if b is not None and str(_get(b, "parameter_name", "")) == "BaseTint":
                return e
    return None


def _scalar_param(material, name, default, group, x, y, smin=None, smax=None, key=None):
    node, _ = _mk_master(material, unreal.MaterialExpressionScalarParameter, key or name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", float(default))
    if smin is not None:
        _set(node, "slider_min", float(smin))
    if smax is not None:
        _set(node, "slider_max", float(smax))
    return node


def _vector_param(material, name, rgba, group, x, y, key=None):
    node, _ = _mk_master(material, unreal.MaterialExpressionVectorParameter, key or name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", unreal.LinearColor(*rgba))
    return node


def _switch_param(material, name, default, group, x, y, key=None):
    node, _ = _mk_master(material, unreal.MaterialExpressionStaticSwitchParameter, key or name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", bool(default))
    return node


def _cleanup_tagged(material):
    MEL = unreal.MaterialEditingLibrary
    victims = []
    for e in _exprs(material):
        if str(_get(e, "desc", "")).startswith(TAG):
            victims.append(e)
    for e in victims:
        try:
            MEL.delete_material_expression(material, e)
        except Exception as exc:
            _log(f"cleanup {e.get_name()}: {exc}")
    return len(victims)


# ────────────────────────────────────────────────────────────────
# Unique Nikki material functions (used ONLY by the Nikki masters)
# ────────────────────────────────────────────────────────────────

PASTEL_HLSL = r"""
float lum = dot(Mask, float3(0.299, 0.587, 0.114));
float pos = max(RampPosMid, 0.001);
float3 ramp = lum < pos
    ? lerp(RampLow, RampMid, saturate(lum / pos))
    : lerp(RampMid, RampHigh, saturate((lum - pos) / max(1.0 - pos, 0.001)));
float3 graded = lerp(BaseColor, ramp, saturate(Strength));
float3 lifted = lerp(graded, float3(1, 1, 1), saturate(PastelLift) * (1.0 - lum * 0.65));
float bloom = saturate((lum - 0.75) / 0.25) * saturate(Bloom);
return lifted + RampHigh * bloom;
"""

STICKER_HLSL = r"""
float lum = dot(Mask, float3(0.299, 0.587, 0.114));
float bands = max(BandCount, 1.0);
float banded = round(lum * bands) / bands;
float soft = lerp(lum, banded, saturate(BandSoftness));
float3 sticker = lerp(ShadeColor, BaseColor, saturate(soft * 1.25));
return lerp(BaseColor, sticker, saturate(Strength));
"""

TWINKLE_HLSL = r"""
float ndv = saturate(dot(normalize(Normal), normalize(Parameters.CameraVector)));
float fres = pow(1.0 - ndv, 2.0);
float3 ir = 0.5 + 0.5 * cos(6.28318 * (fres * max(Iridescence, 0.01) + float3(0.0, 0.33, 0.67)));
float tw = 0.5 + 0.5 * sin(dot(WorldPosition * max(TwinkleScale, 0.001), float3(1.7, 2.3, 0.9)) + 1.0);
float3 sheen = lerp(BaseColor, BaseColor * ir + Tint * fres, saturate(Sheen));
return sheen + Tint * tw * saturate(TwinkleAmount) * fres;
"""


def _build_mf(name, description, inputs, hlsl):
    """Create (or rebuild in place) a Nikki-unique material function."""
    path = f"{FUNCTION_DIR}/{name}"
    function = unreal.EditorAssetLibrary.load_asset(path)
    if function is None:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        function = tools.create_asset(name, FUNCTION_DIR, unreal.MaterialFunction, unreal.MaterialFunctionFactoryNew())
    if function is None:
        raise RuntimeError(f"Could not load/create {path}")
    try:
        unreal.MaterialEditingLibrary.delete_all_material_expressions_in_function(function)
    except Exception as exc:
        _log(f"function {name} graph clear failed: {exc}")

    fn_inputs = {}
    for i, (iname, itype) in enumerate(inputs):
        node, _ = _mk_fn(function, unreal.MaterialExpressionFunctionInput, "Input_" + iname, -1500, -500 + i * 130)
        _set(node, "input_name", iname)
        _set(node, "input_type", itype)
        _set(node, "sort_priority", i)
        fn_inputs[iname] = node

    custom, _ = _mk_fn(function, unreal.MaterialExpressionCustom, "Custom", -500, 0)
    _set(custom, "description", description)
    _set(custom, "code", hlsl)
    _set(custom, "output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ci = []
    for iname, _ in inputs:
        c = unreal.CustomInput()
        _set(c, "input_name", iname)
        ci.append(c)
    _set(custom, "inputs", ci)
    for iname in fn_inputs:
        _connect(fn_inputs[iname], "", custom, iname)

    out, _ = _mk_fn(function, unreal.MaterialExpressionFunctionOutput, "Output", 300, 0)
    _set(out, "output_name", "Color")
    _connect(custom, "", out, "")
    unreal.MaterialEditingLibrary.update_material_function(function)
    unreal.EditorAssetLibrary.save_loaded_asset(function)
    return function


def build_unique_functions() -> dict:
    f3 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3
    f1 = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
    pastel = _build_mf("MF_NikkiPastelGrade", "Kawaii pastel grade: lift + sakura ramp + dream bloom",
                       [("BaseColor", f3), ("Mask", f1), ("RampLow", f3), ("RampMid", f3), ("RampHigh", f3),
                        ("RampPosMid", f1), ("Strength", f1), ("PastelLift", f1), ("Bloom", f1)], PASTEL_HLSL)
    sticker = _build_mf("MF_NikkiStickerShade", "Sticker/anime-cel flattening for soft squishy cloth",
                        [("BaseColor", f3), ("Mask", f1), ("BandCount", f1), ("BandSoftness", f1),
                         ("ShadeColor", f3), ("Strength", f1)], STICKER_HLSL)
    twinkle = _build_mf("MF_NikkiTwinkleIris", "Iridescent twinkle + pastel fabric sheen",
                        [("BaseColor", f3), ("Normal", f3), ("WorldPosition", f3), ("Sheen", f1),
                         ("Iridescence", f1), ("TwinkleScale", f1), ("TwinkleAmount", f1), ("Tint", f3)],
                        TWINKLE_HLSL)
    return {"pastel": pastel, "sticker": sticker, "twinkle": twinkle}


# ────────────────────────────────────────────────────────────────
# Promotion + master surgery
# ────────────────────────────────────────────────────────────────

def _promote(name: str) -> str:
    src = f"{SCRATCH}/{name}.{name}"
    dest = f"{MASTER_DIR}/{name}.{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        _log(f"{dest} already exists")
        return dest
    if not unreal.EditorAssetLibrary.does_asset_exist(src):
        raise RuntimeError(f"promote source missing: {src}")
    if not unreal.EditorAssetLibrary.duplicate_asset(src, f"{MASTER_DIR}/{name}"):
        raise RuntimeError(f"promote duplicate failed: {name}")
    _log(f"promoted {src} -> {dest}")
    return dest


def _find_irid_call(material):
    candidates = []
    for e in _exprs(material):
        if type(e).__name__ != "MaterialExpressionMaterialFunctionCall":
            continue
        fn = _get(e, "material_function", None)
        if fn is not None and fn.get_name() in ("MF_IridescenceSheen", "MF_NikkiIridescenceSheen"):
            w = _wiring(material, e)
            if w.get("BaseColorIn") is not None:
                candidates.append(e)
    return candidates[0] if candidates else None


def master_surgery(material, landscape: bool, functions: dict):
    MEL = unreal.MaterialEditingLibrary
    _cleanup_tagged(material)

    # ── 1. remove v1 triplanar (surface only) ──
    base_src = None
    if not landscape:
        v1_switch = _param(material, "bTriplanar_Active")
        tintmul = _find_tintmul(material)
        if tintmul is None:
            raise RuntimeError("tintmul (BaseTint multiply) not found")
        if v1_switch is not None:
            for name in ("TriplanarScale", "TriplanarBlendSharpness"):
                p = _param(material, name)
                if p is not None:
                    MEL.delete_material_expression(material, p)
            for e in list(_exprs(material)):
                if type(e).__name__ == "MaterialExpressionMaterialFunctionCall":
                    fn = _get(e, "material_function", None)
                    if fn is not None and fn.get_name() == "MF_Triplanar":
                        MEL.delete_material_expression(material, e)
                if type(e).__name__ == "MaterialExpressionTextureObjectParameter" and _get(e, "parameter_name", "") == "Albedo":
                    MEL.delete_material_expression(material, e)
            MEL.delete_material_expression(material, v1_switch)
        albedo_samp = None
        for e in _exprs(material):
            if type(e).__name__ == "MaterialExpressionTextureSampleParameter2D" and _get(e, "parameter_name", "") == "Albedo":
                albedo_samp = e
                break
        if albedo_samp is None:
            raise RuntimeError("Albedo TextureSampleParameter2D not found")
        base_src = albedo_samp
        _connect(base_src, "RGB", tintmul, "A")
    else:
        for e in _exprs(material):
            if type(e).__name__ == "MaterialExpressionLandscapeLayerBlend":
                base_src = e
                break
        if base_src is None:
            raise RuntimeError("landscape layer blend not found")

    # ── 2. locate the grade chain anchors ──
    irid = _find_irid_call(material)
    if irid is None:
        raise RuntimeError("MF_IridescenceSheen call not found")
    atmos = None
    for e in _exprs(material):
        if type(e).__name__ == "MaterialExpressionLinearInterpolate":
            w = _wiring(material, e)
            b = w.get("B")
            if b is not None and str(_get(b, "parameter_name", "")) == "AtmosphericColor":
                atmos = e
                break
    if atmos is None:
        raise RuntimeError("atmospheric lerp not found")
    prev_out = irid
    prev_pin = "ColorOut"

    # ── 3. substance triplanar pro lane (default OFF) ──
    g = "03 | Triplanar"
    tsw = _switch_param(material, "bTriplanarPro_Active", False, g, -2350, -700)
    _scalar_param(material, "TriplanarPro_Scale", 0.01, g, -2350, -560, 0.00001, 1.0)
    _scalar_param(material, "TriplanarPro_Sharpness", 4.0, g, -2350, -500, 0.01, 32.0)
    _scalar_param(material, "TriplanarPro_BlendStrength", 0.0, g, -2350, -440, 0.0, 1.0)
    _scalar_param(material, "TriplanarPro_BreakupStrength", 0.0, g, -2350, -220, 0.0, 1.0)
    _scalar_param(material, "TriplanarPro_BreakupScale", 1.0, g, -2350, -160, 0.001, 32.0)
    _scalar_param(material, "TriplanarPro_BreakupContrast", 1.0, g, -2350, -100, 0.01, 8.0)
    off = _vector_param(material, "TriplanarPro_ProjectionOffset", (0, 0, 0, 0), g, -2350, -40)
    rot = _vector_param(material, "TriplanarPro_ProjectionRotation", (0, 0, 0, 0), g, -2350, 20)
    aw = _vector_param(material, "TriplanarPro_AxisWeights", (1, 1, 1, 0), g, -2350, 80)

    pro_fn = unreal.EditorAssetLibrary.load_asset(PRO_FN)
    call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "ProCall", -2100, -600)
    _set(call, "material_function", pro_fn)
    tex_obj, _ = _mk_master(material, unreal.MaterialExpressionTextureObjectParameter, "ProTex", -2350, -820)
    _set(tex_obj, "parameter_name", "Albedo")
    _set(tex_obj, "group", g)
    wp, _ = _mk_master(material, unreal.MaterialExpressionWorldPosition, "ProWP", -2350, 200)
    vn, _ = _mk_master(material, unreal.MaterialExpressionVertexNormalWS, "ProVN", -2350, 280)
    _connect(tex_obj, "", call, "Tex")
    _connect(wp, "", call, "WorldPosition")
    _connect(vn, "", call, "WorldNormal")
    _connect(_param(material, "TriplanarPro_Scale"), "", call, "ProjectionScale")
    _connect(_param(material, "TriplanarPro_Sharpness"), "", call, "BlendSharpness")
    _connect(off, "", call, "ProjectionOffset")
    _connect(rot, "", call, "ProjectionRotation")
    _connect(aw, "", call, "AxisWeights")
    _connect(_param(material, "TriplanarPro_BreakupScale"), "", call, "BreakupScale")
    _connect(_param(material, "TriplanarPro_BreakupStrength"), "", call, "BreakupStrength")
    _connect(_param(material, "TriplanarPro_BreakupContrast"), "", call, "BreakupContrast")
    tri_lerp, _ = _mk_master(material, unreal.MaterialExpressionLinearInterpolate, "ProBlend", -1900, -600)
    _connect(base_src, "RGB" if not landscape else "", tri_lerp, "A")
    _connect(call, "Color", tri_lerp, "B")
    _connect(_param(material, "TriplanarPro_BlendStrength"), "", tri_lerp, "Alpha")
    _connect(tri_lerp, "", tsw, "True")
    _connect(base_src, "RGB" if not landscape else "", tsw, "False")

    # splice the triplanar gate in place of the direct base source
    tintmul = _find_tintmul(material)
    if tintmul is None:
        raise RuntimeError("tintmul (BaseTint multiply) not found")
    _connect(tsw, "", tintmul, "A")

    # ── 4. unique function chain: sticker -> twinkle -> pastel -> shadow dream ──
    gn = "04 | Nikki Cute"
    # sticker
    s_sw = _switch_param(material, "bNikkiStickerShade_Active", False, gn, -1600, 200)
    _scalar_param(material, "NikkiStickerBandCount", 4.0, gn, -1600, 340, 1.0, 8.0)
    _scalar_param(material, "NikkiStickerBandSoftness", 0.85, gn, -1600, 400, 0.0, 1.0)
    _scalar_param(material, "NikkiStickerStrength", 0.5, gn, -1600, 460, 0.0, 1.0)
    _vector_param(material, "NikkiStickerShadeColor", (0.72, 0.55, 0.68, 1), gn, -1600, 280)
    s_call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "StickerCall", -1750, 240)
    _set(s_call, "material_function", functions["sticker"])
    _connect(prev_out, prev_pin, s_call, "BaseColor")
    lum_w, _ = _mk_master(material, unreal.MaterialExpressionConstant3Vector, "LumW", -1950, 520)
    _set(lum_w, "constant", unreal.LinearColor(0.299, 0.587, 0.114, 0))
    lum, _ = _mk_master(material, unreal.MaterialExpressionDotProduct, "LumDot", -1950, 580)
    _connect(prev_out, prev_pin, lum, "A")
    _connect(lum_w, "", lum, "B")
    _connect(lum, "", s_call, "Mask")
    _connect(_param(material, "NikkiStickerBandCount"), "", s_call, "BandCount")
    _connect(_param(material, "NikkiStickerBandSoftness"), "", s_call, "BandSoftness")
    _connect(_param(material, "NikkiStickerShadeColor"), "", s_call, "ShadeColor")
    _connect(_param(material, "NikkiStickerStrength"), "", s_call, "Strength")
    _connect(prev_out, prev_pin, s_sw, "False")
    _connect(s_call, "Color", s_sw, "True")

    # twinkle iris (fabric sheen)
    t_sw = _switch_param(material, "bNikkiTwinkleIris_Active", True, gn, -1350, 200)
    _scalar_param(material, "NikkiFabricSheen", 0.5, gn, -1350, 360, 0.0, 1.0)
    _scalar_param(material, "NikkiIridescence", 2.0, gn, -1350, 420, 0.0, 8.0)
    _scalar_param(material, "NikkiTwinkleScale", 0.5, gn, -1350, 480, 0.01, 8.0)
    _scalar_param(material, "NikkiTwinkleAmount", 0.12, gn, -1350, 540, 0.0, 1.0)
    _vector_param(material, "NikkiIrisTint", (1.0, 0.8, 0.95, 1), gn, -1350, 300)
    t_call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "TwinkleCall", -1500, 240)
    _set(t_call, "material_function", functions["twinkle"])
    _connect(s_sw, "", t_call, "BaseColor")
    _connect(vn, "", t_call, "Normal")
    _connect(wp, "", t_call, "WorldPosition")
    _connect(_param(material, "NikkiFabricSheen"), "", t_call, "Sheen")
    _connect(_param(material, "NikkiIridescence"), "", t_call, "Iridescence")
    _connect(_param(material, "NikkiTwinkleScale"), "", t_call, "TwinkleScale")
    _connect(_param(material, "NikkiTwinkleAmount"), "", t_call, "TwinkleAmount")
    _connect(_param(material, "NikkiIrisTint"), "", t_call, "Tint")
    _connect(s_sw, "", t_sw, "False")
    _connect(t_call, "Color", t_sw, "True")

    # pastel grade (the kawaii default, ON)
    p_sw = _switch_param(material, "bNikkiPastelGrade_Active", True, gn, -1100, 200)
    _scalar_param(material, "NikkiPastelStrength", 0.6, gn, -1100, 400, 0.0, 1.0)
    _scalar_param(material, "NikkiPastelLift", 0.12, gn, -1100, 460, 0.0, 0.5)
    _scalar_param(material, "NikkiPastelPosMid", 0.45, gn, -1100, 520, 0.05, 0.95)
    _scalar_param(material, "NikkiPastelBloom", 0.25, gn, -1100, 580, 0.0, 1.0)
    _vector_param(material, "NikkiPastelRampLow", (0.95, 0.85, 0.92, 1), gn, -1100, 300)
    _vector_param(material, "NikkiPastelRampMid", (0.99, 0.93, 0.90, 1), gn, -1100, 340)
    _vector_param(material, "NikkiPastelRampHigh", (1.0, 0.98, 0.96, 1), gn, -1100, 380)
    p_call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "PastelCall", -1250, 240)
    _set(p_call, "material_function", functions["pastel"])
    _connect(t_sw, "", p_call, "BaseColor")
    _connect(lum, "", p_call, "Mask")
    _connect(_param(material, "NikkiPastelRampLow"), "", p_call, "RampLow")
    _connect(_param(material, "NikkiPastelRampMid"), "", p_call, "RampMid")
    _connect(_param(material, "NikkiPastelRampHigh"), "", p_call, "RampHigh")
    _connect(_param(material, "NikkiPastelPosMid"), "", p_call, "RampPosMid")
    _connect(_param(material, "NikkiPastelStrength"), "", p_call, "Strength")
    _connect(_param(material, "NikkiPastelLift"), "", p_call, "PastelLift")
    _connect(_param(material, "NikkiPastelBloom"), "", p_call, "Bloom")
    _connect(t_sw, "", p_sw, "False")
    _connect(p_call, "Color", p_sw, "True")

    # shadow dream (mirrors universal pattern, gated default-OFF)
    gsd = "05 | Shadow Dream"
    sd_sw = _switch_param(material, "bShadowDream_Active", False, gsd, -850, 200)
    _scalar_param(material, "ShadowDreamStrength", 0.15, gsd, -850, 340, 0.0, 1.5)
    _scalar_param(material, "ShadowSoftness", 1.0, gsd, -850, 400, 0.1, 8.0)
    _vector_param(material, "ShadowDreamTint", (0.48, 0.42, 0.62, 1), gsd, -850, 280)
    lv, _ = _mk_master(material, unreal.MaterialExpressionLightVector, "SDLight", -1050, 500)
    ndl, _ = _mk_master(material, unreal.MaterialExpressionDotProduct, "SDNdotL", -1050, 560)
    _connect(vn, "", ndl, "A")
    _connect(lv, "", ndl, "B")
    om, _ = _mk_master(material, unreal.MaterialExpressionOneMinus, "SDOneMinus", -1050, 620)
    _connect(ndl, "", om, "")
    pw, _ = _mk_master(material, unreal.MaterialExpressionPower, "SDPow", -1050, 680)
    _connect(om, "", pw, "Base")
    _connect(_param(material, "ShadowSoftness"), "", pw, "Exp")
    smul, _ = _mk_master(material, unreal.MaterialExpressionMultiply, "SDMul", -1050, 740)
    _connect(pw, "", smul, "A")
    _connect(_param(material, "ShadowDreamStrength"), "", smul, "B")
    tintmul2, _ = _mk_master(material, unreal.MaterialExpressionMultiply, "SDTintMul", -1050, 800)
    _connect(p_sw, "", tintmul2, "A")
    _connect(_param(material, "ShadowDreamTint"), "", tintmul2, "B")
    sd_lerp, _ = _mk_master(material, unreal.MaterialExpressionLinearInterpolate, "SDLerp", -850, 260)
    _connect(p_sw, "", sd_lerp, "A")
    _connect(tintmul2, "", sd_lerp, "B")
    _connect(smul, "", sd_lerp, "Alpha")
    _connect(p_sw, "", sd_sw, "False")
    _connect(sd_lerp, "", sd_sw, "True")

    # re-splice into the atmospheric lerp
    _connect(sd_sw, "", atmos, "A")

    # ── 5. kawaii squish WPO (default OFF, optional) ──
    gw = "06 | Kawaii Squish"
    sq_sw = _switch_param(material, "bKawaiiSquish_Active", False, gw, -500, 200)
    _scalar_param(material, "SquishAmount", 0.4, gw, -500, 340, 0.0, 4.0)
    sq_dot, _ = _mk_master(material, unreal.MaterialExpressionDotProduct, "SquishDot", -700, 420)
    dirv, _ = _mk_master(material, unreal.MaterialExpressionConstant3Vector, "SquishDir", -900, 480)
    _set(dirv, "constant", unreal.LinearColor(1.3, 2.1, 0.7, 0))
    _connect(wp, "", sq_dot, "A")
    _connect(dirv, "", sq_dot, "B")
    sq_sin, _ = _mk_master(material, unreal.MaterialExpressionSine, "SquishSin", -700, 480)
    _connect(sq_dot, "", sq_sin, "")
    sq_mul, _ = _mk_master(material, unreal.MaterialExpressionMultiply, "SquishMul", -700, 560)
    _connect(sq_sin, "", sq_mul, "A")
    _connect(_param(material, "SquishAmount"), "", sq_mul, "B")
    sq_off, _ = _mk_master(material, unreal.MaterialExpressionMultiply, "SquishOffset", -700, 640)
    _connect(vn, "", sq_off, "A")
    _connect(sq_mul, "", sq_off, "B")
    zero, _ = _mk_master(material, unreal.MaterialExpressionConstant3Vector, "SquishZero", -700, 720)
    _set(zero, "constant", unreal.LinearColor(0, 0, 0, 0))
    _connect(sq_off, "", sq_sw, "True")
    _connect(zero, "", sq_sw, "False")
    MEL.connect_material_property(sq_sw, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)

    # ── 6. kawaii defaults ──
    bt = _param(material, "BaseTint")
    if bt is not None:
        _set(bt, "default_value", unreal.LinearColor(0.98, 0.93, 0.96, 1))
    ef = _param(material, "EmissiveFloor")
    if ef is not None:
        _set(ef, "default_value", 0.18)
    ira = _param(material, "IridescenceRoughnessAtten")
    if ira is not None:
        _set(ira, "default_value", 0.25)

    MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def main():
    functions = build_unique_functions()
    _log("unique functions built")
    for name, landscape in (("M_Master_Nikki", False), ("M_Master_Nikki_Landscape", True)):
        path = _promote(name)
        material = unreal.EditorAssetLibrary.load_asset(path)
        if material is None:
            raise RuntimeError(f"load failed: {path}")
        master_surgery(material, landscape, functions)
        _log(f"surgery complete: {path}")
    return {"functions": [f"{FUNCTION_DIR}/MF_NikkiPastelGrade", f"{FUNCTION_DIR}/MF_NikkiStickerShade",
                          f"{FUNCTION_DIR}/MF_NikkiTwinkleIris"],
            "masters": [f"{MASTER_DIR}/M_Master_Nikki", f"{MASTER_DIR}/M_Master_Nikki_Landscape"]}


if __name__ == "__main__":
    main()
