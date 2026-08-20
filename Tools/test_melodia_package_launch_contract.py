#!/usr/bin/env python3
"""Offline guard for the Chapter 1 montage/package-launch contract.

The package-launch failure was caused by montage segments retaining an old
Quaternius folder/prefix after the clips were re-retargeted.  These checks do
not claim a cook or a packaged launch; they prove that the checked-out montage
packages and the wiring driver agree on the current asset paths before an
editor-owned mutation or cook is attempted.
"""
from __future__ import annotations

import json
from pathlib import Path

from wire_melusina_quaternius_actions import (
    BINDINGS,
    asset_exists_on_disk,
    asset_package_path,
    binding_preflight,
    build_steps,
)


PROJECT = Path(__file__).resolve().parents[1]
OLD_PATH_MARKERS = ("Quaternius_Retargeted", "CAS_Q_Armature")
REQUIRED_REPOINTS = {
    "AM_Melusina_Spell_Shoot": "A_Q_Melusina_Spell_Simple_Shoot",
    "AM_Melusina_Sword_Attack": "A_Q_Melusina_Sword_Attack",
}


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def test_all_bindings_are_current_and_loadable() -> None:
    assert_true(len(BINDINGS) == 10, f"expected 10 action bindings, got {len(BINDINGS)}")
    preflight = binding_preflight()
    assert_true(preflight["missing_montages"] == [], preflight)
    assert_true(preflight["missing_clips"] == [], preflight)
    for montage, clip in BINDINGS:
        assert_true(asset_exists_on_disk(montage), montage)
        assert_true(asset_exists_on_disk(clip), clip)
        assert_true(asset_package_path(montage) is not None, montage)


def test_rerun_does_not_create_existing_montages() -> None:
    steps = build_steps()
    creates = [
        params["asset_path"]
        for tool, action, params in steps
        if tool == "animation_query" and action == "create_montage"
    ]
    assert_true(creates == [], f"current checkout would duplicate existing montages: {creates}")


def test_repointed_packages_contain_no_stale_reference() -> None:
    source = (
        PROJECT / "Tools" / "wire_melusina_quaternius_actions.py"
    ).read_text(encoding="utf-8")
    for marker in OLD_PATH_MARKERS:
        assert_true(marker not in source, f"stale marker remains in driver: {marker}")

    for montage_name, clip_name in REQUIRED_REPOINTS.items():
        montage = (
            PROJECT
            / "Content"
            / "Melodia"
            / "Characters"
            / "Melusina"
            / "Animations"
            / "Montages"
            / f"{montage_name}.uasset"
        )
        text = montage.read_bytes().decode("latin1", errors="ignore")
        for marker in OLD_PATH_MARKERS:
            assert_true(marker not in text, f"{montage_name} retains stale marker {marker}")
        assert_true("QuaterniusRetargeted" in text, montage)
        assert_true(clip_name in text, (montage, clip_name))


def main() -> int:
    test_all_bindings_are_current_and_loadable()
    test_rerun_does_not_create_existing_montages()
    test_repointed_packages_contain_no_stale_reference()
    print(json.dumps({"ok": True, "tests": 3}, indent=2))
    print("validated Melusina package-launch montage contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
