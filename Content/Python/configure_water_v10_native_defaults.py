"""Configure the project-wide native Water Body presentation contract.

This is intentionally project-owned and profile-driven. It does not edit UE's
Water plugin assets or any map package. The global profile leaves WaterBodyId
unset so each native body keeps its own runtime identity; promoted zones still
bind explicit body components through BP_MelodiaWaterSimulationZone.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROFILE_PATH = "/Game/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default"
SURFACE_MATERIAL = "/Game/EnvSandbox/Materials/Instances/Water/v10/MI_WaterV10_NativeDefault"
UNDERWATER_MATERIAL = "/Game/EnvSandbox/Materials/Masters/M_Water_Underwater_Post_v10"
AUDIT_PATH = Path(unreal.Paths.project_saved_dir()) / "Audit" / "water_v10_native_defaults.json"

ENGINE_COMPONENT_CLASSES = {
    "NativeShallowWaterComponentClass": (
        "/Water/FluidSimulation/Blueprints/Components/"
        "ShallowWaterSimComponent.ShallowWaterSimComponent_C"
    ),
    "NativeWaveFoamComponentClass": (
        "/Water/FluidSimulation/Blueprints/Components/"
        "WaveFoamSimComponent.WaveFoamSimComponent_C"
    ),
}


def _require(path: str):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        raise RuntimeError(f"Missing required asset: {path}")
    return asset


def main() -> dict:
    profile = _require(PROFILE_PATH)
    surface = _require(SURFACE_MATERIAL)
    underwater = _require(UNDERWATER_MATERIAL)

    # A project-wide profile cannot safely hard-code the validation map's
    # actor name. Runtime samples carry the real Water Body/Zone identity.
    profile.set_editor_property("WaterBodyId", unreal.Name(""))
    profile.set_editor_property("SurfaceMaterial", surface)
    profile.set_editor_property("UnderwaterMaterial", underwater)
    profile.set_editor_property("bUseNativeWater", True)
    profile.set_editor_property("bUseBakedSimulationForQueries", True)
    profile.set_editor_property("bRouteContactsToNativeWater", True)

    class_results = {}
    for property_name, class_path in ENGINE_COMPONENT_CLASSES.items():
        native_class = unreal.load_class(None, class_path)
        if not native_class:
            class_results[property_name] = {"path": class_path, "resolved": False}
            continue
        try:
            profile.set_editor_property(property_name, native_class)
            class_results[property_name] = {"path": class_path, "resolved": True}
        except Exception as exc:
            # These are advisory profile fields; the promoted zone owns the
            # actual component references. Never fail the shared material and
            # underwater contract because a plugin class is not assignable to
            # a soft UActorComponent property in a particular editor build.
            class_results[property_name] = {
                "path": class_path,
                "resolved": False,
                "reason": str(exc),
            }

    profile.set_editor_property(
        "Provenance",
        "Project-wide native UE Water Body defaults; V9 remains untouched; "
        "body identity is runtime-sourced; promoted zones own engine fluid components.",
    )
    unreal.EditorAssetLibrary.save_asset(PROFILE_PATH)

    result = {
        "ok": True,
        "profile": PROFILE_PATH,
        "surface_material": SURFACE_MATERIAL,
        "underwater_material": UNDERWATER_MATERIAL,
        "water_body_identity": "runtime Water Body actor name and Water Body/Zone indices",
        "native_component_classes": class_results,
        "promoted_zone_blueprint": "/Game/MelodiaIntegration/Water/Blueprints/BP_MelodiaWaterSimulationZone",
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("[WaterV10] configured project-wide native Water defaults")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
