"""Expand M_Master_Nikki with a Melodia gouache-wash feature.

Builds MF_MeluGouacheWash (Custom HLSL: toon-band ramp + granulation darken +
wash-blotch darken + fwidth edge ink, all scalar/vector inputs) and splices it
at the END of the Nikki feature chain (after petal shadow, before ShadowDream),
behind its own default-OFF static switch, tagged `MeluGouache:` for idempotent
re-runs. Mirrors Content/Python/expand_nikki_features.py exactly:
  - _build_mf pattern (FunctionInput nodes + Custom node + FunctionOutput "Color")
  - per-stage static switch (False=bypass, True=effect) chained switch-to-switch
  - scalar params with slider ranges, vector params, texture params, one group
  - MI_Nikki_Show_GouacheWash demo + Saved/Audit receipt JSON

Why an MF and not the orphan M_PainterlyGouache master: the MF composes with
the existing Nikki/Melu toolchain (MPC params, Nikki feature switches, T3D
baseline family) instead of forking a parallel Substrate master that renders
black outside its own preview.

The HLSL is a faithful port of the gouache band/granulation/blotch/edge math
(DDX/DDY dot form preserved), with two deliberate deviations noted inline:
band softness is clamped >= 1e-3 (smoothstep with equal edges is undefined),
and a global Strength gate is added (the orphan had none).

Texture fields (granulation/blotch) are sampled by the MASTER from the
existing gouache tileables (/Game/Materials/Textures/Gouache/) and passed in
as scalars, so the MF stays pure math like the rest of the family.

Landscape master is deliberately NOT touched: a character paint wash does not
belong on landscape. Revisit only with an explicit art call.

Run in the UE editor: expand_melu_gouache.main()
Writes: Saved/Audit/melodia_gouache_mf_2026-10-10.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

FUNCTION_DIR = "/Game/EnvSandbox/Materials/Functions"
MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
SHOW_DIR = "/Game/EnvSandbox/Materials/Instances/NikkiHero"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "melodia_gouache_mf_2026-10-10.json"
TAG = "MeluGouache:"

MEL = unreal.MaterialEditingLibrary


def _get(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _set(obj, name, value):
    obj.set_editor_property(name, value)


def _log(message):
    unreal.log(f"[MeluGouache] {message}")


def _fexprs(function):
    return list(MEL.get_material_function_expressions(function) or [])


def _find_tag(exprs, key):
    wanted = TAG + key
    for e in exprs:
        if str(_get(e, "desc", "")) == wanted:
            return e
    return None


def _mk_fn(function, cls, key, x, y):
    node = _find_tag(_fexprs(function), key)
    if node:
        return node, False
    node = MEL.create_material_expression_in_function(function, cls, x, y)
    _set(node, "desc", TAG + key)
    return node, True


def _connect(source, output, target, input_name):
    if not MEL.connect_material_expressions(source, output, target, input_name):
        raise RuntimeError(f"connect failed: {source.get_name()}:{output} -> {target.get_name()}:{input_name}")


GOUACHE_WASH = r"""
// Melodia gouache wash: toon bands + pigment granulation + wash blotch + ink edge.
// Port of the M_PainterlyGouache node chain (band smoothsteps, granulation lerp,
// blotch lerp, DDX/DDY-dot fwidth edge); deviations: BandSoftness clamped >=1e-3,
// global Strength gate added.
float b = saturate(NdotL);
float soft = max(BandSoftness, 1e-3);
float ssLo = smoothstep(BandShadow - soft, BandShadow + soft, b);
float ssHi = smoothstep(BandLight - soft, BandLight + soft, b);
float3 c0 = lerp(BaseColor, InkColor, saturate(ShadowMix));
float3 c1 = lerp(c0, BaseColor, ssLo);
float3 c2 = lerp(c1, HighlightTint, ssHi);
float3 c3 = lerp(c2, c2 * saturate(GranDarken), saturate(GranField) * saturate(Granulation) * saturate(Mask));
float3 c4 = lerp(c3, c3 * saturate(BlotchField), saturate(BlotchStrength) * saturate(Mask));
float v = ssLo + ssHi;
float fw = abs(ddx(v) * ddy(v));
float edge = saturate(fw * EdgeWidth / max(EdgeReference, 1e-4)) * saturate(EdgeStrength);
float3 c5 = lerp(c4, InkColor, edge * saturate(Mask));
return lerp(BaseColor, c5, saturate(Strength) * saturate(Mask));
"""

# (input_name, input_type) — FunctionInput types follow the expand_nikki_features.py
# convention: scalar vs vector3. Keep names stable: they are the MF's contract.
WASH_INPUTS = [
    ("BaseColor", "float3"),
    ("Mask", "float"),
    ("NdotL", "float"),
    ("GranField", "float"),
    ("BlotchField", "float"),
    ("BandShadow", "float"),
    ("BandLight", "float"),
    ("BandSoftness", "float"),
    ("ShadowMix", "float"),
    ("Granulation", "float"),
    ("GranDarken", "float"),
    ("BlotchStrength", "float"),
    ("EdgeWidth", "float"),
    ("EdgeReference", "float"),
    ("EdgeStrength", "float"),
    ("InkColor", "float3"),
    ("HighlightTint", "float3"),
    ("Strength", "float"),
]


def _build_mf(name, description, inputs, hlsl):
    """Create (or rebuild in place) the gouache wash material function."""
    path = f"{FUNCTION_DIR}/{name}"
    function = unreal.EditorAssetLibrary.load_asset(path)
    if function is None:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        function = tools.create_asset(name, FUNCTION_DIR, unreal.MaterialFunction,
                                      unreal.MaterialFunctionFactoryNew())
    if function is None:
        raise RuntimeError(f"Could not load/create {path}")
    try:
        MEL.delete_all_material_expressions_in_function(function)
    except Exception as exc:
        _log(f"function {name} graph clear failed: {exc}")

    fn_inputs = {}
    for i, (iname, itype) in enumerate(inputs):
        node, _ = _mk_fn(function, unreal.MaterialExpressionFunctionInput, "Input_" + iname,
                          -1500, -500 + i * 90)
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
    MEL.update_material_function(function)
    unreal.EditorAssetLibrary.save_loaded_asset(function)
    return function


def build_wash_function() -> dict:
    function = _build_mf(
        "MF_MeluGouacheWash",
        "Melodia gouache wash: toon bands + granulation + blotch + ink edge (see module docstring)",
        WASH_INPUTS,
        GOUACHE_WASH,
    )
    return {"wash": function}


def _exprs(material):
    return list(MEL.get_material_expressions(material) or [])


def _param(material, name):
    for e in _exprs(material):
        if str(_get(e, "parameter_name", "")) == name:
            return e
    return None


def _find_tag_master(material, key):
    wanted = TAG + key
    for e in _exprs(material):
        if str(_get(e, "desc", "")) == wanted:
            return e
    return None


def _mk_master(material, cls, key, x, y):
    node = _find_tag_master(material, key)
    if node:
        return node, False
    node = MEL.create_material_expression(material, cls, x, y)
    _set(node, "desc", TAG + key)
    return node, True


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


def _texture_param(material, name, texture_path, group, x, y, key=None):
    node, _ = _mk_master(material, unreal.MaterialExpressionTextureSampleParameter2D, key or name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    tex = unreal.EditorAssetLibrary.load_asset(texture_path)
    if tex is None:
        raise RuntimeError(f"texture missing: {texture_path}")
    _set(node, "texture", tex)
    return node


def master_surgery(material, functions: dict):
    g = "07 | Gouache Wash"

    # clean up nodes from a prior run so the rebuild is clean.
    # ONLY removes nodes this script tagged (MeluGouache:) - never the original
    # Nikki chain (NikkiX:) or the NikkiFeat: nodes.
    victims = []
    for e in _exprs(material):
        if str(_get(e, "desc", "")).startswith(TAG):
            victims.append(e)
    for e in victims:
        try:
            MEL.delete_material_expression(material, e)
        except Exception as exc:
            _log(f"cleanup {e.get_name()}: {exc}")

    # Verified insertion point: the tagged feature stage that feeds the final
    # BaseColor pin of the master's BSDF. The August `NikkiX:SDLerp` node is a
    # dead orphan on the live master (a `MelPile:` stage now ends the chain), so
    # walk the live graph instead of trusting that tag.
    def _inputs_of(node):
        try:
            names = list(MEL.get_material_expression_input_names(node))
        except Exception:
            names = []
        try:
            ins = list(MEL.get_inputs_for_material_expression(material, node))
        except Exception:
            ins = []
        out = {}
        for i, n in enumerate(names):
            x = ins[i] if i < len(ins) else None
            if x is not None:
                out[n] = x
        return out

    bsdf = None
    for e in _exprs(material):
        if "SubstrateToonBSDF" in type(e).__name__ or "Substrate" in type(e).__name__:
            bsdf = e
            break
    if bsdf is None:
        raise RuntimeError("no BSDF node found to anchor the gouache splice")
    bi = _inputs_of(bsdf)
    final_node = bi.get("BaseColor")
    if final_node is None:
        raise RuntimeError("BSDF BaseColor has no input to splice before")
    final_pin, tail_src = None, None
    for pin, src in _inputs_of(final_node).items():
        d = ""
        try:
            d = str(_get(src, "desc", "")) if src else ""
        except Exception:
            d = ""
        if d.startswith(("NikkiX:", "NikkiFeat:", "MelPile:", TAG)):
            final_pin, tail_src = pin, src
            break
    if tail_src is None or final_pin is None:
        raise RuntimeError("no tagged feature stage found feeding the final basecolor pin")

    # ── Gouache wash stage ──
    gw_sw = _switch_param(material, "bMeluGouacheWash_Active", False, g, 900, 200)
    _scalar_param(material, "MeluGouache_BandShadow", 0.4, g, 900, 340, 0.05, 1.0)
    _scalar_param(material, "MeluGouache_BandLight", 0.7, g, 900, 400, 0.05, 1.0)
    _scalar_param(material, "MeluGouache_BandSoftness", 0.04, g, 900, 460, 0.0, 0.25)
    _scalar_param(material, "MeluGouache_ShadowMix", 0.55, g, 900, 520, 0.0, 1.0)
    _scalar_param(material, "MeluGouache_Granulation", 0.35, g, 900, 580, 0.0, 1.0)
    _scalar_param(material, "MeluGouache_GranDarken", 0.7, g, 900, 640, 0.0, 1.0)
    _scalar_param(material, "MeluGouache_BlotchStrength", 0.18, g, 900, 700, 0.0, 1.0)
    _scalar_param(material, "MeluGouache_EdgeWidth", 1.0, g, 900, 760, 0.01, 4.0)
    _scalar_param(material, "MeluGouache_EdgeReference", 0.02, g, 900, 820, 0.001, 0.5)
    _scalar_param(material, "MeluGouache_EdgeStrength", 0.55, g, 900, 880, 0.0, 2.0)
    _scalar_param(material, "MeluGouache_Strength", 1.0, g, 900, 940, 0.0, 1.5)
    _vector_param(material, "MeluGouache_InkColor", (0.05, 0.07, 0.12, 1), g, 900, 300)
    _vector_param(material, "MeluGouache_HighlightTint", (0.88, 0.84, 0.76, 1), g, 900, 360)
    _vector_param(material, "MeluGouache_KeyLightDir", (0, 0, 1, 0), g, 900, 420)
    gran_tex = _texture_param(material, "MeluGouache_GranulationTex",
                              "/Game/Materials/Textures/Gouache/T_Gouache_Granulation", g, 400, 1100)
    blotch_tex = _texture_param(material, "MeluGouache_BlotchTex",
                                "/Game/Materials/Textures/Gouache/T_Gouache_WashBlotch", g, 620, 1100)
    _scalar_param(material, "MeluGouache_UVTiling", 6.0, g, 510, 1220, 0.1, 64.0)

    tc, _ = _mk_master(material, unreal.MaterialExpressionTextureCoordinate, "WashUV", 300, 1220)
    uv_mul, _ = _mk_master(material, unreal.MaterialExpressionMultiply, "WashUVMul", 300, 1100)
    _connect(tc, "", uv_mul, "A")
    _connect(_param(material, "MeluGouache_UVTiling"), "", uv_mul, "B")
    _connect(uv_mul, "", gran_tex, "UVs")
    _connect(uv_mul, "", blotch_tex, "UVs")

    vn, _ = _mk_master(material, unreal.MaterialExpressionVertexNormalWS, "WashVN", 300, 500)
    ndot, _ = _mk_master(material, unreal.MaterialExpressionDotProduct, "WashNDotL", 300, 560)
    _connect(vn, "", ndot, "A")
    _connect(_param(material, "MeluGouache_KeyLightDir"), "", ndot, "B")
    nsat, _ = _mk_master(material, unreal.MaterialExpressionSaturate, "WashNDotLSat", 300, 620)
    _connect(ndot, "", nsat, "Input")

    gw_call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "WashCall", 700, 240)
    _set(gw_call, "material_function", functions["wash"])
    lum, _ = _mk_master(material, unreal.MaterialExpressionDotProduct, "WashLum", 500, 800)
    lumw, _ = _mk_master(material, unreal.MaterialExpressionConstant3Vector, "WashLumW", 300, 840)
    _set(lumw, "constant", unreal.LinearColor(0.299, 0.587, 0.114, 0))
    _connect(tail_src, "", lum, "A")
    _connect(lumw, "", lum, "B")
    _connect(tail_src, "", gw_call, "BaseColor")
    _connect(lum, "", gw_call, "Mask")
    _connect(nsat, "", gw_call, "NdotL")
    _connect(gran_tex, "R", gw_call, "GranField")
    _connect(blotch_tex, "R", gw_call, "BlotchField")
    for pname, fname in (("MeluGouache_BandShadow", "BandShadow"),
                         ("MeluGouache_BandLight", "BandLight"),
                         ("MeluGouache_BandSoftness", "BandSoftness"),
                         ("MeluGouache_ShadowMix", "ShadowMix"),
                         ("MeluGouache_Granulation", "Granulation"),
                         ("MeluGouache_GranDarken", "GranDarken"),
                         ("MeluGouache_BlotchStrength", "BlotchStrength"),
                         ("MeluGouache_EdgeWidth", "EdgeWidth"),
                         ("MeluGouache_EdgeReference", "EdgeReference"),
                         ("MeluGouache_EdgeStrength", "EdgeStrength"),
                         ("MeluGouache_InkColor", "InkColor"),
                         ("MeluGouache_HighlightTint", "HighlightTint"),
                         ("MeluGouache_Strength", "Strength")):
        _connect(_param(material, pname), "", gw_call, fname)

    _connect(tail_src, "", gw_sw, "False")
    _connect(gw_call, "Color", gw_sw, "True")
    _connect(gw_sw, "", sd_lerp, "A")

    MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return True


def make_show():
    """MI_Nikki_Show_GouacheWash: demo instance with the wash switched on."""
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    name = "MI_Nikki_Show_GouacheWash"
    mi = unreal.EditorAssetLibrary.load_asset(f"{SHOW_DIR}/{name}")
    if mi is None:
        mi = tools.create_asset(name, SHOW_DIR, unreal.MaterialInstanceConstant,
                                unreal.MaterialInstanceConstantFactoryNew())
    parent = unreal.EditorAssetLibrary.load_asset(f"{MASTER_DIR}/M_Master_Nikki")
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)
    unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
        mi, "bMeluGouacheWash_Active", True)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        mi, "MeluGouache_Strength", 0.85)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return f"{SHOW_DIR}/{name}"


def main(rebuild_functions: bool = True):
    if rebuild_functions:
        functions = build_wash_function()
        _log("gouache wash function built")
    else:
        functions = {}
        fn = unreal.EditorAssetLibrary.load_asset(f"{FUNCTION_DIR}/MF_MeluGouacheWash")
        if fn is None:
            raise RuntimeError("function missing: MF_MeluGouacheWash")
        functions["wash"] = fn
    path = f"{MASTER_DIR}/M_Master_Nikki"
    material = unreal.EditorAssetLibrary.load_asset(path)
    if material is None:
        raise RuntimeError(f"load failed: {path}")
    master_surgery(material, functions)
    _log(f"surgery complete: {path}")
    show = make_show()
    payload = {"generated": "2026-10-10", "functions": ["wash:MF_MeluGouacheWash"],
               "masters": [path], "show": show}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _log("done")
    return payload


if __name__ == "__main__":
    main()
