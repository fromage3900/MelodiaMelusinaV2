"""Expand the triplanar + SDF-quasicrystal material lane (Melodia, 2026-10-10).

Rider-authored shader source is the single source of truth:
  Source/MelodiaShader/Shaders/MelodiaInkCommon.ush        (shared helpers)
  Source/MelodiaShader/Shaders/MelodiaTriplanarCommon.ush  (triplanar v2)
  Source/MelodiaShader/Shaders/MelodiaSdfQuasicrystal.ush  (quasicrystal field)

This builder INLINES that source (after stripping #pragma / #include) into
Custom HLSL nodes — the proven lane the ink shaders use, and the reason the
Custom node never depends on a runtime #include resolving.

Builds three functions:
  MF_MeluTriplanar_Albedo  - per-axis scale/offset/rotation, macro-variation
                             anti-tiling, distance fade (replaces the "albedo
                             only, one uniform scale" limit of MF_Triplanar_Stable)
  MF_MeluTriplanar_Normal  - RG decode + world-space whiteout blend, so a
                             triplanar surface can finally carry a normal map
  MF_MeluSdfQuasicrystal   - aperiodic 5/8/12-fold field: nodal facet lines,
                             contour bands, per-facet tint, iridescence

Splices the quasicrystal stage into M_Master_Nikki behind the default-OFF
`bMeluQuasicrystal_Active` switch, group `08 | Quasicrystal`, chaining after
whatever currently feeds the ShadowDream lerp (so it composes with the gouache
wash instead of fighting it). Creates MI_Nikki_Show_Quasicrystal.

Deliberately NOT done here:
  * MF_Triplanar_Stable is left untouched. Rebuilding its graph in place would
    change its input pins and silently break every consumer master that calls it
    (Universal / Nikki / Landscape). Migrating a master to the v2 functions is a
    per-master art call; the splice hook exists but stays off.
  * M_Master_Gemstone is not auto-spliced: its basecolor anchor has not been
    inspected, and a blind splice into a live gemstone master is destructive.
    Pass --gemstone after inspecting its anchor.

Run in the UE editor: expand_melu_sdf_triplanar.main()
Writes: Saved/Audit/melodia_sdf_triplanar_2026-10-10.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
SHADER_DIR = ROOT / "Source" / "MelodiaShader" / "Shaders"
COMMON = SHADER_DIR / "MelodiaInkCommon.ush"
TRIPLANAR = SHADER_DIR / "MelodiaTriplanarCommon.ush"
QUASICRYSTAL = SHADER_DIR / "MelodiaSdfQuasicrystal.ush"

FUNCTION_DIR = "/Game/EnvSandbox/Materials/Functions"
MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
SHOW_DIR = "/Game/EnvSandbox/Materials/Instances/NikkiHero"
OUT = ROOT / "Saved" / "Audit" / "melodia_sdf_triplanar_2026-10-10.json"
TAG = "MeluShaders:"

MEL = unreal.MaterialEditingLibrary

# FunctionInputType enum names differ across engine versions; resolve defensively.
def _fit(name: str, fallback: str):
    return getattr(unreal.FunctionInputType, name, fallback)

FN_SCALAR = _fit("FUNCTION_INPUT_SCALAR", "float")
FN_VEC3 = _fit("FUNCTION_INPUT_VECTOR3", "float3")
FN_TEX = _fit("FUNCTION_INPUT_TEXTURE2D", "texture2D")


def _get(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _set(obj, name, value):
    obj.set_editor_property(name, value)


def _log(message):
    unreal.log(f"[MeluShaders] {message}")


def inline_source(paths):
    """Strip #pragma once / #include lines so the body can be pasted into a
    Custom node. Includes are resolved by simple concatenation, in order."""
    chunks = []
    for p in paths:
        if not p.exists():
            raise RuntimeError(f"shader source missing: {p}")
        for line in p.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#pragma once") or stripped.startswith("#include"):
                continue
            chunks.append(line)
    return "\n".join(chunks)


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
        raise RuntimeError(
            f"connect failed: {source.get_name()}:{output} -> {target.get_name()}:{input_name}")


def _build_mf(name, description, inputs, hlsl):
    """Create (or rebuild in place) a Custom-HLSL material function."""
    path = f"{FUNCTION_DIR}/{name}"
    function = unreal.EditorAssetLibrary.load_asset(path)
    if function is None:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        function = tools.create_asset(name, FUNCTION_DIR, unreal.MaterialFunction,
                                      unreal.MaterialFunctionFactoryNew())
    if function is None:
        raise RuntimeError(f"could not load/create {path}")
    try:
        MEL.delete_all_material_expressions_in_function(function)
    except Exception as exc:
        _log(f"function {name} graph clear failed: {exc}")

    fn_inputs = {}
    for i, (iname, itype) in enumerate(inputs):
        node, _ = _mk_fn(function, unreal.MaterialExpressionFunctionInput,
                         "Input_" + iname, -1500, -500 + i * 110)
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
    _save(function)
    return function


COMMON_SRC = None


def build_functions():
    # Inline order matters: shared helpers first, then the lane body.
    tp_body = inline_source([COMMON, TRIPLANAR])
    tp_albedo_code = tp_body + """

return MelTriplanarAlbedo(Tex, TexSampler, WorldPos, Normal, Scale, Offset, Rotation,
                          Sharpness, MacroScale, MacroAmount, FadeStart, FadeEnd,
                          ViewPos, FadeColor);
"""
    tp_normal_code = tp_body + """

return MelTriplanarNormal(Tex, TexSampler, WorldPos, Normal, Scale, Sharpness, Strength);
"""
    qc_body = inline_source([COMMON, QUASICRYSTAL])
    qc_code = qc_body + """

// drift the field through the golden-ratio direction so the pattern evolves
// without repeating; Phase is the animation driver (material Time), BeatPulse
// adds a musical push (tempo-locked upstream, never wall-clock here).
float2 qcP = WorldPos.xz * Scale + float2(MEL_QC_CONJ, -MEL_QC_CONJ) * Phase * 0.15;
float field = MelQcWave(qcP, Folds, Freq, Ratio);

float nodal = MelQcZeroLine(field, NodalWidth);
float band = MelQcBand(field, BandCount, BandWidth);
float facet = MelQcCellHash(qcP, FacetScale);

float3 facetCol = FacetTint * (0.75 + 0.5 * facet);
float3 c = lerp(BaseColor, facetCol, MelSaturate(Mask) * 0.85);
c = lerp(c, EdgeColor, nodal * MelSaturate(Mask));
c += EdgeColor * band * 0.35 * MelSaturate(Mask);

float ndv = MelSaturate(dot(normalize(Normal), normalize(ViewVector)));
c *= MelQcIridescence(ndv, IriShift + BeatPulse * 0.25, IriStrength);

return lerp(BaseColor, c, MelSaturate(Strength) * MelSaturate(Mask));
"""

    fns = {}
    fns["albedo"] = _build_mf(
        "MF_MeluTriplanar_Albedo",
        "Triplanar v2 albedo: per-axis scale/offset/rotation, hash anti-tiling, distance fade",
        [("Tex", FN_TEX), ("Normal", FN_VEC3), ("WorldPos", FN_VEC3), ("ViewPos", FN_VEC3),
         ("Scale", FN_VEC3), ("Offset", FN_VEC3), ("Rotation", FN_VEC3),
         ("Sharpness", FN_SCALAR), ("MacroScale", FN_SCALAR), ("MacroAmount", FN_SCALAR),
         ("FadeStart", FN_SCALAR), ("FadeEnd", FN_SCALAR), ("FadeColor", FN_VEC3)],
        tp_albedo_code)
    fns["normal"] = _build_mf(
        "MF_MeluTriplanar_Normal",
        "Triplanar v2 normal: RG decode + world-space whiteout blend",
        [("Tex", FN_TEX), ("Normal", FN_VEC3), ("WorldPos", FN_VEC3),
         ("Scale", FN_VEC3), ("Sharpness", FN_SCALAR), ("Strength", FN_SCALAR)],
        tp_normal_code)
    fns["quasicrystal"] = _build_mf(
        "MF_MeluSdfQuasicrystal",
        "Aperiodic quasicrystal field: nodal facet lines + contour bands + facet tint + iridescence",
        [("BaseColor", FN_VEC3), ("Normal", FN_VEC3), ("WorldPos", FN_VEC3),
         ("ViewVector", FN_VEC3), ("Mask", FN_SCALAR),
         ("Scale", FN_SCALAR), ("Folds", FN_SCALAR), ("Freq", FN_SCALAR), ("Ratio", FN_SCALAR),
         ("NodalWidth", FN_SCALAR), ("BandCount", FN_SCALAR), ("BandWidth", FN_SCALAR),
         ("FacetScale", FN_SCALAR), ("FacetTint", FN_VEC3), ("EdgeColor", FN_VEC3),
         ("IriShift", FN_SCALAR), ("IriStrength", FN_SCALAR),
         ("Phase", FN_SCALAR), ("BeatPulse", FN_SCALAR), ("Strength", FN_SCALAR)],
        qc_code)
    return fns


# ---------------------------------------------------------------------------
# Master surgery (same dynamic-anchor technique proven for the gouache wash)
# ---------------------------------------------------------------------------

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


def _inputs(material, node):
    """{pin_name: source_expression_name} for connected inputs only."""
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
            out[n] = x.get_name()
    return out


def _by_name(material, name):
    for e in _exprs(material):
        if e.get_name() == name:
            return e
    return None


def _resolve_tail(material):
    """Find the VERIFIED insertion point: the tagged feature stage that feeds the
    final BaseColor pin of the material's BSDF.

    Returns (final_node, final_pin, tail_expression). Insert a stage by feeding
    final_node.final_pin with a switch whose False branch forwards
    tail_expression - byte-identical behaviour when off, additive when on.

    This replaces an earlier anchor that assumed the August `NikkiX:SDLerp` node
    still terminated the chain. The live master had moved on (a `MelPile:`
    glitter-pile stage now ends it); that lerp is now an orphan with no inputs,
    which is exactly why this walks the live graph instead of trusting a tag.
    """
    bsdf = None
    for e in _exprs(material):
        if "SubstrateToonBSDF" in type(e).__name__ or "Substrate" in type(e).__name__:
            bsdf = e
            break
    if bsdf is None:
        raise RuntimeError("no BSDF node found to anchor the splice")
    final_name = _inputs(material, bsdf).get("BaseColor")
    if final_name is None:
        raise RuntimeError("BSDF BaseColor has no input to splice before")
    final_node = _by_name(material, final_name)
    if final_node is None:
        raise RuntimeError(f"final basecolor node not found: {final_name}")

    for pin, src_name in _inputs(material, final_node).items():
        src = _by_name(material, src_name)
        d = ""
        try:
            d = str(_get(src, "desc", "")) if src else ""
        except Exception:
            d = ""
        if d.startswith(("NikkiX:", "NikkiFeat:", "MelPile:", TAG)):
            return final_node, pin, src
    raise RuntimeError("no tagged feature stage found feeding the final basecolor pin")


def splice_quasicrystal(material, functions):
    g = "08 | Quasicrystal"

    victims = [e for e in _exprs(material) if str(_get(e, "desc", "")).startswith(TAG)]
    for e in victims:
        try:
            MEL.delete_material_expression(material, e)
        except Exception as exc:
            _log(f"cleanup {e.get_name()}: {exc}")

    final_node, final_pin, tail = _resolve_tail(material)

    sw = _switch_param(material, "bMeluQuasicrystal_Active", False, g, 1500, 200)
    _scalar_param(material, "MeluQuasicrystal_Scale", 0.55, g, 1500, 340, 0.01, 8.0)
    _scalar_param(material, "MeluQuasicrystal_Folds", 5.0, g, 1500, 400, 3.0, 12.0)
    _scalar_param(material, "MeluQuasicrystal_Freq", 9.0, g, 1500, 460, 0.1, 64.0)
    _scalar_param(material, "MeluQuasicrystal_Ratio", 0.85, g, 1500, 520, 0.0, 1.0)
    _scalar_param(material, "MeluQuasicrystal_NodalWidth", 0.035, g, 1500, 580, 0.001, 0.25)
    _scalar_param(material, "MeluQuasicrystal_BandCount", 6.0, g, 1500, 640, 1.0, 24.0)
    _scalar_param(material, "MeluQuasicrystal_BandWidth", 0.18, g, 1500, 700, 0.01, 1.0)
    _scalar_param(material, "MeluQuasicrystal_FacetScale", 3.0, g, 1500, 760, 0.1, 32.0)
    _scalar_param(material, "MeluQuasicrystal_IriShift", 0.35, g, 1500, 820, 0.0, 1.0)
    _scalar_param(material, "MeluQuasicrystal_IriStrength", 0.6, g, 1500, 880, 0.0, 1.0)
    _scalar_param(material, "MeluQuasicrystal_Strength", 0.9, g, 1500, 940, 0.0, 1.5)
    _scalar_param(material, "MeluQuasicrystal_Phase", 0.0, g, 1500, 1000, 0.0, 60.0,
                  key="MeluQuasicrystal_Phase")
    _vector_param(material, "MeluQuasicrystal_FacetTint", (0.55, 0.72, 0.95, 1), g, 1500, 300)
    _vector_param(material, "MeluQuasicrystal_EdgeColor", (0.95, 0.98, 1.0, 1), g, 1500, 360)

    call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall,
                         "QcCall", 1250, 240)
    _set(call, "material_function", functions["quasicrystal"])

    vn, _ = _mk_master(material, unreal.MaterialExpressionVertexNormalWS, "QcVN", 900, 560)
    wp, _ = _mk_master(material, unreal.MaterialExpressionWorldPosition, "QcWP", 900, 620)
    cam, _ = _mk_master(material, unreal.MaterialExpressionCameraPositionWS, "QcCam", 900, 680)
    vv, _ = _mk_master(material, unreal.MaterialExpressionCameraVectorWS, "QcVV", 900, 740)
    lum, _ = _mk_master(material, unreal.MaterialExpressionDotProduct, "QcLum", 900, 800)
    lumw, _ = _mk_master(material, unreal.MaterialExpressionConstant3Vector, "QcLumW", 900, 860)
    _set(lumw, "constant", unreal.LinearColor(0.299, 0.587, 0.114, 0))

    _connect(tail, "", call, "BaseColor")
    _connect(vn, "", call, "Normal")
    _connect(wp, "", call, "WorldPos")
    _connect(vv, "", call, "ViewVector")
    _connect(tail, "", lum, "A")
    _connect(lumw, "", lum, "B")
    _connect(lum, "", call, "Mask")
    _connect(_param(material, "MeluQuasicrystal_Scale"), "", call, "Scale")
    _connect(_param(material, "MeluQuasicrystal_Folds"), "", call, "Folds")
    _connect(_param(material, "MeluQuasicrystal_Freq"), "", call, "Freq")
    _connect(_param(material, "MeluQuasicrystal_Ratio"), "", call, "Ratio")
    _connect(_param(material, "MeluQuasicrystal_NodalWidth"), "", call, "NodalWidth")
    _connect(_param(material, "MeluQuasicrystal_BandCount"), "", call, "BandCount")
    _connect(_param(material, "MeluQuasicrystal_BandWidth"), "", call, "BandWidth")
    _connect(_param(material, "MeluQuasicrystal_FacetScale"), "", call, "FacetScale")
    _connect(_param(material, "MeluQuasicrystal_FacetTint"), "", call, "FacetTint")
    _connect(_param(material, "MeluQuasicrystal_EdgeColor"), "", call, "EdgeColor")
    _connect(_param(material, "MeluQuasicrystal_IriShift"), "", call, "IriShift")
    _connect(_param(material, "MeluQuasicrystal_IriStrength"), "", call, "IriStrength")
    _connect(_param(material, "MeluQuasicrystal_Strength"), "", call, "Strength")
    # BeatPulse is left unconnected on purpose: the Custom input defaults to 0,
    # so the quasicrystal is NOT audio-reactive until a BattleMusicClock-driven
    # MPC scalar is wired to it. Do not fake tempo with a Time node here.
    _connect(_param(material, "MeluQuasicrystal_Phase"), "", call, "Phase")

    _connect(tail, "", sw, "False")
    _connect(call, "Color", sw, "True")
    _connect(sw, "", final_node, final_pin)   # insertion at the verified tail pin

    MEL.recompile_material(material)
    _save(material)
    return True


def make_show():
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    name = "MI_Nikki_Show_Quasicrystal"
    mi = unreal.EditorAssetLibrary.load_asset(f"{SHOW_DIR}/{name}")
    if mi is None:
        mi = tools.create_asset(name, SHOW_DIR, unreal.MaterialInstanceConstant,
                                unreal.MaterialInstanceConstantFactoryNew())
    parent = unreal.EditorAssetLibrary.load_asset(f"{MASTER_DIR}/M_Master_Nikki")
    MEL.set_material_instance_parent(mi, parent)
    MEL.set_material_instance_static_switch_parameter_value(mi, "bMeluQuasicrystal_Active", True)
    MEL.set_material_instance_scalar_parameter_value(mi, "MeluQuasicrystal_Strength", 0.85)
    _save(mi)
    return f"{SHOW_DIR}/{name}"


def _save(asset):
    """Save an asset, falling back to package-level save.

    EditorAssetLibrary.desync (documented project trap: does_asset_exist returns
    False for a perfectly intact asset) also makes save_loaded_asset a silent
    no-op, which leaves freshly built functions dirty. Fall back to
    save_packages on the asset's own package, which does not consult that view.
    """
    if unreal.EditorAssetLibrary.save_loaded_asset(asset):
        return True
    try:
        pkgs = [asset.get_outer()]
        if pkgs[0] is not None:
            return bool(unreal.EditorLoadingAndSavingUtils.save_packages(pkgs, False))
    except Exception as exc:
        _log(f"save_packages fallback failed: {exc}")
    return False


def _load(path):
    """Load via EditorAssetLibrary, falling back to the global loader.

    EditorAssetLibrary.load_asset can return None for a Material that is open in
    a Material Editor tab (observed on this master); unreal.load_asset resolves
    the same path reliably. MaterialFunction loads are unaffected but go through
    the same helper for consistency.
    """
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        try:
            asset = unreal.load_asset(path)
        except Exception as exc:
            _log(f"global load failed for {path}: {exc}")
    return asset


def main(rebuild_functions: bool = True, gemstone: bool = False):
    if rebuild_functions:
        functions = build_functions()
        _log("triplanar v2 + quasicrystal functions built")
    else:
        functions = {}
        for key, name in (("albedo", "MF_MeluTriplanar_Albedo"),
                          ("normal", "MF_MeluTriplanar_Normal"),
                          ("quasicrystal", "MF_MeluSdfQuasicrystal")):
            fn = unreal.EditorAssetLibrary.load_asset(f"{FUNCTION_DIR}/{name}")
            if fn is None:
                raise RuntimeError(f"function missing: {name}")
            functions[key] = fn

    master_path = f"{MASTER_DIR}/M_Master_Nikki"
    material = _load(master_path)
    if material is None:
        raise RuntimeError(f"load failed: {master_path}")
    splice_quasicrystal(material, functions)
    _log(f"surgery complete: {master_path}")

    if gemstone:
        # Opt-in only: requires an inspected basecolor anchor on the gemstone master.
        raise NotImplementedError(
            "gemstone splice intentionally not enabled — inspect M_Master_Gemstone's "
            "basecolor anchor first, then wire it like the Nikki splice")

    show = make_show()
    payload = {
        "generated": "2026-10-10",
        "shader_source": [str(p.relative_to(ROOT)).replace("\\", "/")
                          for p in (COMMON, TRIPLANAR, QUASICRYSTAL)],
        "functions": ["MF_MeluTriplanar_Albedo", "MF_MeluTriplanar_Normal",
                      "MF_MeluSdfQuasicrystal"],
        "spliced": [f"{master_path} :: bMeluQuasicrystal_Active (group 08 | Quasicrystal)"],
        "show": show,
        "not_done": ["MF_Triplanar_Stable untouched (pin-compatible consumers preserved)",
                     "M_Master_Gemstone splice opt-in only"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _log("done")
    return payload


if __name__ == "__main__":
    main()
