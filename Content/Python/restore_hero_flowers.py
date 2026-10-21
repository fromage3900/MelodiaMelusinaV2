"""Restore GenericFlower1 and GenericFlowerTall as hero flowers in Data Assets.

Appends these two greybox flower assets back to the Flowers category.
Run inside UE editor:
    import restore_hero_flowers as rhf
    rhf.run()
"""

from __future__ import annotations

import unreal

HERO_FLOWERS = [
    ("/Game/EnvSandbox/Library/FoliageCards/GenericFlower1", 2.0),
    ("/Game/EnvSandbox/Library/FoliageCards/GenericFlowerTall", 1.0),
]

DAS_WITH_FLOWERS = [
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_RockScatter",
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_MorningBiome",
    "/Game/Melodia/PCG/MassiveBiome/DA_Melodia_DistantForest",
]


def run() -> dict:
    results = {}
    for da_path in DAS_WITH_FLOWERS:
        da = unreal.EditorAssetLibrary.load_asset(da_path)
        if da is None:
            results[da_path] = {"status": "NOT_FOUND"}
            continue

        # Get template from existing Flowers
        flowers = da.get_editor_property('Flowers')
        if len(flowers) == 0:
            # Try other categories
            for cat in ["Small Rocks", "Big Rocks", "Bushes"]:
                try:
                    arr = da.get_editor_property(cat)
                    if len(arr) > 0:
                        flowers = arr  # use as template source
                        break
                except Exception:
                    continue

        if len(flowers) == 0:
            results[da_path] = {"status": "NO_TEMPLATE"}
            continue

        template = flowers[0]
        original_mesh = template.get_editor_property('mesh')
        original_weight = template.get_editor_property('weight')

        # Get current Flowers array
        try:
            current_flowers = da.get_editor_property('Flowers')
        except Exception:
            current_flowers = []

        added = 0
        for mesh_path, weight in HERO_FLOWERS:
            if not unreal.EditorAssetLibrary.does_asset_exist(mesh_path):
                unreal.log_warning(f"[HERO] not found: {mesh_path}")
                continue

            # Check if already in array
            mesh = unreal.load_asset(mesh_path)
            already = False
            for entry in current_flowers:
                try:
                    if entry.get_editor_property('mesh') == mesh:
                        already = True
                        break
                except Exception:
                    pass
            if already:
                continue

            # Modify template
            template.set_editor_property('mesh', mesh)
            template.set_editor_property('weight', weight)

            # Append
            current_flowers.append(template)

            # Restore template
            template.set_editor_property('mesh', original_mesh)
            template.set_editor_property('weight', original_weight)

            added += 1
            unreal.log(f"[HERO] restored {mesh_path} to {da_path} Flowers")

        if added > 0:
            da.set_editor_property('Flowers', current_flowers)
            unreal.EditorAssetLibrary.save_asset(da_path, False)
            results[da_path] = {"status": "OK", "added": added}
        else:
            results[da_path] = {"status": "ALREADY_PRESENT"}

    return results


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))