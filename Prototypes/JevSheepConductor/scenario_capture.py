"""Five-beat capture driver for the Jev Sheep Conductor prototype.

Beats (48s total, evaluated every 2s — musical phrases, never per-frame):
  1. ENTER_FIELD   0-10s  quiet exploration      -> GRAZE + SOFT_WIND
  2. APPROACH     10-20s  Melusina nears flock   -> TURN_TO_PLAYER + LAVENDER
  3. WIND         20-30s  wind strengthens       -> FOLLOW_WIND + FLOWER_HUE
  4. RESONANCE    30-40s  resonance peak         -> SPIRAL then CRESCENDO_BURST
  5. SETTLE       40-48s  energy spent           -> RETURN_TO_IDLE + NONE

All state is source="scenario" (scripted). The UE adapter (README) replaces
this driver with live signals; the conductor API is unchanged.

Outputs (all inside this folder; delete the folder to remove everything):
  capture_log.txt     timestamped HUD lines, one per evaluation
  capture_report.json full distributions + provenance per evaluation
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jev_sheep_conductor import (  # noqa: E402
    ConductorState,
    SheepConductor,
    format_hud,
)

STEP = 2.0


def beat_state(t: float, sslr: float) -> tuple[str, ConductorState]:
    """Scripted state trajectory. Values are hand-authored for the beats.
    sslr = seconds since the flock last changed response (driver clock)."""
    if t < 10.0:
        return "ENTER_FIELD", ConductorState(
            bpm_intensity=0.2, beat_energy=0.2, player_distance_m=25.0,
            player_movement="walk", resonance=0.1, wind_direction_deg=90.0,
            wind_strength=0.2, palette_state="neutral",
            seconds_since_last_response=sslr, recent_interaction="none",
            current_behavior="GRAZE",
        )
    if t < 20.0:
        k = (t - 10.0) / 10.0
        return "APPROACH", ConductorState(
            bpm_intensity=0.25, beat_energy=0.3,
            player_distance_m=25.0 - 23.0 * k,
            player_movement="walk" if k < 0.6 else "still",
            resonance=0.25, wind_direction_deg=90.0, wind_strength=0.25,
            palette_state="neutral", seconds_since_last_response=sslr,
            recent_interaction="approached" if k > 0.4 else "none",
            current_behavior="GRAZE",
        )
    if t < 30.0:
        k = (t - 20.0) / 10.0
        return "WIND", ConductorState(
            bpm_intensity=0.4, beat_energy=0.5, player_distance_m=5.0,
            player_movement="still", resonance=0.3,
            wind_direction_deg=90.0 + 40.0 * k,
            wind_strength=0.3 + 0.5 * k, palette_state="lavender_wash",
            seconds_since_last_response=sslr,
            recent_interaction="approached", current_behavior="TURN_TO_PLAYER",
        )
    if t < 40.0:
        k = (t - 30.0) / 10.0
        return "RESONANCE", ConductorState(
            bpm_intensity=0.6 + 0.3 * k, beat_energy=0.6 + 0.35 * k,
            player_distance_m=6.0, player_movement="still",
            resonance=0.55 + 0.4 * k, wind_direction_deg=130.0,
            wind_strength=0.5 - 0.2 * k, palette_state="gold_shimmer",
            seconds_since_last_response=sslr,
            recent_interaction="approached",
            current_behavior="SPIRAL_FORMATION" if k > 0.4 else "FOLLOW_WIND",
        )
    return "SETTLE", ConductorState(
        bpm_intensity=0.2, beat_energy=0.2, player_distance_m=8.0,
        player_movement="still", resonance=0.15,
        wind_direction_deg=130.0, wind_strength=0.2,
        palette_state="neutral",
        seconds_since_last_response=sslr, recent_interaction="none",
        current_behavior="CRESCENDO_BURST",
    )


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    conductor = SheepConductor()
    now = 0.0
    log_lines: list[str] = []
    report: list[dict] = []
    t = 0.0
    last_response_t = 0.0
    prev_flock = conductor.current_flock
    while t < 48.0:
        beat, state = beat_state(t, sslr=round(t - last_response_t, 1))
        state.provenance = "scenario"
        dec = conductor.evaluate(state, now=now)
        hud = format_hud(dec)
        log_lines.append(f"[t={t:05.1f}s {beat}] src={dec.source}")
        log_lines.append(hud)
        log_lines.append("")
        report.append({
            "t": round(t, 1), "beat": beat, "source": dec.source,
            "reason": dec.reason,
            "flock": {"choice": dec.flock.choice,
                      "confidence": round(dec.flock.confidence, 3),
                      "probabilities": {k: round(v, 3)
                                        for k, v in dec.flock.probabilities.items()},
                      "displayed": conductor.current_flock,
                      "switched": dec.switched_flock},
            "world": {"choice": dec.world.choice,
                      "confidence": round(dec.world.confidence, 3),
                      "probabilities": {k: round(v, 3)
                                        for k, v in dec.world.probabilities.items()},
                      "displayed": conductor.current_world,
                      "switched": dec.switched_world},
        })
        print(f"[t={t:05.1f}s {beat}]")
        print(hud)
        print("")
        if conductor.current_flock != prev_flock:
            last_response_t = t
            prev_flock = conductor.current_flock
        t += STEP
        now += STEP
    with open(os.path.join(here, "capture_log.txt"), "w") as f:
        f.write("\n".join(log_lines))
    with open(os.path.join(here, "capture_report.json"), "w") as f:
        json.dump({"evaluations": report}, f, indent=2)
    print(f"wrote capture_log.txt + capture_report.json ({len(report)} evals)")


if __name__ == "__main__":
    main()
