#!/usr/bin/env python3
"""Pure-stdlib source verifier for Melusina House GN discoverability.

This deliberately does not import bpy. It answers the question agents kept
getting wrong: are the expected source files, imports, category declarations,
builder registrations, presets, and front-door discovery hooks present?
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_FOUNDATION = [
    "MEL_mh_foundation_pod",
    "MEL_mh_foundation_cluster",
    "MEL_mh_foundation_porch",
    "MEL_mh_foundation_master",
]

HOUSE_MODULES = [
    ROOT / "deploy/surreal_arch/melodia_gn/melusina_house_foundation.py",
    ROOT / "deploy/surreal_arch/melodia_gn/melodia_house.py",
    ROOT / "deploy/surreal_arch/melodia_gn/melusina_house.py",
    ROOT / "deploy/surreal_arch/melodia_gn/house_dress.py",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def main() -> int:
    checks = []
    errors = []

    core = read(ROOT / "deploy/surreal_arch/melodia_gn/core.py")
    init = read(ROOT / "deploy/surreal_arch/melodia_gn/__init__.py")
    presets = read(ROOT / "deploy/surreal_arch/melodia_gn/presets.py")
    start = read(ROOT / "MELUSINA_HOUSE_GN_START_HERE.md")
    index = read(ROOT / "DOC_INDEX.md")
    cockpit = read(ROOT / "Docs/BLENDER_MELODIA_COCKPIT.md")

    def check(name: str, ok: bool, detail: str = ""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            errors.append(name)

    check("dedicated category", '"melusina_house"' in core)
    check("foundation module imported", "melusina_house_foundation" in init)
    check("root start-here exists", bool(start))
    check("DOC_INDEX discovery", "MELUSINA_HOUSE_GN_START_HERE.md" in index)
    check("Blender cockpit discovery", "MELUSINA_HOUSE_GN_START_HERE.md" in cockpit)

    foundation_text = read(HOUSE_MODULES[0])
    for builder_id in EXPECTED_FOUNDATION:
        check(f"builder source: {builder_id}", builder_id in foundation_text)
        check(f"preset source: {builder_id}", builder_id in presets)

    all_house = "\n".join(read(path) for path in HOUSE_MODULES)
    registered = sorted(set(re.findall(r'register_builder\(\s*["\']([^"\']+)', all_house)))
    house_ids = [name for name in registered if name.startswith("MEL_mh") or name == "MEL_melusina_house_round_interior"]
    check("house builders discovered", len(house_ids) >= 17, f"found={len(house_ids)}")
    check("dedicated category used by foundation", 'category="melusina_house"' in foundation_text)

    report = {
        "schema": "melodia.melusina_house_gn_catalog_verify.v1",
        "ok": not errors,
        "expected_foundation": EXPECTED_FOUNDATION,
        "registered_house_ids_found": house_ids,
        "checks": checks,
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
