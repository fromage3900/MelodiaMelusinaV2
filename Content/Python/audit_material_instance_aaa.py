"""Catalog-wide AAA readiness audit for active EnvSandbox material instances.

This is an editor-side evidence pass. It does not modify assets. It reports
parameter-contract problems that are easy to miss in a large MI catalog while
leaving visual approval to the shared-light grid and level viewport.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPORT = Path(__file__).resolve().parents[2] / "Saved/Audit/material_instance_aaa_audit.json"
ROOT = "/Game/EnvSandbox/Materials/"
EXCLUDES = ("/_Archive/", "/_Scratch/", "/_Legacy/")


def run() -> dict:
    import unreal

    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_class(
        unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant"), True
    )
    rows: list[dict] = []
    parent_missing: list[str] = []
    empty_profiles: list[str] = []
    vector_outliers: list[dict] = []
    bad_layer_weights: list[dict] = []
    texture_without_albedo: list[str] = []

    for data in assets:
        path = str(data.package_name)
        if not path.startswith(ROOT) or any(x in path for x in EXCLUDES):
            continue
        instance = unreal.EditorAssetLibrary.load_asset(path)
        if not instance:
            continue
        parent = instance.get_editor_property("parent")
        if not parent:
            parent_missing.append(path)
        vectors = instance.get_editor_property("vector_parameter_values") or []
        textures = instance.get_editor_property("texture_parameter_values") or []
        scalars = instance.get_editor_property("scalar_parameter_values") or []
        if not vectors and not textures and not scalars:
            empty_profiles.append(path)

        for entry in vectors:
            info = entry.get_editor_property("parameter_info")
            name = str(info.get_editor_property("name"))
            value = entry.get_editor_property("parameter_value")
            rgb = [float(value.r), float(value.g), float(value.b)]
            if any(channel < 0.0 for channel in rgb):
                vector_outliers.append({"path": path, "parameter": name, "value": rgb})
            elif max(rgb) > 2.0 and any(
                token in name.lower() for token in ("tint", "color", "ramp", "palette")
            ):
                vector_outliers.append({"path": path, "parameter": name, "value": rgb})

        scalar_values = {
            str(entry.get_editor_property("parameter_info").get_editor_property("name")): float(
                entry.get_editor_property("parameter_value")
            )
            for entry in scalars
        }
        for name in ("TextureWeight", "LayerA_TextureWeight", "LayerB_TextureWeight"):
            value = scalar_values.get(name)
            if value is not None and value > 1.0:
                bad_layer_weights.append({"path": path, "parameter": name, "value": value})

        albedo_values = [
            str(entry.get_editor_property("parameter_value"))
            for entry in textures
            if "albedo" in str(
                entry.get_editor_property("parameter_info").get_editor_property("name")
            ).lower()
        ]
        if scalar_values.get("TextureWeight", 0.0) > 0.0 and albedo_values and not any(
            value not in ("None", "") for value in albedo_values
        ):
            texture_without_albedo.append(path)

        rows.append({
            "path": path,
            "parent": str(parent.get_path_name()) if parent else None,
            "has_authored_inputs": bool(vectors or textures or scalars),
        })

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "instance_count": len(rows),
        "parent_missing": parent_missing,
        "empty_profiles": empty_profiles,
        "vector_outliers": vector_outliers,
        "bad_layer_weights": bad_layer_weights,
        "texture_without_albedo": texture_without_albedo,
        "ready": not any((
            parent_missing,
            empty_profiles,
            vector_outliers,
            bad_layer_weights,
            texture_without_albedo,
        )),
        "instances": rows,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("AAA material audit: " + json.dumps({
        "instance_count": report["instance_count"],
        "ready": report["ready"],
        "vector_outliers": len(vector_outliers),
        "bad_layer_weights": len(bad_layer_weights),
    }))
    return report


if __name__ == "__main__":
    run()
