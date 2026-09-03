"""Editor-only smoke adapter for the recovered BP_InstanceOnSpline.

Run with Unreal's ExecutePythonScript. It creates/reuses only a named fixture
provider and test actor; the old reference Blueprint is never saved or edited.
"""
from __future__ import annotations

import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
REQUEST_PATH = PROJECT / "Content" / "Python" / "gmm" / "fixtures" / "instance_on_spline_request.json"
REPORT_PATH = PROJECT / "Saved" / "Audit" / "instance_on_spline_validation.json"
TARGET = "/Game/EnvSandbox/PCG/Universal/BP_InstanceOnSpline"
OLD_REFERENCE = "/Game/Melodia/Actor_BP/BP_InstanceOnSpline_Old"


def _bounds(actor, unreal):
    origin, extent = actor.get_actor_bounds(only_colliding_components=False, include_from_child_actors=True)
    return [round(abs(extent.x * 2.0), 3), round(abs(extent.y * 2.0), 3), round(abs(extent.z * 2.0), 3)]


def main() -> dict:
    import unreal
    from gmm.pcg.instance_on_spline import validate_request
    from build_pcg_spline_provider import spawn_spline_provider

    request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
    contract = validate_request(request)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    points = [(0.0, 0.0, 0.0), (600.0, 0.0, 0.0), (1200.0, 300.0, 0.0)]
    provider_spline = spawn_spline_provider(eas, "BP_InstanceOnSpline_TestSpline", points)
    asset = unreal.EditorAssetLibrary.load_asset(TARGET)
    result = {
        "ok": False, "asset_id": request.get("asset_id"), "target": TARGET,
        "old_reference": OLD_REFERENCE, "contract": contract,
        "provider_created": provider_spline is not None, "spline_points": points,
        "instance_count": 0, "bounds_cm": [0.0, 0.0, 0.0],
        "old_reference_untouched": True, "notes": [],
    }
    if not asset:
        result["notes"].append("Recovered Blueprint did not load")
    else:
        generated = unreal.EditorAssetLibrary.load_blueprint_class(TARGET)
        actor = eas.spawn_actor_from_class(generated, unreal.Vector(0.0, 600.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0)) if generated else None
        if actor:
            actor.set_actor_label("BP_InstanceOnSpline_TestActor")
            actor.call_editor_construction_script()
            mesh_components = actor.get_components_by_class(unreal.StaticMeshComponent)
            result["instance_count"] = len(mesh_components)
            result["bounds_cm"] = _bounds(actor, unreal)
            result["actor_spawned"] = True
            result["notes"].append("Construction script executed; inspect component count for authored dressing")
        else:
            result["notes"].append("Recovered Blueprint loaded but generated class could not spawn")
    result["ok"] = bool(contract["ok"] and asset and result.get("actor_spawned") and result["bounds_cm"] != [0.0, 0.0, 0.0])
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    unreal.log("BP_InstanceOnSpline validation: " + json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
