"""Audit static meshes for missing or WorldGrid material assignments.

Run inside the Unreal Editor Python environment. The audit is intentionally
read-only apart from writing its JSON report.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOTS = ("/Game/Melodia", "/Game/EnvSandbox")
REPORT_PATH = Path("G:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/static_mesh_material_instance_audit.json")


def _asset_path(asset_data: unreal.AssetData) -> str:
    """Build an object path using fields exposed by UE 5.8 AssetData."""
    package = str(asset_data.get_editor_property("package_name"))
    name = str(asset_data.get_editor_property("asset_name"))
    return f"{package}.{name}"


def audit() -> dict:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    flagged = []
    scanned = 0

    for root in ROOTS:
        for asset_data in registry.get_assets_by_path(root, recursive=True):
            if asset_data.get_editor_property("asset_class_path").asset_name != "StaticMesh":
                continue

            scanned += 1
            asset_path = _asset_path(asset_data)
            mesh = unreal.load_asset(asset_path)
            if not mesh:
                flagged.append({"asset": asset_path, "reason": "load_failed"})
                continue

            bad_slots = []
            for index, slot in enumerate(mesh.get_editor_property("static_materials")):
                material = slot.get_editor_property("material_interface")
                material_path = material.get_path_name() if material else ""
                if not material:
                    bad_slots.append({"slot": index, "reason": "missing"})
                elif "WorldGrid" in material_path:
                    bad_slots.append(
                        {"slot": index, "reason": "WorldGrid", "material": material_path}
                    )

            if bad_slots:
                flagged.append({"asset": asset_path, "bad_slots": bad_slots})

    return {
        "ok": not flagged,
        "roots": list(ROOTS),
        "scanned": scanned,
        "flagged_count": len(flagged),
        "flagged": flagged,
    }


def main() -> int:
    report = audit()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(json.dumps({key: report[key] for key in ("ok", "scanned", "flagged_count")}))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    main()
