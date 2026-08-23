from __future__ import annotations

import json
from pathlib import Path

from import_melusina_offline_world import build_import_plan


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUNDLE = PROJECT_ROOT / "Content" / "MelodiaIntegration" / "ResonantWorld" / "OfflineWorldGen" / "PetalCantata_3900" / "bundle.json"


def test_bundle_import_plan_is_valid_and_non_mutating() -> None:
    plan = build_import_plan(BUNDLE)

    assert plan["ok"] is True
    assert plan["source_fbx"]["exists"] is True
    assert plan["destination"]["asset_path"] == "/Game/_PROJECT/ResonantWorld/Offline/MelodiaMIDIEnvironment"
    assert plan["destination"]["static_mesh_only"] is True
    assert plan["apply"]["performed"] is False
    assert plan["apply"]["maps_touched"] is False
    assert plan["apply"]["gameplay_save_written"] is False

    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    assert bundle["artifacts"]["blender_obj"]["exists"] is True
    assert bundle["artifacts"]["blender_obj"]["project_relative_path"].startswith(
        "Content/MelodiaIntegration/ResonantWorld/OfflineWorldGen/"
    )


def test_missing_bundle_cannot_claim_an_import_plan(tmp_path: Path) -> None:
    plan = build_import_plan(tmp_path / "missing_bundle.json")

    assert plan["ok"] is False
    assert plan["errors"]


def test_import_plan_falls_back_to_project_relative_fbx_path(tmp_path: Path) -> None:
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    bundle["artifacts"]["blender_fbx"]["path"] = r"Z:\missing\MelodiaMIDIEnvironment.fbx"
    relocated_bundle = tmp_path / "bundle.json"
    relocated_bundle.write_text(json.dumps(bundle), encoding="utf-8")

    plan = build_import_plan(relocated_bundle)

    assert plan["ok"] is True
    assert plan["source_fbx"]["path"].endswith(
        "Content\\MelodiaIntegration\\ResonantWorld\\OfflineWorldGen\\PetalCantata_3900\\MelodiaMIDIEnvironment.fbx"
    )
