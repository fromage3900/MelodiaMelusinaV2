"""Convert masters still missing SubstrateToon on disk (save-retry pass).

Disk check avoids stale in-memory graphs when GUI editor holds locks.

Run headless (close GUI editor tabs on target materials first):
  UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript=".../run_toon_conversion_pending.py"

Or in open editor Output Log:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_toon_conversion_pending.py"
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import unreal

from convert_masters_to_substrate_toon import BATCH_1, BATCH_2, main

CONTENT = Path(__file__).resolve().parents[2] / "Content"

# Cmd runs Python before asset registry finishes — wait for OnFilesLoaded
time.sleep(20)


def _game_to_disk(game_path: str) -> Path:
    rel = game_path.removeprefix("/Game/").replace("/", "\\") + ".uasset"
    return CONTENT / rel


def _disk_missing_toon(game_path: str) -> bool:
    disk = _game_to_disk(game_path)
    if not disk.exists():
        return False
    text = disk.read_bytes().decode("ascii", "ignore")
    return "SubstrateToon" not in text and "ToonBSDF" not in text


PENDING = [p for p in list(BATCH_1) + list(BATCH_2) if _disk_missing_toon(p)]
unreal.log(f"[ToonPending] {len(PENDING)} masters missing SubstrateToon on disk")

if not PENDING:
    unreal.log("[ToonPending] Nothing to do — all batch masters have Toon on disk")
    raise SystemExit(0)

sys.argv = [
    "run_toon_conversion_pending.py",
    "--fix-params",
    "--assign-profiles",
    "--paths",
    *PENDING,
]

raise SystemExit(main())
