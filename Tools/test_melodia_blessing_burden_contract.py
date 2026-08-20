#!/usr/bin/env python3
"""Validate the offline Blessing/Burden contract and expose unfinished runtime seams."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "specs" / "roguelike" / "melodia_blessing_burden_contract.v1.json"
BLESSINGS = ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_Blessings.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    contract = load_json(CONTRACT)
    data = load_json(BLESSINGS)
    rows = data.get("Rows")
    assert contract["kind"] == "melodia_blessing_burden_contract"
    assert data.get("DataType") == contract["source_content"]["data_type"]
    assert isinstance(rows, dict) and rows
    assert len(rows) == contract["source_content"]["observed_row_count"] == 26

    required = set(contract["source_content"]["required_fields"])
    stable_ids = []
    burden_rows = []
    for row_key, row in rows.items():
        assert required <= set(row), row_key
        assert row_key == row["blessing_id"], row_key
        assert isinstance(row["token_cost"], int) and row["token_cost"] >= 0, row_key
        assert isinstance(row["effect_type"], str) and row["effect_type"], row_key
        assert isinstance(row["effect_value"], (int, float)), row_key
        stable_ids.append(row["blessing_id"])
        if "burden" in row_key.lower() or "burden" in row["effect_type"].lower():
            burden_rows.append(row_key)

    assert len(stable_ids) == len(set(stable_ids)), "duplicate blessing IDs"
    assert not burden_rows, burden_rows
    assert contract["source_content"]["observed_burden_row_count"] == 0
    assert contract["burden"]["status"] == "design_pending"
    assert contract["runtime_authority"]["catalog_consumer"] is None
    assert contract["runtime_authority"]["purchase_and_apply_authority"] is None
    assert contract["runtime_authority"]["currency_authority_decision"] == "pending_owner_decision"

    widget = ROOT / "Content" / "Melodia" / "UI" / "WBP_BlessingBurden.uasset"
    assert widget.is_file(), widget
    generator_inspector = ROOT / "Content" / "Python" / "audit_roguelike_generator_readonly.py"
    assert generator_inspector.is_file(), generator_inspector
    entrance = ROOT / "Plugins" / "MelodiaCore" / "Source" / "MelodiaCore" / "MelodiaRoomEntrance.cpp"
    assert entrance.is_file(), entrance

    print(
        "validated Blessing/Burden contract: "
        f"{len(rows)} blessings, {len(burden_rows)} burdens, "
        "runtime consumer/currency pending"
    )


if __name__ == "__main__":
    main()
