# -*- coding: utf-8 -*-
"""Burn watermarks per-file so one locked PNG doesn't abort the batch."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SITE = Path(r"G:\EnvironmentPortfolio\BS_GodFile\my-site-clean\generated\assets\nightshift")
TOOL = Path(r"G:\EnvironmentPortfolio\BS_GodFile\Tools\burn_fromage_watermark.py")


def main() -> int:
    files = []
    for pattern in ("MI_SDF_*.png", "MI_Toon_*.png", "MI_Cosmic_*.png", "grid_*.png"):
        files.extend(sorted(SITE.glob(pattern)))
    ok = fail = 0
    failures = []
    for path in files:
        proc = subprocess.run(
            [sys.executable, str(TOOL), str(path), "--inplace", "--force"],
            capture_output=True,
            text=True,
        )
        burned = False
        try:
            payload = json.loads(proc.stdout.strip().splitlines()[-1])
            burned = bool(payload.get("burned"))
        except Exception:
            burned = proc.returncode == 0
        if proc.returncode == 0 and burned:
            ok += 1
        else:
            fail += 1
            failures.append({"file": path.name, "stdout": proc.stdout[-300:], "stderr": proc.stderr[-300:]})
    print(json.dumps({"ok": fail == 0, "burned": ok, "failed": fail, "failures": failures[:8]}))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
