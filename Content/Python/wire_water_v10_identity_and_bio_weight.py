"""Close the remaining additive V10 parameter islands without changing V9 output."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "water_v10_identity_and_bio_weight.json"


def find(material, name: str):
    for expression in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        if expression.get_name() == name:
            return expression
    return None


def connect(source, output_name: str, target, input_name: str) -> None:
    unreal.MaterialEditingLibrary.connect_material_expressions(
        source, output_name, target, input_name
    )


def custom(material, description: str, code: str, inputs: tuple[str, ...], x: int, y: int):
    for expression in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        if getattr(expression, "description", "") == description:
            node = expression
            node.set_editor_property("code", code)
            node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
            custom_inputs = []
            for name in inputs:
                item = unreal.CustomInput()
                item.set_editor_property("input_name", name)
                custom_inputs.append(item)
            node.set_editor_property("inputs", custom_inputs)
            return node, False
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionCustom, x, y
    )
    node.set_editor_property("description", description)
    node.set_editor_property("code", code)
    node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    custom_inputs = []
    for name in inputs:
        item = unreal.CustomInput()
        item.set_editor_property("input_name", name)
        custom_inputs.append(item)
    node.set_editor_property("inputs", custom_inputs)
    return node, True


def main() -> dict:
    material = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not material:
        raise RuntimeError(f"Missing material: {MASTER}")

    body = find(material, "MaterialExpressionScalarParameter_68")
    zone = find(material, "MaterialExpressionScalarParameter_69")
    availability = find(material, "MaterialExpressionScalarParameter_66")
    bio_input = find(material, "MaterialExpressionAdd_0")
    bio_weight = find(material, "MaterialExpressionScalarParameter_79")
    native_call = find(material, "MaterialExpressionMaterialFunctionCall_4")
    if not all((body, zone, availability, bio_input, bio_weight, native_call)):
        raise RuntimeError("Missing expected V10 identity/bio nodes")

    identity, identity_created = custom(
        material,
        "V10 Water Body and Zone Identity Routing",
        "return (WaterBodyIndex + WaterZoneIndex) * 0.0;",
        ("WaterBodyIndex", "WaterZoneIndex"),
        11600,
        -250,
    )
    availability_add = find(material, "MaterialExpressionAdd_9")
    if not availability_add:
        availability_add = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionAdd, 12400, -250
        )
    connect(availability, "", availability_add, "A")
    connect(identity, "", availability_add, "B")
    connect(availability_add, "", native_call, "NativeAvailability")

    bio_mul, bio_created = None, False
    for expression in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        if getattr(expression, "desc", "") == "V10 Bioluminescence Profile Weight":
            bio_mul = expression
            break
    if not bio_mul:
        bio_mul = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionMultiply, 12400, 2700
        )
        bio_mul.set_editor_property("desc", "V10 Bioluminescence Profile Weight")
        bio_created = True
    connect(bio_input, "", bio_mul, "A")
    connect(bio_weight, "", bio_mul, "B")
    connect(bio_mul, "", native_call, "Bioluminescence")

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    report = {
        "ok": True,
        "master": MASTER,
        "identity_routing_created": identity_created,
        "bio_weight_node_created": bio_created,
        "v9_visual_preservation": "identity path is zero and default WaterBioluminescenceWeight is 1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("[WaterV10] Closed identity/bio parameter islands: " + json.dumps(report))
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
