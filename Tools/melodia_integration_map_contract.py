#!/usr/bin/env python3
"""Offline contract gate for the disposable MelodiaIntegrationMap proof lane.

This tool classifies the existing class-count inventory, validates the planned
fixture kit, checks the three data-only Melody Slime proof rows, and imports the
safe wiring preflight.  It never opens an editor, mutates a Blueprint, saves a
map, or claims PIE/map-placement evidence.

Usage:
    python Tools/melodia_integration_map_contract.py
    python Tools/melodia_integration_map_contract.py --json
    python Tools/melodia_integration_map_contract.py --strict  # expected to fail live gates
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from melodia_wiring_preflight import build_report as build_wiring_report


ROOT = Path(__file__).resolve().parents[1]
MAP_CONTRACT_PATH = ROOT / "specs" / "blueprints" / "melodia_integration_map_overhaul.v1.json"
SLIME_CONTRACT_PATH = ROOT / "specs" / "blueprints" / "melody_slime_variant_contract.v1.json"
INVENTORY_PATH = ROOT / "Saved" / "Audit" / "integration_map_inventory.json"
SLIME_TABLES = {
    "DT_MelodySlime_Enemies": {
        "asset_path": "/Game/Melodia/DataStuctures/DT_MelodySlime_Enemies",
        "row_struct": "FMelodiaSlimeEnemyRow",
        "expected_count": 48,
    },
    "DT_MelodySlime_Skills": {
        "asset_path": "/Game/Melodia/DataStuctures/DT_MelodySlime_Skills",
        "row_struct": "FMelodiaSlimeSkillRow",
        "expected_count": 24,
    },
    "DT_MelodySlime_RoomMods": {
        "asset_path": "/Game/Melodia/DataStuctures/DT_MelodySlime_RoomMods",
        "row_struct": "FMelodiaSlimeRoomModRow",
        "expected_count": 21,
    },
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def relpath(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def game_asset_path_to_file(asset_path: str) -> Path:
    if not asset_path.startswith("/Game/"):
        raise ValueError(f"unsupported asset path: {asset_path}")
    relative = asset_path.removeprefix("/Game/").replace("/", "/")
    return ROOT / "Content" / f"{relative}.uasset"


def _class_counts(inventory: dict[str, Any]) -> tuple[dict[str, int], list[dict[str, Any]]]:
    raw_classes = inventory.get("classes")
    if isinstance(raw_classes, dict):
        counts: dict[str, int] = {}
        for class_name, count in raw_classes.items():
            if not isinstance(count, int) or count < 0:
                raise ValueError(f"inventory class count must be a non-negative integer: {class_name}")
            counts[str(class_name)] = count
        return counts, []

    actors = inventory.get("actors")
    if not isinstance(actors, list):
        raise ValueError("inventory must contain either a classes object or an actors array")
    records: list[dict[str, Any]] = []
    counts = Counter()
    for index, actor in enumerate(actors):
        if not isinstance(actor, dict):
            raise ValueError(f"inventory actor {index} must be an object")
        class_name = actor.get("class") or actor.get("class_name")
        if not class_name:
            raise ValueError(f"inventory actor {index} has no class/class_name")
        class_name = str(class_name)
        counts[class_name] += 1
        records.append(actor)
    return dict(counts), records


def classify_inventory(
    inventory: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    counts, actor_records = _class_counts(inventory)
    rules: dict[str, dict[str, Any]] = {}
    duplicate_rules: list[str] = []
    for rule in contract["inventory"]["classification_rules"]:
        for class_name in rule["class_names"]:
            if class_name in rules:
                duplicate_rules.append(class_name)
            rules[class_name] = rule
    if duplicate_rules:
        raise ValueError(f"duplicate inventory classification rules: {sorted(set(duplicate_rules))}")

    declared_total = inventory.get("total")
    calculated_total = sum(counts.values())
    total_matches = declared_total is None or declared_total == calculated_total
    classifications = []
    category_totals: Counter[str] = Counter()
    unclassified: list[str] = []
    for class_name in sorted(counts):
        rule = rules.get(class_name)
        category = str(rule["category"]) if rule else "unclassified"
        if rule is None:
            unclassified.append(class_name)
        category_totals[category] += counts[class_name]
        item: dict[str, Any] = {
            "class_name": class_name,
            "count": counts[class_name],
            "category": category,
            "reason": rule.get("reason") if rule else "No deterministic rule exists; owner review required.",
        }
        if rule and "expected_count" in rule:
            item["expected_count"] = rule["expected_count"]
            item["singleton_status"] = (
                "pass" if counts[class_name] == rule["expected_count"] else "fail"
            )
        classifications.append(item)

    singleton_checks = []
    for expectation in contract["inventory"]["singleton_expectations"]:
        count = counts.get(expectation["class_name"], 0)
        singleton_checks.append(
            {
                "class_name": expectation["class_name"],
                "observed_count": count,
                "min_count": expectation["min_count"],
                "max_count": expectation["max_count"],
                "status": (
                    "pass"
                    if expectation["min_count"] <= count <= expectation["max_count"]
                    else "fail"
                ),
            }
        )

    world = str(inventory.get("world", ""))
    proof_map = contract["proof_map"]
    world_normalized = world.split(".", 1)[0]
    return {
        "source": relpath(INVENTORY_PATH),
        "source_shape": "actor_records" if actor_records else "class_counts",
        "world": world,
        "world_matches_proof_map": world_normalized == proof_map,
        "declared_total": declared_total,
        "calculated_total": calculated_total,
        "total_matches": total_matches,
        "class_counts": dict(sorted(counts.items())),
        "classifications": classifications,
        "category_totals": dict(sorted(category_totals.items())),
        "unclassified_classes": unclassified,
        "singleton_checks": singleton_checks,
        "actor_level_evidence_available": bool(actor_records),
        "status": (
            "classified_before_snapshot"
            if total_matches
            and world_normalized == proof_map
            and not unclassified
            and all(item["status"] == "pass" for item in singleton_checks)
            else "inventory_needs_review"
        ),
        "claim_boundary": contract["inventory"]["evidence_limit"],
    }


def fixture_contract_check(
    fixture_path: Path,
    expected_asset: str,
    proof_map: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": relpath(fixture_path),
        "exists": fixture_path.is_file(),
        "asset_path": expected_asset,
        "asset_on_disk": game_asset_path_to_file(expected_asset).is_file(),
    }
    if not fixture_path.is_file():
        result.update({"status": "missing_fixture_contract", "checks": {}})
        return result
    try:
        fixture = load_json(fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result.update({"status": "invalid_fixture_contract", "error": str(exc), "checks": {}})
        return result

    if fixture.get("kind") == "melodia_content_fixture":
        package = fixture.get("package", {})
        blueprint = fixture.get("blueprint", {})
        checks = {
            "kind": True,
            "status": fixture.get("status") == "contract_spec_only",
            "readiness_level": fixture.get("readiness_level") == "L1",
            "planned_asset": blueprint.get("planned_asset") == expected_asset,
            "fixture_map": package.get("FixtureMap") == proof_map,
            "entry_route": bool(fixture.get("deterministic_fixture", {}).get("entry_route")),
            "reset_route": bool(fixture.get("deterministic_fixture", {}).get("reset_route")),
            "authority_declared": bool(blueprint.get("runtime_authority")),
        }
    else:
        checks = {
            "kind": fixture.get("kind") == "melodia_integration_map_fixture",
            "status": fixture.get("status") == "contract_spec_only",
            "readiness_level": fixture.get("readiness_level") == "L1",
            "planned_asset": fixture.get("planned_asset") == expected_asset,
            "fixture_map": fixture.get("map") == proof_map,
            "entry_route": bool(fixture.get("entry_route")),
            "reset_route": bool(fixture.get("reset_route")),
            "authority_declared": bool(fixture.get("authority")),
        }
    result.update(
        {
            "fixture_id": fixture.get("fixture_id"),
            "kind": fixture.get("kind"),
            "checks": checks,
            "status": "L1_contract_ready" if all(checks.values()) else "fixture_needs_review",
            "live_graph_status": "pending",
            "live_placement_status": "pending",
        }
    )
    return result


def fixture_readiness(contract: dict[str, Any]) -> dict[str, Any]:
    items = []
    for kit in contract["fixture_kit"]:
        asset_path = str(kit["asset_path"])
        asset_file = game_asset_path_to_file(asset_path)
        item: dict[str, Any] = {
            "id": kit["id"],
            "role": kit["role"],
            "asset_path": asset_path,
            "asset_file": relpath(asset_file),
            "asset_on_disk": asset_file.is_file(),
            "fixture_spec": kit.get("fixture_spec"),
            "parent_contract": kit["parent_contract"],
            "live_graph_status": "pending",
            "live_map_status": "pending",
        }
        fixture_spec = kit.get("fixture_spec")
        if fixture_spec:
            item["fixture"] = fixture_contract_check(
                ROOT / fixture_spec,
                asset_path,
                contract["proof_map"],
            )
        else:
            item["fixture"] = {
                "status": "authority_contract_live_pending",
                "checks": {"asset_path_declared": True},
            }
        item["offline_status"] = (
            "asset_and_contract_present_live_pending"
            if item["asset_on_disk"]
            and item["fixture"]["status"] in {"L1_contract_ready", "authority_contract_live_pending"}
            else "contract_or_asset_missing"
        )
        items.append(item)
    return {
        "items": items,
        "all_contracts_ready": all(
            item["fixture"]["status"] in {"L1_contract_ready", "authority_contract_live_pending"}
            for item in items
        ),
        "assets_on_disk": sum(item["asset_on_disk"] for item in items),
        "kit_size": len(items),
        "live_graphs_proven": 0,
        "live_placements_proven": 0,
    }


def rows_from_source(path: Path, table_label: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    payload = load_json(path)
    rows = payload.get("Rows")
    if not isinstance(rows, dict):
        raise ValueError(f"{table_label} must contain a Rows object")
    normalized: dict[str, dict[str, Any]] = {}
    for row_id, row in rows.items():
        if not isinstance(row, dict):
            raise ValueError(f"{table_label} row {row_id} must be an object")
        normalized[str(row_id)] = row
    return normalized, payload


def slime_contract_check(contract: dict[str, Any]) -> dict[str, Any]:
    source_paths = {
        "enemy": ROOT / contract["data_sources"]["enemy_rows"],
        "skill": ROOT / contract["data_sources"]["skill_rows"],
        "room_mod": ROOT / contract["data_sources"]["room_mod_rows"],
    }
    table_rows: dict[str, dict[str, dict[str, Any]]] = {}
    table_payloads: dict[str, dict[str, Any]] = {}
    source_checks: dict[str, Any] = {}
    for table, path in source_paths.items():
        if not path.is_file():
            source_checks[table] = {"path": relpath(path), "exists": False, "status": "missing"}
            table_rows[table] = {}
            table_payloads[table] = {}
            continue
        rows, payload = rows_from_source(path, table)
        table_rows[table] = rows
        table_payloads[table] = payload
        source_checks[table] = {
            "path": relpath(path),
            "exists": True,
            "row_count": len(rows),
            "status": "loaded",
        }

    schema = contract["row_schema"]
    schema_checks: list[dict[str, Any]] = []
    for table, field_key, id_field in (
        ("enemy", "enemy_required_fields", "enemy_id"),
        ("skill", "skill_required_fields", "skill_id"),
        ("room_mod", "room_mod_required_fields", "blessing_id"),
    ):
        required = set(schema[field_key])
        missing = []
        invalid_ids = []
        for row_key, row in table_rows[table].items():
            missing_fields = sorted(required - set(row))
            if missing_fields:
                missing.append({"row": row_key, "fields": missing_fields})
            if table != "room_mod" and str(row.get(id_field, "")) != row_key:
                invalid_ids.append(row_key)
        schema_checks.append(
            {
                "table": table,
                "missing_fields": missing,
                "id_mismatches": invalid_ids,
                "status": "pass" if not missing and not invalid_ids else "fail",
            }
        )

    content_checks: list[dict[str, Any]] = []
    allowed_elements = set(schema["allowed_elements"])
    for row_id, row in table_rows["enemy"].items():
        numeric_valid = all(
            isinstance(row.get(field), (int, float)) and row[field] > 0
            for field in ("max_hp", "max_toughness", "base_damage", "speed")
        )
        bpm = row.get("bpm")
        element_valid = row.get("element") in allowed_elements
        bpm_valid = isinstance(bpm, (int, float)) and schema["bpm_range"][0] <= bpm <= schema["bpm_range"][1]
        content_checks.append(
            {
                "table": "enemy",
                "row": row_id,
                "status": "pass" if numeric_valid and element_valid and bpm_valid else "fail",
                "numeric_valid": numeric_valid,
                "element_valid": element_valid,
                "bpm_valid": bpm_valid,
            }
        )
    for row_id, row in table_rows["skill"].items():
        pitches = row.get("note_pitches")
        durations = row.get("note_durations")
        arrays_valid = (
            isinstance(pitches, list)
            and isinstance(durations, list)
            and len(pitches) == len(durations)
            and len(pitches) > 0
        )
        content_checks.append(
            {
                "table": "skill",
                "row": row_id,
                "status": "pass" if arrays_valid else "fail",
                "parallel_note_arrays": arrays_valid,
            }
        )

    variants = []
    for proof in contract["proof_variants"]:
        enemy_id = proof["enemy_row"]
        skill_ids = proof["skill_rows"]
        room_ids = proof["room_mod_rows"]
        checks = {
            "enemy_row": enemy_id in table_rows["enemy"],
            "skill_rows": bool(skill_ids) and all(item in table_rows["skill"] for item in skill_ids),
            "room_mod_rows": bool(room_ids) and all(item in table_rows["room_mod"] for item in room_ids),
            "data_only": True,
        }
        variants.append(
            {
                "variant_id": proof["variant_id"],
                "enemy_row": enemy_id,
                "skill_rows": skill_ids,
                "room_mod_rows": room_ids,
                "checks": checks,
                "status": "data_only_row_ready" if all(checks.values()) else "variant_needs_review",
            }
        )

    row_header = ROOT / contract["data_sources"]["row_struct_header"]
    row_header_text = row_header.read_text(encoding="utf-8", errors="ignore") if row_header.is_file() else ""
    row_struct_check = {
        "path": relpath(row_header),
        "exists": row_header.is_file(),
        "enemy_struct": "FMelodiaSlimeEnemyRow" in row_header_text,
        "skill_struct": "FMelodiaSlimeSkillRow" in row_header_text,
        "room_mod_struct": "FMelodiaSlimeRoomModRow" in row_header_text,
        "status": (
            "present"
            if row_header.is_file()
            and all(
                name in row_header_text
                for name in (
                    "FMelodiaSlimeEnemyRow",
                    "FMelodiaSlimeSkillRow",
                    "FMelodiaSlimeRoomModRow",
                )
            )
            else "missing_or_incomplete"
        ),
    }
    imported_assets = {}
    for table_name, table_spec in SLIME_TABLES.items():
        imported_path = ROOT / "Content" / "Melodia" / "DataStuctures" / f"{table_name}.uasset"
        imported_assets[table_name] = {
            "asset_path": table_spec["asset_path"],
            "row_struct": table_spec["row_struct"],
            "expected_row_count": table_spec["expected_count"],
            "path": relpath(imported_path),
            "on_disk": imported_path.is_file(),
            "status": "imported_candidate" if imported_path.is_file() else "not_imported",
        }

    all_static_rows_valid = (
        all(item["status"] == "loaded" for item in source_checks.values())
        and all(item["status"] == "pass" for item in schema_checks)
        and all(item["status"] == "pass" for item in content_checks)
        and all(item["status"] == "data_only_row_ready" for item in variants)
        and row_struct_check["status"] == "present"
    )
    return {
        "contract": relpath(SLIME_CONTRACT_PATH),
        "source_checks": source_checks,
        "row_counts": {table: len(rows) for table, rows in table_rows.items()},
        "schema_checks": schema_checks,
        "content_checks": content_checks,
        "proof_variants": variants,
        "row_struct": row_struct_check,
        "imported_assets": imported_assets,
        "data_only_acceptance": contract["fourth_variant_acceptance"],
        "offline_contract_status": "pass" if all_static_rows_valid else "fail",
        "live_parent_status": "pending",
        "live_battle_presentation_status": "pending",
        "live_datatable_status": (
            "ready_for_live_readback"
            if all(item["on_disk"] for item in imported_assets.values())
            else "source_rows_only"
        ),
        "claim_boundary": "Validated rows do not prove DataTable import, parent/CDO wiring, encounter reference, battle presentation, map placement, or PIE.",
    }


def build_report() -> dict[str, Any]:
    map_contract = load_json(MAP_CONTRACT_PATH)
    slime_contract = load_json(SLIME_CONTRACT_PATH)
    inventory = load_json(INVENTORY_PATH)
    inventory_report = classify_inventory(inventory, map_contract)
    fixture_report = fixture_readiness(map_contract)
    slime_report = slime_contract_check(slime_contract)
    wiring_report = build_wiring_report()
    static_ok = (
        inventory_report["status"] == "classified_before_snapshot"
        and fixture_report["all_contracts_ready"]
        and slime_report["offline_contract_status"] == "pass"
        and wiring_report["static_preconditions"]
        and all(item["status"] == "pass" for item in wiring_report["static_preconditions"])
    )
    return {
        "schema_version": "1.0",
        "kind": "melodia_integration_map_contract_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "offline_only": True,
        "mutations_issued": False,
        "map_contract": relpath(MAP_CONTRACT_PATH),
        "inventory": inventory_report,
        "fixture_readiness": fixture_report,
        "slime_variants": slime_report,
        "wiring_preflight": wiring_report,
        "offline_contract_status": "pass" if static_ok else "fail",
        "live_evidence_available": False,
        "live_proof_status": "pending",
        "summary": {
            "map_kit_items": fixture_report["kit_size"],
            "map_kit_assets_on_disk": fixture_report["assets_on_disk"],
            "legacy_inventory_actors": inventory_report["calculated_total"],
            "legacy_replace_placements": inventory_report["category_totals"].get("replace", 0),
            "slime_enemy_rows": slime_report["row_counts"].get("enemy", 0),
            "slime_skill_rows": slime_report["row_counts"].get("skill", 0),
            "slime_room_mod_rows": slime_report["row_counts"].get("room_mod", 0),
            "slime_proof_variants": len(slime_report["proof_variants"]),
        },
        "live_blockers": map_contract["offline_blockers"],
        "forbidden_claims": map_contract["forbidden_claims"],
    }


def print_text(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print("MelodiaIntegrationMap overhaul contract (offline)")
    print(f"  inventory: {report['inventory']['calculated_total']} actors, "
          f"{report['inventory']['category_totals'].get('replace', 0)} replace-classified placements")
    print(f"  kit assets on disk: {summary['map_kit_assets_on_disk']}/{summary['map_kit_items']}")
    print(f"  slime rows: {summary['slime_enemy_rows']} enemies, "
          f"{summary['slime_skill_rows']} skills, {summary['slime_room_mod_rows']} room mods")
    print(f"  slime proof variants: {summary['slime_proof_variants']}")
    print(f"  offline contract: {report['offline_contract_status']}")
    print("  live evidence: pending (not contacted)")
    print()
    for item in report["fixture_readiness"]["items"]:
        print(f"  {item['id']:<18} {item['offline_status']:<42} "
              f"asset_on_disk={item['asset_on_disk']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return non-zero until live graph/save/mtime/PIE gates are available",
    )
    args = parser.parse_args(argv)
    try:
        report = build_report()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"integration-map contract failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    if report["offline_contract_status"] != "pass":
        return 1
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
