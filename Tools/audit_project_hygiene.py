"""Read-only filesystem hygiene audit for the project workspace.

It reports empty directories, known generated/cache roots, and unusually large
directories. It never deletes, moves, or changes files.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "Saved" / "Audit" / "project_hygiene_audit.json"
SKIP = {".git", "DerivedDataCache", "Binaries", "Intermediate", "Saved"}
GENERATED_MARKERS = ("cache", "temp", "tmp", "generated", "exports", "export", "logs", "savestates")


def main() -> int:
    empty = []
    generated = []
    sizes = []

    for current, dirs, files in os.walk(ROOT):
        path = Path(current)
        rel = path.relative_to(ROOT)

        if rel.parts and rel.parts[0] in SKIP:
            dirs[:] = []
            continue

        # Filter dirs in-place
        dirs[:] = [d for d in dirs if d not in SKIP]

        if not files and not dirs:
            empty.append(rel.as_posix())

        low = rel.as_posix().lower()

        if any(marker in low.split("/") for marker in GENERATED_MARKERS):
            generated.append(rel.as_posix())

        total = sum((p.stat().st_size for p in path.iterdir() if p.is_file()), 0)

        if total >= 524288000:
            sizes.append({"path": rel.as_posix(), "bytes": total})

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ok": True,
        "empty_directories": sorted(empty),
        "generated_or_cache_candidates": sorted(set(generated)),
        "large_directories": sorted(sizes, key=lambda x: x["bytes"], reverse=True),
        "notes": [
            "Read-only report; review candidates before any cleanup.",
            "Active Blender/UE writers must release generated folders first.",
        ],
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "empty": len(empty),
                "generated_candidates": len(set(generated)),
                "large": len(sizes),
                "report": str(REPORT),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
