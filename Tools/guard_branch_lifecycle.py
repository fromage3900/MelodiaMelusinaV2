#!/usr/bin/env python3
"""Fail PRs whose branch base has drifted too far from current main.

This is intentionally a PR integration guard, not a history-rewrite tool.
Agents must reconverge bounded work onto a fresh branch from origin/main.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--max-behind", type=int, default=8)
    args = parser.parse_args()

    head_branch = os.environ.get("HEAD_BRANCH", "")
    retired = {
        "feature/spout-beauty-2026-09-26",
    }
    if head_branch in retired:
        print(f"ERROR: retired branch must never be reused: {head_branch}", file=sys.stderr)
        return 2

    try:
        merge_base = git("merge-base", args.base, "HEAD")
        behind = int(git("rev-list", "--count", f"{merge_base}..{args.base}"))
    except (subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR: unable to calculate branch divergence: {exc}", file=sys.stderr)
        return 2

    print(f"branch-lifecycle: head={head_branch or '(detached)'} base={args.base} behind={behind} max={args.max_behind}")
    if behind > args.max_behind:
        print(
            "ERROR: branch is too stale to integrate safely. "
            "Do not merge/rebase the long-lived lane or revive an old branch. "
            "Create a fresh branch from current origin/main and reconverge only the bounded intended delta.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
