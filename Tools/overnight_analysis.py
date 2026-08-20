#!/usr/bin/env python3
"""overnight_analysis.py — unattended Bedrock analysis passes into Saved/Overnight/.

READ THIS FIRST, BECAUSE IT DETERMINES WHAT THIS CAN HONESTLY DO
================================================================
This does **not** close gates, and it cannot. `model_router.py chat` is a single-shot
text call: the models have no tools, no filesystem, no editor, no repo. They reason over
context this script pastes in and return text.

The two remaining completion gates cannot be closed by a text model at all:

  repeat_consume  -> needs a runtime replay of an authored beat across a save/reload
  package_launch  -> needs a cook that reaches archive, then a real launch

Both are session-bound and need the editor or a successful cook. Anything claiming
otherwise overnight would be exactly the failure this project has already paid for:
prose asserting a state the evidence contradicts.

What this DOES do is make the morning fast. It produces written analysis -- a plan, a
review, a triage -- so that a human sitting down with the editor executes rather than
investigates. Output is advisory. **Nothing here is evidence, and this script never
writes to Saved/gate_ledger.json.**

Usage
-----
    AWS_PROFILE=bedrock python Tools/overnight_analysis.py            # all tasks
    AWS_PROFILE=bedrock python Tools/overnight_analysis.py --task cook
    python Tools/overnight_analysis.py --list

Schedule it (Windows), running once at 02:00:
    schtasks /create /tn MelodiaOvernight /sc once /st 02:00 ^
      /tr "cmd /c set AWS_PROFILE=bedrock&& python C:\\EnvironmentPortfolio\\BS_GodFile\\Tools\\overnight_analysis.py"

Cost: at these context sizes a full pass is a few cents. The $25 budget alarm
(`melodia-monthly-guard`) is the backstop.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Saved" / "Overnight"
ROUTER = ROOT / "Tools" / "model_router.py"

HEADER = """You are assisting an unattended overnight analysis pass on a UE 5.8 game project.

CRITICAL RULES:
- You have NO tools and NO repo access. Reason only over the context pasted below.
- Where you need a fact that was not given, write "NEED: <the fact>" instead of guessing.
  A confident wrong answer costs more than an admitted gap.
- Your output is a plan for a human, not evidence. Do not describe anything as verified,
  passing or done.
"""


def _read(rel: str, limit: int = 14000) -> str:
    p = ROOT / rel
    if not p.exists():
        return f"[missing: {rel}]"
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError as exc:
        return f"[unreadable: {rel}: {exc}]"


def _sh(*args) -> str:
    try:
        r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=120)
        return (r.stdout or r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"[command failed: {exc}]"


def task_repeat_consume() -> tuple[str, str]:
    ctx = (_read("Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.cpp", 20000)
           + "\n\n--- types ---\n"
           + _read("Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeTypes.h", 6000))
    return "deep", f"""{HEADER}
GOAL: produce the exact manual test procedure to close the `repeat_consume` gate.

Contract: `melodia:stat:<IntentId>:<StatId>:<Delta>` must be idempotent per **IntentId**
(not per StatId), recorded in FMelodiaNarrativeRecord::ConsumedIntentIds, and must survive
a save/load round trip so replaying an authored beat after a reload is a no-op.

A prior reading found the code likely correct: ConsumedIntentIds is SaveGame-flagged and
the key is built from IntentId. Your job is NOT to re-review the code. It is to write the
runtime procedure that PROVES it, as numbered steps a human executes in PIE.

For each step give: the action, and the exact observable (log line, on-screen value, or
save-file field) that distinguishes pass from fail. Include the negative case -- what a
double-consume would look like -- so the tester can recognise failure rather than assuming
success. End with the one step most likely to be skipped.

--- SOURCE ---
{ctx}
"""


def task_cook() -> tuple[str, str]:
    log = ""
    for cand in ("Saved/Logs/BS_GodFile.log", "Saved/Logs/BS_GodFile_2.log"):
        p = ROOT / cand
        if p.exists():
            log = p.read_text(encoding="utf-8", errors="replace")[-18000:]
            log = log.encode("ascii", "replace").decode("ascii")
            break
    return "cpp", f"""{HEADER}
GOAL: triage a UE 5.8 cook that exited with code -1 during GLOBAL SHADER COMPILATION.
No archive was produced. The game executable linked fine (518/518 actions); the failure is
cook-side only.

Find the FIRST REAL error -- not the first line containing the word "error", which in UE
cook logs is usually a warning cascade from an earlier root cause.

Known environment facts:
- Zen DDC is configured as Zen=(Type=Zen,LocalPath=G:\\UE_DDC\\Zen,Server=127.0.0.1:8558)
- The Zen server IS listening on 8558, but G:\\UE_DDC\\Zen DOES NOT EXIST (G:\\UE_DDC is empty)
- Disk is not the issue: C: 51.8 GB free, G: 159.5 GB free
- A previous run failed on locked VRM4U DLLs held by UnrealEditor.exe; that was resolved

Return: (1) the most probable root cause with your confidence, (2) the specific evidence in
the log that supports it, (3) the single next diagnostic command to run, (4) whether the
missing DDC LocalPath is plausibly causal or a red herring, argued either way.

--- LOG TAIL ---
{log or "[no log captured]"}
"""


def task_rhythm() -> tuple[str, str]:
    return "deep", f"""{HEADER}
GOAL: a calibration and tuning procedure for a rhythm battle the owner describes as
"working but clunky, needs timing polish".

Known values:
- PerfectWindowMs = 90.0, GreatWindowMs = 120.0, GoodWindowMs = 160.0, LatencyOffsetMs = 0.0
  (MelodiaCoreRulesLibrary.h:37-50)
- UMelodiaMusicClockSubsystem::CalibrationOffsetMs defaults to 0.0 and is applied to every
  timing measurement via GetTimingErrorMsToNearestBeat()
- Input is Q/W/O/P through BP_BattleUI::OnKeyDown, verified working in play
- Music is 128 BPM driven by a Harmonix MIDI beat grid
- No DA_MelodiaRhythmProfile asset exists; windows are struct defaults per component

Produce: (1) a concrete procedure for measuring this machine's actual audio+display latency
and deriving a CalibrationOffsetMs, using only what is in the game; (2) whether an
uncalibrated 0.0 offset would present as "clunky" and how that differs symptomatically from
windows being too tight; (3) a recommended starting window set for a 128 BPM game aimed at
players who are not rhythm-game specialists, with reasoning; (4) the order to change things
in, changing ONE variable at a time.
"""


def task_ledger() -> tuple[str, str]:
    return "audit", f"""{HEADER}
GOAL: find contradictions between the evidence ledger and project prose.

LEDGER (authoritative):
{_sh(sys.executable, str(ROOT / "Tools" / "record_gate.py"), "--list")}

PROSE:
{_read("_TASK_QUEUE.md", 9000)}

Report ONLY contradictions: a gate the ledger says passed but the prose calls open, or the
reverse. Quote both sides. The ledger always wins. Flag anywhere prose collapses "structure
verified" into "runtime verified" -- they are different claims. If there are none, say so
plainly rather than manufacturing findings.
"""


TASKS = {
    "repeat_consume": task_repeat_consume,
    "cook": task_cook,
    "rhythm": task_rhythm,
    "ledger": task_ledger,
}


def run(name: str) -> int:
    cls, prompt = TASKS[name]()
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    dest = OUT / f"{name}_{stamp}.md"

    print(f"[overnight] {name} -> class={cls}")
    # encoding/errors are explicit: text=True decodes as cp1252 on Windows, and UE
    # log tails contain bytes that are not valid cp1252 -- that raised
    # UnicodeDecodeError mid-capture and left stdout as None. Both guarded.
    try:
        r = subprocess.run([sys.executable, str(ROUTER), "chat", cls, "--prompt", prompt],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900)
        body = (r.stdout or "").strip() or (r.stderr or "").strip()
        code = r.returncode
    except Exception as exc:  # noqa: BLE001
        body, code = f"[runner error: {exc}]", 1
    dest.write_text(
        f"# Overnight analysis — {name}\n\n"
        f"Generated {stamp} · router class `{cls}`\n\n"
        "> **Advisory only.** Produced by a single-shot text model with no repo access.\n"
        "> This is a plan for a human, not evidence. No gate is closed by this file.\n\n"
        "---\n\n" + body + "\n", encoding="utf-8")
    print(f"[overnight] wrote {dest} ({len(body)} chars, exit {code})")
    return 0 if body and not body.startswith("[runner error") else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--task", choices=sorted(TASKS), help="run one task (default: all)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for k in sorted(TASKS):
            print(" ", k)
        return 0
    if not os.environ.get("AWS_PROFILE") and not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        print("warning: neither AWS_PROFILE nor AWS_BEARER_TOKEN_BEDROCK is set; "
              "the router will fall through to non-Bedrock lanes.", file=sys.stderr)
    names = [a.task] if a.task else sorted(TASKS)
    # Independent tasks: one failure must not abort the remaining passes,
    # which is the whole point of an unattended run.
    results = []
    for n in names:
        try:
            results.append(run(n))
        except Exception as exc:  # noqa: BLE001
            print(f"[overnight] {n} FAILED: {exc}", file=sys.stderr)
            results.append(1)
    return max(results) if results else 1


if __name__ == "__main__":
    sys.exit(main())
