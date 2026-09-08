#!/usr/bin/env python3
"""Prevent active code/config changes from reviving the deprecated
fromage3900/EnvironmentPortfolio *Git repository* as canonical authority.

The local filesystem directory C:/EnvironmentPortfolio/ is allowed and may
remain the workspace container for nested independent repositories.
"""
from __future__ import annotations

import argparse
import subprocess

BANNED_TOKENS = (
    "github.com/fromage3900/environmentportfolio",
    "fromage3900/environmentportfolio.git",
)

ACTIVE_PREFIXES = (
    "Tools/",
    "deploy/",
    "Content/Python/",
    "Scripts/",
    ".github/",
    "Config/",
)


def is_active_surface(path: str) -> bool:
    return path.startswith(ACTIVE_PREFIXES)


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
            payload = line[1:].lower()
            if any(token in payload for token in BANNED_TOKENS):
                hits.append((current, line[1:].strip()))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    args = parser.parse_args()

    hits = changed_added_lines(args.base)
    if not hits:
        print("[OK] deprecated root Git repo not reintroduced")
        return 0

    print("[FAIL] deprecated EnvironmentPortfolio Git repo reintroduced in active code/config:")
    for path, line in hits:
        print(f"  {path}: {line}")
    print(
        "C:/EnvironmentPortfolio/ filesystem paths are allowed. "
        "Do not use fromage3900/EnvironmentPortfolio as active Git authority."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
