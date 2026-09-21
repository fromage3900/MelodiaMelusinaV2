import json
import sys
from pathlib import Path

PIPELINE = Path(__file__).resolve().parent / "animation_import_pipeline"
sys.path.insert(0, str(PIPELINE))

from presentation_gate import DEFAULT_CONTRACT, validate_probe, validate_reference_evidence  # noqa: E402
from promotion import build_plan  # noqa: E402


def _contract():
    return json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))


def _passing_probe():
    contract = _contract()
    return {
        "target": contract["target"],
        "shoulders": {
            "controller_tracks_static_at_reference": True,
            "deform_tracks_animated": True,
            "normalization_applied": True,
            "visual_review_passed": True,
            "capture_only_reference_promoted": False,
        },
        "montage": {"duration_seconds": 1.3},
        "bow": contract["bow"],
        "harp_to_bow": {
            "implementation": "static_mesh_visibility_swap",
            "continuous_morph_claimed": False,
        },
    }


def test_reference_evidence_matches_canonical_contract():
    report = validate_reference_evidence(_contract())
    assert report["ok"] is True
    assert report["promotion_allowed"] is False


def test_production_probe_passes_only_with_reviewed_normalization():
    assert validate_probe(_passing_probe(), _contract())["promotion_allowed"] is True


def test_hiked_shoulders_fail_closed():
    probe = _passing_probe()
    probe["shoulders"]["normalization_applied"] = False
    report = validate_probe(probe, _contract())
    assert report["ok"] is False
    assert any("requires normalization" in error for error in report["errors"])


def test_backwards_bow_and_morph_claim_fail_closed():
    probe = _passing_probe()
    probe["bow"]["draw_world_rotation_pitch_yaw_roll"] = [0.0, 0.0, 90.0]
    probe["harp_to_bow"]["continuous_morph_claimed"] = True
    report = validate_probe(probe, _contract())
    assert report["ok"] is False
    assert len(report["errors"]) == 2


def test_zero_duration_montage_fails_closed():
    probe = _passing_probe()
    probe["montage"]["duration_seconds"] = 0
    assert validate_probe(probe, _contract())["promotion_allowed"] is False


def test_bow_profile_cannot_bypass_presentation_gate():
    manifest = {
        "status": "canonical",
        "target_skeleton": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton",
        "target_mesh": "/Game/Melodia/Characters/Melusina/SK_Melusina",
        "root_motion": "in_place",
        "clip_id": "LIB_TEST_BOW",
        "foot_contact_audit": {"status": "passed", "audited_consumer": "montage"},
        "presentation_profile": "melusina_bow_v1",
    }
    report = build_plan(
        manifest,
        {"ok": True, "staging_ok": True},
        animation="/Game/Staging/A_Bow",
        consumer="montage",
        montage_target="/Game/Staging/AM_Bow",
    )
    assert report["promotion_allowed"] is False
    assert any("presentation gate" in blocker for blocker in report["blockers"])
