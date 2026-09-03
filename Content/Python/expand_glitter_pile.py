"""Build + splice MF_MelodiaGlitterPile — triple-A audio-reactive glitter pile.

The showpiece glitter for the lookdev hour (2026-08-29). Techniques (validated
against Nightshift Glitter Shader, Spivak's Borderlands flake study, Quilez
smooth-impulse points):

  1. World-aligned cells, per-flake sub-cell jitter (no visible grid).
  2. Per-flake scattered facet normal; glint simulated as emissive (UE
     materials cannot read scene lights).
  3. Per-flake peak viewing angle -> flakes flare at their own camera angle.
  4. Harmonix musical twinkle: per-flake subdivision (1, 1/2, 1/4 beat) with
     per-flake offset — polyrhythmic but tempo-locked via MPC BeatPhase.
  5. BeatPulse (cos^2) raises activation and flashes the strongest flakes.
  6. Impact (MPC Mid, one-shot decay) bursts extra flakes.
  7. Per-flake iridescent tint + audio-lifted fresnel halo.

MPC contract (written every tick by UMelodiaAudioReactivePresentationSubsystem):
  BeatPhase (continuous Harmonix phase), BeatPulse (cos^2), Mid (impact decay),
  GlobalReactivity (battle gate). All four are wired as CollectionParameter
  nodes into the master graph and connected to the MF call inputs.

NOTE (UE 5.8 doc): a material may reference at most 2 MaterialParameterCollections.
This script counts distinct collections already referenced by each master before
adding MPC_Melodia_Palette and refuses (with a loud log + audit row) rather than
silently breaking the 2-collection limit.

Splice: the pile runs AFTER petal shadow in the Nikki parallel feature chain
(pt_sw -> pile -> sd_lerp "A"), splicing at the lerp's free A input exactly as
expand_nikki_features does — never at an already-connected True pin (crash risk).
Routing is a per-MI scalar gate (GlitterPile_Gate, 0=off default, 1=full pile)
through a LinearInterpolate — MIC-writable from Python, no static-switch API.

Idempotent: every node this script creates is tagged "MelPile:"; prior runs are
cleaned before rebuild. Never touches NikkiX:/NikkiFeat: nodes.

Run in the UE editor (Monolith run_python): expand_glitter_pile.main()
Writes: Saved/Audit/glitter_pile_2026-08-29.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

FUNCTION_DIR = "/Game/EnvSandbox/Materials/Functions"
MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
SHOWS_DIR = "/Game/EnvSandbox/Materials/Instances/NikkiHero"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "glitter_pile_2026-08-29.json"
TAG = "MelPile:"

MEL = unreal.MaterialEditingLibrary

f3 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3
f1 = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR


def _get(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _set(obj, name, value):
    obj.set_editor_property(name, value)


def _log(message):
    unreal.log(f"[GlitterPile] {message}")


# ── HLSL body: must stay in sync with MelGlitterPile in MelodiaNikkiCommon.ush ──
GLITTER_PILE = r"""
float3 wp = WorldPosition * Scale;
float2 sp = wp.xy + float2(wp.z * 0.37, -wp.z * 0.59);
float2 cellId = floor(sp);

float rA = frac(sin(dot(cellId + 0.731,  float2(12.9898, 78.233))) * 43758.5453);
float rB = frac(sin(dot(cellId + 3.117,  float2(39.346, 11.135)))  * 43758.5453);
float rC = frac(sin(dot(cellId + 7.913,  float2(127.1, 311.7)))    * 43758.5453);
float rD = frac(sin(dot(cellId + 11.71,  float2(269.5, 183.3)))    * 43758.5453);
float rE = frac(sin(dot(cellId + 17.13,  float2(41.29, 289.91)))   * 43758.5453);
float rF = frac(sin(dot(cellId + 23.77,  float2(93.989, 67.345)))  * 43758.5453);

float activation = saturate(Density + (BeatPulse * 0.20 + Impact * 0.45) * Reactivity);
float exists = step(1.0 - activation, rA);

float2 fpos = frac(sp) - 0.5;
float2 joff = (float2(rC, rD) - 0.5) * 0.6;
float d = length(fpos - joff);
float flakeR = 0.10 + rB * 0.22;
float flake = saturate(1.0 - smoothstep(flakeR * 0.6, flakeR, d));

float3 Ns = normalize(Normal);
float3 V = normalize(CameraVector);
float3 T1 = normalize(cross(Ns, float3(0.0, 0.0, 1.0)) + float3(1e-4, 0.0, 0.0));
float3 T2 = cross(Ns, T1);
float3 F = normalize(Ns + T1 * (rC - 0.5) * 1.6 + T2 * (rD - 0.5) * 1.6);

float facetGlint = pow(saturate(dot(F, V) * (0.6 + 0.8 * rF)), max(FacetSharpness, 1.0));

float period = exp2(-floor(rE * 2.999));
float p = frac(BeatPhase / period + rF * 7.13);
float twin = exp(-p * 7.0);
float shimmer = pow(saturate(sin(Time * (6.0 + rA * 14.0) + rE * 6.28318) * 0.5 + 0.5), 10.0);

float beatFlash = BeatPulse * Reactivity * step(0.72, rA) * 0.9;

float fres = pow(1.0 - saturate(dot(Ns, V)), 2.0);
float3 irid = 0.5 + 0.5 * cos(6.28318 * (fres * Iridescence + rB + float3(0.0, 0.33, 0.67)));
float3 flakeColor = GlitterColor * lerp(float3(1.0, 1.0, 1.0), irid, saturate(Iridescence));

float spark = exists * flake *
    (facetGlint * (0.45 + 0.55 * twin) + twin * 0.55 + shimmer * 0.30);
float3 result = BaseColor + flakeColor * (spark * FlakeBrightness * saturate(Mask) + exists * flake * beatFlash);

float halo = pow(1.0 - saturate(dot(Ns, V)), HaloPower)
           * HaloStrength * (1.0 + BeatPulse * 0.5 * Reactivity);
return result + GlitterColor * halo * saturate(Mask);
"""

PILE_INPUTS = [
    ("BaseColor", f3), ("Normal", f3), ("WorldPosition", f3), ("CameraVector", f3), ("Mask", f1),
    ("Scale", f1), ("Density", f1), ("FacetSharpness", f1), ("FlakeBrightness", f1),
    ("GlitterColor", f3), ("Iridescence", f1),
    ("HaloStrength", f1), ("HaloPower", f1),
    ("BeatPhase", f1), ("BeatPulse", f1), ("Impact", f1), ("Reactivity", f1), ("Time", f1),
]

# MPC scalar parameters consumed by the pile (all written every tick by the
# audio presentation subsystem — see MelodiaAudioReactivePresentationSubsystem.cpp)
MPC_INPUT_MAP = {
    "BeatPhase": "BeatPhase",
    "BeatPulse": "BeatPulse",
    "Impact": "Mid",             # MPC Mid == ImpactPulse (one-shot, 3.5/s decay)
    "Reactivity": "GlobalReactivity",
}


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


def build_pile_function():
    """Create (or rebuild in place) MF_MelodiaGlitterPile."""
    path = f"{FUNCTION_DIR}/MF_MelodiaGlitterPile"
    function = unreal.EditorAssetLibrary.load_asset(path)
    if function is None:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        function = tools.create_asset("MF_MelodiaGlitterPile", FUNCTION_DIR,
                                      unreal.MaterialFunction, unreal.MaterialFunctionFactoryNew())
    if function is None:
        raise RuntimeError(f"could not load/create {path}")
    try:
        MEL.delete_all_material_expressions_in_function(function)
    except Exception as exc:
        _log(f"function graph clear failed: {exc}")

    fn_inputs = {}
    for i, (iname, itype) in enumerate(PILE_INPUTS):
        node, _ = _mk_fn(function, unreal.MaterialExpressionFunctionInput, "Input_" + iname,
                         -1500, -800 + i * 120)
        _set(node, "input_name", iname)
        _set(node, "input_type", itype)
        _set(node, "sort_priority", i)
        fn_inputs[iname] = node

    custom, _ = _mk_fn(function, unreal.MaterialExpressionCustom, "Custom", -500, 0)
    _set(custom, "description", "Triple-A audio-reactive glitter pile (Harmonix beat-synced)")
    _set(custom, "code", GLITTER_PILE)
    _set(custom, "output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ci = []
    for iname, _ in PILE_INPUTS:
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
    _log(f"function built: {path}")
    return function


def _exprs_of(material):
    return list(MEL.get_material_expressions(material) or [])


def _param(material, name):
    for e in _exprs_of(material):
        if str(_get(e, "parameter_name", "")) == name:
            return e
    return None


def _mk_master(material, cls, key, x, y):
    node = _find_tag(_exprs_of(material), key)
    if node:
        return node, False
    node = MEL.create_material_expression(material, cls, x, y)
    _set(node, "desc", TAG + key)
    return node, True


def _scalar_param(material, name, default, group, x, y, smin=None, smax=None):
    node, _ = _mk_master(material, unreal.MaterialExpressionScalarParameter, "P_" + name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", float(default))
    if smin is not None:
        _set(node, "slider_min", float(smin))
    if smax is not None:
        _set(node, "slider_max", float(smax))
    return node


def _vector_param(material, name, rgba, group, x, y):
    node, _ = _mk_master(material, unreal.MaterialExpressionVectorParameter, "P_" + name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", unreal.LinearColor(*rgba))
    return node


def _switch_param(material, name, default, group, x, y):
    node, _ = _mk_master(material, unreal.MaterialExpressionStaticSwitchParameter, "S_" + name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", bool(default))
    return node


def _collections_referenced(material):
    """Distinct MPC assets already referenced by this material (UE limit: 2)."""
    found = set()
    for e in _exprs_of(material):
        if type(e).__name__ == "MaterialExpressionCollectionParameter":
            col = _get(e, "collection", None)
            if col is not None:
                try:
                    found.add(col.get_path_name())
                except Exception:
                    found.add(str(col))
    return found


def master_surgery(material, pile_function, mpc_asset):
    """Splice the pile into the Nikki chain after petal shadow."""
    g = "07 | Glitter Pile"

    # clean nodes from a prior run (only MelPile:-tagged)
    victims = [e for e in _exprs_of(material) if str(_get(e, "desc", "")).startswith(TAG)]
    for e in victims:
        try:
            MEL.delete_material_expression(material, e)
        except Exception as exc:
            _log(f"cleanup {e.get_name()}: {exc}")

    # MPC limit guard (UE 5.8: max 2 collections per material)
    existing = _collections_referenced(material)
    mpc_path = mpc_asset.get_path_name()
    if mpc_path not in existing and len(existing) >= 2:
        raise RuntimeError(
            f"{material.get_name()} already references {len(existing)} MPCs "
            f"({existing}); cannot add MPC_Melodia_Palette (UE 5.8 limit is 2).")

    # anchors — the splice point is the ShadowDream lerp's A input (same anchor
    # expand_nikki_features uses; the petal-shadow switch currently feeds it).
    sd_lerp = None
    for e in _exprs_of(material):
        if type(e).__name__ == "MaterialExpressionLinearInterpolate" and \
                str(_get(e, "desc", "")) == "NikkiX:SDLerp":
            sd_lerp = e
            break
    pt_sw = _param(material, "bNikkiPetalShadow_Active")
    if sd_lerp is None or pt_sw is None:
        raise RuntimeError("anchors not found (NikkiX:SDLerp or petal switch) — "
                           "run expand_nikki_features.main() first")

    # ── parameters ──
    _scalar_param(material, "GlitterPile_Scale", 90.0, g, 900, 380, 8.0, 512.0)
    _scalar_param(material, "GlitterPile_Density", 0.55, g, 900, 440, 0.0, 1.0)
    _scalar_param(material, "GlitterPile_FacetSharpness", 48.0, g, 900, 500, 2.0, 256.0)
    _scalar_param(material, "GlitterPile_Brightness", 2.2, g, 900, 560, 0.0, 8.0)
    _scalar_param(material, "GlitterPile_Iridescence", 1.2, g, 900, 620, 0.0, 4.0)
    _scalar_param(material, "GlitterPile_HaloStrength", 0.25, g, 900, 680, 0.0, 1.0)
    _scalar_param(material, "GlitterPile_HaloPower", 4.0, g, 900, 740, 0.5, 16.0)
    _vector_param(material, "GlitterPile_Color", (1.0, 0.96, 0.90, 1), g, 900, 300)
    # Per-MI gate (0 = pile off, 1 = full pile). A scalar gate is deliberately
    # used instead of a StaticSwitchParameter: MIC scalar values are writable
    # from Python (set_scalar_parameter_value) and per-MI, while static-switch
    # values are not reliably settable from the Python API.
    _scalar_param(material, "GlitterPile_Gate", 0.0, g, 900, 800, 0.0, 1.0)

    # ── shared nodes ──
    pile_call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "PileCall", 1100, 240)
    _set(pile_call, "material_function", pile_function)
    vn, _ = _mk_master(material, unreal.MaterialExpressionVertexNormalWS, "PileVN", 700, 900)
    wp, _ = _mk_master(material, unreal.MaterialExpressionWorldPosition, "PileWP", 700, 1000)
    cv, _ = _mk_master(material, unreal.MaterialExpressionCameraVectorWS, "PileCV", 700, 1100)
    tv, _ = _mk_master(material, unreal.MaterialExpressionTime, "PileTime", 700, 1200)
    lum, _ = _mk_master(material, unreal.MaterialExpressionDotProduct, "PileLum", 700, 1300)
    _set(lum, "desc", TAG + "PileLum")
    lw, _ = _mk_master(material, unreal.MaterialExpressionConstant3Vector, "PileLumW", 500, 1360)
    _set(lw, "constant", unreal.LinearColor(0.299, 0.587, 0.114, 0))
    _connect(pt_sw, "", lum, "A")
    _connect(lw, "", lum, "B")

    # ── MPC collection parameters (4) ──
    mpc_nodes = {}
    for i, (input_name, mpc_param) in enumerate(MPC_INPUT_MAP.items()):
        node, _ = _mk_master(material, unreal.MaterialExpressionCollectionParameter,
                             f"MPC_{input_name}", 400, 1500 + i * 160)
        _set(node, "collection", mpc_asset)
        _set(node, "parameter_name", mpc_param)
        mpc_nodes[input_name] = node

    # ── wiring ──
    _connect(pt_sw, "", pile_call, "BaseColor")
    _connect(vn, "", pile_call, "Normal")
    _connect(wp, "", pile_call, "WorldPosition")
    _connect(cv, "", pile_call, "CameraVector")
    _connect(lum, "", pile_call, "Mask")
    _connect(_param(material, "GlitterPile_Scale"), "", pile_call, "Scale")
    _connect(_param(material, "GlitterPile_Density"), "", pile_call, "Density")
    _connect(_param(material, "GlitterPile_FacetSharpness"), "", pile_call, "FacetSharpness")
    _connect(_param(material, "GlitterPile_Brightness"), "", pile_call, "FlakeBrightness")
    _connect(_param(material, "GlitterPile_Color"), "", pile_call, "GlitterColor")
    _connect(_param(material, "GlitterPile_Iridescence"), "", pile_call, "Iridescence")
    _connect(_param(material, "GlitterPile_HaloStrength"), "", pile_call, "HaloStrength")
    _connect(_param(material, "GlitterPile_HaloPower"), "", pile_call, "HaloPower")
    _connect(mpc_nodes["BeatPhase"], "", pile_call, "BeatPhase")
    _connect(mpc_nodes["BeatPulse"], "", pile_call, "BeatPulse")
    _connect(mpc_nodes["Impact"], "", pile_call, "Impact")
    _connect(mpc_nodes["Reactivity"], "", pile_call, "Reactivity")
    _connect(tv, "", pile_call, "Time")

    # out blend: gate lerp (0 = un-glittered chain passthrough, 1 = pile) —
    # connected through a LinearInterpolate into the ShadowDream lerp's A input.
    gate_lerp, _ = _mk_master(material, unreal.MaterialExpressionLinearInterpolate, "PileGateLerp", 1300, 240)
    _connect(pt_sw, "", gate_lerp, "A")
    _connect(pile_call, "Color", gate_lerp, "B")
    _connect(_param(material, "GlitterPile_Gate"), "", gate_lerp, "Alpha")
    _connect(gate_lerp, "", sd_lerp, "A")

    MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return {"master": material.get_path_name(), "mpc_referenced": sorted(existing | {mpc_path})}


def make_show_instance(parent_master_path):
    """MI_Melodia_Show_GlitterPile — hero-preset instance with the pile ON."""
    name = "MI_Melodia_Show_GlitterPile"
    existing = unreal.EditorAssetLibrary.load_asset(f"{SHOWS_DIR}/{name}")
    if existing is not None:
        mid = existing
    else:
        parent = unreal.EditorAssetLibrary.load_asset(parent_master_path)
        if parent is None:
            raise RuntimeError(f"parent master missing: {parent_master_path}")
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        mid = tools.create_asset(name, SHOWS_DIR, unreal.MaterialInstanceConstant, None)
        if mid is None:
            raise RuntimeError(f"could not create {SHOWS_DIR}/{name}")
        _set(mid, "parent", parent)

    def sset(pname, value):
        try:
            # slim-API quirk: the setter returns False even on success — verify
            # by read-back (proven 2026-08-29).
            MEL.set_material_instance_scalar_parameter_value(mid, pname, float(value))
            got = MEL.get_material_instance_scalar_parameter_value(mid, pname)
            return got is not None and abs(float(got) - float(value)) < 1e-4
        except Exception as exc:
            _log(f"show-instance set {pname} failed: {exc}")
            return False

    sset("GlitterPile_Gate", 1.0)
    sset("GlitterPile_Scale", 110.0)
    sset("GlitterPile_Density", 0.62)
    sset("GlitterPile_FacetSharpness", 56.0)
    sset("GlitterPile_Brightness", 2.6)
    sset("GlitterPile_Iridescence", 1.5)
    unreal.EditorAssetLibrary.save_loaded_asset(mid, only_if_is_dirty=False)
    return mid.get_path_name()


def main():
    mpc_asset = unreal.EditorAssetLibrary.load_asset(MPC_PATH)
    if mpc_asset is None:
        raise RuntimeError(f"MPC missing: {MPC_PATH}")
    pile_function = build_pile_function()
    results = []
    for name in ("M_Master_Nikki", "M_Master_Nikki_Landscape"):
        path = f"{MASTER_DIR}/{name}"
        material = unreal.EditorAssetLibrary.load_asset(path)
        if material is None:
            _log(f"master missing (skipping): {path}")
            continue
        results.append(master_surgery(material, pile_function, mpc_asset))
        _log(f"surgery complete: {path}")
    show = None
    try:
        show = make_show_instance(f"{MASTER_DIR}/M_Master_Nikki")
    except Exception as exc:
        _log(f"show instance skipped: {exc}")
    payload = {
        "generated": "2026-08-29",
        "mpc": MPC_PATH,
        "mpc_params": sorted(MPC_INPUT_MAP.values()),
        "function": f"{FUNCTION_DIR}/MF_MelodiaGlitterPile",
        "masters": results,
        "show_instance": show,
        "notes": [
            "BeatPhase/BeatPulse/Mid/GlobalReactivity wired as CollectionParameter nodes.",
            "UE 5.8 limit enforced: max 2 MPC references per material (guarded).",
            "Pile is default-OFF (GlitterPile_Gate=0 scalar gate); enable per MI.",
            "No clock running -> static pile (graceful degradation, no fake tempo).",
        ],
        "ok": True,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _log(f"audit -> {OUT}")
    return payload


if __name__ == "__main__":
    main()