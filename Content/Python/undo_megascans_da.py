"""Undo Megascans integration — remove all Megascans mesh entries from Data Assets.

Filters out entries whose mesh path starts with /Game/Megascans/.
Run inside UE editor:
    import undo_megascans_da as umda
    umda.run()
"""

from __future__ import annotations

import unreal

DAS = [
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_RockScatter",
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_MorningBiome",
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_CrystalGarden",
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_DistantForest",
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_IslandGrove",
]
CATEGORIES = ["Flowers", "Bushes", "Small Rocks", "Big Rocks"]
MEGASCANS_PREFIX = "/Game/Megascans"


def _remove_megascans_from_category(da, category: str) -> int:
    """Remove Megascans entries from a category. Returns count removed."""
    try:
        arr = da.get_editor_property(category)
    except Exception:
        return 0

    original_count = len(arr)
    filtered = []
    removed = 0
    for entry in arr:
        try:
            mesh = entry.get_editor_property('mesh')
            mesh_path = str(mesh.get_path_name()) if mesh else ""
            if mesh_path.startswith(MEGASCANS_PREFIX):
                removed += 1
            else:
                filtered.append(entry)
        except Exception:
            filtered.append(entry)

    if removed > 0:
        da.set_editor_property(category, filtered)

    return removed


def run() -> dict:
    results = {}
    for da_path in DAS:
        da = unreal.EditorAssetLibrary.load_asset(da_path)
        if da is None:
            results[da_path] = {"status": "NOT_FOUND"}
            continue

        cat_results = {}
        total_removed = 0
        for cat in CATEGORIES:
            removed = _remove_megascans_from_category(da, cat)
            cat_results[cat] = removed
            total_removed += removed

        if total_removed > 0:
            unreal.EditorAssetLibrary.save_asset(da_path, False)
            results[da_path] = {"status": "OK", "removed": total_removed, "categories": cat_results}
            unreal.log(f"[UNDO] removed {total_removed} Megascans entries from {da_path}")
        else:
            results[da_path] = {"status": "NO_MEGASCANS_FOUND", "removed": 0, "categories": cat_results}

    return results


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))