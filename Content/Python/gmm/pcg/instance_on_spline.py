"""Dependency-free contract for authored spline instance dressing.

Unreal owns the Blueprint and instance generation.  This module only validates
the request/audit boundary and deliberately imports no Unreal modules.
"""
from __future__ import annotations

import json
import math
import re
from typing import Any, Mapping

FORMAT = "gmm_spline_instance_request_v1"
SUPPORTED_MAJOR = 1
SUPPORTED_MINOR = 0
VALID_ROTATION_MODES = {"spline_frame", "world", "random_yaw"}
VALID_LIGHT_POLICIES = {"none", "per_instance", "baked"}
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _asset_path(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(("/Game/", "/Engine/")) and "\\" not in value and "://" not in value


def validate_request(request: Mapping[str, Any], *, require_ue_results: bool = False) -> dict[str, Any]:
    """Return ``errors`` and ``warnings`` for a spline-instance request."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(request, Mapping):
        return {"ok": False, "errors": ["request root must be an object"], "warnings": []}

    if request.get("format") != FORMAT:
        errors.append(f"format must be {FORMAT!r}")
    version = request.get("schema_version", 1)
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        errors.append("schema_version must be a positive integer")
    elif version > SUPPORTED_MAJOR:
        errors.append(f"unsupported schema major version: {version}")
    minor = request.get("schema_minor", 0)
    if isinstance(minor, int) and minor > SUPPORTED_MINOR:
        warnings.append(f"unknown schema minor version: {minor}")

    for field in ("asset_id", "style_id", "spline_id", "mesh_role"):
        value = request.get(field)
        if not isinstance(value, str) or not value or not _IDENTIFIER.fullmatch(value):
            errors.append(f"{field} must be a non-empty identifier")
    if not _asset_path(request.get("mesh_asset")):
        errors.append("mesh_asset must be a project asset path, not a machine-specific path")

    spacing = request.get("spacing_cm")
    if not _finite_number(spacing) or spacing <= 0:
        errors.append("spacing_cm must be finite and positive")

    scale = request.get("scale_range")
    if not isinstance(scale, (list, tuple)) or len(scale) != 2 or not all(_finite_number(x) for x in scale):
        errors.append("scale_range must contain two finite numbers")
    elif scale[0] <= 0 or scale[1] < scale[0]:
        errors.append("scale_range must satisfy 0 < min <= max")

    if request.get("rotation_mode") not in VALID_ROTATION_MODES:
        errors.append(f"rotation_mode must be one of {sorted(VALID_ROTATION_MODES)}")
    light_policy = request.get("light_policy")
    if light_policy not in VALID_LIGHT_POLICIES:
        errors.append(f"light_policy must be one of {sorted(VALID_LIGHT_POLICIES)}")
    elif light_policy != "none":
        warnings.append("optional light spawning requires Unreal-side validation")

    count = request.get("expected_instance_count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        errors.append("expected_instance_count must be a non-negative integer")
    bounds = request.get("expected_bounds_cm")
    if not isinstance(bounds, (list, tuple)) or len(bounds) != 3 or not all(_finite_number(x) and x >= 0 for x in bounds):
        errors.append("expected_bounds_cm must contain three non-negative finite numbers")
    if not isinstance(request.get("provenance"), Mapping):
        errors.append("provenance must be an object")
    if count == 0 or (isinstance(bounds, (list, tuple)) and all(x == 0 for x in bounds)):
        warnings.append("request contains provisional zero UE results")
    if require_ue_results and (count == 0 or not bounds or all(x == 0 for x in bounds)):
        errors.append("expected_instance_count and expected_bounds_cm must be populated by UE validation")
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def serialize_request(request: Mapping[str, Any]) -> str:
    """Serialize deterministically for review, hashing, and audit comparison."""
    return json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def default_request() -> dict[str, Any]:
    return {
        "format": FORMAT, "schema_version": 1, "schema_minor": 0,
        "asset_id": "example_spline_dressing", "style_id": "MELODIA_STAGE",
        "spline_id": "GardenSpline", "mesh_role": "ornament",
        "mesh_asset": "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m",
        "spacing_cm": 250.0, "seed": 1337, "scale_range": [0.8, 1.2],
        "rotation_mode": "spline_frame", "light_policy": "none",
        "expected_instance_count": 0, "expected_bounds_cm": [0, 0, 0], "provenance": {},
    }
