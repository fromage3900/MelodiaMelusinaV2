from __future__ import annotations

from pathlib import Path

from import_melusina_offline_world import build_import_plan


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUNDLE = PROJECT_ROOT / "Saved" / "Blender" / "MelodiaStudio" / "OfflineWorldGen" / "PetalCantata_3900" / "bundle.json"


def test_bundle_import_plan_is_valid_and_non_mutating() -> None:
    plan = build_import_plan(BUNDLE)

    assert plan["ok"] is True
    assert plan["source_fbx"]["exists"] is True
    assert plan["destination"]["asset_path"] == "/Game/_PROJECT/ResonantWorld/Offline/MelodiaMIDIEnvironment"
    assert plan["destination"]["static_mesh_only"] is True
    assert plan["apply"]["performed"] is False
    assert plan["apply"]["maps_touched"] is False
    assert plan["apply"]["gameplay_save_written"] is False


def test_missing_bundle_cannot_claim_an_import_plan(tmp_path: Path) -> None:
    plan = build_import_plan(tmp_path / "missing_bundle.json")

    assert plan["ok"] is False
    assert plan["errors"]
