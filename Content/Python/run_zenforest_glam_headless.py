"""Headless launcher for ZenForestTest musical glam — editor MUST be closed.

Usage (from repo root, plain PowerShell or CI):

    python BS_GodFile/Content/Python/run_zenforest_glam_headless.py            # full glam + sequence
    python BS_GodFile/Content/Python/run_zenforest_glam_headless.py --dry-run  # audit-only writes
    python BS_GodFile/Content/Python/run_zenforest_glam_headless.py --audit    # post-run verify only

What it does:
  1. Refuses to run if UnrealEditor.exe is open (Error 32 file lock on .umap/.uasset).
  2. Stage A (-nullRHI): setup_zenforest_musical_glam.py  -> mats + Niagara actors + cams + PPV
  3. Stage B (-nullRHI): setup_zenforest_musical_sequence.py -> LS + MRQ preset
  4. Stage C: run_zenforest_hero_capture_cmd.py WITHOUT -nullRHI (RHI needed for PNGs) --skip-capture to omit
  5. Writes Saved/Logs/zenforest_glam_headless.log + Saved/Audit/zenforest_musical_*.json evidence.

Pattern follows proven project launchers:
  - run_editor_tasks_headless.py (refuse-if-editor-open guard)
  - run_portfolio_capture.py (two-stage sleep, RHI stage without nullrhi)
  - _Scripts/run_unreal.bat / run_unreal_bat (canonical Cmd invocation)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
UE_CMD = r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
UPROJECT = str(PROJECT_ROOT / "BS_GodFile" / "BS_GodFile.uproject")
PY_DIR = PROJECT_ROOT / "BS_GodFile" / "Content" / "Python"
LOG_DIR = PROJECT_ROOT / "BS_GodFile" / "Saved" / "Logs"
TIMEOUT_SEC = 900


def _editor_open() -> bool:
    for exe in ("UnrealEditor", "UnrealEditor-Cmd"):
        probe = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {exe}.exe"],
            capture_output=True, text=True,
        )
        if probe.returncode == 0 and exe.lower() in probe.stdout.lower():
            return True
    return False


def _run_ue(script: str, rhi: bool, log_name: str) -> tuple[int, str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / log_name
    cmd = [UE_CMD, UPROJECT, f"-ExecutePythonScript={script}", "-unattended", "-noP4",
           "-NOSOUND", "-stdout", "-nosplash", f"-log={log_path}"]
    if not rhi:
        cmd.insert(3, "-nullRHI")
    print(f"[GlamHeadless] launching: {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_SEC)
    tail = "\n".join((proc.stdout or "").splitlines()[-30:])
    if proc.returncode != 0:
        print(f"[GlamHeadless] FAILED rc={proc.returncode}\n{tail}", file=sys.stderr)
    else:
        print(f"[GlamHeadless] ok log={log_path}")
    return proc.returncode, tail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--skip-capture", action="store_true")
    args = ap.parse_args()

    if args.audit:
        rc, _ = _run_ue(str(PY_DIR / "audit_zenforest_musical.py"), rhi=False,
                        log_name="zenforest_audit.log")
        return rc

    if _editor_open():
        print("[GlamHeadless] REFUSED: UnrealEditor is open. Close it first "
              "(one editor rule; .umap is LFS lockable, Error 32 otherwise).", file=sys.stderr)
        return 2

    suffix = "_dryrun" if args.dry_run else ""
    glam = "setup_zenforest_musical_glam.py --dry-run" if args.dry_run else \
           "setup_zenforest_musical_glam.py"
    seq = "setup_zenforest_musical_sequence.py --dry-run" if args.dry_run else \
          "setup_zenforest_musical_sequence.py"

    rc_a, _ = _run_ue(glam, rhi=False, log_name=f"zenforest_glam{suffix}.log")
    if rc_a != 0:
        return rc_a
    time.sleep(3)

    rc_b, _ = _run_ue(seq, rhi=False, log_name=f"zenforest_seq{suffix}.log")
    if rc_b != 0:
        return rc_b
    time.sleep(3)

    if not args.dry_run and not args.skip_capture:
        # RHI stage: hero stills. No -nullRHI.
        rc_c, _ = _run_ue(str(PY_DIR / "run_zenforest_hero_capture_cmd.py"), rhi=True,
                          log_name="zenforest_capture.log")
        if rc_c != 0:
            return rc_c

    rc_d, _ = _run_ue("audit_zenforest_musical.py", rhi=False, log_name="zenforest_audit.log")
    print(f"[GlamHeadless] DONE dry_run={args.dry_run} capture={'skipped' if args.skip_capture or args.dry_run else 'ran'} final_audit_rc={rc_d}")
    return rc_d


if __name__ == "__main__":
    raise SystemExit(main())
