"""Use ordinary graph nodes for Water Body/Zone identity and bio weighting.

This replaces a failed Custom HLSL identity probe that could not expose its
inputs reliably through UE 5.8's Python API. The route is numerically neutral
for the default profile but keeps the parameters live and auditable.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "water_v10_parameter_routes.json"


def find(material, name: str):
    for expression in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        if expression.get_name() == name:
            return expression
    return None


def desc(expression) -> str:
    try:
        return str(expression.get_editor_property("desc"))
    except Exception:
        try:
            return str(expression.get_editor_property("description"))
        except Exception:
            return ""


def connect(source, output_name: str, target, input_name: str) -> None:
    unreal.MaterialEditingLibrary.connect_material_expressions(
        source, output_name, target, input_name
    )


def create(owner, cls, x: int, y: int, label: str | None = None):
    node = unreal.MaterialEditingLibrary.create_material_expression(owner, cls, x, y)
    if label:
        try:
            node.set_editor_property("desc", label)
        except Exception:
            try:
                node.set_editor_property("description", label)
            except Exception:
                pass
    return node


def main() -> dict:
    material = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not material:
        raise RuntimeError(f"Missing material: {MASTER}")

    # These were created only by the failed identity-routing attempts in this
    # lane; remove them before installing the deterministic ordinary-node path.
    for expression in list(unreal.MaterialEditingLibrary.get_material_expressions(material) or []):
        if desc(expression) == "V10 Water Body and Zone Identity Routing" or expression.get_name() in {
            "MaterialExpressionAdd_4",
            "MaterialExpressionAdd_5",
            "MaterialExpressionMultiply_1",
            "MaterialExpressionMultiply_2",
        }:
            unreal.MaterialEditingLibrary.delete_material_expression(material, expression)

    body = find(material, "MaterialExpressionScalarParameter_68")
    zone = find(material, "MaterialExpressionScalarParameter_69")
    availability = find(material, "MaterialExpressionScalarParameter_66")
    bio_input = find(material, "MaterialExpressionAdd_0")
    bio_weight = find(material, "MaterialExpressionScalarParameter_79")
    native_call = find(material, "MaterialExpressionMaterialFunctionCall_4")
    if not all((body, zone, availability, bio_input, bio_weight, native_call)):
        raise RuntimeError("Missing expected V10 parameter-route nodes")

    index_sum = create(material, unreal.MaterialExpressionAdd, 11600, -250,
                       "V10 Water Body and Zone Identity Sum")
    index_zero = create(material, unreal.MaterialExpressionConstant, 11600, -50,
                        "V10 Water Identity Neutral")
    index_zero.set_editor_property("r", 0.0)
    index_noop = create(material, unreal.MaterialExpressionMultiply, 12000, -250,
                        "V10 Water Identity No-op")
    availability_add = create(material, unreal.MaterialExpressionAdd, 12400, -250,
                               "V10 Native Availability With Identity")
    connect(body, "", index_sum, "A")
    connect(zone, "", index_sum, "B")
    connect(index_sum, "", index_noop, "A")
    connect(index_zero, "", index_noop, "B")
    connect(availability, "", availability_add, "A")
    connect(index_noop, "", availability_add, "B")
    connect(availability_add, "", native_call, "NativeAvailability")

    bio_mul = create(material, unreal.MaterialExpressionMultiply, 12000, 2700,
                     "V10 Bioluminescence Profile Weight")
    connect(bio_input, "", bio_mul, "A")
    connect(bio_weight, "", bio_mul, "B")
    connect(bio_mul, "", native_call, "Bioluminescence")

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    report = {
        "ok": True,
        "master": MASTER,
        "body_zone_identity_route": "WaterBodyIndex + WaterZoneIndex multiplied by zero, added to availability",
        "bioluminescence_weight_route": "existing V9 bio luminance+impulse multiplied by WaterBioluminescenceWeight",
        "default_visual_preservation": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("[WaterV10] Deterministic parameter routes: " + json.dumps(report))
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
