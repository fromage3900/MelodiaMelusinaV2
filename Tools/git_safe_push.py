#!/usr/bin/env python3
"""
git_safe_push.py - LFS batch budget gate (Docs/GIT_BATCH_DISCIPLINE.md).

Refuses to proceed when LFS objects would exceed LimitMB.

Modes:
  staged (default)     - git diff --cached (pre-push / local)
  --range A..B         - files changed between commits (CI PR base..head)
  --auto-limit         - 50 MB for collab/cursor/docs branches, else 512

Usage:
  python Tools/git_safe_push.py --check-only
  python Tools/git_safe_push.py --limit-mb 50 --check-only
  python Tools/git_safe_push.py --range origin/main..HEAD --limit-mb 50 --check-only
  python Tools/git_safe_push.py --auto-limit --check-only
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

POINTER_RE = re.compile(
    rb"^version https://git-lfs\.github\.com/spec/v1\r?\n"
    rb"oid sha256:([0-9a-f]{64})\r?\n"
    rb"size (\d+)\r?\n",
    re.MULTILINE,
)

BINARY_SUFFIXES = {
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
    ".ttf",
    ".otf",
    ".mp4",
    ".webm",
}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def run_bytes(cmd: list[str]) -> subprocess.CompletedProcess[bytes]:
    """Blob reads must stay binary.

    `run()` decodes with the platform default codec -- cp1252 on Windows -- so any
    blob holding a byte outside that map (a real binary, or UTF-8 punctuation)
    raised UnicodeDecodeError, left stdout None, and crashed the gate on the
    AttributeError instead of reporting a budget. Re-encoding the decoded text
    also corrupted the very bytes the pointer check inspects.
    """
    return subprocess.run(cmd, check=False, capture_output=True)


def current_branch() -> str:
    proc = run(["git", "symbolic-ref", "--short", "HEAD"])
    return proc.stdout.strip() if proc.returncode == 0 else ""


def auto_limit_mb(branch: str) -> float:
    env = os.environ.get("MELODIA_LFS_LIMIT_MB")
    if env:
        return float(env)
    for prefix in ("collab/", "cursor/", "docs/"):
        if branch.startswith(prefix):
            return 50.0
    return 512.0


def staged_paths() -> list[tuple[str, str]]:
    proc = run(["git", "diff", "--cached", "--name-status"])
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        sys.exit(2)
    return _parse_name_status(proc.stdout)


def range_paths(rev_range: str) -> list[tuple[str, str]]:
    # Accept "A..B" or "A...B"
    proc = run(["git", "diff", "--name-status", rev_range])
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        sys.exit(2)
    return _parse_name_status(proc.stdout)


def _parse_name_status(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        status, path = line.split("\t", 1)
        code = status[0]
        if code in {"R", "C"} and "\t" in path:
            path = path.split("\t")[-1]
        rows.append((code, path))
    return rows


def _pointer_meta(data: bytes) -> tuple[str, int] | None:
    match = POINTER_RE.match(data)
    if not match:
        return None
    return match.group(1).decode(), int(match.group(2))


def _read_blob(rel: str, at_ref: str | None = None) -> bytes | None:
    if at_ref:
        proc = run_bytes(["git", "show", f"{at_ref}:{rel}"])
        if proc.returncode != 0:
            return None
        return proc.stdout
    path = Path(rel)
    try:
        return path.read_bytes()
    except OSError:
        proc = run_bytes(["git", "show", f":{rel}"])
        if proc.returncode != 0:
            return None
        return proc.stdout


def blob_pointer_size(rel: str, at_ref: str | None = None) -> int | None:
    """Size from LFS pointer at ref, or working tree file."""
    data = _read_blob(rel, at_ref=at_ref)
    if data is None:
        return None
    meta = _pointer_meta(data)
    if meta:
        return meta[1]
    path = Path(rel)
    if path.suffix.lower() in BINARY_SUFFIXES or Path(rel).suffix.lower() in BINARY_SUFFIXES:
        return len(data) if not path.exists() else path.stat().st_size
    return None


def same_lfs_oid(rel: str, left_ref: str, right_ref: str) -> bool:
    """True when both sides are LFS pointers with the same oid (pointer-text-only edit)."""
    left = _read_blob(rel, at_ref=left_ref)
    right = _read_blob(rel, at_ref=right_ref)
    if left is None or right is None:
        return False
    left_meta = _pointer_meta(left)
    right_meta = _pointer_meta(right)
    if not left_meta or not right_meta:
        return False
    return left_meta[0] == right_meta[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Refuse oversized LFS push batches")
    parser.add_argument("--limit-mb", type=float, default=None)
    parser.add_argument("--auto-limit", action="store_true")
    parser.add_argument("--range", dest="rev_range", default="", help="e.g. origin/main..HEAD")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("extras", nargs="*", help=argparse.SUPPRESS)
    args = parser.parse_args()

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
        if key in {"range"} and i + 1 < len(extras):
            args.rev_range = extras[i + 1]
            i += 2
            continue
        i += 1

    branch = args.branch or current_branch()
    if args.limit_mb is None:
        args.limit_mb = auto_limit_mb(branch)

    limit_bytes = int(args.limit_mb * 1024 * 1024)

    left_ref = None
    size_at: str | None
    if args.rev_range:
        # Prefer right side of A..B as blob source
        if "..." in args.rev_range:
            left_ref, right = args.rev_range.split("...", 1)
        elif ".." in args.rev_range:
            left_ref, right = args.rev_range.split("..", 1)
        else:
            left_ref, right = "HEAD", args.rev_range
        right = right or "HEAD"
        left_ref = left_ref or "HEAD"
        paths = range_paths(args.rev_range)
        size_at = right
    else:
        paths = staged_paths()
        size_at = None
        left_ref = "HEAD"

    total = 0
    skipped_same_oid = 0
    rows: list[tuple[str, int]] = []
    for status, rel in paths:
        if status == "D":
            continue
        # Pointer-text-only edits (EOL) keep the same LFS oid - no storage delta.
        if left_ref:
            head_blob = _read_blob(rel, at_ref=left_ref)
            new_blob = _read_blob(rel, at_ref=size_at)  # None => working/index
            if head_blob is not None and new_blob is not None:
                head_meta = _pointer_meta(head_blob)
                new_meta = _pointer_meta(new_blob)
                if head_meta and new_meta and head_meta[0] == new_meta[0]:
                    skipped_same_oid += 1
                    continue
        size = blob_pointer_size(rel, at_ref=size_at)
        if size is None:
            continue
        total += size
        rows.append((rel, size))

    rows.sort(key=lambda r: r[1], reverse=True)
    mode = f"range {args.rev_range}" if args.rev_range else "staged"
    skip_note = f", skipped {skipped_same_oid} same-oid pointer edits" if skipped_same_oid else ""
    print(
        f"LFS batch candidates ({mode}): {len(rows)} files, "
        f"{total / (1024 * 1024):.2f} MB (limit {args.limit_mb:.0f} MB, "
        f"branch={branch or 'detached'}{skip_note})"
    )
    for rel, size in rows[:20]:
        print(f"  {size / (1024 * 1024):7.2f} MB  {rel}")
    if len(rows) > 20:
        print(f"  ... {len(rows) - 20} more")

    if total > limit_bytes:
        print(
            f"BLOCKED: LFS batch {total / (1024 * 1024):.2f} MB exceeds "
            f"limit {args.limit_mb:.0f} MB",
            file=sys.stderr,
        )
        return 1

    print("LFS budget gate OK.")
    if args.check_only or not args.branch:
        return 0

    push = run(["git", "push", args.remote, f"HEAD:{args.branch}"])
    sys.stdout.write(push.stdout)
    sys.stderr.write(push.stderr)
    return push.returncode


if __name__ == "__main__":
    raise SystemExit(main())
