"""NPC source staging validator — checks the sourcing manifest against disk.

Report only by default; --apply moves nothing (sources are dropped in place) but
writes Imports/NPCs/source_validation.json and warns on provenance gaps.

Usage:
    py Tools/stage_npc_sources.py --check      # report only (default)
    py Tools/stage_npc_sources.py --apply      # write validation report
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # BS_GodFile/
MANIFEST_PATH = PROJECT_ROOT / "Imports" / "NPCs" / "source_manifest.json"
REPORT_PATH = PROJECT_ROOT / "Imports" / "NPCs" / "source_validation.json"
REGISTRY_PATH = PROJECT_ROOT / "Content" / "Python" / "gmm" / "npc" / "vrm_registry.json"

PLACEHOLDER_URLS = ("XXXXXXX", "TODO", "REPLACE")


@dataclass
class SourceCheck:
    character: str
    family: str
    status: str = "ok"
    missing: list[str] = field(default_factory=list)
    present: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def resolve(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


def check_placeholder_urls(entry: dict) -> list[str]:
    warnings = []
    for key in ("source_url", "license_url"):
        value = entry.get(key, "")
        if value and any(tok in value for tok in PLACEHOLDER_URLS):
            warnings.append(f"{key} is a placeholder: {value}")
    return warnings


def check_character(entry: dict) -> SourceCheck:
    check = SourceCheck(character=entry["character"], family=entry["family"])
    for fname in entry.get("expected_files", []):
        path = resolve(str(entry["staging_path"])) / fname
        if not path.exists():
            check.missing.append(str(path))
        else:
            check.present.append(str(path))
    check.warnings.extend(check_placeholder_urls(entry))

    if entry.get("status") == "staged":
        check.status = "staged" if not check.missing else "partial"
    elif check.missing:
        check.status = "missing"
    else:
        check.status = "ready"
    return check


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate staged NPC model sources")
    parser.add_argument("--apply", action="store_true", help="write source_validation.json")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found: {MANIFEST_PATH}")
        return 1

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    checks = [check_character(e) for e in manifest["characters"]]

    report = {
        "project": manifest["project"],
        "generated": manifest["generated"],
        "summary": {
            "total": len(checks),
            "staged": sum(1 for c in checks if c.status == "staged"),
            "ready": sum(1 for c in checks if c.status == "ready"),
            "partial": sum(1 for c in checks if c.status == "partial"),
            "missing": sum(1 for c in checks if c.status == "missing"),
            "warnings": sum(len(c.warnings) for c in checks),
        },
        "checks": [asdict(c) for c in checks],
    }

    print(f"NPC source validation ({len(checks)} characters)")
    print(f"  staged : {report['summary']['staged']}")
    print(f"  ready  : {report['summary']['ready']}")
    print(f"  partial: {report['summary']['partial']}")
    print(f"  missing: {report['summary']['missing']}")
    print(f"  warnings: {report['summary']['warnings']}")
    for c in checks:
        if c.status != "staged":
            print(f"  [{c.status:>7}] {c.character}")
            for m in c.missing:
                print(f"           missing: {m}")
            for w in c.warnings:
                print(f"           warn: {w}")

    if args.apply:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nReport written: {REPORT_PATH}")

    return 0 if report["summary"]["missing"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
