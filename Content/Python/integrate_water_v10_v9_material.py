"""Build the additive Water v10 material upgrade from the complete v9 graph.

The v9 master remains untouched as the rollback/reference asset.  This script
duplicates it once, inserts MF_WaterNativeInteraction_v10, and routes native
Water state additively around the existing v9 wave, ripple, foam, WPO, and
bioluminescence paths.

Run in the UE editor through Monolith:
    exec(open('Content/Python/integrate_water_v10_v9_material.py').read())
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

import material_lib as lib


MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade"
NATIVE_FUNCTION = "/Game/EnvSandbox/Materials/Functions/MF_WaterNativeInteraction_v10"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "water_v10_v9_material_integration.json"
GROUP = "Water v10 | Native Additive"


def _expressions(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def _find(material, name):
    return next((e for e in _expressions(material) if e and e.get_name() == name), None)


def _find_param(material, name):
    for expr in _expressions(material):
        if not expr or "Parameter" not in type(expr).__name__ or "Function" in type(expr).__name__:
            continue
        try:
            if str(expr.get_editor_property("parameter_name")) == name:
                return expr
        except Exception:
            pass
    return None


def _find_function_call(material, leaf_name):
    for expr in _expressions(material):
        if not expr or type(expr).__name__ != "MaterialExpressionMaterialFunctionCall":
            continue
        try:
            fn = expr.get_editor_property("material_function")
            if fn and fn.get_name() == leaf_name:
                return expr
        except Exception:
            pass
    return None


def _require(material, name):
    expr = _find(material, name)
    if not expr:
        raise RuntimeError(f"Required v9 expression missing: {name}")
    return expr


def _scalar(material, name, default, y):
    existing = _find_param(material, name)
    if existing:
        return existing
    return lib.scalar_param(
        material,
        name,
        GROUP,
        default,
        11200,
        y,
        desc="Native Water v10 input; preserves the v9 analytic fallback when unavailable.",
    )


def _vector(material, name, default, y):
    existing = _find_param(material, name)
    if existing:
        return existing
    return lib.vector_param(
        material,
        name,
        GROUP,
        default,
        11200,
        y,
        desc="Native Water v10 vector input; runtime-written when native state is valid.",
    )


def _wire(src, output, dst, pin):
    if not lib.connect(src, output, dst, pin):
        raise RuntimeError(f"Failed to connect {src.get_name()}:{output} -> {dst.get_name()}:{pin}")


def build() -> dict:
    material = unreal.EditorAssetLibrary.load_asset(MASTER)
    function = unreal.EditorAssetLibrary.load_asset(NATIVE_FUNCTION)
    if not material:
        raise RuntimeError(f"Could not load {MASTER}")
    if not function:
        raise RuntimeError(f"Could not load {NATIVE_FUNCTION}")

    existing_call = _find_function_call(material, "MF_WaterNativeInteraction_v10")
    if existing_call:
        return {"ok": True, "modified": False, "reason": "already_integrated", "master": MASTER}

    # The first editor attempt can leave only this disconnected probe node when
    # UE rejects a pin connection. Remove that known script-owned residue before
    # retrying; the duplicated v9 graph has no ComponentMask_0 node.
    stale_probe = _find(material, "MaterialExpressionComponentMask_0")
    if stale_probe:
        unreal.MaterialEditingLibrary.delete_material_expression(material, stale_probe)

    # These are the preserved v9 roots.  They are intentionally not replaced.
    wave = _require(material, "MaterialExpressionMaterialFunctionCall_3")
    ripple = _find_function_call(material, "MF_WaterRippleField_v9") or _require(
        material, "MaterialExpressionMaterialFunctionCall_0"
    )
    foam = _find_function_call(material, "MF_WaterProximityFoam_v9") or _require(
        material, "MaterialExpressionMaterialFunctionCall_1"
    )
    biolum = _find_function_call(material, "MF_WaterBioluminescence_v9") or _require(
        material, "MaterialExpressionMaterialFunctionCall_2"
    )
    v9_normal = _require(material, "MaterialExpressionCustom_1")
    v9_wpo = _require(material, "MaterialExpressionCustom_3")
    v9_normal_blend = _require(material, "MaterialExpressionCustom_4")
    v9_emissive = _require(material, "MaterialExpressionCustom_5")
    v9_foam_color = _require(material, "MaterialExpressionMultiply_11")

    # Runtime-written native state. Defaults deliberately select the analytic v9 path.
    native_available = _scalar(material, "NativeWaterAvailability", 0.0, -1200)
    native_height = _scalar(material, "NativeShallowWaterHeight", 0.0, -1000)
    native_velocity = _vector(material, "NativeShallowWaterVelocity", (0.0, 0.0, 0.0, 0.0), -800)
    native_normal = _vector(material, "NativeShallowWaterNormal", (0.0, 0.0, 1.0, 0.0), -600)
    water_body_index = _scalar(material, "WaterBodyIndex", 0.0, -400)
    water_zone_index = _scalar(material, "WaterZoneIndex", 0.0, -200)
    wpo_scale = _scalar(material, "WaterWPOScale", 0.0, 0)
    velocity_normal_strength = _scalar(material, "WaterVelocityNormalStrength", 0.1, 200)
    wave_foam_weight = _scalar(material, "WaterWaveFoamWeight", 0.35, 400)
    shore_foam_weight = _scalar(material, "WaterShorelineFoamWeight", 0.65, 600)
    ripple_foam_weight = _scalar(material, "WaterRippleFoamWeight", 0.45, 800)
    velocity_foam_weight = _scalar(material, "WaterVelocityFoamWeight", 0.1, 1000)
    velocity_bio_weight = _scalar(material, "WaterVelocityBioluminescenceWeight", 0.15, 1200)
    crest_bio_weight = _scalar(material, "WaterCrestBioluminescenceWeight", 0.15, 1400)
    bio_impulse = _scalar(material, "WaterBioluminescenceImpulse", 0.0, 1600)
    bio_weight = _scalar(material, "WaterBioluminescenceWeight", 1.0, 1800)
    bio_add_color = _vector(material, "WaterV10BioAddColor", (0.02, 0.75, 0.65, 1.0), 2000)

    # Extract the v9 wave height and v9 bioluminescence into scalar inputs without
    # disturbing any existing v9 connection.
    wave_height = lib.create_expression(material, unreal.MaterialExpressionComponentMask, 11600, 2400)
    wave_height.set_editor_property("r", False)
    wave_height.set_editor_property("g", False)
    wave_height.set_editor_property("b", True)
    wave_height.set_editor_property("a", False)
    # Displacement is the first output of the v9 wave function. ComponentMask's
    # Python pin is the unnamed/default input in UE 5.8.
    _wire(wave, "", wave_height, "")

    bio_luma = lib.create_expression(material, unreal.MaterialExpressionDotProduct, 11600, 2600)
    bio_luma_color = lib.create_expression(material, unreal.MaterialExpressionConstant3Vector, 11300, 2800)
    bio_luma_color.set_editor_property("constant", unreal.LinearColor(0.2126, 0.7152, 0.0722, 0.0))
    _wire(biolum, "Emissive", bio_luma, "A")
    _wire(bio_luma_color, "", bio_luma, "B")
    bio_input = lib.create_expression(material, unreal.MaterialExpressionAdd, 12000, 2600)
    _wire(bio_luma, "", bio_input, "A")
    _wire(bio_impulse, "", bio_input, "B")

    # Keep the profile weight live without changing the default V9 response
    # (WaterBioluminescenceWeight defaults to 1.0).
    bio_profile_input = lib.create_expression(material, unreal.MaterialExpressionMultiply, 12400, 2600)
    _wire(bio_input, "", bio_profile_input, "A")
    _wire(bio_weight, "", bio_profile_input, "B")

    # Body/zone IDs are routing metadata.  This neutral path keeps them in the
    # material contract without gating valid index 0 or altering V9 visuals.
    identity_sum = lib.create_expression(material, unreal.MaterialExpressionAdd, 11600, -250)
    identity_zero = lib.create_expression(material, unreal.MaterialExpressionConstant, 11600, -50)
    identity_zero.set_editor_property("r", 0.0)
    identity_noop = lib.create_expression(material, unreal.MaterialExpressionMultiply, 12000, -250)
    availability_with_identity = lib.create_expression(material, unreal.MaterialExpressionAdd, 12400, -250)
    _wire(water_body_index, "", identity_sum, "A")
    _wire(water_zone_index, "", identity_sum, "B")
    _wire(identity_sum, "", identity_noop, "A")
    _wire(identity_zero, "", identity_noop, "B")
    _wire(native_available, "", availability_with_identity, "A")
    _wire(identity_noop, "", availability_with_identity, "B")

    native_call = lib.create_expression(material, unreal.MaterialExpressionMaterialFunctionCall, 13200, 1100)
    native_call.set_editor_property("material_function", function)
    for source, pin in (
        (availability_with_identity, "NativeAvailability"),
        (native_height, "NativeHeight"),
        (native_velocity, "NativeVelocity"),
        (native_normal, "NativeNormal"),
        (wave_height, "FallbackHeight"),
        (wave, "FallbackNormal"),
        (wave, "WaveCrest"),
        (foam, "ShorelineFoam"),
        (ripple, "RippleMask"),
        (bio_profile_input, "Bioluminescence"),
        (wpo_scale, "WPOScale"),
        (velocity_normal_strength, "VelocityNormalStrength"),
        (wave_foam_weight, "WaveFoamWeight"),
        (shore_foam_weight, "ShorelineFoamWeight"),
        (ripple_foam_weight, "RippleFoamWeight"),
        (velocity_foam_weight, "VelocityFoamWeight"),
        (velocity_bio_weight, "VelocityBioluminescenceWeight"),
        (crest_bio_weight, "CrestBioluminescenceWeight"),
    ):
        if source is wave:
            output = "WaveNormal" if pin == "FallbackNormal" else "CrestCompression"
        else:
            output = "FoamMask" if source is foam else "RippleMask" if source is ripple else ""
        _wire(source, output, native_call, pin)

    # Keep the complete V9 normal/ripple stack pixel-side, then blend native
    # normal data at the final normal output. This prevents camera-dependent V9
    # detail from being promoted into the vertex shader by the WPO branch.
    _wire(v9_normal, "", v9_normal_blend, "BaseNormal")
    native_normal_blend = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, 13800, -250)
    _wire(v9_normal_blend, "", native_normal_blend, "A")
    _wire(native_call, "InteractionNormal", native_normal_blend, "B")
    _wire(native_available, "", native_normal_blend, "Alpha")
    bsdf = _require(material, "MaterialExpressionSubstrateSingleLayerWaterBSDF_0")
    _wire(native_normal_blend, "", bsdf, "Normal")

    # Native foam is additive to the v9 proximity/crest/ripple foam path.
    foam_add = lib.create_expression(material, unreal.MaterialExpressionAdd, 13200, 2200)
    foam_sat = lib.create_expression(material, unreal.MaterialExpressionSaturate, 13600, 2200)
    _wire(foam, "FoamMask", foam_add, "A")
    _wire(native_call, "FoamMask", foam_add, "B")
    lib.connect_unary(foam_add, foam_sat)
    _wire(foam_sat, "", v9_foam_color, "A")

    # v9 bioluminescence stays intact; v10 adds native-response emission.
    bio_add = lib.create_expression(material, unreal.MaterialExpressionMultiply, 13200, 2600)
    bio_total = lib.create_expression(material, unreal.MaterialExpressionAdd, 13600, 2600)
    _wire(native_call, "BioluminescenceMask", bio_add, "A")
    _wire(bio_add_color, "", bio_add, "B")
    _wire(biolum, "Emissive", bio_total, "A")
    _wire(bio_add, "", bio_total, "B")
    _wire(bio_total, "", v9_emissive, "BiolumEmission")

    # v10 WPO is additive and defaults to zero, so v9 is visually identical until
    # an instance or native runtime profile opts into the new contribution. Keep
    # this branch vertex-safe: the native multi-output function also consumes
    # pixel-only V9 foam/bio inputs, so its WPO output cannot be used directly.
    safe_wpo = lib.create_expression(material, unreal.MaterialExpressionCustom, 13200, 3400)
    safe_wpo.set_editor_property("description", "V10 Native WPO Vertex Safe")
    safe_wpo.set_editor_property(
        "code",
        "float blend = saturate(NativeAvailability); float3 fallbackN = float3(0.0, 0.0, 1.0); "
        "float3 nativeN = normalize(NativeNormal + float3(0.0, 0.0, 0.0001)); "
        "float3 n = normalize(lerp(fallbackN, nativeN, blend) + float3(NativeVelocity.xy * 0.01, 0.0)); "
        "float height = lerp(FallbackHeight, NativeHeight, blend); return n * height * WPOScale;",
    )
    safe_wpo.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    safe_inputs = []
    for input_name in ("NativeAvailability", "NativeHeight", "NativeVelocity", "NativeNormal", "FallbackHeight", "WPOScale"):
        custom_input = unreal.CustomInput()
        custom_input.set_editor_property("input_name", input_name)
        safe_inputs.append(custom_input)
    safe_wpo.set_editor_property("inputs", safe_inputs)
    for source, pin in (
        (native_available, "NativeAvailability"),
        (native_height, "NativeHeight"),
        (native_velocity, "NativeVelocity"),
        (native_normal, "NativeNormal"),
        (wave_height, "FallbackHeight"),
        (wpo_scale, "WPOScale"),
    ):
        _wire(source, "", safe_wpo, pin)
    wpo_add = lib.create_expression(material, unreal.MaterialExpressionAdd, 13200, 3000)
    _wire(v9_wpo, "", wpo_add, "A")
    _wire(safe_wpo, "", wpo_add, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        wpo_add, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET
    )

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    report = {
        "ok": True,
        "modified": True,
        "master": MASTER,
        "source_master": "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v9",
        "native_function": NATIVE_FUNCTION,
        "preserved_v9_paths": {
            "wave": wave.get_name(),
            "ripple": ripple.get_name(),
            "foam": foam.get_name(),
            "bioluminescence": biolum.get_name(),
            "normal": v9_normal.get_name(),
            "wpo": v9_wpo.get_name(),
        },
        "native_inputs": [
            "NativeWaterAvailability",
            "NativeShallowWaterHeight",
            "NativeShallowWaterVelocity",
            "NativeShallowWaterNormal",
            "WaterBodyIndex",
            "WaterZoneIndex",
            "WaterWPOScale",
            "WaterBioluminescenceImpulse",
        ],
        "default_behavior": "v9 analytic fallback; native/WPO contributions opt in through parameters",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    unreal.log("Water v10/v9 additive material integration: " + json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
