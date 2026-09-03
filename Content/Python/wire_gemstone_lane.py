"""
Wire the gemstone lane on M_Master_Toon_Universal (Substrate Toon BSDF).

Creates GemstoneF0 + GemstoneEmissive Custom HLSL nodes, gates the sparkle
layer behind bGemstone_Active, and injects it into the StaticSwitchParameter
that feeds the BSDF EmissiveColor. Default (bGemstone_Active=False) is
bit-identical to the pre-wire state. Idempotent: every node is matched by
description and skipped if present. Run top-to-bottom (works with exec()).
"""

import unreal

MATERIAL_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

GROUP = "06 | Gemstone"

F0_HLSL = """float eta = saturate(IOR);
float F0 = ((eta - 1.0) * (eta - 1.0)) / ((eta + 1.0) * (eta + 1.0));
return float3(F0, F0, F0) * GemstoneTint;
"""

EMISSIVE_HLSL = """// sparkle: hash-snapped grid in view space
float2 ip = floor(Parameters.WorldPosition.xz * GlintScale);
float h = frac(sin(dot(ip, float2(12.9898, 78.233))) * 43758.5453);
float sparkle = step(0.995 - GlintIntensity * 0.004, h);
return sparkle * GemstoneTint * ChromaticStrength;
"""


def _expr_type(expr):
    return type(expr).__name__


def _desc(expr):
    for prop in ("description", "desc"):
        try:
            raw = expr.get_editor_property(prop)
            if raw:
                return str(raw)
        except Exception:
            pass
    return ""


def _find_bsdf(exprs):
    for e in exprs:
        if _expr_type(e).startswith("MaterialExpressionSubstrateToonBSDF"):
            return e
    return None


def _find_param(exprs, cls_name, param_name):
    for e in exprs:
        if _expr_type(e) != cls_name:
            continue
        try:
            if str(e.get_editor_property("parameter_name")) == param_name:
                return e
        except Exception:
            pass
    return None


def _find_by_desc(exprs, wanted):
    for e in exprs:
        if _desc(e) == wanted:
            return e
    return None


def _find_custom(exprs, wanted):
    for e in exprs:
        if _expr_type(e) == "MaterialExpressionCustom" and _desc(e) == wanted:
            return e
    return None


def _wire(from_expr, from_out, to_expr, to_in):
    try:
        result = unreal.MaterialEditingLibrary.connect_material_expressions(
            from_expr, from_out, to_expr, to_in
        )
        return result is not False
    except Exception:
        return False


def _create_custom(material, desc_text, code, output_type, input_names, x, y):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionCustom, x, y
    )
    node.set_editor_property("description", desc_text)
    node.set_editor_property("code", code)
    node.set_editor_property("output_type", output_type)
    inputs = []
    for name in input_names:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", name)
        inputs.append(ci)
    node.set_editor_property("inputs", inputs)
    return node


def _static_switch_true_index(switch):
    names = list(unreal.MaterialEditingLibrary.get_material_expression_input_names(switch) or [])
    for candidate in ("True", "true", "TRUE", "A", "a"):
        if candidate in names:
            return names.index(candidate), names[names.index(candidate)]
    if names:
        return 0, names[0]
    return None, None


def _make_gate(material, exprs, emissive, bool_param, base_x, base_y):
    gate = _find_by_desc(exprs, "GemstoneLane_Gate")
    if not gate:
        print("[WireGem] Create LinearInterpolate GemstoneLane_Gate (gate emissive)")
        gate = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionLinearInterpolate, base_x, base_y
        )
        gate.set_editor_property("desc", "GemstoneLane_Gate")
    else:
        print("[WireGem] Reuse existing GemstoneLane_Gate")
    zero = _find_by_desc(exprs, "GemstoneLane_Zero")
    if not zero:
        print("[WireGem] Create Constant3Vector GemstoneLane_Zero")
        zero = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, base_x, base_y + 120
        )
        zero.set_editor_property("desc", "GemstoneLane_Zero")
        zero.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
    else:
        print("[WireGem] Reuse existing GemstoneLane_Zero")
    print("[WireGem] Wire GemstoneLane_Zero -> Gate.A")
    _wire(zero, "", gate, "A")
    print("[WireGem] Wire GemstoneEmissive -> Gate.B")
    _wire(emissive, "", gate, "B")
    print("[WireGem] Wire bGemstone_Active -> Gate.Alpha")
    _wire(bool_param, "", gate, "Alpha")
    return gate


def _make_inject(material, exprs, true_src, gate, bool_param, base_x, base_y):
    inject = _find_by_desc(exprs, "GemstoneLane_EmissiveInject")
    if not inject:
        print("[WireGem] Create LinearInterpolate GemstoneLane_EmissiveInject")
        inject = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionLinearInterpolate, base_x, base_y
        )
        inject.set_editor_property("desc", "GemstoneLane_EmissiveInject")
    else:
        print("[WireGem] Reuse existing GemstoneLane_EmissiveInject")
    print("[WireGem] Wire existing emissive source -> Inject.A")
    _wire(true_src, "", inject, "A")
    print("[WireGem] Wire gated GemstoneEmissive -> Inject.B")
    _wire(gate, "", inject, "B")
    print("[WireGem] Wire bGemstone_Active -> Inject.Alpha")
    _wire(bool_param, "", inject, "Alpha")
    return inject


def main():
    mel = unreal.MaterialEditingLibrary
    lib = unreal.EditorAssetLibrary

    material = lib.load_asset(MATERIAL_PATH)
    if not material:
        print("[WireGem] FAILED to load material %s" % MATERIAL_PATH)
        return

    exprs = list(mel.get_material_expressions(material) or [])
    material.modify()

    bsdf = _find_bsdf(exprs)
    if not bsdf:
        print("[WireGem] FAILED: no SubstrateToonBSDF on material")
    else:
        print("[WireGem] BSDF found: %s" % _expr_type(bsdf))

    bool_param = _find_param(exprs, "MaterialExpressionStaticBoolParameter", "bGemstone_Active")
    ior_param = _find_param(exprs, "MaterialExpressionScalarParameter", "IOR")
    tint_param = _find_param(exprs, "MaterialExpressionVectorParameter", "GemstoneTint")
    scale_param = _find_param(exprs, "MaterialExpressionScalarParameter", "GlintScale")
    inten_param = _find_param(exprs, "MaterialExpressionScalarParameter", "GlintIntensity")
    chroma_param = _find_param(exprs, "MaterialExpressionScalarParameter", "ChromaticStrength")

    missing = [n for n, p in (
        ("bGemstone_Active", bool_param), ("IOR", ior_param), ("GemstoneTint", tint_param),
        ("GlintScale", scale_param), ("GlintIntensity", inten_param),
        ("ChromaticStrength", chroma_param),
    ) if not p]
    if missing:
        print("[WireGem] FAILED: missing params %s" % missing)
        return

    bsdf_x = 1400
    bsdf_y = 0
    try:
        pos = mel.get_material_expression_node_position(bsdf) if bsdf else None
        if pos:
            bsdf_x, bsdf_y = int(pos.x), int(pos.y)
    except Exception:
        pass

    f0_state = "existing"
    f0 = _find_custom(exprs, "GemstoneF0")
    if not f0:
        print("[WireGem] Create Custom node GemstoneF0")
        f0 = _create_custom(
            material, "GemstoneF0", F0_HLSL,
            unreal.CustomMaterialOutputType.CMOT_FLOAT3,
            ("IOR", "GemstoneTint"), bsdf_x + 300, bsdf_y - 200,
        )
        f0_state = "created"
    else:
        print("[WireGem] Reuse existing GemstoneF0")
    print("[WireGem] Wire IOR -> GemstoneF0.IOR")
    _wire(ior_param, "", f0, "IOR")
    print("[WireGem] Wire GemstoneTint -> GemstoneF0.GemstoneTint")
    _wire(tint_param, "RGB", f0, "GemstoneTint")

    emissive = _find_custom(exprs, "GemstoneEmissive")
    emissive_state = "existing"
    if not emissive:
        print("[WireGem] Create Custom node GemstoneEmissive")
        emissive = _create_custom(
            material, "GemstoneEmissive", EMISSIVE_HLSL,
            unreal.CustomMaterialOutputType.CMOT_FLOAT3,
            ("GlintScale", "GlintIntensity", "GemstoneTint", "ChromaticStrength"),
            bsdf_x + 300, bsdf_y + 40,
        )
        emissive_state = "created"
    else:
        print("[WireGem] Reuse existing GemstoneEmissive")
    print("[WireGem] Wire GlintScale -> GemstoneEmissive.GlintScale")
    _wire(scale_param, "", emissive, "GlintScale")
    print("[WireGem] Wire GlintIntensity -> GemstoneEmissive.GlintIntensity")
    _wire(inten_param, "", emissive, "GlintIntensity")
    print("[WireGem] Wire GemstoneTint -> GemstoneEmissive.GemstoneTint")
    _wire(tint_param, "RGB", emissive, "GemstoneTint")
    print("[WireGem] Wire ChromaticStrength -> GemstoneEmissive.ChromaticStrength")
    _wire(chroma_param, "", emissive, "ChromaticStrength")

    gate = _make_gate(material, exprs, emissive, bool_param, bsdf_x + 300, bsdf_y + 260)

    switch = None
    true_pin = None
    true_src = None
    if bsdf:
        bsdf_names = list(mel.get_material_expression_input_names(bsdf) or [])
        emissive_idx = None
        for candidate in ("EmissiveColor", "Emissive"):
            if candidate in bsdf_names:
                emissive_idx = bsdf_names.index(candidate)
                break
        if emissive_idx is not None:
            wired = list(mel.get_inputs_for_material_expression(material, bsdf) or [])
            src = wired[emissive_idx] if emissive_idx < len(wired) else None
            if src and _expr_type(src).startswith("MaterialExpressionStaticSwitchParameter"):
                switch = src
                true_idx, true_pin = _static_switch_true_index(switch)
                if true_pin:
                    sw_wired = list(mel.get_inputs_for_material_expression(material, switch) or [])
                    true_src = sw_wired[true_idx] if true_idx < len(sw_wired) else None
        if switch:
            print("[WireGem] Emissive source switch: %s (true pin '%s', source %s)" % (
                _expr_type(switch), true_pin,
                _expr_type(true_src) if true_src else "None"))
        else:
            print("[WireGem] SKIP inject: EmissiveColor not fed by a StaticSwitchParameter")

    if switch and true_pin and true_src:
        inject = _make_inject(material, exprs, true_src, gate, bool_param, bsdf_x + 300, bsdf_y + 420)
        print("[WireGem] Wire GemstoneLane_EmissiveInject -> switch '%s'" % true_pin)
        _wire(inject, "", switch, true_pin)
    else:
        inject = None
        print("[WireGem] SKIP inject: switch/true pin/source not found - default emissive untouched")

    print("[WireGem] Recompile material")
    try:
        mel.recompile_material(material)
    except Exception as exc:
        print("[WireGem] Recompile raised: %s" % exc)
    lib.save_loaded_asset(material, only_if_is_dirty=False)
    print("[WireGem] Saved %s" % MATERIAL_PATH)

    print("[WireGem] REPORT: GemstoneF0=%s GemstoneEmissive=%s Gate=%s Inject=%s" % (
        f0_state,
        emissive_state,
        "ok" if gate else "missing",
        "wired" if inject else "skipped",
    ))


main()
