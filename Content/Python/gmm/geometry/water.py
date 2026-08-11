"""Dependency-free contract for project-wide water surface authoring."""
from __future__ import annotations

import json
import math
import re
from typing import Any, Mapping

FORMAT = "gmm_water_surface_request_v1"
SUPPORTED_MAJOR = 1
SUPPORTED_MINOR = 0
ROLES = {"lake", "pond", "river", "waterfall", "stream"}
MODES = {"water_body", "spline_sheet"}
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _asset_path(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(("/Game/", "/Engine/")) and "\\" not in value and "://" not in value


def validate_request(request: Mapping[str, Any], *, require_ue_results: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(request, Mapping):
        return {"ok": False, "errors": ["request root must be an object"], "warnings": []}

    if request.get("format") != FORMAT:
        errors.append(f"format must be {FORMAT!r}")
    major = request.get("schema_version", 1)
    minor = request.get("schema_minor", 0)
    if not isinstance(major, int) or isinstance(major, bool) or major < 1:
        errors.append("schema_version must be a positive integer")
    elif major > SUPPORTED_MAJOR:
        errors.append(f"unsupported schema major version: {major}")
    if isinstance(minor, int) and minor > SUPPORTED_MINOR:
        warnings.append(f"unknown schema minor version: {minor}")

    asset_id = request.get("asset_id")
    if not isinstance(asset_id, str) or not _ID.fullmatch(asset_id):
        errors.append("asset_id must be a non-empty identifier")
    role = request.get("water_role")
    if role not in ROLES:
        errors.append(f"water_role must be one of {sorted(ROLES)}")
    mode = request.get("authoring_mode")
    if mode not in MODES:
        errors.append(f"authoring_mode must be one of {sorted(MODES)}")
    if not _asset_path(request.get("material_instance")):
        errors.append("material_instance must be a project asset path")

    spline_id = request.get("spline_id")
    if mode == "spline_sheet":
        if not isinstance(spline_id, str) or not _ID.fullmatch(spline_id):
            errors.append("spline_id is required for spline_sheet authoring")
    elif spline_id is not None:
        warnings.append("spline_id is ignored for water_body authoring")

    dimensions = request.get("dimensions_cm")
    if not isinstance(dimensions, (list, tuple)) or len(dimensions) != 3 or not all(_finite(v) and v > 0 for v in dimensions):
        errors.append("dimensions_cm must contain three positive finite values")
    flow = request.get("flow_direction", [1.0, 0.0, 0.0])
    if not isinstance(flow, (list, tuple)) or len(flow) != 3 or not all(_finite(v) for v in flow):
        errors.append("flow_direction must contain three finite values")
    speed = request.get("flow_speed", 0.0)
    if not _finite(speed) or speed < 0:
        errors.append("flow_speed must be finite and non-negative")
    if not isinstance(request.get("seed", 0), int) or isinstance(request.get("seed", 0), bool):
        errors.append("seed must be an integer")
    for field in ("shoreline_profile", "vfx_profile"):
        if request.get(field) is not None and (not isinstance(request[field], str) or not _ID.fullmatch(request[field])):
            errors.append(f"{field} must be an identifier when provided")
    if request.get("shoreline_profile") is None:
        warnings.append("optional shoreline_profile is not specified")
    if request.get("vfx_profile") is None:
        warnings.append("optional vfx_profile is not specified")
    if require_ue_results and not isinstance(request.get("ue_validation"), Mapping):
        errors.append("ue_validation results are required for release")
    if not isinstance(request.get("provenance", {}), Mapping):
        errors.append("provenance must be an object")
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def serialize_request(request: Mapping[str, Any]) -> str:
    return json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def default_request() -> dict[str, Any]:
    return {
        "format": FORMAT, "schema_version": 1, "schema_minor": 0,
        "asset_id": "sakura_shrine_pond", "water_role": "pond",
        "material_instance": "/Game/EnvSandbox/Materials/Instances/Water/MI_GrandWater_SakuraPond",
        "authoring_mode": "water_body", "spline_id": None,
        "dimensions_cm": [1200.0, 900.0, 80.0], "flow_direction": [1.0, 0.0, 0.0],
        "flow_speed": 0.22, "shoreline_profile": "soft_stone", "vfx_profile": "pond_shimmer",
        "seed": 1337, "provenance": {},
    }
