"""Cold backup of every dirty path, OUTSIDE the repo.

Why this exists: 61 paths in this tree are untracked, and three of them belong
to lanes that are not mine - the ANMN301 animatic submission (due Fri Oct 9,
21 MB MP4 + 24 MB of panels), the humber toon-spine workflow, and the brutalist
GN city/roof builders untracked since 2026-09-25. None of it is recoverable
from the object store. `git clean -fd` would delete every untracked file in
this project permanently.

The destination is P:/_laptop_safety_<date>/, a SIBLING of the repo and not
inside it, so no git command operating on the repo can reach it.

Read-only against the repo. Writes only to the destination.

Usage:
    python Tools/repo_safety_backup.py --date 2026-10-01
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

REPO = r"P:/MelodiaMelusinaV2-Laptop"
DEST_ROOT = "P:/_laptop_safety"


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True,
                          text=True, shell=False).stdout


def md5(path: str, limit: int = 8 << 20) -> str:
    """md5 of the first `limit` bytes - enough to detect a truncated copy
    without spending minutes hashing a 21 MB video."""
    h = hashlib.md5()
    try:
        with open(path, "rb") as fh:
            h.update(fh.read(limit))
    except OSError:
        return "unreadable"
    return h.hexdigest()


def copy_entry(src: str, dst: str, manifest: list, bucket: str) -> None:
    """Copy a file or a whole directory tree, recording every file written."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
        for dp, _dn, fn in os.walk(dst):
            for f in fn:
                full = os.path.join(dp, f)
                manifest.append({"bucket": bucket,
                                 "rel": os.path.relpath(full, dst),
                                 "src": src, "bytes": os.path.getsize(full),
                                 "md5_head": md5(full)})
    else:
        shutil.copy2(src, dst)
        manifest.append({"bucket": bucket, "rel": os.path.basename(src),
                         "src": src, "bytes": os.path.getsize(dst),
                         "md5_head": md5(dst)})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    dest = os.path.join(DEST_ROOT, args.date)
    if os.path.exists(dest):
        print("REFUSING: %s already exists - refusing to overwrite a backup"
              % dest)
        return 2

    status = git("status", "--porcelain")
    untracked, modified = [], []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        code, path = line[:2], line[3:]
        if code == "??":
            untracked.append(path)
        elif code.strip() == "M":
            modified.append(path)

    manifest: list = []
    for p in untracked:
        src = os.path.join(REPO, p)
        if os.path.exists(src):
            copy_entry(src, os.path.join(dest, "untracked", p), manifest,
                       "untracked")
    for p in modified:
        src = os.path.join(REPO, p)
        if os.path.isfile(src):
            copy_entry(src, os.path.join(dest, "modified", p), manifest,
                       "modified")

    head = git("rev-parse", "HEAD").strip()
    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    stashes = git("stash", "list")
    summary = {
        "date": args.date,
        "repo": REPO,
        "head": head,
        "branch": branch,
        "origin_main": git("rev-parse", "origin/main").strip(),
        "local_main": git("rev-parse", "main").strip(),
        "stashes": [ln for ln in stashes.splitlines() if ln.strip()],
        "untracked_paths": untracked,
        "modified_paths": modified,
        "files_written": len(manifest),
        "bytes_written": sum(m["bytes"] for m in manifest),
        "manifest": manifest,
    }
    with open(os.path.join(dest, "BACKUP_MANIFEST.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    print("dest        : %s" % dest)
    print("head        : %s on %s" % (head[:12], branch))
    print("origin/main : %s" % summary["origin_main"][:12])
    print("local main  : %s" % summary["local_main"][:12])
    print("untracked   : %d paths" % len(untracked))
    print("modified    : %d paths" % len(modified))
    print("written     : %d files, %.1f MB"
          % (len(manifest), summary["bytes_written"] / 1e6))
    print("stashes     : %d (recorded, NOT touched)" % len(summary["stashes"]))
    print("manifest    : %s" % os.path.join(dest, "BACKUP_MANIFEST.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())