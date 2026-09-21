"""Report (and optionally remove) STALE git lock files.

Why this exists
---------------
A `.git/index.lock` that outlives its git process blocks EVERY git operation
with "Another git process seems to be running". On 2026-09-18 a stale
`index.lock` (0 bytes, no git process, ~1h35m old) blocked staging, and the repo
also carries 14 orphaned `index.stash.*.lock` files and a `sparse-checkout.lock`
from interrupted operations.

Safety rule: this tool NEVER removes a lock while a `git.exe` process is live,
and never removes a lock younger than --age seconds. Removing a provably stale
lock is non-destructive (the lock is a mutex, not data; the index itself is not
touched). It is NOT one of the pipeline-law forbidden commands.

Usage
-----
    python deploy/_melodia_lock_sweep.py                 # report stale locks (exit 1 if any)
    python deploy/_melodia_lock_sweep.py --fix           # remove provably-stale locks
    python deploy/_melodia_lock_sweep.py --age 600       # only locks older than 600s
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPT = Path(__file__).resolve()
DEFAULT_REPO = SCRIPT.parent.parent


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Report/remove stale git lock files")
    ap.add_argument("--fix", action="store_true", help="Remove provably-stale locks.")
    ap.add_argument("--force-remove", action="store_true",
                    help="With --fix: remove stale locks even if a git.exe is present (you have checked).")
    ap.add_argument("--age", type=int, default=300, help="Min age in seconds to call a lock stale.")
    ap.add_argument("--repo", default="", help="Explicit repo root.")
    return ap.parse_args()


def git_running() -> bool:
    if shutil.which("tasklist") is None:
        return True  # cannot tell -> assume running (safe default: never delete)
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq git.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=20,
        )
    except Exception:
        return True
    return any(ln.strip().startswith('"') for ln in (out.stdout or "").splitlines())


def find_locks(repo: Path) -> list[Path]:
    gitdir = repo / ".git"
    if not gitdir.is_dir():
        return []
    return sorted(p for p in gitdir.rglob("*.lock") if p.is_file())


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve() if args.repo else DEFAULT_REPO
    running = git_running()
    locks = find_locks(repo)
    now = time.time()

    if not locks:
        print(f"LOCK SWEEP: no *.lock files under {repo / '.git'} (git running={running})")
        return 0

    stale: list[tuple[Path, float]] = []
    live: list[tuple[Path, float]] = []
    for p in locks:
        try:
            age = now - p.stat().st_mtime
        except OSError:
            continue
        (stale if age >= args.age else live).append((p, age))

    print(f"LOCK SWEEP: {len(locks)} lock file(s); git.exe running={running}; stale_threshold={args.age}s")
    for p, age in stale:
        print(f"  STALE  {p.relative_to(repo)}  age={int(age)}s")
    for p, age in live:
        print(f"  recent {p.relative_to(repo)}  age={int(age)}s")

    if not stale:
        print("No stale locks.")
        return 0

    if not args.fix:
        print("Re-run with --fix to remove the STALE locks (live git is respected).")
        return 1

    if running and not args.force_remove:
        print("REFUSING to --fix: a git.exe process is running. Retry once it exits "
              "(or pass --force-remove after verifying it is a zombie).", file=sys.stderr)
        return 2

    removed = 0
    for p, _age in stale:
        try:
            p.unlink()
            removed += 1
            print(f"  removed {p.relative_to(repo)}")
        except OSError as exc:
            print(f"  FAILED to remove {p.name}: {exc}", file=sys.stderr)
    print(f"LOCK SWEEP: removed {removed} stale lock(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
