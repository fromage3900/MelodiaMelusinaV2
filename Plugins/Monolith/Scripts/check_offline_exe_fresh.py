#!/usr/bin/env python3
"""
check_offline_exe_fresh.py -- staleness guard for the offline Monolith CLI.

The offline tool monolith_query.exe is built from Tools/MonolithQuery/monolith_query.cpp
by Tools/MonolithQuery/build.bat. That build injects the SHA256-first-16 of the source
as a /DSOURCE_HASH define, which the exe echoes back under --version as "source_hash".

This script recomputes that same hash from the on-disk source, asks the exe what it was
built from, and exits non-zero if they disagree -- i.e. the shipped exe is stale relative
to the tracked source and must be rebuilt.

An exe built before the hash-injection landed reports source_hash="dev"; that will never
match a real hex hash, so such an exe is correctly reported STALE.

Usage (run from the Monolith plugin root):
    python Scripts/check_offline_exe_fresh.py

Exit codes:
    0  exe source_hash matches the current source (fresh)
    1  mismatch (STALE -- rebuild via Tools/MonolithQuery/build.bat)
    4  preflight failure (source or exe missing, or --version unparseable)

stdlib-only. Do not add third-party deps.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

# Script lives in <MonolithRoot>/Scripts/, so the plugin root is parent.parent.
SCRIPT_DIR = Path(__file__).resolve().parent
MONO_ROOT = SCRIPT_DIR.parent
SRC_PATH = MONO_ROOT / "Tools" / "MonolithQuery" / "monolith_query.cpp"
EXE_PATH = MONO_ROOT / "Binaries" / "monolith_query.exe"

# Must match build.bat: first 16 hex chars of the source's SHA256.
HASH_PREFIX_LEN = 16


def compute_source_hash(path):
    """SHA256 of the file bytes, lowercase hex, first HASH_PREFIX_LEN chars."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:HASH_PREFIX_LEN]


def read_exe_source_hash(exe_path):
    """Run `<exe> --version`, parse JSON, return its source_hash string (or None)."""
    proc = subprocess.run(
        [str(exe_path), "--version"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise ValueError(
            "exe --version exited {0}: {1!r}".format(
                proc.returncode, (proc.stderr or "").strip()[:300]
            )
        )
    try:
        data = json.loads(proc.stdout)
    except Exception as exc:  # noqa: BLE001 - surface any parse failure
        raise ValueError(
            "could not parse --version JSON: {0}; raw[:300]={1!r}".format(
                exc, (proc.stdout or "")[:300]
            )
        )
    return data.get("source_hash")


def main():
    if not SRC_PATH.exists():
        print("FATAL: source not found at {0}".format(SRC_PATH))
        return 4
    if not EXE_PATH.exists():
        print("FATAL: exe not found at {0}".format(EXE_PATH))
        return 4

    src_hash = compute_source_hash(SRC_PATH)

    try:
        exe_hash = read_exe_source_hash(EXE_PATH)
    except ValueError as exc:
        print("FATAL: {0}".format(exc))
        return 4

    print("Offline exe freshness check")
    print("  source = {0}".format(SRC_PATH))
    print("  exe    = {0}".format(EXE_PATH))
    print("  source SHA256[:{0}] = {1}".format(HASH_PREFIX_LEN, src_hash))
    print("  exe   source_hash  = {0}".format(exe_hash))

    if exe_hash == src_hash:
        print("\nRESULT: FRESH -- exe matches current source.")
        return 0

    print("\nRESULT: STALE -- exe was built from different (or pre-hash) source.")
    print("  exe is STALE - rebuild via Tools/MonolithQuery/build.bat")
    return 1


if __name__ == "__main__":
    sys.exit(main())
