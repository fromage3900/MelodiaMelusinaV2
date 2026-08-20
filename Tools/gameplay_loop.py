#!/usr/bin/env python3
"""
Gameplay continuous loop - editor-gated verification with PIE recordings.
Runs static gates, PIE smoke, and gameplay task checks in a loop.
Editor must be on 9316 (Windows python only).
Usage:
  python Tools/gameplay_loop.py --interval 60 --pie-duration 10
  python Tools/gameplay_loop.py --once  (single iteration, for testing)
"""
import subprocess, sys, time, json, os
from pathlib import Path
from datetime import datetime

PROJECT = Path(__file__).resolve().parent.parent
USE_PY = "python"  # Windows python (caller should be Windows python)

def run(cmd, timeout=600):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT), timeout=timeout)
    out = (r.stdout or "") + ("\n" + r.stderr if r.stderr else "")
    return r.returncode, out.strip()

def step(name, fn):
    print(f"\n[STEP] {name}")
    try:
        ok, detail = fn()
        icon = "PASS" if ok else "FAIL"
        print(f"  [{icon}] {detail}")
        return ok, detail
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False, str(e)[:200]

def check_static():
    code, out = run([USE_PY, "Tools/echo_run.py", "run", "static_gates"], timeout=900)
    ok = code == 0 and "ALL OK" in out
    # tail
    tail = "\n".join(out.splitlines()[-8:])
    return ok, tail.replace("\r","")

def check_pie():
    # Smoke on L_KaleidoNave: first try idle smoke, then attempt Quill-triggered battle via narrative subsystem
    outdir = str(PROJECT / "Saved" / "PIE_Loop")
    code, out = run([USE_PY, "Tools/pie_smoke_runner.py", "--map", "/Game/EnvSandbox/Environments/L_KaleidoNave", "--duration", "10", "--output", outdir, "--name", f"loop_{datetime.now().strftime('%H%M%S')}"], timeout=400)
    ok = code == 0
    # Check if battle was attempted: look for battle logs in report
    battle_hint = "battle" in out.lower() or "encounter" in out.lower()
    tail = "\n".join(out.splitlines()[-6:])
    detail = tail.replace("\r","")[:500]
    if not battle_hint:
        detail += " | note: idle PIE never hits FirstDream_InteractionBattle volume (bIsMoving false); use playtest_harness.py run --map L_KaleidoNave for real Q/W/O/P battle test"
    return ok, detail

def check_tasks():
    # Verify Muse handoff tasks + static artifact existence
    tasks = []
    # M3 memory index
    exists = (PROJECT / "Saved" / "memory_index.json").exists()
    tasks.append(f"memory_index.json {'exists' if exists else 'missing'}")
    # M4 AGENTS split
    sz = (PROJECT / "AGENTS.md").stat().st_size if (PROJECT / "AGENTS.md").exists() else 0
    tasks.append(f"AGENTS.md {sz} bytes ({'OVER 32K' if sz>32768 else 'ok'})")
    # M5 surreal_arch
    untracked = len(list((PROJECT / "deploy" / "surreal_arch" / "melodia_gn").glob("*.py"))) if (PROJECT / "deploy" / "surreal_arch" / "melodia_gn").exists() else 0
    tasks.append(f"surreal_arch/melodia_gn {untracked} py files")
    # Loop health
    ok = True  # informational only
    return ok, "; ".join(tasks)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--pie-duration", type=int, default=10)
    ap.add_argument("--no-pie", action="store_true", help="skip PIE to run faster")
    args = ap.parse_args()

    iteration = 0
    while True:
        iteration += 1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("\n" + "="*60)
        print(f" Gameplay Loop iteration {iteration} — {now}")
        print("="*60)

        results = []
        # Always run static
        ok, det = step("static_gates", check_static)
        results.append(("static_gates", ok))
        # PIE (optional)
        if not args.no_pie:
            ok, det = step("pie_smoke L_KaleidoNave", check_pie)
            results.append(("pie_smoke", ok))
        else:
            print("\n[STEP] pie_smoke SKIPPED (--no-pie)")

        ok, det = step("task_checks", check_tasks)
        results.append(("task_checks", ok))

        # Summary
        passed = sum(1 for _,ok in results if ok)
        total = len(results)
        print(f"\n[SUMMARY] {passed}/{total} steps passed")
        # Write status
        status_path = PROJECT / "Saved" / "gameplay_loop_status.json"
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(json.dumps({
            "iteration": iteration,
            "time": now,
            "results": [{"name":n,"ok":ok} for n,ok in results],
            "passed": passed, "total": total
        }, indent=2), encoding="utf-8")
        print(f"Status: {status_path}")

        if args.once:
            break
        print(f"\nSleep {args.interval}s (Ctrl+C to stop)...")
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped.")
            break

if __name__ == "__main__":
    main()
