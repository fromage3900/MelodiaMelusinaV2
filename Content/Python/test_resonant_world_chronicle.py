"""Contract tests for the long-lived Resonant World memory read model."""
from __future__ import annotations

import sys
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from resonant_world_chronicle import (  # noqa: E402
    CHRONICLE_FORMAT,
    CHRONICLE_VERSION,
    build_chronicle,
    validate_chronicle,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_empty_chronicle_is_stable_and_read_only() -> None:
    first = build_chronicle(3900, movement_id="petal_cantata", project_root=PROJECT_ROOT)
    second = build_chronicle(3900, movement_id="petal_cantata", project_root=PROJECT_ROOT)

    assert first["chronicle_id"] == second["chronicle_id"]
    assert first["ok"] is True
    assert validate_chronicle(first) == []
    assert first["projection"]["discovered_movement_ids"] == ["petal_cantata"]
    assert first["persistence"]["writes_save"] is False
    assert first["runtime_boundary"]["does_not_apply_unreal"] is True
    assert first["materialization"]["writes_project_state"] is False


def test_event_projection_replays_discovery_style_and_sparse_edits() -> None:
    events = [
        {"sequence": 0, "event_type": "discovery", "chunk": [0, 0], "payload": {"movement_id": "star_loom"}},
        {"sequence": 1, "event_type": "movement_attuned", "chunk": [1, 0], "payload": {"movement_id": "star_loom"}},
        {"sequence": 2, "event_type": "score_completed", "chunk": [1, 0], "payload": {"score_id": "score_echo"}},
        {"sequence": 3, "event_type": "style_voicing", "chunk": [1, 0], "payload": {"archetype_id": "SakuraDreamer", "style_axes": ["pearlescent", "petal"]}},
        {"sequence": 4, "event_type": "voxel_edit", "chunk": [1, 0], "payload": {"cell": [2, 3, 4], "material_id": "note_block", "pitch_class": 9, "timbre": "crystal"}},
        {"sequence": 5, "event_type": "voxel_edit", "chunk": [1, 0], "payload": {"cell": [2, 3, 4], "material_id": "note_block", "pitch_class": 10, "timbre": "bells"}},
    ]
    chronicle = build_chronicle(3900, movement_id="petal_cantata", events=events, project_root=PROJECT_ROOT)

    assert chronicle["ok"] is True
    projection = chronicle["projection"]
    assert projection["attuned_movement_id"] == "star_loom"
    assert projection["discovered_movement_ids"] == ["star_loom"]
    assert projection["visited_chunks"] == [[0, 0], [1, 0]]
    assert projection["completed_score_ids"] == ["score_echo"]
    assert projection["style_voicings"][0]["archetype_id"] == "SakuraDreamer"
    assert projection["voxel_edits"][0]["pitch_class"] == 10
    assert projection["voxel_edits"][0]["timbre"] == "bells"


def test_invalid_chronicle_is_rejected() -> None:
    malformed = {
        "format": CHRONICLE_FORMAT,
        "chronicle_version": CHRONICLE_VERSION,
        "world": {"movement_id": "petal_cantata"},
        "events": [
            {"event_id": "duplicate", "sequence": 1, "event_type": "world_opened"},
            {"event_id": "duplicate", "sequence": 0, "event_type": "unknown"},
        ],
        "projection": {"attuned_movement_id": "not_authored"},
        "runtime_boundary": {},
        "materialization": {"writes_project_state": True},
    }
    errors = validate_chronicle(malformed)

    assert errors
    assert any("sequences" in error for error in errors)
    assert any("event IDs" in error for error in errors)
    assert any("unknown chronicle" in error for error in errors)
    assert any("attuned movement" in error for error in errors)
    assert any("materialization" in error for error in errors)


def test_chronicle_embeds_asset_and_quantum_source_provenance() -> None:
    chronicle = build_chronicle(3900, movement_id="liquid_cathedral", project_root=PROJECT_ROOT)
    provenance = chronicle["source_provenance"]

    assert chronicle["ok"] is True
    assert provenance["score_id"]
    assert provenance["constellation_id"]
    assert provenance["asset_bindings"]
    assert provenance["quantum"]["trace_id"]
    assert provenance["quantum"]["provenance_embedded_in_trace"] is True
