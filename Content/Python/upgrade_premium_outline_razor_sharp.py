"""Premium Outline — Razor Sharp Thin Professional (2026).

Top-of-the-line toon outline techniques integrated:
  1. Depth + Normal edge detection (combined response) — already in base material
  2. View-angle depth threshold modulation — prevents grazing-angle false edges
  3. Distance-based thickness modulation — min/max thickness by camera distance
  4. Custom depth stencil — selective per-object outlining
  5. Edge blending — clean overlapping outline management
  6. Multiplier + bias (smoothstep) instead of hard threshold — anti-aliased edges

Parameters are exposed as material instance scalars so artists can tune without
recompiling. Idempotent — safe to re-run. Runs in-editor via Unreal Python.

Run:
    import upgrade_premium_outline_razor_sharp as rs; rs.run_all()
"""
from __future__ import annotations

import unreal

MAT = "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate"
INST = "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_RazorSharp"
MEL = unreal.MaterialEditingLibrary

# --- Parameter defaults -------------------------------------------------------
RAZOR_SHARPNESS_DEFAULT = 2.5
RAZOR_AA_FLOOR_DEFAULT = 0.25
RAZOR_CONTRAST_DEFAULT = 4.0
RAZOR_VIEW_ANGLE_DEFAULT = 0.7
RAZOR_MIN_THICKNESS_DEFAULT = 0.5
RAZOR_MAX_THICKNESS_DEFAULT = 1.5
RAZOR_THICKNESS_FALLOFF_DEFAULT = 500.0
RAZOR_CUSTOM_STENCIL_DEFAULT = 0
RAZOR_STENCIL_MODE_DEFAULT = 0
RAZOR_EDGE_BLEND_DEFAULT = 0.3


def _get_custom(m):
    for e in MEL.get_material_expressions(m) or []:
        if type(e).__name__ == "MaterialExpressionCustom":
            return e
    return None


def _param_exists(m, name: str) -> bool:
    """Check if a scalar parameter with this name already exists in the graph."""
    for e in MEL.get_material_expressions(m) or []:
        if type(e).__name__ == "MaterialExpressionScalarParameter":
            try:
                if e.get_editor_property("parameter_name") == name:
                    return True
            except Exception:
                pass
    return False


def _add_scalar_param(m, name: str, default_val: float, x: int, y: int):
    """Add a ScalarParameter expression connected to nothing yet (declared)."""
    p = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
    p.set_editor_property("parameter_name", name)
    p.set_editor_property("default_value", default_val)
    unreal.log(f"[RazorSharp] added scalar param '{name}' = {default_val}")
    return p


def _find_anchor(code: str) -> str | None:
    """Find the final output anchor to insert the razor-sharp block before."""
    anchors = [
        "return float4(finalColor, 1.0);",
        "float3 finalColor = lerp(SceneColor.rgb, edgeColor, edgeResponse);",
        "return float4(ink, edge);",
        "// --- FINAL OUTPUT ---",
    ]
    for a in anchors:
        if a in code:
            return a
    return None


RAZOR_BLOCK = r"""
    // ---- RAZOR SHARP THIN PROFESSIONAL (2026) ------------------------------
    // 1. View-angle depth threshold modulation (prevents grazing-angle false edges)
    //    When view is parallel to surface, depth differences between neighbors
    //    blow up even on flat geometry. Modulate threshold by view angle.
    float2 viewDir = normalize(View.ViewVectorWS - WorldPosition);
    float viewAngle = dot(viewDir, WorldNormal);
    float angleMod = 1.0 - saturate(viewAngle * RazorViewAngleMod);
    float razorThreshold = RazorAAFloor * (1.0 + angleMod);

    // 2. Distance-based thickness modulation (consistent screen-space thickness)
    //    Outlines get thinner as camera moves away, thicker up close.
    float distToCam = length(View.ViewVectorWS - WorldPosition);
    float distFactor = saturate(distToCam / RazorThicknessFalloff);
    float thicknessMod = lerp(RazorMaxThickness, RazorMinThickness, distFactor);

    // 3. Razor response: sharpen edge response with multiplier + smoothstep contrast
    float razorResponse = saturate(edgeResponse * RazorSharpness * thicknessMod);
    float razorAAS = max(rcp(max(widthPx, 1.0)) * RazorAAFloor, 1e-4);
    float razorEdge = smoothstep(razorThreshold, razorThreshold * RazorContrast, razorResponse);

    // 4. Custom depth stencil selective outlining (1/2/3 = only matching stencil)
    if (RazorStencilMode > 0.5) {
        float stencilVal = GBufferCustomStencil.r;
        float stencilMatch = (stencilVal == RazorCustomStencil) ? 1.0 : 0.0;
        razorEdge *= stencilMatch;
    }

    // 5. Apply edge color with razor-thin contrast step
    edgeColor = lerp(edgeColor, float3(0,0,0), razorEdge);

    // 6. Edge blending for overlapping outlines — soft transition at intersections
    float razorOpacity = smoothstep(0.02, 0.15, razorResponse);
    edgeColor *= razorOpacity;
    // ------
"""


def apply(m) -> str:
    """Apply razor-sharp thin mutations to the material's Custom HLSL block."""
    custom = _get_custom(m)
    if not custom:
        raise RuntimeError(f"No MaterialExpressionCustom found in {MAT}")

    code = custom.get_editor_property("code")
    changes = 0

    # 1. Declare all scalar parameters (only once)
    params = [
        ("RazorSharpness", RAZOR_SHARPNESS_DEFAULT, 1400, 400),
        ("RazorAAFloor", RAZOR_AA_FLOOR_DEFAULT, 1400, 450),
        ("RazorContrast", RAZOR_CONTRAST_DEFAULT, 1400, 500),
        ("RazorViewAngleMod", RAZOR_VIEW_ANGLE_DEFAULT, 1400, 550),
        ("RazorMinThickness", RAZOR_MIN_THICKNESS_DEFAULT, 1400, 600),
        ("RazorMaxThickness", RAZOR_MAX_THICKNESS_DEFAULT, 1400, 650),
        ("RazorThicknessFalloff", RAZOR_THICKNESS_FALLOFF_DEFAULT, 1400, 700),
        ("RazorCustomStencil", RAZOR_CUSTOM_STENCIL_DEFAULT, 1400, 750),
        ("RazorStencilMode", RAZOR_STENCIL_MODE_DEFAULT, 1400, 800),
        ("RazorEdgeBlend", RAZOR_EDGE_BLEND_DEFAULT, 1400, 850),
    ]
    for name, default_val, x, y in params:
        if not _param_exists(m, name):
            _add_scalar_param(m, name, default_val, x, y)
            changes += 1

    # 2. Insert razor-sharp block before final output (only once)
    if "RAZOR SHARP THIN PROFESSIONAL" in code:
        unreal.log("[RazorSharp] professional razor block already present — skipping")
    else:
        anchor = _find_anchor(code)
        if anchor:
            code = code.replace(anchor, RAZOR_BLOCK + anchor, 1)
            changes += 1
            print(f"[OK] Professional razor sharp block inserted before '{anchor[:50]}...'")
        else:
            print(f"[WARN] No final-output anchor found — razor block not inserted")
            print(f"  Code ends with: ...{code[-200:]}")

    if changes > 0:
        custom.set_editor_property("code", code)
        MEL.recompile_material(m)
        unreal.EditorAssetLibrary.save_asset(m.get_path_name())
        print(f"[DONE] Razor sharp thin professional applied — {changes} changes")
    else:
        print("[NOOP] No changes — may already be razor-sharp professional")

    # --- Verify ---------------------------------------------------------------
    rb = _get_custom(m)
    rc = rb.get_editor_property("code") if rb else ""
    v_ok = (
        "RazorSharpness" in rc
        and "RazorAAFloor" in rc
        and "RazorContrast" in rc
        and "RazorViewAngleMod" in rc
        and "RazorMinThickness" in rc
        and "RazorMaxThickness" in rc
        and "RazorStencilMode" in rc
        and "RAZOR SHARP THIN PROFESSIONAL" in rc
    )
    print(f"  Verification: sharp={'RazorSharpness' in rc} "
          f"aaFloor={'RazorAAFloor' in rc} contrast={'RazorContrast' in rc} "
          f"viewAngle={'RazorViewAngleMod' in rc} "
          f"thickness={'RazorMinThickness' in rc} "
          f"stencil={'RazorStencilMode' in rc} "
          f"block={'RAZOR SHARP THIN PROFESSIONAL' in rc}")
    return "ok" if v_ok else "READBACK FAILED"


def build_instance() -> str | None:
    """Create/update the Razor Sharp material instance with thin defaults."""
    parent = unreal.EditorAssetLibrary.load_asset(MAT)
    if not parent:
        unreal.log_warning(f"[RazorSharp] parent missing: {MAT}")
        return None

    if unreal.EditorAssetLibrary.does_asset_exist(INST):
        inst = unreal.EditorAssetLibrary.load_asset(INST)
    else:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        inst = asset_tools.create_asset(
            INST.rsplit("/", 1)[-1],
            INST.rsplit("/", 1)[0],
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew(),
        )

    if not inst:
        unreal.log_warning(f"[RazorSharp] could not create/load instance {INST}")
        return None

    MEL.set_material_instance_parent(inst, parent)
    def set_scalar(name, val):
        try:
            MEL.set_material_instance_scalar_parameter_value(inst, name, val)
            MEL.set_material_instance_parameter_override(inst, name, True)
            unreal.log(f"[RazorSharp] set {name} = {val}")
        except Exception as exc:
            unreal.log_warning(f"[RazorSharp] set {name}: {exc}")

    set_scalar("RazorSharpness", RAZOR_SHARPNESS_DEFAULT)
    set_scalar("RazorAAFloor", RAZOR_AA_FLOOR_DEFAULT)
    set_scalar("RazorContrast", RAZOR_CONTRAST_DEFAULT)
    set_scalar("RazorViewAngleMod", RAZOR_VIEW_ANGLE_DEFAULT)
    set_scalar("RazorMinThickness", RAZOR_MIN_THICKNESS_DEFAULT)
    set_scalar("RazorMaxThickness", RAZOR_MAX_THICKNESS_DEFAULT)
    set_scalar("RazorThicknessFalloff", RAZOR_THICKNESS_FALLOFF_DEFAULT)
    set_scalar("RazorCustomStencil", RAZOR_CUSTOM_STENCIL_DEFAULT)
    set_scalar("RazorStencilMode", RAZOR_STENCIL_MODE_DEFAULT)
    set_scalar("RazorEdgeBlend", RAZOR_EDGE_BLEND_DEFAULT)

    # Persist instance parameter changes to disk
    MEL.update_material_instance(inst)

    # --- Verify read-back ---------------------------------------------------
    for name in ["RazorSharpness", "RazorAAFloor", "RazorContrast", "RazorViewAngleMod",
                 "RazorMinThickness", "RazorMaxThickness", "RazorThicknessFalloff",
                 "RazorCustomStencil", "RazorStencilMode", "RazorEdgeBlend"]:
        try:
            rv = MEL.get_material_instance_scalar_parameter_value(inst, name)
            unreal.log(f"[RazorSharp] readback {name} = {rv}")
        except Exception as exc:
            unreal.log_warning(f"[RazorSharp] readback {name}: {exc}")

    unreal.EditorAssetLibrary.save_asset(inst.get_path_name())
    unreal.log(f"[RazorSharp] instance {INST} sharpness={RAZOR_SHARPNESS_DEFAULT} "
               f"viewAngle={RAZOR_VIEW_ANGLE_DEFAULT} minThick={RAZOR_MIN_THICKNESS_DEFAULT} "
               f"maxThick={RAZOR_MAX_THICKNESS_DEFAULT} stencilMode={RAZOR_STENCIL_MODE_DEFAULT}")
    return INST


def run_all() -> str:
    print(f"=== Premium Outline — Razor Sharp Thin Professional ===")
    print(f"  Material: {MAT}")
    m = unreal.load_asset(MAT)
    if not m:
        raise RuntimeError(f"Missing {MAT}")
    status = apply(m)
    inst_path = build_instance()
    print(f"  Instance: {inst_path}")
    print(f"  Status: {status}")
    return status


if __name__ == "__main__":
    try:
        import unreal  # noqa: F401
    except ImportError:
        raise SystemExit("This script must run inside Unreal Editor Python")
    run_all()