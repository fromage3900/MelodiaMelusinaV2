"""Separate the native WPO path from pixel-only V9 inputs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "water_v10_wpo_vertex_path.json"


def find(material, name: str):
    for expression in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        if expression.get_name() == name:
            return expression
    return None


def connect(source, output_name: str, target, input_name: str) -> None:
    unreal.MaterialEditingLibrary.connect_material_expressions(
        source, output_name, target, input_name
    )


def get_or_create(material):
    for expression in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        if getattr(expression, "description", "") == "V10 Native WPO Vertex Safe":
            return expression, False

    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionCustom, 13200, 3400
    )
    node.set_editor_property("description", "V10 Native WPO Vertex Safe")
    node.set_editor_property(
        "code",
        "float blend = saturate(NativeAvailability); "
        "float3 fallbackN = float3(0.0, 0.0, 1.0); "
        "float3 nativeN = normalize(NativeNormal + float3(0.0, 0.0, 0.0001)); "
        "float3 n = normalize(lerp(fallbackN, nativeN, blend) "
        "+ float3(NativeVelocity.xy * 0.01, 0.0)); "
        "float height = lerp(FallbackHeight, NativeHeight, blend); "
        "return n * height * WPOScale;",
    )
    node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    inputs = []
    for name in (
        "NativeAvailability",
        "NativeHeight",
        "NativeVelocity",
        "NativeNormal",
        "FallbackHeight",
        "WPOScale",
    ):
        custom_input = unreal.CustomInput()
        custom_input.set_editor_property("input_name", name)
        inputs.append(custom_input)
    node.set_editor_property("inputs", inputs)
    return node, True


def main() -> dict:
    material = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not material:
        raise RuntimeError(f"Missing material: {MASTER}")

    availability = find(material, "MaterialExpressionScalarParameter_66")
    height = find(material, "MaterialExpressionScalarParameter_67")
    velocity = find(material, "MaterialExpressionVectorParameter_17")
    normal = find(material, "MaterialExpressionVectorParameter_18")
    fallback_height = find(material, "MaterialExpressionComponentMask_0")
    wpo_scale = find(material, "MaterialExpressionScalarParameter_70")
    wpo_add = find(material, "MaterialExpressionAdd_3")
    native_call = find(material, "MaterialExpressionMaterialFunctionCall_4")
    if not all((availability, height, velocity, normal, fallback_height, wpo_scale, wpo_add, native_call)):
        raise RuntimeError("Missing expected native/WPO nodes")

    safe_wpo, created = get_or_create(material)
    for source, output_name, input_name in (
        (availability, "", "NativeAvailability"),
        (height, "", "NativeHeight"),
        (velocity, "", "NativeVelocity"),
        (normal, "", "NativeNormal"),
        (fallback_height, "", "FallbackHeight"),
        (wpo_scale, "", "WPOScale"),
    ):
        connect(source, output_name, safe_wpo, input_name)

    # Keep the native function's foam/bio/normal outputs pixel-side; only the
    # dedicated vertex-safe node may feed World Position Offset.
    connect(safe_wpo, "", wpo_add, "B")

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    report = {
        "ok": True,
        "master": MASTER,
        "created_vertex_safe_wpo": created,
        "native_function_wpo_disconnected_from_vertex_output": True,
        "v9_wpo_retained": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("[WaterV10] Vertex-safe WPO split: " + json.dumps(report))
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
