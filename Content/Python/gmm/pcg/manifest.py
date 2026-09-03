"""Canonical Surreal world-manifest contract shared by GMM and UE tools."""
from __future__ import annotations

import hashlib
import math
from typing import Any

FORMAT_ID = "surreal_arch_world_v1"
SCHEMA_VERSION = 2
COORDINATE_SYSTEM = "blender_z_up_meters"


def stable_instance_id(world_root: str, role: str, lib: str, source: str, ordinal: int) -> str:
    """Return a deterministic ID that is independent of Blender object suffixes."""
    raw = f"{world_root}|{role}|{lib}|{source}|{ordinal}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def _is_matrix4(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 4
        and all(isinstance(row, list) and len(row) == 4 for row in value)
        and all(isinstance(cell, (int, float)) and math.isfinite(cell) for row in value for cell in row)
    )


def validate_manifest(data: Any, *, require_resolved_meshes: bool = False) -> list[str]:
    """Validate the canonical producer/consumer contract.

    Structural validation is useful before assets are imported. Set
    ``require_resolved_meshes`` for an apply/release gate.
    """
    if not isinstance(data, dict):
        return ["manifest root must be an object"]

    errors: list[str] = []
    if data.get("format") != FORMAT_ID:
        errors.append(f"format must be {FORMAT_ID!r}")
    version = data.get("schema_version")
    if not isinstance(version, int) or version < 1 or version > SCHEMA_VERSION:
        errors.append(f"schema_version must be between 1 and {SCHEMA_VERSION}")
    if data.get("coordinate_system") not in ("blender_z_up", COORDINATE_SYSTEM):
        errors.append(f"unsupported coordinate_system: {data.get('coordinate_system')!r}")

    instances = data.get("instances")
    if not isinstance(instances, list):
        errors.append("instances must be an array")
        return errors
    if data.get("instance_count") != len(instances):
        errors.append("instance_count must equal len(instances)")

    seen_ids: set[str] = set()
    for index, entry in enumerate(instances):
        prefix = f"instances[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("role", "lib", "object"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if not _is_matrix4(entry.get("transform")):
            errors.append(f"{prefix}.transform must be a finite 4x4 matrix")
        stable_id = entry.get("id")
        if version and version >= 2:
            if not isinstance(stable_id, str) or not stable_id:
                errors.append(f"{prefix}.id is required for schema v2")
            elif stable_id in seen_ids:
                errors.append(f"{prefix}.id duplicates {stable_id!r}")
            else:
                seen_ids.add(stable_id)
        mesh_path = entry.get("static_mesh_path")
        if require_resolved_meshes and (not isinstance(mesh_path, str) or not mesh_path.startswith("/Game/")):
            errors.append(f"{prefix}.static_mesh_path must resolve under /Game/ for apply")

    groups = data.get("hism_groups", [])
    if not isinstance(groups, list):
        errors.append("hism_groups must be an array")
    else:
        if instances and not groups:
            errors.append("hism_groups must not be empty when instances are present")
        grouped_count = 0
        for index, group in enumerate(groups):
            if not isinstance(group, dict):
                errors.append(f"hism_groups[{index}] must be an object")
                continue
            if require_resolved_meshes:
                mesh_path = group.get("static_mesh_path")
                if not isinstance(mesh_path, str) or not mesh_path.startswith("/Game/"):
                    errors.append(f"hism_groups[{index}].static_mesh_path must resolve under /Game/ for apply")
            transforms = group.get("transforms")
            if not isinstance(transforms, list) or not all(_is_matrix4(xf) for xf in transforms):
                errors.append(f"hism_groups[{index}].transforms must contain 4x4 matrices")
                continue
            if group.get("instance_count") != len(transforms):
                errors.append(f"hism_groups[{index}].instance_count mismatch")
            grouped_count += len(transforms)
        if groups and grouped_count != len(instances):
            errors.append("HISM group transform total must equal instance_count")
    return errors


def manifest_summary(data: dict, *, require_resolved_meshes: bool = False) -> dict:
    errors = validate_manifest(data, require_resolved_meshes=require_resolved_meshes)
    instances = data.get("instances") if isinstance(data, dict) else []
    instances = instances if isinstance(instances, list) else []
    unresolved = [entry.get("id") or entry.get("object") for entry in instances if not str(entry.get("static_mesh_path", "")).startswith("/Game/")]
    return {
        "ok": not errors,
        "format": data.get("format") if isinstance(data, dict) else None,
        "schema_version": data.get("schema_version") if isinstance(data, dict) else None,
        "instance_count": len(instances),
        "hism_group_count": len(data.get("hism_groups", [])) if isinstance(data, dict) and isinstance(data.get("hism_groups", []), list) else 0,
        "unresolved_mesh_count": len(unresolved),
        "unresolved_meshes": unresolved,
        "errors": errors,
    }
