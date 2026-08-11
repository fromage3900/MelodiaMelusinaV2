"""Array tool specs — pure-Python contracts for UE-side array generation.

Each spec describes the transform computation for one array type.
UE adapters consume these to generate PCG graphs, HISM instances,
or direct actor spawns. Safe to import outside Unreal.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ArrayTransform:
    """One computed instance transform in the array."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rot_x: float = 0.0
    rot_y: float = 0.0
    rot_z: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0

    def to_dict(self) -> dict[str, float]:
        return {
            "x": self.x, "y": self.y, "z": self.z,
            "rot_x": self.rot_x, "rot_y": self.rot_y, "rot_z": self.rot_z,
            "scale_x": self.scale_x, "scale_y": self.scale_y, "scale_z": self.scale_z,
        }


def _validate_int(name: str, value: Any, min_v: int, max_v: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, int):
        errors.append(f"{name} must be int, got {type(value).__name__}")
    elif value < min_v or value > max_v:
        errors.append(f"{name} ({value}) out of range [{min_v}, {max_v}]")
    return errors


def _validate_float(name: str, value: Any, min_v: float, max_v: float) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, (int, float)):
        errors.append(f"{name} must be numeric, got {type(value).__name__}")
    elif value < min_v or value > max_v:
        errors.append(f"{name} ({value}) out of range [{min_v}, {max_v}]")
    return errors


def compute_spiral_array(
    count: int = 32,
    turns: float = 3.0,
    radius: float = 2.0,
    radius_growth: float = 0.0,
    height: float = 4.0,
    scale_per_item: float = 1.0,
    roll_per_item: float = 0.0,
) -> tuple[list[ArrayTransform], list[str]]:
    """Compute instance transforms for a helical spiral array.

    Returns (transforms, warnings).
    """
    errors: list[str] = []
    errors.extend(_validate_int("count", count, 2, 512))
    errors.extend(_validate_float("turns", turns, 0.1, 100.0))
    errors.extend(_validate_float("radius", radius, 0.01, 500.0))
    errors.extend(_validate_float("scale_per_item", scale_per_item, 0.01, 10.0))
    if errors:
        return [], errors

    transforms: list[ArrayTransform] = []
    warnings: list[str] = []

    for i in range(count):
        t = i / max(count - 1, 1)
        angle = t * turns * 2.0 * math.pi
        r = radius + t * radius_growth
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        z_val = t * height

        scale = scale_per_item
        roll = t * roll_per_item

        transforms.append(ArrayTransform(
            x=x, y=y, z=z_val,
            rot_x=0.0, rot_y=0.0, rot_z=angle + roll,
            scale_x=scale, scale_y=scale, scale_z=scale,
        ))

    return transforms, warnings


def compute_radial_array(
    count: int = 8,
    radius: float = 2.0,
    arc_angle: float = 6.283,
    scale_per_item: float = 1.0,
    rotate_with_arc: bool = True,
) -> tuple[list[ArrayTransform], list[str]]:
    """Compute instance transforms for a radial (circular arc) array.

    Returns (transforms, warnings).
    """
    errors: list[str] = []
    errors.extend(_validate_int("count", count, 1, 256))
    errors.extend(_validate_float("radius", radius, 0.01, 500.0))
    errors.extend(_validate_float("arc_angle", arc_angle, 0.01, 12.566))
    errors.extend(_validate_float("scale_per_item", scale_per_item, 0.01, 10.0))
    if errors:
        return [], errors

    transforms: list[ArrayTransform] = []
    warnings: list[str] = []

    effective_count = max(count, 1)
    for i in range(effective_count):
        t = i / effective_count if effective_count > 1 else 0.0
        angle = t * arc_angle
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        facing = angle + (math.pi / 2.0) if rotate_with_arc else 0.0

        transforms.append(ArrayTransform(
            x=x, y=y, z=0.0,
            rot_x=0.0, rot_y=0.0, rot_z=facing,
            scale_x=scale_per_item, scale_y=scale_per_item, scale_z=scale_per_item,
        ))

    return transforms, warnings


def compute_weighted_array(
    count: int = 50,
    scale_min: float = 0.5,
    scale_max: float = 1.5,
    seed: float = 0.0,
) -> tuple[list[ArrayTransform], list[str]]:
    """Compute random surface-distribution transforms.

    Pure-Python version generates positions within a unit square plane;
    UE adapter applies surface projection. Returns (transforms, warnings).
    """
    errors: list[str] = []
    errors.extend(_validate_int("count", count, 1, 5000))
    errors.extend(_validate_float("scale_min", scale_min, 0.01, 10.0))
    errors.extend(_validate_float("scale_max", scale_max, 0.01, 10.0))
    if errors:
        return [], errors

    import random
    rng = random.Random(seed)

    transforms: list[ArrayTransform] = []
    warnings: list[str] = []

    for _ in range(count):
        x = rng.uniform(-5.0, 5.0)
        y = rng.uniform(-5.0, 5.0)
        s = rng.uniform(scale_min, scale_max)
        rz = rng.uniform(0.0, 6.283)

        transforms.append(ArrayTransform(
            x=x, y=y, z=0.0,
            rot_x=0.0, rot_y=0.0, rot_z=rz,
            scale_x=s, scale_y=s, scale_z=s,
        ))

    return transforms, warnings


def compute_curve_array(
    count: int = 10,
    scale_start: float = 1.0,
    scale_end: float = 1.0,
    rotation_offset: float = 0.0,
    align_to_curve: bool = True,
) -> tuple[list[ArrayTransform], list[str]]:
    """Compute instance transforms along a generic curve parameter t in [0,1].

    The UE adapter maps these to curve-length sampling. Returns (transforms, warnings).
    """
    errors: list[str] = []
    errors.extend(_validate_int("count", count, 2, 500))
    errors.extend(_validate_float("scale_start", scale_start, 0.0, 10.0))
    errors.extend(_validate_float("scale_end", scale_end, 0.0, 10.0))
    if errors:
        return [], errors

    transforms: list[ArrayTransform] = []
    warnings: list[str] = []

    for i in range(count):
        t = i / max(count - 1, 1) if count > 1 else 0.0
        s = scale_start + (scale_end - scale_start) * t

        # Default: linear along X axis — UE adapter maps to actual curve
        x = t * 10.0
        rz = rotation_offset * t if align_to_curve else rotation_offset

        transforms.append(ArrayTransform(
            x=x, y=0.0, z=0.0,
            rot_x=0.0, rot_y=0.0, rot_z=rz,
            scale_x=s, scale_y=s, scale_z=s,
        ))

    return transforms, warnings


ARRAY_TOOL_SPECS: dict[str, dict[str, object]] = {
    "spiral": {
        "label": "Spiral Array",
        "description": "Helical sweep with radius growth, height, per-item roll",
        "params": [
            {"name": "count", "type": "int", "default": 32, "min": 2, "max": 512},
            {"name": "turns", "type": "float", "default": 3.0, "min": 0.1, "max": 100.0},
            {"name": "radius", "type": "float", "default": 2.0, "min": 0.01, "max": 500.0},
            {"name": "radius_growth", "type": "float", "default": 0.0, "min": -10.0, "max": 10.0},
            {"name": "height", "type": "float", "default": 4.0, "min": -20.0, "max": 20.0},
            {"name": "scale_per_item", "type": "float", "default": 1.0, "min": 0.01, "max": 10.0},
            {"name": "roll_per_item", "type": "float", "default": 0.0, "min": -6.283, "max": 6.283},
        ],
    },
    "radial": {
        "label": "Radial Array",
        "description": "Arc-distributed with angular offset and per-item rotation tracking",
        "params": [
            {"name": "count", "type": "int", "default": 8, "min": 1, "max": 256},
            {"name": "radius", "type": "float", "default": 2.0, "min": 0.01, "max": 500.0},
            {"name": "arc_angle", "type": "float", "default": 6.283, "min": 0.01, "max": 12.566},
            {"name": "scale_per_item", "type": "float", "default": 1.0, "min": 0.01, "max": 10.0},
            {"name": "rotate_with_arc", "type": "bool", "default": True},
        ],
    },
    "weighted": {
        "label": "Weighted Array",
        "description": "Random surface distribution with per-item random scale and alignment",
        "params": [
            {"name": "count", "type": "int", "default": 50, "min": 1, "max": 5000},
            {"name": "scale_min", "type": "float", "default": 0.5, "min": 0.01, "max": 10.0},
            {"name": "scale_max", "type": "float", "default": 1.5, "min": 0.01, "max": 10.0},
            {"name": "seed", "type": "float", "default": 0.0, "min": 0.0, "max": 10000.0},
        ],
    },
    "curve": {
        "label": "Curve Array",
        "description": "Curve-aligned array with start-to-end taper and rotation offset",
        "params": [
            {"name": "count", "type": "int", "default": 10, "min": 2, "max": 500},
            {"name": "scale_start", "type": "float", "default": 1.0, "min": 0.0, "max": 10.0},
            {"name": "scale_end", "type": "float", "default": 1.0, "min": 0.0, "max": 10.0},
            {"name": "rotation_offset", "type": "float", "default": 0.0, "min": -6.283, "max": 6.283},
            {"name": "align_to_curve", "type": "bool", "default": True},
        ],
    },
}


def spec_to_pcg_params(spec_id: str, params: dict[str, object]) -> dict[str, object]:
    """Convert an array tool spec + user params to PCG-compatible parameters."""
    transforms, warnings = globals()[f"compute_{spec_id}_array"](**params)
    mesh_path = params.get("mesh_path", "/Game/EnvSandbox/Shapes/SM_Cube.SM_Cube")
    return {
        "format": "gmm_pcg_array_v1",
        "array_type": spec_id,
        "mesh_path": mesh_path,
        "instance_count": len(transforms),
        "transforms": [t.to_dict() for t in transforms],
        "warnings": warnings,
    }
