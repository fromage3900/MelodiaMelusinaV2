"""Normalize working-tree line endings to the .gitattributes policy.

Why this exists
---------------
`.gitattributes` declares `*.py` / `*.json` / `*.md` (and friends) as
`text eol=lf`, but a file written by a CRLF-producing tool (a JSON dumper, a
PowerShell redirect, an editor default) lands in the working tree as CRLF. Git
then normalizes it to LF on `git add`, so:

  * the FIRST commit of such a file shows a whole-file rewrite
    (`Tools/registry_baseline.json` churned ~5000 lines on 2026-09-18 for
    exactly this reason), and
  * `git status` shows EOL-only "modified" files nobody meant to change, which
    makes the 800-file dirty tree even harder to read.

This tool finds tracked text files whose working-tree ending disagrees with the
declared policy and (with --fix) rewrites only the offending bytes. It never
touches binary/LFS files (`-text` rules are skipped).

Usage
-----
    python deploy/_melodia_eol.py                      # report violations (exit 1 if any)
    python deploy/_melodia_eol.py --fix                # rewrite to the declared ending
    python deploy/_melodia_eol.py --fix --path deploy  # scope to a subtree
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
DEFAULT_REPO = SCRIPT.parent.parent


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Normalize line endings to .gitattributes policy")
    ap.add_argument("--fix", action="store_true", help="Rewrite offending files (default: report only).")
    ap.add_argument("--path", default="", help="Optional pathspec to scope the scan.")
    ap.add_argument("--repo", default="", help="Explicit repo root.")
    return ap.parse_args()


def policy(repo: Path) -> list[tuple[str, str]]:
    """[(glob, 'lf'|'crlf')] from .gitattributes, skipping -text/binary rules."""
    rules: list[tuple[str, str]] = []
    ga = repo / ".gitattributes"
    if not ga.is_file():
        return rules
    for raw in ga.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        attrs = parts[1:]
        if any(a == "-text" or a.startswith("filter=") for a in attrs):
            continue  # binary / LFS — never touch
        eol = None
        for a in attrs:
            if a == "eol=lf":
                eol = "lf"
            elif a == "eol=crlf":
                eol = "crlf"
        if eol is not None:
            rules.append((parts[0], eol))
    return rules


def desired_for(path: str, rules: list[tuple[str, str]]) -> str | None:
    name = os.path.basename(path)
    best = None
    for glob, eol in rules:
        if fnmatch.fnmatch(name, glob) or fnmatch.fnmatch(path.replace("\\", "/"), glob.lstrip("/")):
            best = eol
    return best


def tracked_files(repo: Path, scope: str) -> list[str]:
    cmd = ["git", "-C", str(repo), "ls-files"]
    if scope:
        cmd += ["--", scope]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        return []
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def detect_eol(data: bytes) -> str:
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n") - crlf
    if crlf and lf:
        return "mixed"
    if crlf:
        return "crlf"
    return "lf"


def to_lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def to_crlf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve() if args.repo else DEFAULT_REPO
    rules = policy(repo)
    if not rules:
        print("No eol rules in .gitattributes; nothing to do.")
        return 0

    offenders: list[tuple[str, str, str]] = []  # (path, found, desired)
    for rel in tracked_files(repo, args.path):
        want = desired_for(rel, rules)
        if want is None:
            continue
        p = repo / rel
        if not p.is_file():
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        found = detect_eol(data)
        if want == "lf" and found != "lf":
            offenders.append((rel, found, want))
        elif want == "crlf" and found != "crlf":
            offenders.append((rel, found, want))

    if not offenders:
        print(f"EOL CLEAN - scanned tracked files, 0 violations (scope={args.path or 'repo'})")
        return 0

    print(f"EOL VIOLATIONS ({len(offenders)}) scope={args.path or 'repo'}:")
    fixed = 0
    for rel, found, want in offenders:
        print(f"  {rel}: {found} -> {want}")
        if args.fix:
            p = repo / rel
            data = p.read_bytes()
            new = to_lf(data) if want == "lf" else to_crlf(data)
            p.write_bytes(new)
            fixed += 1
    if args.fix:
        print(f"FIXED {fixed} file(s).")
        return 0
    print("Re-run with --fix to normalize.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
