#!/usr/bin/env python3
"""Offline contract tests for the Melusina Universal Animation Library."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
PIPELINE = TOOLS / "animation_import_pipeline"
sys.path.insert(0, str(PIPELINE))

from import_chain import TARGET_MESH, _pick_retargeter  # noqa: E402
from melusina_anim_unit_guard import scan_fbx_name_style  # noqa: E402
from manifest_v2 import (  # noqa: E402
    CANONICAL_RIG,
    CANONICAL_SKELETON_PATH,
    RETARGET_PROFILE,
    TARGET_MESH_PATH,
    TARGET_SKELETON_PATH,
    deterministic_clip_id,
    load_as_v2,
    to_v2_manifest,
    validate_v2,
)
from registry import _status_for_path  # noqa: E402
from promotion import build_plan  # noqa: E402
from live_promotion import promote  # noqa: E402


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def valid_manifest() -> dict:
    return to_v2_manifest(
        {
            "clip_name": "A_BL_Source_Idle_Loop",
            "source_name": "Melusina v22 ARP stage idle",
            "source_type": "blender",
            "canonical_rig": CANONICAL_RIG,
            "status": "canonical",
            "fps": 30,
            "units": "cm",
            "frame_start": 0,
            "frame_end": 60,
            "loop": True,
            "root_motion": "in_place",
            "context": "locomotion",
            "consumer": "blendspace",
            "animation_only": True,
            "one_clip_per_file": True,
            "provenance": "v22-stage.blend:Idle",
            "license": "project-authored",
        },
        "Exports/AnimationLibrary/Blender/A_BL_Source_Idle_Loop.fbx",
        status="canonical",
    )


def test_bom_and_legacy_catalogue() -> None:
    with tempfile.TemporaryDirectory() as raw_dir:
        sidecar = Path(raw_dir) / "legacy.manifest.json"
        sidecar.write_text('\ufeff{"schema_version":"1.0","clip_id":"Idle"}', encoding="utf-8")
        manifest, errors, legacy = load_as_v2(sidecar, "Inbox/Idle.fbx")
        assert_true(legacy, "BOM legacy sidecar must be readable")
        assert_true(errors and "legacy" in errors[0], errors)
        assert_true(manifest["status"] in {"legacy", "manual_required", "blocked"}, manifest)


def test_deterministic_id() -> None:
    first = deterministic_clip_id("blender", "v22-stage.blend", "A_BL_Source_Idle_Loop")
    second = deterministic_clip_id("blender", "v22-stage.blend", "A_BL_Source_Idle_Loop")
    assert_true(first == second, (first, second))
    assert_true(re.fullmatch(r"LIB_[A-Z0-9_]+", first) is not None, first)


def test_valid_and_invalid_contracts() -> None:
    manifest = valid_manifest()
    assert_true(validate_v2(manifest) == [], validate_v2(manifest))
    broken = dict(manifest, fps=24, units="m", target_skeleton="/Game/Live")
    errors = validate_v2(broken)
    assert_true(any("fps" in error for error in errors), errors)
    assert_true(any("units" in error for error in errors), errors)
    assert_true(any("target_skeleton" in error for error in errors), errors)


def test_classification_and_no_direct_bypass() -> None:
    status, reasons = _status_for_path(
        Path("Imports/Animations/Cascadeur/Inbox/A_CAS_Melusina_Idle_Loop.fbx"),
        {"source_name": "Quaternius UAL1", "source_type": "quaternius"},
        "quaternius",
    )
    assert_true(status == "manual_required", (status, reasons))
    status, reasons = _status_for_path(
        Path("Exports/MelusinaAnim/A_BL_Melusina_Idle_Loop_raw.fbx"),
        {"source_type": "blender"},
        "blender",
    )
    assert_true(status == "blocked", (status, reasons))
    status, reasons = _status_for_path(
        Path("Exports/MelusinaAnims/A_Melusina_Idle_v22.fbx"),
        {"source_type": "blender"},
        "blender",
    )
    assert_true(status == "manual_required", (status, reasons))
    status, reasons = _status_for_path(
        Path("Exports/AnimationLibrary/Blender/A_BL_Source_Idle_Loop.fbx"),
        {"schema_version": 2, "status": "promoted", "source_type": "blender"},
        "blender",
    )
    assert_true(status == "blocked", (status, reasons))
    assert_true(TARGET_MESH == TARGET_MESH_PATH + ".SK_Melusina", TARGET_MESH)
    assert_true(_pick_retargeter("A_CAS_Melusina_Idle_Loop") == "/Game/Melodia/Characters/Melusina/RTG_Source_to_Melusina.RTG_Source_to_Melusina", "foreign direct retarget bypass")
    direct = dict(valid_manifest(), canonical_skeleton=TARGET_SKELETON_PATH)
    assert_true(any("canonical_skeleton" in error for error in validate_v2(direct)), "live skeleton must not be source rig")


def test_blocked_source_cannot_enter_import_chain() -> None:
    blocked_manifest = TOOLS.parent / "Exports" / "AnimationLibrary" / "Blender" / "A_BL_Source_Idle_Loop.manifest.json"
    blocked_fbx = blocked_manifest.parent / "A_BL_Source_Idle_Loop.fbx"
    result = subprocess.run(
        [sys.executable, str(PIPELINE / "import_chain.py"), str(blocked_fbx), "--manifest", str(blocked_manifest), "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert_true(result.returncode != 0, result.stdout)
    assert_true("not importable" in result.stdout, result.stdout)


def test_owner_normalized_source_ignores_arp_custom_property_names() -> None:
    fbx = TOOLS.parent / "Exports" / "AnimationLibrary" / "Blender" / "A_BL_FinalHandKeyed_Source_20260824.fbx"
    report = scan_fbx_name_style(fbx)
    assert_true(report["name_style"] == "underscore", report)
    assert_true(report["dotted_hits"] == [], report)


def test_promotion_fails_closed() -> None:
    report = build_plan(
        valid_manifest(),
        {"ok": False, "promotion_allowed": False, "promotion_blockers": ["UE:pending"]},
        animation="/Game/Melodia/Characters/Melusina/Animations/SourceRetargeted/A_BL_Source_Idle_Loop__MUAL_TARGET",
        consumer="blendspace",
        speed=0.0,
    )
    assert_true(not report["promotion_allowed"], report)
    assert_true(any("UE:" in item for item in report["blockers"]), report)
    assert_true(any("speed" in item for item in report["errors"]), report)


def test_contact_audit_metadata_is_preserved() -> None:
    manifest = valid_manifest()
    assert_true(
        manifest["foot_contact_audit"] == {"status": "pending_manual", "required_for_promotion": True},
        manifest,
    )
    passed = to_v2_manifest(
        dict(manifest, foot_contact_audit={"status": "passed", "required_for_promotion": True}),
        "Exports/AnimationLibrary/Blender/A_BL_Source_Idle_Loop.fbx",
        status="canonical",
    )
    assert_true(passed["foot_contact_audit"]["status"] == "passed", passed)


def test_measured_speed_evidence_is_required_and_reusable() -> None:
    manifest = valid_manifest()
    ue = {
        "ok": False,
        "promotion_allowed": False,
        "promotion_blockers": ["pending"],
        "measured_speed": {"verified": True, "speed_cm_s": 123.0},
    }
    plan = build_plan(
        manifest,
        ue,
        animation="/Game/Staging/A_Source__MUAL_TARGET",
        consumer="blendspace",
    )
    assert_true(plan["measured_speed"] == 123.0, plan)
    assert_true(plan["measured_speed_source"] == "ue_report", plan)


def test_montage_accepts_explicit_in_place_policy() -> None:
    manifest = valid_manifest()
    ue = {"ok": True, "promotion_allowed": True}
    plan = build_plan(
        manifest,
        ue,
        animation="/Game/Staging/A_Source__MUAL_TARGET",
        consumer="montage",
        montage_target="/Game/Melodia/Characters/Melusina/Animations/Montages/AM_MUAL_Source_Idle",
    )
    assert_true("montage promotion requires explicit root-motion policy" not in plan["errors"], plan)
    assert_true(plan["promotion_allowed"] is False, "contact evidence must still gate promotion")


def test_static_contact_scope_unlocks_montage_only() -> None:
    manifest = valid_manifest()
    manifest["foot_contact_audit"] = {
        "status": "passed",
        "required_for_promotion": True,
        "audited_consumer": "montage",
        "mode": "static_pose",
    }
    ue = {
        "ok": True,
        "staging_ok": True,
        "promotion_allowed": False,
        "promotion_blockers": ["measured_speed", "foot_contact_audit"],
    }
    montage = build_plan(
        manifest,
        ue,
        animation="/Game/Staging/A_Source__MUAL_TARGET",
        consumer="montage",
        montage_target="/Game/Montages/AM_MUAL_Source_Idle",
    )
    assert_true(montage["promotion_allowed"] is True, montage)
    blendspace = build_plan(
        manifest,
        ue,
        animation="/Game/Staging/A_Source__MUAL_TARGET",
        consumer="blendspace",
        speed=123.0,
    )
    assert_true(blendspace["promotion_allowed"] is False, blendspace)
    assert_true(any("scoped to montage" in item for item in blendspace["blockers"]), blendspace)


def test_static_idle_can_replace_speed_zero_sample() -> None:
    manifest = valid_manifest()
    manifest["speed_evidence"] = {
        "mode": "static_pose",
        "status": "declared",
        "speed_cm_s": 0.0,
    }
    manifest["foot_contact_audit"] = {
        "status": "passed",
        "required_for_promotion": True,
        "audited_consumer": "blendspace",
        "mode": "static_pose",
    }
    ue = {
        "ok": True,
        "staging_ok": True,
        "promotion_allowed": True,
        "promotion_blockers": [],
        "measured_speed": {"verified": True, "speed_cm_s": 0.0},
    }
    plan = build_plan(
        manifest,
        ue,
        animation="/Game/Staging/A_Source__MUAL_TARGET",
        consumer="blendspace",
        speed=0.0,
        replace_existing_speed=True,
    )
    assert_true(plan["promotion_allowed"] is True, plan)
    assert_true(plan.get("replacement_samples"), plan)


def test_live_promotion_never_bypasses_failed_gates() -> None:
    with tempfile.TemporaryDirectory() as raw_dir:
        root = Path(raw_dir)
        manifest_path = root / "clip.manifest.json"
        ue_path = root / "ue.json"
        plan_path = root / "plan.json"
        output_path = root / "out.json"
        manifest_path.write_text(json.dumps(valid_manifest()), encoding="utf-8")
        ue_path.write_text(json.dumps({"ok": False, "promotion_allowed": False}), encoding="utf-8")
        plan_path.write_text(json.dumps({"promotion_allowed": False}), encoding="utf-8")
        code = promote(
            manifest_path,
            ue_path,
            plan_path,
            apply=True,
            output=output_path,
            animation="/Game/Staging/A_Source__MUAL_TARGET",
            consumer="blendspace",
            speed=123.0,
        )
        assert_true(code != 0, code)
        report = json.loads(output_path.read_text(encoding="utf-8"))
        assert_true(report["promotion_allowed"] is False, report)


def test_live_promotion_rejects_mismatched_passed_plan() -> None:
    with tempfile.TemporaryDirectory() as raw_dir:
        root = Path(raw_dir)
        manifest_path = root / "clip.manifest.json"
        ue_path = root / "ue.json"
        plan_path = root / "plan.json"
        output_path = root / "out.json"
        manifest = valid_manifest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        ue_path.write_text(json.dumps({"ok": True, "promotion_allowed": True}), encoding="utf-8")
        plan_path.write_text(json.dumps({
            "promotion_allowed": True,
            "manifest_clip_id": "LIB_DIFFERENT",
            "consumer": "montage",
            "animation": "/Game/Staging/Other",
            "montage_target": "/Game/Staging/OtherMontage",
        }), encoding="utf-8")
        code = promote(
            manifest_path,
            ue_path,
            plan_path,
            apply=True,
            output=output_path,
            animation="/Game/Staging/A_Source__MUAL_TARGET",
            consumer="montage",
            montage_target="/Game/Staging/OtherMontage",
        )
        assert_true(code != 0, code)
        report = json.loads(output_path.read_text(encoding="utf-8"))
        assert_true(report["promotion_allowed"] is False, report)


def main() -> int:
    test_bom_and_legacy_catalogue()
    test_deterministic_id()
    test_valid_and_invalid_contracts()
    test_classification_and_no_direct_bypass()
    test_blocked_source_cannot_enter_import_chain()
    test_owner_normalized_source_ignores_arp_custom_property_names()
    test_promotion_fails_closed()
    test_contact_audit_metadata_is_preserved()
    test_measured_speed_evidence_is_required_and_reusable()
    test_montage_accepts_explicit_in_place_policy()
    test_static_contact_scope_unlocks_montage_only()
    test_static_idle_can_replace_speed_zero_sample()
    test_live_promotion_never_bypasses_failed_gates()
    test_live_promotion_rejects_mismatched_passed_plan()
    print(json.dumps({"ok": True, "tests": 15}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
