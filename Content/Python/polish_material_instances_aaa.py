"""Apply conservative, portfolio-safe ranges to active EnvSandbox MIs.

This pass is intentionally parameter-name driven. It does not touch masters,
textures, static switches, archived assets, scratch assets, or Melodia runtime
materials. The goal is consistent readability across the active portfolio
catalog while preserving authored values that already sit in a reasonable
range.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPORT = Path(__file__).resolve().parents[2] / "Saved/Audit/material_instance_aaa_polish.json"
ROOT = "/Game/EnvSandbox/Materials/"
EXCLUDES = ("/_Scratch/", "/_Archive/", "/_Legacy/", "/_ThirdParty/")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _range_for(name: str, path: str) -> tuple[float, float] | None:
    n = name.lower()
    p = path.lower()
    # Hair intentionally disables surface-water controls. Preserve those zeros.
    if "/melusina/" in p and "hair" in p:
        return None
    if "bias" in n or "offset" in n or "phase" in n:
        return None
    if "roughness" in n and "strength" not in n:
        return (0.0, 1.0)
    if "metallic" in n:
        return (0.0, 1.0)
    if "opacity" in n:
        return (0.0, 1.0)
    if "speed" in n:
        return (0.0, 4.0)
    if any(token in n for token in ("parallaxsteps", "samples", "iterations")):
        return (1.0, 64.0)
    if any(token in n for token in ("power", "sharpness", "contrast")):
        return (0.0, 32.0)
    if any(token in n for token in ("scale", "tiling", "texelsize")):
        return (0.001, 512.0)
    if any(token in n for token in (
        "intensity", "strength", "weight", "amount", "saturation", "glow",
        "sparkle", "iridescence", "impasto", "displacement", "wetness",
        "parallax", "rim", "smear", "pooling", "ink",
    )):
        return (0.0, 4.0)
    return None


def run(*, apply: bool = True) -> dict:
    import unreal

    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_class(
        unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant"), True
    )
    changes: list[dict] = []
    scanned = 0
    for data in assets:
        path = str(data.package_name)
        if not path.startswith(ROOT) or any(x in path for x in EXCLUDES):
            continue
        instance = unreal.EditorAssetLibrary.load_asset(path)
        if not instance:
            continue
        scanned += 1
        changed = False
        for entry in instance.get_editor_property("scalar_parameter_values") or []:
            info = entry.get_editor_property("parameter_info")
            name = str(info.get_editor_property("name"))
            old = float(entry.get_editor_property("parameter_value"))
            limits = _range_for(name, path)
            if limits is None:
                continue
            new = _clamp(old, *limits)
            if abs(new - old) < 1e-6:
                continue
            row = {"path": path, "parameter": name, "old": old, "new": new, "range": limits}
            changes.append(row)
            if apply:
                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                    instance, name, new
                )
                changed = True
        if apply and changed:
            unreal.EditorAssetLibrary.save_asset(path)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "apply": apply,
        "scanned": scanned,
        "changed": len(changes),
        "changes": changes,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("AAA MI polish: " + json.dumps({k: report[k] for k in ("scanned", "changed")}))
    return report


if __name__ == "__main__":
    run()
