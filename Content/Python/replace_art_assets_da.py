"""Replace greybox 'Art' assets with cozy JRPG baroque morning Megascans/project assets.

Replaces placeholder meshes (Rock01_Art, Stone01_Art, Bush01_Art, Tree01_Art,
GenericFlower1, etc.) with recommended Megascans and project assets.

Run inside UE editor:
    import replace_art_assets_da as rada
    rada.run()
"""

from __future__ import annotations

import unreal

# Recommended assets per category for cozy JRPG baroque morning
RECOMMENDED = {
    "Flowers": [
        "/Game/Megascans/3D_Plants/WhiteWindflower/SM_WhiteWindflower_01",
        "/Game/Megascans/3D_Plants/WhiteWindflower/SM_WhiteWindflower_02",
        "/Game/Megascans/3D_Plants/WhiteWindflower/SM_WhiteWindflower_03",
        "/Game/Megascans/3D_Plants/CloverVarieties/SM_CloverVarieties_01",
        "/Game/Megascans/3D_Plants/CloverVarieties/SM_CloverVarieties_02",
        "/Game/Megascans/3D_Plants/LilyOfTheValley/SM_LilyOfTheValley_01",
        "/Game/Megascans/3D_Plants/LilyOfTheValley/SM_LilyOfTheValley_02",
    ],
    "Bushes": [
        "/Game/Megascans/3D_Plants/EuropeanHornbeam/Geometry/SimpleWind/SM_EuropeanHornbeam_Sapling_01",
        "/Game/Megascans/3D_Plants/EuropeanHornbeam/Geometry/SimpleWind/SM_EuropeanHornbeam_Sapling_02",
        "/Game/Megascans/3D_Plants/Elderberry/SM_Elderberry_01",
        "/Game/Megascans/3D_Plants/Elderberry/SM_Elderberry_02",
        "/Game/Megascans/3D_Plants/DragonTree/SM_DragonTree_01",
        "/Game/Megascans/3D_Plants/BeechFern/SM_BeechFern_01",
        "/Game/Megascans/3D_Plants/BeechFern/SM_BeechFern_02",
        "/Game/Megascans/3D_Plants/SilverLadyFern/SM_SilverLadyFern_01",
    ],
    "Small Rocks": [
        "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_01",
        "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_02",
        "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_03",
        "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_01",
        "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_02",
        "/Game/Megascans/3D_Assets/ForestRockSlab/SM_ForestRockSlab_01",
        "/Game/Megascans/3D_Assets/ForestRockShelf/SM_ForestRockShelf_01",
    ],
    "Big Rocks": [
        "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_04",
        "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_05",
        "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_06",
        "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_03",
        "/Game/Megascans/3D_Assets/ForestRockShelf/SM_ForestRockShelf_01",
        "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_01",
        "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_02",
    ],
}

# Crystal garden specific assets
CRYSTAL_RECOMMENDED = {
    "Small Rocks": [
        "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_01",
        "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_02",
        "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_03",
        "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_01",
        "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_02",
        "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_01",
        "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_02",
    ],
    "Big Rocks": [
        "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_04",
        "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_05",
        "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_06",
        "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_03",
        "/Game/Megascans/3D_Assets/ForestRockShelf/SM_ForestRockShelf_01",
        "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_01",
        "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_02",
    ],
}

DAS = {
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_RockScatter": RECOMMENDED,
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_MorningBiome": RECOMMENDED,
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_CrystalGarden": CRYSTAL_RECOMMENDED,
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_DistantForest": RECOMMENDED,
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_IslandGrove": None,  # Skip - keep original Megascans
}


def _filter_existing(paths: list[str]) -> list[str]:
    existing = []
    for p in paths:
        if unreal.EditorAssetLibrary.does_asset_exist(p):
            existing.append(p)
        else:
            unreal.log_warning(f"[REPLACE] asset missing: {p}")
    return existing


def _replace_category(da, category: str, mesh_paths: list[str], weights: list[float] = None) -> int:
    """Replace all entries in a category with new Megascans meshes.

    Uses first existing entry as template for struct type.
    Returns number of entries added.
    """
    if weights is None:
        weights = [1.0] * len(mesh_paths)

    # Get template from any non-empty category
    template = None
    for cat in ["Small Rocks", "Big Rocks", "Flowers", "Bushes"]:
        try:
            arr = da.get_editor_property(cat)
            if len(arr) > 0:
                template = arr[0]
                break
        except Exception:
            continue

    if template is None:
        unreal.log_error(f"[REPLACE] no template found in {da.get_name()}")
        return 0

    original_mesh = template.get_editor_property('mesh')
    original_weight = template.get_editor_property('weight')

    # Build new array
    new_arr = []
    for i, mesh_path in enumerate(mesh_paths):
        if not unreal.EditorAssetLibrary.does_asset_exist(mesh_path):
            continue
        mesh = unreal.load_asset(mesh_path)
        if mesh is None:
            continue

        # Modify template
        template.set_editor_property('mesh', mesh)
        w = weights[i] if i < len(weights) else 1.0
        template.set_editor_property('weight', w)

        # Append (creates copy)
        new_arr.append(template)

        # Restore template
        template.set_editor_property('mesh', original_mesh)
        template.set_editor_property('weight', original_weight)

    if new_arr:
        da.set_editor_property(category, new_arr)

    return len(new_arr)


def replace_da(da_path: str, recommended: dict) -> dict:
    """Replace greybox assets with recommended Megascans assets in a DA."""
    da = unreal.EditorAssetLibrary.load_asset(da_path)
    if da is None:
        return {"status": "FAILED", "reason": f"DA not found: {da_path}"}

    results = {"da": da_path, "categories": {}}

    for category, mesh_paths in recommended.items():
        existing_paths = _filter_existing(mesh_paths)
        if not existing_paths:
            results["categories"][category] = 0
            continue

        n = _replace_category(da, category, existing_paths)
        results["categories"][category] = n
        unreal.log(f"[REPLACE] {da_path}: {category} -> {n} Megascans entries")

    # Save
    if any(v > 0 for v in results["categories"].values()):
        unreal.EditorAssetLibrary.save_asset(da_path, False)
        results["status"] = "OK"
        unreal.log(f"[REPLACE] saved {da_path}")
    else:
        results["status"] = "NO_CHANGES"

    return results


def run() -> dict:
    results = {}
    for da_path, recommended in DAS.items():
        if recommended is None:
            results[da_path] = {"status": "SKIPPED (keeping original)"}
            continue
        results[da_path] = replace_da(da_path, recommended)
    return results


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))