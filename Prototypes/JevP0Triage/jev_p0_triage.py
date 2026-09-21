"""Jev-driven P0 triage conductor — isolated prototype.

ISOLATION CONTRACT:
- Everything lives in Prototypes/JevP0Triage/. Delete this folder to remove it.
- NO .umap/.uasset writes. NO editor mutations. NO ledger writes.
  Code READS state (echo status, git_ok, disk, port) and RECOMMENDS the next
  authored verification action. A human (or the P0 loop) executes it.
- Jev selects ONLY among the authored NEXT_ACTIONS below. It never generates
  content, commands, or parameters beyond the closed sets.
- Provenance: every Decision records source="jev-live" or
  source="classical-fallback" plus reason. Fallback runs without
  TYPESAFE_API_KEY and is NOT Jev evidence.

Skill: typesafe-ai. Choice + Noul + Score go in ONE system_one call over the
same state; code owns workflow, cooldown, and execution.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional

NEXT_ACTIONS = (
    "RUN_HEADLESS_SUITE",   # UnrealEditor-Cmd Melodia.Integration suites
    "RUN_PIE_SMOKE",        # Morning PIE smoke + HighResShot set
    "CAPTURE_STILLS",       # Authored capture pass for portfolio/AE
    "COOK_TO_G",            # Packaged cook to G: (disk-safe target)
    "HOLD_FOR_OWNER",       # Blocked or low-confidence: wait, don't burn time
)

MIN_HOLD_SECONDS = 60.0  # triage phrases, not frames
SWITCH_MARGIN = 0.08
CONF_SWITCH_GATE = 0.80


@dataclass
class P0State:
    """Compact normalized state. None = unknown (reads as missing, not zero)."""

    gate_staleness_days: Optional[float] = None  # oldest PASS row age
    dirty_count: Optional[int] = None            # git_ok dirty files
    disk_gb_free_c: Optional[float] = None       # C: free space
    editor_up: Optional[bool] = None
    port_9316_open: Optional[bool] = None
    last_failures: str = "none"                  # free text, e.g. "97/99 viewport-only"
    time_budget_min: float = 60.0
    current_action: str = "HOLD_FOR_OWNER"
    seconds_since_last_action: float = 9999.0
    provenance: str = "assembled"                # assembled | live-read

    def to_jev_state(self) -> dict[str, Any]:
        raw: dict[str, Any] = {
            "gate_staleness_days": self.gate_staleness_days,
            "dirty_count": self.dirty_count,
            "disk_gb_free_c": self.disk_gb_free_c,
            "editor_up": self.editor_up,
            "port_9316_open": self.port_9316_open,
            "last_failures": self.last_failures,
            "time_budget_min": self.time_budget_min,
            "current_action": self.current_action,
            "seconds_since_last_action": round(self.seconds_since_last_action, 1),
        }
        return {k: v for k, v in raw.items() if v is not None}


NEXT_ACTION_CRITERIA: dict[str, Any] = {
    name: f"Authored next verification step: {name}." for name in NEXT_ACTIONS
}

NEEDS_HUMAN_CRITERIA = (
    "The current P0 state needs an owner decision before burning "
    "editor/cook time (blocked, ambiguous, or irreversible-adjacent)."
)

CAPTURE_READY_LEVELS = [
    "No usable frames: nothing worth publishing.",
    "Raw frames only: audit stills exist but uncurated.",
    "Curated set: compressed web frames ready for the site.",
    "Portfolio moment: AE/TD-ready selects with a story beat.",
]


@dataclass
class TriageDecision:
    action: str
    action_probs: dict[str, float]
    needs_human: bool
    needs_human_prob: float
    capture_score: int
    capture_probs: list[float]
    source: str  # jev-live | classical-fallback
    reason: str
    confidence: float = 0.0


def classical_fallback(state: P0State) -> TriageDecision:
    """Deterministic rules. Clearly labeled, never Jev evidence."""
    probs = {a: 0.02 for a in NEXT_ACTIONS}
    reason: str
    if state.editor_up is False:
        probs["RUN_HEADLESS_SUITE"] = 0.88
        action, reason = "RUN_HEADLESS_SUITE", "editor down: headless suites need no viewport"
    elif (state.disk_gb_free_c or 99) < 20:
        probs["HOLD_FOR_OWNER"] = 0.88
        action, reason = "HOLD_FOR_OWNER", "C: disk low: cooking risks LFS failure"
    elif (state.gate_staleness_days or 0) > 14 and (state.time_budget_min or 0) >= 30:
        probs["RUN_PIE_SMOKE"] = 0.80
        action, reason = "RUN_PIE_SMOKE", "stale gates + budget: re-prove with PIE smoke first"
    elif "portfolio" in (state.last_failures or "").lower() or "capture" in (state.last_failures or "").lower():
        probs["CAPTURE_STILLS"] = 0.80
        action, reason = "CAPTURE_STILLS", "owner asked for site frames: curated capture pass"
    else:
        probs["RUN_HEADLESS_SUITE"] = 0.70
        action, reason = "RUN_HEADLESS_SUITE", "default: cheapest real signal first"
    # renormalize
    total = sum(probs.values())
    probs = {k: round(v / total, 4) for k, v in probs.items()}
    needs_human = action == "HOLD_FOR_OWNER"
    cap = 2 if action == "CAPTURE_STILLS" else 1
    cap_probs = [0.05, 0.15, 0.15, 0.65] if False else [0.1, 0.55, 0.3, 0.05]
    if action == "CAPTURE_STILLS":
        cap, cap_probs = 2, [0.05, 0.2, 0.6, 0.15]
    return TriageDecision(
        action=action, action_probs=probs,
        needs_human=needs_human,
        needs_human_prob=0.9 if needs_human else 0.15,
        capture_score=cap, capture_probs=cap_probs,
        source="classical-fallback", reason=reason,
        confidence=round(max(probs.values()), 3),
    )


def _try_jev_live(state: P0State) -> Optional[TriageDecision]:
    """Live Jev via TypeSafe SDK. Returns None when unavailable (no key/sdk)."""
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        return None
    try:
        from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
    except ImportError:
        return None
    try:
        questions = {
            "next": Choice(
                instructions="Pick the single best next P0 verification step from the authored set.",
                criteria=NEXT_ACTION_CRITERIA,
            ),
            "human": Noul(
                instructions="Should an owner decide before spending editor/cook time?",
                criteria={
                    "true": NEEDS_HUMAN_CRITERIA,
                    "false": "The state is unambiguous enough to proceed without the owner.",
                },
            ),
            "capture": Score(
                instructions="How publish-ready is the current capture set?",
                criteria=CAPTURE_READY_LEVELS,
            ),
        }
        with TypeSafeClient(api_key=key) as client:
            resp = client.system_one(state=state.to_jev_state(), questions=questions)
        nxt = resp.choices["next"]
        hum = resp.nouls["human"]
        cap = resp.scores["capture"]
        action = nxt.choice if nxt.choice in NEXT_ACTIONS else "HOLD_FOR_OWNER"
        probs = {k: float(v) for k, v in (nxt.probabilities or {}).items() if k in NEXT_ACTIONS}
        if action not in probs:
            probs[action] = float(nxt.confidence or 0.5)
        return TriageDecision(
            action=action, action_probs=probs,
            needs_human=bool(hum.noul > 0.5),
            needs_human_prob=float(hum.noul),
            capture_score=max(0, min(len(CAPTURE_READY_LEVELS) - 1, int(round(cap.score or 0)))),
            capture_probs=[float(p) for p in (cap.probabilities or [])],
            source="jev-live", reason="typesafe System One Choice+Noul+Score",
            confidence=float(nxt.confidence or 0.0),
        )
    except Exception as exc:  # service failure is not a decision
        return TriageDecision(
            action="HOLD_FOR_OWNER",
            action_probs={a: (0.88 if a == "HOLD_FOR_OWNER" else 0.03) for a in NEXT_ACTIONS},
            needs_human=True, needs_human_prob=0.95,
            capture_score=0, capture_probs=[0.9, 0.05, 0.03, 0.02],
            source="classical-fallback", reason=f"jev-live failed, holding: {type(exc).__name__}",
            confidence=0.9,
        )


def triage(state: P0State, live_enabled: bool = True) -> TriageDecision:
    """Entry point. Cooldown/hysteresis keeps triage phrasing, not twitching."""
    raw: Optional[TriageDecision] = None
    if live_enabled:
        raw = _try_jev_live(state)
    if raw is None:
        raw = classical_fallback(state)
    # Hysteresis: hold current action unless the top clearly wins.
    if (
        state.seconds_since_last_action < MIN_HOLD_SECONDS
        and state.current_action in NEXT_ACTIONS
        and raw.action != state.current_action
    ):
        cur_p = raw.action_probs.get(state.current_action, 0.0)
        top_p = raw.action_probs.get(raw.action, 0.0)
        if not (top_p - cur_p >= SWITCH_MARGIN or raw.confidence >= CONF_SWITCH_GATE):
            held_probs = dict(raw.action_probs)
            return TriageDecision(
                action=state.current_action, action_probs=held_probs,
                needs_human=raw.needs_human, needs_human_prob=raw.needs_human_prob,
                capture_score=raw.capture_score, capture_probs=raw.capture_probs,
                source=raw.source, reason=raw.reason + " | held by cooldown",
                confidence=raw.confidence,
            )
    return raw


def hud(decision: TriageDecision) -> str:
    top_alt = sorted(decision.action_probs.items(), key=lambda kv: -kv[1])[:2]
    alt = f" alt {top_alt[1][0]} {top_alt[1][1]:.2f}" if len(top_alt) > 1 else ""
    return (
        "JEV P0 TRIAGE\n"
        f"Action: {decision.action} {decision.action_probs.get(decision.action, 0.0):.2f}{alt}\n"
        f"Human: {'YES' if decision.needs_human else 'no'} {decision.needs_human_prob:.2f} | "
        f"Capture: L{decision.capture_score} [{CAPTURE_READY_LEVELS[decision.capture_score]}]\n"
        f"Source: {decision.source} | {decision.reason}"
    )
