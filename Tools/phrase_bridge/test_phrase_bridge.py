"""A1 finish-line checks: schema validation, OSC encoding, trace byte-stability.

Run: python -m unittest test_phrase_bridge -v   (from Tools/phrase_bridge)
"""

import json
import os
import tempfile
import unittest

import bridge
from osc_min import encode_message
from phrase_schema import (
    PhraseSchemaError,
    PhraseState,
    SectionTag,
    from_json,
    validate_payload,
)


class TestSchema(unittest.TestCase):
    def test_roundtrip(self):
        s = PhraseState(phrase_index=4, section=SectionTag.CLIMAX, bar=10,
                        beat_in_bar=2.0, energy=0.9, confidence=1.0)
        self.assertEqual(from_json(s.to_json()).to_dict(), s.to_dict())

    def test_rejects_unknown_field(self):
        d = PhraseState().to_dict()
        d["bogus"] = 1
        self.assertTrue(validate_payload(d))

    def test_rejects_bad_version(self):
        d = PhraseState().to_dict()
        d["schema_version"] = "melodia.phrase/v2"
        with self.assertRaises(PhraseSchemaError):
            from_json(json.dumps(d))

    def test_rejects_out_of_range(self):
        d = PhraseState().to_dict()
        d["energy"] = 1.5
        self.assertTrue(validate_payload(d))
        d = PhraseState().to_dict()
        d["beat_in_bar"] = 4.5
        self.assertTrue(validate_payload(d))

    def test_rejects_wrong_type_and_bool_int(self):
        d = PhraseState().to_dict()
        d["bar"] = True
        self.assertTrue(validate_payload(d))
        d = PhraseState().to_dict()
        d["boundary_pulse"] = "yes"
        self.assertTrue(validate_payload(d))


class TestOsc(unittest.TestCase):
    def test_encode_int_float_string(self):
        msg = encode_message("/melodia/phrase/state", [1, "VOICE", 4, 0.5])
        self.assertTrue(msg.startswith(b"/melodia/phrase/state\x00"))
        self.assertIn(b",isif\x00", msg[:40])
        self.assertEqual(len(msg) % 4, 0)

    def test_encode_rejects_bad_address(self):
        with self.assertRaises(ValueError):
            encode_message("no-slash", [1])


class TestTraceStability(unittest.TestCase):
    def test_record_is_byte_stable(self):
        with tempfile.TemporaryDirectory() as td:
            p1, p2 = os.path.join(td, "a.jsonl"), os.path.join(td, "b.jsonl")
            bridge.run_emit(6.0, p1, None)
            bridge.run_emit(6.0, p2, None)
            with open(p1, "rb") as f:
                b1 = f.read()
            with open(p2, "rb") as f:
                b2 = f.read()
            self.assertEqual(b1, b2)
            self.assertGreater(len(b1.splitlines()), 50)

    def test_record_validates_and_replays(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "t.jsonl")
            bridge.run_emit(6.0, p, None)
            with open(p, "r", encoding="utf-8") as f:
                for ln in f:
                    rec = json.loads(ln)
                    self.assertEqual(rec["kind"], "state")
                    self.assertEqual(validate_payload(rec["payload"]), [])
            n = bridge.run_replay(p, None, speed=0.0)
            with open(p, "r", encoding="utf-8") as f:
                self.assertEqual(n, len(f.readlines()))

    def test_engine_determinism(self):
        e1, e2 = bridge.PhraseEngine(), bridge.PhraseEngine()
        for i in range(0, 450):
            t = i / 10.0
            self.assertEqual(e1.state_at(t).to_json(), e2.state_at(t).to_json())

    def test_boundary_pulse_held_one_bar(self):
        e = bridge.PhraseEngine()
        pulses = [e.state_at(i / 10.0).boundary_pulse for i in range(0, 60)]  # bars 0-1
        self.assertTrue(pulses[0])
        self.assertTrue(all(pulses[0:30]))   # bar 0, 3 s at 10 Hz
        self.assertTrue(all(pulses[30:60]))  # bar 1 (confidence high at t=3)
        # Rest section (phrase 6, confidence 0.3 from t=42): confidence gates the pulse.
        self.assertFalse(e.state_at(42.5).boundary_pulse)
        self.assertFalse(e.state_at(44.9).boundary_pulse)


if __name__ == "__main__":
    unittest.main()
