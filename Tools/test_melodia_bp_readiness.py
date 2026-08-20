"""Offline regression checks for the Melodia Blueprint readiness inventory."""

from __future__ import annotations

import sys
import json
from pathlib import Path

from melodia_bp_readiness import KAWAII_PROBE, build_report


def main() -> int:
    report = build_report()
    templates = report["templates"]
    assert report["kind"] == "melodia_blueprint_readiness_report"
    assert len(templates) == 7
    assert report["live_evidence_available"] is False
    assert report["summary"]["promoted_l2_or_higher"] == 0
    assert report["kawaii_probe"]["asset_path"] == KAWAII_PROBE
    kawaii_contract_path = Path(__file__).resolve().parents[1] / "specs" / "blueprints" / "kawaii_physics_placement_probe.v1.json"
    with kawaii_contract_path.open("r", encoding="utf-8") as handle:
        kawaii_contract = json.load(handle)
    promotion = kawaii_contract["production_promotion_contract"]
    assert promotion["promotion_status"] == "fixture_only_until_l4"
    assert promotion["root_body_policy"]["missing_body_behavior"] == "fail_closed_and_use_no_physics_variant"
    assert set(promotion["runtime_variants"]) >= {"full_physics", "reduced_physics", "no_physics_fallback"}
    assert promotion["map_policy"]["save_reload_is_required_before_promotion"] is True
    for item in templates:
        assert item["readiness"] in {"planned_L0_missing_asset", "L0_inventory_only_live_pending"}
        materialization = item.get("materialization")
        assert isinstance(materialization, dict), item["id"]
        assert materialization.get("artifact_model"), item["id"]
        assert materialization.get("status"), item["id"]
        assert materialization.get("materialization_blockers"), item["id"]
        fixture = item.get("fixture")
        if fixture is not None:
            assert fixture["state"] in {"L1_contract_spec_only", "contract_needs_review", "missing_contract", "invalid_contract"}
    print(
        f"validated Blueprint readiness inventory: {len(templates)} templates, "
        f"{report['summary']['contract_only_fixtures']} contract fixtures, live proof pending"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
