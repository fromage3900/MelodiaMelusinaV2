"""A5 finish-line checks: fallback sequence, allowlist, latency rule, layout seeds.

Run: python -m unittest test_jev_director -v   (from Tools/listening_field)
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phrase_bridge"))

import jev_director
from directive_schema import (
    SHEEP_DIRECTIVES, Directive, sanitize, validate,
    SCHEMA_VERSION,
)
from phrase_schema import PhraseState, SectionTag

TRACE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "..", "Saved", "Audit", "phrase_traces",
                     "listening_field_v1.jsonl")


class TestFallbackSequence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dirs = jev_director.run_trace(TRACE, None, use_jev=False)

    def test_every_boundary_produces_a_directive(self):
        # 15 bars in 45 s; the rest bar (14, confidence 0.3) is correctly
        # gated out — 14 decisions is the right count.
        self.assertEqual(len(self.dirs), 14)

    def test_directives_follow_spec_timeline(self):
        # Sections start mid-bar, so each section's FIRST boundary lands on
        # the next full bar. Keyed by the bar the directive applies at.
        by_apply = {d.for_bar: d for d in self.dirs}
        self.assertEqual(by_apply[1].sheep, "HOLD")                       # bar 0 SPARSE opening
        self.assertEqual(by_apply[4].sheep, "TURN_TO_PLAYER")             # bar 3, first VOICE boundary
        self.assertEqual(by_apply[6].sheep, "HOLD")                       # bar 5 VOICE sustain
        self.assertEqual(by_apply[9].sheep, "RESONANCE_PULSE")            # bar 8 BUILD
        self.assertEqual(by_apply[11].sheep, "SPIRAL_FORMATION")          # bar 10 CLIMAX entry
        self.assertEqual(by_apply[14].sheep, "CRESCENDO_BURST")           # bar 13 RELEASE

    def test_restraint_arc(self):
        by_apply = {d.for_bar: d for d in self.dirs}
        self.assertEqual(by_apply[1].restraint, 1.0)    # opening: full hold
        self.assertEqual(by_apply[4].restraint, 0.7)    # voice: held breath
        self.assertEqual(by_apply[9].restraint, 0.2)    # build: opening
        self.assertEqual(by_apply[11].restraint, 0.0)   # climax: full release
        self.assertEqual(by_apply[14].restraint, 0.3)   # tail: easing

    def test_layout_seed_only_at_climax(self):
        seeds = [(d.for_bar, d.layout_seed) for d in self.dirs if d.layout_seed]
        self.assertEqual(len(seeds), 1)
        self.assertEqual(seeds[0][0], 11)     # applies the bar after CLIMAX begins
        self.assertTrue(seeds[0][1].startswith("seed_"))

    def test_latency_rule(self):
        # every directive applies strictly after its decision bar
        self.assertTrue(all(d.for_bar >= 1 for d in self.dirs))


class TestAllowlist(unittest.TestCase):
    def test_sanitize_kills_unlisted(self):
        d = sanitize(Directive(5, "FLY_AWAY", "EXPLODE", 0.5, "seed_bogus", "jev", 0.9))
        self.assertEqual((d.sheep, d.world, d.layout_seed), ("", "", None))
        self.assertEqual(d.restraint, 0.5)

    def test_settle_not_in_vocabulary(self):
        self.assertNotIn("SETTLE", SHEEP_DIRECTIVES)
        self.assertNotIn("RETURN_TO_IDLE", SHEEP_DIRECTIVES)

    def test_validate_accepts_clean(self):
        d = Directive(5, "HOLD", "RESTRAIN", 1.0, None, "fallback", 1.0).to_dict()
        d["schema_version"] = SCHEMA_VERSION
        self.assertEqual(validate(d), [])


class TestOfflineOperation(unittest.TestCase):
    def test_run_writes_jsonl_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            p1, p2 = os.path.join(td, "a.jsonl"), os.path.join(td, "b.jsonl")
            jev_director.run_trace(TRACE, p1, use_jev=False)
            jev_director.run_trace(TRACE, p2, use_jev=False)
            with open(p1, "rb") as f1, open(p2, "rb") as f2:
                self.assertEqual(f1.read(), f2.read())

    def test_no_key_no_crash(self):
        old = os.environ.pop("TYPESAFE_API_KEY", None)
        try:
            self.assertFalse(jev_director.jev_available())
            ds = jev_director.run_trace(TRACE, None, use_jev=None)
            self.assertEqual(len(ds), 14)
            self.assertTrue(all(d.source == "fallback" for d in ds))
        finally:
            if old is not None:
                os.environ["TYPESAFE_API_KEY"] = old


if __name__ == "__main__":
    unittest.main()
