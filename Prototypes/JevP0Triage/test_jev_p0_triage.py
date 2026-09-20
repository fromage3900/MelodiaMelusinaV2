"""Tests for the Jev P0 triage conductor. No key, no editor, no network."""

import unittest

from jev_p0_triage import (
    CAPTURE_READY_LEVELS,
    NEXT_ACTIONS,
    P0State,
    classical_fallback,
    hud,
    triage,
)


class TestTriage(unittest.TestCase):
    def test_action_always_authored(self):
        for kwargs in (
            {"editor_up": False},
            {"editor_up": True, "disk_gb_free_c": 8},
            {"editor_up": True, "gate_staleness_days": 30, "time_budget_min": 60},
            {},
        ):
            d = triage(P0State(**kwargs), live_enabled=False)
            self.assertIn(d.action, NEXT_ACTIONS)
            self.assertEqual(d.source, "classical-fallback")

    def test_editor_down_runs_headless(self):
        d = triage(P0State(editor_up=False), live_enabled=False)
        self.assertEqual(d.action, "RUN_HEADLESS_SUITE")

    def test_low_disk_holds_for_owner(self):
        d = triage(P0State(editor_up=True, disk_gb_free_c=8), live_enabled=False)
        self.assertEqual(d.action, "HOLD_FOR_OWNER")
        self.assertTrue(d.needs_human)

    def test_stale_gates_prefers_pie_smoke(self):
        d = triage(
            P0State(editor_up=True, gate_staleness_days=30, time_budget_min=60),
            live_enabled=False,
        )
        self.assertEqual(d.action, "RUN_PIE_SMOKE")

    def test_probs_cover_authored_set(self):
        d = triage(P0State(), live_enabled=False)
        self.assertEqual(set(d.action_probs), set(NEXT_ACTIONS))
        self.assertAlmostEqual(sum(d.action_probs.values()), 1.0, places=2)

    def test_capture_levels_sane(self):
        d = triage(P0State(), live_enabled=False)
        self.assertGreaterEqual(d.capture_score, 0)
        self.assertLess(d.capture_score, len(CAPTURE_READY_LEVELS))

    def test_cooldown_holds(self):
        # High-margin switch wins even inside the hold window (confidence gate).
        s = P0State(
            editor_up=True, gate_staleness_days=30, time_budget_min=60,
            current_action="RUN_HEADLESS_SUITE", seconds_since_last_action=5.0,
        )
        d = triage(s, live_enabled=False)
        self.assertEqual(d.action, "RUN_PIE_SMOKE")

    def test_cooldown_holds_near_tie(self):
        # Near-tie top vs current inside the hold window stays put.
        import jev_p0_triage as m

        near_tie = m.TriageDecision(
            action="RUN_PIE_SMOKE",
            action_probs={a: 0.2 for a in m.NEXT_ACTIONS} | {"RUN_PIE_SMOKE": 0.22},
            needs_human=False, needs_human_prob=0.2,
            capture_score=1, capture_probs=[0.1, 0.6, 0.2, 0.1],
            source="classical-fallback", reason="near tie",
            confidence=0.22,
        )
        real = m._try_jev_live
        m._try_jev_live = lambda state: near_tie
        try:
            s = P0State(
                current_action="RUN_HEADLESS_SUITE", seconds_since_last_action=5.0,
            )
            d = triage(s, live_enabled=True)
        finally:
            m._try_jev_live = real
        self.assertEqual(d.action, "RUN_HEADLESS_SUITE")
        self.assertIn("cooldown", d.reason)

    def test_determinism(self):
        s = P0State(editor_up=True, gate_staleness_days=30, time_budget_min=60)
        a = triage(s, live_enabled=False)
        b = triage(s, live_enabled=False)
        self.assertEqual(a.action, b.action)
        self.assertEqual(a.action_probs, b.action_probs)

    def test_hud_format(self):
        d = triage(P0State(), live_enabled=False)
        h = hud(d)
        self.assertIn("JEV P0 TRIAGE", h)
        self.assertIn("Action:", h)
        self.assertIn(d.source, h)


if __name__ == "__main__":
    unittest.main(verbosity=2)
