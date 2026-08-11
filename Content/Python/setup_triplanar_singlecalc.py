"""Add single-calc triplanar UVs + slope-gated per-channel blend to M_Master_Toon_Universal.

Replaces 18 separate WorldAlignedTexture/WAT function calls with one Custom HLSL
node that computes 3 world-projected UVs + blend weights in a single pass.

Adds:
  - bTriplanar_Active (StaticBool, default False)
  - TriplanarSlopeStart, TriplanarSlopeEnd (scalar, group Triplanar)
  - TriplanarBlend_Albedo, _Normal, _Roughness (scalar, group Triplanar)
  - TriplanarUVs Custom HLSL node
  - Slope-gated per-channel wiring into existing TextureSample nodes on all 3 layers

Run in Unreal Editor:
  import setup_triplanar_singlecalc; setup_triplanar_singlecalc.main()
"""

import unreal
import material_lib as lib

MATERIAL_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
GROUP = "Triplanar"

TRIPLANAR_UVS_HLSL = """\
float3 worldPos = Parameters.WorldPosition;
float3 normal = abs(Parameters.WorldNormal);
float3 weights = pow(normal, TriplanarSharpness);
weights /= dot(weights, float3(1,1,1));

float2 uvX = worldPos.yz * TriplanarTiling;
float2 uvY = worldPos.xz * TriplanarTiling;
float2 uvZ = worldPos.xy * TriplanarTiling;

float4 triUV1 = float4(uvX, uvY);
float4 triUV2 = float4(uvZ.xy, weights.xy);
float output_unused = weights.z;
"""


def param_by_name(material, name):
    for expr in (unreal.MaterialEditingLibrary.get_material_expressions(material) or []):
        try:
            if (hasattr(expr, "has_editor_property") and
                    expr.has_editor_property("parameter_name") and
                    str(expr.get_editor_property("parameter_name")) == name):
                return expr
        except Exception:
            pass
    return None


def group_params(material):
    """Build {param_name: expression} from all parameter expressions."""
    result = {}
    for expr in (unreal.MaterialEditingLibrary.get_material_expressions(material) or []):
        try:
            if hasattr(expr, "has_editor_property") and expr.has_editor_property("parameter_name"):
                result[str(expr.get_editor_property("parameter_name"))] = expr
        except Exception:
            pass
    return result


def expr_in(material, expr, input_idx):
    """Return the expression connected to expr's input_idx, or None."""
    if not expr:
        return None
    try:
        inputs = list(
            unreal.MaterialEditingLibrary.get_inputs_for_material_expression(material, expr) or []
        )
        if input_idx < len(inputs):
            return inputs[input_idx]
    except Exception:
        pass
    return None


def input_names(expr):
    try:
        return list(unreal.MaterialEditingLibrary.get_material_expression_input_names(expr) or [])
    except Exception:
        return []


def find_uv_input_idx(expr):
    names = input_names(expr)
    for i, n in enumerate(names):
        if n.lower() in ("uvs", "coordinates", "uv", "texcoord", "coordinate"):
            return i
    return None


def main():
    MEL = unreal.MaterialEditingLibrary
    con = MEL.connect_material_expressions

    if not unreal.EditorAssetLibrary.does_asset_exist(MATERIAL_PATH):
        print(f"ERROR: Material not found at {MATERIAL_PATH}")
        return

    mat = unreal.EditorAssetLibrary.load_asset(MATERIAL_PATH)
    if not mat:
        print(f"ERROR: Could not load material at {MATERIAL_PATH}")
        return

    print(f"Material: {MATERIAL_PATH}")
    existing = group_params(mat)
    created = []
    reused = []

    # ──────────────────────────────────────────────
    # 1. Parameters (skip if already exist)
    # ──────────────────────────────────────────────

    if "bTriplanar_Active" not in existing:
        sw = lib.create_expression(mat, unreal.MaterialExpressionStaticSwitchParameter, -1800, -200)
        sw.set_editor_property("parameter_name", "bTriplanar_Active")
        sw.set_editor_property("default_value", False)
        sw.set_editor_property("group", GROUP)
        created.append("bTriplanar_Active")
    else:
        reused.append("bTriplanar_Active")

    for pname, default, smin, smax in [
        ("TriplanarSlopeStart", 0.35, 0.0, 1.0),
        ("TriplanarSlopeEnd", 0.72, 0.0, 1.0),
        ("TriplanarBlend_Albedo", 0.0, 0.0, 1.0),
        ("TriplanarBlend_Normal", 0.0, 0.0, 1.0),
        ("TriplanarBlend_Roughness", 0.0, 0.0, 1.0),
    ]:
        if pname not in existing:
            p = lib.scalar_param(mat, pname, GROUP, default, -1800, 0)
            p.set_editor_property("slider_min", smin)
            p.set_editor_property("slider_max", smax)
            created.append(pname)
        else:
            reused.append(pname)

    # ──────────────────────────────────────────────
    # 2. TriplanarUVs Custom HLSL node
    # ──────────────────────────────────────────────

    custom = None
    for e in (MEL.get_material_expressions(mat) or []):
        if type(e).__name__ == "MaterialExpressionCustom" and getattr(e, "description", None) == "TriplanarUVs":
            custom = e
            break

    if not custom:
        custom = lib.create_expression(mat, unreal.MaterialExpressionCustom, -1600, 200)
        custom.set_editor_property("description", "TriplanarUVs")
        custom.set_editor_property("code", TRIPLANAR_UVS_HLSL)
        custom.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT4)

        # Inputs
        inputs = list(custom.get_editor_property("inputs") or [])
        if not inputs:
            for inp_name in ("TriplanarSharpness", "TriplanarTiling"):
                ci = unreal.CustomInput()
                ci.set_editor_property("input_name", inp_name)
                inputs.append(ci)
            custom.set_editor_property("inputs", inputs)

        # Additional outputs (triUV2 float4 + output_unused float)
        try:
            extra = list(custom.get_editor_property("additional_outputs") or [])
            if len(extra) < 2:
                extra = []
                o2 = unreal.CustomOutput()
                o2.set_editor_property("output_name", "triUV2")
                o2.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT4)
                extra.append(o2)
                o3 = unreal.CustomOutput()
                o3.set_editor_property("output_name", "output_unused")
                o3.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT_1)
                extra.append(o3)
                custom.set_editor_property("additional_outputs", extra)
        except Exception:
            pass

        created.append("TriplanarUVs (Custom HLSL)")
    else:
        reused.append("TriplanarUVs (Custom HLSL)")

    # Wire scalar params to custom node inputs
    for inp_name in ("TriplanarSharpness", "TriplanarTiling"):
        p = param_by_name(mat, inp_name)
        if p:
            con(p, "", custom, inp_name)

    # Re-read param dict after adding new ones
    existing = group_params(mat)

    # ──────────────────────────────────────────────
    # 3. Slope gating chain (shared by all layers)
    # ──────────────────────────────────────────────

    slope_start = existing.get("TriplanarSlopeStart")
    slope_end = existing.get("TriplanarSlopeEnd")

    normal_node = None
    slope_blend = None

    if slope_start and slope_end:
        # steepness = 1 - dot(normal, (0,0,1))
        normal_node = lib.create_expression(mat, unreal.MaterialExpressionPixelNormalWS, -1400, 1400)
        up_vec = lib.create_expression(mat, unreal.MaterialExpressionConstant3Vector, -1400, 1500)
        up_vec.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 0.0))
        dot_node = lib.create_expression(mat, unreal.MaterialExpressionDotProduct, -1220, 1450)
        con(normal_node, "", dot_node, "A")
        con(up_vec, "", dot_node, "B")
        one_minus = lib.create_expression(mat, unreal.MaterialExpressionOneMinus, -1060, 1450)
        lib.connect_unary(dot_node, one_minus)

        # remap [slope_start, slope_end] -> [0, 1]
        sub_start = lib.create_expression(mat, unreal.MaterialExpressionSubtract, -900, 1400)
        con(one_minus, "", sub_start, "A")
        con(slope_start, "", sub_start, "B")
        sub_span = lib.create_expression(mat, unreal.MaterialExpressionSubtract, -900, 1500)
        con(slope_end, "", sub_span, "A")
        con(slope_start, "", sub_span, "B")
        div_node = lib.create_expression(mat, unreal.MaterialExpressionDivide, -740, 1450)
        con(sub_start, "", div_node, "A")
        con(sub_span, "", div_node, "B")
        slope_blend = lib.create_expression(mat, unreal.MaterialExpressionSaturate, -600, 1450)
        lib.connect_unary(div_node, slope_blend)

        created.append("Slope gating chain")
    else:
        print("  Skipped slope gating — missing TriplanarSlopeStart/End params")

    # ──────────────────────────────────────────────
    # 4. Wire triplanar UVs into texture samples
    # ──────────────────────────────────────────────

    # Channel blend param lookup
    blend_params = {
        "Albedo": existing.get("TriplanarBlend_Albedo"),
        "Normal": existing.get("TriplanarBlend_Normal"),
        "Roughness": existing.get("TriplanarBlend_Roughness"),
    }

    # Texture parameter name -> channel classification
    def classify_tex_param(pname):
        """Return (layer_key, channel) or (None, None)."""
        p = pname.lower()
        if "albedo" in p:
            chan = "Albedo"
        elif "normal" in p:
            chan = "Normal"
        elif "roughness" in p or "rough" in p:
            chan = "Roughness"
        elif "orm" in p:
            chan = "Roughness"
        elif "height" in p:
            chan = "Albedo"
        elif "metallic" in p:
            chan = "Roughness"
        else:
            return None, None

        if p.startswith("layerb_"):
            return "B", chan
        elif p.startswith("layerc_"):
            return "C", chan
        elif p == "albedo" or p == "normalmap" or p == "orm" or p == "heightmap" or p == "roughnessmap" or p == "metallicmap":
            return "A", chan
        return None, None

    # Find all texture sample nodes that have UV inputs
    all_exprs = list(MEL.get_material_expressions(mat) or [])
    tex_samples = [e for e in all_exprs
                   if type(e).__name__ in ("MaterialExpressionTextureSample",
                                           "MaterialExpressionTextureSampleParameter2D")]

    wired = 0
    skipped_no_uv = 0
    skipped_no_tex = 0
    used_switches = set()

    for s in tex_samples:
        # Determine texture param name
        tname = None
        try:
            if hasattr(s, "has_editor_property") and s.has_editor_property("parameter_name"):
                tname = str(s.get_editor_property("parameter_name"))
            elif hasattr(s, "has_editor_property") and s.has_editor_property("texture"):
                tex_obj = s.get_editor_property("texture")
                if tex_obj and hasattr(tex_obj, "has_editor_property") and tex_obj.has_editor_property("parameter_name"):
                    tname = str(tex_obj.get_editor_property("parameter_name"))
        except Exception:
            pass

        if not tname:
            skipped_no_tex += 1
            continue

        layer, channel = classify_tex_param(tname)
        if layer is None:
            skipped_no_tex += 1
            continue

        # Find UV input index
        uv_idx = find_uv_input_idx(s)
        if uv_idx is None:
            skipped_no_uv += 1
            continue

        # Get current UV source
        old_uv = expr_in(mat, s, uv_idx)
        if old_uv is None:
            skipped_no_uv += 1
            continue

        # Choose triplanar UV based on layer
        # A -> uvX (YZ projection, from triUV1.xy)
        # B -> uvY (XZ projection, from triUV1.zw)
        # C -> uvZ (XY projection, from triUV2.xy)
        if layer == "A":
            mask_r = True; mask_g = True; mask_b = False; mask_a = False
            src_node = custom
            src_pin = ""
        elif layer == "B":
            mask_r = False; mask_g = False; mask_b = True; mask_a = True
            src_node = custom
            src_pin = ""
        else:
            mask_r = True; mask_g = True; mask_b = False; mask_a = False
            src_node = custom
            src_pin = "triUV2"

        # Extract the right channels from custom node output as float2
        cm = lib.create_expression(mat, unreal.MaterialExpressionComponentMask, -400, 0)
        cm.set_editor_property("r", mask_r)
        cm.set_editor_property("g", mask_g)
        cm.set_editor_property("b", mask_b)
        cm.set_editor_property("a", mask_a)
        con(src_node, src_pin, cm, "")

        # Compute blend factor: bTriplanar_Active * slope_blend * channel_blend
        # First multiply: slope * channel_blend
        chan_blend = blend_params.get(channel)
        if chan_blend and slope_blend:
            factor = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -200, 0)
            con(slope_blend, "", factor, "A")
            con(chan_blend, "", factor, "B")
        elif chan_blend:
            factor = chan_blend
        elif slope_blend:
            factor = slope_blend
        else:
            factor = None

        # Lerp: old_uv <-> tri_uv by factor
        if factor:
            lerp_node = lib.create_expression(mat, unreal.MaterialExpressionLinearInterpolate, -50, 0)
            con(old_uv, "", lerp_node, "A")
            con(cm, "", lerp_node, "B")
            con(factor, "", lerp_node, "Alpha")
            tri_uv_src = lerp_node
        else:
            tri_uv_src = cm

        # Gate with bTriplanar_Active static switch
        sw = lib.create_expression(mat, unreal.MaterialExpressionStaticSwitchParameter, 120, 0)
        sw.set_editor_property("parameter_name", "bTriplanar_Active")
        sw.set_editor_property("default_value", False)
        sw.set_editor_property("group", GROUP)
        con(old_uv, "", sw, "False")
        con(tri_uv_src, "", sw, "True")
        used_switches.add(str(sw.get_name()))

        # Wire switch to texture sample UV input
        try:
            con(sw, "", s, input_names(s)[uv_idx] if input_names(s) else "")
            wired += 1
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # 5. Compile + save
    # ──────────────────────────────────────────────

    MEL.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)

    print(f"\nParams created: {len(created)} ({', '.join(created[:6])}{'...' if len(created) > 6 else ''})")
    print(f"Params reused: {len(reused)}")
    print(f"Texture samples wired: {wired}")
    print(f"Skipped (no UV input): {skipped_no_uv}")
    print(f"Skipped (unclassified): {skipped_no_tex}")


if __name__ == "__main__":
    main()
