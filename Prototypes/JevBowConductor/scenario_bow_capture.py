"""Five-beat bow capture for the Jev Bow Conductor.

Beats (40s total, evaluated every 2s — musical phrases, never per-frame):
  1. STRINGING  0-8s   quiet, bow unstrung at rest  -> IDLE_READY
  2. DRAW       8-16s  target nears, first draw     -> BOW_V1
  3. HOLD      16-24s  beat rises, second voice     -> BOW_V2 / GAMEPLAY
  4. LOOSE     24-32s  resonance peak               -> BOW_POLISHED + loose
  5. LOWER     32-40s  energy spent                 -> LOWER_BOW

All state is source="scenario" (scripted). The UE adapter (README) replaces
this driver with live signals; the conductor API is unchanged.

Outputs (inside this folder; delete the folder to remove everything):
  bow_capture_log.txt     timestamped HUD lines, one per evaluation
  bow_capture_report.json full distributions + provenance per evaluation
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jev_bow_director import (  # noqa: E402
    BowConductor,
    BowState,
    format_hud,
)

STEP = 2.0


def beat_state(t: float) -> tuple[str, BowState]:
    if t < 8.0:
        return "STRINGING", BowState(
            bpm_intensity=0.2, beat_energy=0.2, target_distance_m=None,
            movement="still", resonance=0.1, wind_strength=0.2,
            seconds_since_last_loose=99.0, current_bow="IDLE_READY",
        )
    if t < 16.0:
        k = (t - 8.0) / 8.0
        return "DRAW", BowState(
            bpm_intensity=0.35, beat_energy=0.45,
            target_distance_m=22.0 - 12.0 * k, movement="walk",
            resonance=0.3, wind_strength=0.25,
            seconds_since_last_loose=99.0, current_bow="IDLE_READY",
        )
    if t < 24.0:
        k = (t - 16.0) / 8.0
        return "HOLD", BowState(
            bpm_intensity=0.55 + 0.2 * k, beat_energy=0.6 + 0.2 * k,
            target_distance_m=9.0, movement="still",
            resonance=0.45 + 0.15 * k, wind_strength=0.4,
            seconds_since_last_loose=99.0, current_bow="BOW_V1",
        )
    if t < 32.0:
        k = (t - 24.0) / 8.0
        return "LOOSE", BowState(
            bpm_intensity=0.7 + 0.25 * k, beat_energy=0.7 + 0.25 * k,
            target_distance_m=9.0, movement="still",
            resonance=0.6 + 0.35 * k, wind_strength=0.3,
            seconds_since_last_loose=99.0, current_bow="BOW_V2",
        )
    return "LOWER", BowState(
        bpm_intensity=0.2, beat_energy=0.2, target_distance_m=None,
        movement="still", resonance=0.15, wind_strength=0.2,
        seconds_since_last_loose=t - 30.0, current_bow="BOW_POLISHED",
    )


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    conductor = BowConductor()
    now = 0.0
    log_lines: list[str] = []
    report: list[dict] = []
    t = 0.0
    while t < 40.0:
        beat, state = beat_state(t)
        state.provenance = "scenario"
        dec = conductor.evaluate(state, now=now)
        hud = format_hud(dec)
        log_lines.append(f"[t={t:05.1f}s {beat}] src={dec.source}")
        log_lines.append(hud)
        log_lines.append("")
        report.append({
            "t": round(t, 1), "beat": beat, "source": dec.source,
            "reason": dec.reason,
            "bow": {"choice": dec.bow.choice,
                    "confidence": round(dec.bow.confidence, 3),
                    "probabilities": {k: round(v, 3)
                                      for k, v in dec.bow.probabilities.items()},
                    "displayed": conductor.current,
                    "switched": dec.switched},
            "loose": dec.loose, "loose_p": dec.loose_probability,
        })
        print(f"[t={t:05.1f}s {beat}]")
        print(hud)
        print("")
        t += STEP
        now += STEP
    with open(os.path.join(here, "bow_capture_log.txt"), "w") as f:
        f.write("\n".join(log_lines))
    with open(os.path.join(here, "bow_capture_report.json"), "w") as f:
        json.dump({"evaluations": report}, f, indent=2)
    print(f"wrote bow_capture_log.txt + bow_capture_report.json ({len(report)} evals)")


if __name__ == "__main__":
    main()
