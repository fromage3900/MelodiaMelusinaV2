#!/usr/bin/env python3
"""orphan_scan.py — enumerate single-copy files: not in git HEAD, not in the
P4 depot have-list, not machine-local by rule.

A file on this list can burn with zero recovery. Every entry needs one verdict:
submit to depot, commit to git, or declare machine-local-and-accepted.

Usage:
    python Tools/orphan_scan.py [--out Saved/Audit/orphan_scan_<date>.json]

Read-only against both VCS systems (git status/ls-files, p4 fstat/have).
Never stages, submits, deletes, or modifies anything.
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path prefixes (repo-relative, / separators) that are machine-local by rule:
# regenerable, caches, logs, tool state. Never reported as orphans.
MACHINE_LOCAL_PREFIXES = (
    "Saved/",
    "DerivedDataCache/",
    "Intermediate/",
    "Binaries/",
    ".vs/",
    ".vscode/",
    ".idea/",
    ".pytest_cache/",
    ".pi/",
    ".opencode/",
    "_staging/",
    "node_modules/",
    "__pycache__/",
)

# Set this env var to a text file with one //Melodia/main/... depot path per
# line (e.g. from `p4 -F "%depotFile%" files //Melodia/main/...`). When present,
# depot membership is a fast set lookup instead of per-file fstat batches.
# Without it, the scan falls back to `p4 -x - fstat` (slow on huge trees).
DEPOT_MANIFEST_ENV = "ORPHAN_SCAN_DEPOT_MANIFEST"

MACHINE_LOCAL_SUFFIXES = (
    ".tmp", ".log", ".bak", ".orig", ".rej",
    ".pyc", ".pyo",
)


def run(cmd, **kw):
    kw.setdefault("encoding", "utf-8")
    kw.setdefault("errors", "replace")
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, **kw)


def repo_rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def safe(s):
    return s.encode("ascii", "backslashreplace").decode("ascii")


def is_linked_worktree(rel):
    """A directory that is a separate git worktree: its files belong to
    another gitdir, so they must never be staged/submitted from here."""
    if not rel.endswith("/"):
        return False
    gitfile = os.path.join(ROOT, rel, ".git")
    try:
        with open(gitfile, encoding="utf-8", errors="replace") as fh:
            return fh.read(1024).startswith("gitdir:")
    except OSError:
        return False


def is_machine_local(rel):
    if rel.startswith(MACHINE_LOCAL_PREFIXES):
        return True
    low = rel.lower()
    if low.endswith(MACHINE_LOCAL_SUFFIXES):
        return True
    parts = low.split("/")
    if "node_modules" in parts or "__pycache__" in parts:
        return True
    return False


def git_untracked_files(include_ignored=False):
    """Files git sees as untracked.

    include_ignored=False honours .gitignore (the normal status view).
    include_ignored=True lists everything git doesn't track, including ignored
    paths — the only way to catch single-copy files hiding under a blanket
    ignore (e.g. new binaries under a P4-owned tree).
    """
    cmd = ["git", "ls-files", "--others", "-z"]
    if not include_ignored:
        cmd.append("--exclude-standard")
    p = run(cmd)
    if p.returncode != 0:
        print("ERROR: git ls-files failed:\n" + p.stderr, file=sys.stderr)
        sys.exit(2)
    return [f for f in p.stdout.split("\0") if f]


def load_depot_manifest():
    path = os.environ.get(DEPOT_MANIFEST_ENV, "")
    if not path or not os.path.exists(path):
        return None
    have = set()
    data = None
    for enc in ("utf-8-sig", "utf-16"):
        try:
            with open(path, encoding=enc) as fh:
                data = fh.read()
            if "//Melodia/main/" in data:
                break
        except (UnicodeError, OSError):
            continue
    if data is None:
        print("WARNING: could not read depot manifest %s" % path, file=sys.stderr)
        return None
    for line in data.splitlines():
        line = line.strip()
        if line.startswith("//Melodia/main/"):
            have.add(line.replace("//Melodia/main/", "", 1))
    return have


def p4_have_map(paths):
    """Batch fstat: return set of repo-rel paths present in the depot.

    Uses `p4 -x - fstat`, one depot path per line on stdin. Missing files
    report 'no such file(s)' on stderr and are simply absent from the map.
    """
    depot_paths = ["//Melodia/main/" + f for f in paths]
    p = subprocess.run(
        ["p4", "-x", "-", "fstat", "-T", "depotFile,clientFile"],
        input="\n".join(depot_paths) + "\n",
        capture_output=True, text=True, cwd=ROOT,
    )
    have = set()
    for line in p.stdout.splitlines():
        if line.startswith("... depotFile "):
            depot = line.split(" ", 2)[2].strip()
            rel = depot.replace("//Melodia/main/", "", 1)
            have.add(rel)
    return have


def p4_opened_set():
    p = run(["p4", "opened"])
    opened = set()
    for line in p.stdout.splitlines():
        if line.startswith("//Melodia/main/"):
            depot = line.split("#")[0]
            opened.add(depot.replace("//Melodia/main/", "", 1))
    return opened


def main():
    out = None
    args = sys.argv[1:]
    if args and args[0] == "--out":
        out = args[1] if len(args) > 1 else None
    if out is None:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out = os.path.join("Saved", "Audit", "orphan_scan_%s.json" % stamp)

    untracked = git_untracked_files(include_ignored="--all" in args)
    candidates = [f for f in untracked if not is_machine_local(f)]
    manifest = load_depot_manifest()
    if manifest is not None:
        have = set(f for f in candidates if f in manifest)
    else:
        have = p4_have_map(candidates) if candidates else set()
    opened = p4_opened_set()

    orphans, depot_backed, staged, worktrees = [], [], [], []
    for f in sorted(candidates):
        if is_linked_worktree(f):
            worktrees.append(f)
        elif f in have:
            if f in opened:
                staged.append(f)
            else:
                depot_backed.append(f)
        else:
            orphans.append(f)

    def size_of(f):
        try:
            return os.path.getsize(os.path.join(ROOT, f))
        except OSError:
            return -1

    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "untracked_total": len(untracked),
        "machine_local_skipped": len(untracked) - len(candidates),
        "depot_backed_recoverable_via_sync": len(depot_backed),
        "p4_open_staged": len(staged),
        "orphans_single_copy_no_recovery": len(orphans),
        "linked_worktrees_excluded": worktrees,
        "orphan_bytes": sum(s for s in (size_of(f) for f in orphans) if s > 0),
        "orphans": orphans,
    }
    out_path = os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print("untracked=%d machine_local=%d depot_backed=%d staged=%d ORPHANS=%d (%d bytes) worktrees=%d" % (
        report["untracked_total"], report["machine_local_skipped"],
        len(depot_backed), len(staged), len(orphans), report["orphan_bytes"],
        len(worktrees)))
    print("report: " + safe(out))
    for f in orphans[:50]:
        print("  ORPHAN " + safe(f))
    if len(orphans) > 50:
        print("  ... and %d more (see report)" % (len(orphans) - 50))
    for w in worktrees:
        print("  WORKTREE (separate authority, never touch from here) " + safe(w))
    return 0 if not orphans else 1


if __name__ == "__main__":
    sys.exit(main())
