"""Procedural-content governance, manifest contracts, and release gates."""
from __future__ import annotations

from gmm.pcg.control import preflight, release_gate, repair_quarantined_references, validate_manifest_file
from gmm.pcg.manifest import (
    COORDINATE_SYSTEM,
    FORMAT_ID,
    SCHEMA_VERSION,
    manifest_summary,
    stable_instance_id,
    validate_manifest,
)
from gmm.pcg.wp_grid import report_summary, validate_wp_grid_file, validate_wp_grid_report

__all__ = [
    "COORDINATE_SYSTEM",
    "FORMAT_ID",
    "SCHEMA_VERSION",
    "manifest_summary",
    "preflight",
    "release_gate",
    "repair_quarantined_references",
    "stable_instance_id",
    "validate_manifest",
    "validate_manifest_file",
    "report_summary",
    "validate_wp_grid_file",
    "validate_wp_grid_report",
]
