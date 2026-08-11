"""Wire the FabricType system on M_Master_Toon_Universal (Substrate Toon BSDF).

Adds the style-peak FabricAnisoGate Custom HLSL node and injects it into
BSDF.Anisotropy through a lerp (A = ToonAnisotropy, B = gate, Alpha = gate), a
FabricWeaveGate lerp (A = Constant 0, B = FabricWeaveNormal, Alpha =
FabricWeaveStrength) injected into the BSDF Normal chain behind
StaticSwitchParameter_12's False branch via a FabricNormalBlend scalar, plus an
unconnected FabricWeaveTangent (0,1,0) vector constant. DO NOT touch BSDF.Tangent.

Default-value safe: with FabricType=0, FabricAnisoLevel=0, FabricWeaveStrength=0
and FabricNormalBlend=0 every gate resolves to passthrough/0, so the visual
result is identical to the pre-wire state.

Idempotent: every node is matched by description / parameter_name and skipped if
present. Runs top-to-bottom (exec()).
"""

import unreal

import material_lib as lib

MATERIAL_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
BSDF_TYPE_PREFIX = "MaterialExpressionSubstrateToonBSDF"
GROUP = "10 | Nikki Iridescence & Sheen"
SWITCH_NAME = "StaticSwitchParameter_12"
WEAVE_CUSTOM_DESCS = ("Procedural fabric weave normal perturbation", "FabricWeaveNormal")

FABRIC_ANISO_HLSL = """float a = 0.0;
// Silk (2), Satin (3), Sequins (7) get strong anisotropy
a += smoothstep(1.5, 2.5, FabricType) * 0.9;         // silk
a += smoothstep(2.5, 3.5, FabricType) * 0.95;        // satin
a += smoothstep(6.5, 7.5, FabricType) * 0.7;         // sequins
a += smoothstep(0.5, 1.5, FabricType) * 0.15;        // cotton slight
return saturate(a + FabricAnisoLevel);
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
        if _expr_type(e).startswith(BSDF_TYPE_PREFIX):
            return e
    return None


def _find_by_name(exprs, wanted):
    for e in exprs:
        if e.get_name() == wanted:
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


def _find_weave_custom(exprs):
    for e in exprs:
        if _expr_type(e) != "MaterialExpressionCustom":
            continue
        for marker in WEAVE_CUSTOM_DESCS:
            try:
                if str(e.get_editor_property("description")) == marker:
                    return e
            except Exception:
                pass
            try:
                if str(e.get_editor_property("name")) == marker:
                    return e
            except Exception:
                pass
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


def _create_lerp(material, desc_text, x, y):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, x, y
    )
    node.set_editor_property("desc", desc_text)
    return node


def _static_switch_false_pin(switch):
    names = list(
        unreal.MaterialEditingLibrary.get_material_expression_input_names(switch) or []
    )
    for candidate in ("False", "false", "FALSE", "B", "b", "No", "no"):
        if candidate in names:
            return names.index(candidate), names[names.index(candidate)]
    return None, None


def _custom_input_source(node, input_name):
    try:
        for ci in (node.get_editor_property("inputs") or []):
            if str(ci.get_editor_property("input_name")) == input_name:
                inp = ci.get_editor_property("input")
                if inp:
                    try:
                        return inp.get_editor_property("expression")
                    except Exception:
                        return None
                return None
    except Exception:
        pass
    return None


def main():
    mel = unreal.MaterialEditingLibrary
    lib_eal = unreal.EditorAssetLibrary

    material = lib_eal.load_asset(MATERIAL_PATH)
    if not material:
        print("[WireFabric] FAILED to load material %s" % MATERIAL_PATH)
        return
    print("[WireFabric] Loaded %s" % MATERIAL_PATH)

    exprs = list(mel.get_material_expressions(material) or [])
    material.modify()

    bsdf = _find_bsdf(exprs)
    if not bsdf:
        print("[WireFabric] FAILED: no SubstrateToonBSDF on material — aborting")
        return
    print("[WireFabric] BSDF found: %s" % _expr_type(bsdf))

    bsdf_x, bsdf_y = 1400, 0
    try:
        pos = mel.get_material_expression_node_position(bsdf)
        if pos:
            bsdf_x, bsdf_y = int(pos.x), int(pos.y)
    except Exception:
        pass

    fabric_type = _find_param(exprs, "MaterialExpressionScalarParameter", "FabricType")
    aniso_level = _find_param(exprs, "MaterialExpressionScalarParameter", "FabricAnisoLevel")
    toon_aniso = _find_param(exprs, "MaterialExpressionScalarParameter", "ToonAnisotropy")
    weave_scale = _find_param(exprs, "MaterialExpressionScalarParameter", "FabricWeaveScale")
    weave_strength = _find_param(exprs, "MaterialExpressionScalarParameter", "FabricWeaveStrength")
    weave_custom = _find_weave_custom(exprs)
    # Resolve the Normal switch structurally via BSDF.Normal (name may shift).
    switch_12 = None
    bsdf_names = list(mel.get_material_expression_input_names(bsdf) or [])
    bsdf_wired = list(mel.get_inputs_for_material_expression(material, bsdf) or [])
    nrm_idx = None
    for candidate in ("Normal",):
        if candidate in bsdf_names:
            nrm_idx = bsdf_names.index(candidate)
            break
    if nrm_idx is not None and nrm_idx < len(bsdf_wired):
        switch_12 = bsdf_wired[nrm_idx]
    if switch_12:
        print("[WireFabric] Normal switch resolved structurally: %s" % switch_12.get_name())

    for name, found in (
        ("FabricType", fabric_type), ("FabricAnisoLevel", aniso_level),
        ("ToonAnisotropy", toon_aniso), ("FabricWeaveScale", weave_scale),
        ("FabricWeaveStrength", weave_strength), ("FabricWeaveNormal", weave_custom),
    ):
        if not found:
            print("[WireFabric] WARN: expected node/param not found: %s" % name)
    if not switch_12:
        print("[WireFabric] WARN: %s not found — normal-chain inject will be skipped" % SWITCH_NAME)

    # ── 1. FabricAnisoGate Custom HLSL node ────────────────────────────────
    aniso_gate = _find_custom(exprs, "FabricAnisoGate")
    if not aniso_gate:
        print("[WireFabric] Create Custom node FabricAnisoGate (CMOT_FLOAT1, style-peak)")
        aniso_gate = _create_custom(
            material, "FabricAnisoGate", FABRIC_ANISO_HLSL,
            unreal.CustomMaterialOutputType.CMOT_FLOAT1,
            ("FabricType", "FabricAnisoLevel"),
            bsdf_x - 900, bsdf_y + 120,
        )
    else:
        print("[WireFabric] Reuse existing FabricAnisoGate")
    if fabric_type:
        print("[WireFabric] Wire FabricType -> FabricAnisoGate.FabricType")
        _wire(fabric_type, "", aniso_gate, "FabricType")
    if aniso_level:
        print("[WireFabric] Wire FabricAnisoLevel -> FabricAnisoGate.FabricAnisoLevel")
        _wire(aniso_level, "", aniso_gate, "FabricAnisoLevel")

    # ── 2. Inject FabricAnisoGate into BSDF.Anisotropy via lerp ────────────
    aniso_lerp = _find_by_desc(exprs, "FabricAniso_GateLerp")
    if not aniso_lerp:
        print("[WireFabric] Create LinearInterpolate FabricAniso_GateLerp")
        aniso_lerp = _create_lerp(material, "FabricAniso_GateLerp", bsdf_x - 500, bsdf_y + 100)
    else:
        print("[WireFabric] Reuse existing FabricAniso_GateLerp")

    bsdf_names = list(mel.get_material_expression_input_names(bsdf) or [])
    bsdf_wired = list(mel.get_inputs_for_material_expression(material, bsdf) or [])
    aniso_idx = None
    for candidate in ("Anisotropy", "Aniso"):
        if candidate in bsdf_names:
            aniso_idx = bsdf_names.index(candidate)
            break
    current_aniso = None
    if aniso_idx is not None and aniso_idx < len(bsdf_wired):
        current_aniso = bsdf_wired[aniso_idx]

    aniso_a = toon_aniso if toon_aniso else (
        None if current_aniso == aniso_lerp else current_aniso
    )
    if not aniso_a:
        print("[WireFabric] SKIP Anisotropy rewire: no ToonAnisotropy param and no current source")
    else:
        if current_aniso:
            print("[WireFabric] Anisotropy current source: %s" % (
                _expr_type(current_aniso) if current_aniso else "UNCONNECTED"))
        print("[WireFabric] Wire %s -> FabricAniso_GateLerp.A" % (
            "ToonAnisotropy" if aniso_a == toon_aniso else _expr_type(aniso_a)))
        _wire(aniso_a, "", aniso_lerp, "A")
        print("[WireFabric] Wire FabricAnisoGate -> FabricAniso_GateLerp.B")
        _wire(aniso_gate, "", aniso_lerp, "B")
        print("[WireFabric] Wire FabricAnisoGate -> FabricAniso_GateLerp.Alpha")
        _wire(aniso_gate, "", aniso_lerp, "Alpha")
        print("[WireFabric] Wire FabricAniso_GateLerp -> BSDF.Anisotropy (targeted rewire)")
        _wire(aniso_lerp, "", bsdf, "Anisotropy")

    # ── 3. FabricWeaveGate lerp (A = 0, B = FabricWeaveNormal, Alpha = strength) ──
    weave_gate = _find_by_desc(exprs, "FabricWeaveGate")
    if not weave_gate:
        print("[WireFabric] Create LinearInterpolate FabricWeaveGate")
        weave_gate = _create_lerp(material, "FabricWeaveGate", bsdf_x - 900, bsdf_y + 360)
    else:
        print("[WireFabric] Reuse existing FabricWeaveGate")

    weave_zero = _find_by_desc(exprs, "FabricWeaveGate_Zero")
    if not weave_zero:
        print("[WireFabric] Create Constant FabricWeaveGate_Zero (0)")
        weave_zero = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, bsdf_x - 1100, bsdf_y + 380
        )
        weave_zero.set_editor_property("desc", "FabricWeaveGate_Zero")
        weave_zero.set_editor_property("R", 0.0)
    else:
        print("[WireFabric] Reuse existing FabricWeaveGate_Zero")

    if weave_custom:
        # Additive wiring of the (currently unconnected) weave HLSL inputs so the
        # perturbation is actually driven by the existing scale/strength params.
        if not _custom_input_source(weave_custom, "WeaveScale") and weave_scale:
            print("[WireFabric] Wire FabricWeaveScale -> FabricWeaveNormal.WeaveScale")
            _wire(weave_scale, "", weave_custom, "WeaveScale")
        else:
            print("[WireFabric] SKIP FabricWeaveNormal.WeaveScale — already connected or param missing")
        if not _custom_input_source(weave_custom, "WeaveStrength") and weave_strength:
            print("[WireFabric] Wire FabricWeaveStrength -> FabricWeaveNormal.WeaveStrength")
            _wire(weave_strength, "", weave_custom, "WeaveStrength")
        else:
            print("[WireFabric] SKIP FabricWeaveNormal.WeaveStrength — already connected or param missing")

    print("[WireFabric] Wire FabricWeaveGate_Zero -> FabricWeaveGate.A")
    _wire(weave_zero, "", weave_gate, "A")
    if weave_custom:
        print("[WireFabric] Wire FabricWeaveNormal -> FabricWeaveGate.B")
        _wire(weave_custom, "", weave_gate, "B")
    if weave_strength:
        print("[WireFabric] Wire FabricWeaveStrength -> FabricWeaveGate.Alpha")
        _wire(weave_strength, "", weave_gate, "Alpha")

    # ── 4. Inject FabricWeaveGate into BSDF Normal chain (switch False branch) ──
    normal_lerp = None
    if switch_12:
        false_idx, false_pin = _static_switch_false_pin(switch_12)
        sw_wired = list(mel.get_inputs_for_material_expression(material, switch_12) or [])
        false_src = None
        if false_pin and false_idx is not None and false_idx < len(sw_wired):
            false_src = sw_wired[false_idx]
        print("[WireFabric] %s False pin '%s', source: %s" % (
            SWITCH_NAME, false_pin, _expr_type(false_src) if false_src else "UNCONNECTED"))
        if false_pin and false_src:
            blend_param = _find_param(exprs, "MaterialExpressionScalarParameter", "FabricNormalBlend")
            if not blend_param:
                print("[WireFabric] Create ScalarParameter FabricNormalBlend (0, 0-1)")
                blend_param = lib.scalar_param(
                    material, "FabricNormalBlend", GROUP, 0.0, bsdf_x - 1200, bsdf_y + 560
                )
                blend_param.set_editor_property("slider_min", 0.0)
                blend_param.set_editor_property("slider_max", 1.0)
            else:
                print("[WireFabric] Reuse existing FabricNormalBlend")
            normal_lerp = _find_by_desc(exprs, "FabricNormal_WeaveLerp")
            if not normal_lerp:
                print("[WireFabric] Create LinearInterpolate FabricNormal_WeaveLerp")
                normal_lerp = _create_lerp(material, "FabricNormal_WeaveLerp", bsdf_x - 600, bsdf_y + 560)
            else:
                print("[WireFabric] Reuse existing FabricNormal_WeaveLerp")
            print("[WireFabric] Wire current False source (%s) -> FabricNormal_WeaveLerp.A" % _expr_type(false_src))
            _wire(false_src, "", normal_lerp, "A")
            print("[WireFabric] Wire FabricWeaveGate -> FabricNormal_WeaveLerp.B")
            _wire(weave_gate, "", normal_lerp, "B")
            print("[WireFabric] Wire FabricNormalBlend -> FabricNormal_WeaveLerp.Alpha")
            _wire(blend_param, "", normal_lerp, "Alpha")
            print("[WireFabric] Wire FabricNormal_WeaveLerp -> %s.%s (targeted rewire)" % (SWITCH_NAME, false_pin))
            _wire(normal_lerp, "", switch_12, false_pin)
        else:
            print("[WireFabric] SKIP normal inject: switch False pin or its source not found")
    else:
        print("[WireFabric] SKIP normal inject: %s not found" % SWITCH_NAME)

    # ── 5. FabricWeaveTangent vector constant (0,1,0) — unconnected ───────
    tangent = _find_by_desc(exprs, "FabricWeaveTangent")
    if not tangent:
        print("[WireFabric] Create Constant3Vector FabricWeaveTangent (0,1,0) — unconnected")
        tangent = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, bsdf_x - 300, bsdf_y + 720
        )
        tangent.set_editor_property("desc", "FabricWeaveTangent")
        tangent.set_editor_property("constant", unreal.LinearColor(0.0, 1.0, 0.0, 0.0))
    else:
        print("[WireFabric] Reuse existing FabricWeaveTangent")
    print("[WireFabric] BSDF.Tangent left UNCONNECTED (per spec)")

    # ── 6. Save + recompile ───────────────────────────────────────────────
    print("[WireFabric] Recompile material")
    try:
        mel.recompile_material(material)
    except Exception as exc:
        print("[WireFabric] Recompile raised: %s" % exc)
    lib_eal.save_loaded_asset(material, only_if_is_dirty=False)
    print("[WireFabric] Saved %s" % MATERIAL_PATH)

    print("[WireFabric] REPORT: aniso_gate=%s aniso_lerp=%s weave_gate=%s weave_zero=%s normal_lerp=%s blend=%s tangent=%s" % (
        "ok" if aniso_gate else "missing",
        "wired" if aniso_a else "skipped",
        "ok" if weave_gate else "missing",
        "ok" if weave_zero else "missing",
        "wired" if normal_lerp else "skipped",
        "ok" if _find_param(list(mel.get_material_expressions(material) or []),
                            "MaterialExpressionScalarParameter", "FabricNormalBlend") else "missing",
        "ok" if tangent else "missing",
    ))


main()
