"""Audit the reusable Gaea -> Nikki landscape material contract.

Read-only with respect to the level and viewport. The report is intentionally
plain JSON so a later import or repair pass can compare the exact same contract.
"""

import json
import os
from datetime import datetime, timezone

import unreal


MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape"
INSTANCE_PATH = "/Game/Gaea/Glacier/Materials/MI_Glacier_Landscape_Layered"
LEVEL_PATH = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
LANDSCAPE_ACTOR_OBJECT_PATH = (
    "/Game/__ExternalActors__/LV_SeaAbove_Prototype/8/44/"
    "TO7CUZC3W04JZOUSFXP8FT.Landscape_UAID_7C5758FA1CACB5FD02_1896451520"
)
REPORT_PATH = os.path.abspath(
    os.path.join(unreal.Paths.project_dir(), "Saved", "Audit", "gaea_landscape_pipeline_contract_2026-09-05.json")
)


def _asset_path(asset):
    if asset is None:
        return None
    try:
        path = str(unreal.EditorAssetLibrary.get_path_name_for_loaded_asset(asset))
        if path:
            return path
    except Exception:
        pass
    try:
        return str(asset.get_path_name()).split(".")[0]
    except Exception:
        return str(asset)


def _safe_value(fn, *args):
    try:
        return fn(*args)
    except Exception as exc:
        return {"error": str(exc)}


def _load_asset(path):
    """EditorAssetLibrary can miss a loaded asset while the editor is compiling."""
    return unreal.load_asset(path) or unreal.EditorAssetLibrary.load_asset(path)


def _json_value(value):
    if isinstance(value, unreal.LinearColor):
        return {"r": float(value.r), "g": float(value.g), "b": float(value.b), "a": float(value.a)}
    if isinstance(value, unreal.Vector):
        return {"x": float(value.x), "y": float(value.y), "z": float(value.z)}
    if isinstance(value, unreal.Vector4):
        return {"x": float(value.x), "y": float(value.y), "z": float(value.z), "w": float(value.w)}
    if isinstance(value, unreal.Object):
        return _asset_path(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    try:
        return str(value)
    except Exception:
        return repr(value)


def _expression_contract(material):
    expressions = list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])
    by_name = {e.get_name(): e for e in expressions}
    parameter_names = {}
    for expression in expressions:
        try:
            parameter = str(expression.get_editor_property("parameter_name"))
        except Exception:
            parameter = None
        if parameter:
            parameter_names.setdefault(parameter, []).append(expression.get_name())
    normalized = [
        {
            "name": e.get_name(),
            "position": list(unreal.MaterialEditingLibrary.get_material_expression_node_position(e)),
            "description": str(e.get_editor_property("desc")),
        }
        for e in expressions
        if "SINGLE UV AUTHORITY" in str(_safe_value(e.get_editor_property, "desc"))
        or "Gaea normalized UV clamp" in str(_safe_value(e.get_editor_property, "desc"))
    ]
    semantic = {}
    for parameter in (
        "Gaea_SnowMask",
        "Gaea_WaterMask",
        "Gaea_RockMask",
        "Gaea_FlowMask",
        "Gaea_SnowWeight",
        "Gaea_WaterWeight",
        "Gaea_RockWeight",
        "Gaea_FlowWeight",
        "GaeaLandscapeMin",
        "GaeaLandscapeSize",
        "bUseGaeaMasks",
        "bGaeaWholeLandscapeColor",
    ):
        semantic[parameter] = parameter_names.get(parameter, [])
    return {
        "expression_count": len(expressions),
        "normalized_uv_nodes": normalized,
        "semantic_parameter_nodes": semantic,
        "required_layer_samples": {
            layer: [
                e.get_name()
                for e in expressions
                if e.get_class().get_name() == "MaterialExpressionLandscapeLayerSample"
                and str(_safe_value(e.get_editor_property, "parameter_name")) == layer
            ]
            for layer in ("Snow", "Water", "Rock")
        },
        "required_clamps": {
            label: [
                e.get_name()
                for e in expressions
                if e.get_class().get_name() == "MaterialExpressionSaturate"
                and label in str(_safe_value(e.get_editor_property, "desc"))
            ]
            for label in ("Snow weight clamp", "Water weight clamp", "Rock weight clamp", "Flow weight clamp")
        },
        "by_name": by_name,
    }


def _instance_values(instance):
    scalar_names = [
        "Gaea_SnowWeight",
        "Gaea_WaterWeight",
        "Gaea_RockWeight",
        "Gaea_FlowWeight",
        "CymaticsLandscapeAmount",
        "CymaticsLandscapeMaxEmission",
        "Rock_TriplanarNormalStrength",
        "Rock_DetailAlbedoReference",
        "Rock_DetailAlbedoStrength",
        "TriplanarPro_Scale",
    ]
    texture_names = [
        "Gaea_SnowMask",
        "Gaea_WaterMask",
        "Gaea_RockMask",
        "Gaea_FlowMask",
        "Albedo",
        "Ground_Albedo",
        "Grass_Albedo",
        "Rock_Albedo",
        "Snow_Albedo",
        "Water_Albedo",
    ]
    vector_names = ["GaeaLandscapeMin", "GaeaLandscapeSize"]
    switch_names = ["bUseGaeaMasks", "bGaeaWholeLandscapeColor", "bTriplanarPro_Active", "bRockTriplanarNormals", "bSnowCoverageBreakup"]
    values = {
        "scalars": {
            name: _json_value(unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(instance, name))
            for name in scalar_names
        },
        "textures": {
            name: _asset_path(unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(instance, name))
            for name in texture_names
        },
        "vectors": {
            name: _json_value(unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(instance, name))
            for name in vector_names
        },
        "static_switches": {
            name: _json_value(unreal.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(instance, name))
            for name in switch_names
        },
    }
    values["scalar_range_violations"] = {
        name: value
        for name, value in values["scalars"].items()
        if name.startswith("Gaea_") and (not isinstance(value, (int, float)) or value < 0.0 or value > 1.0)
    }
    values["mode_contract"] = {
        "whole_map": values["static_switches"].get("bGaeaWholeLandscapeColor"),
        "triplanar_detail": values["static_switches"].get("bTriplanarPro_Active"),
        "valid": values["static_switches"].get("bGaeaWholeLandscapeColor") != values["static_switches"].get("bTriplanarPro_Active"),
    }
    return values


def _landscape_state():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(subsystem.get_all_level_actors() or []) if subsystem else []
    landscapes = []
    for actor in actors:
        if actor.get_class().get_name() != "Landscape":
            continue
        component = actor.get_landscape_info() if hasattr(actor, "get_landscape_info") else None
        material = None
        try:
            material = actor.get_editor_property("landscape_material")
        except Exception:
            pass
        location = actor.get_actor_location()
        landscapes.append(
            {
                "name": actor.get_name(),
                "label": actor.get_actor_label(),
                "material": _asset_path(material),
                "location": [float(location.x), float(location.y), float(location.z)],
                "bounds_origin": _json_value(actor.get_actor_location()),
                "has_landscape_info": component is not None,
            }
        )
    return {"level_loaded": str(unreal.EditorLevelLibrary.get_editor_world().get_path_name()) if unreal.EditorLevelLibrary.get_editor_world() else None, "landscapes": landscapes}


def _landscape_assignment():
    """Read the external Landscape actor without loading or moving its level."""
    actor = unreal.load_object(None, LANDSCAPE_ACTOR_OBJECT_PATH)
    if actor is None:
        return {"actor": LANDSCAPE_ACTOR_OBJECT_PATH, "material": None, "found": False}
    material = None
    try:
        material = actor.get_editor_property("landscape_material")
    except Exception:
        pass
    return {
        "actor": LANDSCAPE_ACTOR_OBJECT_PATH,
        "material": _asset_path(material),
        "found": True,
        "matches_instance": _asset_path(material) == INSTANCE_PATH,
    }


def run(write_report=True):
    master = _load_asset(MASTER_PATH)
    instance = _load_asset(INSTANCE_PATH)
    if master is None or instance is None:
        raise RuntimeError("Missing master or Glacier instance")
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "master_path": MASTER_PATH,
        "instance_path": INSTANCE_PATH,
        "expected_level_path": LEVEL_PATH,
        "master": _expression_contract(master),
        "instance": _instance_values(instance),
        "landscape": _landscape_state(),
        "landscape_assignment": _landscape_assignment(),
        "camera_touched": False,
        "connections_changed": False,
    }
    # The by_name map contains UObject references and is only useful in-memory;
    # remove it before writing JSON.
    report["master"].pop("by_name", None)
    report["status"] = (
        "PASS"
        if (
            not report["instance"]["scalar_range_violations"]
            and report["instance"]["mode_contract"]["valid"]
            and report["master"]["normalized_uv_nodes"]
            and report["landscape_assignment"].get("matches_instance")
        )
        else "ATTENTION"
    )
    if write_report:
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
    print(json.dumps(report, indent=2, sort_keys=True))
    return report


if __name__ == "__main__":
    run()
