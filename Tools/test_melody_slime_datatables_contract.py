#!/usr/bin/env python3
"""Offline checks for the Melody Slime DataTable materialization pipeline."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "Content" / "Python"
HEADER = ROOT / "Plugins" / "MelodiaCore" / "Source" / "MelodiaCore" / "MelodiaSlimeDataRows.h"
SCRIPT = PYTHON / "import_melody_slime_datatables.py"
sys.path.insert(0, str(PYTHON))

import import_melody_slime_datatables as importer  # noqa: E402


def main() -> int:
    sources, errors = importer.load_all_sources()
    assert not errors, errors
    assert importer.DEST == "/Game/Melodia/DataStuctures"
    assert {
        name: len(source["rows"]) for name, source in sources.items()
    } == {
        "DT_MelodySlime_Enemies": 48,
        "DT_MelodySlime_Skills": 24,
        "DT_MelodySlime_RoomMods": 21,
    }

    header = HEADER.read_text(encoding="utf-8")
    for struct_name in (
        "FMelodiaSlimeEnemyRow",
        "FMelodiaSlimeSkillRow",
        "FMelodiaSlimeRoomModRow",
    ):
        assert f"struct MELODIACORE_API {struct_name} : public FTableRowBase" in header
        assert f"GENERATED_BODY()" in header
    for field in {
        field
        for spec in importer.TABLES.values()
        for field in spec["fields"]
    }:
        assert f" {field}" in header or f"\t{field}" in header, field

    script = SCRIPT.read_text(encoding="utf-8")
    for marker in (
        "resolve_row_struct",
        "DataTableFactory",
        "set_editor_property(\"struct\"",
        "fill_from_json_string",
        "json.dumps(source[\"import_rows\"]",
        "save_loaded_asset",
        "readback_ok",
        "cleanup_new_assets",
        "row_struct_unavailable_compile_required",
    ):
        assert marker in script, marker
    assert "/Game/Melodia/DataStructures" not in script
    assert "make_directory(DEST)" not in script

    # Offline execution must refuse before any editor mutation.
    assert importer.main() == 2
    try:
        importer.resolve_row_struct("FMelodiaSlimeEnemyRow")
    except RuntimeError as exc:
        assert "unreal_module_unavailable" in str(exc)
    else:
        raise AssertionError("missing Unreal module must fail closed")

    print("validated Melody Slime sources, row schemas, destination, and fail-closed gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
