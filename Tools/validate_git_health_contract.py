#!/usr/bin/env python3
"""Fail when the repository's Git-health enforcement contract drifts apart."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    ".githooks/pre-commit": [
        "Tools/agent_lane_registry.py guard",
        "Large files not tracked by Git LFS",
        "Protected files staged",
    ],
    ".githooks/pre-push": [
        "direct pushes to main are not allowed",
        "Tools/git_safe_push.py",
        "only refs/heads/* and refs/tags/* may be pushed",
    ],
    ".github/workflows/echo_gates.yml": [
        "Reject stale or retired feature branches",
        "LFS budget and pointer gates",
        "python Tools/lfs_health_audit.py --game-paths-only",
        "Project health scorecard (offline slice)",
    ],
    "Docs/Production/MULTI_AGENT_LANES.md": [
        "`main` is not a place you work",
        "refs/agents/<lane>",
        "30 minutes",
    ],
    "Docs/Production/GIT_HEALTH_CONTRACT.md": [
        "zero ambiguous integration state",
        "Offline static gates",
        "PR #201",
    ],
}

def main() -> int:
    failures = []
    for rel, needles in REQUIRED.items():
        path = ROOT / rel
        if not path.is_file():
            failures.append(f"missing required health surface: {rel}")
            continue
        text = path.read_text(encoding="utf-8-sig")
        lower = text.lower()
        for needle in needles:
            if needle.lower() not in lower:
                failures.append(f"{rel}: missing contract marker: {needle!r}")

    if failures:
        print("Git health contract: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(f"Git health contract: PASS ({len(REQUIRED)} enforcement surfaces aligned)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
