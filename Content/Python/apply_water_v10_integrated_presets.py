"""Apply additive V10 controls to the V9-derived integrated water family.

This is intentionally editor-side and deterministic. It does not touch the V9
master or V9 instances; it only updates the project-owned V10 integrated
instances and writes a small audit report for the material lane.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = "/Game/EnvSandbox/Materials"
MASTER = f"{ROOT}/Masters/M_Water_Master_Grand_v10_Upgrade"
INTEGRATED_DIR = f"{ROOT}/Instances/Water/v10/Integrated"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "water_v10_integrated_presets.json"


# V9 profile identity is retained; these are deliberately modest additive
# controls so the family remains legible in the material viewport while native
# Water can override the availability/height/velocity inputs at runtime.
PRESETS: dict[str, dict[str, float]] = {
    "CalmPond": {
        "NativeWaterAvailability": 0.0,
        "WaterBodyIndex": 0.0,
        "WaterZoneIndex": 0.0,
        "WaterWPOScale": 0.08,
        "WaterVelocityNormalStrength": 0.10,
        "WaterWaveFoamWeight": 0.35,
        "WaterShorelineFoamWeight": 0.65,
        "WaterRippleFoamWeight": 0.45,
        "WaterVelocityFoamWeight": 0.10,
        "WaterVelocityBioluminescenceWeight": 0.15,
        "WaterCrestBioluminescenceWeight": 0.15,
        "WaterBioluminescenceImpulse": 0.0,
        "WaterBioluminescenceWeight": 0.25,
    },
    "BiolumGrotto": {
        "NativeWaterAvailability": 0.0,
        "WaterBodyIndex": 0.0,
        "WaterZoneIndex": 0.0,
        "WaterWPOScale": 0.14,
        "WaterVelocityNormalStrength": 0.22,
        "WaterWaveFoamWeight": 0.70,
        "WaterShorelineFoamWeight": 0.45,
        "WaterRippleFoamWeight": 0.95,
        "WaterVelocityFoamWeight": 0.40,
        "WaterVelocityBioluminescenceWeight": 1.20,
        "WaterCrestBioluminescenceWeight": 0.90,
        "WaterBioluminescenceImpulse": 0.15,
        "WaterBioluminescenceWeight": 0.90,
    },
    "CinematicHero": {
        "NativeWaterAvailability": 0.0,
        "WaterBodyIndex": 0.0,
        "WaterZoneIndex": 0.0,
        "WaterWPOScale": 0.18,
        "WaterVelocityNormalStrength": 0.32,
        "WaterWaveFoamWeight": 1.00,
        "WaterShorelineFoamWeight": 0.75,
        "WaterRippleFoamWeight": 1.00,
        "WaterVelocityFoamWeight": 0.65,
        "WaterVelocityBioluminescenceWeight": 1.50,
        "WaterCrestBioluminescenceWeight": 1.20,
        "WaterBioluminescenceImpulse": 0.25,
        "WaterBioluminescenceWeight": 1.00,
    },
    "OceanPreview": {
        "NativeWaterAvailability": 0.0,
        "WaterBodyIndex": 0.0,
        "WaterZoneIndex": 0.0,
        "WaterWPOScale": 0.12,
        "WaterVelocityNormalStrength": 0.18,
        "WaterWaveFoamWeight": 0.80,
        "WaterShorelineFoamWeight": 0.55,
        "WaterRippleFoamWeight": 0.70,
        "WaterVelocityFoamWeight": 0.35,
        "WaterVelocityBioluminescenceWeight": 0.40,
        "WaterCrestBioluminescenceWeight": 0.35,
        "WaterBioluminescenceImpulse": 0.05,
        "WaterBioluminescenceWeight": 0.35,
    },
    "RiverClear": {
        "NativeWaterAvailability": 0.0,
        "WaterBodyIndex": 0.0,
        "WaterZoneIndex": 0.0,
        "WaterWPOScale": 0.16,
        "WaterVelocityNormalStrength": 0.36,
        "WaterWaveFoamWeight": 0.75,
        "WaterShorelineFoamWeight": 0.60,
        "WaterRippleFoamWeight": 0.80,
        "WaterVelocityFoamWeight": 0.85,
        "WaterVelocityBioluminescenceWeight": 0.55,
        "WaterCrestBioluminescenceWeight": 0.45,
        "WaterBioluminescenceImpulse": 0.05,
        "WaterBioluminescenceWeight": 0.30,
    },
}


def asset_path(name: str) -> str:
    return f"{INTEGRATED_DIR}/MI_WaterV10_Integrated_{name}"


def main() -> dict:
    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        raise RuntimeError(f"Missing integrated V10 master: {MASTER}")

    master = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not master:
        raise RuntimeError(f"Could not load integrated V10 master: {MASTER}")

    results = []
    for name, values in PRESETS.items():
        path = asset_path(name)
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            raise RuntimeError(f"Missing integrated V10 instance: {path}")
        instance = unreal.EditorAssetLibrary.load_asset(path)
        if not instance:
            raise RuntimeError(f"Could not load integrated V10 instance: {path}")

        parent = instance.get_editor_property("parent")
        parent_path = parent.get_path_name().split(".", 1)[0] if parent else ""
        if parent_path != MASTER:
            raise RuntimeError(f"Wrong parent for {path}: {parent_path}")

        for parameter, value in values.items():
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                instance, parameter, float(value)
            )
        unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
        results.append({
            "name": name,
            "asset": path,
            "parent": parent_path,
            "applied_parameters": values,
            "status": "saved",
        })

    unreal.MaterialEditingLibrary.recompile_material(master)
    unreal.EditorAssetLibrary.save_loaded_asset(master, only_if_is_dirty=False)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER,
        "source_v9_master": f"{ROOT}/Masters/M_Water_Master_Grand_v9",
        "integrated_directory": INTEGRATED_DIR,
        "v9_rollback_untouched": True,
        "native_availability_default": 0.0,
        "instances": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[WaterV10] Applied and saved {len(results)} additive integrated instances")
    return report


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
