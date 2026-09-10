#!/usr/bin/env python3
"""Deadline git check. Seconds, not a research day.

    python Tools/git_ok.py

If this prints OK, git is not the task. Do not reconstruct merge history,
do not run ``git_health_audit.py``, do not write a git report.

If it FAILs, fix the printed lines only.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import guard_protected_assets as gpa  # noqa: E402


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def ref_exists(name: str) -> bool:
    return git("rev-parse", "--verify", "--quiet", name).returncode == 0


def main() -> int:
    branch = git("branch", "--show-current").stdout.strip() or "detached"
    dirty = len([line for line in git("status", "--porcelain").stdout.splitlines() if line])
    base = "origin/main" if ref_exists("origin/main") else ""
    ahead = behind = 0
    if base:
        counts = git("rev-list", "--left-right", "--count", f"{base}...HEAD").stdout.strip()
        if "\t" in counts:
            behind_s, ahead_s = counts.split("\t", 1)
            behind, ahead = int(behind_s), int(ahead_s)

    print(f"git_ok  branch={branch}  dirty={dirty}  ahead={ahead} behind={behind}", flush=True)

    required = list(
        json.loads(gpa.MANIFEST.read_text(encoding="utf-8")).get("required_paths") or []
    )
    fails = gpa.check_required(required, gpa.tracked_files())
    fails.extend(gpa.check_not_ignored(required))
    if base:
        fails.extend(gpa.check_merges(base))

    if fails:
        print("FAIL  protected assets")
        for item in fails:
            print(f"  - {item}")
    else:
        print(f"OK    protected assets ({len(required)})")

    lfs_fail = False
    if base:
        lfs = subprocess.run(
            [
                sys.executable,
                str(HERE / "git_safe_push.py"),
                "--check-only",
                "--auto-limit",
                "--range",
                f"{base}..HEAD",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        lfs_fail = lfs.returncode != 0
        summary = next(
            (line for line in (lfs.stdout or "").splitlines() if line.startswith("LFS ")),
            (lfs.stdout or "").strip().splitlines()[-1] if (lfs.stdout or "").strip() else "LFS budget",
        )
        print(("FAIL  " if lfs_fail else "OK    ") + summary)
        if lfs_fail and lfs.stderr:
            print(lfs.stderr.strip())
    else:
        print("OK    LFS budget skipped (no origin/main)")

    if fails or lfs_fail:
        print("git_ok: FAIL")
        print("Fix the FAIL lines only. Do not reconstruct merge history.")
        return 1
    print("git_ok: OK")
    print("Stop. Do not investigate git.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
