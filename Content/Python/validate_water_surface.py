"""UE editor adapter for a deterministic water request."""
from __future__ import annotations
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REQUEST = PROJECT / "Content/Python/gmm/fixtures/water_surface_request.json"
REPORT = PROJECT / "Saved/Audit/water_surface_validation.json"
SPLINE_LABEL = "WaterSurface_TestSpline"

def main() -> dict:
    import unreal
    from gmm.geometry.water import validate_request
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    contract = validate_request(request)
    result = {"ok": False, "asset_id": request.get("asset_id"),
              "authoring_mode": request.get("authoring_mode"),
              "material_instance": request.get("material_instance"),
              "contract": contract, "spline_fixture": None,
              "water_volume_check": "not_applicable", "notes": []}
    if not contract["ok"]:
        result["notes"].append("Request rejected before editor mutation")
    else:
        material_ok = unreal.EditorAssetLibrary.does_asset_exist(request["material_instance"])
        if not material_ok:
            result["notes"].append("Material instance does not resolve in the editor")
        if request.get("authoring_mode") == "spline_sheet":
            from build_pcg_spline_provider import spawn_spline_provider
            eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            points = [(0.0, 0.0, 0.0), (600.0, 0.0, 0.0), (1200.0, 300.0, 0.0)]
            spline = spawn_spline_provider(eas, SPLINE_LABEL, points)
            result["spline_fixture"] = {"label": SPLINE_LABEL, "points": points, "created": spline is not None}
            result["water_volume_check"] = "requires authored exclusion volume"
        result["ue_validation"] = {"adapter": "validate_water_surface.py",
                                    "material_resolves": material_ok,
                                    "status": "pass" if material_ok else "warning"}
    result["ok"] = bool(contract["ok"] and not result["notes"])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    unreal.log("Water surface validation: " + json.dumps(result, sort_keys=True))
    return result

if __name__ == "__main__":
    main()
