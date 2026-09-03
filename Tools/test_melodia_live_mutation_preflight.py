#!/usr/bin/env python3
"""Focused regression coverage for the read-only IntegrationMap owner gate."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Tools"))

import melodia_live_mutation_preflight as preflight  # noqa: E402


def main() -> int:
    clean = {
        name: {"exists": True, "class": "DataTable"}
        for name in preflight.DATATABLES
    }
    ready = preflight.evaluate_readiness(
        {"dirty_packages": []},
        {"logs": []},
        clean,
    )
    assert ready["ready_for_map_mutation"] is True
    assert ready["mutations_issued"] is False

    blocked = preflight.evaluate_readiness(
        {
            "dirty_packages": [
                {"package": "/Game/Other/DirtyMap", "is_map": True},
                {"package": "/Game/Other/DirtyAsset", "is_map": False},
            ]
        },
        {"logs": [{"message": "LogMonolith: Warning: MODAL_OPEN"}]},
        {
            "DT_MelodySlime_Enemies": {"exists": False},
            "DT_MelodySlime_Skills": {"exists": True},
            "DT_MelodySlime_RoomMods": {"exists": False},
        },
    )
    assert blocked["ready_for_map_mutation"] is False
    assert "another_dirty_map_present" in blocked["blockers"]
    assert "unrelated_dirty_packages_present" in blocked["blockers"]
    assert "modal_evidence_present" in blocked["blockers"]
    assert blocked["absent_datatables"] == [
        "DT_MelodySlime_Enemies",
        "DT_MelodySlime_RoomMods",
    ]

    print("validated read-only map mutation preflight guards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
