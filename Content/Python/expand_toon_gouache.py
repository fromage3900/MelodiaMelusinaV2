"""Gated gouache / watercolour function on M_Master_Toon_Universal.

One default-OFF static switch (bGouache_Active) splices a tagged stage in front of the Substrate Toon
BSDF's BaseColor, Normal and Roughness pins. No new master, no PPV. Tagged nodes (ToonGouache:) make
re-runs idempotent; with the switch off every existing instance renders as before.

The BaseColor stage (Custom HLSL) is the gouache look:
  1. Cool-shifted shadows   - shadow side lerps toward a violet tint and gains saturation (never grey/black)
  2. Soft-stepped light     - wrap light, two smoothstep bands; the terminator is broken by the blotch field
                              so it bleeds like pigment wicking into paper (not hard cel)
  3. Chalk matte            - white-mixed lift in the highlight band; roughness pin pushed high
  4. Paper tooth            - low-contrast paper height modulation (Rebelle Aquarelle tile, UV space)
  5. Pigment pooling        - darker pigment at silhouette (fresnel) and along band transitions (wet edge)
  +  Granulation            - real Rebelle grain, settling in paper valleys and in shadow
  +  Bloom / backrun        - cauliflower rim from a thresholded low-frequency field; darker edge, lifted core
  +  De-tiling              - blotch is sampled twice at different scale and rotation and blended
  +  Boil (optional)        - frame-stepped UV jitter on the wet fields, a hand-painted flipbook shimmer
The Normal stage adds paper relief. The Roughness stage lifts roughness toward ChalkRoughness.

Run in the UE editor:
    import expand_toon_gouache as g; g.main()                  # build + save + recompile
    g.main(compile_now=False)                                   # defer the shader compile
Writes: Saved/Audit/Gouache/toon_universal_gouache_splice.json
"""
import json
from pathlib import Path

import unreal

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
TEX = "/Game/EnvSandbox/Materials/Textures/Gouache/"
FLIP_TEX = TEX + "T_Gouache_PoolFlipbook"      # 4x4 x 256: R wet edge | G bloom | B smooth bloom, 16-frame loop with baked swirl
PIGMENT_TEX = TEX + "T_Gouache_Pigment_RGBA"   # R paper height | G granulation (valley-derived) | B wet edge (signed) | A backrun bloom
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "Gouache" / "toon_universal_gouache_splice.json"
TAG = "ToonGouache:"
GROUP = "08 | Gouache"

MEL = unreal.MaterialEditingLibrary

GOUACHE_HLSL = """
float2 uv = UV;
float c2 = 0.8776, s2r = 0.4794;
float2 uvR = float2(uv.x * c2 - uv.y * s2r, uv.x * s2r + uv.y * c2) * DetileScale + float2(0.31, 0.17);
float stp = floor(T * BoilFPS);
float2 boil = BoilFPS > 0.0 ? float2(frac(stp * 0.318), frac(stp * 0.577)) * BoilAmount : float2(0.0, 0.0);

float2 drift = float2(sin(T * SwirlSpeed), cos(T * SwirlSpeed * 0.83)) * SwirlDrift;   // slow continuous swirl of the wash
float4 pA = Texture2DSample(Pig, PigSampler, uv + boil + drift);
float4 pB = Texture2DSample(Pig, PigSampler, uvR - drift);     // second sample: different scale + rotation breaks the tiling
float paper = pA.r;                                            // R  paper height
float gran = pA.g;                                             // G  granulation, already settled in R's valleys
float wet = (pA.b - 0.5) * 2.0;                                // B  signed wet edge: +dark rim, -lighter inner halo
float bloomF = lerp(pA.a, pB.a, 0.5);                          // A  backrun / flocculation field
// 4x4 looping flipbook (swirl baked in): wet edge + bloom animate on a material-owned clock, frame-lerped
float fr = frac(T * FlipFPS / 16.0) * 16.0;
float f0 = floor(fr);
float f1 = fmod(f0 + 1.0, 16.0);
float fa = frac(fr);
float2 fuv = frac(uv * FlipTiling + drift * 3.0);
float2 inset = fuv * (1.0 - 2.0 / 256.0) + 1.0 / 256.0;
float2 cA = (inset + float2(fmod(f0, 4.0), floor(f0 / 4.0))) * 0.25;
float2 cB = (inset + float2(fmod(f1, 4.0), floor(f1 / 4.0))) * 0.25;
float4 fl = lerp(Texture2DSample(Flip, FlipSampler, cA), Texture2DSample(Flip, FlipSampler, cB), fa);
wet = lerp(wet, (fl.r - 0.5) * 2.0, FlipAmount);
bloomF = lerp(bloomF, fl.g, FlipAmount);
float blotch = bloomF;

float3 n = normalize(N);
float3 L = normalize(KeyDir);
float ndl = dot(n, L) * 0.5 + 0.5;
ndl += (bloomF - 0.5) * BleedJitter;                           // pigment bleed: the terminator wanders with the wash
float soft = max(BandSoft, 0.001);
float s1 = smoothstep(Band1 - soft, Band1 + soft, ndl);
float s2 = smoothstep(Band2 - soft, Band2 + soft, ndl);
float lit = (s1 + s2) * 0.5;

float3 shaded = BaseColor * ShadowTint;                        // cool-shifted shadow: hue changes, it does not just darken
float lum = dot(shaded, float3(0.299, 0.587, 0.114));
shaded = lerp(float3(lum, lum, lum), shaded, 1.0 + ShadowSat);
float3 c = lerp(lerp(BaseColor, shaded, ShadowMix), BaseColor, lit);
c = lerp(c, c + (1.0 - c) * ChalkLift, s2);                    // white-mixed chalk in the light band

c *= 1.0 - GranAmount * (0.35 + 0.65 * (1.0 - lit)) * gran;   // granulation: heavier in shadow, only where the paper is low

float rim = saturate(wet);                                     // wet edge from the real wash boundaries in the map...
float halo = saturate(-wet);
float bandEdge = (s1 * (1.0 - s1) + s2 * (1.0 - s2)) * 2.0;    // ...plus a pooled line where the light bands meet
c *= 1.0 - EdgePool * (rim + 0.5 * bandEdge);
c += (1.0 - c) * EdgeHalo * halo;

float fres = pow(1.0 - saturate(dot(n, normalize(V))), PoolPower);
c *= 1.0 - PoolAmount * fres;                                  // pigment pooling at the silhouette

float bw = max(BloomSoft, 0.001);
float bl = smoothstep(BloomThresh - bw, BloomThresh + bw, blotch);
float bRim = bl * (1.0 - bl) * 4.0;
c *= 1.0 - BloomEdge * bRim;                                   // backrun: darker cauliflower rim...
c += (1.0 - c) * BloomLift * bl * 0.35;                        // ...and a lifted core
float3 washTint = lerp(float3(1.12, 0.96, 0.86), ShadowTint * 1.3, bl);   // each wash drifts warm <-> cool: colour variation inside the paint
c = lerp(c, c * washTint, saturate(BloomLift * 1.4) * (0.35 + 0.65 * bloomF));

c *= 1.0 + PaperGrain * (paper - PaperMean) * 2.0;             // paper tooth
return lerp(BaseColor, saturate(c), Strength);
"""

NORMAL_HLSL = """
float2 e = float2(TexelSize, 0.0);
float hL = Texture2DSample(Tex, TexSampler, UV - e.xy).r;
float hR = Texture2DSample(Tex, TexSampler, UV + e.xy).r;
float hD = Texture2DSample(Tex, TexSampler, UV - e.yx).r;
float hU = Texture2DSample(Tex, TexSampler, UV + e.yx).r;
float2 d = float2(hL - hR, hD - hU) * NormalStrength;
float3 n = normalize(float3(BaseNormal.xy + d, max(BaseNormal.z, 0.001)));
return lerp(BaseNormal, n, Strength);
"""

# name: (default, min, max)
SCALARS = {
    "Gouache_Strength": (1.0, 0.0, 1.5), "Gouache_UVTiling": (2.2, 0.5, 64.0),
    "Gouache_DetileScale": (0.37, 0.1, 2.0),
    "Gouache_FlipFPS": (4.0, 0.0, 24.0), "Gouache_FlipAmount": (1.0, 0.0, 1.0), "Gouache_FlipTiling": (1.2, 0.25, 16.0),
    "Gouache_SwirlSpeed": (0.15, 0.0, 2.0), "Gouache_SwirlDrift": (0.02, 0.0, 0.1),
    "Gouache_PaperMean": (0.5, 0.0, 1.0), "Gouache_PaperGrain": (0.14, 0.0, 0.5),
    "Gouache_Band1": (0.36, 0.0, 1.0), "Gouache_Band2": (0.64, 0.0, 1.0), "Gouache_BandSoft": (0.09, 0.0, 0.3),
    "Gouache_BleedJitter": (0.6, 0.0, 0.8), "Gouache_ShadowMix": (0.85, 0.0, 1.0), "Gouache_ShadowSat": (0.3, 0.0, 1.5),
    "Gouache_ChalkLift": (0.08, 0.0, 0.4), "Gouache_GranAmount": (0.95, 0.0, 1.0),
    "Gouache_EdgePool": (1.0, 0.0, 1.0), "Gouache_EdgeHalo": (0.6, 0.0, 1.0),
    "Gouache_PoolAmount": (0.55, 0.0, 1.0), "Gouache_PoolPower": (3.0, 0.5, 8.0),
    "Gouache_BloomThresh": (0.5, 0.0, 1.0), "Gouache_BloomSoft": (0.12, 0.0, 0.3),
    "Gouache_BloomEdge": (0.95, 0.0, 1.0), "Gouache_BloomLift": (0.7, 0.0, 1.0),
    "Gouache_BoilFPS": (6.0, 0.0, 24.0), "Gouache_BoilAmount": (0.015, 0.0, 0.2),
    "Gouache_NormalStrength": (0.18, 0.0, 4.0), "Gouache_TexelSize": (1.0 / 1024.0, 0.0001, 0.05),
    "Gouache_ChalkRoughness": (0.92, 0.0, 1.0),
}
VECTORS = {
    "Gouache_ShadowTint": (0.62, 0.55, 0.96, 1.0),
    "Gouache_KeyLightDir": (0.4, -0.3, 0.85, 0.0),
}


def _get(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _set(obj, name, value):
    obj.set_editor_property(name, value)


def _log(message):
    unreal.log(f"[ToonGouache] {message}")


def _exprs(material):
    return list(MEL.get_material_expressions(material) or [])


def _is_tagged(node):
    return node is not None and str(_get(node, "desc", "")).startswith(TAG)


def _find_tag(material, key):
    wanted = TAG + key
    for e in _exprs(material):
        if str(_get(e, "desc", "")) == wanted:
            return e
    return None


def _mk(material, cls, key, x, y):
    node = _find_tag(material, key)
    if node:
        return node
    node = MEL.create_material_expression(material, cls, x, y)
    _set(node, "desc", TAG + key)
    return node


def _connect(source, output, target, input_name):
    if not MEL.connect_material_expressions(source, output, target, input_name):
        raise RuntimeError(f"connect failed: {source.get_name()}:{output} -> {target.get_name()}:{input_name}")


def _inputs_of(material, node):
    try:
        names = list(MEL.get_material_expression_input_names(node))
    except Exception:
        names = []
    try:
        ins = list(MEL.get_inputs_for_material_expression(material, node))
    except Exception:
        ins = []
    return {n: ins[i] for i, n in enumerate(names) if i < len(ins) and ins[i] is not None}


def _scalar(material, name, default, x, y, smin=None, smax=None):
    node = _mk(material, unreal.MaterialExpressionScalarParameter, name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", GROUP)
    _set(node, "default_value", float(default))
    if smin is not None:
        _set(node, "slider_min", float(smin))
    if smax is not None:
        _set(node, "slider_max", float(smax))
    return node


def _vector(material, name, rgba, x, y):
    node = _mk(material, unreal.MaterialExpressionVectorParameter, name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", GROUP)
    _set(node, "default_value", unreal.LinearColor(*rgba))
    return node


def _switch(material, key, x, y):
    node = _mk(material, unreal.MaterialExpressionStaticSwitchParameter, key, x, y)
    _set(node, "parameter_name", "bGouache_Active")
    _set(node, "group", GROUP)
    _set(node, "default_value", False)
    return node


def _texture(material, name, path, x, y):
    node = _mk(material, unreal.MaterialExpressionTextureObjectParameter, name, x, y)
    tex = unreal.EditorAssetLibrary.load_asset(path)
    if tex is None:
        raise RuntimeError(f"texture missing: {path}")
    _set(node, "parameter_name", name)
    _set(node, "group", GROUP)
    _set(node, "texture", tex)
    _set(node, "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    return node


def _custom(material, key, code, input_names, out_type, x, y):
    node = _mk(material, unreal.MaterialExpressionCustom, key, x, y)
    _set(node, "description", "Gouache stage (" + key + ")")
    _set(node, "code", code)
    _set(node, "output_type", out_type)
    ci = []
    for iname in input_names:
        c = unreal.CustomInput()
        _set(c, "input_name", iname)
        ci.append(c)
    _set(node, "inputs", ci)
    return node


def _original(material, bsdf, pin):
    """What fed `pin` before our splice (looks through our own switch on re-runs)."""
    cur = _inputs_of(material, bsdf).get(pin)
    if _is_tagged(cur):
        return _inputs_of(material, cur).get("False")
    return cur


def splice(material):
    bsdf = next((e for e in _exprs(material) if type(e).__name__ == "MaterialExpressionSubstrateToonBSDF"), None)
    if bsdf is None:
        raise RuntimeError("no SubstrateToonBSDF found to anchor the splice")
    orig = {pin: _original(material, bsdf, pin) for pin in ("BaseColor", "Normal", "Roughness")}
    if any(v is None for v in orig.values()):
        raise RuntimeError(f"BSDF pin has no source to splice in front of: {orig}")

    for pin, src in orig.items():                 # restore untouched wiring, then drop only our tagged nodes
        _connect(src, "", bsdf, pin)
    # Never delete expressions from Python: deleting a tagged node asserted `!IsRooted()` and crashed the editor
    # (2026-10-22). Retag the previous generation as inert legacy instead; orphans compile out. Sweep them in a
    # closed-editor session.
    for e in [e for e in _exprs(material) if _is_tagged(e)]:
        _set(e, "desc", "ToonGouacheLegacy#" + str(_get(e, "desc", "")).split(":", 1)[-1])

    pos = MEL.get_material_expression_node_position(bsdf)
    x0, y0 = int(pos[0]) - 1800, int(pos[1]) + 1800

    sw = {p: _switch(material, "Sw" + p, x0 + 1500, y0 + i * 300) for i, p in enumerate(("BaseColor", "Normal", "Roughness"))}
    sc = {}
    for i, (name, (d, lo, hi)) in enumerate(SCALARS.items()):
        sc[name] = _scalar(material, name, d, x0, y0 - 1600 + i * 100, lo, hi)
    vc = {name: _vector(material, name, v, x0 + 300, y0 - 1600 + i * 100) for i, (name, v) in enumerate(VECTORS.items())}
    pig = _texture(material, "Gouache_PigmentTex", PIGMENT_TEX, x0 + 300, y0 + 600)
    flip = _texture(material, "Gouache_FlipTex", FLIP_TEX, x0 + 300, y0 + 700)

    tc = _mk(material, unreal.MaterialExpressionTextureCoordinate, "UV", x0, y0 + 900)
    uv = _mk(material, unreal.MaterialExpressionMultiply, "UVMul", x0 + 300, y0 + 900)
    _connect(tc, "", uv, "A")
    _connect(sc["Gouache_UVTiling"], "", uv, "B")
    vn = _mk(material, unreal.MaterialExpressionVertexNormalWS, "N", x0, y0 + 1000)
    cam = _mk(material, unreal.MaterialExpressionCameraVectorWS if hasattr(unreal, "MaterialExpressionCameraVectorWS")
              else unreal.MaterialExpressionCameraVector, "V", x0, y0 + 1100)
    tm = _mk(material, unreal.MaterialExpressionTime, "T", x0, y0 + 1200)

    g_inputs = ["Pig", "Flip", "UV", "BaseColor", "N", "V", "T", "KeyDir",
                "DetileScale", "FlipFPS", "FlipAmount", "FlipTiling", "SwirlSpeed", "SwirlDrift", "BoilFPS", "BoilAmount", "Band1", "Band2", "BandSoft", "BleedJitter",
                "ShadowTint", "ShadowSat", "ShadowMix", "ChalkLift", "GranAmount", "EdgePool", "EdgeHalo",
                "PoolPower", "PoolAmount", "BloomThresh", "BloomSoft", "BloomEdge", "BloomLift",
                "PaperGrain", "PaperMean", "Strength"]
    g = _custom(material, "Gouache", GOUACHE_HLSL, g_inputs, unreal.CustomMaterialOutputType.CMOT_FLOAT3, x0 + 900, y0)
    wires = {"Pig": pig, "Flip": flip, "UV": uv, "BaseColor": orig["BaseColor"],
             "N": vn, "V": cam, "T": tm, "KeyDir": vc["Gouache_KeyLightDir"], "ShadowTint": vc["Gouache_ShadowTint"]}
    for inp in g_inputs:
        src = wires.get(inp) or sc.get("Gouache_" + inp)
        _connect(src, "", g, inp)

    n = _custom(material, "Normal", NORMAL_HLSL,
                ["Tex", "UV", "BaseNormal", "NormalStrength", "TexelSize", "Strength"],
                unreal.CustomMaterialOutputType.CMOT_FLOAT3, x0 + 900, y0 + 300)
    for pin, src in (("Tex", pig), ("UV", uv), ("BaseNormal", orig["Normal"]),
                     ("NormalStrength", sc["Gouache_NormalStrength"]), ("TexelSize", sc["Gouache_TexelSize"]),
                     ("Strength", sc["Gouache_Strength"])):
        _connect(src, "", n, pin)

    rough = _mk(material, unreal.MaterialExpressionLinearInterpolate, "RoughLerp", x0 + 900, y0 + 600)
    _connect(orig["Roughness"], "", rough, "A")
    _connect(sc["Gouache_ChalkRoughness"], "", rough, "B")
    _connect(sc["Gouache_Strength"], "", rough, "Alpha")

    for pin, on in (("BaseColor", g), ("Normal", n), ("Roughness", rough)):
        _connect(orig[pin], "", sw[pin], "False")
        _connect(on, "", sw[pin], "True")
        _connect(sw[pin], "", bsdf, pin)
    return bsdf


UDW_MPC = "/Game/UltraDynamicSky/Materials/Weather/UltraDynamicWeather_Parameters"   # written by UDS itself every tick
LIVE_MPC = "/Game/EnvSandbox/Materials/Functions/MPC_Gouache_Live"                   # keyframe-only multipliers (Sequencer MPC track); NOT a palette
LIVE_MULS = ["Mul_Strength", "Mul_Bleed", "Mul_Gran", "Mul_EdgePool", "Mul_Bloom", "Mul_FlipSpeed", "Mul_Swirl", "Mul_Boil"]
LIVE_SCALARS = {
    "Gouache_SunFollow": (1.0, 0.0, 1.0),        # 0 = fixed Gouache_KeyLightDir, 1 = follow the UDS sun
    "Gouache_SunSign": (-1.0, -1.0, 1.0),        # UDS 'Sun Vector' is the direction the light travels; toward-sun = -1 * it
    "Gouache_WetBleedGain": (2.0, 0.0, 8.0),     # UDS 'Wet' raises bleed: wet paper bleeds more
    "Gouache_WindSwirlGain": (1.5, 0.0, 8.0),    # UDS 'Wind Intensity' speeds the swirl
    "Gouache_WindFlipGain": (0.5, 0.0, 4.0),     # ...and the flipbook rate
}


def ensure_live_mpc():
    """Create MPC_Gouache_Live once (all multipliers default 1.0 = no change). Sole writer: Sequencer/Blueprint tracks."""
    mpc = unreal.EditorAssetLibrary.load_asset(LIVE_MPC)
    if mpc is None:
        folder, name = LIVE_MPC.rsplit("/", 1)
        mpc = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, folder, unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
        params = []
        for n in LIVE_MULS:
            p = unreal.CollectionScalarParameter()
            p.set_editor_property("parameter_name", n)
            p.set_editor_property("default_value", 1.0)
            params.append(p)
        mpc.set_editor_property("scalar_parameters", params)
        unreal.EditorAssetLibrary.save_loaded_asset(mpc)
        _log(f"created {LIVE_MPC}")
    return mpc


def wire_live(material):
    """Sun-driven key light, weather-driven bleed/swirl and keyframe multipliers. connect()-only: no node is deleted."""
    gnode = _find_tag(material, "Gouache")
    if gnode is None:
        raise RuntimeError("Gouache custom node not found: run splice() first")
    # HARD LIMIT: a material may reference at most 2 MaterialParameterCollections, and this master already uses
    # MPC_Melodia_Palette. So the only extra collection allowed here is UDS's own (sun / wet / wind). A third
    # (MPC_Gouache_Live) failed every gouache-ON permutation on 2026-10-22: global keyframe multipliers must
    # live in an EXISTING collection (owner decision) or be keyframed per-instance, not in a new MPC.
    udw = unreal.EditorAssetLibrary.load_asset(UDW_MPC)
    if udw is None:
        raise RuntimeError(f"missing {UDW_MPC}")
    for name, (d, lo, hi) in LIVE_SCALARS.items():
        _scalar(material, name, d, 0, 2600, lo, hi)

    def cp(key, mpc, pname, x, y):
        n = _mk(material, unreal.MaterialExpressionCollectionParameter, key, x, y)
        _set(n, "collection", mpc)
        _set(n, "parameter_name", pname)
        return n

    def mul(key, a, b, x, y):
        n = _mk(material, unreal.MaterialExpressionMultiply, key, x, y)
        _connect(a, "", n, "A")
        _connect(b, "", n, "B")
        return n

    def par(name):
        n = _find_tag(material, name)
        if n is None:
            raise RuntimeError(f"param node missing: {name}")
        return n

    x0 = -3000
    wet = cp("LiveWet", udw, "Wet", x0, 2700)
    wind = cp("LiveWind", udw, "Wind Intensity", x0, 2800)
    one = _mk(material, unreal.MaterialExpressionConstant, "One", x0, 2900)
    _set(one, "r", 1.0)
    # 1 + Wet * gain ; 1 + Wind * gain
    wet1 = _mk(material, unreal.MaterialExpressionAdd, "WetFactor", x0 + 600, 2700)
    _connect(mul("WetGain", wet, par("Gouache_WetBleedGain"), x0 + 300, 2700), "", wet1, "A")
    _connect(one, "", wet1, "B")
    wnd_s = _mk(material, unreal.MaterialExpressionAdd, "WindSwirlFactor", x0 + 600, 2800)
    _connect(mul("WindSwirlGain", wind, par("Gouache_WindSwirlGain"), x0 + 300, 2800), "", wnd_s, "A")
    _connect(one, "", wnd_s, "B")
    wnd_f = _mk(material, unreal.MaterialExpressionAdd, "WindFlipFactor", x0 + 600, 2900)
    _connect(mul("WindFlipGain", wind, par("Gouache_WindFlipGain"), x0 + 300, 2900), "", wnd_f, "A")
    _connect(one, "", wnd_f, "B")

    def drive(input_name, param, extra=None):
        v = par(param) if extra is None else mul("N_" + input_name, par(param), extra, x0 + 1200, 3000)
        _connect(v, "", gnode, input_name)

    drive("Strength", "Gouache_Strength")
    drive("BleedJitter", "Gouache_BleedJitter", wet1)       # wet paper bleeds more (UDS Wet)
    drive("GranAmount", "Gouache_GranAmount")
    drive("EdgePool", "Gouache_EdgePool")
    drive("BloomEdge", "Gouache_BloomEdge")
    drive("FlipFPS", "Gouache_FlipFPS", wnd_f)              # wind quickens the flipbook (UDS Wind Intensity)
    drive("SwirlSpeed", "Gouache_SwirlSpeed", wnd_s)        # ...and the swirl
    drive("BoilAmount", "Gouache_BoilAmount")

    # key light: lerp(fixed KeyLightDir, -UDS Sun Vector, SunFollow). float4 -> float3 via ComponentMask.
    def rgb(key, src, x, y):
        m = _mk(material, unreal.MaterialExpressionComponentMask, key, x, y)
        _set(m, "r", True)
        _set(m, "g", True)
        _set(m, "b", True)
        _set(m, "a", False)
        _connect(src, "", m, "")
        return m

    sun = rgb("SunRGB", cp("LiveSun", udw, "Sun Vector", x0, 3100), x0 + 300, 3100)
    sun_dir = mul("SunDir", sun, par("Gouache_SunSign"), x0 + 600, 3100)
    fixed = rgb("FixedRGB", par("Gouache_KeyLightDir"), x0 + 300, 3200)
    key = _mk(material, unreal.MaterialExpressionLinearInterpolate, "KeyLerp", x0 + 900, 3150)
    _connect(fixed, "", key, "A")
    _connect(sun_dir, "", key, "B")
    _connect(par("Gouache_SunFollow"), "", key, "Alpha")
    _connect(key, "", gnode, "KeyDir")
    return gnode


def main(compile_now: bool = True):
    material = unreal.EditorAssetLibrary.load_asset(MASTER)
    if material is None:
        raise RuntimeError(f"load failed: {MASTER}")
    splice(material)
    wire_live(material)
    if compile_now:
        MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    payload = {"master": MASTER, "tag": TAG, "switch": "bGouache_Active", "compiled": bool(compile_now),
               "textures": [PIGMENT_TEX],
               "stages": ["BaseColor: shadow hue, soft bands + bleed, chalk, granulation, wet edge, pooling, bloom, paper, boil",
                          "Normal: paper relief", "Roughness: chalk matte"],
               "scalar_params": sorted(SCALARS), "vector_params": sorted(VECTORS)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _log(f"splice saved (compiled={compile_now}): {MASTER}")
    return payload


if __name__ == "__main__":
    main()
