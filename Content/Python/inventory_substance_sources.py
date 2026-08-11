"""Inventory staged Substance sources without requiring Unreal or the Substance plugin."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "Imports" / "SubstanceSource"
REPORT = ROOT / "Saved" / "Audit" / "substance_source_inventory.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    files = []
    if SOURCE_ROOT.exists():
        for path in sorted(p for p in SOURCE_ROOT.rglob("*") if p.is_file()):
            files.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "extension": path.suffix.lower(),
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": SOURCE_ROOT.as_posix(),
        "source_archive": r"F:\bling surface pbr material vol3.rar",
        "files": files,
        "sbsar_count": sum(item["extension"] == ".sbsar" for item in files),
        "baked_map_count": sum(item["extension"] in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".exr"} for item in files),
        "ok": bool(files) and all(item["sha256"] for item in files),
        "plugin_required_for_editor_import": True,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("source_root", "sbsar_count", "baked_map_count", "ok", "plugin_required_for_editor_import")}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
