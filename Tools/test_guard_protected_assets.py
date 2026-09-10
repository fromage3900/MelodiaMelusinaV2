#!/usr/bin/env python3
"""Assertions for Tools/guard_protected_assets.py."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import guard_protected_assets as gpa  # noqa: E402

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
    print("protected git assets contract")
    tracked = gpa.tracked_files()
    required = [
        "Content/EnvSandbox/Materials/Masters/M_Master_Nikki.uasset",
        "Content/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape.uasset",
        "Content/EnvSandbox/Materials/Masters/M_Master_Toon_Character.uasset",
    ]
    missing = gpa.check_required(required, tracked)
    ignored = gpa.check_not_ignored(required)
    check("Nikki character master is tracked", missing == [], str(missing))
    check("required masters are not gitignored", ignored == [], str(ignored))
    check(
        "known both-parent drop is detected on f19b6459",
        any("M_Master_Nikki.uasset" in item for item in gpa.both_parent_deletions("f19b6459")),
    )
    check(
        "non-merge commit is not scanned as a merge",
        gpa.both_parent_deletions("36663933") == [],
    )
    total = passed + failed
    print(f"=== {passed}/{total} passed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
