"""Read-only live audit of Melusina's WaterHair KawaiiPhysics node."""
from __future__ import annotations

import json
import unreal

ABP = "/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair"
MESH = "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair"


def read(obj, name, default=None):
    try:
        value = obj.get_editor_property(name)
        try:
            bone_name = value.get_editor_property("bone_name")
            if bone_name:
                return str(bone_name)
        except Exception:
            pass
        if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
            return [float(value.x), float(value.y), float(value.z)]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
    except Exception:
        return default


def main():
    abp = unreal.load_asset(ABP)
    mesh = unreal.load_asset(MESH)
    cls = getattr(unreal, "AnimGraphNode_KawaiiPhysics", None)
    nodes = abp.get_nodes_of_class(cls) if abp and cls else []
    report = {
        "schema": "melodia.melusina_hair_physics_probe.v1",
        "ok": bool(abp and mesh and nodes),
        "asset": ABP,
        "mesh": MESH,
        "node_count": len(nodes),
        "nodes": [],
    }
    for graph_node in nodes:
        node = graph_node.get_editor_property("node")
        settings = node.get_editor_property("physics_settings")
        report["nodes"].append({
            "name": graph_node.get_name(),
            "root_bone": read(node, "root_bone"),
            "additional_root_bones": read(node, "additional_root_bones", []),
            "dummy_bone_length": read(node, "dummy_bone_length"),
            "need_warm_up": read(node, "need_warm_up"),
            "warm_up_frames": read(node, "warm_up_frames"),
            "bone_subdivision_count": read(node, "bone_subdivision_count"),
            "gravity": read(node, "gravity"),
            "enable_wind": read(node, "enable_wind"),
            "wind_scale": read(node, "wind_scale"),
            "physics_settings": {
                "damping": read(settings, "damping"),
                "stiffness": read(settings, "stiffness"),
                "world_damping_location": read(settings, "world_damping_location"),
                "world_damping_rotation": read(settings, "world_damping_rotation"),
                "radius": read(settings, "radius"),
                "limit_angle": read(settings, "limit_angle"),
            },
        })
    print("MELUSINA_HAIR_PROBE=" + json.dumps(report, sort_keys=True))
    return report


main()
