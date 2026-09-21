"""Jev gaze director — FIRST IN-ENGINE PROOF bridge (t=20 moment).

What this is: pure-Python directing logic with injected sense/act seams.
No `unreal` import here, no editor calls here. The thin Monolith binding
lives in monolith_gaze_binding.py; the staging runbook is
JEV_GAZE_STAGING.md. Everything stays in Prototypes/JevSheepConductor/.

Directing contract (from the proof brief):
- Jev decides the expressive middle (TURN_TO_PLAYER or not).
- Jev does NOT own termination: release back to idle is deterministic
  and authored, and it overrides Jev. Resolution is always AUTHORED.
- Failsafe: any Jev failure/timeout/invalid output -> deterministic
  sheep behavior, Director=FALLBACK. Gameplay never blocks on network.
- Gaze execution is authored: per-sheep onset delays, yaw variance,
  eased slew. Jev never touches animation detail.
- Wind counter-pressure: rising wind must not break the gaze while Jev
  holds TURN_TO_PLAYER. This falls out of the criteria (wind is never a
  negative for TURN) plus the hold below: once GAZE is ON it latches
  until the authored release fires.

Authored numbers (tune by eye, all in one place):
  AWARENESS_RADIUS_M = 8.0    enter the encounter
  RELEASE_RADIUS_M = 10.0     hysteresis band outside awareness
  STILL_SPEED_MPS = 0.35      below this Melusina counts as still
  RELEASE_MOVE_S = 3.0        fast movement this long forces release
  MAX_SLEW_DEG_S = 90.0       no snapping
  ONSET_DELAY_S = (0.15..0.45 per sheep, seeded)
  YAW_VARIANCE_DEG = 8.0      flock attention, not robot sync
  JEV_TIMEOUT_S = 8.0       failsafe trip
"""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from jev_sheep_conductor import (
    ConductorState,
    Decision,
    SheepConductor,
)

AWARENESS_RADIUS_M = 8.0
RELEASE_RADIUS_M = 10.0
STILL_SPEED_MPS = 0.35
RELEASE_MOVE_S = 3.0
MAX_SLEW_DEG_S = 90.0
YAW_VARIANCE_DEG = 8.0
JEV_TIMEOUT_S = 8.0


def _shortest_arc_deg(from_deg: float, to_deg: float) -> float:
    return ((to_deg - from_deg + 180.0) % 360.0) - 180.0


@dataclass
class SheepHandle:
    """One flock member. yaw_deg is the last commanded yaw (authored)."""
    sheep_id: str
    x: float = 0.0
    y: float = 0.0
    yaw_deg: float = 0.0
    onset_delay_s: float = 0.3
    yaw_var_deg: float = 0.0


@dataclass
class GazeHud:
    behavior: str = "GRAZE"
    behavior_prob: float = 0.0
    alt: str = "—"
    alt_prob: float = 0.0
    wind: float = 0.0
    player_dist: float = 0.0
    player_still: int = 0
    director: str = "FALLBACK"  # JEV | FALLBACK
    resolution: str = "AUTHORED"

    def render(self) -> str:
        return "\n".join([
            "JEV SHEEP CONDUCTOR",
            f"Behavior: {self.behavior} {self.behavior_prob:.2f}",
            f"Alt: {self.alt} {self.alt_prob:.2f}",
            f"Wind: {self.wind:.2f}",
            f"PlayerDist: {self.player_dist:.1f}",
            f"PlayerStill: {self.player_still}",
            f"Director: {self.director}",
            f"Resolution: {self.resolution}",
        ])


class SheepGazeDirector:
    """Owns encounter state. sense()/act() are injected by the binding."""

    def __init__(self, sheep: list[SheepHandle],
                 decide: Optional[Callable[[ConductorState], Decision]] = None):
        self.sheep = sheep
        self._conductor = SheepConductor()
        self._decide = decide or self._live_decide
        self.gaze_on = False
        self.gaze_elapsed = 0.0
        self.moving_time = 0.0
        self.sslr = 0.0  # seconds since last flock response (own clock)
        self.director = "FALLBACK"
        self.last_decision: Optional[Decision] = None
        self.hud = GazeHud()
        # Deterministic per-sheep character: seeded from index, not random.
        for i, s in enumerate(self.sheep):
            s.onset_delay_s = 0.15 + 0.10 * ((i * 37) % 4) / 1.0 * 0.75
            s.yaw_var_deg = YAW_VARIANCE_DEG * (((i * 53) % 7) / 3.0 - 1.0)

    # -- Jev path (failsafe-wrapped) -------------------------------------
    def _live_decide(self, state: ConductorState) -> Decision:
        box: dict[str, Any] = {}
        def run() -> None:
            try:
                box["dec"] = self._conductor.evaluate(state)
            except Exception as exc:  # noqa: BLE001 — failsafe must catch all
                box["err"] = exc
        th = threading.Thread(target=run, daemon=True)
        th.start()
        th.join(timeout=JEV_TIMEOUT_S)
        if box.get("dec") is None:
            raise TimeoutError("jev decision timeout" if th.is_alive()
                               else f"jev decision failed: {box.get('err')}")
        return box["dec"]

    # -- one phrase tick ---------------------------------------------------
    def tick(self, player_x: float, player_y: float, player_speed_mps: float,
             wind01: float, dt_s: float) -> dict[str, Any]:
        """Sense -> (maybe) ask Jev -> gaze/release -> authored act.
        Returns the act commands for the binding to execute."""
        still = player_speed_mps < STILL_SPEED_MPS
        dist = math.hypot(player_x, player_y)  # binding passes flock-relative
        self.sslr += dt_s

        if not still:
            self.moving_time += dt_s
        else:
            self.moving_time = 0.0

        # Authored release ALWAYS wins (Jev never owns termination).
        release = (dist > RELEASE_RADIUS_M
                   or self.moving_time >= RELEASE_MOVE_S)
        entered = dist <= AWARENESS_RADIUS_M

        decision: Optional[Decision] = None
        if entered and not release:
            state = ConductorState(
                bpm_intensity=0.25, beat_energy=0.3,
                player_distance_m=dist,
                player_movement="still" if still else "walk",
                resonance=0.25, wind_strength=wind01,
                palette_state="neutral",
                seconds_since_last_response=round(self.sslr, 1),
                recent_interaction="approached",
                current_behavior=("TURN_TO_PLAYER" if self.gaze_on
                                  else "GRAZE"),
                provenance="ue-live",
            )
            try:
                decision = self._decide(state)
                self.director = ("JEV" if decision.source == "jev-live"
                                 else "FALLBACK")
            except Exception:  # noqa: BLE001 — failsafe
                decision = None
                self.director = "FALLBACK"

        if decision is not None:
            self.last_decision = decision
            want_gaze = decision.flock.choice == "TURN_TO_PLAYER"
            if want_gaze and not self.gaze_on:
                self.gaze_on = True
                self.gaze_elapsed = 0.0
                self.sslr = 0.0
            # NOTE: no else-branch turning gaze OFF from a Jev verdict.
            # Only the authored release below ends the encounter.

        if release and self.gaze_on:
            self.gaze_on = False
            self.sslr = 0.0

        if self.gaze_on:
            self.gaze_elapsed += dt_s

        # Authored act: eased slew toward player bearing + variance.
        acts: list[dict[str, Any]] = []
        for s in self.sheep:
            if self.gaze_on and self.gaze_elapsed >= s.onset_delay_s:
                bearing = math.degrees(math.atan2(player_y - s.y,
                                                  player_x - s.x))
                target = bearing + s.yaw_var_deg
                step = _shortest_arc_deg(s.yaw_deg, target)
                max_step = MAX_SLEW_DEG_S * dt_s
                s.yaw_deg += max(-max_step, min(max_step, step))
                acts.append({"sheep_id": s.sheep_id, "gaze": True,
                             "yaw_deg": round(s.yaw_deg, 2)})
            else:
                acts.append({"sheep_id": s.sheep_id, "gaze": False,
                             "yaw_deg": round(s.yaw_deg, 2)})

        self.hud = self._hud(dist, still, wind01)
        return {"gaze_on": self.gaze_on, "acts": acts,
                "director": self.director, "hud": self.hud.render()}

    def _hud(self, dist: float, still: bool, wind: float) -> GazeHud:
        d = self.last_decision
        if d is None:
            return GazeHud(wind=wind, player_dist=dist,
                           player_still=int(still),
                           director=self.director)
        alts = [a for a in d.flock.alternates if a[0] != d.flock.choice]
        alt = alts[0] if alts else ("—", 0.0)
        return GazeHud(
            behavior=d.flock.choice,
            behavior_prob=d.flock.probabilities.get(d.flock.choice, 0.0),
            alt=alt[0], alt_prob=alt[1], wind=wind, player_dist=dist,
            player_still=int(still), director=self.director)
