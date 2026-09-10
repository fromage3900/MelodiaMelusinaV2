#!/usr/bin/env python3
"""Assertions for Tools/git_ok.py — must stay a seconds-long check."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  ok  {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {detail}")


def main() -> int:
    print("git_ok contract")
    source = (ROOT / "Tools/git_ok.py").read_text(encoding="utf-8")
    check("does not call git fsck", "fsck" not in source)
    check("does not call lfs fsck", "lfs fsck" not in source and '"lfs", "fsck"' not in source)
    completed = subprocess.run(
        [sys.executable, str(ROOT / "Tools/git_ok.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    check("git_ok exits 0 on this checkout", completed.returncode == 0, output[-800:])
    check("prints stop rule on success", "Stop. Do not investigate git." in output)
    total = passed + failed
    print(f"=== {passed}/{total} passed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
