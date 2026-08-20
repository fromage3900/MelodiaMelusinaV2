#!/usr/bin/env python3
"""Copy dashboard snapshots into the lookbook + GitHub Pages tree.

    python Tools/publish_site_dashboards.py
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT / "Saved"
WIX = Path(r"C:\EnvironmentPortfolio\wix")
STATUS = Path(r"C:\EnvironmentPortfolio\generated\melodia\status")
SITE = Path(r"C:\EnvironmentPortfolio\my-site-clean")
SITE_WIX = SITE / "wix"
SITE_STATUS = SITE / "generated" / "melodia" / "status"
SITE_PUBLIC = SITE / "public" / "melodia" / "status"

DASHBOARDS = [
    "project_health.html",
    "loop_monitor.html",
    "live_dashboard.html",
    "metrics_dashboard.html",
    "agent-dashboard-t3d.html",
    "t3d-catalog.html",
    "dashboards.html",
]
JSON_FILES = [
    SAVED / "Audit" / "project_health_claims.json",
    SAVED / "Audit" / "math_run_latest.json",
    SAVED / "Audit" / "math_run_models_latest.json",
]


def _copy(src: Path, dest: Path) -> None:
    if not src.is_file():
        return
    if src.resolve() == dest.resolve():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"  {src} -> {dest}")


def main() -> int:
    print(f"publish dashboards {datetime.now().isoformat(timespec='seconds')}")
    for name in DASHBOARDS:
        src = WIX / name
        if not src.is_file():
            src = SAVED / name
        if not src.is_file():
            print(f"  skip missing {name}")
            continue
        _copy(src, WIX / name)
        if SITE_WIX.is_dir():
            _copy(src, SITE_WIX / name)
    for path in JSON_FILES:
        if not path.is_file():
            continue
        _copy(path, STATUS / path.name)
        if SITE.exists():
            _copy(path, SITE_STATUS / path.name)
            _copy(path, SITE_PUBLIC / path.name)
    health = WIX / "project_health.html"
    if health.is_file() and SITE_PUBLIC.is_dir():
        _copy(health, SITE_PUBLIC / "index.html")
    harness = WIX / "melusina-agent-harness.html"
    if harness.is_file() and SITE_WIX.is_dir():
        _copy(harness, SITE_WIX / "melusina-agent-harness.html")
    print("GitHub Pages URL after deploy: https://fromage3900.github.io/my-site/wix/dashboards.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
