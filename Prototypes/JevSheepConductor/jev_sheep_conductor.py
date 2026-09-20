"""Jev-driven Choral Sheep Conductor — isolated prototype.

ISOLATION CONTRACT (read before touching):
- Everything lives in Prototypes/JevSheepConductor/. Delete this folder to
  remove the experiment. Nothing here imports Melodia game modules.
- NO production-map mutation. NO .umap/.uasset writes. NO editor calls.
- Jev selects ONLY among authored options (9 flock + 6 world). It never
  generates content, dialogue, or parameters — execution of a selection
  belongs to existing Blueprint/PCG/MPC/material systems (wiring stub is in
  README.md, not in this file).
- Telemetry honesty: state fields marked source="scenario" are scripted by
  scenario_capture.py for the capture beats. Fields marked source="ue-live"
  must come from the UE adapter (README mapping table) when wired. This
  module never invents live telemetry — unknown fields stay None and the
  fallback treats them as calm/missing.
- Provenance: every Decision records source="jev-live" or
  source="classical-fallback" plus the reason. Fallback exists so the loop
  runs before TYPESAFE_API_KEY is configured; it is NOT Jev evidence.

Skill: typesafe-ai. Per its guidance, both judgments go in ONE system_one
call as parallel Choice questions over the same state; code owns workflow,
cooldown, and execution.
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

FLOCK_OPTIONS = (
    "GRAZE",
    "TURN_TO_PLAYER",
    "CHORAL_SWAY",
    "FOLLOW_WIND",
    "PART_PATH",
    "SPIRAL_FORMATION",
    "RESONANCE_PULSE",
    "CRESCENDO_BURST",
    "RETURN_TO_IDLE",
)

WORLD_OPTIONS = (
    "NONE",
    "SOFT_WIND",
    "LAVENDER_PALETTE",
    "GOLD_CYMATICS",
    "FLOWER_HUE_SHIFT",
    "RESONANCE_RIPPLE",
)

# Cooldown / hysteresis: flock should phrase, not twitch.
MIN_HOLD_SECONDS = 4.0
SWITCH_MARGIN = 0.08  # top_prob must clear current_prob by this (or conf gate)
CONF_SWITCH_GATE = 0.80  # high-confidence top may switch even under margin


@dataclass
class ConductorState:
    """Compact normalized state. 0.0..1.0 unless noted. None = unknown."""

    bpm_intensity: Optional[float] = None
    beat_energy: Optional[float] = None
    player_distance_m: Optional[float] = None  # raw metres, not normalized
    player_movement: str = "still"  # still | walk | run
    resonance: Optional[float] = None
    wind_direction_deg: Optional[float] = None  # 0..360
    wind_strength: Optional[float] = None
    palette_state: str = "neutral"  # free string from live palette, if exposed
    seconds_since_last_response: float = 0.0
    recent_interaction: str = "none"  # none | approached | touched | fed
    current_behavior: str = "GRAZE"
    provenance: str = "scenario"  # scenario | ue-live

    def to_jev_state(self) -> dict[str, Any]:
        """Named JSON fields for Jev. Drops None so missing data reads as
        missing, not as zero."""
        proximity = None
        if self.player_distance_m is not None:
            proximity = max(0.0, min(1.0, 1.0 - self.player_distance_m / 30.0))
        raw: dict[str, Any] = {
            "bpm_intensity": self.bpm_intensity,
            "beat_energy": self.beat_energy,
            "player_distance_m": self.player_distance_m,
            "player_proximity": proximity,
            "player_movement": self.player_movement,
            "resonance": self.resonance,
            "wind_direction_deg": self.wind_direction_deg,
            "wind_strength": self.wind_strength,
            "palette_state": self.palette_state,
            "seconds_since_last_response": round(self.seconds_since_last_response, 1),
            "recent_interaction": self.recent_interaction,
            "current_behavior": self.current_behavior,
        }
        return {k: v for k, v in raw.items() if v is not None}


FLOCK_CRITERIA: dict[str, Any] = {
    "GRAZE": {
        "what": "Calm default; sheep crop grass, ears soft, no formation.",
        "when": "Quiet exploration, low music, player far or still.",
        "not_for": "Any peak, approach greeting, or wind event.",
    },
    "TURN_TO_PLAYER": {
        "what": "Heads lift and turn toward Melusina; no locomotion.",
        "when": "She approaches or interacts; greeting before anything bigger.",
        "not_for": "Wind or resonance peaks; this is a hello, not a setpiece.",
    },
    "CHORAL_SWAY": {
        "what": "Gentle rhythmic sway in place, breathing with the beat.",
        "when": "Moderate musical energy, flock settled but listening.",
        "not_for": "Strong resonance or wind — sway stays small and in place.",
    },
    "FOLLOW_WIND": {
        "what": "Flock drifts/leans with the wind; coats ripple downwind.",
        "when": "Wind strengthens clearly above ambient.",
        "not_for": "Calm air or resonance peaks; needs real wind.",
    },
    "PART_PATH": {
        "what": "Sheep step aside to open a path for Melusina.",
        "when": "She walks/runs through or toward the flock at close range.",
        "not_for": "Standing far away; no one to make way for.",
    },
    "SPIRAL_FORMATION": {
        "what": "Slow spiral gathering; first obvious magical response.",
        "when": "Strong resonance with musical support.",
        "not_for": "Weak resonance or wind-only moments.",
    },
    "RESONANCE_PULSE": {
        "what": "One breathing pulse of light/sound through wool; flock holds.",
        "when": "Mid resonance with a beat accent; smaller than spiral.",
        "not_for": "Full peaks (use CRESCENDO_BURST) or calm (use sway/graze).",
    },
    "CRESCENDO_BURST": {
        "what": "Single musical-peak eruption: rear, bells, light; then release.",
        "when": "Musical peak only — high beat energy AND high resonance.",
        "not_for": "Anything less than a peak; rarest state.",
    },
    "RETURN_TO_IDLE": {
        "what": "Deliberate settle: heads lower, formation loosens, field exhales.",
        "when": "After a peak or greeting, energy spent, time passed.",
        "not_for": "Mid-peak; only when the moment is ending.",
    },
}

WORLD_CRITERIA: dict[str, Any] = {
    "NONE": {"what": "No accompaniment; field stays as it is."},
    "SOFT_WIND": {"what": "Light ambient wind lift; grass breathes."},
    "LAVENDER_PALETTE": {"what": "Soft lavender grade wash; greeting tint."},
    "GOLD_CYMATICS": {"what": "Gold cymatic shimmer; strong-resonance dress."},
    "FLOWER_HUE_SHIFT": {"what": "Flower hue drift with the wind."},
    "RESONANCE_RIPPLE": {"what": "Visible ripple ring at the musical peak."},
}

FLOCK_INSTRUCTIONS = (
    "Choose the single flock behavior that fits this moment of Melusina near "
    "the Choral Sheep. Prefer the smallest response that honors the state: "
    "greet before celebrating, sway before spiraling, spiral before bursting. "
    "Reserve CRESCENDO_BURST for true musical peaks and RETURN_TO_IDLE for "
    "the exhale after one."
)
WORLD_INSTRUCTIONS = (
    "Choose the single world accompaniment that fits the same moment. "
    "Prefer restraint: NONE or SOFT_WIND unless the state earns color or "
    "ripple. Match the flock choice in scale, never outshine it."
)


@dataclass
class ChannelResult:
    choice: str
    probabilities: dict[str, float]
    confidence: float
    alternates: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class Decision:
    flock: ChannelResult
    world: ChannelResult
    source: str  # jev-live | classical-fallback
    reason: str
    switched_flock: bool
    switched_world: bool
    # Pre-gate candidate tops (what the arm wanted before cooldown). Used by
    # the shadow-duet harness to tell "wanted earlier" from "displayed".
    cand_flock: str = ""
    cand_world: str = ""

    def top_alternate(self, ch: ChannelResult) -> Optional[tuple[str, float]]:
        return ch.alternates[0] if ch.alternates else None


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
def _fallback_scores(s: ConductorState) -> tuple[dict[str, float], dict[str, float]]:
    """Deterministic classical heuristic. Documents the sanity-check mapping
    as code so the loop runs with no backend. NOT Jev evidence."""
    f = {o: 0.05 for o in FLOCK_OPTIONS}
    w = {o: 0.05 for o in WORLD_OPTIONS}
    bpm = s.bpm_intensity if s.bpm_intensity is not None else 0.2
    beat = s.beat_energy if s.beat_energy is not None else 0.2
    reso = s.resonance if s.resonance is not None else 0.0
    wind = s.wind_strength if s.wind_strength is not None else 0.0
    near = s.player_distance_m is not None and s.player_distance_m < 8.0
    calm = bpm < 0.35 and beat < 0.35 and reso < 0.3

    f["GRAZE"] += 0.6 if calm and not near else 0.1
    if near and calm:
        f["TURN_TO_PLAYER"] += 0.9
        w["LAVENDER_PALETTE"] += 0.8
    if s.player_movement in ("walk", "run") and near:
        f["PART_PATH"] += 0.9
    if 0.35 <= beat < 0.7:
        f["CHORAL_SWAY"] += 0.6
        w["SOFT_WIND"] += 0.4 if wind < 0.5 else 0.0
    if wind >= 0.55:
        f["FOLLOW_WIND"] += 0.8
        w["FLOWER_HUE_SHIFT"] += 0.8
        w["SOFT_WIND"] += 0.3
    elif wind > 0.15:
        w["SOFT_WIND"] += 0.5
    else:
        w["NONE"] += 0.5
    if 0.4 <= reso < 0.65 and beat >= 0.5:
        f["RESONANCE_PULSE"] += 0.8
    if reso >= 0.6 and beat >= 0.4:
        f["SPIRAL_FORMATION"] += 0.9
        w["GOLD_CYMATICS"] += 0.9
    if reso >= 0.85 and beat >= 0.7:
        f["CRESCENDO_BURST"] += 1.2
        w["RESONANCE_RIPPLE"] += 1.1
    if s.seconds_since_last_response > 10.0 and calm:
        # Settle only matters after something happened; a flock already
        # grazing has nowhere to return from.
        if s.current_behavior not in ("GRAZE", "RETURN_TO_IDLE"):
            f["RETURN_TO_IDLE"] += 0.9
            w["NONE"] += 0.4
    if s.current_behavior in ("CRESCENDO_BURST", "SPIRAL_FORMATION") and calm:
        f["RETURN_TO_IDLE"] += 0.7
    return f, w


def _softmax(scores: dict[str, float], temp: float = 0.4) -> dict[str, float]:
    """Sharpened so a clear winner reads as one. Temperature is a display
    choice for the fallback only; Jev-live distributions pass through."""
    m = max(scores.values())
    exps = {k: math.exp((v - m) / temp) for k, v in scores.items()}
    total = sum(exps.values())
    return {k: v / total for k, v in exps.items()}


# ---------------------------------------------------------------- Jev live
def _jev_ask(state: ConductorState, timeout: float = 20.0) -> Optional[Decision]:
    """One system_one call, two parallel Choice questions. Returns None when
    the backend is unavailable (no key / no package / transport error)."""
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
                    "flock_response": Choice(
                        instructions=FLOCK_INSTRUCTIONS,
                        criteria=FLOCK_CRITERIA,
                    ),
                    "world_accompaniment": Choice(
                        instructions=WORLD_INSTRUCTIONS,
                        criteria=WORLD_CRITERIA,
                    ),
                },
            )
        flock_a = resp.choices["flock_response"]
        world_a = resp.choices["world_accompaniment"]
        flock_dist = _norm_dist(dict(flock_a.probabilities or {}), FLOCK_OPTIONS)
        world_dist = _norm_dist(dict(world_a.probabilities or {}), WORLD_OPTIONS)
        flock_choice = str(flock_a.choice)
        world_choice = str(world_a.choice)
        if flock_choice not in FLOCK_OPTIONS or world_choice not in WORLD_OPTIONS:
            return None  # refuse unauthored output; fall through to fallback
        return Decision(
            flock=ChannelResult(
                choice=flock_choice,
                probabilities=flock_dist,
                confidence=float(flock_a.confidence or 0.0),
                alternates=_with_alternates(flock_choice, flock_dist),
            ),
            world=ChannelResult(
                choice=world_choice,
                probabilities=world_dist,
                confidence=float(world_a.confidence or 0.0),
                alternates=_with_alternates(world_choice, world_dist),
            ),
            source="jev-live",
            reason="jev system_one 2xChoice, full distribution preserved",
            switched_flock=True,
            switched_world=True,
        )
    except Exception as exc:
        return Decision(
            flock=ChannelResult("GRAZE", {o: 0.0 for o in FLOCK_OPTIONS}, 0.0),
            world=ChannelResult("NONE", {o: 0.0 for o in WORLD_OPTIONS}, 0.0),
            source="classical-fallback",
            reason=f"jev transport failure ({type(exc).__name__}); fallback held calm",
            switched_flock=False,
            switched_world=False,
        )


# ---------------------------------------------------------------- conductor
class SheepConductor:
    """Holds current display state; enforces cooldown/hysteresis."""
    def __init__(self) -> None:
        self.current_flock = "GRAZE"
        self.current_world = "SOFT_WIND"
        # None = conductor just booted; first evaluation establishes the
        # flock as "already grazing" so cooldown applies from session start.
        self._last_flock_switch: Optional[float] = None
        self._last_world_switch: Optional[float] = None
        self.history: list[dict[str, Any]] = []

    def _gate(
        self, current: str, top: str, dist: dict[str, float],
        conf: float, last_switch: float, now: float,
    ) -> tuple[str, bool, float]:
        if top == current:
            return current, False, last_switch
        held = now - last_switch
        margin = dist.get(top, 0.0) - dist.get(current, 0.0)
        if held < MIN_HOLD_SECONDS and not (
            conf >= CONF_SWITCH_GATE and dist.get(top, 0.0) >= 0.9
        ):
            return current, False, last_switch
        if margin >= SWITCH_MARGIN or conf >= CONF_SWITCH_GATE:
            return top, True, now
        return current, False, last_switch

    def evaluate(
        self, state: ConductorState, now: Optional[float] = None,
        force_live: bool = False, live_enabled: bool = True,
    ) -> Decision:
        now = time.monotonic() if now is None else now
        booting = self._last_flock_switch is None
        live = _jev_ask(state) if live_enabled else None
        if live is not None and live.source == "jev-live":
            cand_flock, cand_world = live.flock, live.world
            source, reason = "jev-live", live.reason
        else:
            f_scores, w_scores = _fallback_scores(state)
            f_dist, w_dist = _softmax(f_scores), _softmax(w_scores)
            f_top = max(f_dist, key=f_dist.get)
            w_top = max(w_dist, key=w_dist.get)
            if live is not None:  # transport-failure calm hold
                return live
            cand_flock = ChannelResult(
                f_top, f_dist, f_dist[f_top], _with_alternates(f_top, f_dist))
            cand_world = ChannelResult(
                w_top, w_dist, w_dist[w_top], _with_alternates(w_top, w_dist))
            source = "classical-fallback"
            if force_live:
                reason = "force_live requested but no backend; fallback used"
            else:
                reason = ("no TYPESAFE_API_KEY; classical heuristic fallback "
                          "(not Jev evidence)")

        flock, sw_f, self._last_flock_switch = self._gate(
            self.current_flock, cand_flock.choice, cand_flock.probabilities,
            cand_flock.confidence, self._last_flock_switch or now, now)
        world, sw_w, self._last_world_switch = self._gate(
            self.current_world, cand_world.choice, cand_world.probabilities,
            cand_world.confidence, self._last_world_switch or now, now)
        if booting:
            # First hearing: adopt what the world says, then cooldown rules.
            flock, world = cand_flock.choice, cand_world.choice
            sw_f, sw_w = True, True
            self._last_flock_switch = now
            self._last_world_switch = now
        if sw_f:
            self.current_flock = flock
        if sw_w:
            self.current_world = world
        dec = Decision(cand_flock, cand_world, source, reason, sw_f, sw_w,
                       cand_flock=cand_flock.choice, cand_world=cand_world.choice)
        self.history.append({
            "t": round(now, 2), "flock": flock, "world": world,
            "source": source, "switched": [sw_f, sw_w],
        })
        # expose the HELD (displayed) values on the decision channels
        dec.flock = ChannelResult(
            flock, cand_flock.probabilities, cand_flock.confidence,
            cand_flock.alternates)
        dec.world = ChannelResult(
            world, cand_world.probabilities, cand_world.confidence,
            cand_world.alternates)
        return dec


def format_hud(dec: Decision) -> str:
    lines = ["JEV SHEEP CONDUCTOR"]
    fp = dec.flock.probabilities.get(dec.flock.choice, 0.0)
    wp = dec.world.probabilities.get(dec.world.choice, 0.0)
    lines.append(f"Behavior: {dec.flock.choice} {fp:.2f}")
    lines.append(f"World: {dec.world.choice} {wp:.2f}")
    alts = [a for a in dec.flock.alternates if a[0] != dec.flock.choice]
    if not alts:  # candidate differed from held; name the candidate top
        cands = sorted(dec.flock.probabilities.items(),
                       key=lambda kv: kv[1], reverse=True)
        alts = [(cands[0][0], cands[0][1])] if cands else []
    if alts:
        lines.append(f"Alt: {alts[0][0]} {alts[0][1]:.2f}")
    lines.append(f"src: {dec.source}")
    return "\n".join(lines)
