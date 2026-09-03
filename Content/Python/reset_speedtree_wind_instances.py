"""Reset extreme SpeedTree wind overrides on foliage material instances.

Run inside the UE editor Python environment. The script targets the actual
SpeedTreeImporter master used by the imported foliage cards and preserves
texture, tint, and unrelated material overrides.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = "/Game/EnvSandbox"
SPEEDTREE_PARENT = "/SpeedTreeImporter/SpeedTree9/SpeedTreeMaster"
MOTION_KEYS = (
    "branch",
    "oscill",
    "ripple",
    "wind",
    "gust",
    "turbulence",
    "flexibility",
    "independence",
    "stretch",
    "sway",
)
REPORT = Path("G:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/speedtree_wind_reset.json")


def _is_motion(name: str) -> bool:
    lowered = name.lower()
    return any(key in lowered for key in MOTION_KEYS)


def main() -> int:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    changed = []
    scanned = 0

    for data in registry.get_assets_by_path(ROOT, recursive=True):
        if data.get_editor_property("asset_class_path").asset_name != "MaterialInstanceConstant":
            continue

        asset_path = f"{data.get_editor_property('package_name')}.{data.get_editor_property('asset_name')}"
        instance = unreal.load_asset(asset_path)
        if not instance:
            continue

        try:
            parent = instance.get_editor_property("parent")
        except Exception:
            parent = None
        if not parent or SPEEDTREE_PARENT not in parent.get_path_name():
            continue

        scanned += 1
        removed = []

        # UE 5.8 keeps instance override arrays protected. Use the supported
        # material editing API so scalar, vector, and static-switch overrides
        # are disabled without disturbing textures or tint parameters.
        for getter in (
            unreal.MaterialEditingLibrary.get_scalar_parameter_names,
            unreal.MaterialEditingLibrary.get_vector_parameter_names,
            unreal.MaterialEditingLibrary.get_static_switch_parameter_names,
        ):
            for parameter_name in getter(instance):
                name = str(parameter_name)
                if _is_motion(name) and unreal.MaterialEditingLibrary.set_material_instance_parameter_override(
                    instance, parameter_name, False
                ):
                    removed.append(name)

        if removed:
            unreal.MaterialEditingLibrary.update_material_instance(instance)

        if removed:
            unreal.EditorAssetLibrary.save_asset(asset_path)
            changed.append({"asset": asset_path, "removed": removed})

    report = {
        "ok": True,
        "parent": SPEEDTREE_PARENT,
        "scanned": scanned,
        "changed_count": len(changed),
        "changed": changed,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(json.dumps({key: report[key] for key in ("ok", "scanned", "changed_count")}))
    return 0


if __name__ == "__main__":
    main()
