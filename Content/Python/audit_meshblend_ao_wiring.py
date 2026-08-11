"""Verify that MeshBlend's activator drives an AO input on the universal master.

MeshBlend uses GBuffer ambient occlusion as a private contact-stencil channel.
This audit deliberately checks the graph connection rather than treating a
mere material-function reference as a working integration.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MESHBLEND_TOKEN = "MF_MeshBlend_Activator_Index_"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "meshblend_ao_wiring.json"


def _expression_inputs(material, owner):
    mel = unreal.MaterialEditingLibrary
    try:
        names = list(mel.get_material_expression_input_names(owner) or [])
        inputs = list(mel.get_inputs_for_material_expression(material, owner) or [])
    except Exception:
        return []
    return [(names[index] if index < len(names) else f"Input_{index}", value)
            for index, value in enumerate(inputs)]


def _input_source(value):
    try:
        return value.get_editor_property("expression")
    except Exception:
        return None


def _object_path(value):
    try:
        return value.get_path_name()
    except Exception:
        return ""


def main() -> None:
    material = unreal.load_asset(MASTER)
    if not material:
        raise RuntimeError(f"Missing master: {MASTER}")

    expressions = list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])
    calls = []
    for expression in expressions:
        if not isinstance(expression, unreal.MaterialExpressionMaterialFunctionCall):
            continue
        function = expression.get_editor_property("material_function")
        function_path = function.get_path_name() if function else ""
        if MESHBLEND_TOKEN not in function_path:
            continue
        calls.append(expression)

    connections = []
    for call in calls:
        for owner in expressions:
            for input_name, value in _expression_inputs(material, owner):
                if _object_path(_input_source(value)) == _object_path(call):
                    connections.append({
                        "function_call": call.get_name(),
                        "target_expression": owner.get_name(),
                        "target_type": type(owner).__name__,
                        "target_input": input_name,
                    })

    ao_connections = [
        row for row in connections
        if "ambientocclusion" in row["target_input"].replace(" ", "").lower()
        or row["target_input"].strip().lower() in {"ao", "occlusion"}
    ]
    root_ao = None
    root_ao_error = ""
    try:
        root_ao = unreal.MaterialEditingLibrary.get_material_property_input_node(
            material, unreal.MaterialProperty.MP_AMBIENT_OCCLUSION
        )
    except Exception as exc:
        root_ao_error = str(exc)
    root_ao_wired = _object_path(root_ao) in {_object_path(call) for call in calls}
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER,
        "meshblend_call_count": len(calls),
        "meshblend_functions": [
            call.get_editor_property("material_function").get_path_name() for call in calls
        ],
        "connections": connections,
        "ao_connections": ao_connections,
        "ao_wired": bool(ao_connections) or root_ao_wired,
        "root_ao_wired": root_ao_wired,
        "material_root_ao_source": _object_path(root_ao),
        "material_root_ao_error": root_ao_error,
        "substrate_input_inventory": [
            {
                "expression": expression.get_name(),
                "type": type(expression).__name__,
                "inputs": [name for name, _ in _expression_inputs(material, expression)],
            }
            for expression in expressions
            if "Substrate" in type(expression).__name__
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[MeshBlendAOAudit] wired={report['ao_wired']} -> {OUT}")
    if not report["ao_wired"]:
        raise RuntimeError("MeshBlend activator is not connected to an AO input")


if __name__ == "__main__":
    main()
