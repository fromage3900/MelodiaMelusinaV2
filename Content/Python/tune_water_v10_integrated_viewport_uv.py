"""Tune integrated water instances so their full V9/V10 structure reads on a cube."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = "/Game/EnvSandbox/Materials/Instances/Water/v10/Integrated"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "water_v10_integrated_viewport_uv.json"


PRESETS = {
    "CalmPond": {"BaseTiling": 0.80, "MidTiling": 1.37, "Layer2Tiling": 2.80, "HighlightTiling": 0.73, "RampBlend": 0.25, "MacroScale": 0.00035, "WaveAmplitude": 0.030, "WaterV10AntiTileStrength": 0.68, "WaterV10WorldTextureScale": 0.0012, "WaterV10WorldUVBlend": 1.0},
    "BiolumGrotto": {"BaseTiling": 0.95, "MidTiling": 1.61, "Layer2Tiling": 3.40, "HighlightTiling": 0.91, "RampBlend": 0.40, "MacroScale": 0.00050, "WaveAmplitude": 0.040, "WaterV10AntiTileStrength": 0.58, "WaterV10WorldTextureScale": 0.0016, "WaterV10WorldUVBlend": 1.0, "SparkleDensity": 0.12, "MagicalIntensity": 0.75},
    "CinematicHero": {"BaseTiling": 1.10, "MidTiling": 1.91, "Layer2Tiling": 4.70, "HighlightTiling": 1.07, "RampBlend": 0.50, "MacroScale": 0.00065, "WaveAmplitude": 0.060, "WaterV10AntiTileStrength": 0.46, "WaterV10WorldTextureScale": 0.0013, "WaterV10WorldUVBlend": 1.0, "SparkleDensity": 0.18, "MagicalIntensity": 1.0, "CausticIntensity": 0.45},
    "OceanPreview": {"BaseTiling": 0.70, "MidTiling": 1.20, "Layer2Tiling": 2.50, "HighlightTiling": 0.65, "RampBlend": 0.22, "MacroScale": 0.00030, "WaveAmplitude": 0.050, "WaterV10AntiTileStrength": 0.72, "WaterV10WorldTextureScale": 0.0009, "WaterV10WorldUVBlend": 1.0},
    "RiverClear": {"BaseTiling": 1.00, "MidTiling": 1.70, "Layer2Tiling": 3.60, "HighlightTiling": 0.87, "RampBlend": 0.35, "MacroScale": 0.00050, "WaveAmplitude": 0.050, "WaterV10AntiTileStrength": 0.62, "WaterV10WorldTextureScale": 0.0015, "WaterV10WorldUVBlend": 1.0, "SparkleDensity": 0.10},
}


def instance_path(name: str) -> str:
    return f"{ROOT}/MI_WaterV10_Integrated_{name}"


def main() -> dict:
    results = []
    for name, values in PRESETS.items():
        path = instance_path(name)
        instance = unreal.EditorAssetLibrary.load_asset(path)
        if not instance:
            raise RuntimeError(f"Missing integrated instance: {path}")
        for parameter, value in values.items():
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                instance, parameter, float(value)
            )
        unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
        results.append({"name": name, "asset": path, "parameters": values, "status": "saved"})

    report = {
        "ok": True,
        "directory": ROOT,
        "v9_rollback_touched": False,
        "purpose": "make analytic wave, macro-ramp, and layered UV structure legible in Material Render Studio cube previews",
        "instances": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[WaterV10] Tuned integrated viewport UVs for {len(results)} instances")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
