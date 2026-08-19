"""Focused offline checks for the IntegrationMap overhaul contract."""

from __future__ import annotations

from melodia_integration_map_contract import build_report


def main() -> int:
    report = build_report()
    assert report["kind"] == "melodia_integration_map_contract_report"
    assert report["offline_only"] is True
    assert report["mutations_issued"] is False
    assert report["live_evidence_available"] is False
    assert report["offline_contract_status"] == "pass"

    inventory = report["inventory"]
    assert inventory["source_shape"] == "class_counts"
    assert inventory["calculated_total"] == 149
    assert inventory["world_matches_proof_map"] is True
    assert inventory["unclassified_classes"] == []
    assert inventory["category_totals"]["replace"] == 78
    assert all(item["status"] == "pass" for item in inventory["singleton_checks"])
    assert inventory["actor_level_evidence_available"] is False

    fixtures = report["fixture_readiness"]
    assert fixtures["kit_size"] == 12
    assert fixtures["all_contracts_ready"] is True
    assert fixtures["live_graphs_proven"] == 0
    assert fixtures["live_placements_proven"] == 0
    assert all(item["live_graph_status"] == "pending" for item in fixtures["items"])

    slime = report["slime_variants"]
    assert slime["offline_contract_status"] == "pass"
    assert slime["row_counts"] == {"enemy": 48, "skill": 24, "room_mod": 21}
    imported = slime["imported_assets"]
    assert {
        name: item["asset_path"] for name, item in imported.items()
    } == {
        "DT_MelodySlime_Enemies": "/Game/Melodia/DataStuctures/DT_MelodySlime_Enemies",
        "DT_MelodySlime_Skills": "/Game/Melodia/DataStuctures/DT_MelodySlime_Skills",
        "DT_MelodySlime_RoomMods": "/Game/Melodia/DataStuctures/DT_MelodySlime_RoomMods",
    }
    assert {
        name: item["expected_row_count"] for name, item in imported.items()
    } == {
        "DT_MelodySlime_Enemies": 48,
        "DT_MelodySlime_Skills": 24,
        "DT_MelodySlime_RoomMods": 21,
    }
    assert len(slime["proof_variants"]) == 3
    assert all(item["status"] == "data_only_row_ready" for item in slime["proof_variants"])
    assert slime["data_only_acceptance"]["expected_new_authority_count"] == 0
    assert slime["data_only_acceptance"]["expected_new_blueprint_count"] == 0
    assert slime["live_parent_status"] == "pending"
    assert slime["live_battle_presentation_status"] == "pending"

    wiring = report["wiring_preflight"]
    assert wiring["ready_for_live_mutation"] is False
    assert all(item["status"] == "pass" for item in wiring["static_preconditions"])
    assert all(item["status"] == "pending" for item in wiring["live_preconditions"])

    print("validated IntegrationMap inventory, 12-asset kit, three data-only slime variants, and wiring gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
