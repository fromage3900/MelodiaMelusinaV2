"""Authored phrase plan + deterministic clock engine for the Listening Field.

The plan IS the 45-second sequence from
Docs/Production/LISTENING_FIELD_SPEC_2026-09-20.md §5, transcribed into
data. FL Studio is the live source in production; this plan is the trace
authority: what `emit --record` writes and `replay` plays back must be
byte-stable, because the portfolio capture is driven by the trace, not the
network.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from phrase_schema import PhraseState, SectionTag, EnergyTrend

BPM = 80.0
BEATS_PER_BAR = 4.0
TICK_HZ = 10.0
BAR_SECONDS = (60.0 / BPM) * BEATS_PER_BAR  # 3.0 s at 80 BPM, 4/4

BOUNDARY_CONFIDENCE_MIN = 0.5


@dataclass(frozen=True)
class SectionSpan:
    """One authored section of the sequence."""

    start_s: float
    phrase_index: int
    section: SectionTag
    energy_at: callable  # (t_rel_in_section) -> 0..1
    confidence: float


def _lerp(a: float, b: float) -> callable:
    return lambda t: a + (b - a) * t


# 45 s plan. Times match spec §5. Energy is authored directorial intent,
# drawn as simple ramps — the composer redraws these in FL automation later;
# the shapes here are the trace authority for capture.
SECTION_PLAN: list[SectionSpan] = [
    SectionSpan(0.0,  0, SectionTag.SPARSE,  _lerp(0.15, 0.20), 1.0),   # 0:00 sparse piano
    SectionSpan(8.0,  1, SectionTag.VOICE,   _lerp(0.30, 0.45), 1.0),   # 0:08 voice enters
    SectionSpan(15.0, 2, SectionTag.VOICE,   _lerp(0.45, 0.55), 0.9),   # 0:15 sustained, restraint
    SectionSpan(22.0, 3, SectionTag.BUILD,   _lerp(0.55, 0.75), 1.0),   # 0:22 arps layer
    SectionSpan(30.0, 4, SectionTag.CLIMAX,  _lerp(0.80, 1.00), 1.0),   # 0:30 major phrase
    SectionSpan(38.0, 5, SectionTag.RELEASE, _lerp(0.70, 0.30), 0.9),   # 0:38 tail
    SectionSpan(42.0, 6, SectionTag.SPARSE,  _lerp(0.20, 0.10), 0.3),   # 0:42 rest (confidence decays)
]


def section_at(t: float) -> SectionSpan:
    current = SECTION_PLAN[0]
    for span in SECTION_PLAN:
        if t >= span.start_s:
            current = span
        else:
            break
    return current


class PhraseEngine:
    """Deterministic clock. Same t -> same state, always."""

    def __init__(self, bpm: float = BPM, beats_per_bar: float = BEATS_PER_BAR):
        self.bpm = bpm
        self.beats_per_bar = beats_per_bar
        self._prev_energy: float | None = None
        self._bar_at_last_tick = -1
        self._boundary_bar = -1  # bar the current pulse belongs to

    def state_at(self, t: float) -> PhraseState:
        span = section_at(t)
        bar = int(t // BAR_SECONDS)
        beat_in_bar = ((t % BAR_SECONDS) / BAR_SECONDS) * self.beats_per_bar

        energy = max(0.0, min(1.0, span.energy_at(t - span.start_s)))

        if self._prev_energy is None:
            trend = EnergyTrend.FLAT
        else:
            d = energy - self._prev_energy
            trend = EnergyTrend.RISING if d > 1e-4 else EnergyTrend.FALLING if d < -1e-4 else EnergyTrend.FLAT
        self._prev_energy = energy

        # Boundary pulse: bar wrapped AND confidence high enough (rests gate it).
        pulse = False
        if bar != self._bar_at_last_tick:
            self._bar_at_last_tick = bar
            if span.confidence >= BOUNDARY_CONFIDENCE_MIN:
                self._boundary_bar = bar
                pulse = True
        elif self._boundary_bar == bar:
            pulse = True  # held exactly one bar

        return PhraseState(
            phrase_index=span.phrase_index,
            section=span.section,
            bar=bar,
            beat_in_bar=round(beat_in_bar, 3),
            energy=round(energy, 3),
            energy_trend=trend,
            confidence=span.confidence,
            boundary_pulse=pulse,
        )


def run_emit(duration_s: float, record_path: str | None, udp: tuple[str, int] | None) -> int:
    """Run the engine for duration_s at TICK_HZ, optionally recording and/or sending.

    Returns number of ticks emitted. Deterministic: recording happens against
    the engine clock, so the trace is stable across runs and machines.
    """
    from osc_min import OscUdpSender

    engine = PhraseEngine()
    writer = open(record_path, "w", encoding="utf-8", newline="\n") if record_path else None
    sender = OscUdpSender(*udp) if udp else None
    tick = 1.0 / TICK_HZ
    n = 0
    try:
        t = 0.0
        while t < duration_s:
            state = engine.state_at(t)
            if writer:
                writer.write('{"t":%.3f,"kind":"state","payload":%s}\n' % (t, state.to_json()))
            if sender:
                _send_state(sender, state)
                if state.boundary_pulse and state.beat_in_bar < tick:
                    sender.send("/melodia/phrase/boundary", [state.phrase_index, state.bar])
            n += 1
            t = round(t + tick, 3)
    finally:
        if writer:
            writer.close()
        if sender:
            sender.close()
    return n


def _send_state(sender, state: PhraseState) -> None:
    sender.send(
        "/melodia/phrase/state",
        [
            state.phrase_index,
            state.section.value,
            state.bar,
            state.energy,
            state.energy_trend.value,
            state.confidence,
            1 if state.boundary_pulse else 0,
        ],
    )


def run_replay(trace_path: str, udp: tuple[str, int] | None, speed: float = 1.0) -> int:
    """Replay a recorded trace. Payload bytes are re-derived from the JSON, so
    a valid trace replays byte-stable (see selftest). Timing follows the wall
    clock scaled by `speed`; use `--speed 0` to verify without sending.
    """
    from osc_min import OscUdpSender

    n = 0
    with open(trace_path, "r", encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip()]
    sender = OscUdpSender(*udp) if udp else None
    t0_wall = time.perf_counter()
    try:
        for ln in lines:
            t_rel = float(ln.split('"t":', 1)[1].split(",", 1)[0])
            if speed > 0:
                while (time.perf_counter() - t0_wall) * speed < t_rel:
                    time.sleep(0.0005)
            import json as _json
            rec = _json.loads(ln)
            if rec["kind"] == "state":
                from phrase_schema import from_payload
                _send_state(sender, from_payload(rec["payload"])) if sender else None
            n += 1
    finally:
        if sender:
            sender.close()
    return n
