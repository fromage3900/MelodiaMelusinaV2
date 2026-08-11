"""Port all _PROJECT M_SDF_* masters missing from EnvSandbox (incl. math-art).

Standalone:
  python Content/Python/port_sdf_expansion.py
  python Content/Python/port_sdf_expansion.py --force
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "Content" / "_PROJECT" / "04_Materials"
DST = PROJECT_ROOT / "Content" / "EnvSandbox" / "Materials" / "Masters"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "sdf_port_expansion.json"


def _discover_batch() -> list[tuple[str, str]]:
    batch: list[tuple[str, str]] = []
    if not SRC_ROOT.exists():
        return batch
    for src in sorted(SRC_ROOT.rglob("M_SDF_*.uasset")):
        rel = src.relative_to(SRC_ROOT).with_suffix("").as_posix()
        batch.append((rel, src.stem))
    return batch


def main() -> int:
    force = "--force" in sys.argv
    DST.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    skipped: list[str] = []
    missing: list[str] = []

    for rel, stem in _discover_batch():
        src = SRC_ROOT / Path(rel).with_suffix(".uasset")
        dst = DST / f"{stem}.uasset"
        if not src.exists():
            missing.append(stem)
            continue
        if dst.exists() and not force and dst.stat().st_size == src.stat().st_size:
            skipped.append(stem)
            continue
        shutil.copy2(src, dst)
        copied.append(stem)
        print(f"Ported {stem}")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "force": force,
        "total_project_sdf": len(_discover_batch()),
        "copied": copied,
        "skipped_unchanged": skipped,
        "missing_source": missing,
        "dest": str(DST),
        "note": "Run run_portfolio_sdf_texture_pipeline.py for rewire + texture integration.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Ported {len(copied)}, skipped {len(skipped)}, missing {len(missing)} -> {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
