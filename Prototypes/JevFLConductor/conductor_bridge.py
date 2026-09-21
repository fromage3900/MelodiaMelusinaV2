"""External Jev x FL Studio bridge process.

This process owns TYPESAFE_API_KEY (environment ONLY — it is never
printed, logged, or written anywhere) and runs the phrase-boundary loop:

  poll FL transport -> phrase start? -> snapshot -> Jev ask -> hysteresis
  -> authored preset (mixer mutes on whitelisted stem tracks) -> HUD + log

Allowed FL writes: mixer_set_mute on whitelisted stem tracks, and nothing
else. No tempo, no plugins, no patterns, no clips, no save. HOLD sends
zero commands. --dry-run sends zero commands and still logs everything.

Usage:
  python conductor_bridge.py --cue jev_fl_cue.json
  python conductor_bridge.py --cue jev_fl_cue.json --dry-run --once
  python conductor_bridge.py --cue jev_fl_cue.json --max-phrases 16

Live Jev needs TYPESAFE_API_KEY in this process's environment. Without
it the loop runs on the labeled classical fallback (NOT Jev evidence).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fl_snapshot import (  # noqa: E402
    EnergyTracker,
    bar_of,
    read_group_active,
    read_peaks,
    read_transport,
)
from jev_fl_conductor import (  # noqa: E402
    ARRANGE_OPTIONS,
    FLConductor,
    FLPhraseState,
    format_hud,
)

STEM_KEYS = ("VOICE_OR_CHOIR", "RHYTHM", "ATMOSPHERE", "RESONANCE")


def load_cue(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate_cue(cue: dict) -> list[str]:
    """Return a list of problems (empty = valid)."""
    problems: list[str] = []
    groups = cue.get("stem_groups", {})
    for key in STEM_KEYS:
        if key not in groups:
            problems.append(f"missing stem group: {key}")
    whitelist: set[int] = set()
    for tracks in groups.values():
        whitelist.update(int(t) for t in tracks)
    presets = cue.get("presets", {})
    for opt in ARRANGE_OPTIONS:
        if opt not in presets:
            problems.append(f"missing preset: {opt}")
    for name, preset in presets.items():
        for t in list(preset.get("mute", [])) + list(preset.get("unmute", [])):
            if int(t) == cue.get("master_track", 0):
                problems.append(f"preset {name}: master track is never mutable")
            if int(t) not in whitelist:
                problems.append(f"preset {name}: track {t} outside whitelist")
    if cue.get("initial_preset", "HOLD") not in ARRANGE_OPTIONS:
        problems.append("initial_preset is not an authored choice")
    return problems


def section_at(cue: dict, bar: int) -> tuple[str | None, bool]:
    """(authored section name or None, near-ending flag)."""
    name = None
    for sec in cue.get("authored_sections", []):
        if sec.get("from_bar", 1) <= bar <= sec.get("to_bar", 0):
            name = sec.get("name")
    ending_bar = cue.get("ending_bar")
    ending = bool(ending_bar) and bar >= ending_bar - cue.get("phrase_bars", 2)
    return name, ending


def apply_preset(bridge, cue: dict, choice: str, dry_run: bool) -> list[dict]:
    """Send mixer mutes for an authored preset. Returns the command list
    (empty for HOLD). Raises on anything outside the whitelist."""
    preset = cue["presets"][choice]
    if choice == "HOLD":
        return []
    sent: list[dict] = []
    for t in preset.get("mute", []):
        sent.append({"cmd": "mixer_set_mute", "params": {"track": int(t), "mute": True}})
    for t in preset.get("unmute", []):
        sent.append({"cmd": "mixer_set_mute", "params": {"track": int(t), "mute": False}})
    if dry_run:
        return sent
    for c in sent:
        bridge.call(c["cmd"], c["params"])
    return sent


def open_bridge():
    from fl_studio_mcp.connection import get_bridge

    bridge = get_bridge()
    bridge.open()
    bridge.check_alive()
    return bridge


def run(args: argparse.Namespace) -> int:
    cue = load_cue(args.cue)
    problems = validate_cue(cue)
    if problems:
        print("CUE CONFIG REFUSED:")
        for p in problems:
            print(f"  - {p}")
        return 2

    phrase_bars = int(cue.get("phrase_bars", 2))
    beats_per_bar = int(cue.get("beats_per_bar", 4))
    stem_tracks = {k: [int(t) for t in v] for k, v in cue["stem_groups"].items()}
    master_track = int(cue.get("master_track", 0))

    log_fh = open(args.log, "a", encoding="utf-8") if args.log else None
    conductor = FLConductor(initial_preset=cue.get("initial_preset", "FULL_CHORUS"))
    energy = EnergyTracker()
    prev_decision = "HOLD"
    bars_since_change = 0
    last_phrase_bar: int | None = None
    phrases = 0

    if args.check_cue:
        print(f"cue OK: {cue.get('cue_name')} "
              f"({len(ARRANGE_OPTIONS)} presets, {len(stem_tracks)} stem groups)")
        return 0

    bridge = open_bridge()
    print(f"bridge live. cue={cue.get('cue_name')} "
          f"dry_run={args.dry_run} live_jev={bool(os.environ.get('TYPESAFE_API_KEY'))}")

    try:
        while True:
            t = read_transport(bridge)
            if not t["playing"]:
                if args.once:
                    print("transport stopped; --once has nothing to evaluate.")
                    return 0
                time.sleep(0.5)
                continue
            bar, beat_in_bar = bar_of(t["position_beats"], beats_per_bar)
            is_phrase_start = (bar - 1) % phrase_bars == 0
            if not is_phrase_start or bar == last_phrase_bar:
                time.sleep(0.2)
                continue
            last_phrase_bar = bar

            master_peak, stem_peaks = read_peaks(bridge, master_track, stem_tracks)
            group_active = read_group_active(bridge, stem_tracks)
            level, trend = energy.update(master_peak)
            section, ending = section_at(cue, bar)

            state = FLPhraseState(
                tempo_bpm=t["tempo_bpm"],
                bar=bar,
                beat_in_bar=beat_in_bar,
                playing=True,
                master_peak=master_peak,
                energy=level,
                energy_trend=trend,
                stem_peaks=stem_peaks,
                group_active=group_active,
                current_preset=conductor.current,
                previous_decision=prev_decision,
                bars_since_change=bars_since_change,
                authored_section=section,
                authored_ending=ending,
                provenance="fl-live",
            )
            decision = conductor.evaluate(state, live_enabled=not args.fallback_only)
            sent = apply_preset(bridge, cue, decision.arrangement.choice,
                                dry_run=args.dry_run)
            prev_decision = decision.arrangement.choice
            bars_since_change = 0 if decision.switched else bars_since_change + phrase_bars

            hud = format_hud(state, decision, decision.arrangement.choice)
            print(hud, flush=True)
            if log_fh:
                log_fh.write(json.dumps({
                    "bar": bar,
                    "tempo_bpm": state.tempo_bpm,
                    "energy": level,
                    "energy_trend": trend,
                    "stem_peaks": stem_peaks,
                    "group_active": group_active,
                    "section": section,
                    "choice": decision.arrangement.choice,
                    "probabilities": decision.arrangement.probabilities,
                    "confidence": decision.arrangement.confidence,
                    "source": decision.source,
                    "reason": decision.reason,
                    "switched": decision.switched,
                    "commands": sent if args.dry_run else [c["cmd"] for c in sent],
                    "dry_run": args.dry_run,
                }) + "\n")
                log_fh.flush()

            phrases += 1
            if args.once or (args.max_phrases and phrases >= args.max_phrases):
                return 0
    finally:
        if log_fh:
            log_fh.close()
        try:
            bridge.close()
        except Exception:
            pass
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Jev x FL Studio phrase bridge")
    ap.add_argument("--cue", required=True, help="cue config JSON path")
    ap.add_argument("--log", default="jev_fl_sidecar.jsonl",
                    help="sidecar log path (full distributions)")
    ap.add_argument("--dry-run", action="store_true",
                    help="evaluate + log, send zero mixer commands")
    ap.add_argument("--once", action="store_true",
                    help="evaluate one phrase boundary then exit")
    ap.add_argument("--max-phrases", type=int, default=0,
                    help="stop after N phrase evaluations (0 = run)")
    ap.add_argument("--fallback-only", action="store_true",
                    help="never call Jev; labeled classical fallback")
    ap.add_argument("--check-cue", action="store_true",
                    help="validate the cue config and exit (no FL needed)")
    return run(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
