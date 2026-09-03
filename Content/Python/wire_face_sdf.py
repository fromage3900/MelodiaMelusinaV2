"""Wire the Face SDF shadow mask + skin wrap-light SSS on M_Master_Toon_Universal.

Face SDF: builds FaceSDFUV (UV1) -> tiling -> FaceSDFSample (R) -> FaceSDFMask
(HLSL) -> OneMinus -> FaceSDFGate (lit mask, default 1.0) -> FaceSDFApply
inserted into StaticSwitchParameter_10's True pin (BSDF BaseColor source).
SkinSSS: finds the NdotL DotProduct, wires the existing SkinSSS custom node and
injects a SkinSSSGate lerp (A = current NdotL, B = SkinSSS, Alpha = strength)
back into the NdotL consumer.

Default-value safe: FaceSDF_Strength=0 and SkinSSS_Strength=0 resolve every
gate to passthrough, so visuals are identical to the pre-wire state.
NOTE: FaceSDFApply is wired as base x FaceSDFGate (Alpha pinned to 1.0) rather
than the literal base x mask / gate-alpha chain: the literal chain outputs
black at Strength=0 (mask=0 -> B=0, gate=1 -> lerp picks B), violating the
default-identical rule. The gate IS the strength-gated lit mask, so
base x gate gives exactly the intended darkening while staying neutral at 0.

Idempotent: the whole Face SDF section is skipped when the FaceSDFMask custom
node exists; the SkinSSS section is skipped when the SkinSSSGate lerp exists.
Runs top-to-bottom (exec()).
"""

import unreal

import material_lib as lib

MATERIAL_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
GROUP = "09 | Character"
BSDF_PREFIX = "MaterialExpressionSubstrateToonBSDF"
SWITCH_NAME = "StaticSwitchParameter_10"
BASE_TRUE_SOURCE_NAME = "LinearInterpolate_3"

FACESDF_HLSL = """// SDF face shadow: darken shadows on the face region
// FaceSDF texture: white=lit area, black=shadow area
float mask = 1.0 - SDFValue;            // 0 = lit, 1 = shadowed
return mask * FaceSDFStrength;
"""

SKINSSS_HLSL = """float wrap = 1.0 + SkinSSSRadius;
float sss = saturate((NdotL + SkinSSSRadius) / (wrap * wrap));
return lerp(NdotL, sss, SkinSSSStrength);"""

NORMAL_NODE_NAMES = ("MaterialExpressionVertexNormalWS", "MaterialExpressionPixelNormalWS")
LIGHTISH_NODE_NAMES = ("MaterialExpressionConstant3Vector",)
LIGHTISH_TYPE_MARKERS = ("LightVector", "LightDirection")

CHAIN_Y_OFFSET = 760


def _expr_type(expr):
    return type(expr).__name__


def _node_stem(expr):
    name = str(expr.get_name())
    if name.startswith("MaterialExpression"):
        return name[len("MaterialExpression"):]
    return name


def _desc(expr):
    for prop in ("description", "desc"):
        try:
            raw = expr.get_editor_property(prop)
            if raw:
                return str(raw)
        except Exception:
            pass
    return ""


def _set_desc(expr, text):
    for prop in ("description", "desc"):
        try:
            if expr.has_editor_property(prop):
                expr.set_editor_property(prop, text)
                return
        except Exception:
            continue


def _find_bsdf(exprs):
    for e in exprs:
        if _expr_type(e).startswith(BSDF_PREFIX):
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


def _find_custom(exprs, wanted):
    for e in exprs:
        if _expr_type(e) != "MaterialExpressionCustom":
            continue
        for marker in (wanted, "description"):
            try:
                if str(e.get_editor_property("description")) == wanted:
                    return e
            except Exception:
                pass
        if _desc(e) == wanted:
            return e
    return None


def _find_by_desc(exprs, wanted):
    for e in exprs:
        if _desc(e) == wanted:
            return e
    return None


def _find_skinsss_custom(exprs):
    for e in exprs:
        if _expr_type(e) != "MaterialExpressionCustom":
            continue
        if _desc(e) == "SkinSSS":
            return e
        try:
            names = [str(ci.get_editor_property("input_name")) for ci in (e.get_editor_property("inputs") or [])]
        except Exception:
            names = []
        try:
            code = str(e.get_editor_property("code") or "")
        except Exception:
            code = ""
        if all(n in names for n in ("NdotL", "SkinSSSStrength", "SkinSSSRadius")) and "wrap" in code:
            return e
    return None


def _wire(from_expr, from_output, to_expr, to_input):
    try:
        result = unreal.MaterialEditingLibrary.connect_material_expressions(
            from_expr, from_output, to_expr, to_input
        )
        return result is not False
    except Exception:
        return False


def _pin_names(expr):
    try:
        return list(unreal.MaterialEditingLibrary.get_material_expression_input_names(expr) or [])
    except Exception:
        return []


def _wired_sources(material, expr):
    try:
        return list(unreal.MaterialEditingLibrary.get_inputs_for_material_expression(material, expr) or [])
    except Exception:
        return []


def _pin_index(expr, candidates):
    pins = _pin_names(expr)
    for wanted in candidates:
        for i, name in enumerate(pins):
            if str(name).lower() == wanted.lower():
                return i, name
    return None, None


def _create_custom(material, desc_text, code, input_names, x, y):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionCustom, x, y
    )
    node.set_editor_property("description", desc_text)
    node.set_editor_property("code", code)
    node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
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
    _set_desc(node, desc_text)
    return node


def _create_const1(material, desc_text, x, y):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, x, y
    )
    _set_desc(node, desc_text)
    for prop in ("r", "constant"):
        try:
            node.set_editor_property(prop, 1.0)
            break
        except Exception:
            continue
    return node


def _chain_has(material, expr, markers, depth):
    if not expr:
        return False
    if _expr_type(expr) in markers:
        return True
    if depth <= 0:
        return False
    for src in _wired_sources(material, expr):
        if src and _chain_has(material, src, markers, depth - 1):
            return True
    return False


def _is_lightish(expr):
    tname = _expr_type(expr)
    if tname in LIGHTISH_NODE_NAMES:
        return True
    for marker in LIGHTISH_TYPE_MARKERS:
        if marker in tname:
            return True
    return False


def _find_ndotl(material, exprs):
    mel = unreal.MaterialEditingLibrary
    dots = [e for e in exprs if _expr_type(e) == "MaterialExpressionDotProduct"]
    for dot in dots:
        pins = _pin_names(dot)
        wired = _wired_sources(material, dot)
        a_idx, a_pin = _pin_index(dot, ("A", "a", "Input0", "R"))
        b_idx, b_pin = _pin_index(dot, ("B", "b", "Input1", "G"))
        src_a = wired[a_idx] if a_idx is not None and a_idx < len(wired) else None
        src_b = wired[b_idx] if b_idx is not None and b_idx < len(wired) else None
        if src_a is None or src_b is None:
            continue
        a_is_normal = _chain_has(material, src_a, NORMAL_NODE_NAMES, 3)
        b_is_normal = _chain_has(material, src_b, NORMAL_NODE_NAMES, 3)
        if a_is_normal and _is_lightish(src_b):
            return dot, src_a, src_b
        if b_is_normal and _is_lightish(src_a):
            return dot, src_b, src_a
    return None, None, None


def _find_consumers(material, exprs, source):
    consumers = []
    for expr in exprs:
        if expr == source:
            continue
        pins = _pin_names(expr)
        wired = _wired_sources(material, expr)
        for i, src in enumerate(wired):
            if src is not None and src == source:
                pin = pins[i] if i < len(pins) else ""
                consumers.append((expr, pin))
    return consumers


def _wire_face_sdf(material, exprs, mel):
    # Resolve the BaseColor switch structurally via BSDF.BaseColor (name may
    # change after node renumbering).
    bsdf = _find_bsdf(exprs)
    if not bsdf:
        print("[WireFace] FAILED: BSDF not found — face SDF section aborted")
        return None
    bsdf_names = list(mel.get_material_expression_input_names(bsdf) or [])
    bsdf_wired = list(mel.get_inputs_for_material_expression(material, bsdf) or [])
    base_idx = None
    for candidate in ("BaseColor", "DiffuseColor"):
        if candidate in bsdf_names:
            base_idx = bsdf_names.index(candidate)
            break
    switch = None
    if base_idx is not None and base_idx < len(bsdf_wired):
        switch = bsdf_wired[base_idx]
    if not switch or "StaticSwitchParameter" not in _expr_type(switch):
        print("[WireFace] FAILED: BSDF.BaseColor source is not a switch — face SDF section aborted")
        return None
    print("[WireFace] BaseColor switch resolved structurally: %s" % switch.get_name())
    switch_x, switch_y = -520, 0
    try:
        pos = mel.get_material_expression_node_position(switch)
        if pos:
            switch_x, switch_y = int(pos.x), int(pos.y)
    except Exception:
        pass

    true_idx, true_pin = _pin_index(switch, ("True", "true", "A", "a"))
    if true_idx is None:
        print("[WireFace] FAILED: no True pin on %s (pins=%s)" % (
            SWITCH_NAME, _pin_names(switch)))
        return None
    switch_wired = _wired_sources(material, switch)
    base_src = switch_wired[true_idx] if true_idx < len(switch_wired) else None
    if not base_src:
        print("[WireFace] FAILED: %s.True has no source — aborted" % SWITCH_NAME)
        return None
    print("[WireFace] Anchor: %s.True pin '%s' source = %s (%s)" % (
        SWITCH_NAME, true_pin, base_src.get_name(), _expr_type(base_src)))
    if _node_stem(base_src) != BASE_TRUE_SOURCE_NAME:
        print("[WireFace] WARN: True source is %s, expected %s — continuing with actual source" % (
            _node_stem(base_src), BASE_TRUE_SOURCE_NAME))

    tex_param = _find_param(exprs, "MaterialExpressionTextureObjectParameter", "FaceSDF_Texture")
    strength = _find_param(exprs, "MaterialExpressionScalarParameter", "FaceSDF_Strength")
    tiling = _find_param(exprs, "MaterialExpressionScalarParameter", "FaceSDF_Tiling")
    uv1 = _find_param(exprs, "MaterialExpressionStaticBoolParameter", "bFaceSDF_UV1")
    for name, node in (("FaceSDF_Texture", tex_param), ("FaceSDF_Strength", strength),
                       ("FaceSDF_Tiling", tiling), ("bFaceSDF_UV1", uv1)):
        if not node:
            print("[WireFace] WARN: expected param not found: %s" % name)
    if strength:
        try:
            print("[WireFace] FaceSDF_Strength default = %s" % strength.get_editor_property("default_value"))
        except Exception:
            pass

    chain_y = switch_y + CHAIN_Y_OFFSET
    sx = switch_x

    if _find_custom(exprs, "FaceSDFMask"):
        print("[WireFace] SKIP face SDF section — FaceSDFMask custom node already exists")
        return base_src

    uv = _find_by_desc(exprs, "FaceSDFUV")
    if not uv:
        print("[WireFace] Create TextureCoordinate FaceSDFUV (uv_index=%s)" % (
            "1" if (uv1 and uv1.get_editor_property("default_value")) else "0"))
        uv = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureCoordinate, sx - 2300, chain_y
        )
        _set_desc(uv, "FaceSDFUV")
    else:
        print("[WireFace] Reuse existing FaceSDFUV")
    uv_index = 1 if (uv1 and uv1.get_editor_property("default_value")) else 0
    uv.set_editor_property("coordinate_index", uv_index)

    tiling_mul = _find_by_desc(exprs, "FaceSDF_TilingMul")
    if not tiling_mul:
        print("[WireFace] Create Multiply FaceSDF_TilingMul (Tiling x UV)")
        tiling_mul = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionMultiply, sx - 2080, chain_y
        )
        _set_desc(tiling_mul, "FaceSDF_TilingMul")
    else:
        print("[WireFace] Reuse existing FaceSDF_TilingMul")
    if tiling:
        print("[WireFace] Wire FaceSDF_Tiling -> FaceSDF_TilingMul.A")
        _wire(tiling, "", tiling_mul, "A")
    print("[WireFace] Wire FaceSDFUV -> FaceSDF_TilingMul.B")
    _wire(uv, "", tiling_mul, "B")

    sample = _find_by_desc(exprs, "FaceSDFSample")
    if not sample:
        print("[WireFace] Create TextureSample FaceSDFSample")
        sample = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSample, sx - 1860, chain_y
        )
        _set_desc(sample, "FaceSDFSample")
    else:
        print("[WireFace] Reuse existing FaceSDFSample")
    if tex_param:
        print("[WireFace] Wire FaceSDF_Texture -> FaceSDFSample.TextureObject")
        _wire(tex_param, "", sample, "TextureObject")
    else:
        print("[WireFace] WARN: FaceSDF_Texture missing — sample left on default texture")
    print("[WireFace] Wire FaceSDF_TilingMul -> FaceSDFSample.Coordinates")
    _wire(tiling_mul, "", sample, "Coordinates")

    mask_r = _find_by_desc(exprs, "FaceSDF_MaskR")
    if not mask_r:
        print("[WireFace] Create ComponentMask FaceSDF_MaskR (R only)")
        mask_r = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionComponentMask, sx - 1640, chain_y
        )
        _set_desc(mask_r, "FaceSDF_MaskR")
        mask_r.set_editor_property("r", True)
        mask_r.set_editor_property("g", False)
        mask_r.set_editor_property("b", False)
        mask_r.set_editor_property("a", False)
    else:
        print("[WireFace] Reuse existing FaceSDF_MaskR")
    print("[WireFace] Wire FaceSDFSample -> FaceSDF_MaskR.Input")
    _wire(sample, "", mask_r, "Input")

    sdf_mask = _find_custom(exprs, "FaceSDFMask")
    if not sdf_mask:
        print("[WireFace] Create Custom FaceSDFMask (CMOT_FLOAT1)")
        sdf_mask = _create_custom(
            material, "FaceSDFMask", FACESDF_HLSL,
            ("SDFValue", "FaceSDFStrength"), sx - 1420, chain_y
        )
    else:
        print("[WireFace] Reuse existing FaceSDFMask")
    print("[WireFace] Wire FaceSDF_MaskR -> FaceSDFMask.SDFValue")
    _wire(mask_r, "", sdf_mask, "SDFValue")
    if strength:
        print("[WireFace] Wire FaceSDF_Strength -> FaceSDFMask.FaceSDFStrength")
        _wire(strength, "", sdf_mask, "FaceSDFStrength")

    one_minus = _find_by_desc(exprs, "FaceSDF_OneMinus")
    if not one_minus:
        print("[WireFace] Create OneMinus FaceSDF_OneMinus")
        one_minus = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionOneMinus, sx - 1200, chain_y - 40
        )
        _set_desc(one_minus, "FaceSDF_OneMinus")
    else:
        print("[WireFace] Reuse existing FaceSDF_OneMinus")
    print("[WireFace] Wire FaceSDFMask -> FaceSDF_OneMinus.Input")
    _wire(sdf_mask, "", one_minus, "Input")

    gate = _find_by_desc(exprs, "FaceSDFGate")
    if not gate:
        print("[WireFace] Create LinearInterpolate FaceSDFGate (A=1, B=1-mask, Alpha=Strength)")
        gate = _create_lerp(material, "FaceSDFGate", sx - 980, chain_y - 80)
    else:
        print("[WireFace] Reuse existing FaceSDFGate")
    gate_one = _find_by_desc(exprs, "FaceSDFGate_One")
    if not gate_one:
        print("[WireFace] Create Constant FaceSDFGate_One (1.0)")
        gate_one = _create_const1(material, "FaceSDFGate_One", sx - 1200, chain_y + 20)
    else:
        print("[WireFace] Reuse existing FaceSDFGate_One")
    print("[WireFace] Wire FaceSDFGate_One -> FaceSDFGate.A")
    _wire(gate_one, "", gate, "A")
    print("[WireFace] Wire FaceSDF_OneMinus -> FaceSDFGate.B")
    _wire(one_minus, "", gate, "B")
    if strength:
        print("[WireFace] Wire FaceSDF_Strength -> FaceSDFGate.Alpha")
        _wire(strength, "", gate, "Alpha")

    apply_mul = _find_by_desc(exprs, "FaceSDFApply_Mul")
    if not apply_mul:
        print("[WireFace] Create Multiply FaceSDFApply_Mul (BaseColor x FaceSDFGate)")
        apply_mul = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionMultiply, sx - 560, chain_y + 40
        )
        _set_desc(apply_mul, "FaceSDFApply_Mul")
    else:
        print("[WireFace] Reuse existing FaceSDFApply_Mul")
    print("[WireFace] Wire %s -> FaceSDFApply_Mul.A" % base_src.get_name())
    _wire(base_src, "", apply_mul, "A")
    print("[WireFace] Wire FaceSDFGate -> FaceSDFApply_Mul.B")
    _wire(gate, "", apply_mul, "B")

    apply = _find_by_desc(exprs, "FaceSDFApply")
    if not apply:
        print("[WireFace] Create LinearInterpolate FaceSDFApply (A=base, B=base x gate, Alpha=1)")
        apply = _create_lerp(material, "FaceSDFApply", sx - 300, chain_y + 120)
    else:
        print("[WireFace] Reuse existing FaceSDFApply")
    apply_one = _find_by_desc(exprs, "FaceSDFApply_One")
    if not apply_one:
        print("[WireFace] Create Constant FaceSDFApply_One (1.0)")
        apply_one = _create_const1(material, "FaceSDFApply_One", sx - 480, chain_y + 200)
    else:
        print("[WireFace] Reuse existing FaceSDFApply_One")
    print("[WireFace] Wire %s -> FaceSDFApply.A" % base_src.get_name())
    _wire(base_src, "", apply, "A")
    print("[WireFace] Wire FaceSDFApply_Mul -> FaceSDFApply.B")
    _wire(apply_mul, "", apply, "B")
    print("[WireFace] Wire FaceSDFApply_One -> FaceSDFApply.Alpha")
    _wire(apply_one, "", apply, "Alpha")

    print("[WireFace] Wire FaceSDFApply -> %s.%s (targeted rewire)" % (SWITCH_NAME, true_pin))
    _wire(apply, "", switch, true_pin)
    return base_src


def _wire_skin_sss(material, exprs, mel):
    sss_strength = _find_param(exprs, "MaterialExpressionScalarParameter", "SkinSSS_Strength")
    sss_radius = _find_param(exprs, "MaterialExpressionScalarParameter", "SkinSSS_Radius")
    skin = _find_skinsss_custom(exprs)
    if not skin:
        print("[WireFace] Create Custom SkinSSS (CMOT_FLOAT1, wrap-light)")
        x, y = -1400, 1400
        skin = _create_custom(material, "SkinSSS", SKINSSS_HLSL,
                              ("NdotL", "SkinSSSStrength", "SkinSSSRadius"), x, y)
    else:
        print("[WireFace] Reuse existing SkinSSS custom node")

    if _find_by_desc(exprs, "SkinSSSGate"):
        print("[WireFace] SKIP SkinSSS section — SkinSSSGate already exists")
        return None, None

    ndotl, normal_src, light_src = _find_ndotl(material, exprs)
    if not ndotl:
        print("[WireFace] NdotL source not found — manual hookup needed")
        print("[WireFace] SkinSSS left unconnected (NdotL, SkinSSSStrength, SkinSSSRadius)"
              " — rerun after adding a VertexNormalWS/LightVector DotProduct")
        return None, None

    print("[WireFace] Anchor: NdotL DotProduct = %s (A=%s %s, B=%s %s)" % (
        ndotl.get_name(),
        normal_src.get_name() if normal_src else "?",
        _expr_type(normal_src) if normal_src else "?",
        light_src.get_name() if light_src else "?",
        _expr_type(light_src) if light_src else "?"))

    gate = _find_by_desc(exprs, "SkinSSSGate")
    if not gate:
        print("[WireFace] Create LinearInterpolate SkinSSSGate (A=NdotL, B=SkinSSS, Alpha=Strength)")
        gate = _create_lerp(material, "SkinSSSGate", -1400, 1560)
    else:
        print("[WireFace] Reuse existing SkinSSSGate")

    print("[WireFace] Wire %s -> SkinSSSGate.A (current NdotL)" % ndotl.get_name())
    _wire(ndotl, "", gate, "A")
    print("[WireFace] Wire SkinSSS -> SkinSSSGate.B")
    _wire(skin, "", gate, "B")
    if sss_strength:
        print("[WireFace] Wire SkinSSS_Strength -> SkinSSSGate.Alpha")
        _wire(sss_strength, "", gate, "Alpha")

    print("[WireFace] Wire %s -> SkinSSS.NdotL" % ndotl.get_name())
    _wire(ndotl, "", skin, "NdotL")
    if sss_strength:
        print("[WireFace] Wire SkinSSS_Strength -> SkinSSS.SkinSSSStrength")
        _wire(sss_strength, "", skin, "SkinSSSStrength")
    if sss_radius:
        print("[WireFace] Wire SkinSSS_Radius -> SkinSSS.SkinSSSRadius")
        _wire(sss_radius, "", skin, "SkinSSSRadius")

    consumers = _find_consumers(material, exprs, ndotl)
    if not consumers:
        print("[WireFace] WARN: %s output has no consumers — SkinSSSGate wired but not injected" % ndotl.get_name())
    for consumer, pin in consumers:
        print("[WireFace] Wire SkinSSSGate -> %s.%s (targeted rewire)" % (
            consumer.get_name(), pin or "?"))
        _wire(gate, "", consumer, pin)
    return ndotl, len(consumers)


def main():
    mel = unreal.MaterialEditingLibrary
    lib_eal = unreal.EditorAssetLibrary

    material = lib_eal.load_asset(MATERIAL_PATH)
    if not material:
        print("[WireFace] FAILED to load material %s" % MATERIAL_PATH)
        return
    print("[WireFace] Loaded %s" % MATERIAL_PATH)

    exprs = list(mel.get_material_expressions(material) or [])
    material.modify()

    bsdf = _find_bsdf(exprs)
    if not bsdf:
        print("[WireFace] FAILED: no SubstrateToonBSDF on material — aborting")
        return
    print("[WireFace] BSDF found: %s" % _expr_type(bsdf))

    base_src = _wire_face_sdf(material, exprs, mel)
    ndotl, consumer_count = _wire_skin_sss(material, exprs, mel)

    print("[WireFace] Recompile material")
    try:
        mel.recompile_material(material)
    except Exception as exc:
        print("[WireFace] Recompile raised: %s" % exc)
    lib_eal.save_loaded_asset(material, only_if_is_dirty=False)
    print("[WireFace] Saved %s" % MATERIAL_PATH)

    print("[WireFace] REPORT: bsdf=%s switch=True_src=%s face_sdf=%s ndotl=%s sss_consumers_rewired=%s" % (
        _expr_type(bsdf),
        base_src.get_name() if base_src else "MISSING",
        "wired" if _find_custom(list(mel.get_material_expressions(material) or []), "FaceSDFMask") else "skipped",
        ndotl.get_name() if ndotl else "NOT_FOUND",
        consumer_count if consumer_count is not None else "skipped",
    ))


main()
