"""Idempotently assert the canonical Melusina WaterHair KawaiiPhysics tune."""
from __future__ import annotations

import json
from pathlib import Path
import unreal

PROJECT = Path(unreal.Paths.project_dir())
CONTRACT_PATH = PROJECT / "specs" / "anim_presets" / "melusina_hair_physics.json"
REPORT_PATH = PROJECT / "Saved" / "Audit" / "melusina_hair_physics_apply_20260921.json"


def close(a, b, tolerance=1e-4):
    return abs(float(a) - float(b)) <= tolerance


def main():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8-sig"))
    expected = contract["settings"]
    abp = unreal.load_asset(contract["asset"])
    klass = getattr(unreal, "AnimGraphNode_KawaiiPhysics", None)
    nodes = abp.get_nodes_of_class(klass) if abp and klass else []
    if len(nodes) != 1 or nodes[0].get_name() != contract["node"]:
        raise RuntimeError(f"Expected one canonical Kawaii node, got {[n.get_name() for n in nodes]}")
    graph_node = nodes[0]
    node = graph_node.get_editor_property("node")
    root = str(node.get_editor_property("root_bone").get_editor_property("bone_name"))
    if root != contract["root_bone"]:
        raise RuntimeError(f"Refusing noncanonical root {root!r}")
    settings = node.get_editor_property("physics_settings")
    before = {
        "damping": float(settings.damping), "stiffness": float(settings.stiffness),
        "world_damping_location": float(settings.world_damping_location),
        "world_damping_rotation": float(settings.world_damping_rotation),
        "limit_angle": float(settings.limit_angle), "radius": float(settings.radius),
        "gravity": [float(node.gravity.x), float(node.gravity.y), float(node.gravity.z)],
        "enable_wind": bool(node.enable_wind), "wind_scale": float(node.wind_scale),
        "dummy_bone_length": float(node.dummy_bone_length),
        "bone_subdivision_count": int(node.bone_subdivision_count),
        "need_warm_up": bool(node.need_warm_up), "warm_up_frames": int(node.warm_up_frames),
    }
    changed = False
    for key, wanted in expected.items():
        got = before[key]
        changed |= got != wanted if not isinstance(wanted, float) else not close(got, wanted)
    if changed:
        settings.damping = expected["damping"]
        settings.stiffness = expected["stiffness"]
        settings.world_damping_location = expected["world_damping_location"]
        settings.world_damping_rotation = expected["world_damping_rotation"]
        settings.limit_angle = expected["limit_angle"]
        settings.radius = expected["radius"]
        node.set_editor_property("physics_settings", settings)
        node.set_editor_property("gravity", unreal.Vector(*expected["gravity"]))
        for key in ("enable_wind", "wind_scale", "dummy_bone_length", "bone_subdivision_count", "need_warm_up", "warm_up_frames"):
            node.set_editor_property(key, expected[key])
        graph_node.set_editor_property("node", node)
        unreal.BlueprintEditorLibrary.compile_blueprint(abp)
        if not unreal.EditorAssetLibrary.save_loaded_asset(abp, False):
            raise RuntimeError("Failed to save canonical WaterHair AnimBP")
    report = {"schema": "melodia.melusina_hair_physics_apply.v1", "ok": True, "changed": changed, "asset": contract["asset"], "before": before, "canonical": expected}
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("MELUSINA_HAIR_APPLY=" + json.dumps(report, sort_keys=True))
    return report


main()
