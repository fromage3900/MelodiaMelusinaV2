"""Guarded UE-editor text-injection bridge for the Water v10 family.

This module is intentionally narrow. It may validate project-owned assets,
write whitelisted profile fields, and set parameters on existing material
instances. It never mutates engine content, material graphs, parents, or
Blueprint topology.

Run inside the UE 5.8 editor through Monolith/editor_query.run_python, e.g.:

    exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Tools/water_v10_text_injector.py").read())
    print(water_v10_validate())

All mutating entry points require ``apply=True``. The default is dry-run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import unreal


PROJECT_ROOT = Path(unreal.Paths.project_dir())
MANIFEST_PATH = PROJECT_ROOT / "Saved" / "Portfolio" / "Materials" / "water_v10_manifest.json"
PROJECT_PREFIX = "/Game/"

PROFILE_PATH = "/Game/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default"

PROFILE_SCALARS = {
    "ToonLightBands": (1.0, 8.0),
    "ToonShadowSoftness": (0.0, 1.0),
    "ToonRimStrength": (0.0, 4.0),
    "ToonSpecularBand": (0.0, 1.0),
    "SurfaceRoughness": (0.0, 1.0),
    "SurfaceMetallic": (0.0, 1.0),
    "SurfaceSubsurfaceWeight": (0.0, 1.0),
    "WaterBioluminescenceWeight": (0.0, 4.0),
    "MaxContactsPerSecond": (1, 240),
    "MaxNativeDynamicForces": (0, 64),
    "MaxNativeImpulseForces": (0, 64),
    "ShallowWaterRenderTargetScale": (0.25, 2.0),
}

PROFILE_BOOLS = {
    "bUseNativeWater",
    "bUseBakedSimulationForQueries",
    "bRouteContactsToNativeWater",
    "bUseSubstrateToonLayer",
}

PROFILE_NAMES = {"WaterBodyId", "EffectProfileId", "AudioProfileId", "ToonProfileId", "SchemaVersion"}

PROFILE_COLORS = {"ToonShadowTint", "ToonHighlightTint"}

PROFILE_ASSET_REFS = {
    "ContactDataChannel",
    "ContactSystem",
    "RippleSystem",
    "SplashSystem",
    "FluidSystem",
    "SurfaceMaterial",
    "UnderwaterMaterial",
}

MATERIAL_SCALAR_PARAMETERS = {
    "ToonLightBands",
    "ToonShadowSoftness",
    "ToonRimStrength",
    "ToonSpecularBand",
    "SurfaceRoughness",
    "SurfaceMetallic",
    "SurfaceSubsurfaceWeight",
    "WaterBioluminescenceWeight",
    "WaterNoiseTiling",
    "WaterNoiseContrast",
    "WaterNoiseSpeed",
    "WaterWPOAmplitude",
    "WaterWPOClamp",
    "RetroQuantizationSteps",
    "RetroDitherStrength",
    "WaterShearThreshold",
    "WaterFlashDecay",
}

MATERIAL_VECTOR_PARAMETERS = {
    "ToonShadowTint",
    "ToonHighlightTint",
    "WaterBioluminescenceTint",
}


def _load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise RuntimeError(f"Missing Water v10 manifest: {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _asset_exists(path: str) -> bool:
    return bool(path) and unreal.EditorAssetLibrary.does_asset_exist(path)


def _assert_project_write_path(path: str) -> None:
    if not path.startswith(PROJECT_PREFIX) or "." in path:
        raise ValueError(f"Only project package paths without object suffixes are writable: {path}")


def _project_asset_paths(manifest: dict[str, Any]) -> list[str]:
    paths = [
        manifest.get("baseline"),
        manifest.get("niagara", {}).get("contact_data_channel"),
        manifest.get("niagara", {}).get("contact_system"),
        manifest.get("material_family", {}).get("native_interaction_function"),
        manifest.get("material_family", {}).get("substrate_master"),
        manifest.get("material_family", {}).get("underwater_post_process"),
    ]
    paths.extend(
        entry.get("asset")
        for entry in manifest.get("material_family", {}).get("instances", [])
    )
    return [path for path in paths if path]


def water_v10_validate() -> dict[str, Any]:
    """Read-only validation of manifest references and the profile asset."""

    manifest = _load_manifest()
    project_assets = _project_asset_paths(manifest)
    project_results = {path: _asset_exists(path) for path in project_assets}

    engine_refs = list(manifest.get("native_water", {}).get("engine_component_references", []))
    engine_results = {path: _asset_exists(path) for path in engine_refs}

    profile_exists = _asset_exists(PROFILE_PATH)
    return {
        "ok": profile_exists and all(project_results.values()),
        "manifest": str(MANIFEST_PATH),
        "profile": {"path": PROFILE_PATH, "exists": profile_exists},
        "project_assets": project_results,
        "engine_reference_assets": engine_results,
        "note": "Missing engine templates are reported but never written by this tool.",
    }


def _set_profile_property(profile: unreal.Object, name: str, value: Any) -> None:
    if name in PROFILE_SCALARS:
        low, high = PROFILE_SCALARS[name]
        if not isinstance(value, (int, float)) or not low <= value <= high:
            raise ValueError(f"{name}={value!r} is outside [{low}, {high}]")
    elif name in PROFILE_BOOLS:
        if not isinstance(value, bool):
            raise ValueError(f"{name} must be bool")
    elif name in PROFILE_NAMES:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} must be a non-empty string")
    elif name in PROFILE_COLORS:
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            raise ValueError(f"{name} must be RGBA with four values")
        value = unreal.LinearColor(*[float(channel) for channel in value])
    elif name in PROFILE_ASSET_REFS:
        if not isinstance(value, str) or not value.startswith("/"):
            raise ValueError(f"{name} must be an Unreal asset path")
        if value.startswith(PROJECT_PREFIX) and not _asset_exists(value):
            raise ValueError(f"{name} references a missing asset: {value}")
        loaded = unreal.EditorAssetLibrary.load_asset(value)
        if not loaded:
            raise ValueError(f"{name} could not be loaded: {value}")
        value = loaded
    else:
        raise ValueError(f"Profile property is not in the guarded allowlist: {name}")

    profile.set_editor_property(name, value)


def water_v10_set_profile(properties: dict[str, Any], *, apply: bool = False) -> dict[str, Any]:
    """Set whitelisted profile values; dry-run unless ``apply=True``."""

    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    if not profile:
        raise RuntimeError(f"Missing profile asset: {PROFILE_PATH}")

    for name in properties:
        if name in PROFILE_ASSET_REFS and isinstance(properties[name], str):
            _assert_project_write_path(PROFILE_PATH)
    for name, value in properties.items():
        _set_profile_property(profile, name, value)

    if not apply:
        return {"ok": True, "dry_run": True, "profile": PROFILE_PATH, "properties": properties}

    if not unreal.EditorAssetLibrary.save_asset(PROFILE_PATH, only_if_is_dirty=True):
        raise RuntimeError(f"UE editor refused to save profile: {PROFILE_PATH}")
    return {"ok": True, "dry_run": False, "profile": PROFILE_PATH, "properties": properties}


def water_v10_set_material_instance(
    material_path: str,
    scalar_parameters: dict[str, float] | None = None,
    vector_parameters: dict[str, list[float]] | None = None,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Set guarded parameters on an existing project-owned material instance."""

    _assert_project_write_path(material_path)
    material = unreal.EditorAssetLibrary.load_asset(material_path)
    if not material or not isinstance(material, unreal.MaterialInstanceConstant):
        raise ValueError(f"Expected an existing MaterialInstanceConstant: {material_path}")

    scalar_parameters = scalar_parameters or {}
    vector_parameters = vector_parameters or {}
    unknown_scalars = set(scalar_parameters) - MATERIAL_SCALAR_PARAMETERS
    unknown_vectors = set(vector_parameters) - MATERIAL_VECTOR_PARAMETERS
    if unknown_scalars or unknown_vectors:
        raise ValueError(f"Unknown material parameters: scalars={sorted(unknown_scalars)}, vectors={sorted(unknown_vectors)}")

    for name, value in scalar_parameters.items():
        if not isinstance(value, (int, float)):
            raise ValueError(f"Scalar {name} must be numeric")
        if name in {"WaterNoiseTiling", "WaterWPOClamp"} and value < 0.0:
            raise ValueError(f"Scalar {name} must be non-negative")
        if name == "RetroQuantizationSteps" and not 1.0 <= value <= 32.0:
            raise ValueError("RetroQuantizationSteps must be in [1, 32]")

    for name, value in vector_parameters.items():
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            raise ValueError(f"Vector {name} must be RGBA with four values")

    if apply:
        for name, value in scalar_parameters.items():
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(material, name, float(value))
        for name, value in vector_parameters.items():
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                material, name, unreal.LinearColor(*[float(channel) for channel in value])
            )
        unreal.MaterialEditingLibrary.update_material_instance(material)
        if not unreal.EditorAssetLibrary.save_asset(material_path, only_if_is_dirty=True):
            raise RuntimeError(f"UE editor refused to save material instance: {material_path}")

    return {
        "ok": True,
        "dry_run": not apply,
        "material": material_path,
        "scalars": scalar_parameters,
        "vectors": vector_parameters,
    }


def water_v10_report() -> str:
    """Return a stable JSON report for text-injection logs and CI handoff."""

    return json.dumps(water_v10_validate(), indent=2, sort_keys=True)
