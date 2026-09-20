"""Jev-driven Melusina Bow Conductor — isolated prototype.

ISOLATION CONTRACT (read before touching):
- Everything lives in Prototypes/JevBowConductor/. Delete this folder to
  remove the experiment. Nothing here imports Melodia game modules.
- NO production-map mutation. NO .umap/.uasset writes. NO editor calls.
- Jev selects ONLY among authored options (7 bow responses mapped 1:1 to
  .uasset files that exist on disk, verified by the contract test). It never
  generates content. Execution of a selection belongs to existing
  Blueprint/ABP/montage systems (wiring stub is in README.md, not here).
- Telemetry honesty: fields marked source="scenario" are scripted by
  scenario_bow_capture.py. Fields marked source="ue-live" must come from
  the UE adapter (README mapping table) when wired. Unknown fields stay
  None and the fallback treats them as calm/missing.
- Provenance: every Decision records source="jev-live" or
  source="classical-fallback" plus the reason. Fallback is NOT Jev evidence.
- The API key lives ONLY in the shell environment (TYPESAFE_API_KEY).
  It is never written to any file in this folder.

Skill: typesafe-ai. Both judgments go in ONE system_one call as parallel
questions over the same state (Choice + Noul); code owns workflow,
cooldown, and execution.
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

REPO = "C:/EnvironmentPortfolio/BS_GodFile"
ANIM_DIR = REPO + "/Content/Melodia/Characters/Melusina/Animations"
POLISH = ANIM_DIR + "/Polish_20260919"

# Option -> authored asset on disk. Verified by test (existence only:
# the test confirms presence, never animation contents).
BOW_OPTIONS = (
    "IDLE_READY",
    "BOW_V1",
    "BOW_V2",
    "BOW_POLISHED",
    "BOW_GAMEPLAY",
    "BOW_BOUND",
    "LOWER_BOW",
)

ASSET_MAP = {
    "IDLE_READY": ANIM_DIR + "/AM_Idle.uasset",
    "BOW_V1": POLISH + "/A_Melusina_BowAttack_A_RangeAttack.uasset",
    "BOW_V2": POLISH + "/A_Melusina_BowAttackV2_A_RangeAttack.uasset",
    "BOW_POLISHED": POLISH + "/AM_Melusina_BowAttack_Polished.uasset",
    "BOW_GAMEPLAY": POLISH + "/AM_Melusina_BowAttack_Gameplay.uasset",
    "BOW_BOUND": POLISH + "/AM_Melusina_BowAttack_Bound.uasset",
    "LOWER_BOW": ANIM_DIR + "/A_ThirdPersonIdle.uasset",
}

BOW_MESH = (
    REPO + "/Content/Melodia/Characters/Melusina/Meshes/M_bow_002.uasset"
)

# Cooldown / hysteresis: the bow should phrase, not twitch.
MIN_HOLD_SECONDS = 4.0
SWITCH_MARGIN = 0.08
CONF_SWITCH_GATE = 0.80


@dataclass
class BowState:
    """Compact normalized state. 0.0..1.0 unless noted. None = unknown."""

    bpm_intensity: Optional[float] = None
    beat_energy: Optional[float] = None
    target_distance_m: Optional[float] = None
    movement: str = "still"  # still | walk | run
    resonance: Optional[float] = None
    wind_strength: Optional[float] = None
    seconds_since_last_loose: float = 99.0
    current_bow: str = "IDLE_READY"
    provenance: str = "scenario"  # scenario | ue-live

    def to_jev_state(self) -> dict[str, Any]:
        raw: dict[str, Any] = {
            "bpm_intensity": self.bpm_intensity,
            "beat_energy": self.beat_energy,
            "target_distance_m": self.target_distance_m,
            "movement": self.movement,
            "resonance": self.resonance,
            "wind_strength": self.wind_strength,
            "seconds_since_last_loose": round(self.seconds_since_last_loose, 1),
            "current_bow": self.current_bow,
        }
        return {k: v for k, v in raw.items() if v is not None}


BOW_CRITERIA: dict[str, Any] = {
    "IDLE_READY": {
        "what": "Bow carried ready, string slack. Resting default.",
        "when": "Quiet exploration, no target, energy spent.",
        "not_for": "Any peak or engaged exchange.",
    },
    "BOW_V1": {
        "what": "First authored range-attack take.",
        "when": "Standard engagement at moderate energy.",
        "not_for": "Peaks (prefer V2/POLISHED) or rest (prefer IDLE).",
    },
    "BOW_V2": {
        "what": "Second authored range-attack take.",
        "when": "Heavier engagement, rising energy, alternate phrasing.",
        "not_for": "Quiet moments; this is the louder voice.",
    },
    "BOW_POLISHED": {
        "what": "Polished performance take.",
        "when": "Musical peaks and capturable moments — the showcase voice.",
        "not_for": "Routine exchanges; rarest selection.",
    },
    "BOW_GAMEPLAY": {
        "what": "Gameplay-timed take, combat rhythm.",
        "when": "Active combat timing with beat support.",
        "not_for": "Showcase or rest.",
    },
    "BOW_BOUND": {
        "what": "Bound/notified take, quest-framed.",
        "when": "Scripted or notified story beats involving the bow.",
        "not_for": "Free combat or rest.",
    },
    "LOWER_BOW": {
        "what": "Deliberate lowering: the exchange ends, field exhales.",
        "when": "After a loose or peak, target gone, energy spent.",
        "not_for": "Mid-engagement; only when the moment ends.",
    },
}

BOW_INSTRUCTIONS = (
    "Choose the single authored bow response that fits this moment of "
    "Melusina with her bow. Prefer the smallest response that honors the "
    "state: ready before attacking, V1 before V2, V2 before POLISHED. "
    "Reserve BOW_POLISHED for true musical peaks and LOWER_BOW for the "
    "exhale after one."
)

LOOSE_INSTRUCTIONS = (
    "Should Melusina loose (release the string) during this phrase? "
    "Say yes only when a drawn attack is held AND the musical moment "
    "earns a release — beat energy with resonance behind it."
)


@dataclass
class ChannelResult:
    choice: str
    probabilities: dict[str, float]
    confidence: float
    alternates: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class BowDecision:
    bow: ChannelResult
    loose: bool
    loose_probability: float
    source: str  # jev-live | classical-fallback
    reason: str
    switched: bool


def _norm_dist(dist: dict[str, float], options: tuple[str, ...]) -> dict[str, float]:
    full = {o: float(dist.get(o, 0.0)) for o in options}
    total = sum(full.values())
    if total <= 0:
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
def _fallback_scores(s: BowState) -> dict[str, float]:
    """Deterministic classical heuristic. NOT Jev evidence."""
    f = {o: 0.05 for o in BOW_OPTIONS}
    bpm = s.bpm_intensity if s.bpm_intensity is not None else 0.2
    beat = s.beat_energy if s.beat_energy is not None else 0.2
    reso = s.resonance if s.resonance is not None else 0.0
    calm = bpm < 0.35 and beat < 0.35 and reso < 0.3
    engaged = s.target_distance_m is not None and s.target_distance_m < 25.0

    f["IDLE_READY"] += 0.7 if calm and not engaged else 0.1
    if engaged and calm:
        f["BOW_V1"] += 0.8
    if engaged and 0.35 <= beat < 0.7:
        f["BOW_V1"] += 0.4
        f["BOW_GAMEPLAY"] += 0.6
    if engaged and beat >= 0.7:
        f["BOW_V2"] += 0.9
    if engaged and reso >= 0.85 and beat >= 0.7:
        f["BOW_POLISHED"] += 1.2
    if s.seconds_since_last_loose < 6.0 and calm:
        f["LOWER_BOW"] += 0.9
    if s.current_bow in ("BOW_POLISHED", "BOW_V2") and calm:
        f["LOWER_BOW"] += 0.7
    return f


def _fallback_loose(s: BowState, bow_name: str) -> float:
    beat = s.beat_energy if s.beat_energy is not None else 0.0
    reso = s.resonance if s.resonance is not None else 0.0
    if bow_name in ("BOW_V1", "BOW_V2", "BOW_POLISHED", "BOW_GAMEPLAY"):
        return min(1.0, 0.2 + beat * 0.5 + reso * 0.4)
    return 0.05


def _softmax(scores: dict[str, float], temp: float = 0.4) -> dict[str, float]:
    m = max(scores.values())
    exps = {k: math.exp((v - m) / temp) for k, v in scores.items()}
    total = sum(exps.values())
    return {k: v / total for k, v in exps.items()}


# ---------------------------------------------------------------- Jev live
def _jev_ask(s: BowState) -> Optional[tuple[ChannelResult, float]]:
    """One system_one call: Choice (asset) + Noul (loose?). None when the
    backend is unavailable (no key / no package / transport error)."""
    if not os.environ.get("TYPESAFE_API_KEY"):
        return None
    try:
        from typesafe_sdk import Choice, Noul, TypeSafeClient
    except Exception:
        return None
    try:
        with TypeSafeClient() as client:
            resp = client.system_one(
                state=s.to_jev_state(),
                questions={
                    "bow_response": Choice(
                        instructions=BOW_INSTRUCTIONS,
                        criteria=BOW_CRITERIA,
                    ),
                    "loose_now": Noul(instructions=LOOSE_INSTRUCTIONS),
                },
            )
        bow_a = resp.choices["bow_response"]
        loose_a = resp.nouls["loose_now"]
        dist = _norm_dist(dict(bow_a.probabilities or {}), BOW_OPTIONS)
        pick = str(bow_a.choice)
        if pick not in BOW_OPTIONS:
            return None  # refuse unauthored output
        return (
            ChannelResult(
                pick, dist, float(bow_a.confidence or 0.0),
                _with_alternates(pick, dist),
            ),
            float(loose_a.noul or 0.0),
        )
    except Exception:
        return None


# ---------------------------------------------------------------- conductor
class BowConductor:
    """Holds current display state; enforces cooldown/hysteresis."""

    def __init__(self) -> None:
        self.current = "IDLE_READY"
        self._last_switch: Optional[float] = None
        self.history: list[dict[str, Any]] = []

    def _gate(self, top: str, dist: dict[str, float], conf: float,
              now: float) -> tuple[str, bool]:
        if self._last_switch is None:
            # First hearing: adopt what the moment says, clock starts now.
            self._last_switch = now
            return top, top != self.current
        if top == self.current:
            return self.current, False
        held = now - self._last_switch
        margin = dist.get(top, 0.0) - dist.get(self.current, 0.0)
        if held < MIN_HOLD_SECONDS and not (
            conf >= CONF_SWITCH_GATE and dist.get(top, 0.0) >= 0.9
        ):
            return self.current, False
        if margin >= SWITCH_MARGIN or conf >= CONF_SWITCH_GATE:
            return top, True
        return self.current, False

    def evaluate(self, s: BowState, now: Optional[float] = None) -> BowDecision:
        now = time.monotonic() if now is None else now
        live = _jev_ask(s)
        if live is not None:
            cand, loose_p = live
            source = "jev-live"
            reason = "jev system_one Choice+Noul, full distribution preserved"
        else:
            dist = _softmax(_fallback_scores(s))
            top = max(dist, key=dist.get)
            cand = ChannelResult(top, dist, dist[top],
                                 _with_alternates(top, dist))
            loose_p = _fallback_loose(s, top)
            source = "classical-fallback"
            reason = "no TYPESAFE_API_KEY or backend; classical heuristic (not Jev evidence)"
        held, switched = self._gate(cand.choice, cand.probabilities,
                                    cand.confidence, now)
        if switched:
            self.current = held
            self._last_switch = now
        dec = BowDecision(
            bow=ChannelResult(held, cand.probabilities, cand.confidence,
                              cand.alternates),
            loose=bool(loose_p >= 0.6 and held not in ("IDLE_READY", "LOWER_BOW")),
            loose_probability=round(loose_p, 3),
            source=source, reason=reason, switched=switched,
        )
        self.history.append({"t": round(now, 2), "bow": held,
                             "source": source, "switched": switched})
        return dec


def format_hud(dec: BowDecision) -> str:
    lines = ["JEV BOW CONDUCTOR"]
    p = dec.bow.probabilities.get(dec.bow.choice, 0.0)
    lines.append(f"Bow: {dec.bow.choice} {p:.2f}")
    lines.append(f"Loose: {'YES' if dec.loose else 'hold'} {dec.loose_probability:.2f}")
    if dec.bow.alternates:
        lines.append(f"Alt: {dec.bow.alternates[0][0]} {dec.bow.alternates[0][1]:.2f}")
    lines.append(f"src: {dec.source}")
    return "\n".join(lines)
