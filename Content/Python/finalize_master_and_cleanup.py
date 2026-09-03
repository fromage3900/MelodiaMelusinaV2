"""Wire compositing-library defaults on M_Master_Toon_Universal (no engine checkerboard/white).

Replaces any DefaultTexture / WhiteSquare fallbacks with /Game/Textures catalog paths
via portfolio_texture_catalog.apply_master_defaults(force=True).

Does NOT delete instance folders — use archive_unused_instances.py for that.

Headless:
  UnrealEditor-Cmd BS_GodFile.uproject -ExecutePythonScript=".../finalize_master_and_cleanup.py"
    -unattended -nullrhi
"""
from __future__ import annotations

import unreal

import material_lib as lib
import portfolio_texture_catalog as catalog

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
SAFE_MASTERS = [
    MASTER,
    "/Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Unified",
]


def fix_master_textures() -> dict[str, dict[str, str]]:
    results: dict[str, dict[str, str]] = {}
    for base in SAFE_MASTERS:
        if not unreal.EditorAssetLibrary.does_asset_exist(base):
            unreal.log_warning(f"[Finalize] missing {base}")
            continue
        leaf = base.rsplit("/", 1)[-1]
        mat = unreal.load_asset(f"{base}.{leaf}")
        if not mat:
            continue
        wired = catalog.apply_master_defaults(mat, base, force=True)
        lib.save_package(mat)
        results[base] = wired
        unreal.log(f"[Finalize] {base}: {len(wired)} compositing textures")
    return results


def main():
    try:
        unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
    except Exception as exc:
        unreal.log_warning(f"[Finalize] registry: {exc}")

    results = fix_master_textures()
    total = sum(len(v) for v in results.values())
    unreal.log(f"[Finalize] compositing defaults wired={total} across {len(results)} masters")
    print(f"FINALIZE_OK compositing_textures={total}")


if __name__ == "__main__":
    main()
