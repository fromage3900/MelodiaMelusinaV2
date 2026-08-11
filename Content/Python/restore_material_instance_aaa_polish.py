"""Restore the previous live AAA polish pass from its audit report."""
from __future__ import annotations

import json
from pathlib import Path


def run() -> int:
    import unreal

    project = Path(__file__).resolve().parents[2]
    report = project / "Saved/Audit/material_instance_aaa_polish.json"
    data = json.loads(report.read_text(encoding="utf-8"))
    restored = 0
    for row in data.get("changes", []):
        asset = unreal.EditorAssetLibrary.load_asset(row["path"])
        if not asset:
            continue
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            asset, row["parameter"], float(row["old"])
        )
        unreal.EditorAssetLibrary.save_asset(row["path"])
        restored += 1
    unreal.log(f"Restored {restored} material-instance polish changes")
    return restored


if __name__ == "__main__":
    run()
