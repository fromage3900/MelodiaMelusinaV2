#!/usr/bin/env python3
"""Fail when a change introduces the deprecated EnvironmentPortfolio workspace
into active executable/config surfaces.

Historical documentation is intentionally allowed to retain old paths. This
guard is about preventing active code/config from reviving the obsolete
umbrella workspace as a canonical root.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEPRECATED = "environmentportfolio"

ACTIVE_PREFIXES = (
    "Tools/",
    "deploy/",
    "Content/Python/",
    "Scripts/",
    ".github/",
    "Config/",
)

ROOT_EXEC_SUFFIXES = {".py", ".ps1", ".bat", ".cmd", ".sh", ".json", ".yml", ".yaml"}

ALLOW_EXACT = {
    "Tools/safe_root_sweep.py",  # migration/audit tool whose purpose is finding old roots
    "Tools/guard_deprecated_workspace_refs.py",  # this guard names the deprecated root by design
}


def is_active_surface(path: str) -> bool:
    if path in ALLOW_EXACT:
        return False
    if path.startswith(ACTIVE_PREFIXES):
        return True
    p = Path(path)
    return len(p.parts) == 1 and p.suffix.lower() in ROOT_EXEC_SUFFIXES


def changed_added_lines(base: str) -> list[tuple[str, str]]:
    proc = subprocess.run(
        ["git", "diff", "--unified=0", f"{base}..HEAD", "--"],
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
    )
    current = ""
    hits: list[tuple[str, str]] = []
    for line in proc.stdout.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            continue
        if not current or not is_active_surface(current):
            continue
        if line.startswith("+") and not line.startswith("+++"):
            payload = line[1:]
            if DEPRECATED in payload.lower():
                hits.append((current, payload.strip()))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    args = parser.parse_args()

    hits = changed_added_lines(args.base)
    if not hits:
        print("[OK] no new active-code references to deprecated EnvironmentPortfolio root")
        return 0

    print("[FAIL] deprecated EnvironmentPortfolio root introduced in active code/config:")
    for path, line in hits:
        print(f"  {path}: {line}")
    print(
        "Use checkout-relative resolution / MELODIA_PROJECT_ROOT / Config/paths.json instead. "
        "Historical docs may retain old paths."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
