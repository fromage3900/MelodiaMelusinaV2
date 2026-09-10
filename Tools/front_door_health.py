#!/usr/bin/env python3
"""front_door_health.py — keep git truth and current-status docs from drifting apart.

This does not rewrite CURRENT_STATE. It fails closed when the front door
contradicts git, or when production source moved and the score was not
refreshed. Agents and CI run it; a human (or a scoped agent) does the refresh.

    python Tools/front_door_health.py           # report + brief, exit 1 on FAIL
    python Tools/front_door_health.py --ci      # same, machine-readable
    python Tools/front_door_health.py --age     # also fail if source moved and
                                                # CURRENT_STATE was not refreshed
    python Tools/front_door_health.py --brief   # print commits the refresh must cover

Do not treat this as git archaeology. It does not merge branches or rewrite history.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FRONT_DOOR = (
    "AGENT_START_HERE.md",
    "CURRENT_STATE.md",
    "TODO.md",
    "_VERTICAL_SLICE_SCOPE.md",
    "REPOSITORY_AUTHORITY.md",
    "MELODIA_TECHNICAL_VERTICAL_SLICE.md",
    "Docs/Production/CANONICAL_PROJECT_PIPELINE_2026-09-08.md",
)

# Claims that already burned a session. Match only as *current* status, not
# historical vocabulary ("10 IDs", "historical PASS").
FORBIDDEN_CURRENT_CLAIMS = (
    ("_VERTICAL_SLICE_SCOPE.md", re.compile(r"(?im)^\*\*Current status:\*\*.*10/10")),
    (
        "CURRENT_STATE.md",
        re.compile(r"(?im)^\*\*Overall Status:\*\*.*10/10 P0 Completion Gates PASS"),
    ),
    (
        "CURRENT_STATE.md",
        re.compile(r"(?im)^\*\*`main` and `origin/main` are diverged lineages\*\*"),
    ),
    ("TODO.md", re.compile(r"\[ \] Run full process restart proof")),
    ("TODO.md", re.compile(r"\[ \] Run packaged-build proof")),
)

LEDGER_ACTIVE_DIVERGENCE = re.compile(
    r"origin/main is a diverged lineage and does NOT",
    re.I,
)

ROOT_STUB_NAMES = (
    "48H_CHANGE_REVIEW_2026-08-05.md",
    "_AUDIT_2026-08-05.md",
    "_INTAKE_REPORT_2026-07-26.md",
    "_ROADBLOCKS_2026-07-31.md",
    "ART_DIRECTOR_REVIEW.md",
)

WORK_PATHS = ("Source/", "Plugins/", "Content/Python/", "Docs/P0_TASK_LEDGER.json")
CANONICAL_REMOTE = "melodiamelusinav2"
BANNED_REMOTE = "environmentportfolio"


def git(*args: str, check: bool = False) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )
    return (proc.stdout or "").strip()


def read_text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def first_content_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def check_front_door_present() -> list[str]:
    fails = []
    for rel in FRONT_DOOR:
        if not (ROOT / rel).is_file():
            fails.append(f"missing front-door file: {rel}")
    return fails


def check_forbidden_claims() -> list[str]:
    fails = []
    for rel, pattern in FORBIDDEN_CURRENT_CLAIMS:
        text = read_text(rel)
        if text and pattern.search(text):
            fails.append(f"{rel}: forbidden current-status claim ({pattern.pattern})")
    return fails


def check_ledger_git_authority() -> list[str]:
    path = ROOT / "Docs/P0_TASK_LEDGER.json"
    if not path.is_file():
        return ["missing Docs/P0_TASK_LEDGER.json"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Docs/P0_TASK_LEDGER.json unparseable: {exc}"]
    authority = str(data.get("current_source_truth", {}).get("git_authority", ""))
    if LEDGER_ACTIVE_DIVERGENCE.search(authority) and "Reconciled" not in authority:
        return [
            "Docs/P0_TASK_LEDGER.json git_authority still claims origin/main is a live diverged lineage"
        ]
    return []


def check_root_stubs() -> list[str]:
    """If a known stale status title is back at repo root, it must be a HISTORICAL stub."""
    fails = []
    for name in ROOT_STUB_NAMES:
        path = ROOT / name
        if not path.is_file():
            continue
        line = first_content_line(path.read_text(encoding="utf-8", errors="replace"))
        if "HISTORICAL" not in line.upper():
            fails.append(
                f"{name}: leftover root status file is not a HISTORICAL stub"
            )
    return fails


def check_origin_remote() -> list[str]:
    url = git("remote", "get-url", "origin").lower()
    if not url:
        return ["git remote origin is missing"]
    fails = []
    if BANNED_REMOTE in url and "melodiamelusinav2" not in url:
        fails.append(f"origin points at deprecated EnvironmentPortfolio: {url}")
    if CANONICAL_REMOTE not in url:
        fails.append(f"origin is not fromage3900/MelodiaMelusinaV2: {url}")
    return fails


def check_age() -> list[str]:
    """Fail when production source moved after CURRENT_STATE was last committed."""
    state_hash = git("log", "-1", "--format=%h", "--", "CURRENT_STATE.md")
    if not state_hash:
        return ["CURRENT_STATE.md has no commit history"]
    newer = git(
        "log",
        "--oneline",
        f"{state_hash}..HEAD",
        "--",
        *WORK_PATHS,
    )
    if not newer.strip():
        return []
    first = newer.splitlines()[0]
    return [
        "CURRENT_STATE.md is behind production source. "
        f"Newest work not covered: {first}. Run with --brief and refresh the front door."
    ]


def refresh_brief(limit: int = 15) -> list[str]:
    state_hash = git("log", "-1", "--format=%h", "--", "CURRENT_STATE.md")
    if not state_hash:
        return ["CURRENT_STATE.md has no commit history"]
    lines = [
        f"CURRENT_STATE.md last commit: {state_hash}",
        f"Commits after that touching {', '.join(WORK_PATHS)}:",
    ]
    log = git(
        "log",
        "--oneline",
        f"-{limit}",
        f"{state_hash}..HEAD",
        "--",
        *WORK_PATHS,
    )
    if not log:
        lines.append("  (none — front door covers current source)")
    else:
        for row in log.splitlines():
            lines.append(f"  {row}")
    ahead_behind = git("rev-list", "--left-right", "--count", "origin/main...HEAD")
    if ahead_behind:
        behind, ahead = ahead_behind.split()
        lines.append(f"origin/main...HEAD: {behind} behind, {ahead} ahead")
    return lines


def collect_fails(*, age: bool) -> list[str]:
    fails: list[str] = []
    fails += check_front_door_present()
    fails += check_forbidden_claims()
    fails += check_ledger_git_authority()
    fails += check_root_stubs()
    fails += check_origin_remote()
    if age:
        fails += check_age()
    return fails


def main() -> int:
    parser = argparse.ArgumentParser(description="Front-door / git health gate")
    parser.add_argument("--ci", action="store_true", help="quiet FAIL/OK lines for CI")
    parser.add_argument(
        "--age",
        action="store_true",
        help="fail when Source/Plugins/Python moved after CURRENT_STATE",
    )
    parser.add_argument("--brief", action="store_true", help="print refresh brief")
    args = parser.parse_args()

    fails = collect_fails(age=args.age)
    if args.brief or fails:
        print("\n".join(refresh_brief()))
        print()
    if fails:
        print(f"[FAIL] front-door health ({len(fails)})")
        for item in fails:
            print(f"  - {item}")
        print("Refresh CURRENT_STATE.md / TODO.md / AGENT_START_HERE.md against those commits.")
        print("Do not invent a second status document.")
        return 1
    extra = " + age" if args.age else ""
    print(f"[OK] front-door health{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
