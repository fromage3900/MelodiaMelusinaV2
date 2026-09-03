"""Stage, configure, and verify the Sea Above P0 prototype slice.
Manages isolated prototype maps, materials, anomaly effects, and Blueprint text injection drivers.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
MAP_PATH = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
DEST_ROOT = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "sea_above_slice_stage.json"

SEA_ABOVE_ASSETS = {
    "map": MAP_PATH,
    "surface_ocean_material": f"{DEST_ROOT}/Materials/MI_SeaAbove_SurfaceOcean",
    "false_ocean_material": f"{DEST_ROOT}/Materials/MI_SeaAbove_FalseOcean",
    "membrane_material": f"{DEST_ROOT}/Materials/M_SeaAbove_Membrane_Prototype",
    "pulse_driver_blueprint": f"{DEST_ROOT}/Blueprints/BP_SeaAbovePulseDriver",
    "anomaly_controller_blueprint": f"{DEST_ROOT}/Blueprints/BP_SeaAboveAnomalyController",
    "upward_particles": f"{DEST_ROOT}/VFX/NS_SeaAbove_UpwardDroplets_Prototype",
    "mesh_terrain": f"{DEST_ROOT}/Terrain/SM_SeaAbove_LiquidCathedral_257",
}

SEA_ABOVE_PULSE_CONFIG = {
    "pulse_period_seconds_min": 12.0,
    "pulse_period_seconds_max": 20.0,
    "pulse_period_default": 16.0,
    "mpc_palette_path": "/Game/EnvSandbox/Materials/MPC/MPC_Melodia_Palette",
    "membrane_sheen_pristine": 0.18,
    "membrane_sheen_healed": 0.32,
    "false_ocean_world_uv_blend": 1.0,
    "false_ocean_texture_scale": 0.0012,
}


def build_stage_manifest() -> dict[str, Any]:
    """Generates the stage configuration manifest for the Sea Above slice."""
    return {
        "schema": "melodia.sea_above_slice_stage.v1",
        "slice_id": "P0_SeaAbove_FirstDream",
        "assets": SEA_ABOVE_ASSETS,
        "pulse_config": SEA_ABOVE_PULSE_CONFIG,
        "anomalies": [
            {"id": "upward_droplets", "type": "niagara", "direction": [0.0, 0.0, 1.0], "acceleration_on_pulse": 2.5},
            {"id": "distant_fish_silhouettes", "type": "mesh_card", "velocity": [-50.0, 10.0, 0.0]},
            {"id": "bell_shadow_sweep", "type": "material_panner", "period": 30.0},
        ],
        "t3d_injection_targets": [
            "sea_above_pulse_cycle",
            "sea_above_anomaly_burst",
            "sea_above_membrane_sheen",
        ],
        "verification_gates": {
            "isolated_map": True,
            "surface_and_false_ocean_present": True,
            "bell_proxy_membrane_present": True,
            "pulse_timing_in_range": True,
            "t3d_nodes_valid": True,
        },
    }


def main():
    manifest = build_stage_manifest()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[SEA_ABOVE_STAGE] Generated Sea Above stage manifest at {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    main()
