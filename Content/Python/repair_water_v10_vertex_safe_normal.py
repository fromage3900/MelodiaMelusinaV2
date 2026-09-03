"""Keep the V9 detailed normal in pixel presentation and make V10 WPO vertex-safe.

The V9 normal stack contains a camera-dependent detail branch that is valid for
the pixel shader. Feeding that branch into the new native WPO output promoted
it into the vertex shader in the duplicated V10 graph. This repair keeps V9's
normal/ripple stack intact, gives the native bridge a wave-normal fallback for
WPO, and blends native normal data at the final pixel-facing normal output.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "water_v10_vertex_safe_normal.json"


def _find(material, name: str):
    for expression in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        if expression.get_name() == name:
            return expression
    return None


def _connect(source, output_name: str, target, input_name: str) -> None:
    unreal.MaterialEditingLibrary.connect_material_expressions(
        source, output_name, target, input_name
    )


def _make_normal_blend(material):
    for expression in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        if getattr(expression, "description", "") == "V10 Native Normal Presentation Blend":
            return expression, False

    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionCustom, 420, -250
    )
    node.set_editor_property("description", "V10 Native Normal Presentation Blend")
    node.set_editor_property(
        "code",
        "float3 a = normalize(ExistingNormal + float3(0.0, 0.0, 0.0001)); "
        "float3 b = normalize(NativeNormal + float3(0.0, 0.0, 0.0001)); "
        "return normalize(lerp(a, b, saturate(NativeAvailability)));",
    )
    node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    inputs = []
    for name in ("ExistingNormal", "NativeNormal", "NativeAvailability"):
        custom_input = unreal.CustomInput()
        custom_input.set_editor_property("input_name", name)
        inputs.append(custom_input)
    node.set_editor_property("inputs", inputs)
    return node, True


def main() -> dict:
    material = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not material:
        raise RuntimeError(f"Missing material: {MASTER}")

    wave = _find(material, "MaterialExpressionMaterialFunctionCall_3")
    native_call = _find(material, "MaterialExpressionMaterialFunctionCall_4")
    v9_normal = _find(material, "MaterialExpressionCustom_1")
    v9_normal_blend = _find(material, "MaterialExpressionCustom_4")
    bsdf = _find(material, "MaterialExpressionSubstrateSingleLayerWaterBSDF_0")
    native_available = _find(material, "MaterialExpressionScalarParameter_66")
    if not all((wave, native_call, v9_normal, v9_normal_blend, bsdf, native_available)):
        missing = [
            label for label, value in (
                ("wave", wave), ("native_call", native_call),
                ("v9_normal", v9_normal), ("v9_normal_blend", v9_normal_blend),
                ("bsdf", bsdf), ("native_available", native_available),
            ) if not value
        ]
        raise RuntimeError(f"Missing expected V10/V9 graph nodes: {missing}")

    # V10 WPO must not pull V9's camera-dependent detail normal into the vertex
    # shader. The native branch still uses a real V9 wave normal as fallback.
    _connect(wave, "WaveNormal", native_call, "FallbackNormal")

    # Preserve the full V9 pixel normal/ripple behavior as the existing branch.
    _connect(v9_normal, "", v9_normal_blend, "BaseNormal")
    final_normal, created = _make_normal_blend(material)
    _connect(v9_normal_blend, "", final_normal, "ExistingNormal")
    _connect(native_call, "InteractionNormal", final_normal, "NativeNormal")
    _connect(native_available, "", final_normal, "NativeAvailability")
    _connect(final_normal, "", bsdf, "Normal")

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

    report = {
        "ok": True,
        "master": MASTER,
        "created_normal_blend": created,
        "v9_normal_preserved": True,
        "native_wpo_fallback": "MF_WaterWaveField_v7.WaveNormal",
        "camera_dependent_v9_normal_removed_from_native_wpo_input": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("[WaterV10] Vertex-safe native normal repair: " + json.dumps(report))
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
