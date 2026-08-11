"""Validation for the shared Blender/GMM project manifest contract."""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import cast

from .contracts import (
    APPLICATIONS,
    FORMAT,
    SUPPORTED_COORDINATE_SYSTEMS,
    SUPPORTED_UNITS,
    is_known_role,
    is_known_style,
)

Manifest = Mapping[str, object]


def _required(data: Manifest, key: str, errors: list[str]) -> object:
    value = data.get(key)
    if value is None or value == "":
        errors.append(f"missing required field: {key}")
    return value


def validate_manifest(manifest: Manifest) -> dict[str, object]:
    """Return a stable validation report without importing Blender or Unreal."""
    errors: list[str] = []
    warnings: list[str] = []

    if manifest.get("format") != FORMAT:
        errors.append(f"format must be {FORMAT}")

    _ = _required(manifest, "project_id", errors)
    _ = _required(manifest, "asset_id", errors)
    style_id = _required(manifest, "style_id", errors)
    roles = _required(manifest, "roles", errors)
    instances = _required(manifest, "instances", errors)

    source = manifest.get("source")
    if not isinstance(source, Mapping):
        errors.append("source must be an object")
    else:
        source_map = cast(Manifest, source)
        application = _required(source_map, "application", errors)
        if application not in APPLICATIONS:
            errors.append(f"unsupported source.application: {application}")
        _ = _required(source_map, "generator", errors)
        _ = _required(source_map, "generator_version", errors)

    if isinstance(style_id, str) and not is_known_style(style_id):
        errors.append(f"unknown style_id: {style_id}")

    if not isinstance(roles, list) or not roles:
        errors.append("roles must be a non-empty array")
    else:
        for role in cast(list[object], roles):
            if not isinstance(role, str) or not is_known_role(role):
                errors.append(f"unknown role: {role}")

    units = manifest.get("units")
    if units not in SUPPORTED_UNITS:
        errors.append(f"unsupported units: {units}")

    coordinates = manifest.get("coordinate_system")
    if coordinates not in SUPPORTED_COORDINATE_SYSTEMS:
        errors.append(f"unsupported coordinate_system: {coordinates}")

    if not isinstance(instances, list):
        errors.append("instances must be an array")
    else:
        for index, raw_instance in enumerate(cast(list[object], instances)):
            if not isinstance(raw_instance, Mapping):
                errors.append(f"instances[{index}] must be an object")
                continue
            instance = cast(Manifest, raw_instance)
            transform = instance.get("transform")
            if transform is not None and not _finite_matrix(transform):
                errors.append(f"instances[{index}].transform must be a finite 4x4 matrix")

    material_hints = manifest.get("material_hints")
    if material_hints is not None and not isinstance(material_hints, list):
        errors.append("material_hints must be an array")
    if "validation" not in manifest:
        warnings.append("manifest has no producer validation block")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _finite_matrix(value: object) -> bool:
    if not isinstance(value, list) or len(value) != 4:
        return False
    rows = cast(list[object], value)
    return all(
        isinstance(row, list)
        and len(row) == 4
        and all(isinstance(item, (int, float)) and math.isfinite(item) for item in cast(list[object], row))
        for row in rows
    )
