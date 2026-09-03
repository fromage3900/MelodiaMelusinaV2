"""Offline validation for the UE World Partition traversal-grid handoff."""
from __future__ import annotations

import math
from typing import Any
import json
from pathlib import Path

LEVEL_KEYS = {"SakuraDream", "SpaceCathedral", "BaroqueGrotto", "CosmicOrrery"}


def validate_wp_grid_report(report: Any) -> list[str]:
    """Validate deployment evidence without importing Unreal."""
    if not isinstance(report, dict):
        return ["grid report must be an object"]
    errors: list[str] = []
    results = report.get("results", report.get("levels"))
    if not isinstance(results, list):
        return ["grid report must contain a results array"]
    seen: set[str] = set()
    for index, entry in enumerate(results):
        prefix = f"results[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        level = entry.get("level")
        if level not in LEVEL_KEYS:
            errors.append(f"{prefix}.level is unknown")
        elif level in seen:
            errors.append(f"{prefix}.level is duplicated")
        else:
            seen.add(level)
        if not isinstance(entry.get("graph"), str) or not entry["graph"].startswith("/Game/"):
            errors.append(f"{prefix}.graph must be a project asset path")
        if not isinstance(entry.get("style_id"), str) or not entry["style_id"]:
            errors.append(f"{prefix}.style_id must be present")
        if entry.get("navigation_configured") is not True:
            errors.append(f"{prefix}.navigation_configured must be true")
        for field in ("platforms", "pcg_volumes", "links"):
            value = entry.get(field)
            if not isinstance(value, int) or value < 0:
                errors.append(f"{prefix}.{field} must be a non-negative integer")
        nodes = entry.get("route_nodes", [])
        if not isinstance(nodes, list) or len(nodes) != entry.get("platforms", -1):
            errors.append(f"{prefix}.route_nodes must match platforms")
        for node_index, node in enumerate(nodes if isinstance(nodes, list) else []):
            location = node.get("location_cm") if isinstance(node, dict) else None
            if not isinstance(location, list) or len(location) != 3 or not all(
                isinstance(value, (int, float)) and math.isfinite(value) for value in location
            ):
                errors.append(f"{prefix}.route_nodes[{node_index}].location_cm must be finite XYZ")
            if isinstance(node, dict) and node.get("encounter_clear") is not True:
                errors.append(f"{prefix}.route_nodes[{node_index}] must declare encounter_clear")
    if seen and seen != LEVEL_KEYS:
        errors.append("grid report must cover all four WP levels")
    return errors


def report_summary(report: Any) -> dict[str, Any]:
    errors = validate_wp_grid_report(report)
    results = report.get("results", []) if isinstance(report, dict) else []
    return {"ok": not errors, "levels": len(results) if isinstance(results, list) else 0, "errors": errors}


def validate_wp_grid_file(path: str | Path) -> dict[str, Any]:
    report_path = Path(path).expanduser().resolve()
    if not report_path.is_file():
        return {"ok": False, "path": str(report_path), "errors": ["grid report does not exist"]}
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "path": str(report_path), "errors": [f"JSON load failed: {exc}"]}
    return {"path": str(report_path), **report_summary(report)}
