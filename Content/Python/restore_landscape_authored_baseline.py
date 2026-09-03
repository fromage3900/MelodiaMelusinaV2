"""Restore the authored Landscape master without rebuilding its material graph.

This intentionally duplicates package assets through Unreal's AssetTools API.
It never calls either graph-clearing landscape builder and leaves a uniquely
named copy of the current safe fallback before replacing the active package.
Run only with the editor closed through UnrealEditor-Cmd.
"""

import unreal


MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
ACTIVE = f"{MASTER_DIR}/M_Master_Toon_Landscape_HeightBlend"
AUTHORED = f"{MASTER_DIR}/M_Master_Toon_Landscape_HeightBlend_BACKUP_20260728"
SAFE_BASE = f"{MASTER_DIR}/M_Master_Toon_Landscape_HeightBlend_SAFE_FALLBACK_20260729"


def unique_asset_path(base_path: str) -> str:
    if not unreal.EditorAssetLibrary.does_asset_exist(base_path):
        return base_path
    suffix = 2
    while unreal.EditorAssetLibrary.does_asset_exist(f"{base_path}_{suffix:02d}"):
        suffix += 1
    return f"{base_path}_{suffix:02d}"


def duplicate_asset(source_path: str, destination_path: str):
    source = unreal.EditorAssetLibrary.load_asset(source_path)
    if not source:
        raise RuntimeError(f"Unable to load {source_path}")
    if not isinstance(source, unreal.Material):
        raise RuntimeError(f"Expected a Material at {source_path}, got {source.get_class().get_name()}")

    destination_dir, destination_name = destination_path.rsplit("/", 1)
    copied = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(
        destination_name, destination_dir, source
    )
    if not copied:
        raise RuntimeError(f"Duplicate failed: {source_path} -> {destination_path}")
    unreal.EditorAssetLibrary.save_loaded_asset(copied)
    return copied


def main():
    authored = unreal.EditorAssetLibrary.load_asset(AUTHORED)
    active = unreal.EditorAssetLibrary.load_asset(ACTIVE)
    if not isinstance(authored, unreal.Material):
        raise RuntimeError("The authored backup is missing or is not a Material.")
    if not isinstance(active, unreal.Material):
        raise RuntimeError("The active safe fallback is missing or is not a Material.")

    safe_path = unique_asset_path(SAFE_BASE)
    duplicate_asset(ACTIVE, safe_path)
    unreal.log(f"[LandscapeRestore] Preserved safe fallback at {safe_path}")

    # Existing material instances continue to reference this exact package path.
    # The active graph is deleted only after the fallback duplicate is saved.
    if not unreal.EditorAssetLibrary.delete_asset(ACTIVE):
        raise RuntimeError(f"Unable to remove active material package: {ACTIVE}")

    restored = duplicate_asset(AUTHORED, ACTIVE)
    unreal.EditorAssetLibrary.save_loaded_asset(restored)
    unreal.log(f"[LandscapeRestore] Restored authored master at {ACTIVE}")
    unreal.log("[LandscapeRestore] No material graph was cleared or regenerated.")


main()
