"""Integrate Megascans meshes into Melodia biome Data Assets.

Modifies DA_Melodia_RockScatter, DA_Melodia_MorningBiome, DA_Melodia_CrystalGarden
to include Megascans rock, plant, and crystal meshes alongside existing greybox meshes.

Uses the proven modify-append-restore pattern: modify an existing entry's mesh,
append to array (creates copy), restore original entry.

Run inside UE editor:
    import integrate_megascans_da as imda
    imda.run()
"""

from __future__ import annotations

import unreal

# Megascans mesh paths verified on disk
MEGASCANS_ROCK_MESHES = [
    "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_01",
    "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_02",
    "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_03",
    "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_04",
    "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_05",
    "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_06",
    "/Game/Megascans/3D_Assets/ForestRockSlab/SM_ForestRockSlab_01",
    "/Game/Megascans/3D_Assets/ForestRockShelf/SM_ForestRockShelf_01",
    "/Game/Megascans/3D_Assets/ForestRockShelf/SM_ForestRockShelf_02",
    "/Game/Megascans/3D_Assets/ForestRockWall/SM_ForestRockWall_01",
    "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_01",
    "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_02",
    "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_03",
    "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_01",
    "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_02",
    "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_03",
]

MEGASCANS_PLANT_MESHES = [
    "/Game/Megascans/3D_Plants/KikuyuGrass/SM_KikuyuGrass_01",
    "/Game/Megascans/3D_Plants/KikuyuGrass/SM_KikuyuGrass_02",
    "/Game/Megascans/3D_Plants/KikuyuGrass/SM_KikuyuGrass_03",
    "/Game/Megascans/3D_Plants/KikuyuGrass/SM_KikuyuGrass_04",
    "/Game/Megascans/3D_Plants/KikuyuGrass/SM_KikuyuGrass_07",
    "/Game/Megascans/3D_Plants/BeechFern/SM_BeechFern_01",
    "/Game/Megascans/3D_Plants/SilverLadyFern/SM_SilverLadyFern_01",
    "/Game/Megascans/3D_Plants/PinkCordyline/SM_PinkCordyline_01",
    "/Game/Megascans/3D_Plants/PurpleShamrock/SM_PurpleShamrock_01",
    "/Game/Megascans/3D_Plants/LilyOfTheValley/SM_LilyOfTheValley_01",
    "/Game/Megascans/3D_Plants/Periwinkle/SM_Periwinkle_01",
    "/Game/Megascans/3D_Plants/WhiteWindflower/SM_WhiteWindflower_01",
    "/Game/Megascans/3D_Plants/CloverVarieties/SM_CloverVarieties_01",
]

MEGASCANS_CRYSTAL_MESHES = [
    "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_01",
    "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_02",
    "/Game/Megascans/3D_Assets/ForestRockFormation/SM_ForestRockFormation_03",
    "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_01",
    "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_02",
    "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_03",
    "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_01",
    "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_02",
    "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_03",
]


def _filter_existing(paths: list[str]) -> list[str]:
    existing = []
    for p in paths:
        if unreal.EditorAssetLibrary.does_asset_exist(p):
            existing.append(p)
        else:
            unreal.log_warning(f"[MEGASCANS] asset missing on disk: {p}")
    return existing


def _add_meshes_to_category(da, category: str, mesh_paths: list[str], weight: float = 1.0) -> int:
    """Add Megascans meshes to a DA category using modify-append-restore pattern.

    Returns number of meshes successfully added.
    """
    try:
        arr = da.get_editor_property(category)
    except Exception as e:
        unreal.log_warning(f"[MEGASCANS] category '{category}' not found: {e}")
        return 0

    if len(arr) == 0:
        unreal.log_warning(f"[MEGASCANS] category '{category}' is empty, cannot use as template")
        return 0

    template = arr[0]
    original_mesh = template.get_editor_property('mesh')
    added = 0

    for mesh_path in mesh_paths:
        if not unreal.EditorAssetLibrary.does_asset_exist(mesh_path):
            unreal.log_warning(f"[MEGASCANS] mesh not found: {mesh_path}")
            continue

        mesh = unreal.load_asset(mesh_path)
        if mesh is None:
            unreal.log_warning(f"[MEGASCANS] failed to load: {mesh_path}")
            continue

        # Check if already in array
        already_exists = False
        for entry in arr:
            try:
                if entry.get_editor_property('mesh') == mesh:
                    already_exists = True
                    break
            except Exception:
                pass
        if already_exists:
            continue

        # Modify template
        template.set_editor_property('mesh', mesh)
        template.set_editor_property('weight', weight)

        # Append (creates copy)
        arr.append(template)

        # Restore template
        template.set_editor_property('mesh', original_mesh)
        template.set_editor_property('weight', arr[0].get_editor_property('weight') if len(arr) > 1 else 1.0)

        added += 1
        unreal.log(f"[MEGASCANS] added {mesh_path} to {category}")

    if added > 0:
        da.set_editor_property(category, arr)

    return added


def integrate_da(da_path: str, rock_meshes: list[str], plant_meshes: list[str], crystal_meshes: list[str]) -> dict:
    """Integrate Megascans meshes into a single Data Asset."""
    da = unreal.EditorAssetLibrary.load_asset(da_path)
    if da is None:
        return {"status": "FAILED", "reason": f"DA not found: {da_path}"}

    results = {"da": da_path, "categories": {}}

    # Determine which meshes to add to which categories
    # Rocks -> Small Rocks, Big Rocks
    # Plants -> Flowers, Bushes
    # Crystals -> Small Rocks, Big Rocks

    rock_existing = _filter_existing(rock_meshes)
    plant_existing = _filter_existing(plant_meshes)
    crystal_existing = _filter_existing(crystal_meshes)

    # Small Rocks: add rocks
    n = _add_meshes_to_category(da, 'Small Rocks', rock_existing, 1.0)
    results["categories"]["Small Rocks"] = n

    # Big Rocks: add rocks
    n = _add_meshes_to_category(da, 'Big Rocks', rock_existing, 0.8)
    results["categories"]["Big Rocks"] = n

    # Flowers: add plants
    n = _add_meshes_to_category(da, 'Flowers', plant_existing, 1.0)
    results["categories"]["Flowers"] = n

    # Bushes: add plants
    n = _add_meshes_to_category(da, 'Bushes', plant_existing, 1.0)
    results["categories"]["Bushes"] = n

    # Save
    if any(v > 0 for v in results["categories"].values()):
        unreal.EditorAssetLibrary.save_asset(da_path, False)
        results["status"] = "OK"
        unreal.log(f"[MEGASCANS] saved {da_path}")
    else:
        results["status"] = "NO_CHANGES"

    return results


def run() -> dict:
    # Filter mesh lists
    rock_meshes = _filter_existing(MEGASCANS_ROCK_MESHES)
    plant_meshes = _filter_existing(MEGASCANS_PLANT_MESHES)
    crystal_meshes = _filter_existing(MEGASCANS_CRYSTAL_MESHES)

    results = {}

    # RockScatter DA: rocks only
    results["RockScatter"] = integrate_da(
        "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_RockScatter",
        rock_meshes, [], []
    )

    # MorningBiome DA: rocks + plants
    results["MorningBiome"] = integrate_da(
        "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_MorningBiome",
        rock_meshes, plant_meshes, []
    )

    # CrystalGarden DA: crystals (rocks)
    results["CrystalGarden"] = integrate_da(
        "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_CrystalGarden",
        crystal_meshes, [], crystal_meshes
    )

    # DistantForest DA: rocks + plants
    results["DistantForest"] = integrate_da(
        "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_DistantForest",
        rock_meshes, plant_meshes, []
    )

    # IslandGrove DA: rocks only (already has Megascans plants)
    results["IslandGrove"] = integrate_da(
        "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_IslandGrove",
        rock_meshes, [], []
    )

    return results


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))