"""Pure-Python parameter schemas for GMM geometry modifiers."""
from __future__ import annotations

from collections.abc import Mapping


BEVEL_DEFAULTS: dict[str, object] = {
    "width": 0.04,
    "segments": 3,
    "profile": 0.5,
    "angle_threshold": 35.0,
    "clamp_overlap": True,
    "allow_material_boundary": True,
}


def validate_bevel_parameters(parameters: Mapping[str, object]) -> list[str]:
    """Return validation errors; an empty list means the parameters are safe."""
    errors: list[str] = []
    width = parameters.get("width", BEVEL_DEFAULTS["width"])
    segments = parameters.get("segments", BEVEL_DEFAULTS["segments"])
    profile = parameters.get("profile", BEVEL_DEFAULTS["profile"])
    angle = parameters.get("angle_threshold", BEVEL_DEFAULTS["angle_threshold"])
    clamp_overlap = parameters.get("clamp_overlap", BEVEL_DEFAULTS["clamp_overlap"])

    if not isinstance(width, (int, float)) or width <= 0:
        errors.append("width must be greater than 0")
    if not isinstance(segments, int) or isinstance(segments, bool) or not 1 <= segments <= 32:
        errors.append("segments must be an integer from 1 to 32")
    if not isinstance(profile, (int, float)) or not 0.0 <= profile <= 1.0:
        errors.append("profile must be between 0 and 1")
    if not isinstance(angle, (int, float)) or not 0.0 <= angle <= 180.0:
        errors.append("angle_threshold must be between 0 and 180")
    if not isinstance(clamp_overlap, bool):
        errors.append("clamp_overlap must be a boolean")
    return errors


def validate_boolean_parameters(modifier_type: str, parameters: Mapping[str, object]) -> list[str]:
    """Return validation errors for boolean-difference/union/intersect modifiers."""
    errors: list[str] = []
    expected_operation = modifier_type.removeprefix("boolean_")
    operation = parameters.get("operation", expected_operation)
    if operation != expected_operation:
        errors.append(f"operation '{operation}' does not match modifier_type '{modifier_type}'")

    cutter_path = parameters.get("cutter_mesh_path", "")
    if not isinstance(cutter_path, str) or not cutter_path.strip():
        errors.append("cutter_mesh_path must be a non-empty Unreal asset path string")

    for vector_name in ("cutter_location", "cutter_scale"):
        vector = parameters.get(vector_name, {})
        if not isinstance(vector, Mapping):
            errors.append(f"{vector_name} must be a mapping with x/y/z keys")
            continue
        for axis in ("x", "y", "z"):
            value = vector.get(axis, 0.0)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"{vector_name}.{axis} must be a number")

    rotation = parameters.get("cutter_rotation", {})
    if not isinstance(rotation, Mapping):
        errors.append("cutter_rotation must be a mapping with pitch/yaw/roll keys")
    else:
        for axis in ("pitch", "yaw", "roll"):
            value = rotation.get(axis, 0.0)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"cutter_rotation.{axis} must be a number")

    for flag in ("show_preview", "preserve_cutter"):
        value = parameters.get(flag, False)
        if not isinstance(value, bool):
            errors.append(f"{flag} must be a boolean")
    return errors
