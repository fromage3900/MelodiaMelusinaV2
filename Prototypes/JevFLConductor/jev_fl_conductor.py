"""Jev-driven FL Studio phrase conductor — isolated prototype.

ISOLATION CONTRACT (read before touching):
- Everything lives in Prototypes/JevFLConductor/. Delete this folder to
  remove the experiment. Nothing here imports Melodia game modules.
- Jev selects ONLY among 8 authored arrangement responses. It never
  composes notes, rewrites the project, inserts/deletes plugins, moves
  clips, saves anything, or sets arbitrary mixer values. Execution of a
  selection is a deterministic, human-authored preset applied by
  conductor_bridge.py through mixer mutes on whitelisted stem tracks only.
- Telemetry honesty: state fields set to None stay missing — they are
  dropped from the Jev state, never zero-filled. Provenance on every
  Decision: source="jev-live" or source="classical-fallback" plus reason.
  Fallback exists so the loop runs before TYPESAFE_API_KEY is configured;
  it is NOT Jev evidence.
- TYPESAFE_API_KEY lives in the environment of the bridge process ONLY.
  It must never appear in FL scripts, .flp files, MIDI, logs, or git.

Skill: typesafe-ai. One narrow Choice question over named JSON state;
code owns workflow, hysteresis, and execution. Full probability
distributions are preserved on every Decision.
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

ARRANGE_OPTIONS = (
    "HOLD",
    "THIN",
    "BUILD",
    "BLOOM",
    "RESTRAIN",
    "DROP_TO_VOICE",
    "FULL_CHORUS",
    "SETTLE",
)

ARRANGE_INSTRUCTIONS = (
    "Given the current musical phrase state, what should the NEXT "
    "authored phrase do? Choose exactly one of the defined arrangement "
    "responses. Never invent a response outside the criteria."
)

ARRANGE_CRITERIA: dict[str, Any] = {
    "HOLD": {
        "what": "No change; the current arrangement state continues.",
        "when": "The phrase is working and nothing asks for motion.",
        "not_for": "Moments that clearly want thinning, building, or rest.",
    },
    "THIN": {
        "what": "Reduce to the predefined sparse combination.",
        "when": "Texture is crowding the voice, or a breath is needed.",
        "not_for": "Climaxes, or when the groove alone carries the phrase.",
    },
    "BUILD": {
        "what": "Enable the next authored layer.",
        "when": "Energy is rising and the phrase wants forward motion.",
        "not_for": "The peak itself, or fragile quiet passages.",
    },
    "BLOOM": {
        "what": "Open the predefined atmosphere/resonance combination.",
        "when": "The phrase wants width and shimmer around a steady core.",
        "not_for": "Dense rhythmic peaks; bloom needs air to read.",
    },
    "RESTRAIN": {
        "what": "Maintain tension instead of taking the obvious peak.",
        "when": "Everything points up but the music is better for waiting.",
        "not_for": "Release moments the arrangement has already earned.",
    },
    "DROP_TO_VOICE": {
        "what": "Use the authored voice-led state.",
        "when": "The voice should carry alone or nearly alone.",
        "not_for": "Instrumental passages with no vocal lead present.",
    },
    "FULL_CHORUS": {
        "what": "Enable the predefined full arrangement state.",
        "when": "The peak has been earned and should land completely.",
        "not_for": "Anything before the rise has done its work.",
    },
    "SETTLE": {
        "what": "Return to the authored resolution state.",
        "when": "Near an authored ending, or when the cue must come home.",
        "not_for": "Mid-cue rises; settling early deflates the arc.",
    },
}

# Hysteresis: phrases, not frames. Values mirror the sheep conductor.
MIN_HOLD_BARS = 2
SWITCH_MARGIN = 0.08  # top_prob must clear current_prob by this (or conf gate)
CONF_SWITCH_GATE = 0.80  # high-confidence top may switch even under margin
SETTLE_CONF = 0.60  # below this near an authored ending: deterministic SETTLE


@dataclass
class FLPhraseState:
    """One phrase-boundary observation. 0.0..1.0 unless noted.

    None = unknown / unavailable. to_jev_state() drops Nones so missing
    data reads as missing, never as zero.
    """

    tempo_bpm: Optional[float] = None
    bar: int = 1
    beat_in_bar: Optional[float] = None
    playing: bool = True
    master_peak: Optional[float] = None
    energy: Optional[float] = None  # smoothed 0..1
    energy_trend: str = "unknown"  # rising | falling | steady | unknown
    stem_peaks: dict[str, Optional[float]] = field(default_factory=dict)
    group_active: dict[str, bool] = field(default_factory=dict)
    current_preset: str = "FULL_CHORUS"
    previous_decision: str = "HOLD"
    bars_since_change: int = 0
    authored_section: Optional[str] = None  # bridge-side, if available
    authored_ending: bool = False  # True when the cue is near its ending
    provenance: str = "fl-live"  # fl-live | scripted

    def to_jev_state(self) -> dict[str, Any]:
        raw: dict[str, Any] = {
            "tempo_bpm": self.tempo_bpm,
            "bar": self.bar,
            "beat_in_bar": self.beat_in_bar,
            "playing": self.playing,
            "master_peak": self.master_peak,
            "energy": self.energy,
            "energy_trend": self.energy_trend,
            "stem_peaks": {
                k: v for k, v in self.stem_peaks.items() if v is not None
            } or None,
            "group_active": self.group_active or None,
            "current_preset": self.current_preset,
            "previous_decision": self.previous_decision,
            "bars_since_change": self.bars_since_change,
            "authored_section": self.authored_section,
            "authored_ending": self.authored_ending,
        }
        return {k: v for k, v in raw.items() if v is not None}


@dataclass
class ArrangementResult:
    choice: str
    probabilities: dict[str, float]
    confidence: float
    alternates: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class Decision:
    arrangement: ArrangementResult
    source: str  # jev-live | classical-fallback
    reason: str
    switched: bool


def _norm_dist(raw: dict[str, float], options: tuple[str, ...]) -> dict[str, float]:
    full = {o: max(0.0, float(raw.get(o, 0.0))) for o in options}
    total = sum(full.values())
    if total <= 0.0:
        n = len(options)
        return {o: 1.0 / n for o in options}
    return {o: v / total for o, v in full.items()}


def _with_alternates(choice: str, dist: dict[str, float]) -> list[tuple[str, float]]:
    return sorted(
        ((o, p) for o, p in dist.items() if o != choice),
        key=lambda kv: kv[1],
        reverse=True,
    )


# ---------------------------------------------------------------- fallback
def _fallback_scores(s: FLPhraseState) -> dict[str, float]:
    """Deterministic classical heuristic. Documents the sanity-check
    mapping as code so the loop runs with no backend. NOT Jev evidence."""
    f = {o: 0.05 for o in ARRANGE_OPTIONS}
    energy = s.energy if s.energy is not None else 0.3
    trend = s.energy_trend
    calm = energy < 0.3
    hot = energy >= 0.7

    f["HOLD"] += 0.7 if 0.3 <= energy < 0.6 and trend == "steady" else 0.1
    if calm:
        f["THIN"] += 0.7
        f["DROP_TO_VOICE"] += 0.5
    if trend == "rising" and not hot:
        f["BUILD"] += 0.9
    if trend == "rising" and 0.4 <= energy < 0.7:
        f["RESTRAIN"] += 0.5  # wait before the obvious peak
    if 0.4 <= energy < 0.7 and trend in ("steady", "rising"):
        f["BLOOM"] += 0.6
    if hot and trend == "rising":
        f["FULL_CHORUS"] += 1.1
    if s.authored_ending:
        f["SETTLE"] += 1.2
    elif s.bars_since_change >= 8 and calm:
        f["SETTLE"] += 0.5
    return f


def _softmax(scores: dict[str, float], temp: float = 0.4) -> dict[str, float]:
    """Sharpened so a clear winner reads as one. Display choice for the
    fallback only; Jev-live distributions pass through untouched."""
    m = max(scores.values())
    exps = {k: math.exp((v - m) / temp) for k, v in scores.items()}
    total = sum(exps.values())
    return {k: v / total for k, v in exps.items()}


# ---------------------------------------------------------------- Jev live
def _jev_ask(state: FLPhraseState, timeout: float = 30.0) -> Optional[Decision]:
    """One system_one call, one Choice question. Returns None when the
    backend is unavailable (no key / no package / transport error)."""
    if not os.environ.get("TYPESAFE_API_KEY"):
        return None
    try:
        from typesafe_sdk import Choice, TypeSafeClient
    except Exception:
        return None
    try:
        with TypeSafeClient() as client:
            resp = client.system_one(
                state=state.to_jev_state(),
                questions={
                    "next_phrase": Choice(
                        instructions=ARRANGE_INSTRUCTIONS,
                        criteria=ARRANGE_CRITERIA,
                    ),
                },
            )
        ans = resp.choices["next_phrase"]
        dist = _norm_dist(dict(ans.probabilities or {}), ARRANGE_OPTIONS)
        choice = str(ans.choice)
        if choice not in ARRANGE_OPTIONS:
            return None  # refuse unauthored output; fall through to fallback
        return Decision(
            arrangement=ArrangementResult(
                choice=choice,
                probabilities=dist,
                confidence=float(ans.confidence or 0.0),
                alternates=_with_alternates(choice, dist),
            ),
            source="jev-live",
            reason="jev system_one Choice, full distribution preserved",
            switched=True,  # gate below decides the actual switch
        )
    except Exception as exc:
        return Decision(
            arrangement=ArrangementResult(
                "HOLD", {o: 0.0 for o in ARRANGE_OPTIONS}, 0.0
            ),
            source="classical-fallback",
            reason=f"jev transport failure ({type(exc).__name__}); held",
            switched=False,
        )


# ---------------------------------------------------------------- conductor
class FLConductor:
    """Holds the current arrangement; enforces phrase hysteresis."""

    def __init__(self, initial_preset: str = "FULL_CHORUS") -> None:
        if initial_preset not in ARRANGE_OPTIONS and initial_preset != "FULL_CHORUS":
            raise ValueError(f"unauthored initial preset: {initial_preset}")
        self.current = initial_preset if initial_preset in ARRANGE_OPTIONS else "HOLD"
        self._last_change_bar: Optional[int] = None
        self.history: list[dict[str, Any]] = []

    def _gate(
        self,
        top: str,
        dist: dict[str, float],
        conf: float,
        state: FLPhraseState,
    ) -> tuple[str, bool, str]:
        # SETTLE rule: low confidence near an authored ending resolves
        # deterministically instead of dithering.
        if state.authored_ending and conf < SETTLE_CONF:
            reason = "settle-safety: low confidence near ending, authored resolution"
            return "SETTLE", self.current != "SETTLE", reason
        if top == self.current:
            return self.current, False, "hold: top == current"
        margin = dist.get(top, 0.0) - dist.get(self.current, 0.0)
        if state.bars_since_change < MIN_HOLD_BARS and not (
            conf >= CONF_SWITCH_GATE and dist.get(top, 0.0) >= 0.9
        ):
            return self.current, False, (
                f"hold: min-hold {state.bars_since_change}b < {MIN_HOLD_BARS}b"
            )
        if margin >= SWITCH_MARGIN or conf >= CONF_SWITCH_GATE:
            return top, True, f"switch: margin {margin:.2f}, conf {conf:.2f}"
        return self.current, False, (
            f"hold: margin {margin:.2f} < {SWITCH_MARGIN}, conf {conf:.2f}"
        )

    def evaluate(
        self,
        state: FLPhraseState,
        now: Optional[float] = None,
        live_enabled: bool = True,
    ) -> Decision:
        now = time.monotonic() if now is None else now
        live = _jev_ask(state) if live_enabled else None
        if live is not None and live.source == "jev-live":
            cand = live.arrangement
            source, _ = "jev-live", live.reason
        else:
            if live is not None:  # transport-failure calm hold
                self._record(state, live, now)
                return live
            scores = _fallback_scores(state)
            dist = _softmax(scores)
            top = max(dist, key=dist.get)
            cand = ArrangementResult(
                top, dist, dist[top], _with_alternates(top, dist)
            )
            source = "classical-fallback"
        if self._last_change_bar is None:
            self._last_change_bar = state.bar
        choice, switched, gate_reason = self._gate(
            cand.choice, cand.probabilities, cand.confidence, state
        )
        if switched:
            self._last_change_bar = state.bar
        self.current = choice
        decision = Decision(
            arrangement=ArrangementResult(
                choice, cand.probabilities, cand.confidence, cand.alternates
            ),
            source=source,
            reason=f"{source}; {gate_reason}",
            switched=switched,
        )
        self._record(state, decision, now)
        return decision

    def _record(self, state: FLPhraseState, decision: Decision, now: float) -> None:
        self.history.append(
            {
                "t": now,
                "bar": state.bar,
                "energy": state.energy,
                "energy_trend": state.energy_trend,
                "choice": decision.arrangement.choice,
                "probabilities": decision.arrangement.probabilities,
                "confidence": decision.arrangement.confidence,
                "source": decision.source,
                "reason": decision.reason,
                "switched": decision.switched,
            }
        )


def format_hud(state: FLPhraseState, decision: Decision, next_preset: str) -> str:
    """Debug HUD, exactly the spec shape."""
    a = decision.arrangement
    alt = a.alternates[0] if a.alternates else ("—", 0.0)
    energy = (
        f"{state.energy:.2f}/{state.energy_trend}"
        if state.energy is not None
        else "unknown"
    )
    director = "JEV" if decision.source == "jev-live" else "FALLBACK"
    lines = [
        "JEV FL CONDUCTOR",
        "",
        f"Bar: {state.bar}",
        f"Tempo: {state.tempo_bpm if state.tempo_bpm is not None else 'unknown'}",
        f"Energy: {energy}",
        "",
        "Current:",
        state.current_preset,
        "",
        "Jev:",
        f"{a.choice} {a.confidence:.2f}",
        "",
        "Alternate:",
        f"{alt[0]} {alt[1]:.2f}",
        "",
        "Director:",
        director,
        "",
        "Next:",
        next_preset,
    ]
    return "\n".join(lines)
