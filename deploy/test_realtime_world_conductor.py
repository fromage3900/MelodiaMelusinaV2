#!/usr/bin/env python3
"""Offline tests for deploy/realtime_world_conductor.py and Config/world_schema.json.

Run:  python deploy/test_realtime_world_conductor.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Content" / "Python"))
sys.path.insert(0, str(ROOT / "deploy"))

CONDUCTOR_PATH = ROOT / "deploy" / "realtime_world_conductor.py"
SCHEMA_PATH = ROOT / "Config" / "world_schema.json"
V1 = ROOT / "deploy" / "fixtures" / "SurrealPlan_Castle_WorldRoot.world.json"
ZEN = ROOT / "deploy" / "fixtures" / "SurrealPlan_ZenShrine_WorldRoot.world.json"
V2 = ROOT / "deploy" / "fixtures" / "surreal_arch_world_v2_sector.world.json"
V2_EAST = ROOT / "deploy" / "fixtures" / "surreal_arch_world_v2_sector_east.world.json"


def _load_conductor():
    spec = importlib.util.spec_from_file_location("realtime_world_conductor", CONDUCTOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


rwc = _load_conductor()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_validate(data: dict) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return rwc.structural_errors(data)
    return [error.message for error in jsonschema.Draft7Validator(schema).iter_errors(data)]


def test_v1_fixture_is_valid():
    errors = _schema_validate(_load(V1))
    assert errors == [], errors
    assert rwc.structural_errors(_load(V1)) == []


def test_v2_fixtures_are_valid():
    for path in (V2, V2_EAST):
        errors = _schema_validate(_load(path))
        assert errors == [], (path.name, errors)


def test_unknown_top_level_field_rejected():
    data = _load(V1)
    data["not_a_real_field"] = True
    errors = _schema_validate(data)
    if "jsonschema" in sys.modules or _schema_has_jsonschema():
        assert errors, "additionalProperties:false must reject unknown keys"
    else:
        # structural checker is v1-required-fields only; unknown keys stay a schema job
        assert rwc.structural_errors(data) == []


def _schema_has_jsonschema() -> bool:
    try:
        import jsonschema  # noqa: F401
        return True
    except ImportError:
        return False


def test_v1_required_fields_still_required():
    data = _load(V1)
    del data["instances"]
    errors = rwc.structural_errors(data)
    assert any("instances" in error for error in errors)


def test_resonant_world_json_is_skipped_not_parsed_as_surreal():
    fake = {
        "format": "melodia_resonant_world_manifest",
        "schema_version": 1,
        "instances": [],
        "instance_count": 0,
        "coordinate_system": "ue_z_up",
    }
    report = rwc.validate_manifest(fake)
    assert report["ok"] is False
    assert any("surreal_arch_world_v1" in error for error in report["structural"])


def test_dirty_groups_then_unchanged(tmp_path: Path | None = None):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        rwc.RECEIPT_PATH = tmp_path / "receipt.json"
        rwc.STATUS_PATH = tmp_path / "status.json"
        rwc.AUDIT = tmp_path
        first = rwc.tick([V1], apply=False)
        assert first["ok"] is True
        assert first["dirty_group_count"] == 3
        assert first["evidence_level"].startswith("SOURCE-TOOL")
        second = rwc.tick([V1], apply=False)
        assert second["dirty_group_count"] == 0
        assert second["unchanged_group_count"] == 3


def test_tile_expansion_and_filtered_dirty_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        rwc.RECEIPT_PATH = tmp_path / "receipt.json"
        rwc.STATUS_PATH = tmp_path / "status.json"
        rwc.AUDIT = tmp_path
        status = rwc.tick([V2], apply=True)
        assert status["ok"] is True
        roots = {row["world_root"] for row in status["scanned"]}
        sectors = {row.get("sector_id") for row in status["scanned"]}
        assert "Shorewake_WorldRoot" in roots
        assert "shorewake.east_01" in sectors
        assert status["dirty_group_count"] >= 2
        apply_hook = status["apply"]
        if isinstance(apply_hook, list):
            statuses = {item.get("status") for item in apply_hook if isinstance(item, dict)}
        else:
            statuses = {apply_hook.get("status")}
        assert "stubbed_offline" in statuses or "stubbed_import_unavailable" in statuses or "import_reported" in statuses
        dirty_files = list(tmp_path.glob("realtime_dirty_*.world.json"))
        assert dirty_files, "conductor must write a filtered dirty manifest"
        filtered = json.loads(dirty_files[0].read_text(encoding="utf-8"))
        assert filtered["format"] == "surreal_arch_world_v1"
        assert filtered["instance_count"] == len(filtered["instances"])
        assert rwc.structural_errors(filtered) == []


def test_use_case_b_checklist_castle_and_zen():
    castle = rwc.use_case_b_checklist(_load(V1))
    assert castle["ok"] is True, castle
    step_ids = [step["id"] for step in castle["steps"]]
    assert step_ids == [
        "format_surreal_arch_world_v1",
        "materials_resolve_role_ue_hints",
        "hism_groups_by_role_lib",
        "instance_counts_match",
    ]
    sacred = next(
        inst["ue_material_hint"]
        for inst in _load(V1)["instances"]
        if inst["role"] == "sacred"
    )
    assert sacred.endswith("MI_Zen_Karesansui")
    zen = rwc.use_case_b_checklist(_load(ZEN))
    assert zen["ok"] is True, zen
    hints = {inst["role"]: inst["ue_material_hint"] for inst in _load(ZEN)["instances"]}
    assert hints["sacred"].endswith("MI_Zen_Karesansui")
    assert hints["gate"].endswith("MI_Zen_ToriiVermillion")
    from surreal_world.role_ue_hints import material_hint

    stone = "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_StoneCliff"
    assert material_hint("WESTERN_CASTLE", "corner_tower") == stone
    assert material_hint("WESTERN_CASTLE", "large") == stone
    assert material_hint("WESTERN_CASTLE", "monument") == stone
    assert material_hint("ZEN_SHRINE", "sacred").endswith("MI_Zen_Karesansui")
    assert "HondenSanctum" not in material_hint("ZEN_SHRINE", "sacred")


def test_importer_apply_is_sma_not_hism():
    src = (ROOT / "Content" / "Python" / "import_world_manifest.py").read_text(encoding="utf-8")
    apply_fn = src.split("def _apply_instance", 1)[1].split("def import_manifest", 1)[0]
    assert "StaticMeshActor" in apply_fn
    assert "apply requires an explicit static_mesh_path" in apply_fn
    assert "HierarchicalInstancedStaticMeshComponent" not in apply_fn
    assert "hism_groups" not in apply_fn


def test_default_manifest_is_castle_surreal_plan():
    assert rwc.DEFAULT_MANIFEST.resolve() == V1.resolve()
    args = rwc.parse_args(["--once"])
    paths = rwc.resolve_manifests(args)
    assert paths == [V1.resolve()]


def test_gmm_v2_sample_still_structurally_valid():
    from gmm.tests.test_pcg_manifest import sample_manifest
    from gmm.pcg.manifest import validate_manifest

    manifest = sample_manifest()
    assert validate_manifest(manifest, require_resolved_meshes=True) == []
    schema_errors = _schema_validate(manifest)
    assert schema_errors == [], schema_errors


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
            except Exception as exc:  # pragma: no cover
                failures += 1
                print(f"ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"\n{'ALL PASS' if not failures else str(failures) + ' FAILED'}")
    raise SystemExit(1 if failures else 0)
