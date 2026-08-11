"""Restore known-corrupt portfolio materials/textures from _PROJECT (safe, no editor).

Run before opening UE if integration scripts crashed on linker assertions:
  python Content/Python/repair_crash_assets.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = (
    "restore_portfolio_textures.py",
    "restore_portfolio_masters.py",
)


def main() -> int:
    py = sys.executable
    for name in SCRIPTS:
        path = PROJECT_ROOT / "Content" / "Python" / name
        print(f">>> {name}")
        rc = subprocess.run([py, str(path)], cwd=str(PROJECT_ROOT)).returncode
        if rc != 0:
            return rc
    print("Repair complete — reopen editor (do not run patch_portfolio_texture_paths.py).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
