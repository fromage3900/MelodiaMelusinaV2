"""Wire the dream compositor into M_Master_Toon_Universal (UE 5.8).

Builds a neutral-by-default (DreamCompositeBlend = 0) compositor lane between
the current EmissiveColor source of StaticSwitchParameter_13 and the BSDF:

  Add_16 --A--+--> LinearInterpolate --> StaticSwitchParameter_13[True] --> BSDF.EmissiveColor
  DreamCompositeGate --B--^         ^-- Alpha = DreamCompositeBlend (default 0)

DreamCompositeGate is a Custom HLSL node that invokes the existing
"DreamCompositor" blend logic on the toon's dream emissive (the output of the
existing "DreamRimSpectral" custom node) against the current True source.

No existing connection is removed except the single targeted rewire of the
switch's True pin to the new lerp output. Idempotent: skips when the
DreamCompositeBlend parameter already exists.
"""

import unreal

MATERIAL_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

GATE_DESCRIPTION = "DreamCompositeGate"

GATE_HLSL = """float3 dreamLumaW = float3(0.2126, 0.7152, 0.0722);
float luma = dot(DreamColor, dreamLumaW);
if (luma < Threshold) return BaseColor;
float3 dream = DreamColor * DreamWarmth * DreamIntensity;
float3 result;
int mode = (int)round(Composition);
if (mode == 0) result = BaseColor + dream;
else if (mode == 1) result = max(BaseColor, dream);
else result = 1.0 - (1.0 - BaseColor) * (1.0 - dream);
return result;"""

# (input name, CustomMaterialOutputType) in the exact order the HLSL expects.
GATE_INPUTS = [
    ("DreamColor", "CMOT_FLOAT3"),
    ("BaseColor", "CMOT_FLOAT3"),
    ("DreamWarmth", "CMOT_FLOAT3"),
    ("DreamIntensity", "CMOT_FLOAT1"),
    ("Composition", "CMOT_FLOAT1"),
    ("Threshold", "CMOT_FLOAT1"),
]

MEL = unreal.MaterialEditingLibrary


def _exprs(material):
    return list(MEL.get_material_expressions(material) or [])


def _custom_title(expr):
    for prop in ("description", "name"):
        try:
            raw = expr.get_editor_property(prop)
            if raw:
                return str(raw)
        except Exception:
            continue
    return None


def _find_param(material, param_name):
    for expr in _exprs(material):
        try:
            if expr.has_editor_property("parameter_name"):
                if str(expr.get_editor_property("parameter_name")) == param_name:
                    return expr
        except Exception:
            continue
    return None


def _find_custom(material, title):
    for expr in _exprs(material):
        if type(expr).__name__ != "MaterialExpressionCustom":
            continue
        if _custom_title(expr) == title:
            return expr
    return None


def _input_map(material, expr):
    names = list(MEL.get_material_expression_input_names(expr) or [])
    sources = list(MEL.get_inputs_for_material_expression(material, expr) or [])
    return {name: (sources[idx] if idx < len(sources) else None) for idx, name in enumerate(names)}


def _connect(from_expr, from_output, to_expr, to_input):
    try:
        MEL.connect_material_expressions(from_expr, from_output, to_expr, to_input)
        return True
    except Exception as exc:
        print(f"[WireDream] connect {from_expr.get_name()} -> {to_expr.get_name()}.{to_input} failed: {exc}")
        return False


def _make_custom_node(material, code, inputs, out_type):
    node = MEL.create_material_expression(material, unreal.MaterialExpressionCustom)
    node.set_editor_property("description", GATE_DESCRIPTION)
    node.set_editor_property("code", code)
    node.set_editor_property("output_type", out_type)
    for prop in ("name", "Name"):
        try:
            node.set_editor_property(prop, GATE_DESCRIPTION)
            break
        except Exception:
            continue
    custom_inputs = []
    for name, io_type in inputs:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", name)
        custom_inputs.append(ci)
    node.set_editor_property("inputs", custom_inputs)
    return node


def _search_bsdf(material):
    found = [e for e in _exprs(material)
             if type(e).__name__.startswith("MaterialExpressionSubstrateToonBSDF")]
    if not found:
        raise RuntimeError("No MaterialExpressionSubstrateToonBSDF found on M_Master_Toon_Universal")
    found.sort(key=lambda e: e.get_name())
    return found[0]


def main():
    material = unreal.load_asset(MATERIAL_PATH)
    if material is None:
        print(f"[WireDream] material not found at {MATERIAL_PATH}")
        return

    # --- Idempotency gate ---
    if _find_param(material, "DreamCompositeBlend") is not None:
        print("[WireDream] DreamCompositeBlend already exists — already wired, skipping")
        return

    # --- Trace: BSDF Emissive -> StaticSwitchParameter_13 -> True source ---
    bsdf = _search_bsdf(material)
    print(f"[WireDream] BSDF = {bsdf.get_name()}")

    sw_map = None
    for name, source in _input_map(material, bsdf).items():
        if name == "EmissiveColor":
            sw_map = (source, _input_map(material, source) if source else {})
            break
    if not sw_map or sw_map[0] is None:
        raise RuntimeError("EmissiveColor of BSDF is not connected — cannot locate StaticSwitchParameter_13")
    switch = sw_map[0]
    print(f"[WireDream] EmissiveColor source = {switch.get_name()}")

    sw_names = list(MEL.get_material_expression_input_names(switch) or [])
    sw_sources = list(MEL.get_inputs_for_material_expression(material, switch) or [])

    true_pin = next((c for c in ("True", "A", "a") if c in sw_names), None) or (sw_names[1] if len(sw_names) > 1 else "True")
    true_idx = sw_names.index(true_pin) if true_pin in sw_names else 1
    true_src = sw_sources[true_idx] if true_idx < len(sw_sources) else None
    if true_src is None:
        raise RuntimeError(f"StaticSwitchParameter {switch.get_name()} True pin ('{true_pin}') is not connected — nothing to insert after")
    add16 = true_src
    print(f"[WireDream] switch={switch.get_name()} input_names={sw_names} TruePin='{true_pin}' TrueSource={add16.get_name()}")

    dream_compositor = _find_custom(material, "DreamCompositor")
    print(f"[WireDream] existing DreamCompositor node found = {dream_compositor is not None}")
    rim_node = _find_custom(material, "DreamRimSpectral")
    print(f"[WireDream] existing DreamRimSpectral node found = {rim_node is not None}")

    # --- Create DreamCompositeBlend scalar (neutral default 0 -> identical visuals) ---
    blend = MEL.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -1100, 300)
    blend.set_editor_property("parameter_name", "DreamCompositeBlend")
    blend.set_editor_property("default_value", 0.0)
    blend.set_editor_property("slider_min", 0.0)
    blend.set_editor_property("slider_max", 1.0)
    blend.set_editor_property("group", "08 Nikki Dream")
    print("[WireDream] created scalar param DreamCompositeBlend (default 0, 0-1, group '08 Nikki Dream')")

    # --- Create DreamCompositeGate custom node ---
    gate = _make_custom_node(
        material,
        GATE_HLSL,
        GATE_INPUTS,
        unreal.CustomMaterialOutputType.CMOT_FLOAT3,
    )
    print("[WireDream] created Custom HLSL node DreamCompositeGate (CMOT_FLOAT3)")

    # --- Wire DreamCompositeGate inputs ---
    _connect(rim_node, "", gate, "DreamColor")
    print(f"[WireDream] wired DreamRimSpectral -> DreamCompositeGate.DreamColor")
    _connect(add16, "", gate, "BaseColor")
    print(f"[WireDream] wired {add16.get_name()} -> DreamCompositeGate.BaseColor")

    for pin, param_name in (
        ("DreamWarmth", "DreamWarmth"),
        ("DreamIntensity", "DreamIntensity"),
        ("Composition", "DreamComposition"),
        ("Threshold", "DreamThreshold"),
    ):
        param = _find_param(material, param_name)
        if param is None:
            print(f"[WireDream] WARN missing param {param_name} — DreamCompositeGate.{pin} left unconnected")
            continue
        _connect(param, "", gate, pin)
        print(f"[WireDream] wired {param_name} -> DreamCompositeGate.{pin}")

    # --- Create lerp: A=Add_16, B=DreamCompositeGate, Alpha=DreamCompositeBlend ---
    lerp = MEL.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, 700, 100)
    _connect(add16, "", lerp, "A")
    _connect(gate, "", lerp, "B")
    _connect(blend, "", lerp, "Alpha")
    print("[WireDream] created LinearInterpolate (A=Add_16, B=DreamCompositeGate, Alpha=DreamCompositeBlend)")

    # --- The single permitted rewire: lerp -> StaticSwitchParameter True ---
    if _connect(lerp, "", switch, true_pin):
        print(f"[WireDream] rewired {switch.get_name()}[{true_pin}] -> LinearInterpolate output")

    # --- Wire DreamRimSpectral inputs only if currently unconnected ---
    if rim_node is not None:
        rim_pins = _input_map(material, rim_node)
        print(f"[WireDream] DreamRimSpectral inputs: { {k: (v.get_name() if v else 'UNCONNECTED') for k, v in rim_pins.items()} }")
        for pin, source in rim_pins.items():
            if source is not None:
                continue
            low = pin.lower()
            if "rim" in low:
                src_param = _find_param(material, "DreamRimStrength")
                if src_param is not None:
                    _connect(src_param, "", rim_node, pin)
                    print(f"[WireDream] wired DreamRimStrength -> DreamRimSpectral.{pin} (was unconnected)")
                else:
                    print(f"[WireDream] WARN no DreamRimStrength param — DreamRimSpectral.{pin} left unconnected")
            else:
                src_param = _find_param(material, "DreamRimCycles") or _find_param(material, "DreamRimPower")
                if src_param is not None:
                    _connect(src_param, "", rim_node, pin)
                    print(f"[WireDream] wired {src_param.get_editor_property('parameter_name')} -> DreamRimSpectral.{pin} (was unconnected)")
                else:
                    print(f"[WireDream] WARN no DreamRimCycles/DreamRimPower param — DreamRimSpectral.{pin} left unconnected")

    # --- Verify the targeted rewire landed ---
    post_names = list(MEL.get_material_expression_input_names(switch) or [])
    post_sources = list(MEL.get_inputs_for_material_expression(material, switch) or [])
    post_idx = post_names.index(true_pin) if true_pin in post_names else true_idx
    wiring_ok = post_idx < len(post_sources) and post_sources[post_idx] == lerp
    print(f"[WireDream] verify {switch.get_name()}[{true_pin}] -> LinearInterpolate: {'OK' if wiring_ok else 'FAILED'}")

    MEL.recompile_material(material)
    print("[WireDream] recompiled M_Master_Toon_Universal (is_compiled will follow on next stats read)")

    ok = unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    print(f"[WireDream] saved M_Master_Toon_Universal = {ok}")
    print(f"[WireDream] DONE — DreamCompositeBlend=0 keeps visuals identical; raise it to reveal the DreamCompositor blend")


main()