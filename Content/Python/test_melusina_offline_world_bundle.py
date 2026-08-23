from __future__ import annotations

import json
from pathlib import Path

from melusina_offline_world_bundle import PROJECT_ROOT, build_offline_world_bundle


MIDI = PROJECT_ROOT / "Content" / "MelodiaIntegration" / "MIDI" / "128BPMarpeggiomelody.mid"
ATLAS = PROJECT_ROOT / "Saved" / "Audit" / "resonant_world_asset_atlas.json"
WARDROBE = PROJECT_ROOT / "Saved" / "Audit" / "resonant_wardrobe_voicing_sakura_3900.json"
PASSAGE = PROJECT_ROOT / "Saved" / "Audit" / "resonant_magic_passage_petal_3900.json"


def test_offline_bundle_is_valid_and_read_only(tmp_path: Path) -> None:
    bundle = build_offline_world_bundle(
        midi_path=MIDI,
        output_dir=tmp_path / "PetalCantata_3900",
        world_seed=3900,
        movement_id="petal_cantata",
        archetype_id="SakuraDreamer",
        radius=1,
        atlas_path=ATLAS,
        wardrobe_path=WARDROBE,
        magic_passage_path=PASSAGE,
    )

    assert bundle["ok"] is True
    assert bundle["world"]["chunk_count"] == 9
    assert bundle["world"]["pcg_hero_volume_count"] == 5
    assert bundle["world"]["pcg_static_spec_count"] == 162
    assert bundle["world"]["score_count"] == 6
    assert bundle["runtime_boundary"]["does_not_call_unreal"] is True
    assert bundle["runtime_boundary"]["does_not_write_gameplay_save"] is True
    assert bundle["ue_import"]["performed"] is False
    assert bundle["ue_import"]["production_maps_touched"] is False

    saved = json.loads((tmp_path / "PetalCantata_3900" / "bundle.json").read_text(encoding="utf-8"))
    assert saved["format"] == "melodia_melusina_offline_world_bundle"
    assert saved["artifacts"]["phrase"]["sha256"]
    assert saved["artifacts"]["score_portfolio"]["sha256"]
    assert saved["artifacts"]["pcg_plan"]["sha256"]


def test_bundle_reports_missing_blender_evidence_without_claiming_success(tmp_path: Path) -> None:
    bundle = build_offline_world_bundle(
        midi_path=MIDI,
        output_dir=tmp_path / "MissingBlender",
        atlas_path=ATLAS,
        wardrobe_path=WARDROBE,
        magic_passage_path=PASSAGE,
        blender_manifest_path=tmp_path / "missing_blender.manifest.json",
    )

    assert bundle["ok"] is False
    assert bundle["blender"]["validated"] is False
    assert bundle["validation_errors"]["blender"]
