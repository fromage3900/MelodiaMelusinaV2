#!/usr/bin/env python3
"""
lfs_health_audit.py — Echo-adjacent repo hygiene (promote stage).

1. Find HEAD blobs that should be LFS pointers but are raw binaries.
2. Optionally measure a collab slice manifest against a max_mb budget.

Usage:
  python Tools/lfs_health_audit.py
  python Tools/lfs_health_audit.py --manifest specs/collab_slices/slice50.json
  python Tools/lfs_health_audit.py --fail-on-nonpointer
"""
from __future__ import annotations

import argparse
import json
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

LFS_SUFFIXES = {
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


def run(cmd: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(cmd, check=False, capture_output=True)


def ls_files(prefixes: list[str] | None = None) -> list[str]:
    cmd = ["git", "ls-files", "-z"]
    if prefixes:
        cmd.extend(prefixes)
    proc = run(cmd)
    if proc.returncode != 0:
        return []
    return [p.decode("utf-8", errors="replace") for p in proc.stdout.split(b"\0") if p]


def head_blob(path: str) -> bytes | None:
    proc = run(["git", "show", f"HEAD:{path}"])
    if proc.returncode != 0:
        return None
    return proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="")
    parser.add_argument("--fail-on-nonpointer", action="store_true")
    parser.add_argument(
        "--game-paths-only",
        action="store_true",
        help="Only scan Content/ and Plugins/**/Content for non-pointers",
    )
    args = parser.parse_args()

    rc = 0
    files = ls_files()
    non_pointers: list[tuple[str, int]] = []
    for rel in files:
        suffix = Path(rel).suffix.lower()
        if suffix not in LFS_SUFFIXES:
            continue
        if args.game_paths_only:
            if not (
                rel.startswith("Content/")
                or "/Content/" in rel.replace("\\", "/")
            ):
                continue
        blob = head_blob(rel)
        if blob is None:
            continue
        if POINTER_RE.match(blob):
            continue
        non_pointers.append((rel, len(blob)))

    non_pointers.sort(key=lambda r: r[1], reverse=True)
    print(f"Non-pointer LFS-suffix files in HEAD: {len(non_pointers)}")
    total_bad = sum(s for _, s in non_pointers)
    print(f"  total raw bytes: {total_bad / (1024 * 1024):.2f} MB")
    for rel, size in non_pointers[:25]:
        print(f"  {size / (1024 * 1024):7.2f} MB  {rel}")
    if len(non_pointers) > 25:
        print(f"  ... {len(non_pointers) - 25} more")

    if args.fail_on_nonpointer and non_pointers:
        # Fail only for game content paths by default when flag set
        game_bad = [
            (r, s)
            for r, s in non_pointers
            if r.startswith("Content/") or "/Content/" in r.replace("\\", "/")
        ]
        if game_bad:
            print(f"FAIL: {len(game_bad)} non-pointer game binaries", file=sys.stderr)
            rc = 1

    if args.manifest:
        man_path = Path(args.manifest)
        man = json.loads(man_path.read_text(encoding="utf-8"))
        max_mb = float(man.get("max_mb", 50))
        includes = man.get("lfs_include", man.get("paths", []))
        # Measure tracked files under include prefixes
        measured = 0
        counted = 0
        missing: list[str] = []
        for pattern in includes:
            prefix = pattern.rstrip("*").rstrip("/")
            # Also support exact paths
            candidates = [f for f in files if f == pattern or f.startswith(prefix + "/") or f.startswith(prefix)]
            if not candidates and man.get("required"):
                missing.append(pattern)
            for rel in candidates:
                blob = head_blob(rel)
                if blob is None:
                    continue
                m = POINTER_RE.match(blob)
                if m:
                    measured += int(m.group(2))
                    counted += 1
                elif Path(rel).suffix.lower() in LFS_SUFFIXES:
                    measured += len(blob)
                    counted += 1
        mb = measured / (1024 * 1024)
        print(f"\nManifest {man_path.name}: {counted} LFS files, {mb:.2f} MB (max {max_mb:.0f} MB)")
        for req in man.get("required_paths", []):
            if req not in files and not any(f.startswith(req.rstrip("/") + "/") for f in files):
                missing.append(req)
                print(f"  MISSING required: {req}")
        if missing and man.get("fail_if_missing"):
            print("FAIL: required paths missing from this checkout", file=sys.stderr)
            rc = 1
        if mb > max_mb:
            print(f"FAIL: manifest exceeds {max_mb:.0f} MB budget", file=sys.stderr)
            rc = 1
        else:
            print("Manifest budget OK.")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
