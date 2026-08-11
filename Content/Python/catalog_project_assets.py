"""Catalog-first inventory for Zen, Greybox, untitled, and PCG assets.

This script reads the Content tree only. It never renames, moves, deletes, or
saves Unreal assets. It is intentionally useful before a binary-asset cleanup.
"""
from __future__ import annotations
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "Content"
REPORT = ROOT / "Saved" / "Audit" / "project_asset_catalog.json"
UNTITLED = re.compile(r"^(untitled|newasset|copy|test|temp|default)([_ -]|$)", re.I)

def classify(path: Path) -> str:
    rel = path.relative_to(CONTENT).as_posix().lower()
    stem = path.stem.lower()
    if UNTITLED.match(stem) or "untitled" in stem:
        return "untitled_or_ambiguous"
    if "/zenforest" in rel or stem.startswith("l_zen"):
        return "canonical_production"
    if "/greybox_kit/" in rel:
        return "prototype_greybox"
    if "/pcg/" in rel or stem.startswith("pcg_"):
        return "pcg_support"
    if "/_legacy/" in rel or "legacy" in rel or "/_thirdparty/" in rel:
        return "legacy_reference"
    if "/environments/" in rel or stem.startswith("l_"):
        return "level_local_authored"
    return "unclassified"

def main() -> dict:
    assets = []
    for path in CONTENT.rglob("*"):
        if path.suffix.lower() not in {".uasset", ".umap", ".json"} or not path.is_file():
            continue
        rel = "/Game/" + path.relative_to(CONTENT).with_suffix("").as_posix()
        entry = {"path": rel, "disk_path": path.relative_to(ROOT).as_posix(),
                 "class_hint": path.suffix.lower()[1:], "bytes": path.stat().st_size,
                 "classification": classify(path), "proposed_name": None,
                 "dependency_audit": "editor_required"}
        if entry["classification"] == "untitled_or_ambiguous":
            entry["proposed_name"] = f"REVIEW_{path.stem}"
        assets.append(entry)
    counts = Counter(item["classification"] for item in assets)
    result = {"timestamp": datetime.now(timezone.utc).isoformat(),
              "root": str(CONTENT), "mutation": "none", "counts": dict(sorted(counts.items())),
              "assets": assets,
              "review_queues": {
                  "untitled_or_ambiguous": [a["path"] for a in assets if a["classification"] == "untitled_or_ambiguous"],
                  "binary_dependency_audit": [a["path"] for a in assets if a["class_hint"] in {"uasset", "umap"}],
              }}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"CATALOG_OK assets={len(assets)} categories={dict(counts)} report={REPORT}")
    return result

if __name__ == "__main__":
    main()
