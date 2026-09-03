from __future__ import annotations

import sys
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from resonant_world_capture_manifest import (  # noqa: E402
    CAPTURE_MANIFEST_VERSION,
    build_capture_manifest,
    validate_capture_manifest,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_capture_manifest_has_four_canonical_slots_and_is_read_only() -> None:
    manifest = build_capture_manifest(3900, project_root=PROJECT_ROOT)

    assert manifest["capture_manifest_version"] == CAPTURE_MANIFEST_VERSION
    assert len(manifest["targets"]) == 4
    assert validate_capture_manifest(manifest) == []
    assert manifest["runtime_boundary"]["does_not_render"] is True
    assert manifest["materialization"]["writes_project_state"] is False


def test_capture_manifest_exposes_absolute_existing_source_assets() -> None:
    manifest = build_capture_manifest(3900, movement_id="petal_cantata", project_root=PROJECT_ROOT)

    assert len(manifest["targets"]) == 2
    refs = [ref for target in manifest["targets"] for ref in target["source_asset_refs"]]
    assert refs
    existing = [ref for ref in refs if ref.get("absolute_path")]
    assert existing
    assert all(Path(ref["absolute_path"]).is_absolute() for ref in existing)
    assert all(Path(ref["absolute_path"]).exists() for ref in existing)


def test_capture_manifest_does_not_call_observed_candidates_publishable() -> None:
    manifest = build_capture_manifest(3900, project_root=PROJECT_ROOT)

    assert manifest["verification"]["clean_approved_count"] == 0
    assert all(target["status"] != "publishable" for target in manifest["targets"])
    assert all(
        target["clean_frame_requirements"]["visual_approval"] == "required"
        for target in manifest["targets"]
    )
