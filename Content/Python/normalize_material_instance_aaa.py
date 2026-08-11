"""Normalize clearly invalid negative MI controls in active portfolio families.

This is intentionally conservative: it only changes negative scalar overrides
whose names describe non-negative controls. Positive authored intensities are
left untouched. Legacy, engine, marketplace, scratch, and archived assets are
excluded.
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REPORT = PROJECT / "Saved" / "Audit" / "material_instance_aaa_normalization.json"
ROOTS = ("/Game/EnvSandbox/Materials/", "/Game/Melodia/")
ACTIVE_EXCLUDES = ("/_Scratch/", "/_Archive/", "/_Legacy/", "/_ThirdParty/")
NON_NEGATIVE_TOKENS = (
    "roughness", "opacity", "weight", "strength", "intensity", "scale",
    "saturation", "contrast", "iridescence", "temporal", "impasto", "brush",
    "noise", "height", "depth", "speed", "amount", "wetness", "glow",
    "parallax", "sparkle", "rim", "metallic", "displacement", "fade",
)


def _eligible(path: str, name: str) -> bool:
    if not path.startswith(ROOTS) or any(x in path for x in ACTIVE_EXCLUDES):
        return False
    if path.startswith("/Game/Melodia/"):
        return False
    return any(token in name.lower() for token in NON_NEGATIVE_TOKENS)


def run(*, apply: bool = True) -> dict:
    import unreal

    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_class(
        unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant"), True
    )
    changes: list[dict] = []
    scanned = 0
    for asset_data in assets:
        path = str(asset_data.package_name)
        if not path.startswith(ROOTS) or any(x in path for x in ACTIVE_EXCLUDES):
            continue
        instance = unreal.EditorAssetLibrary.load_asset(path)
        if not instance:
            continue
        scanned += 1
        for value in instance.get_editor_property("scalar_parameter_values") or []:
            info = value.get_editor_property("parameter_info")
            name = str(info.get_editor_property("name"))
            old = float(value.get_editor_property("parameter_value"))
            if old >= 0.0 or not _eligible(path, name):
                continue
            if "scale" in name.lower() or "noise" in name.lower():
                new = abs(old) if abs(old) <= 16.0 else 1.0
            else:
                new = 0.0
            row = {"path": path, "parameter": name, "old": old, "new": new}
            if apply:
                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                    instance, name, new
                )
                unreal.EditorAssetLibrary.save_asset(path)
            changes.append(row)
    report = {"apply": apply, "scanned": scanned, "changed": len(changes), "changes": changes}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("AAA MI normalization: " + json.dumps({k: report[k] for k in ("apply", "scanned", "changed")}))
    return report


if __name__ == "__main__":
    run()
