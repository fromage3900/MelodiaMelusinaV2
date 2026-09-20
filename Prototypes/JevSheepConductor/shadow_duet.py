"""LIVE JEV SHADOW DUET — bounded experiment 2.

Runs the 48s scripted sheep song through two arms on IDENTICAL state
snapshots. Neither arm controls anything; we measure directorial judgment.

  Arm A: classical fallback  (SheepConductor, live_enabled=False)
  Arm B: live Jev            (SheepConductor, live_enabled=True)

KEY SAFETY: TYPESAFE_API_KEY is read only from the environment, only to
construct the SDK client (inside jev_sheep_conductor._jev_ask). It is never
printed, logged, written to any artifact, or embedded in fixtures. If the
key is absent this script stops cleanly with exit 2 and writes NOTHING —
fallback output is never presented as Jev output.

Usage:
  python shadow_duet.py            # needs TYPESAFE_API_KEY in env
  python shadow_duet.py --selftest # no key needed; verifies metric math on
                                   # clearly-labeled SYNTHETIC decisions only

Artifacts (this folder only):
  live_shadow_capture_log.txt   side-by-side timeline, every evaluation
  live_shadow_report.json       full distributions + metrics (no secrets)
  LIVE_JEV_DUET_REVIEW.md       musical review + golden-question notes
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jev_sheep_conductor import (  # noqa: E402
    ChannelResult,
    Decision,
    SheepConductor,
)
from scenario_capture import STEP, beat_state  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DURATION = 48.0
LOW_CONF = 0.40
HIGH_CONF = 0.70

FLOCK_FAMILIES = {
    "calm": {"GRAZE", "CHORAL_SWAY", "RETURN_TO_IDLE"},
    "greet": {"TURN_TO_PLAYER", "PART_PATH"},
    "wind": {"FOLLOW_WIND"},
    "magic": {"SPIRAL_FORMATION", "RESONANCE_PULSE", "CRESCENDO_BURST"},
}
WORLD_FAMILIES = {
    "neutral": {"NONE", "SOFT_WIND"},
    "tint": {"LAVENDER_PALETTE", "FLOWER_HUE_SHIFT"},
    "peak": {"GOLD_CYMATICS", "RESONANCE_RIPPLE"},
}


def family(choice: str, table: dict[str, set[str]]) -> str:
    for name, members in table.items():
        if choice in members:
            return name
    return "unknown"


def state_summary(t: float, beat: str, st) -> str:
    return (
        f"beat={beat} dist={st.player_distance_m}m move={st.player_movement} "
        f"bpm={st.bpm_intensity} beatE={st.beat_energy} reso={st.resonance} "
        f"wind={st.wind_strength} pal={st.palette_state} "
        f"sslr={st.seconds_since_last_response}s interact={st.recent_interaction}"
    )


def classify_channel(fb_choice: str, jev: ChannelResult,
                     table: dict[str, set[str]]) -> str:
    """exact | compatible | disagree | lowconf. Disagreement is a label for
    review, never an automatic failure."""
    top_prob = jev.probabilities.get(jev.choice, 0.0)
    if jev.choice == fb_choice:
        return "exact"
    if top_prob < LOW_CONF:
        return "lowconf"
    if family(jev.choice, table) == family(fb_choice, table):
        return "compatible"
    return "disagree"


def top_alt(ch: ChannelResult) -> tuple[str, float]:
    if ch.alternates:
        return ch.alternates[0]
    return ("—", 0.0)


def run_duet() -> tuple[list[dict], dict]:
    """Drive both arms over identical snapshots. Returns (timeline, metrics).

    Raises SystemExit(2) if no key — before any evaluation or file write.
    """
    if not os.environ.get("TYPESAFE_API_KEY"):
        print("SHADOW DUET: no TYPESAFE_API_KEY in environment.")
        print("Live portion stopped cleanly — nothing was run, nothing written.")
        print("Set the key and re-run; arm A stays classical fallback.")
        raise SystemExit(2)

    arm_a = SheepConductor()
    arm_b = SheepConductor()
    timeline: list[dict] = []

    t = 0.0
    now = 0.0
    last_response_t = 0.0
    prev_flock_probe = "GRAZE"
    while t < DURATION:
        beat, state = beat_state(t, sslr=round(t - last_response_t, 1))
        state.provenance = "scenario"
        # Identical snapshot to both arms (evaluate() never mutates state).
        da = arm_a.evaluate(state, now=now, live_enabled=False)
        db = arm_b.evaluate(state, now=now, live_enabled=True)
        assert db.source == "jev-live", (
            f"t={t}: live arm did not return jev-live (got {db.source}); "
            "refusing to record non-Jev output as Jev output.")
        assert da.source == "classical-fallback"

        fa, wa = da.flock.choice, da.world.choice  # displayed (post-gate)
        jf, jw = db.flock.choice, db.world.choice
        jfp = db.flock.probabilities.get(jf, 0.0)
        jwp = db.world.probabilities.get(jw, 0.0)
        falt = top_alt(db.flock)
        walt = top_alt(db.world)
        # Alternates should never echo the displayed choice.
        if falt[0] == jf:
            cands = sorted(db.flock.probabilities.items(), key=lambda kv: kv[1],
                           reverse=True)
            falt = next(((c, p) for c, p in cands if c != jf), falt)
        if walt[0] == jw:
            cands = sorted(db.world.probabilities.items(), key=lambda kv: kv[1],
                           reverse=True)
            walt = next(((c, p) for c, p in cands if c != jw), walt)

        cf = classify_channel(fa, db.flock, FLOCK_FAMILIES)
        cw = classify_channel(wa, db.world, WORLD_FAMILIES)

        timeline.append({
            "t": round(t, 1), "beat": beat,
            "input": state_summary(t, beat, state),
            "fallback": {
                "flock": fa,
                "flock_prob": round(da.flock.probabilities.get(fa, 0.0), 3),
                "world": wa,
                "world_prob": round(da.world.probabilities.get(wa, 0.0), 3),
                "cand_flock": da.cand_flock, "cand_world": da.cand_world,
            },
            "jev": {
                "flock": jf, "flock_prob": round(jfp, 3),
                "flock_alt": falt[0], "flock_alt_prob": round(falt[1], 3),
                "world": jw, "world_prob": round(jwp, 3),
                "world_alt": walt[0], "world_alt_prob": round(walt[1], 3),
                "cand_flock": db.cand_flock, "cand_world": db.cand_world,
                "hysteresis_held_flock": db.cand_flock != jf,
                "hysteresis_held_world": db.cand_world != jw,
            },
            "comparison": {"flock": cf, "world": cw},
        })
        if arm_a.current_flock != prev_flock_probe:
            last_response_t = t
            prev_flock_probe = arm_a.current_flock
        t += STEP
        now += STEP
    return timeline, compute_metrics(timeline)


def compute_metrics(timeline: list[dict]) -> dict:
    n = len(timeline)
    fa = sum(1 for e in timeline if e["comparison"]["flock"] == "exact")
    wa = sum(1 for e in timeline if e["comparison"]["world"] == "exact")
    ja = sum(1 for e in timeline
             if e["comparison"]["flock"] == "exact"
             and e["comparison"]["world"] == "exact")
    jev_fconfs = [e["jev"]["flock_prob"] for e in timeline]
    jev_wconfs = [e["jev"]["world_prob"] for e in timeline]
    conf_list = (
        [(e["t"], "flock", e["jev"]["flock"], e["jev"]["flock_prob"])
         for e in timeline]
        + [(e["t"], "world", e["jev"]["world"], e["jev"]["world_prob"])
           for e in timeline]
    )
    conf_list.sort(key=lambda r: r[3])
    held_f = [e["t"] for e in timeline if e["jev"]["hysteresis_held_flock"]]
    held_w = [e["t"] for e in timeline if e["jev"]["hysteresis_held_world"]]
    high_dis = [
        {"t": e["t"], "channel": ch,
         "fallback": e["fallback"][ch], "jev": e["jev"][ch],
         "jev_prob": e["jev"][ch + "_prob"]}
        for e in timeline for ch in ("flock", "world")
        if e["comparison"][ch] == "disagree" and e["jev"][ch + "_prob"] >= HIGH_CONF
    ]
    # "Wanted earlier": first tick each arm's CANDIDATE left its opening pose.
    def first_cand_change(key: str, opening: str) -> object:
        for e in timeline:
            arm_key = "fallback" if key.startswith("fb") else "jev"
            ckey = "cand_flock" if "flock" in key else "cand_world"
            if e[arm_key][ckey] != opening:
                return e["t"]
        return None
    return {
        "n_evaluations": n,
        "flock_agreement": fa, "flock_agreement_rate": round(fa / n, 3),
        "world_agreement": wa, "world_agreement_rate": round(wa / n, 3),
        "joint_agreement": ja, "joint_agreement_rate": round(ja / n, 3),
        "jev_mean_flock_conf": round(sum(jev_fconfs) / n, 3),
        "jev_mean_world_conf": round(sum(jev_wconfs) / n, 3),
        "lowest_confidence": [
            {"t": t_, "channel": ch, "choice": c, "prob": p}
            for t_, ch, c, p in conf_list[:6]
        ],
        "hysteresis_held_flock_ticks": held_f,
        "hysteresis_held_world_ticks": held_w,
        "high_conf_disagreements": high_dis,
        "first_candidate_change": {
            "fallback_flock": first_cand_change("fb_flock", "GRAZE"),
            "jev_flock": first_cand_change("jev_flock", "GRAZE"),
            "fallback_world": first_cand_change("fb_world", "SOFT_WIND"),
            "jev_world": first_cand_change("jev_world", "SOFT_WIND"),
        },
    }


def write_log(timeline: list[dict]) -> str:
    out: list[str] = []
    for e in timeline:
        out.append(f"[t={e['t']:05.1f}s {e['beat']}] {e['input']}")
        f, j = e["fallback"], e["jev"]
        out.append(f"  FALLBACK flock={f['flock']} {f['flock_prob']:.2f} "
                   f"world={f['world']} {f['world_prob']:.2f}")
        out.append(f"  JEV      flock={j['flock']} {j['flock_prob']:.2f} "
                   f"(alt {j['flock_alt']} {j['flock_alt_prob']:.2f}) "
                   f"world={j['world']} {j['world_prob']:.2f} "
                   f"(alt {j['world_alt']} {j['world_alt_prob']:.2f})")
        c = e["comparison"]
        out.append(f"  COMPARE  flock={c['flock']} world={c['world']}")
        out.append("")
    return "\n".join(out)


BEAT_WINDOWS = {
    "ENTER_FIELD (quiet)": (0.0, 10.0),
    "APPROACH (greeting)": (10.0, 20.0),
    "WIND (drift)": (20.0, 30.0),
    "RESONANCE (peak)": (30.0, 40.0),
    "SETTLE (exhale)": (40.0, 48.0),
}


def write_review(timeline: list[dict], metrics: dict) -> str:
    L: list[str] = []
    L.append("# LIVE JEV SHADOW DUET — review")
    L.append("")
    L.append("48s scripted sheep song, identical snapshots to both arms. "
             "Neither arm controlled anything; this scores judgment only. "
             "Disagreement is flagged for musical review, never auto-failed.")
    L.append("")
    L.append("## Agreement")
    L.append("")
    L.append(f"- flock: {metrics['flock_agreement']}/{metrics['n_evaluations']} "
             f"({metrics['flock_agreement_rate']})")
    L.append(f"- world: {metrics['world_agreement']}/{metrics['n_evaluations']} "
             f"({metrics['world_agreement_rate']})")
    L.append(f"- joint: {metrics['joint_agreement']}/{metrics['n_evaluations']} "
             f"({metrics['joint_agreement_rate']})")
    L.append(f"- Jev mean winning confidence: "
             f"flock {metrics['jev_mean_flock_conf']}, "
             f"world {metrics['jev_mean_world_conf']}")
    L.append(f"- first candidate change: {metrics['first_candidate_change']}")
    L.append(f"- hysteresis held Jev flock at ticks: "
             f"{metrics['hysteresis_held_flock_ticks'] or 'none'}")
    L.append(f"- hysteresis held Jev world at ticks: "
             f"{metrics['hysteresis_held_world_ticks'] or 'none'}")
    L.append("")
    L.append("## Five beats")
    L.append("")
    for name, (lo, hi) in BEAT_WINDOWS.items():
        L.append(f"### {name}")
        for e in timeline:
            if lo <= e["t"] < hi:
                f, j, c = e["fallback"], e["jev"], e["comparison"]
                L.append(
                    f"- t={e['t']:.0f}s fb={f['flock']}/{f['world']} "
                    f"jev={j['flock']} {j['flock_prob']:.2f}/"
                    f"{j['world']} {j['world_prob']:.2f} "
                    f"[{c['flock']}/{c['world']}]")
        L.append("")
    L.append("## Lowest-confidence Jev decisions (re-listen first)")
    L.append("")
    for r in metrics["lowest_confidence"]:
        L.append(f"- t={r['t']}s {r['channel']} {r['choice']} {r['prob']}")
    L.append("")
    L.append("## High-confidence disagreements (golden-question candidates)")
    L.append("")
    if metrics["high_conf_disagreements"]:
        for r in metrics["high_conf_disagreements"]:
            L.append(f"- t={r['t']}s {r['channel']}: fallback {r['fallback']} "
                     f"vs Jev {r['jev']} ({r['jev_prob']})")
    else:
        L.append("- none")
    L.append("")
    L.append("## Golden question")
    L.append("")
    L.append("_Does Jev ever make the arc feel more alive than the "
             "deterministic composer? Preserve those moments here on review._")
    return "\n".join(L)


def main() -> None:
    if "--selftest" in sys.argv:
        run_selftest()
        return
    timeline, metrics = run_duet()  # exits 2 with no writes if key absent
    with open(os.path.join(HERE, "live_shadow_capture_log.txt"), "w") as f:
        f.write(write_log(timeline))
    with open(os.path.join(HERE, "live_shadow_report.json"), "w") as f:
        json.dump({"evaluations": timeline, "metrics": metrics}, f, indent=2)
    with open(os.path.join(HERE, "LIVE_JEV_DUET_REVIEW.md"), "w") as f:
        f.write(write_review(timeline, metrics))
    print(f"duet complete: {len(timeline)} evals | "
          f"flock agree {metrics['flock_agreement_rate']} | "
          f"world agree {metrics['world_agreement_rate']} | "
          f"joint {metrics['joint_agreement_rate']}")


def _synth(choice: str, prob: float, options: list[str]) -> ChannelResult:
    rest = (1.0 - prob) / (len(options) - 1)
    dist = {o: (prob if o == choice else rest) for o in options}
    alts = sorted(((o, p) for o, p in dist.items() if o != choice),
                  key=lambda kv: kv[1], reverse=True)
    return ChannelResult(choice, dist, prob, alts)


def run_selftest() -> None:
    """Verify classify/metric math on SYNTHETIC decisions. No backend, no key,
    nothing here is Jev output and nothing is written to report artifacts."""
    from jev_sheep_conductor import FLOCK_OPTIONS, WORLD_OPTIONS
    F = list(FLOCK_OPTIONS)
    W = list(WORLD_OPTIONS)
    assert classify_channel("GRAZE", _synth("GRAZE", 0.5, F), FLOCK_FAMILIES) == "exact"
    assert classify_channel("GRAZE", _synth("CHORAL_SWAY", 0.6, F), FLOCK_FAMILIES) == "compatible"
    assert classify_channel("GRAZE", _synth("SPIRAL_FORMATION", 0.8, F), FLOCK_FAMILIES) == "disagree"
    assert classify_channel("GRAZE", _synth("SPIRAL_FORMATION", 0.2, F), FLOCK_FAMILIES) == "lowconf"
    assert classify_channel("NONE", _synth("GOLD_CYMATICS", 0.9, W), WORLD_FAMILIES) == "disagree"
    tl = [{
        "t": 0.0, "beat": "X", "input": "synthetic",
        "fallback": {"flock": "GRAZE", "flock_prob": 0.5, "world": "NONE",
                     "world_prob": 0.5, "cand_flock": "GRAZE",
                     "cand_world": "NONE"},
        "jev": {"flock": "GRAZE", "flock_prob": 0.5, "flock_alt": "X",
                "flock_alt_prob": 0.1, "world": "NONE", "world_prob": 0.5,
                "world_alt": "Y", "world_alt_prob": 0.1,
                "cand_flock": "GRAZE", "cand_world": "NONE",
                "hysteresis_held_flock": False, "hysteresis_held_world": False},
        "comparison": {"flock": "exact", "world": "exact"},
    }]
    m = compute_metrics(tl)
    assert m["joint_agreement_rate"] == 1.0, m
    assert m["first_candidate_change"]["fallback_flock"] is None, m
    log = write_log(tl)
    assert "FALLBACK" in log and "COMPARE" in log
    print("selftest: all synthetic checks passed (no live backend touched)")


if __name__ == "__main__":
    main()
