"""Dreamprint — build M_PP_MelodiaInk master + profile MIs.

One post-process master (After Tonemapping) that carries the whole printed
music-box ink family: Ben-Day halftone, hatch lines, print misregistration,
paper grain, sync-vision pulse, motion smear. Every effect is a float gate
(0/1) so profile instances can dial the stack per world without touching the
graph. Audio reactivity reads unique MPC globals (BeatPulse/ComboNormalized/
EnemyTension/BreakPulse/VictoryPulse from MPC_Melodia_Palette, Ink* from
MPC_MelodiaInk) — no collection nodes needed, matching the proven grade
master pattern.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib

MASTER_FOLDER = "/Game/Melodia/_PROJECT/04_Materials/PostProcess"
MASTER_NAME = "M_PP_MelodiaInk"
MASTER_PATH = lib.asset_path(MASTER_FOLDER, MASTER_NAME)
PROFILE_FOLDER = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles"
GRADE_DONOR = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dreamprint_material_build.json"
GROUP = "Dreamprint"

SCALAR_PARAMS = [
    ("InkDotPitch", 0.015, 0.002, 0.08),
    ("InkDotAngle", 45.0, 0.0, 180.0),
    ("InkDotLumaDrive", 0.6, 0.0, 1.0),
    ("InkDotScale", 1.0, 0.2, 3.0),
    ("InkHatchDensity", 6.0, 1.0, 24.0),
    ("InkHatchAngle", 0.0, 0.0, 180.0),
    ("InkHatchShadowBand", 1.0, 0.0, 2.0),
    ("InkStrength", 0.65, 0.0, 1.5),
    ("InkPrintOffset", 0.0, 0.0, 1.0),
    ("InkPrintOffsetDepth", 0.5, 0.0, 1.0),
    ("InkGrain", 0.10, 0.0, 0.5),
    ("InkGrainScale", 3.0, 0.5, 12.0),
    ("InkSmear", 0.3, 0.0, 1.0),
    ("InkPaperLight", 1.0, 0.0, 1.0),
    ("InkPaperShadow", 0.65, 0.0, 1.0),
    ("InkHalftone", 1.0, 0.0, 1.0),
    ("InkHatch", 1.0, 0.0, 1.0),
    ("InkPrintShift", 0.0, 0.0, 1.0),
    ("InkGrainOn", 1.0, 0.0, 1.0),
    ("InkSmearOn", 0.0, 0.0, 1.0),
]

VECTOR_PARAMS = [
    ("InkColor", (0.05, 0.07, 0.12, 1.0)),
    ("InkHueTint", (1.0, 1.0, 1.0, 1.0)),
    ("InkPaperColor", (0.98, 0.95, 0.88, 1.0)),
]

# InkSyncVision/InkMasterWeight/InkBass/InkMid/InkTreble/InkReact/InkHueShift
# come from MPC_MelodiaInk; the *Pulse/Combo/Tension/Victory/MeluPrimary names
# come from MPC_Melodia_Palette. Both bind by name in Custom HLSL.
CODE = r"""// ===== M_PP_MelodiaInk — Dreamprint: printed music-box ink =====
// After Tonemapping. All effects float-gated (0/1); InkMasterWeight is the
// global print level so a profile can run at any strength.
float2 uv = UV;
float3 src = SceneColor;
float luma = dot(src, float3(0.2126, 0.7152, 0.0722));

float beat    = saturate(BeatPulse);
float combo   = saturate(ComboNormalized);
float tension = saturate(EnemyTension);
float victory = saturate(VictoryPulse);
float bass    = saturate(InkBass);
float treble  = saturate(InkTreble);
float react   = saturate(InkReact);
float sv      = saturate(InkSyncVision) * (0.5 + 0.5 * beat);

float3 col = src;

// ===== 1. HALFTONE — Ben-Day dots (bigger ink in shadow) =====
float ang = InkDotAngle * 0.0174533;
float ca = cos(ang); float sa = sin(ang);
float2 v = uv - 0.5;
float2 cuv = float2(v.x * ca - v.y * sa, v.x * sa + v.y * ca) + 0.5;
float2 cell = frac(cuv / max(InkDotPitch, 1e-4));
float2 cdist = abs(cell - 0.5) * 2.0;
float dotDist = length(cdist) * 0.7071;
float midInk = saturate(1.0 - abs(luma - 0.5) * 4.0) * saturate(InkMid);
float dotRadius = (0.18 + (1.0 - luma) * 0.55 * InkDotLumaDrive) * InkDotScale;
dotRadius *= 1.0 + beat * 0.18 + combo * 0.10 + bass * 0.06 + midInk * 0.15;
float dotEdge = max(fwidth(dotDist) * 2.0, 0.002);
float dotMask = 1.0 - smoothstep(max(dotRadius - dotEdge, 0.0), dotRadius + dotEdge, dotDist);
float shadowInk = saturate((1.0 - luma) * 0.6 + InkPaperShadow * 0.4);
float inkAmt = dotMask * InkHalftone * shadowInk;
float3 inkCol = InkColor * lerp(float3(1, 1, 1), InkHueTint, 0.6);
float accentMix = saturate((InkHueShift - 0.5) * 2.0);
inkCol = lerp(inkCol, InkAccentTint, accentMix * 0.5);
col = lerp(col, lerp(col, inkCol * 0.7 + col * 0.3, 1.0), inkAmt * InkStrength * (0.6 + react * 0.4));

// ===== 2. HATCH — shadow lines (tension darkens) =====
if (InkHatch > 0.001) {
    float2 hdir = float2(cos(InkHatchAngle * 0.0174533), sin(InkHatchAngle * 0.0174533));
    float hline = frac(dot(uv, hdir) * InkHatchDensity);
    float hatchMask = 1.0 - step(0.5, hline);
    float hatchZone = saturate(1.0 - luma * (1.0 + InkHatchShadowBand)) * (0.55 + tension * 0.45);
    col = lerp(col, col * inkCol * 0.75, hatchMask * hatchZone * InkStrength * 0.35);
}

// ===== 3. PRINT OFFSET — misregistration (break slip) =====
// cR/cB are sampled at dynamic UVs in the graph (SceneTexture PPI0 inputs);
// SceneTextureLookup is not callable inside custom nodes in UE 5.8.
if (InkPrintShift > 0.001) {
    col = lerp(col, float3(cR.r, col.g, cB.b), InkPrintShift * InkStrength * 0.8);
}

// ===== 4. PAPER GRAIN (treble lifts it) =====
if (InkGrainOn > 0.001) {
    float2 gpos = uv * InkGrainScale + float2(View.GameTime * 0.03, View.GameTime * 0.02);
    float g = frac(sin(dot(gpos, float2(12.9898, 78.233))) * 43758.5453);
    float grain = 1.0 + (g - 0.5) * 2.0 * InkGrain * (0.5 + treble * 0.8);
    col *= grain;
}

// ===== 5. SYNC VISION — beat/victory pulse =====
if (sv > 0.001) {
    float3 pv = max(MeluPrimary, 1e-4);
    pv /= max(dot(pv, float3(0.2126, 0.7152, 0.0722)), 1e-4);
    col = lerp(col, col * pv * (1.0 + sv * 0.30), sv * 0.4);
    col += sv * 0.03;
    float inv = smoothstep(0.5, 1.0, beat) * sv;
    col = lerp(col, float3(1.0, 1.0, 1.0) - col, inv * 0.35);
}

// ===== 7. PAPER TONE (InkPaperLight/InkPaperColor; 1.0 = no paper shift) =====
float paperMix = (1.0 - saturate(InkPaperLight)) * (1.0 - luma);
col = lerp(col, col * InkPaperColor, paperMix * 0.35);

// ===== 6. MOTION SMEAR (off by default; sampled at graph-computed UV) =====
if (InkSmearOn > 0.001) {
    col = lerp(col, smeared, InkSmearOn * InkSmear * 0.3);
}

float master = saturate(InkMasterWeight);
return lerp(src, col, master);
"""

PROFILES = {
    "MI_MelodiaInk_GameplayStandard": {
        "scalars": {
            "InkStrength": 0.35, "InkDotScale": 0.8, "InkDotPitch": 0.018,
            "InkGrain": 0.08, "InkPrintShift": 0.0, "InkSmearOn": 0.0,
        },
    },
    "MI_MelodiaInk_Narrative": {
        "scalars": {
            "InkStrength": 0.55, "InkDotScale": 1.0, "InkDotPitch": 0.015,
            "InkGrain": 0.12, "InkPrintShift": 1.0, "InkPrintOffset": 0.4,
            "InkPrintOffsetDepth": 0.5, "InkSmearOn": 0.0,
        },
    },
    "MI_MelodiaInk_PortfolioHero": {
        "scalars": {
            "InkStrength": 0.85, "InkDotScale": 1.2, "InkDotPitch": 0.012,
            "InkGrain": 0.15, "InkPrintShift": 1.0, "InkPrintOffset": 0.7,
            "InkPrintOffsetDepth": 0.7, "InkSmearOn": 1.0, "InkSmear": 0.35,
        },
    },
}


def after_tonemap_location():
    """Explicit After-Tonemapping location — trap #5 (DREAMPRINT_STACK_BUILD
    2026-08-16): material_lib.post_process_blendable_location() falls back to
    BL_REPLACING_TONEMAPPER, which is wrong for LDR post passes."""
    members = [str(x) for x in dir(unreal.BlendableLocation) if not x.startswith("_")]
    for cand in ("BL_SCENE_COLOR_AFTER_TONEMAPPING", "BL_SCENE_COLOR_AFTER_TONEMAP"):
        if cand in members:
            return getattr(unreal.BlendableLocation, cand)
    raise RuntimeError("no After-Tonemapping BlendableLocation enum member available")


def build_master(force: bool = False) -> unreal.Material:
    lib.ensure_directory(MASTER_FOLDER)
    if unreal.EditorAssetLibrary.does_asset_exist(MASTER_PATH):
        mat = unreal.load_asset(MASTER_PATH)
        if mat and not force:
            return mat
        if mat and force:
            lib.clear_material_graph(mat)
    else:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.MaterialFactoryNew()
        mat = asset_tools.create_asset(MASTER_NAME, MASTER_FOLDER, unreal.Material, factory)
    if not mat:
        raise RuntimeError(f"Failed to create {MASTER_PATH}")

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    mat.set_editor_property("blendable_location", after_tonemap_location())
    mat.set_editor_property("blendable_priority", 0.0)

    x, y = -1400, -600
    for name, default, smin, smax in SCALAR_PARAMS:
        lib.scalar_param(mat, name, GROUP, default, x, y)
        y += 60
    for name, rgba in VECTOR_PARAMS:
        lib.vector_param(mat, name, GROUP, rgba, x - 260, y)
        y += 60

    custom = lib.create_expression(mat, unreal.MaterialExpressionCustom, 600, 0)
    custom.set_editor_property("code", CODE)
    unreal.MaterialEditingLibrary.connect_material_property(custom, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    wiring = wire_custom_inputs(mat, custom, force=force)
    if not wiring.get("wired") and not wiring.get("reason", "").startswith("already"):
        raise RuntimeError(f"custom input wiring failed: {wiring}")
    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        unreal.log_warning(f"[Dreamprint] recompile: {exc}")
    lib.save_package(mat)
    return mat


# UE 5.8 custom nodes only see FUNCTION INPUTS — by-name globals (UV, SceneColor,
# MPC channels, material params) are not declared in the generated helper. Every
# identifier the code reads must be a named input (proven by shader dump lab,
# 2026-08-18). SceneTextureLookup is NOT callable in the helper either, so the
# print-offset/smear samples are computed in the graph at dynamic UVs.
MPC_PALETTE_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
MPC_INK_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_MelodiaInk"

MPC_INPUTS: tuple[tuple[str, str], ...] = (
    ("BeatPulse", MPC_PALETTE_PATH), ("ComboNormalized", MPC_PALETTE_PATH),
    ("EnemyTension", MPC_PALETTE_PATH), ("BreakPulse", MPC_PALETTE_PATH),
    ("VictoryPulse", MPC_PALETTE_PATH),
    ("InkMasterWeight", MPC_INK_PATH), ("InkSyncVision", MPC_INK_PATH),
    ("InkBass", MPC_INK_PATH), ("InkMid", MPC_INK_PATH), ("InkTreble", MPC_INK_PATH),
    ("InkReact", MPC_INK_PATH), ("InkHueShift", MPC_INK_PATH),
    ("InkAccentTint", MPC_INK_PATH),
    ("MeluPrimary", MPC_PALETTE_PATH),
)

SCENE_TEX_IDS = {m for m in dir(unreal.SceneTextureId) if not m.startswith("_")}


def _pp_input_id():
    for cand in ("PPI_POST_PROCESS_INPUT0", "PPI_PostProcessInput0"):
        if cand in SCENE_TEX_IDS:
            return getattr(unreal.SceneTextureId, cand)
    return unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0


def _scene_texture(mat: unreal.Material, x: int, y: int, coord_expr=None) -> unreal.MaterialExpression:
    st = lib.create_expression(mat, unreal.MaterialExpressionSceneTexture, x, y)
    st.set_editor_property("scene_texture_id", _pp_input_id())
    if coord_expr is not None:
        unreal.MaterialEditingLibrary.connect_material_expressions(coord_expr, "", st, "Coordinates")
    return st


def wire_custom_inputs(mat: unreal.Material, custom: unreal.MaterialExpressionCustom, force: bool = False) -> dict:
    """Build the 42 named function inputs + the graph that feeds them."""
    existing = custom.get_editor_property("inputs") or []
    if len(existing) >= 40 and not force:
        return {"wired": False, "reason": f"already wired ({len(existing)} inputs)"}
    if force:
        custom.set_editor_property("inputs", [])
        existing = []
    if not existing:
        donor_mat = unreal.load_asset(GRADE_DONOR)
        donor = None
        if donor_mat:
            donor_customs = [e for e in unreal.MaterialEditingLibrary.get_material_expressions(donor_mat)
                             if type(e).__name__ == "MaterialExpressionCustom"]
            donor = (donor_customs[0].get_editor_property("inputs") or [None])[0] if donor_customs else None
        if donor is None:
            return {"wired": False, "reason": "no donor CustomInput template (grade master missing)"}
        template = donor
    else:
        template = existing[0]

    exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat) or []
    by_name: dict[str, unreal.MaterialExpression] = {}
    for e in exprs:
        try:
            by_name[str(e.get_editor_property("parameter_name"))] = e
        except Exception:
            continue

    # MPC collection nodes FIRST — the helper graph reads some of them.
    for ident, coll_path in MPC_INPUTS:
        node = by_name.get(ident)
        if not node or type(node).__name__ != "MaterialExpressionCollectionParameter":
            node = lib.collection_param(mat, coll_path, ident, -1100, 1300)
            by_name[ident] = node

    # --- graph helpers -----------------------------------------------------
    sp = lib.create_expression(mat, unreal.MaterialExpressionScreenPosition, -900, 500)
    half = lib.create_expression(mat, unreal.MaterialExpressionConstant2Vector, -1100, 560)
    half.set_editor_property("r", 0.5)
    half.set_editor_property("g", 0.5)
    sub = lib.create_expression(mat, unreal.MaterialExpressionSubtract, -900, 620)
    unreal.MaterialEditingLibrary.connect_material_expressions(sp, "", sub, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(half, "", sub, "B")
    dotp = lib.create_expression(mat, unreal.MaterialExpressionDotProduct, -800, 620)
    unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", dotp, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", dotp, "B")
    length = lib.create_expression(mat, unreal.MaterialExpressionSquareRoot, -700, 620)
    unreal.MaterialEditingLibrary.connect_material_expressions(dotp, "", length, "")
    two = lib.create_expression(mat, unreal.MaterialExpressionConstant, -900, 700)
    two.set_editor_property("r", 2.0)
    zero = lib.create_expression(mat, unreal.MaterialExpressionConstant, -700, 880)
    zero.set_editor_property("r", 0.0)
    a1 = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -700, 700)
    unreal.MaterialEditingLibrary.connect_material_expressions(length, "", a1, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(two, "", a1, "B")
    a2 = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -600, 700)
    unreal.MaterialEditingLibrary.connect_material_expressions(a1, "", a2, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(by_name["InkPrintOffsetDepth"], "", a2, "B")
    half2 = lib.create_expression(mat, unreal.MaterialExpressionConstant, -700, 760)
    half2.set_editor_property("r", 0.5)
    a3 = lib.create_expression(mat, unreal.MaterialExpressionAdd, -600, 760)
    unreal.MaterialEditingLibrary.connect_material_expressions(half2, "", a3, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(a2, "", a3, "B")
    a4 = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -500, 760)
    unreal.MaterialEditingLibrary.connect_material_expressions(a3, "", a4, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(by_name["InkPrintOffset"], "", a4, "B")
    off_vec = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -500, 620)
    unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", off_vec, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(a4, "", off_vec, "B")
    six = lib.create_expression(mat, unreal.MaterialExpressionConstant, -700, 880)
    six.set_editor_property("r", 0.006)
    bp = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -600, 880)
    unreal.MaterialEditingLibrary.connect_material_expressions(by_name["BreakPulse"], "", bp, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(six, "", bp, "B")
    bp_vec = lib.create_expression(mat, unreal.MaterialExpressionAppendVector, -500, 880)
    unreal.MaterialEditingLibrary.connect_material_expressions(bp, "", bp_vec, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(zero, "", bp_vec, "B")
    off = lib.create_expression(mat, unreal.MaterialExpressionAdd, -400, 700)
    unreal.MaterialEditingLibrary.connect_material_expressions(off_vec, "", off, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(bp_vec, "", off, "B")
    cr_coord = lib.create_expression(mat, unreal.MaterialExpressionAdd, -300, 620)
    unreal.MaterialEditingLibrary.connect_material_expressions(sp, "", cr_coord, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(off, "", cr_coord, "B")
    cb_coord = lib.create_expression(mat, unreal.MaterialExpressionSubtract, -300, 700)
    unreal.MaterialEditingLibrary.connect_material_expressions(sp, "", cb_coord, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(off, "", cb_coord, "B")

    time = lib.create_expression(mat, unreal.MaterialExpressionTime, -900, 1000)
    t07 = lib.create_expression(mat, unreal.MaterialExpressionConstant, -900, 1060)
    t07.set_editor_property("r", 0.7)
    t05 = lib.create_expression(mat, unreal.MaterialExpressionConstant, -900, 1120)
    t05.set_editor_property("r", 0.5)
    s1 = lib.create_expression(mat, unreal.MaterialExpressionSine, -800, 1000)
    unreal.MaterialEditingLibrary.connect_material_expressions(t07, "", s1, "A")
    s2 = lib.create_expression(mat, unreal.MaterialExpressionCosine, -800, 1060)
    unreal.MaterialEditingLibrary.connect_material_expressions(t05, "", s2, "A")
    thr = lib.create_expression(mat, unreal.MaterialExpressionConstant, -800, 1120)
    thr.set_editor_property("r", 0.003)
    one = lib.create_expression(mat, unreal.MaterialExpressionConstant, -900, 1180)
    one.set_editor_property("r", 1.0)
    beat2 = lib.create_expression(mat, unreal.MaterialExpressionAdd, -800, 1180)
    unreal.MaterialEditingLibrary.connect_material_expressions(one, "", beat2, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(by_name["BeatPulse"], "", beat2, "B")
    k = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -700, 1120)
    unreal.MaterialEditingLibrary.connect_material_expressions(by_name["InkSmear"], "", k, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(beat2, "", k, "B")
    ox = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -700, 1000)
    unreal.MaterialEditingLibrary.connect_material_expressions(s1, "", ox, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(thr, "", ox, "B")
    ox2 = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -600, 1000)
    unreal.MaterialEditingLibrary.connect_material_expressions(ox, "", ox2, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(k, "", ox2, "B")
    oy = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -700, 1060)
    unreal.MaterialEditingLibrary.connect_material_expressions(s2, "", oy, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(thr, "", oy, "B")
    oy2 = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -600, 1060)
    unreal.MaterialEditingLibrary.connect_material_expressions(oy, "", oy2, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(k, "", oy2, "B")
    smear_vec = lib.create_expression(mat, unreal.MaterialExpressionAppendVector, -500, 1000)
    unreal.MaterialEditingLibrary.connect_material_expressions(ox2, "", smear_vec, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(oy2, "", smear_vec, "B")
    smear_coord = lib.create_expression(mat, unreal.MaterialExpressionAdd, -400, 1000)
    unreal.MaterialEditingLibrary.connect_material_expressions(sp, "", smear_coord, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(smear_vec, "", smear_coord, "B")

    # --- input sources -----------------------------------------------------
    st_base = _scene_texture(mat, -600, 300)
    st_cr = _scene_texture(mat, -200, 300, cr_coord)
    st_cb = _scene_texture(mat, -200, 400, cb_coord)
    st_smear = _scene_texture(mat, -200, 500, smear_coord)

    sources: dict[str, tuple[unreal.MaterialExpression, str]] = {
        "UV": (sp, "ViewportUV"),
        "SceneColor": (st_base, "Color"),
        "cR": (st_cr, "Color"),
        "cB": (st_cb, "Color"),
        "smeared": (st_smear, "Color"),
    }
    for ident, _coll_path in MPC_INPUTS:
        sources[ident] = (by_name[ident], "")
    for name, _default, _smin, _smax in SCALAR_PARAMS:
        sources[name] = (by_name[name], "")
    for name, _rgba in VECTOR_PARAMS:
        sources[name] = (by_name[name], "")

    names = (["UV", "SceneColor", "cR", "cB", "smeared"]
             + [i for i, _ in MPC_INPUTS]
             + [n for n, *_ in SCALAR_PARAMS]
             + [n for n, _ in VECTOR_PARAMS])
    entries = []
    for name in names:
        entry = unreal.CustomInput()
        entry.set_editor_property("input_name", name)
        entries.append(entry)
    custom.set_editor_property("inputs", entries)

    wired, failed = [], []
    for name in names:
        src, pin = sources[name]
        try:
            unreal.MaterialEditingLibrary.connect_material_expressions(src, pin, custom, name)
            wired.append(name)
        except Exception as exc:
            failed.append({"name": name, "error": str(exc)})
    return {"wired": True, "input_count": len(names), "connected": wired, "failed": failed}


def build_profiles() -> list[str]:
    lib.ensure_directory(PROFILE_FOLDER)
    built = []
    for name, cfg in PROFILES.items():
        mi = lib.create_material_instance(name, PROFILE_FOLDER, MASTER_PATH)
        for pname, value in cfg.get("scalars", {}).items():
            lib.set_instance_scalar(mi, pname, value)
        lib.save_package(mi)
        built.append(lib.asset_path(PROFILE_FOLDER, name))
    return built


def main() -> int:
    force = "--force" in sys.argv
    mat = build_master(force=force)
    profiles = build_profiles()

    params = set()
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        try:
            params.add(str(e.get_editor_property("parameter_name")))
        except Exception:
            pass
    missing = [n for n, *_ in SCALAR_PARAMS + [("InkColor",)] if n not in params] if False else \
              [n for n, *_ in SCALAR_PARAMS if n not in params] + [n for n, _ in VECTOR_PARAMS if n not in params]

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER_PATH,
        "material_domain": str(mat.get_editor_property("material_domain")),
        "blendable_location": str(mat.get_editor_property("blendable_location")),
        "profiles": profiles,
        "params": sorted(params),
        "missing_params": missing,
        "code_len": len(CODE),
        "ok": not missing,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())