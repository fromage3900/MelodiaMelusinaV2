#!/usr/bin/env python3
"""Assertions for Tools/front_door_health.py. No editor required."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import front_door_health as fdh  # noqa: E402

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


def test_forbidden_current_status() -> None:
    bad_scope = "**Current status:** **10/10 P0 Completion Gates PASS | Preflight Ready**\n"
    good_scope = "**Current status:** **8/8 active P0 gates PASS** in `Docs/P0_TASK_LEDGER.json`.\n"
    hist = "Historical completion-gate taxonomy (10 IDs)\n"
    pattern = fdh.FORBIDDEN_CURRENT_CLAIMS[0][1]
    check("10/10 current status is forbidden", bool(pattern.search(bad_scope)))
    check("8/8 current status is allowed", not pattern.search(good_scope))
    check("historical 10 IDs vocabulary is allowed", not pattern.search(hist))


def test_todo_unrun_proofs() -> None:
    restart = fdh.FORBIDDEN_CURRENT_CLAIMS[3][1]
    package = fdh.FORBIDDEN_CURRENT_CLAIMS[4][1]
    check(
        "unchecked restart proof is forbidden",
        bool(restart.search("- [ ] Run full process restart proof.\n")),
    )
    check(
        "unchecked package proof is forbidden",
        bool(package.search("- [ ] Run packaged-build proof\n")),
    )
    check(
        "recorded restart evidence is allowed",
        not restart.search("- wardrobe restore after full editor process restart\n"),
    )


def test_current_state_divergence() -> None:
    pattern = fdh.FORBIDDEN_CURRENT_CLAIMS[2][1]
    active = "**`main` and `origin/main` are diverged lineages** (stale)\n"
    historical = "**Historical Sep 4 snapshot — superseded Sep 9.** At the time, local `main` and `origin/main` were diverged lineages.\n"
    check("active CURRENT_STATE divergence is forbidden", bool(pattern.search(active)))
    check("historical divergence wording is allowed", not pattern.search(historical))


def test_ledger_divergence() -> None:
    live = "origin/main is a diverged lineage and does NOT."
    reconciled = (
        "Reconciled 2026-09-08: this repository's main matches origin/main. "
        "The 2026-09-04 local-vs-origin divergence note is historical."
    )
    check("live divergence sentence matches", bool(fdh.LEDGER_ACTIVE_DIVERGENCE.search(live)))
    check(
        "reconciled ledger text is not an active-divergence fail",
        not (
            fdh.LEDGER_ACTIVE_DIVERGENCE.search(reconciled)
            and "Reconciled" not in reconciled
        ),
    )


def test_stub_banner() -> None:
    stub = "# HISTORICAL — not current project status\n\nThis root copy is a stub.\n"
    live = "# Art Director Review — Environment Portfolio Platform\n"
    check("HISTORICAL banner counts as stub", "HISTORICAL" in fdh.first_content_line(stub).upper())
    check("live review title is not a stub", "HISTORICAL" not in fdh.first_content_line(live).upper())


def test_live_repo_contradictions() -> None:
    fails = fdh.collect_fails(age=False)
    check("live repo has no contradiction FAILs", fails == [], str(fails))


def main() -> int:
    print("front-door health contract")
    test_forbidden_current_status()
    test_todo_unrun_proofs()
    test_current_state_divergence()
    test_ledger_divergence()
    test_stub_banner()
    test_live_repo_contradictions()
    total = passed + failed
    print(f"=== {passed}/{total} passed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
