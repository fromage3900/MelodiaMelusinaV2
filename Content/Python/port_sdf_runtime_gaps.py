"""Port actionable _PROJECT master gaps to EnvSandbox, driven by the manifest.

Reads specs/sdf_runtime_families.json (generated from the live registry) and
copies every non-dead master marked port_state==gap from
Content/_PROJECT/04_Materials to Content/EnvSandbox/Materials/Masters.

Rules:
  - Reads _PROJECT only; never writes there.
  - Writes only EnvSandbox/Materials/Masters (project-owned runtime spine).
  - Idempotent: skips destinations that already exist unless --force.
  - Dead (MooaToon) entries are always skipped.

Run:
  python Content/Python/port_sdf_runtime_gaps.py [--force]
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = PROJECT_ROOT / "specs" / "sdf_runtime_families.json"
PROJECT_MAT = PROJECT_ROOT / "Content" / "_PROJECT" / "04_Materials"
DST = PROJECT_ROOT / "Content" / "EnvSandbox" / "Materials" / "Masters"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "sdf_runtime_port.json"


def main() -> int:
    if not MANIFEST.is_file():
        print(f"Manifest missing: {MANIFEST}")
        return 1
    force = "--force" in sys.argv
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    gaps = [e for e in data["entries"] if e.get("port_state") == "gap" and not e.get("dead")]
    DST.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    skipped: list[str] = []
    not_found: list[str] = []

    for e in sorted(gaps, key=lambda x: x["name"]):
        name = e["name"]
        src = PROJECT_MAT / f"{name}.uasset"
        # Name may be nested under a subfolder (e.g. Underwater/); search by stem
        if not src.is_file():
            hits = list(PROJECT_MAT.rglob(f"{name}.uasset"))
            if not hits:
                not_found.append(name)
                continue
            src = hits[0]
        dst = DST / f"{name}.uasset"
        if dst.exists() and not force:
            skipped.append(name)
            continue
        shutil.copy2(src, dst)
        copied.append(name)
        print(f"Ported {name} <- {src.relative_to(PROJECT_MAT).as_posix()}")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "force": force,
        "manifest": str(MANIFEST),
        "actionable_gaps": len(gaps),
        "copied": copied,
        "skipped_existing": skipped,
        "not_found": not_found,
        "dest": str(DST),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Ported {len(copied)}, skipped {len(skipped)}, missing {len(not_found)} -> {REPORT}")
    return 0 if not not_found else 2


if __name__ == "__main__":
    raise SystemExit(main())
