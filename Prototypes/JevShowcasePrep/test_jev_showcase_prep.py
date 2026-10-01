"""Tests for the Jev showcase-prep conductor.

Authored-only. No network. No API key required. live_enabled=False (or a
patched _try_jev_live) keeps TYPESAFE_API_KEY from ever leaving the process.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import jev_showcase_prep as prep
from jev_showcase_prep import (
    LEVELS,
    NEXT_ACTIONS,
    RENDER_READY_LEVELS,
    ShowcaseState,
    classical_fallback,
    hud,
    level_readiness,
    triage,
)


def _maps(value):
    return {level: value for level in LEVELS}


def _clean(**overrides) -> ShowcaseState:
    base = dict(
        mi_bad_parent_count=_maps(0),
        engine_default_count=_maps(0),
        missing_texture_count=_maps(0),
        last_audit_age_h=_maps(1.0),
        render_proof_exists=_maps(True),
        niagara_default_material_count=0,
        flipbook_authority_ok=True,
        validate_errors=0,
        kawaii_tune_ok=True,
        hair_tick_flags_ok=True,
        blend_verified=True,
        shp_bone_match=True,
        disk_gb_free_c=80.0,
        open_defect=None,
    )
    base.update(overrides)
    return ShowcaseState(**base)


def _assert_no_none(testcase: unittest.TestCase, value) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            testcase.assertIsNotNone(item, key)
            _assert_no_none(testcase, item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            testcase.assertIsNotNone(item)
            _assert_no_none(testcase, item)


class TestShowcasePrep(unittest.TestCase):
    def test_levels_tuple_is_the_six_confirmed_maps(self):
        self.assertEqual(
            LEVELS,
            (
                "/Game/Melodia/Characters/Melusina/Portfolio/L_MelusinaPortfolioCapture",
                "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
                "/Game/EnvSandbox/Environments/L_FallenMoon",
                "/Game/EnvSandbox/Environments/L_KaleidoNave",
                "/Game/ZenForestTest",
                "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype",
            ),
        )
        self.assertEqual(len(LEVELS), 6)

    def test_action_set_closed(self):
        self.assertEqual(
            NEXT_ACTIONS,
            (
                "AUDIT_MATERIAL_INSTANCES",
                "AUDIT_MESH_MAPS",
                "AUDIT_NIAGARA_FLIPBOOK",
                "AUDIT_HAIR_CHAIN",
                "APPLY_FIX",
                "RENDER_PROOF",
                "COOK_TO_G",
                "HOLD_FOR_OWNER",
            ),
        )
        states = (
            ShowcaseState(),
            ShowcaseState(disk_gb_free_c=8),
            _clean(),
            _clean(render_proof_exists=_maps(False)),
            _clean(open_defect="WorldGridMaterial parent", render_proof_exists=_maps(False)),
        )
        for state in states:
            decision = triage(state, live_enabled=False)
            self.assertIn(decision.action, NEXT_ACTIONS)
            self.assertEqual(decision.source, "classical-fallback")
            self.assertEqual(set(decision.action_probs), set(NEXT_ACTIONS))
            self.assertAlmostEqual(sum(decision.action_probs.values()), 1.0, places=2)

    def test_none_dropped_from_jev_state(self):
        state = ShowcaseState(
            mi_bad_parent_count={LEVELS[0]: 2, LEVELS[1]: None},
            engine_default_count=None,
            hair_tick_flags_ok=None,
            disk_gb_free_c=40.0,
        )
        payload = state.to_jev_state()
        self.assertNotIn("engine_default_count", payload)
        self.assertNotIn("hair_tick_flags_ok", payload)
        self.assertNotIn(LEVELS[1], payload["mi_bad_parent_count"])
        self.assertEqual(payload["mi_bad_parent_count"][LEVELS[0]], 2)
        self.assertEqual(payload["disk_gb_free_c"], 40.0)
        _assert_no_none(self, payload)
        self.assertTrue(all(value is not None for value in ShowcaseState().to_jev_state().values()))

    def test_fallback_determinism(self):
        state = ShowcaseState(disk_gb_free_c=80.0, time_budget_min=45.0)
        first = classical_fallback(state)
        second = classical_fallback(state)
        self.assertEqual(first.action, second.action)
        self.assertEqual(first.action_probs, second.action_probs)
        self.assertEqual(first.reason, second.reason)
        self.assertEqual(first.render_ready, second.render_ready)
        self.assertEqual(first.source, "classical-fallback")
        again = triage(state, live_enabled=False)
        self.assertEqual(again.action, first.action)
        self.assertEqual(again.action_probs, first.action_probs)

    def test_unknown_prefers_hair_else_capture_materials(self):
        unknown = triage(ShowcaseState(disk_gb_free_c=80.0), live_enabled=False)
        self.assertEqual(unknown.action, "AUDIT_HAIR_CHAIN")
        known_hair = triage(
            ShowcaseState(
                disk_gb_free_c=80.0,
                hair_tick_flags_ok=True,
                kawaii_tune_ok=True,
            ),
            live_enabled=False,
        )
        self.assertEqual(known_hair.action, "AUDIT_MATERIAL_INSTANCES")
        self.assertIn(LEVELS[0], known_hair.reason)

    def test_cooldown_holds_current_action(self):
        near_tie = prep.TriageDecision(
            action="AUDIT_MATERIAL_INSTANCES",
            action_probs={name: 0.1 for name in NEXT_ACTIONS}
            | {"AUDIT_MATERIAL_INSTANCES": 0.16, "AUDIT_HAIR_CHAIN": 0.14},
            needs_human=False,
            needs_human_prob=0.2,
            render_ready=None,
            render_ready_probs=[0.25, 0.25, 0.25, 0.25],
            source="classical-fallback",
            reason="near tie",
            confidence=0.16,
        )
        real = prep._try_jev_live
        prep._try_jev_live = lambda state: near_tie
        try:
            state = ShowcaseState(
                current_action="AUDIT_HAIR_CHAIN",
                seconds_since_last_action=5.0,
            )
            decision = triage(state, live_enabled=True)
        finally:
            prep._try_jev_live = real
        self.assertEqual(decision.action, "AUDIT_HAIR_CHAIN")
        self.assertIn("cooldown", decision.reason)
        self.assertEqual(decision.source, "classical-fallback")

    def test_cook_only_when_all_levels_l3(self):
        ready = _clean()
        for level in LEVELS:
            self.assertEqual(level_readiness(ready, level), 3)
        cooked = triage(ready, live_enabled=False)
        self.assertEqual(cooked.action, "COOK_TO_G")
        self.assertEqual(cooked.render_ready, 3)

        proofs = _maps(True)
        proofs[LEVELS[1]] = False
        partial = _clean(render_proof_exists=proofs)
        self.assertEqual(level_readiness(partial, LEVELS[1]), 2)
        self.assertNotEqual(triage(partial, live_enabled=False).action, "COOK_TO_G")

        low_disk = triage(_clean(disk_gb_free_c=8), live_enabled=False)
        self.assertEqual(low_disk.action, "HOLD_FOR_OWNER")
        self.assertNotEqual(low_disk.action, "COOK_TO_G")
        self.assertTrue(low_disk.needs_human)

    def test_render_proof_only_at_l2(self):
        proofs = _maps(True)
        proofs[LEVELS[0]] = False
        l2 = _clean(render_proof_exists=proofs, focused_level=LEVELS[0])
        self.assertEqual(level_readiness(l2, LEVELS[0]), 2)
        decision = triage(l2, live_enabled=False)
        self.assertEqual(decision.action, "RENDER_PROOF")
        self.assertEqual(decision.render_ready, 2)
        self.assertEqual(RENDER_READY_LEVELS[2], "L2 clean audits no proof")

        blocking = _clean(
            mi_bad_parent_count=_maps(0) | {LEVELS[0]: 3},
            focused_level=LEVELS[0],
        )
        self.assertEqual(level_readiness(blocking, LEVELS[0]), 0)
        self.assertNotEqual(triage(blocking, live_enabled=False).action, "RENDER_PROOF")
        self.assertNotEqual(triage(ShowcaseState(disk_gb_free_c=80), live_enabled=False).action, "RENDER_PROOF")

    def test_apply_fix_only_with_open_defect(self):
        named = _clean(
            mi_bad_parent_count=_maps(0) | {LEVELS[0]: 2},
            open_defect="WorldGridMaterial parent",
        )
        decision = triage(named, live_enabled=False)
        self.assertEqual(decision.action, "APPLY_FIX")
        self.assertIn("WorldGridMaterial parent", decision.reason)
        self.assertTrue(decision.needs_human)

        unnamed = _clean(mi_bad_parent_count=_maps(0) | {LEVELS[0]: 2}, open_defect=None)
        self.assertNotEqual(triage(unnamed, live_enabled=False).action, "APPLY_FIX")
        blank = _clean(open_defect="   ")
        self.assertNotEqual(triage(blank, live_enabled=False).action, "APPLY_FIX")

    def test_unknown_render_ready_is_not_zero(self):
        decision = triage(ShowcaseState(), live_enabled=False)
        self.assertIsNone(decision.render_ready)
        self.assertIsNone(level_readiness(ShowcaseState(), LEVELS[0]))
        text = hud(decision)
        self.assertIn("unknown", text)
        self.assertNotIn("L0", text)

    def test_hud_contains_source(self):
        decision = triage(ShowcaseState(disk_gb_free_c=80), live_enabled=False)
        text = hud(decision)
        self.assertIn("JEV SHOWCASE PREP", text)
        self.assertIn("Action:", text)
        self.assertIn("Human:", text)
        self.assertIn("Render-ready:", text)
        self.assertIn(decision.source, text)
        self.assertIn(decision.reason, text)
        self.assertIn("classical-fallback", text)

    def test_live_path_not_called_when_disabled(self):
        called = {"n": 0}
        real = prep._try_jev_live

        def _boom(state):
            called["n"] += 1
            raise AssertionError("live path called")

        prep._try_jev_live = _boom
        try:
            decision = triage(ShowcaseState(disk_gb_free_c=80), live_enabled=False)
        finally:
            prep._try_jev_live = real
        self.assertEqual(called["n"], 0)
        self.assertEqual(decision.source, "classical-fallback")
        self.assertEqual(decision.action, "AUDIT_HAIR_CHAIN")

    def test_missing_key_does_not_crash(self):
        saved = os.environ.pop("TYPESAFE_API_KEY", None)
        try:
            decision = triage(ShowcaseState(disk_gb_free_c=80), live_enabled=True)
            text = hud(decision)
        finally:
            if saved is not None:
                os.environ["TYPESAFE_API_KEY"] = saved
        self.assertEqual(decision.source, "classical-fallback")
        self.assertIn(decision.action, NEXT_ACTIONS)
        self.assertNotIn("TYPESAFE_API_KEY", decision.reason)
        self.assertNotIn("TYPESAFE_API_KEY", text)
        if saved:
            self.assertNotIn(saved, decision.reason)
            self.assertNotIn(saved, text)

    def test_service_failure_holds_with_exception_type(self):
        import types

        saved = os.environ.get("TYPESAFE_API_KEY")
        previous = sys.modules.get("typesafe_sdk")
        os.environ["TYPESAFE_API_KEY"] = "unit-test-placeholder"

        fake = types.ModuleType("typesafe_sdk")

        class _Q:
            def __init__(self, *args, **kwargs):
                pass

        class _Client:
            def __init__(self, api_key=None):
                self.api_key = api_key

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def system_one(self, **kwargs):
                raise RuntimeError("service down")

        fake.Choice = _Q
        fake.Noul = _Q
        fake.Score = _Q
        fake.TypeSafeClient = _Client
        sys.modules["typesafe_sdk"] = fake
        try:
            decision = prep._try_jev_live(ShowcaseState())
            text = hud(decision)
        finally:
            if previous is None:
                sys.modules.pop("typesafe_sdk", None)
            else:
                sys.modules["typesafe_sdk"] = previous
            if saved is None:
                os.environ.pop("TYPESAFE_API_KEY", None)
            else:
                os.environ["TYPESAFE_API_KEY"] = saved
        self.assertEqual(decision.action, "HOLD_FOR_OWNER")
        self.assertEqual(decision.source, "classical-fallback")
        self.assertIn("RuntimeError", decision.reason)
        self.assertNotIn("unit-test-placeholder", decision.reason)
        self.assertNotIn("unit-test-placeholder", text)
        if saved:
            self.assertNotIn(saved, decision.reason)
            self.assertNotIn(saved, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
