"""Build stylized Substrate Toon SDF material instances linked to M_Toon_SDF.

Creates 6 new portfolio-named instances with distinct aesthetic personalities:
CelestialVinyl, TealCeramic, RosyQuartz, MossyCopper, VoidStarlight, IvoryScrollwork.

Run in editor:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_stylized_sdf.py"

Part of the material unification plan — DO NOT TOUCH UniversalMasterToon.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "Saved" / "Audit"

MATERIALS_ROOT = "/Game/EnvSandbox/Materials"
SDF_INST_DIR = f"{MATERIALS_ROOT}/SDF/Instances"
PARENT = f"{MATERIALS_ROOT}/Masters/M_Toon_SDF.M_Toon_SDF"

STYLIZED = [
    {
        "name": "MI_SDF_CelestialVinyl",
        "tint": (0.82, 0.71, 0.35, 1.0),
        "accent": (0.12, 0.08, 0.22, 1.0),
        "band_scale": 0.045,
        "band_strength": 0.30,
        "style": "celestial gold + dark vinyl banding, iris-entrance glow",
        "tags": ["magical", "baroque", "henshin"],
    },
    {
        "name": "MI_SDF_TealCeramic",
        "tint": (0.25, 0.48, 0.52, 1.0),
        "accent": (0.85, 0.88, 0.92, 1.0),
        "band_scale": 0.06,
        "band_strength": 0.18,
        "style": "teal ceramic tile + white band relief, polished",
        "tags": ["architectural", "clean", "modern"],
    },
    {
        "name": "MI_SDF_RosyQuartz",
        "tint": (0.95, 0.72, 0.78, 1.0),
        "accent": (0.82, 0.48, 0.55, 1.0),
        "band_scale": 0.04,
        "band_strength": 0.15,
        "style": "rosy pink quartz + cherry blossom band shimmer",
        "tags": ["sakura", "warm", "translucent"],
    },
    {
        "name": "MI_SDF_MossyCopper",
        "tint": (0.42, 0.55, 0.38, 1.0),
        "accent": (0.72, 0.45, 0.22, 1.0),
        "band_scale": 0.055,
        "band_strength": 0.28,
        "style": "aged copper + moss-green patina organic feel",
        "tags": ["nature", "aged", "ornament"],
    },
    {
        "name": "MI_SDF_VoidStarlight",
        "tint": (0.06, 0.04, 0.12, 1.0),
        "accent": (0.18, 0.22, 0.95, 1.0),
        "band_scale": 0.08,
        "band_strength": 0.42,
        "style": "deep void black + starlight blue cosmic depth",
        "tags": ["celestial", "cosmic", "deep"],
    },
    {
        "name": "MI_SDF_IvoryScrollwork",
        "tint": (0.92, 0.88, 0.78, 1.0),
        "accent": (0.75, 0.62, 0.32, 1.0),
        "band_scale": 0.035,
        "band_strength": 0.25,
        "style": "aged ivory parchment + gold filigree manuscript feel",
        "tags": ["manuscript", "warm", "ornate"],
    },
]


def _ensure_directory(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _inst_path(name: str) -> str:
    return f"{SDF_INST_DIR}/{name}.{name}"


def _set_vector(instance: unreal.MaterialInstanceConstant, param: str, rgba: tuple) -> None:
    color = unreal.LinearColor(*rgba)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(instance, param, color)


def _set_scalar(instance: unreal.MaterialInstanceConstant, param: str, value: float) -> None:
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, param, value)


def build_stylized_instances() -> list[dict]:
    _ensure_directory(SDF_INST_DIR)

    parent = unreal.load_asset(PARENT)
    if not parent:
        raise RuntimeError(f"Missing parent material: {PARENT}")

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    results: list[dict] = []

    for spec in STYLIZED:
        name = spec["name"]
        full_path = _inst_path(name)
        entry = {"name": name, "path": full_path, "status": "unknown"}

        if unreal.EditorAssetLibrary.does_asset_exist(full_path):
            entry["status"] = "exists"
            unreal.log(f"[StylizedSDF] exists: {name}")
            results.append(entry)
            continue

        instance = asset_tools.create_asset(
            name, SDF_INST_DIR, unreal.MaterialInstanceConstant, factory
        )
        if not instance:
            entry["status"] = "create_failed"
            results.append(entry)
            continue

        unreal.MaterialEditingLibrary.set_material_instance_parent(instance, parent)
        _set_vector(instance, "BaseTint", spec["tint"])
        _set_vector(instance, "AccentTint", spec["accent"])
        _set_scalar(instance, "SDF_BandScale", spec["band_scale"])
        _set_scalar(instance, "SDF_BandStrength", spec["band_strength"])

        unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
        entry["status"] = "created"
        entry["style"] = spec["style"]
        entry["tags"] = spec["tags"]
        results.append(entry)
        unreal.log(f"[StylizedSDF] created {name} — {spec['style']}")

    return results


def build_all() -> int:
    unreal.log("=== Stylized SDF Toon instances ===")
    results = build_stylized_instances()

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "parent": PARENT,
        "instances": results,
        "created": len([r for r in results if r["status"] == "created"]),
        "existed": len([r for r in results if r["status"] == "exists"]),
        "failed": len([r for r in results if r["status"] not in ("created", "exists")]),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "stylized_sdf_build.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    created = report["created"]
    existed = report["existed"]
    failed = report["failed"]
    unreal.log(f"[StylizedSDF] complete: {created} new, {existed} existing, {failed} failed")
    unreal.log(f"[StylizedSDF] report -> {report_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(build_all())
