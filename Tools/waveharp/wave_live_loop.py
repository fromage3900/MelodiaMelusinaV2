"""The WaveHarp live loop - drive the editor through the bridge, in a loop.

This is the RiderLink surface used from outside Rider: the same Monolith bridge the
focused live-editor tests run over, driven by a script so the loop is repeatable.

Phases per iteration:
  0. the editor session and the world it is in
  1. PIE, then the form/chorus commands, then the receipts from the log
  2. the focused automation group, in the LIVE editor (not headless)
  3. stop PIE

Usage:
  C:/Python314/python.exe Tools/waveharp/wave_live_loop.py            (one iteration)
  C:/Python314/python.exe Tools/waveharp/wave_live_loop.py --loop 6  (keep going)
  C:/Python314/python.exe Tools/waveharp/wave_live_loop.py --discover
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Tools"))
from mcp_client import monolith_call  # noqa: E402

OUT = REPO / "Saved" / "Audit" / "waveharp"


def q(action, params=None, timeout=120):
    return monolith_call("editor_query", {"action": action, "params": params or {}}, timeout=timeout)


def call(name, args, timeout=120):
    return monolith_call(name, args, timeout=timeout)


def tail_log(pattern, limit=40, timeout=90):
    r = q("tail_log", {"pattern": pattern, "max_lines": limit}, timeout=timeout)
    return r


def console(command, timeout=60):
    return q("run_console_command", {"command": command}, timeout=timeout)


def automation(prefix, timeout=300):
    return q("run_automation_tests", {"prefix": prefix}, timeout=timeout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", type=int, default=1)
    ap.add_argument("--discover", action="store_true")
    ap.add_argument("--filter", default="Melodia.WaveHarp")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)

    if args.discover:
        d = call("monolith_discover", {"namespace": "editor", "detail": True}, timeout=120)
        text = json.dumps(d, indent=1) if not isinstance(d, str) else d
        for act in ("run_console_command", "run_automation_tests", "start_pie",
                    "stop_pie", "pie_inject_input_action", "tail_log", "run_python"):
            i = text.find('"%s"' % act)
            if i >= 0:
                print("--- %s\n%s\n" % (act, text[i:i + 700]))
        return 0

    results = {"iterations": []}
    for iteration in range(1, args.loop + 1):
        print("\n" + "=" * 70)
        print("ITERATION %d" % iteration)
        print("=" * 70)
        step = {"iteration": iteration, "at": time.strftime("%H:%M:%S")}

        # 0. the session
        health = call("monolith_discover", {"namespace": "editor"}, timeout=60)
        step["editor_reachable"] = bool(health) and "_error" not in str(health)[:200]
        print("  editor reachable:", step["editor_reachable"])

        # 1. PIE + the commands
        print("  start_pie:", q("start_pie", {}, timeout=180))
        time.sleep(6)

        for command in ("Melodia.WaveHarp.WaterChorus 1",
                        "Melodia.WaveHarp.HeadSwap 1",
                        "Melodia.WaveHarp.SetForm 2"):
            print("  %-34s -> %s" % (command, str(console(command, timeout=90))[:160]))
            time.sleep(1.5)

        time.sleep(4)
        print("  dump:", str(q("run_console_command", {"command": "Melodia.WaveHarp.DumpForm"},
                              timeout=90))[:400])

        receipts = tail_log("MELODIA_WATER_CHORUS|MELODIA_WAVEHARP_FORM|MELODIA_WAVEHARP_VFX|"
                            "MELODIA_WAVEHARP_CHORUS_TOGGLE|MELODIA_WAVEHARP_HEADSWAP", limit=60)
        step["receipts"] = receipts
        print("  receipts:", str(receipts)[:1500])

        # 2. the focused group, live
        step["automation"] = automation(args.filter)
        print("  automation:", str(step["automation"])[:600])

        # 3. stop
        print("  stop_pie:", q("stop_pie", {}, timeout=120))
        results["iterations"].append(step)
        time.sleep(3)

    stamp = time.strftime("%Y%m%d_%H%M%S")
    path = OUT / ("wave_live_loop_%s.json" % stamp)
    path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print("\nreceipt:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
