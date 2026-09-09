#!/usr/bin/env python3
"""Fail if canonical assets vanish, or if a merge deletes a file both parents still had.

Incident: f19b6459 dropped M_Master_Nikki.uasset (and 11 sibling materials)
even though both merge parents still contained them. Content/EnvSandbox/* then
hid the path from git add.

    python Tools/guard_protected_assets.py
    python Tools/guard_protected_assets.py --base origin/main
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specs/git/protected_git_assets.v1.json"


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return (proc.stdout or "").strip()


def tracked_files() -> set[str]:
    return {line for line in git("ls-files").splitlines() if line}


def check_required(required: list[str], tracked: set[str]) -> list[str]:
    return [f"protected asset missing from HEAD: {path}" for path in required if path not in tracked]


def check_not_ignored(required: list[str]) -> list[str]:
    """Fail if a required path matches gitignore even when untracked.

    ``f19b6459`` deleted masters that both parents still had; ``Content/EnvSandbox/*``
    then hid them from a normal ``git add``. Tracked files can still match ignore
    rules, so this uses ``--no-index``.
    """
    fails: list[str] = []
    for path in required:
        proc = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", path],
            cwd=ROOT,
            capture_output=True,
        )
        if proc.returncode == 0:
            fails.append(
                f"protected asset is gitignored (git add cannot restore it): {path}"
            )
    return fails


def path_in_tree(commit: str, path: str) -> bool:
    return (
        subprocess.run(
            ["git", "cat-file", "-e", f"{commit}:{path}"],
            cwd=ROOT,
            capture_output=True,
        ).returncode
        == 0
    )


def both_parent_deletions(merge: str) -> list[str]:
    parents = git("rev-parse", f"{merge}^1", f"{merge}^2").splitlines()
    if len(parents) < 2:
        return []
    deleted = git("diff", "--name-only", "--diff-filter=D", parents[0], merge).splitlines()
    fails = []
    for path in deleted:
        if path and path_in_tree(parents[0], path) and path_in_tree(parents[1], path):
            fails.append(
                f"merge {merge[:12]} deleted {path} even though both parents still had it"
            )
    return fails


def check_merges(base: str) -> list[str]:
    merges = git("rev-list", "--merges", f"{base}..HEAD").splitlines()
    fails: list[str] = []
    for merge in merges:
        fails.extend(both_parent_deletions(merge))
    return fails


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="", help="scan merges in BASE..HEAD for both-parent deletions")
    parser.add_argument("--manifest", default=str(MANIFEST))
    args = parser.parse_args()

    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    required = list(data.get("required_paths") or [])
    tracked = tracked_files()
    fails = check_required(required, tracked)
    fails.extend(check_not_ignored(required))
    if args.base:
        fails.extend(check_merges(args.base))

    if fails:
        print(f"[FAIL] protected git assets ({len(fails)})")
        for item in fails:
            print(f"  - {item}")
        print("Do not resolve this by ignoring the path. Restore the blob from a parent that still has it.")
        return 1
    print(f"[OK] protected git assets ({len(required)} required paths present)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
