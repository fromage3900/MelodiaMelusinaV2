"""Focused offline checks for the puzzle -> water -> quest preflight."""

from __future__ import annotations

from melodia_wiring_preflight import build_report


def main() -> int:
    report = build_report()
    assert report["kind"] == "melodia_wiring_preflight_report"
    assert report["offline_only"] is True
    assert report["mutations_issued"] is False
    assert report["live_evidence_available"] is False
    assert report["ready_for_live_mutation"] is False
    assert all(item["status"] == "pass" for item in report["static_preconditions"])
    assert all(item["status"] == "pending" for item in report["live_preconditions"])
    assert report["allowlist_check"]["flag_present"] is True
    assert report["allowlist_check"]["quest_present"] is True
    assert report["allowlist_check"]["flag"] == "first_resonance_solved"
    assert report["allowlist_check"]["quest"] == "quest.first_dream"
    assert any(item["path"].endswith("wire_melusina_spatial_puzzles.py") for item in report["source_checks"])
    print("validated offline puzzle -> water -> quest preconditions; live graph/save proof remains pending")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
