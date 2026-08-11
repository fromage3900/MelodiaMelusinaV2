"""Reparent material instances from deprecated M_Master_Toon_Unified to M_Master_Toon_Universal.

Run in editor:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/reparent_unified_instances.py"
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "reparent_unified_instances.json"

OLD_PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Unified.M_Master_Toon_Unified"
NEW_PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal"
INST_ROOT = "/Game/EnvSandbox/Materials/Instances"


def main() -> int:
    import unreal

    new_parent = unreal.load_asset(NEW_PARENT)
    if not new_parent:
        raise RuntimeError(f"Missing canonical master: {NEW_PARENT}")

    report: dict = {"reparented": [], "skipped": [], "errors": []}

    if not unreal.EditorAssetLibrary.does_directory_exist(INST_ROOT):
        report["errors"].append(f"missing folder: {INST_ROOT}")
        return 1

    for path in unreal.EditorAssetLibrary.list_assets(INST_ROOT, recursive=True, include_folder=False):
        if not path.endswith((".MI_",)) and "/MI_" not in path:
            continue
        asset = unreal.load_asset(path)
        if not isinstance(asset, unreal.MaterialInstanceConstant):
            continue
        parent = asset.get_editor_property("parent")
        if not parent:
            report["skipped"].append({"instance": path, "reason": "no_parent"})
            continue
        parent_path = parent.get_path_name().split(".", 1)[0]
        if not parent_path.endswith("M_Master_Toon_Unified"):
            continue
        unreal.MaterialEditingLibrary.set_material_instance_parent(asset, new_parent)
        unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        report["reparented"].append(path)
        unreal.log(f"[Reparent] {path} -> Universal")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
