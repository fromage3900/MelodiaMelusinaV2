"""Validate parity between the seven-template BP registry and L1 fixtures."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "specs" / "blueprints" / "melodia_gameplay_bp_kit.v1.json"
FIXTURE_ROOT = ROOT / "specs" / "blueprints" / "fixtures"

EXPECTED_ORDER = [
    "skill",
    "traversal_gate",
    "enemy",
    "encounter",
    "portal",
    "world_challenge",
    "state_anchor",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path}")
    return value


def main() -> int:
    registry = load_json(REGISTRY_PATH)
    templates = registry["templates"]
    assert registry["kind"] == "blueprint_template_registry"
    assert registry["shared_content_contract"] == "specs/blueprints/melodia_content_package.v1.json"
    assert {item["id"] for item in templates} == set(EXPECTED_ORDER)
    assert len(templates) == len(EXPECTED_ORDER)
    assert registry["template_materialization_order"] == EXPECTED_ORDER
    assert len({item["planned_blueprint"] for item in templates}) == len(templates)

    fixture_kinds = {
        "skill": "skill",
        "traversal_gate": "traversal",
        "enemy": "enemy",
        "encounter": "encounter",
        "portal": "portal",
        "world_challenge": "world_challenge",
        "state_anchor": "state_anchor",
    }

    for template in templates:
        template_id = template["id"]
        fixture_path = ROOT / template["fixture_spec"]
        fixture = load_json(fixture_path)
        materialization = template["materialization"]
        blueprint = fixture["blueprint"]
        package = fixture["package"]

        assert fixture["kind"] == "melodia_content_fixture"
        assert fixture["status"] == "contract_spec_only"
        assert fixture["readiness_level"] == "L1"
        assert package["ContentKind"] == fixture_kinds[template_id]
        assert blueprint["parent_template"] == template["planned_blueprint"]
        declared_runtime_authority = materialization.get("runtime_authority")
        if declared_runtime_authority:
            authority_root = declared_runtime_authority.split()[0]
            assert authority_root in blueprint["runtime_authority"], template_id
        else:
            assert blueprint["runtime_authority"]
        assert package["CapabilityGateContract"] == "specs/capability/melodia_capability_gate.v1.json"
        assert materialization["status"]
        assert materialization["materialization_blockers"]

        if template_id == "state_anchor":
            assert materialization["native_parent"] == "/Script/Engine.Actor"
            assert "MelodiaOpeningStateAnchor" not in materialization["native_parent"]
        if template_id in {"world_challenge", "state_anchor"}:
            assert materialization["required_config_allowlist_source"] == (
                "specs/progression/melodia_integration_allowlist_seed.v1.json"
            )

    print("validated BP registry/fixture parity: 7 templates, ordered, authority-safe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
