"""Guarded NiagaraFluids template promotion for Water v10.

Default behavior is a read-only discovery pass. Use ``--apply`` only from a
single clean editor session after the C++ module is loaded. Engine templates
are never edited; the script duplicates them into project-owned assets.
"""

from __future__ import annotations

import json
import sys

import unreal


TARGETS = {
    ("Grid2D_FLIP_Pool",): "/Game/EnvSandbox/Water/v10/FLIP/NS_WaterV10_FLIP2D_Pool",
    ("Grid2D_FLIP_Splash",): "/Game/EnvSandbox/Water/v10/FLIP/NS_WaterV10_FLIP2D_Splash",
    ("Grid3D_FLIP_Pool", "Grid3D_Flip_Pool"): "/Game/EnvSandbox/Water/v10/FLIP/NS_WaterV10_FLIP3D_Pool",
    ("Grid3D_FLIP_Splash", "Grid3D_Flip_Splash"): "/Game/EnvSandbox/Water/v10/FLIP/NS_WaterV10_FLIP3D_Splash",
}


def find_template(asset_names: tuple[str, ...]) -> tuple[str, str]:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    # UE 5.8 changed get_assets_by_class from a string class name to a
    # TopLevelAssetPath.  Query the mounted NiagaraFluids content path instead
    # so this remains valid across editor Python builds and never touches the
    # engine assets themselves.
    for data in registry.get_assets_by_path("/NiagaraFluids", recursive=True):
        name = str(data.asset_name)
        # AssetData.object_path was removed in UE 5.8. package_name is already
        # the loadable object path and is the form duplicate_asset expects.
        path = str(data.package_name)
        if name in asset_names and "/Templates/Liquid/" in path:
            return path, name
    return "", ""


def main() -> int:
    apply_changes = "--apply" in sys.argv
    report = {"apply": apply_changes, "assets": [], "ok": True}

    for source_names, target_path in TARGETS.items():
        source_path, source_name = find_template(source_names)
        item = {"name": source_names[0], "accepted_names": list(source_names), "source": source_path, "target": target_path}
        if not source_path:
            item["status"] = "missing_template"
            report["ok"] = False
        elif not apply_changes:
            item["status"] = "ready_for_duplication"
        elif unreal.EditorAssetLibrary.does_asset_exist(target_path):
            item["status"] = "already_exists"
        else:
            unreal.EditorAssetLibrary.make_directory("/Game/EnvSandbox/Water/v10/FLIP")
            created = unreal.EditorAssetLibrary.duplicate_asset(source_path, target_path)
            item["status"] = "duplicated" if created else "duplicate_failed"
            report["ok"] = report["ok"] and bool(created)
        report["assets"].append(item)

    unreal.log(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
