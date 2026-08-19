#!/usr/bin/env python3
"""
Overnight Persona PIE Loop — core gameplay loop screenshots + tests.

Runs continually tonight: every PIE task for the core persona loop,
captures screenshots, checks logs, and reports.

Core loop tested: Quill dialogue → encounter → battle (Melusina) → result → Quill resume → exploration + persona stats/save

Usage:
  python Tools/overnight_persona_pie_loop.py --once          # single pass
  python Tools/overnight_persona_pie_loop.py --loop          # loop until Ctrl+C
  python Tools/overnight_persona_pie_loop.py --loop --interval 300  # loop every 5min

Launches detached overnight via:
  setsid -f python Tools/overnight_persona_pie_loop.py --loop --interval 600 </dev/null >>/tmp/persona_loop.log 2>&1
"""
import time, json, datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pie_smoke_runner import PieSmokeRunner

PROJECT_DIR = Path(__file__).resolve().parent.parent
SAVED_DIR = PROJECT_DIR / "Saved" / "PersonaLoop_Tonight"
SAVED_DIR.mkdir(parents=True, exist_ok=True)

# ---- PIE tasks for core persona loop (Foundation Gates + persona) ----
# Each entry: (map, duration, capture_interval, name_suffix, sample_vars)
PIE_TASKS = [
    # 1. Widget runtime gate (P0) — which BP_BattleUI is active
    ("/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap", 12, 0.5, "widget_runtime", None),
    # 2. Persona exploration — stats read/write, save
    ("/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap", 15, 0.5, "persona_exploration", ["GroundSpeed", "bIsMoving"]),
    # 3. Battle controller parity — attack/skill/item/flee
    ("/Game/TurnBasedJRPGTemplate/Maps/BattleTestMap", 15, 0.25, "battle_parity", None),
    # 4. Save/load canonical slot
    ("/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap", 10, 0.5, "save_load", None),
]

def wait_for_monolith(timeout=120):
    import urllib.request, json
    url = "http://127.0.0.1:9316/mcp"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"monolith_status","arguments":{}}}).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status == 200:
                    return True
        except:
            pass
        time.sleep(2)
    return False

def run_once(iteration=0):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n=== Persona PIE Loop iteration {iteration} @ {ts} ===")
    if not wait_for_monolith(timeout=30):
        print("[Loop] Monolith 9316 not ready — skipping this iteration (UE still starting?)")
        return False
    results = []
    for map_path, duration, interval, suffix, sample_vars in PIE_TASKS:
        out = SAVED_DIR / f"{ts}_iter{iteration}_{suffix}"
        name = f"persona_{suffix}_{ts}"
        print(f"  → {suffix}: {map_path} ({duration}s, capture {interval}s) → {out}")
        try:
            kwargs = dict(map_path=map_path, duration=duration, output_dir=str(out), capture_interval=interval, test_name=name)
            if sample_vars:
                kwargs["sample_vars"] = sample_vars
            r = PieSmokeRunner(**kwargs)
            r.start()
            res = r.poll_until_complete()
            # Server completion status is "complete" (pie_smoke_runner.py:187);
            # "completed" never matches and would report every run as FAIL.
            ok = res.get("status") == "complete"
            print(f"     {'PASS' if ok else 'FAIL'} — frames:{len(r.captured_frames)} elapsed:{res.get('elapsed_seconds', '?')}s")
            results.append((suffix, ok, str(out)))
            # quick screenshot count
            pngs = list(out.glob("*.png")) + list(out.glob("**/*.png"))
            print(f"     screenshots: {len(pngs)}")
        except Exception as e:
            print(f"     ERROR: {e}")
            results.append((suffix, False, str(out)))
        time.sleep(2)  # cool down between PIEs
    # summary
    summary = SAVED_DIR / f"{ts}_iter{iteration}_SUMMARY.json"
    summary.write_text(json.dumps({"time": ts, "iteration": iteration, "results": results}, indent=2))
    print(f"[Loop] Summary → {summary}")
    return all(ok for _, ok, _ in results)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="single pass then exit")
    ap.add_argument("--loop", action="store_true", help="loop continually")
    ap.add_argument("--interval", type=int, default=600, help="seconds between loop iterations (default 600)")
    args = ap.parse_args()
    if args.once:
        run_once(0)
        return
    if args.loop:
        i = 0
        while True:
            run_once(i)
            i += 1
            print(f"[Loop] sleeping {args.interval}s until next iteration...")
            time.sleep(args.interval)
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
