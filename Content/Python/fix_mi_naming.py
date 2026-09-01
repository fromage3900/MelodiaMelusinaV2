#!/usr/bin/env python3
"""fix_mi_naming.py — Scan Content/ for .uassets, identify MI_<Stem>_<Variant> violations, generate rename plan."""

import os
import re
import json
from pathlib import Path
from datetime import datetime, timezone

CONTENT_DIR = Path("Content")
AUDIT_DIR = Path("Saved") / "Audit"
LOG_FILE = AUDIT_DIR / "mi_naming_fix_2026-08-30.json"

# Regex for valid naming: MI_<Stem>_<Variant>
pattern = re.compile(r'^MI_([^_]+)_([^_]+)$')


def main():
    if not CONTENT_DIR.exists():
        print(f"Content directory {CONTENT_DIR} does not exist.")
        return

    violations = []
    uasset_files = list(CONTENT_DIR.rglob("*.uasset"))

    for filepath in uasset_files:
        try:
            rel_path = filepath.relative_to(CONTENT_DIR)
        except ValueError:
            continue

        stem = filepath.stem
        if not pattern.fullmatch(stem):
            parts = stem.split('_')
            if len(parts) >= 3:
                stem_part = parts[1]
                variant_part = parts[2]
                new_stem = f"MI_{stem_part}_{variant_part}"
            elif len(parts) >= 2:
                stem_part = parts[1]
                variant_part = "default"
                new_stem = f"MI_{stem_part}_{variant_part}"
            else:
                new_stem = "MI_unknown"

            new_filename = new_stem + ".uasset"
            original_path_str = str(CONTENT_DIR / rel_path)
            new_path_str = str(rel_path.with_name(new_filename))

            violations.append({
                "original_path": original_path_str,
                "new_path": new_path_str,
                "violation_reason": "does not match MI_<Stem>_<Variant> pattern",
                "expected_pattern": "MI_<Stem>_<Variant>"
            })

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_violations": len(violations),
        "violations": violations
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Renaming plan generated with {len(violations)} violations. Log saved to {LOG_FILE}")


if __name__ == "__main__":
    main()