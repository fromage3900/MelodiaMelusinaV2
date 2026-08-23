#!/usr/bin/env python3
"""Serial Git/LFS health audit for the shared BS_GodFile checkout.

This is intentionally read-only: it never stages, resets, cleans, fetches, or
pushes. Run without arguments for local health, then add ``--remote`` from a
normal user terminal before staging or pushing LFS assets.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
P0_ASSETS = (
    "Content/TurnBasedJRPGTemplate/Blueprints/EnemyExplorePawns/"
    "BP_EnemyExplorePawnBase.uasset",
    "Content/TurnBasedJRPGTemplate/Blueprints/EnemyExplorePawns/"
    "AggressiveEnemyExplorePawns/BP_AggressiveEnemyExplorePawnBase.uasset",
)
LFS_DISABLED = (
    "-c",
    "filter.lfs.smudge=",
    "-c",
    "filter.lfs.clean=",
    "-c",
    "filter.lfs.process=",
    "-c",
    "filter.lfs.required=false",
)


def run(label: str, *args: str, allowed: tuple[int, ...] = (0,)) -> bool:
    """Run one Git command at a time and report its bounded output."""
    completed = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    ok = completed.returncode in allowed
    state = "PASS" if ok else "FAIL"
    print(f"[{state}] {label}")
    output = completed.stdout.strip()
    if output:
        print(output)
    return ok


def verify_p0_asset(path: str) -> bool:
    """Assert that a reviewed P0 asset is eligible for LFS tracking."""
    ignored = subprocess.run(
        ("git", "check-ignore", "-q", "--", path),
        cwd=ROOT,
        check=False,
    )
    if ignored.returncode == 0:
        print(f"[FAIL] P0 asset is ignored: {path}")
        return False
    if ignored.returncode != 1:
        print(f"[FAIL] unable to inspect P0 ignore rule: {path}")
        return False

    attrs = subprocess.run(
        ("git", "check-attr", "filter", "lockable", "--", path),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    required = ("filter: lfs", "lockable: set")
    if attrs.returncode or not all(value in attrs.stdout for value in required):
        print(f"[FAIL] P0 asset lacks LFS/lockable attributes: {path}")
        if attrs.stdout.strip():
            print(attrs.stdout.strip())
        return False

    print(f"[PASS] P0 asset is versionable and LFS-lockable: {path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remote",
        action="store_true",
        help="also query origin and LFS locks; run from a normal user terminal",
    )
    args = parser.parse_args()

    checks = [
        run("git fsck", "git", "fsck", "--no-dangling"),
        run("index refresh", "git", "update-index", "-q", "--refresh"),
        run("whitespace", "git", "diff", "--check"),
        run("LFS pointers", "git", "lfs", "fsck", "--pointers"),
        run("LFS objects", "git", "lfs", "fsck"),
        # Disabling the filters for this status inspection avoids recursive
        # filter-process startup in restricted shells; it does not change the
        # repository's configured filters.
        run("LFS status", "git", *LFS_DISABLED, "lfs", "status", "--porcelain"),
    ]
    checks.extend(verify_p0_asset(path) for path in P0_ASSETS)

    if args.remote:
        checks.extend(
            [
                run("origin main visibility", "git", "ls-remote", "--heads", "origin", "main"),
                run("LFS locks", "git", "lfs", "locks"),
            ]
        )
    else:
        print("[HOLD] remote checks skipped; run with --remote before an LFS push.")

    if all(checks):
        print("Git health audit: PASS")
        return 0
    print("Git health audit: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
