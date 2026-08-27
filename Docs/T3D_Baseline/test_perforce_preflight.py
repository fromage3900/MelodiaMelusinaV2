#!/usr/bin/env python3
"""Smoke test: perforce_migration_preflight runs read-only on cloud/CI (no p4 required)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = ROOT / "Tools" / "perforce_migration_preflight.py"


def test_preflight_json_exits_zero():
    result = subprocess.run(
        [sys.executable, str(PREFLIGHT), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["git"]["available"] is True
    assert "head" in payload["git"]
    assert payload["lfs"]["available"] is True
    assert "available" in payload["perforce"]


if __name__ == "__main__":
    test_preflight_json_exits_zero()
    print("OK")
