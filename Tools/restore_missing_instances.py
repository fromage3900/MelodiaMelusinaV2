"""Restore material instances deleted by cc6f7484 and still absent from disk.

Recovery for the "missing instances" report (2026-08-13): commit cc6f7484
"Delete all 192 portfolio-owned Material Instances ahead of master finalization"
removed 192 MIs; 115 were later recreated, 77 remain missing on disk. This tool
restores each missing file from the most recent commit in any branch where its
blob still exists, using only targeted per-file `git show` writes.

SAFETY: never `git checkout -- .`, never `git clean`. This script only writes
the specific missing paths, byte-for-byte from history, and nothing else.

Usage (plain Python, editor may be open or closed):
    python Tools/restore_missing_instances.py [--dry-run]

Writes Saved/Audit/restored_mis_manifest.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT = ["git", "-C", str(ROOT)]
MANIFEST = ROOT / "Saved" / "Audit" / "restored_mis_manifest.json"
DELETION_COMMIT = "cc6f7484"


def run(args: list[str]) -> str:
    proc = subprocess.run(GIT + args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()[:400]}")
    return proc.stdout


def deleted_paths() -> list[str]:
    out = run(["show", DELETION_COMMIT, "--name-status", "--format="])
    paths = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("D\t"):
            paths.append(line[2:].strip())
    return paths


def last_commit_with(path: str) -> str | None:
    touches = run(["log", "--all", "--format=%H", "--", path]).split()
    for sha in touches:
        probe = run(["cat-file", "-e", f"{sha}:{path}"]) if False else None
        try:
            subprocess.run(
                GIT + ["cat-file", "-e", f"{sha}:{path}"],
                capture_output=True, check=True,
            )
            return sha
        except subprocess.CalledProcessError:
            continue
    return None


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    missing: list[dict] = []
    for path in deleted_paths():
        target = ROOT / path
        if target.exists():
            continue
        sha = last_commit_with(path)
        if sha is None:
            missing.append({"path": path, "status": "no_blob_in_history"})
            continue
        if dry_run:
            missing.append({"path": path, "status": "would_restore", "source": sha})
            continue
        try:
            data = subprocess.run(
                GIT + ["show", f"{sha}:{path}"], capture_output=True, check=True,
            ).stdout
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            # LFS pointers: blob may be a 130-byte pointer; the real content
            # lives in .git/lfs/objects/<oid-shard>/<oid> when present.
            if data.startswith(b"version https://git-lfs"):
                oid = None
                for line in data.decode("utf-8", errors="replace").splitlines():
                    if line.startswith("oid sha256:"):
                        oid = line.split(":", 1)[1].strip()
                        break
                obj = ROOT / ".git" / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
                if oid and obj.exists():
                    target.write_bytes(obj.read_bytes())
                    materialized = True
                else:
                    materialized = False
            else:
                materialized = False
            missing.append({
                "path": path, "status": "restored", "source": sha,
                "bytes": len(target.read_bytes()),
                "lfs_materialized": materialized,
            })
        except subprocess.CalledProcessError as exc:
            missing.append({"path": path, "status": "restore_failed", "source": sha, "error": str(exc.stderr[:200])})

    restored = [m for m in missing if m["status"] == "restored"]
    failed = [m for m in missing if m["status"] != "restored"]
    print(f"restored={len(restored)} failed_or_absent={len(failed)}")
    for m in failed:
        print(f"  {m['status']}: {m['path']}")

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": dry_run,
            "count": len(missing),
            "items": missing,
        }, indent=2),
        encoding="utf-8",
    )
    print(f"manifest -> {MANIFEST}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
