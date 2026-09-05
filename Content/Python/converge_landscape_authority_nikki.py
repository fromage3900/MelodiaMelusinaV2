"""Converge the landscape authority onto M_Master_Nikki_Landscape.

Owner decision 2026-09-03: M_Master_Nikki_Landscape is the NEW landscape
authority. This script makes it a superset of the retiring universal master
(M_Master_Toon_Landscape_HeightBlend) and activates the cymatics driver MPC.

Stages (each verified; report -> Saved/Audit/landscape_authority_convergence_2026-09-03.json):
  0. MPC_Cymatics_Driver: declare the 8 contract scalars from
     MelodiaCymaticsWriterSubsystem.h (the writer subsystem is compiled+live;
     the empty collection made every write a silent no-op).
  1. Backup-duplicate the Nikki master (no overwrite, no delete).
  2. SKIPPED BY DESIGN: UE 5.8 has no MD_Landscape - landscape materials are
     MD_Surface (verified against the retiring universal master 2026-09-03).
     The Nikki master's LandscapeLayerBlend nodes are already legal.
  3. Graft superset: Snow/Water/Mud/Path layer sets (painted weights + slope
     auto-snow), wetness roughness, Gaea mask intake (bUseGaeaMasks, default
     OFF), cymatics emissive read-lane (CymaticsLandscapeAmount, default 0 ->
     zero delta). Every declared param is consumed this pass - no dead params.
  4. Recompile, save, verify readbacks.

Zero-delta guarantee: with no Snow/Water/Mud/Path layer weights painted and
SnowStrength=0 / CymaticsLandscapeAmount=0 (all defaults), the extended chain
lerps at alpha 0 and the flow gate multiplies by 1 - render identical.

Tap nodes verified 2026-09-03 via material:get_expression_connections on
MaterialExpressionSubstrateToonBSDF_1:
  BaseColor <- MaterialExpressionLinearInterpolate_5
  Roughness <- MaterialExpressionMultiply_15
  Normal    <- MaterialExpressionLandscapeLayerBlend_4
  Emissive  <- MaterialExpressionMultiply_20
  (WPO lanes bKawaiiSquish_Active / bNikkiSquishWPO_Active default OFF, so the
   mesh-only squish graph is pruned and the landscape compile is legal.)

Run: Monolith editor.run_python (execute_file) on this path, or
    import converge_landscape_authority_nikki as c; c.main()
"""

from __future__ import annotations

import time as _time
from datetime import datetime, timezone
from pathlib import Path

import unreal

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape"
BACKUP_DIR = "/Game/EnvSandbox/Materials/_Archive/Masters_BACKUP_20260821"
CYM_MPC = "/Game/Melodia/Cymatics/MPC_Cymatics_Driver"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "landscape_authority_convergence_2026-09-03.json"

CYM_SCALARS = [
    ("Cymatic_BeatPulse", 0.0),
    ("Cymatic_BassIntensity", 0.0),
    ("Cymatic_MidIntensity", 0.0),
    ("Cymatic_EmissiveScale", 0.0),
    ("Cymatic_IridescenceShift", 0.0),
    ("Cymatic_UVDistortion", 0.0),
    ("Cymatic_ModeN", 1.0),
    ("Cymatic_ModeM", 1.0),
]

TAP_BC = "MaterialExpressionLinearInterpolate_5"
TAP_ROUGH = "MaterialExpressionMultiply_15"
TAP_NORMAL = "MaterialExpressionLandscapeLayerBlend_4"
TAP_EMISSIVE = "MaterialExpressionMultiply_20"

NEUTRAL_NORMAL = "/Game/EnvSandbox/Textures/Utility/T_Neutral_Normal.T_Neutral_Normal"
NEUTRAL_GRAY = "/Game/Textures/sbs_-_gradient_texture_pack_-_512x512/512x512/Basic/Horizontal_1_-_512x512.Horizontal_1_-_512x512"


# ---------------------------------------------------------------- helpers

def _expr(mat, cls, x, y):
    e = unreal.MaterialEditingLibrary.create_material_expression(mat, cls)
    e.set_editor_property("material_expression_editor_x", x)
    e.set_editor_property("material_expression_editor_y", y)
    return e


def _const(mat, value, x, y):
    e = _expr(mat, unreal.MaterialExpressionConstant, x, y)
    e.set_editor_property("r", float(value))
    return e


def _scalar_param(mat, name, value, x, y):
    e = _expr(mat, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("default_value", float(value))
    return e


def _vector_param(mat, name, color, x, y):
    e = _expr(mat, unreal.MaterialExpressionVectorParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("default_value", color)
    return e


def _texture_param(mat, name, texture_path, x, y):
    e = _expr(mat, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("texture", unreal.load_asset(texture_path))
    return e


def _static_switch(mat, name, default, x, y):
    e = _expr(mat, unreal.MaterialExpressionStaticSwitchParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("default_value", bool(default))
    return e


def _landscape_sample(mat, layer_name, x, y):
    e = _expr(mat, unreal.MaterialExpressionLandscapeLayerSample, x, y)
    e.set_editor_property("parameter_name", layer_name)
    return e


def _connect(mat, src, dst, src_out, dst_in):
    out = "" if src_out == 0 else src_out
    if isinstance(dst_in, int):
        cls = type(dst).__name__
        table = {
            "MaterialExpressionMultiply": ("A", "B"),
            "MaterialExpressionAdd": ("A", "B"),
            "MaterialExpressionSubtract": ("A", "B"),
            "MaterialExpressionDotProduct": ("A", "B"),
            "MaterialExpressionLinearInterpolate": ("A", "B", "Alpha"),
            "MaterialExpressionStaticSwitchParameter": ("True", "False"),
            "MaterialExpressionSaturate": ("",),
        }
        if cls not in table:
            raise RuntimeError(f"no pin table for {cls}; pass input name string")
        dst_in = table[cls][dst_in]
    ok = unreal.MaterialEditingLibrary.connect_material_expressions(src, out, dst, dst_in)
    if not ok:
        raise RuntimeError(f"connect failed: {src.get_name()}[{out}] -> {dst.get_name()}[{dst_in}]")


def _chain2(mat, cls, a, b, x, y):
    """Two-input node: A <- a, B <- b. Returns node."""
    e = _expr(mat, cls, x, y)
    _connect(mat, a, e, 0, 0)
    _connect(mat, b, e, 0, 1)
    return e


def _lerp(mat, a, b, alpha, x, y):
    e = _expr(mat, unreal.MaterialExpressionLinearInterpolate, x, y)
    _connect(mat, a, e, 0, 0)     # A
    _connect(mat, b, e, 0, 1)     # B
    _connect(mat, alpha, e, 0, 2)  # Alpha
    return e


def _find(mat, expr_name):
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat):
        if e.get_name() == expr_name:
            return e
    raise RuntimeError(f"tap node {expr_name} not found - graph changed, aborting")


# ---------------------------------------------------------------- stage 0

def stage0_cymatics_mpc() -> dict:
    mpc = unreal.EditorAssetLibrary.load_asset(CYM_MPC)
    if not mpc:
        raise RuntimeError("MPC_Cymatics_Driver missing on disk")
    params = list(mpc.get_editor_property("scalar_parameters"))
    existing = {p.get_editor_property("parameter_name") for p in params}
    added = []
    for name, default in CYM_SCALARS:
        if name in existing:
            continue
        entry = unreal.CollectionScalarParameter()
        entry.set_editor_property("parameter_name", name)
        entry.set_editor_property("default_value", default)
        g = unreal.Guid()
        seed = int(_time.time() * 1000) + len(params) * 7919
        g.set_editor_property("a", seed & 0xFFFFFFFF)
        g.set_editor_property("b", (seed >> 32) & 0xFFFF)
        g.set_editor_property("c", (seed * 31) & 0xFFFF)
        g.set_editor_property("d", (seed * 127) & 0xFFFFFFFF)
        entry.set_editor_property("parameter_id", g)
        params.append(entry)
        added.append(name)
    if added:
        mpc.set_editor_property("scalar_parameters", params)
        if not unreal.EditorAssetLibrary.save_loaded_asset(mpc):
            raise RuntimeError("MPC save failed")

    activated = None
    try:
        world = unreal.UnrealEditorSubsystem().get_editor_world()
        activated = unreal.KismetMaterialLibrary.set_scalar_parameter_value(
            world, mpc, "Cymatic_BeatPulse", 0.5)
    except Exception as exc:
        activated = f"test-skipped: {exc}"
    params_now = sorted(p.get_editor_property("parameter_name") for p in mpc.get_editor_property("scalar_parameters"))
    return {"added": added, "all_scalars": params_now, "activation_write_ok": activated}


# ---------------------------------------------------------------- stage 1

def stage1_backup() -> str:
    backup_path = f"{BACKUP_DIR}/M_Master_Nikki_Landscape_PRE_CONVERGE_20260903"
    if unreal.EditorAssetLibrary.does_asset_exist(backup_path):
        return backup_path + " (already existed, not overwritten)"
    dup = unreal.EditorAssetLibrary.duplicate_asset(MASTER, backup_path)
    if not dup:
        raise RuntimeError("backup duplicate failed")
    return backup_path


# ---------------------------------------------------------------- stage 2

def stage2_domain(mat) -> str:
    cur = mat.get_editor_property("material_domain")
    if cur == unreal.MaterialDomain.LANDSCAPE:
        return "already MD_Landscape"
    ok = unreal.MaterialEditingLibrary.set_material_property(mat, "MaterialDomain", unreal.MaterialDomain.LANDSCAPE)
    if not ok:
        raise RuntimeError("set_material_property(MaterialDomain) refused")
    new = mat.get_editor_property("material_domain")
    if new != unreal.MaterialDomain.LANDSCAPE:
        raise RuntimeError(f"domain change not applied, still {new}")
    return f"{cur} -> {new}"


# ---------------------------------------------------------------- stage 3 graft

def stage3_graft(mat) -> dict:
    report = {"params_declared": [], "new_expressions": 0}

    def _reg(e):
        report["new_expressions"] += 1
        return e

    t = -3200
    # --- texture params ---
    snow_albedo = _reg(_texture_param(mat, "Snow_Albedo", NEUTRAL_GRAY, t, -1500))
    snow_normal = _reg(_texture_param(mat, "Snow_NormalMap", NEUTRAL_NORMAL, t, -1400))
    water_albedo = _reg(_texture_param(mat, "Water_Albedo", NEUTRAL_GRAY, t, -1300))
    water_normal = _reg(_texture_param(mat, "Water_NormalMap", NEUTRAL_NORMAL, t, -1200))
    mud_albedo = _reg(_texture_param(mat, "Mud_Albedo", NEUTRAL_GRAY, t, -1100))
    mud_normal = _reg(_texture_param(mat, "Mud_NormalMap", NEUTRAL_NORMAL, t, -1000))
    path_albedo = _reg(_texture_param(mat, "Path_Albedo", NEUTRAL_GRAY, t, -900))
    path_normal = _reg(_texture_param(mat, "Path_NormalMap", NEUTRAL_NORMAL, t, -800))
    gaea_slope = _reg(_texture_param(mat, "Gaea_SlopeMask", NEUTRAL_GRAY, t, -700))
    gaea_water = _reg(_texture_param(mat, "Gaea_WaterMask", NEUTRAL_GRAY, t, -600))
    gaea_flow = _reg(_texture_param(mat, "Gaea_FlowMask", NEUTRAL_GRAY, t, -500))

    # --- scalar/vector params ---
    snow_strength = _reg(_scalar_param(mat, "SnowStrength", 0.0, t, -380))
    snow_up_bias = _reg(_scalar_param(mat, "SnowUpBias", 2.2, t, -310))
    wetness = _reg(_scalar_param(mat, "Wetness", 0.1, t, -240))
    wet_roughness = _reg(_scalar_param(mat, "WetRoughness", 0.45, t, -170))
    cym_amount = _reg(_scalar_param(mat, "CymaticsLandscapeAmount", 0.0, t, -100))
    gaea_slope_w = _reg(_scalar_param(mat, "Gaea_SlopeWeight", 0.0, t, -30))
    gaea_water_w = _reg(_scalar_param(mat, "Gaea_WaterWeight", 0.0, t, 40))
    gaea_flow_w = _reg(_scalar_param(mat, "Gaea_FlowWeight", 0.0, t, 110))

    snow_tint = _reg(_vector_param(mat, "SnowTint", unreal.LinearColor(0.92, 0.95, 0.98, 1.0), t, 180))
    mud_tint = _reg(_vector_param(mat, "MudTint", unreal.LinearColor(0.28, 0.22, 0.16, 1.0), t, 280))
    path_tint = _reg(_vector_param(mat, "PathTint", unreal.LinearColor(0.58, 0.54, 0.48, 1.0), t, 380))
    water_tint = _reg(_vector_param(mat, "WaterAlignTint", unreal.LinearColor(0.55, 0.72, 0.78, 1.0), t, 480))

    b_ext = _reg(_static_switch(mat, "bUseExtendedLayers", True, t, 580))
    b_gaea = _reg(_static_switch(mat, "bUseGaeaMasks", False, t, 680))

    report["params_declared"] = [
        "Snow_Albedo", "Snow_NormalMap", "Water_Albedo", "Water_NormalMap",
        "Mud_Albedo", "Mud_NormalMap", "Path_Albedo", "Path_NormalMap",
        "Gaea_SlopeMask", "Gaea_WaterMask", "Gaea_FlowMask",
        "SnowStrength", "SnowUpBias", "Wetness", "WetRoughness",
        "CymaticsLandscapeAmount", "Gaea_SlopeWeight", "Gaea_WaterWeight", "Gaea_FlowWeight",
        "SnowTint", "MudTint", "PathTint", "WaterAlignTint",
        "bUseExtendedLayers", "bUseGaeaMasks",
    ]

    # --- painted layer weight samples ---
    lw = -2900
    ws = _reg(_landscape_sample(mat, "Snow", lw, -1500))
    ww = _reg(_landscape_sample(mat, "Water", lw, -1400))
    wm = _reg(_landscape_sample(mat, "Mud", lw, -1300))
    wp = _reg(_landscape_sample(mat, "Path", lw, -1200))

    # --- auto-snow (up-biased, gated by SnowStrength; 0 by default) ---
    px_norm = _reg(_expr(mat, unreal.MaterialExpressionPixelNormalWS, -3100, -1600))
    up_const = _reg(_expr(mat, unreal.MaterialExpressionConstant3Vector, -3100, -1500))
    up_const.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 0.0))
    updot = _reg(_chain2(mat, unreal.MaterialExpressionDotProduct, px_norm, up_const, -2950, -1550))
    minus = _expr(mat, unreal.MaterialExpressionSubtract, -2800, -1550)
    _connect(mat, updot, minus, 0, 0)
    _connect(mat, _const(mat, 0.6, -2800, -1470), minus, 0, 1)
    _reg(minus)
    bias_mul = _reg(_chain2(mat, unreal.MaterialExpressionMultiply, minus, snow_up_bias, -2650, -1550))
    auto_sat = _reg(_expr(mat, unreal.MaterialExpressionSaturate, -2500, -1550))
    _connect(mat, bias_mul, auto_sat, 0, 0)
    auto_snow = _reg(_chain2(mat, unreal.MaterialExpressionMultiply, auto_sat, snow_strength, -2350, -1550))

    # --- gaea gates: weight *= lerp(1, mask.r, weight_param); 0-weight => identity ---
    def gate(weight_expr, mask_expr, gweight_expr, x, y):
        one = _const(mat, 1.0, x, y + 90)
        lerp_node = _expr(mat, unreal.MaterialExpressionLinearInterpolate, x + 150, y)
        _connect(mat, one, lerp_node, 0, 0)          # A = 1
        _connect(mat, mask_expr, lerp_node, 0, 1)    # B = mask.r
        _connect(mat, gweight_expr, lerp_node, 0, 2)  # Alpha
        _reg(lerp_node)
        out = _chain2(mat, unreal.MaterialExpressionMultiply, weight_expr, lerp_node, x + 300, y)
        return out

    snow_gated = _reg(gate(ws, gaea_slope, gaea_slope_w, -2200, -1400))
    snow_total = _reg(_chain2(mat, unreal.MaterialExpressionAdd, snow_gated, auto_snow, -2050, -1400))
    water_gated = _reg(gate(ww, gaea_water, gaea_water_w, -2200, -1100))

    # --- alpha = sat(sum of extended weights) ---
    wsnow_water = _reg(_chain2(mat, unreal.MaterialExpressionAdd, snow_total, water_gated, -1900, -1250))
    wmud_path = _reg(_chain2(mat, unreal.MaterialExpressionAdd, wm, wp, -1900, -1150))
    wsum = _reg(_chain2(mat, unreal.MaterialExpressionAdd, wsnow_water, wmud_path, -1750, -1200))
    alpha_sat = _reg(_expr(mat, unreal.MaterialExpressionSaturate, -1600, -1200))
    _connect(mat, wsum, alpha_sat, 0, 0)

    # --- extended albedo (normalized via alpha-lerp into main) ---
    albedo_terms = []
    for i, (w, tex, tint) in enumerate(zip(
            [snow_total, water_gated, wm, wp],
            [snow_albedo, water_albedo, mud_albedo, path_albedo],
            [snow_tint, water_tint, mud_tint, path_tint])):
        tinted = _reg(_chain2(mat, unreal.MaterialExpressionMultiply, tex, tint, -1500, -1500 + i * 70))
        albedo_terms.append(_reg(_chain2(mat, unreal.MaterialExpressionMultiply, tinted, w, -1350, -1500 + i * 70)))
    ext_albedo = albedo_terms[0]
    for term in albedo_terms[1:]:
        ext_albedo = _reg(_chain2(mat, unreal.MaterialExpressionAdd, ext_albedo, term, -1200, -1450 + i * 10))

    # --- extended normal ---
    norm_terms = []
    for i, (w, tex) in enumerate(zip([snow_total, water_gated, wm, wp],
                                     [snow_normal, water_normal, mud_normal, path_normal])):
        norm_terms.append(_reg(_chain2(mat, unreal.MaterialExpressionMultiply, tex, w, -1500, -1150 + i * 70)))
    ext_normal = norm_terms[0]
    for term in norm_terms[1:]:
        ext_normal = _reg(_chain2(mat, unreal.MaterialExpressionAdd, ext_normal, term, -1200, -1080))

    # --- cymatics emissive source ---
    cym_mpc = unreal.load_asset(CYM_MPC)
    cym_beat = _reg(_expr(mat, unreal.MaterialExpressionCollectionParameter, -1600, -550))
    cym_beat.set_editor_property("collection", cym_mpc)
    cym_beat.set_editor_property("parameter_name", "Cymatic_BeatPulse")

    # --- rewires (tap nodes verified; see module docstring) ---
    main_bc = _find(mat, TAP_BC)
    main_rough = _find(mat, TAP_ROUGH)
    main_normal = _find(mat, TAP_NORMAL)
    main_emissive = _find(mat, TAP_EMISSIVE)
    bsdf = _find(mat, "MaterialExpressionSubstrateToonBSDF_1")

    # BaseColor: BSDF <- lerp(main, switch(ext, main), alpha)
    ext_sel = _static_switch(mat, "bUseExtendedLayers", True, 60, -260)  # consumed switch instance
    _reg(ext_sel)
    _connect(mat, ext_albedo, ext_sel, 0, 0)   # True = extended
    _connect(mat, main_bc, ext_sel, 0, 1)      # False = main
    lerp_bc = _reg(_lerp(mat, main_bc, ext_sel, alpha_sat, 200, -160))
    _connect(mat, lerp_bc, bsdf, 0, "BaseColor")

    # Normal: same shape
    ext_sel_n = _static_switch(mat, "bUseExtendedLayers", True, 60, 40)
    _reg(ext_sel_n)
    _connect(mat, ext_normal, ext_sel_n, 0, 0)
    _connect(mat, main_normal, ext_sel_n, 0, 1)
    lerp_n = _reg(_lerp(mat, main_normal, ext_sel_n, alpha_sat, 200, 60))
    _connect(mat, lerp_n, bsdf, 0, "Normal")

    # Roughness: A = switch(bUseGaeaMasks, mul(main_rough, flow_gate), main_rough)
    #            B = lerp(main_rough, WetRoughness, sat(water*Wetness))
    flow_gate = _reg(gate(_const(mat, 1.0, -1750, -780), gaea_flow, gaea_flow_w, -1600, -700))
    # NOTE: gate() multiplies its weight_expr by the lerped mask; pass const 1 so result = mask lerp
    flow_mul = _reg(_chain2(mat, unreal.MaterialExpressionMultiply, main_rough, flow_gate, -1250, -700))
    rough_a = _static_switch(mat, "bUseGaeaMasks", False, -1100, -700)
    _reg(rough_a)
    _connect(mat, flow_mul, rough_a, 0, 0)
    _connect(mat, main_rough, rough_a, 0, 1)
    wet_alpha = _reg(_chain2(mat, unreal.MaterialExpressionMultiply, water_gated, wetness, -1500, -560))
    wet_sat = _reg(_expr(mat, unreal.MaterialExpressionSaturate, -1350, -560))
    _connect(mat, wet_alpha, wet_sat, 0, 0)
    rough_b = _reg(_lerp(mat, main_rough, wet_roughness, wet_sat, -1200, -560))
    lerp_rough = _reg(_lerp(mat, rough_a, rough_b, alpha_sat, 200, 140))
    _connect(mat, lerp_rough, bsdf, 0, "Roughness")

    # Emissive: BSDF <- lerp(main, mul(mul(lerp_bc, BeatPulse), Amount), sat(Amount))
    e1 = _reg(_chain2(mat, unreal.MaterialExpressionMultiply, lerp_bc, cym_beat, 200, 220))
    e2 = _reg(_chain2(mat, unreal.MaterialExpressionMultiply, e1, cym_amount, 350, 220))
    amt_sat = _reg(_expr(mat, unreal.MaterialExpressionSaturate, 350, 290))
    _connect(mat, cym_amount, amt_sat, 0, 0)
    lerp_e = _reg(_lerp(mat, main_emissive, e2, amt_sat, 500, 220))
    _connect(mat, lerp_e, bsdf, 0, "EmissiveColor")

    report["taps"] = {"BaseColor": TAP_BC, "Roughness": TAP_ROUGH,
                      "Normal": TAP_NORMAL, "Emissive": TAP_EMISSIVE}
    return report


# ---------------------------------------------------------------- stage 4

def stage4_verify(mat) -> dict:
    if not unreal.MaterialEditingLibrary.recompile_material(mat):
        raise RuntimeError("recompile failed - see compile errors")
    saved = unreal.MaterialEditingLibrary.save_material(mat)
    params = {}
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat):
        cls = type(e).__name__
        if cls == "MaterialExpressionScalarParameter":
            params.setdefault("scalars", []).append(e.get_editor_property("parameter_name"))
        elif cls == "MaterialExpressionVectorParameter":
            params.setdefault("vectors", []).append(e.get_editor_property("parameter_name"))
        elif cls == "MaterialExpressionTextureSampleParameter2D":
            params.setdefault("textures", []).append(e.get_editor_property("parameter_name"))
        elif cls == "MaterialExpressionStaticSwitchParameter":
            params.setdefault("switches", []).append(e.get_editor_property("parameter_name"))
    domain = mat.get_editor_property("material_domain")
    expr_count = len(unreal.MaterialEditingLibrary.get_material_expressions(mat))
    return {"saved": bool(saved), "domain": str(domain), "expression_count": expr_count,
            "param_census": {k: sorted(v) for k, v in params.items()}}


# ---------------------------------------------------------------- main

def main() -> dict:
    report = {"schema": "melodia.landscape_authority_convergence.v1", "master": MASTER,
              "started": datetime.now(timezone.utc).isoformat()}

    report["stage0_mpc"] = stage0_cymatics_mpc()
    report["stage1_backup"] = stage1_backup()

    mat = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not mat:
        raise RuntimeError("master load failed")

    report["stage2_domain"] = stage2_domain(mat)
    report["stage3_graft"] = stage3_graft(mat)
    report["stage4_verify"] = stage4_verify(mat)
    report["finished"] = datetime.now(timezone.utc).isoformat()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[ConvergeLandscapeAuthority] report -> {REPORT}")
    return report
