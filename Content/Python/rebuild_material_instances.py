"""Wipe the old instance sprawl and rebuild a tight, purposeful set on M_Master_Toon_Universal.

Delegates to starter_instances.py (canonical 10) + apply_starter_instances.build_starter_instances.
Does NOT delete legacy Environment uassets — use archive_unused_instances.py to move them.

Run in-editor:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/rebuild_material_instances.py"
"""
from __future__ import annotations

import unreal
import material_lib as lib
from starter_instances import SHOWCASE_DIR, STARTER_INSTANCES


def main():
    try:
        unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
    except Exception as e:
        unreal.log_warning(f"[Rebuild] registry scan: {e}")

    from starter_instances import MASTER

    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        unreal.log_error("[Rebuild] master missing — build M_Master_Toon_Universal first")
        return

    import apply_starter_instances as apply_mod

    results = apply_mod.build_starter_instances()
    names = [r["instance"] for r in results]
    unreal.log(f"[Rebuild] {len(names)} starter instances in {SHOWCASE_DIR}")
    print(f"REBUILD_OK starters = {len(names)}")
    print(f"STARTERS: {names}")
    print(f"PURPOSES:")
    for spec in STARTER_INSTANCES:
        print(f"  {spec['name']}: {spec.get('purpose', '')}")


if __name__ == "__main__":
    main()
