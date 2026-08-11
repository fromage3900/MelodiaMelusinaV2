"""Validate Ultra Dynamic Sky time-of-day sync and wire M_Master_Toon_Universal.

UDS already drives `/Game/UltraDynamicSky/Materials/Weather/UltraDynamicWeather_Parameters`
via `Update Active Variables` / `Update Material Effect Parameters` on the
Ultra_Dynamic_Sky (and Ultra_Dynamic_Weather) blueprint. No separate
MPC_Portfolio_TimeOfDay is created — that would be a stale duplicate.

Portfolio materials read UDS live through:
  - Material function `Day_to_Night_Color` (Sun Vector from UDS MPC)
  - Static switch `UseUDSTimeOfDay` + scalar `TimeOfDayMPCStrength` on the universal master

Run (editor open):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_time_of_day_mpc.py"
  py ".../setup_time_of_day_mpc.py" --rebuild-master

Also see: setup_portfolio_mpc.py (manual scene palette — MPC_Melodia_Palette)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "uds_time_of_day_sync.json"
INTEGRATION_REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "uds_toon_integration.json"

INSTANCE_ROOTS = (
    "/Game/EnvSandbox/Materials/Instances/Sakura",
    "/Game/EnvSandbox/Materials/Instances/Showcase",
    "/Game/EnvSandbox/Materials/Instances/Landscape",
)

LEVELS = (
    "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath",
    "/Game/EnvSandbox/_Template/L_Template",
)

UDS_ROOT = "/Game/UltraDynamicSky"
UDS_BP = f"{UDS_ROOT}/Blueprints/Ultra_Dynamic_Sky"
UDS_WEATHER_BP = f"{UDS_ROOT}/Blueprints/Ultra_Dynamic_Weather"
UDS_MPC = f"{UDS_ROOT}/Materials/Weather/UltraDynamicWeather_Parameters"
MF_DTN_FLOAT = f"{UDS_ROOT}/Materials/Material_Functions/Sky_Utilities/Day_to_Night_Float"
MF_DTN_COLOR = f"{UDS_ROOT}/Materials/Material_Functions/Sky_Utilities/Day_to_Night_Color"
MASTER = f"{lib.MASTER_DIR}/M_Master_Toon_Universal"

UDS_MPC_SCALARS = [
    "Time of Day",  # 0–2400, updated by UDS each tick
    "DLWE_Base Wetness",
    "DLWE_Snow Depth",
    "Wind Intensity",
    "Wind Force",
    "Wind Angle",
]

UDS_MPC_VECTORS = [
    "Sun Vector",  # drives Day_to_Night_* material functions
    "Moon Vector",
    "Ambient Fog Color",
    "Snow Color",
    "Dust Color",
]

UDS_BP_PROPERTIES = [
    "Time of Day",  # float 0–2400
    "Sun Angle",
    "Sun Inclination",
    "Animate Time of Day",
    "Day Length",
    "Night Length",
]

UDS_BP_FUNCTIONS = [
    "Update Active Variables",
    "Get Time of Day in Real Time Format",
    "Set Time of Day Using Time Code",
    "Bind to Sunrise",
    "Bind to Sunset",
]


def _asset_ok(path: str) -> bool:
    leaf = path.rsplit("/", 1)[-1]
    return unreal.EditorAssetLibrary.does_asset_exist(f"{path}.{leaf}")


def audit_uds() -> dict:
    mpc_path = f"{UDS_MPC}.UltraDynamicWeather_Parameters"
    return {
        "feasible": _asset_ok(UDS_MPC) and _asset_ok(MF_DTN_COLOR),
        "uds_mpc": mpc_path if _asset_ok(UDS_MPC) else None,
        "uds_blueprint": UDS_BP if _asset_ok(UDS_BP) else None,
        "uds_weather_blueprint": UDS_WEATHER_BP if _asset_ok(UDS_WEATHER_BP) else None,
        "material_functions": {
            "Day_to_Night_Float": MF_DTN_FLOAT if _asset_ok(MF_DTN_FLOAT) else None,
            "Day_to_Night_Color": MF_DTN_COLOR if _asset_ok(MF_DTN_COLOR) else None,
        },
        "mpc_scalars": UDS_MPC_SCALARS,
        "mpc_vectors": UDS_MPC_VECTORS,
        "uds_properties": UDS_BP_PROPERTIES,
        "uds_functions": UDS_BP_FUNCTIONS,
        "sync_mechanism": (
            "UDS actor runs Update Active Variables each frame (or on interval), "
            "writing Time of Day and Sun Vector into UltraDynamicWeather_Parameters. "
            "Materials sample that MPC directly or via Day_to_Night_Float/Color."
        ),
        "portfolio_mpc_decision": (
            "MPC_Portfolio_TimeOfDay NOT created — UDS MPC is the live source of truth. "
            "MPC_Melodia_Palette.TimeOfDayWarmth remains a manual scene-grade overlay."
        ),
    }


def rebuild_master_if_requested() -> str | None:
    if not any("rebuild" in str(a).lower() for a in sys.argv):
        return None
    import setup_master_universal as master

    sys.argv = [a for a in sys.argv if "rebuild" not in a.lower()] + ["--force"]
    return master.build()


def apply_uds_on_instances() -> dict:
    """Enable UseUDSTimeOfDay on universal child instances."""
    tuned: list[str] = []
    skipped: list[str] = []
    for root in INSTANCE_ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        paths = unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False) or []
        for asset_path in paths:
            leaf = asset_path.rsplit("/", 1)[-1]
            if not leaf.startswith("MI_"):
                continue
            full = f"{asset_path}.{leaf}" if "." not in asset_path else asset_path
            if not unreal.EditorAssetLibrary.does_asset_exist(full):
                continue
            mi = unreal.load_asset(full)
            if not mi:
                skipped.append(full)
                continue
            try:
                lib.set_instance_static_switch(mi, "UseUDSTimeOfDay", True)
                lib.set_instance_scalar(mi, "TimeOfDayMPCStrength", 1.0)
                lib.save_package(mi)
                tuned.append(full)
            except Exception:
                skipped.append(full)
    return {"tuned": tuned, "skipped": skipped, "count": len(tuned)}


def apply_uds_scenes() -> dict:
    import portfolio_scene_integration as scene

    results: dict = {}
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    for level in LEVELS:
        leaf = level.rsplit("/", 1)[-1]
        if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
            results[level] = {"missing": True}
            continue
        les.load_level(level)
        uds = scene.ensure_uds_actors(eas, time_of_day=1750.0, spawn_weather=True)
        hidden_sun = scene.disable_manual_sun_if_uds(eas)
        les.save_current_level()
        results[level] = {**uds, "manual_sun_hidden": hidden_sun}
    return results


def audit_level_uds() -> dict:
    import portfolio_scene_integration as scene

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_status: dict = {}
    for level in LEVELS:
        leaf = level.rsplit("/", 1)[-1]
        if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
            level_status[level] = {"missing": True}
            continue
        les.load_level(level)
        sky = scene._find_actor_by_tag(eas, scene.TAG_UDS_SKY)
        weather = scene._find_actor_by_tag(eas, scene.TAG_UDS_WEATHER)
        manual_suns = sum(
            1 for a in eas.get_all_level_actors() or [] if isinstance(a, unreal.DirectionalLight)
        )
        level_status[level] = {
            "uds_sky": sky.get_actor_label() if sky else None,
            "uds_weather": weather.get_actor_label() if weather else None,
            "directional_lights": manual_suns,
        }
    return level_status


def main() -> int:
    apply = "--apply" in sys.argv
    audit = audit_uds()
    master_path = None
    apply_result: dict = {}
    if audit["feasible"]:
        master_path = rebuild_master_if_requested()
        if not master_path and _asset_ok(MASTER):
            master_path = f"{MASTER}.M_Master_Toon_Universal"
        if apply:
            apply_result["instances"] = apply_uds_on_instances()
            apply_result["scenes"] = apply_uds_scenes()
    else:
        unreal.log_error(
            "[UDS ToD] UltraDynamicWeather_Parameters or Day_to_Night_Color missing. "
            "Install/sync Content/UltraDynamicSky before enabling UseUDSTimeOfDay."
        )

    level_uds = audit_level_uds() if audit["feasible"] else {}
    instances_tuned = apply_result.get("instances", {}).get("count", 0)
    scenes_ok = all(
        v.get("sky") for v in apply_result.get("scenes", {}).values() if not v.get("missing")
    ) if apply else any(v.get("uds_sky") for v in level_uds.values() if not v.get("missing"))

    integration = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **audit,
        "master_material": master_path,
        "apply_ran": apply,
        "apply_result": apply_result,
        "level_uds": level_uds,
        "instances_with_uds_switch": instances_tuned,
        "passed": audit["feasible"] and (scenes_ok or not apply),
    }
    INTEGRATION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    INTEGRATION_REPORT.write_text(json.dumps(integration, indent=2), encoding="utf-8")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **audit,
        "master_material": master_path,
        "material_switches": {
            "UseUDSTimeOfDay": "Static switch on M_Master_Toon_Universal (default off)",
            "TimeOfDayMPCStrength": "Scalar 0–1 blend toward UDS day/night tint",
            "TimeOfDayWarmth": "Manual fallback when UseUDSTimeOfDay is off",
        },
        "integration_report": str(INTEGRATION_REPORT),
        "level_setup": [
            "1. Drag Ultra_Dynamic_Sky into the level (Content/UltraDynamicSky/Blueprints).",
            "2. Optional: add Ultra_Dynamic_Weather for wetness/snow MPC scalars.",
            "3. Set Basic Controls → Time of Day (0–2400, e.g. 1200 = noon).",
            "4. Enable Animate Time of Day for runtime cycle, or drive Time of Day from Sequencer/Blueprint.",
            "5. On material instances using M_Master_Toon_Universal: enable UseUDSTimeOfDay.",
            "6. Tune TimeOfDayMPCStrength (default 1) for grade intensity.",
        ],
        "external_control": (
            "Get Actor of Class → Ultra_Dynamic_Sky, set Time of Day variable. "
            "Disable Animate Time of Day on UDS to avoid conflicts. "
            "Utility functions: Set Time of Day Using Time Code, Bind to Sunrise/Sunset."
        ),
        "rebuild_command": (
            'py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_time_of_day_mpc.py" --rebuild-master'
        ),
        "apply_command": (
            'py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_time_of_day_mpc.py" --apply'
        ),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(integration, indent=2))
    return 0 if integration.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
