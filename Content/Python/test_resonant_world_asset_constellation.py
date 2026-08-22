"""Contract tests for semantic Resonant World asset constellations."""
from __future__ import annotations

from pathlib import Path

from resonant_world_asset_constellation import (
    REQUIRED_ROLES,
    build_asset_constellation,
    build_constellation_portfolio,
    validate_asset_constellation,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_petal_constellation_binds_real_roles_without_runtime_authority() -> None:
    constellation = build_asset_constellation(PROJECT_ROOT, 3900, movement_id="petal_cantata")

    assert validate_asset_constellation(constellation) == []
    assert constellation["coverage"]["required_role_coverage"] == 1.0
    assert all(constellation["coverage"]["role_counts"][role] > 0 for role in REQUIRED_ROLES)
    assert any("SM_Terrain" in item["reference"] for item in constellation["bindings"]["terrain"])
    assert any("SM_Orn_" in item["reference"] or "Piano" in item["reference"] for item in constellation["bindings"]["ornament"])
    assert all("quarantine" not in item["reference"].lower() for refs in constellation["bindings"].values() for item in refs)
    assert all(item["reference"] != "melusina_hair" for item in constellation["bindings"]["water"])
    assert constellation["runtime_boundary"]["does_not_write_save"] is True


def test_constellation_is_seed_and_chunk_stable() -> None:
    first = build_asset_constellation(PROJECT_ROOT, 3900, movement_id="star_loom", chunk_x=2, chunk_y=-1)
    second = build_asset_constellation(PROJECT_ROOT, 3900, movement_id="star_loom", chunk_x=2, chunk_y=-1)
    changed = build_asset_constellation(PROJECT_ROOT, 3900, movement_id="star_loom", chunk_x=3, chunk_y=-1)

    assert first["constellation_id"] == second["constellation_id"]
    assert first["bindings"] == second["bindings"]
    assert first["constellation_id"] != changed["constellation_id"]


def test_portfolio_covers_all_authored_movements() -> None:
    portfolio = build_constellation_portfolio(PROJECT_ROOT, 3900)

    assert portfolio["ok"] is True
    assert portfolio["constellation_count"] == 6
    assert portfolio["validation_errors"] == {}


def test_quantum_setup_is_exactly_two_candidate_selector() -> None:
    constellation = build_asset_constellation(PROJECT_ROOT, 3900, movement_id="dissonant_expanse")
    quantum = constellation["quantum_setup"]
    preview = quantum["rank_preview"]

    assert len(quantum["candidate_movements"]) == 2
    assert quantum["quantum_is_selector_not_generator"] is True
    assert preview["backend_requested"] == "qsharp-simulator"
    assert preview["backend"] in {"qsharp-simulator", "classical-baseline"}
    assert preview["trace_id"]
    assert preview["provenance"]["source_evidence_embedded_in_trace"] is True
    assert all("provenance" in row for row in preview["candidate_scores"])


def test_manifest_only_refs_are_not_claimed_as_runtime_assets() -> None:
    constellation = build_asset_constellation(PROJECT_ROOT, 3900, movement_id="petal_cantata")

    vfx = constellation["bindings"]["vfx"]
    wardrobe = constellation["bindings"]["wardrobe"]
    assert vfx and wardrobe
    assert all(item["source"].endswith("manifest") for item in vfx + wardrobe)
    assert all(item["runtime_ready"] is False for item in vfx + wardrobe)


def test_magical_moment_keeps_appearance_and_ability_separate() -> None:
    constellation = build_asset_constellation(PROJECT_ROOT, 3900, movement_id="liquid_cathedral")
    style = constellation["magical_moment"]["style_layer"]

    assert style["appearance_is_separate_from_capability"] is True
    assert style["capability_declared_by_form"] == "ResonantForm_TidalConduction"
    assert constellation["magical_moment"]["route_is_a_request"] is True
