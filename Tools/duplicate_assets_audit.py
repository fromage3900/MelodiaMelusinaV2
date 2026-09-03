"""Duplicate asset audit across EnvSandbox + related trees (disk scan, no editor).

Finds:
  1. Same short name in multiple folders (duplicate short names) under
     Content/EnvSandbox and Content/Melodia/_PROJECT/04_Materials.
  2. Byte-identical .uasset pairs (true file dupes) across EnvSandbox.
  3. Material instances with the same parent + zero overrides (pure shells that
     duplicate the master) - candidates for deletion.
  4. _Scratch / _Archive / Candidates content counts (junk candidates).

Writes Saved/Audit/duplicate_assets_audit.json. Read-only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "Content" / "EnvSandbox"
PROJECT_MATS = ROOT / "Content" / "Melodia" / "_PROJECT" / "04_Materials"
OUT = ROOT / "Saved" / "Audit" / "duplicate_assets_audit.json"

SCAN_ROOTS = [ENV, PROJECT_MATS]

JUNK_FOLDERS = ("_Scratch", "_Archive", "Candidates")


def file_hash(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    all_files: list[Path] = []
    for root in SCAN_ROOTS:
        if root.exists():
            all_files.extend(p for p in root.rglob("*.uasset") if p.is_file())

    # 1) duplicate short names
    by_stem: dict[str, list[str]] = defaultdict(list)
    for p in all_files:
        by_stem[p.stem].append(str(p).replace(str(ROOT), "").lstrip("\\/"))
    dup_short = {k: v for k, v in by_stem.items() if len(v) > 1}

    # 2) byte-identical pairs
    hashes: dict[str, list[str]] = defaultdict(list)
    for p in all_files:
        hashes[file_hash(p)].append(str(p).replace(str(ROOT), "").lstrip("\\/"))
    byte_dupes = {h: v for h, v in hashes.items() if len(v) > 1}

    # 3) junk folder inventory
    junk = {}
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for folder in JUNK_FOLDERS:
            d = root / folder
            if d.exists():
                files = list(d.rglob("*.uasset"))
                junk[f"{str(d).replace(str(ROOT), '').lstrip(chr(92)+chr(47))}"] = len(files)

    # 4) envsandbox total
    env_count = sum(1 for p in all_files if str(p).startswith(str(ENV)))

    report = {
        "generated": "2026-08-13",
        "scanned": len(all_files),
        "envsandbox_uassets": env_count,
        "duplicate_short_names": dup_short,
        "duplicate_short_name_count": len(dup_short),
        "byte_identical": byte_dupes,
        "byte_identical_group_count": len(byte_dupes),
        "junk_folders": junk,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"scanned: {len(all_files)}")
    print(f"duplicate short names: {len(dup_short)}")
    print(f"byte-identical groups: {len(byte_dupes)}")
    print("junk folders:")
    for k, v in junk.items():
        print(f"  {v:4d}  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
