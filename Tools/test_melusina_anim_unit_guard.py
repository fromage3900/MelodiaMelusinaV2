#!/usr/bin/env python3
"""Closed-editor tests for Melusina animation unit / Lane A guards."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
sys.path.insert(0, str(HERE))

import melusina_anim_unit_guard as guard  # noqa: E402


def _assert(cond: bool, message: str) -> None:
    if not cond:
        raise AssertionError(message)


def test_spine_classification() -> None:
    _assert(guard.classify_spine_translation(-12.838751792907715) == "cm", "mocap Y is cm")
    _assert(guard.classify_spine_translation(-0.12838755548000336) == "meters", "raw blender Y is meters")
    _assert(guard.classify_spine_translation(0.0) == "zero", "zero is not a unit class")
    _assert(guard.classify_spine_translation(None) == "unknown", "missing probe")
    _assert(guard.spine_matches_mocap_cm(-12.84), "cm probe should match mocap rest")
    _assert(not guard.spine_matches_mocap_cm(-0.128), "meter probe must not match mocap")


def test_forbidden_quaternius() -> None:
    reasons = guard.forbidden_lane_a_reasons(
        {
            "expected_skeleton": "UAL1_Standard_Skeleton",
            "source_name": "Quaternius Universal Animation Library Standard (CC0)",
            "clip_name": "A_CAS_Melusina_Idle_Loop",
        },
        "A_CAS_Melusina_Idle_Loop.fbx",
    )
    _assert(reasons, "UAL1 sidecar must be rejected")
    _assert(any("Lane A" in item or "expected_skeleton" in item for item in reasons), reasons)

    serene = guard.forbidden_lane_a_reasons(
        {
            "expected_skeleton": "SK_Source_Melusina_Skeleton",
            "source_name": "Cascadeur - Melusina - Idle_Serene",
            "clip_id": "Idle_Serene",
        },
        "A_CAS_Melusina_Idle_Serene.fbx",
    )
    _assert(serene, "Idle_Serene source skeleton is not Lane A")

    lane_a = guard.forbidden_lane_a_reasons(
        {
            "expected_skeleton": guard.TARGET_SKELETON,
            "source_name": "Cascadeur Melusina idle",
            "clip_id": "Idle_Authored",
        },
        "CAS_Melusina_Idle_Authored.fbx",
    )
    _assert(lane_a == [], lane_a)


def test_blender_fbx_headers() -> None:
    raw = PROJECT / "Exports" / "MelusinaAnim" / "A_BL_Melusina_Idle_Loop_raw.fbx"
    remapped = PROJECT / "Exports" / "MelusinaAnim" / "A_BL_Melusina_Idle_Loop.fbx"
    _assert(raw.is_file() and remapped.is_file(), "blender idle FBX pair must be on disk")
    raw_header = guard.classify_fbx_header_units(raw)
    remapped_header = guard.classify_fbx_header_units(remapped)
    _assert(raw_header["header_class"] == "blender_meters", raw_header)
    _assert(remapped_header["header_class"] == "blender_meters_x100_header", remapped_header)
    _assert(not raw_header["safe_for_sk_melusina_without_key_scale"], "raw FBX is not cm-safe")
    _assert(
        not remapped_header["safe_for_sk_melusina_without_key_scale"],
        "remapped header still needs post-import key scale",
    )


def test_dotted_vs_underscore_fbx() -> None:
    raw = PROJECT / "Exports" / "MelusinaAnim" / "A_BL_Melusina_Idle_Loop_raw.fbx"
    remapped = PROJECT / "Exports" / "MelusinaAnim" / "A_BL_Melusina_Idle_Loop.fbx"
    _assert(raw.is_file() and remapped.is_file(), "blender idle FBX pair must be on disk")
    raw_names = guard.scan_fbx_name_style(raw)
    remapped_names = guard.scan_fbx_name_style(remapped)
    _assert(raw_names["name_style"] in {"dotted", "mixed"}, raw_names)
    _assert("c_kilt_master.x" in raw_names["dotted_hits"] or "c_hand_ik.l" in raw_names["dotted_hits"], raw_names)
    _assert(remapped_names["name_style"] == "underscore", remapped_names)
    raw_lane = guard.lane_a_contract_errors(raw)
    _assert(any("dotted" in item or "meter-scale" in item for item in raw_lane), raw_lane)
    remapped_lane = guard.lane_a_contract_errors(remapped)
    _assert(any("meter-scale" in item for item in remapped_lane), remapped_lane)


def test_live_skeleton_preflight() -> None:
    bad = guard.live_skeleton_preflight(["DEF_eye.L", "c_kilt_master.x"])
    _assert(not bad["ok"], bad)
    _assert(bad["ue_import"] is False, bad)
    good = guard.live_skeleton_preflight([f"b{i}" for i in range(465)])
    _assert(good["ok"], good)


def test_inbox_rejects_quaternius() -> None:
    inbox = PROJECT / "Imports" / "Animations" / "Cascadeur" / "Inbox"
    idle = inbox / "A_CAS_Melusina_Idle_Loop.fbx"
    if not idle.is_file():
        print("SKIP test_inbox_rejects_quaternius: Inbox idle FBX missing")
        return
    entry = guard.preflight_fbx(idle, require_sidecar=True, lane_a=True)
    _assert(not entry["ok"], entry)
    _assert(entry["sidecar"], "must discover .manifest.json")
    blob = " ".join(entry["errors"])
    _assert("Lane A" in blob or "expected_skeleton" in blob or "Quaternius" in blob, entry["errors"])


def test_sidecar_discovery() -> None:
    inbox = PROJECT / "Imports" / "Animations" / "Cascadeur" / "Inbox"
    fbx = inbox / "A_CAS_Melusina_Idle_Loop.fbx"
    if not fbx.is_file():
        print("SKIP test_sidecar_discovery: Inbox idle FBX missing")
        return
    sidecar = guard.find_sidecar(fbx)
    _assert(sidecar is not None and sidecar.name.endswith(".manifest.json"), sidecar)


def main() -> int:
    test_spine_classification()
    test_forbidden_quaternius()
    test_blender_fbx_headers()
    test_dotted_vs_underscore_fbx()
    test_live_skeleton_preflight()
    test_inbox_rejects_quaternius()
    test_sidecar_discovery()
    print(json.dumps({"ok": True, "tests": 7}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
