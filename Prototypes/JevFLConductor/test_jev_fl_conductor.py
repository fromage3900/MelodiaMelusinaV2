"""Offline tests for the Jev FL conductor. No FL Studio, no API key.

Run:  python -m pytest Prototypes/JevFLConductor/test_jev_fl_conductor.py -q
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import conductor_bridge as bridge_mod
import jev_fl_conductor as C
from fl_snapshot import EnergyTracker, bar_of


def state(**kw):
    base = dict(bar=5, bars_since_change=4, energy=0.5,
                energy_trend="steady", current_preset="FULL_CHORUS")
    base.update(kw)
    return C.FLPhraseState(**base)


def test_closed_option_set():
    assert set(C.ARRANGE_OPTIONS) == {
        "HOLD", "THIN", "BUILD", "BLOOM", "RESTRAIN",
        "DROP_TO_VOICE", "FULL_CHORUS", "SETTLE",
    }


def test_fallback_is_deterministic_and_labeled():
    s = state()
    d1 = C.FLConductor().evaluate(s, live_enabled=False)
    d2 = C.FLConductor().evaluate(s, live_enabled=False)
    assert d1.source == "classical-fallback"
    assert d1.arrangement.probabilities == d2.arrangement.probabilities
    assert abs(sum(d1.arrangement.probabilities.values()) - 1.0) < 1e-9


def test_unauthored_jev_output_refused(monkeypatch):
    bogus = C.Decision(
        arrangement=C.ArrangementResult("FORTISSIMO", {}, 0.99),
        source="jev-live", reason="x", switched=True,
    )
    monkeypatch.setattr(C, "_jev_ask", lambda s, timeout=30.0: None
                        if bogus.arrangement.choice not in C.ARRANGE_OPTIONS else bogus)
    # _jev_ask returning None must fall back, never surface FORTISSIMO
    d = C.FLConductor().evaluate(state(), live_enabled=True)
    assert d.arrangement.choice in C.ARRANGE_OPTIONS


def test_min_hold_blocks_twitch():
    c = C.FLConductor(initial_preset="HOLD")
    c._last_change_bar = 5
    s = state(bar=6, bars_since_change=1, energy=0.9, energy_trend="rising")
    # force a hot top candidate through the gate directly
    dist = {o: 0.02 for o in C.ARRANGE_OPTIONS}
    dist["FULL_CHORUS"] = 0.80
    choice, switched, _ = c._gate("FULL_CHORUS", dist, 0.5, s)
    assert (choice, switched) == ("HOLD", False)


def test_confidence_gate_can_break_hold():
    c = C.FLConductor(initial_preset="HOLD")
    c._last_change_bar = 5
    s = state(bar=6, bars_since_change=1, energy=0.9, energy_trend="rising")
    dist = {o: 0.005 for o in C.ARRANGE_OPTIONS}
    dist["FULL_CHORUS"] = 0.95
    choice, switched, _ = c._gate("FULL_CHORUS", dist, 0.95, s)
    assert (choice, switched) == ("FULL_CHORUS", True)


def test_settle_safety_near_ending():
    c = C.FLConductor(initial_preset="BUILD")
    c._last_change_bar = 20
    s = state(bar=30, bars_since_change=4, authored_ending=True)
    dist = {o: 0.05 for o in C.ARRANGE_OPTIONS}
    dist["BUILD"] = 0.5
    choice, switched, reason = c._gate("BUILD", dist, 0.4, s)
    assert choice == "SETTLE"
    assert "settle-safety" in reason


def test_hud_shape():
    s = state(bar=9, tempo_bpm=100.0, energy=0.62, energy_trend="rising")
    d = C.FLConductor().evaluate(s, live_enabled=False)
    hud = C.format_hud(s, d, d.arrangement.choice)
    for needle in ("JEV FL CONDUCTOR", "Bar: 9", "Tempo: 100.0",
                   "Energy: 0.62/rising", "Current:", "Jev:",
                   "Alternate:", "Director:", "FALLBACK", "Next:"):
        assert needle in hud


def test_bar_math():
    assert bar_of(0.0) == (1, 0.0)
    assert bar_of(8.0) == (3, 0.0)
    assert bar_of(None) == (1, None)


def test_energy_trend_needs_history():
    e = EnergyTracker()
    level, trend = e.update(0.5)
    assert trend == "unknown"
    for v in (0.5, 0.55, 0.6, 0.65, 0.7, 0.75):
        level, trend = e.update(v)
    assert trend == "rising"
    assert level is not None


def test_cue_validation_refuses_master_and_outsiders():
    cue = json.load(open(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "jev_fl_cue.example.json"), encoding="utf-8"))
    assert bridge_mod.validate_cue(cue) == []
    bad = json.loads(json.dumps(cue))
    bad["presets"]["THIN"]["mute"].append(0)
    assert any("master" in p for p in bridge_mod.validate_cue(bad))
    bad2 = json.loads(json.dumps(cue))
    bad2["presets"]["THIN"]["mute"].append(99)
    assert any("whitelist" in p for p in bridge_mod.validate_cue(bad2))


def test_hold_sends_nothing():
    cue = json.load(open(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "jev_fl_cue.example.json"), encoding="utf-8"))

    class FakeBridge:
        def __init__(self):
            self.sent = []

        def call(self, cmd, params):
            self.sent.append((cmd, params))
            return {"ok": True}

    fb = FakeBridge()
    assert bridge_mod.apply_preset(fb, cue, "HOLD", dry_run=False) == []
    assert fb.sent == []
    # dry-run reports but sends nothing
    cmds = bridge_mod.apply_preset(fb, cue, "THIN", dry_run=True)
    assert len(cmds) > 0 and fb.sent == []
