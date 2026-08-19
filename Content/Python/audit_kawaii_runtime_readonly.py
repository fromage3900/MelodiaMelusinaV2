"""Read-only Kawaii Physics/placement audit for a clean Unreal editor session.

This script deliberately performs no asset mutation, compile, save, map load, or
PIE operation.  It avoids two invalid assumptions seen in the 2026-08-14 editor
log: ``AnimNode_KawaiiPhysics.static_class`` is not a Python API, and AnimGraph
nodes do not expose ``node_pos_x``.  The supported inspection path is the
editor-node class returned by ``get_nodes_of_class`` plus
``get_editor_property`` on the runtime node.

Run through the editor's Python console/Monolith once the owner gate is clean:

    exec(open(r"Content/Python/audit_kawaii_runtime_readonly.py", encoding="utf-8").read())

The only output is a JSON report to the editor log/console.
"""

from __future__ import annotations

import json
import unreal


HAIR_ABP = "/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair"
HAIR_MESH = "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair"
PROBE_BP = "/Game/MelodiaIntegration/Tests/BP_KawaiiPhysicsPlacementProbe"
PHYSICS_ASSETS = [
    "/Game/Melodia/Characters/Melusina/SK_Melusina_FIXED_Hair_PhysicsAsset",
    "/Game/Melodia/Characters/Melusina/SK_Melusina_PhysicsAsset",
]
LIMITS_ASSETS = [
    "/Game/Melodia/Characters/Melusina/Physics/DA_Melusina_HairCollisionLimits",
    "/Game/Melodia/Characters/Melusina/Physics/DA_Melusina_SkirtCollisionLimits",
]


def prop(obj, name, default=None):
    """Read one reflected property without assuming the property exists."""
    if obj is None:
        return default
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def path_name(obj):
    if obj is None:
        return None
    try:
        return str(obj.get_path_name())
    except Exception:
        return str(obj)


def name_value(value):
    if value is None:
        return None
    try:
        return str(value)
    except Exception:
        return repr(value)


def asset_result(asset_path):
    asset = unreal.load_asset(asset_path)
    return {
        "path": asset_path,
        "exists_and_loaded": asset is not None,
        "class": path_name(asset.get_class()) if asset is not None else None,
    }


def read_runtime_node(node):
    runtime = prop(node, "node")
    root_ref = prop(runtime, "root_bone")
    physics_settings = prop(runtime, "physics_settings")
    settings = {}
    for field in (
        "damping",
        "stiffness",
        "radius",
        "limit_angle",
        "world_damping_location",
        "world_damping_rotation",
    ):
        value = prop(physics_settings, field)
        if value is not None:
            settings[field] = name_value(value)

    reflected_asset_refs = {}
    for field in (
        "physics_asset",
        "physics_asset_override",
        "limits_data_asset",
        "limits_data",
        "bone_constraints",
        "collision_limits",
    ):
        value = prop(runtime, field)
        if value is not None:
            reflected_asset_refs[field] = path_name(value)

    return {
        "editor_node_class": path_name(node.get_class()),
        "runtime_node_class": path_name(runtime.get_class()) if runtime is not None else None,
        "root_bone": name_value(prop(root_ref, "bone_name")),
        "physics_settings": settings,
        "reflected_asset_refs": reflected_asset_refs,
        "node_position_inspected": False,
    }


def read_anim_blueprint():
    result = {"asset": asset_result(HAIR_ABP), "node_api": None, "nodes": []}
    abp = unreal.load_asset(HAIR_ABP)
    if abp is None:
        result["node_api"] = "asset_not_loaded"
        return result

    node_class = getattr(unreal, "AnimGraphNode_KawaiiPhysics", None)
    if node_class is None:
        result["node_api"] = "AnimGraphNode_KawaiiPhysics_not_exposed"
        return result

    result["node_api"] = "get_nodes_of_class"
    try:
        nodes = list(abp.get_nodes_of_class(node_class))
    except Exception as exc:
        result["node_api"] = f"get_nodes_of_class_error:{exc}"
        return result

    result["nodes"] = [read_runtime_node(node) for node in nodes]
    result["node_count"] = len(nodes)
    return result


def main():
    report = {
        "kind": "melodia_kawaii_runtime_readonly_audit",
        "mutation_issued": False,
        "compile_issued": False,
        "save_issued": False,
        "map_loaded": False,
        "pie_started": False,
        "hair_mesh": asset_result(HAIR_MESH),
        "anim_blueprint": read_anim_blueprint(),
        "placement_probe": asset_result(PROBE_BP),
        "physics_asset_candidates": [asset_result(path) for path in PHYSICS_ASSETS],
        "collision_limits_candidates": [asset_result(path) for path in LIMITS_ASSETS],
        "expected_root_bone": "hair_root",
        "inspection_boundary": [
            "No AnimNode_KawaiiPhysics.static_class call",
            "No node_pos_x/node_pos_y access",
            "No set_editor_property call",
        ],
    }
    text = json.dumps(report, sort_keys=True)
    unreal.log("MELODIA_KAWAII_READONLY_AUDIT: " + text)
    print(text)
    return report


main()
