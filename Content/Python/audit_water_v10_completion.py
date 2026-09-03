"""Evidence audit for the V9-preserving Water v10 material upgrade.

Read-only against project assets.  The only write is the JSON report under
Saved/Audit.  This intentionally checks the whole V9 expression-name/class
inventory, not only a handful of known nodes, so an additive V10 graph cannot
silently drop a legacy branch.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


V9 = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v9"
V10 = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade"
V10_FUNCTION = "/Game/EnvSandbox/Materials/Functions/MF_WaterNativeInteraction_v10"
INSTANCE_NAMES = ("CalmPond", "BiolumGrotto", "CinematicHero", "OceanPreview", "RiverClear")
TEMPORAL = (
    "LayerPanSpeed",
    "TwinkleRate",
    "TemporalBlend",
    "MacroDriftSpeed",
    "FoamNoiseSpeed",
    "BioFlashRate",
    "RippleSpeed",
)
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "water_v10_completion.json"


def _path(asset) -> str:
    if not asset:
        return ""
    try:
        return asset.get_path_name().split(".", 1)[0]
    except Exception:
        return ""


def _load(path: str):
    asset = unreal.load_asset(path)
    if not asset:
        raise RuntimeError(f"Missing material asset: {path}")
    return asset


def _inventory(material):
    expressions = list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])
    nodes = {e.get_name(): e.get_class().get_name() for e in expressions if e}
    textures = {}
    scalars = set()
    functions = set()
    custom_code = []
    for expression in expressions:
        if not expression:
            continue
        class_name = expression.get_class().get_name()
        if class_name == "MaterialExpressionScalarParameter":
            try:
                scalars.add(str(expression.get_editor_property("parameter_name")))
            except Exception:
                pass
        if "Texture" in class_name and "Parameter" in class_name:
            try:
                name = str(expression.get_editor_property("parameter_name"))
                textures[name] = _path(expression.get_editor_property("texture"))
            except Exception:
                pass
        if class_name == "MaterialExpressionMaterialFunctionCall":
            try:
                functions.add(_path(expression.get_editor_property("material_function")))
            except Exception:
                pass
        if class_name == "MaterialExpressionCustom":
            try:
                custom_code.append(str(expression.get_editor_property("code") or ""))
            except Exception:
                pass
    return {
        "nodes": nodes,
        "textures": textures,
        "scalars": scalars,
        "functions": functions,
        "custom_code": custom_code,
    }


def _instance_parent(path: str) -> str:
    instance = unreal.load_asset(path)
    if not instance:
        return ""
    try:
        return _path(instance.get_editor_property("parent"))
    except Exception:
        return ""


def _instance_override_names(path: str) -> dict[str, set[str]]:
    instance = unreal.load_asset(path)
    if not instance:
        return {"scalar": set(), "vector": set(), "texture": set()}
    result = {"scalar": set(), "vector": set(), "texture": set()}
    for kind, property_name in (
        ("scalar", "scalar_parameter_values"),
        ("vector", "vector_parameter_values"),
        ("texture", "texture_parameter_values"),
    ):
        for value in instance.get_editor_property(property_name) or []:
            info = value.get_editor_property("parameter_info")
            result[kind].add(str(info.get_editor_property("name")))
    return result


def main() -> dict:
    v9 = _inventory(_load(V9))
    v10 = _inventory(_load(V10))

    missing_nodes = sorted(name for name in v9["nodes"] if name not in v10["nodes"])
    changed_nodes = sorted(
        name
        for name in v9["nodes"]
        if name in v10["nodes"] and v9["nodes"][name] != v10["nodes"][name]
    )
    texture_names_match = sorted(v9["textures"]) == sorted(v10["textures"])
    texture_paths_match = {
        name: {"v9": v9["textures"].get(name, ""), "v10": v10["textures"].get(name, "")}
        for name in sorted(set(v9["textures"]) | set(v10["textures"]))
    }
    texture_path_mismatches = sorted(
        name
        for name, values in texture_paths_match.items()
        if values["v9"] != values["v10"] or not values["v9"]
    )
    temporal = {
        name: {"v9": name in v9["scalars"], "v10": name in v10["scalars"]}
        for name in TEMPORAL
    }
    v9_functions_preserved = sorted(v9["functions"] - v10["functions"])
    world_uv_code = any(
        "WorldPosition.xy" in code and "WorldUVBlend" in code and "lerp" in code
        for code in v10["custom_code"]
    )
    v10_function_present = V10_FUNCTION in v10["functions"]

    integrated_names = INSTANCE_NAMES
    integrated_instances = {}
    instance_preservation = {}
    for name in integrated_names:
        path = f"/Game/EnvSandbox/Materials/Instances/Water/v10/Integrated/MI_WaterV10_Integrated_{name}"
        integrated_instances[path] = _instance_parent(path)
        v9_path = f"/Game/EnvSandbox/Materials/Instances/Water/v9/MI_WaterV9_{name}"
        v9_overrides = _instance_override_names(v9_path)
        v10_overrides = _instance_override_names(path)
        instance_preservation[name] = {
            "missing_v9_overrides": {
                kind: sorted(v9_overrides[kind] - v10_overrides[kind])
                for kind in v9_overrides
            },
            "v9_override_counts": {kind: len(values) for kind, values in v9_overrides.items()},
            "v10_override_counts": {kind: len(values) for kind, values in v10_overrides.items()},
        }

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "v9": V9,
        "v10": V10,
        "node_tree": {
            "v9_node_count": len(v9["nodes"]),
            "v10_node_count": len(v10["nodes"]),
            "missing_v9_nodes_in_v10": missing_nodes,
            "changed_v9_node_classes": changed_nodes,
            "v10_additive_node_count": len(v10["nodes"]) - len(v9["nodes"]),
        },
        "pbr_texture_maps": {
            "v9_count": len(v9["textures"]),
            "v10_count": len(v10["textures"]),
            "names_match": texture_names_match,
            "path_mismatches": texture_path_mismatches,
            "paths": texture_paths_match,
        },
        "temporal_controls": temporal,
        "functions": {
            "v9_function_count": len(v9["functions"]),
            "v9_functions_missing_from_v10": v9_functions_preserved,
            "native_v10_function_present": v10_function_present,
        },
        "world_uv_repair": {
            "custom_code_contains_world_uv_blend": world_uv_code,
            "rollback_parameter_expected": "WaterV10WorldUVBlend",
        },
        "integrated_instances": integrated_instances,
        "instance_preservation": instance_preservation,
    }
    report["ok"] = all(
        (
            not missing_nodes,
            not changed_nodes,
            texture_names_match,
            not texture_path_mismatches,
            all(row["v9"] and row["v10"] for row in temporal.values()),
            not v9_functions_preserved,
            v10_function_present,
            world_uv_code,
            all(parent == V10 for parent in integrated_instances.values()),
            all(
                not missing
                for row in instance_preservation.values()
                for missing in row["missing_v9_overrides"].values()
            ),
        )
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    unreal.log(f"[WaterV10CompletionAudit] {json.dumps(report)}")
    print(json.dumps(report, indent=2, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
