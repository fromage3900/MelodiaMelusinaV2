#!/usr/bin/env python3
"""Serial, index-safe Git/LFS health audit for BS_GodFile.

This is intentionally read-only: it never refreshes the index, stages, resets,
cleans, fetches, or pushes. Run without arguments for local health, then add
``--remote`` from a normal user terminal before staging or pushing LFS assets.
"""

from __future__ import annotations

import argparse
import os
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
P0_MUST_REMAIN_IGNORED = (
    "Content/TurnBasedJRPGTemplate/Blueprints/EnemyExplorePawns/"
    "AverageEnemyExplorePawns/BP_AverageEnemyExplorePawn.uasset",
    "Content/TurnBasedJRPGTemplate/Blueprints/EnemyExplorePawns/"
    "PassiveEnemyExplorePawns/BP_PassiveEnemyExplorePawnBase.uasset",
    "Content/TurnBasedJRPGTemplate/Blueprints/EnemyExplorePawns/"
    "PassiveEnemyExplorePawns/BP_WeakEnemyExplorePawn.uasset",
    "Content/TurnBasedJRPGTemplate/Blueprints/Battle/"
    "BP_InteractionDetector.uasset",
)
READ_ONLY_ENV = {
    **os.environ,
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_LFS_SKIP_SMUDGE": "1",
}
COMMAND_TIMEOUT_SECONDS = 180


def run(
    label: str,
    *args: str,
    allowed: tuple[int, ...] = (0,),
    show_output_on_success: bool = True,
) -> bool:
    """Run one Git command at a time and report its bounded output."""
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            env=READ_ONLY_ENV,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(f"[FAIL] {label}")
        print(f"command exceeded {COMMAND_TIMEOUT_SECONDS}s timeout")
        return False
    ok = completed.returncode in allowed
    state = "PASS" if ok else "FAIL"
    print(f"[{state}] {label}")
    output = completed.stdout.strip()
    if output and (not ok or show_output_on_success):
        print(output)
    return ok


def capture(*args: str) -> subprocess.CompletedProcess[str] | None:
    """Capture a bounded read-only Git command for a semantic check."""
    try:
        return subprocess.run(
            args,
            cwd=ROOT,
            env=READ_ONLY_ENV,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return None


def verify_no_git_locks() -> bool:
    """Reject known repository lock files without deleting them."""
    git_dir_result = capture("git", "rev-parse", "--absolute-git-dir")
    if git_dir_result is None or git_dir_result.returncode:
        print("[FAIL] unable to resolve Git directory for lock inspection")
        return False

    git_dir = Path(git_dir_result.stdout.strip())
    candidates = sorted(git_dir.glob("*.lock"))
    maintenance_lock = git_dir / "objects" / "maintenance.lock"
    if maintenance_lock.exists():
        candidates.append(maintenance_lock)
    if candidates:
        print("[FAIL] repository lock files present")
        for candidate in candidates:
            print(candidate)
        return False
    print("[PASS] no repository lock files")
    return True


def verify_no_prunable_worktrees() -> bool:
    """Fail if stale worktree metadata is still registered."""
    result = capture("git", "worktree", "prune", "--dry-run", "--verbose")
    if result is None or result.returncode:
        print("[FAIL] unable to inspect worktree registrations")
        if result is not None and result.stdout.strip():
            print(result.stdout.strip())
        return False
    if result.stdout.strip():
        print("[FAIL] prunable worktree metadata remains")
        print(result.stdout.strip())
        return False
    print("[PASS] worktree registrations")
    return True


def verify_saved_artifacts_are_contained() -> bool:
    """Keep arbitrary generated evidence under Saved ignored by default."""
    probe = "Saved/Audit/noncanonical_health_probe.json"
    result = capture("git", "check-ignore", "-q", "--no-index", "--", probe)
    if result is not None and result.returncode == 0:
        print("[PASS] generated Saved artifacts remain ignored")
        return True
    print("[FAIL] generated Saved artifacts are broadly versionable")
    return False


def verify_p0_asset(path: str) -> bool:
    """Assert that a reviewed P0 asset is eligible for LFS tracking."""
    ignored = capture("git", "check-ignore", "-q", "--", path)
    if ignored is None:
        print(f"[FAIL] timed out inspecting P0 ignore rule: {path}")
        return False
    if ignored.returncode == 0:
        print(f"[FAIL] P0 asset is ignored: {path}")
        return False
    if ignored.returncode != 1:
        print(f"[FAIL] unable to inspect P0 ignore rule: {path}")
        return False

    attrs = capture("git", "check-attr", "filter", "lockable", "--", path)
    if attrs is None:
        print(f"[FAIL] timed out inspecting P0 attributes: {path}")
        return False
    required = ("filter: lfs", "lockable: set")
    if attrs.returncode or not all(value in attrs.stdout for value in required):
        print(f"[FAIL] P0 asset lacks LFS/lockable attributes: {path}")
        if attrs.stdout.strip():
            print(attrs.stdout.strip())
        return False

    print(f"[PASS] P0 asset is versionable and LFS-lockable: {path}")
    return True


def verify_p0_exception_is_contained(path: str) -> bool:
    """Assert that non-authored P0 coverage/template assets stay ignored."""
    ignored = capture("git", "check-ignore", "-q", "--", path)
    if ignored is None:
        print(f"[FAIL] timed out inspecting P0 ignore rule: {path}")
        return False
    if ignored.returncode == 0:
        print(f"[PASS] P0 exception remains contained: {path}")
        return True
    if ignored.returncode == 1:
        print(f"[FAIL] unexpected versionable P0 template/coverage asset: {path}")
        return False
    print(f"[FAIL] unable to inspect P0 ignore rule: {path}")
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remote",
        action="store_true",
        help="also query origin and LFS locks; run from a normal user terminal",
    )
    args = parser.parse_args()

    checks = [
        verify_no_git_locks(),
        verify_no_prunable_worktrees(),
        verify_saved_artifacts_are_contained(),
        run("git fsck", "git", "fsck", "--no-dangling"),
        run(
            "index readability",
            "git",
            "status",
            "--porcelain=v2",
            "--untracked-files=no",
            show_output_on_success=False,
        ),
        run("whitespace", "git", "diff", "--check"),
        run("LFS pointers", "git", "lfs", "fsck", "--pointers"),
        run("LFS objects", "git", "lfs", "fsck"),
        run("pre-commit hook", "git", "hook", "run", "pre-commit"),
    ]
    checks.extend(verify_p0_asset(path) for path in P0_ASSETS)
    checks.extend(
        verify_p0_exception_is_contained(path)
        for path in P0_MUST_REMAIN_IGNORED
    )

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
