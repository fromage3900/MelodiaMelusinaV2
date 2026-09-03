from __future__ import annotations

import sys
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from resonant_world_score import (  # noqa: E402
    PHRASE_BEATS,
    SCORE_VERSION,
    build_resonant_score,
    build_score_portfolio,
    validate_resonant_score,
)


def test_score_is_replayable_and_has_a_call_response_phrase() -> None:
    first = build_resonant_score(3900, movement_id="petal_cantata", chunk_x=0, chunk_y=0)
    second = build_resonant_score(3900, movement_id="petal_cantata", chunk_x=0, chunk_y=0)

    assert first == second
    assert first["score_version"] == SCORE_VERSION
    assert validate_resonant_score(first) == []
    assert len(first["events"]) == PHRASE_BEATS
    assert [event["phase"] for event in first["events"][:8]] == ["call"] * 8
    assert [event["phase"] for event in first["events"][8:]] == ["response"] * 8
    assert [stage["stage_id"] for stage in first["stages"]] == [
        "invocation", "unfolding", "threshold", "release"
    ]


def test_score_route_honors_shared_chunk_seams() -> None:
    left = build_resonant_score(3900, movement_id="cadence_cathedral", chunk_x=0, chunk_y=0)
    right = build_resonant_score(3900, movement_id="cadence_cathedral", chunk_x=1, chunk_y=0)

    assert left["route"]["east"]["signature"] == right["route"]["west"]["signature"]
    assert left["route"]["east"]["cell"] == left["route"]["points"][-1]
    assert right["route"]["west"]["cell"] == right["route"]["points"][0]
    assert all(0 <= x < 16 and 0 <= y < 16 for x, y in left["route"]["points"])


def test_score_voicing_uses_existing_asset_bindings_and_safe_quantum_boundary() -> None:
    score = build_resonant_score(3900, movement_id="liquid_cathedral", archetype_id="Melusina")
    all_refs = [
        ref
        for event in score["events"]
        for role in event["asset_voicing"].values()
        if isinstance(role, dict)
        for ref in [role.get("reference")]
        if ref
    ]

    assert all_refs
    assert any("water" in str(ref).lower() or "pond" in str(ref).lower() for ref in all_refs)
    assert len(score["quantum_setup"]["candidate_movements"]) == 2
    assert score["quantum_setup"]["quantum_is_selector_not_generator"] is True
    assert score["runtime_boundary"]["does_not_select_individual_voxels_with_quantum"] is True
    assert score["persistence"]["writes_save"] is False


def test_score_portfolio_covers_all_authored_movements() -> None:
    portfolio = build_score_portfolio(3900)

    assert portfolio["ok"] is True
    assert portfolio["score_count"] == 6
    assert portfolio["validation_errors"] == {}
