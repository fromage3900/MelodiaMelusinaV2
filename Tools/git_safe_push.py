#!/usr/bin/env python3
"""
git_safe_push.py — LFS batch budget gate (Docs/GIT_BATCH_DISCIPLINE.md).

Refuses to proceed when staged/to-push LFS objects would exceed LimitMB.
Used by CI (echo_gates.yml) and local pre-push discipline.

Usage:
  python Tools/git_safe_push.py --limit-mb 512
  python Tools/git_safe_push.py --limit-mb 512 --remote origin --branch main
  python Tools/git_safe_push.py --limit-mb 512 --check-only
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

POINTER_RE = re.compile(
    rb"^version https://git-lfs\.github\.com/spec/v1\n"
    rb"oid sha256:([0-9a-f]{64})\n"
    rb"size (\d+)\n",
    re.MULTILINE,
)


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def staged_paths() -> list[tuple[str, str]]:
    """Return (status, path) for staged files. Status is A/M/D/R/..."""
    proc = run(["git", "diff", "--cached", "--name-status"])
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        sys.exit(2)
    rows: list[tuple[str, str]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        status, path = line.split("\t", 1)
        code = status[0]
        if code in {"R", "C"} and "\t" in path:
            # name-status without -z: R100\told\tnew
            path = path.split("\t")[-1]
        rows.append((code, path))
    return rows


def lfs_pointer_size(path: Path) -> int | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    match = POINTER_RE.match(data)
    if not match:
        # Staged binary that should be LFS but isn't a pointer yet — count file size.
        if path.suffix.lower() in {
            ".uasset",
            ".umap",
            ".fbx",
            ".blend",
            ".png",
            ".jpg",
            ".jpeg",
            ".wav",
            ".mp3",
            ".ogg",
            ".psd",
            ".tif",
            ".tiff",
            ".exr",
            ".dll",
            ".so",
            ".dylib",
        }:
            return path.stat().st_size
        return None
    return int(match.group(2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Refuse oversized LFS push batches")
    parser.add_argument("--limit-mb", type=float, default=512.0)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="")
    parser.add_argument("--check-only", action="store_true")
    # Accept PowerShell-style positional leftovers from the old .ps1 call sites.
    parser.add_argument("extras", nargs="*", help=argparse.SUPPRESS)
    args = parser.parse_args()

    # Map legacy "-LimitMB 512 -Remote origin -Branch x" style if passed via extras.
    extras = list(args.extras)
    i = 0
    while i < len(extras):
        token = extras[i].lstrip("-")
        key = token.lower().replace("_", "")
        if key in {"limitmb", "limit-mb"} and i + 1 < len(extras):
            args.limit_mb = float(extras[i + 1])
            i += 2
            continue
        if key in {"remote"} and i + 1 < len(extras):
            args.remote = extras[i + 1]
            i += 2
            continue
        if key in {"branch"} and i + 1 < len(extras):
            args.branch = extras[i + 1]
            i += 2
            continue
        i += 1

    limit_bytes = int(args.limit_mb * 1024 * 1024)
    paths = staged_paths()
    total = 0
    rows: list[tuple[str, int]] = []
    for status, rel in paths:
        if status == "D":
            continue  # deletions free references; they are not a new LFS upload
        size = lfs_pointer_size(Path(rel))
        if size is None:
            continue
        total += size
        rows.append((rel, size))

    rows.sort(key=lambda r: r[1], reverse=True)
    print(f"LFS batch candidates: {len(rows)} files, {total / (1024 * 1024):.2f} MB")
    for rel, size in rows[:20]:
        print(f"  {size / (1024 * 1024):7.2f} MB  {rel}")
    if len(rows) > 20:
        print(f"  ... {len(rows) - 20} more")

    if total > limit_bytes:
        print(
            f"BLOCKED: LFS batch {total / (1024 * 1024):.2f} MB exceeds "
            f"limit {args.limit_mb:.0f} MB (remote={args.remote} branch={args.branch or '(current)'})",
            file=sys.stderr,
        )
        return 1

    print("LFS budget gate OK.")
    if args.check_only or not args.branch:
        return 0

    # Optional push path for local use; CI only needs the check.
    push = run(["git", "push", args.remote, f"HEAD:{args.branch}"])
    sys.stdout.write(push.stdout)
    sys.stderr.write(push.stderr)
    return push.returncode


if __name__ == "__main__":
    raise SystemExit(main())
