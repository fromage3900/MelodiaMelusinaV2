"""Integrate Megascans rock meshes + MIs into PCG_Biome_RockScatter spawner.

Replaces greybox kit rocks (SM_SM_Rock_1/2/3) with Megascans rock formations.
Run inside UE editor:
    import integrate_megascans_rock_scatter as irs
    irs.run()
"""

from __future__ import annotations

import unreal

GRAPH_PATH = "/Game/Melodia/PCG/MassiveBiome/PCG_Biome_RockScatter"

# Megascans rock meshes available on disk (verified listing)
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
]

# Matching Megascans material instances
MEGASCANS_ROCK_MIS = [
    "/Game/Megascans/3D_Assets/ForestRockFormation/MI_ForestRockFormation_01",
    "/Game/Megascans/3D_Assets/ForestRockFormation/MI_ForestRockFormation_02",
    "/Game/Megascans/3D_Assets/ForestRockFormation/MI_ForestRockFormation_03",
    "/Game/Megascans/3D_Assets/ForestRockFormation/MI_ForestRockFormation_04",
    "/Game/Megascans/3D_Assets/ForestRockFormation/MI_ForestRockFormation_05",
    "/Game/Megascans/3D_Assets/MossyForestBoulder/MI_MossyForestBoulder_01",
    "/Game/Megascans/3D_Assets/MossyForestBoulder/MI_MossyForestBoulder_02",
    "/Game/Megascans/3D_Assets/MossyForestBoulder/MI_MossyForestBoulder_03",
    "/Game/Megascans/3D_Assets/BeachSandWithPebbles/MI_BeachSandWithPebbles_01",
]


def _load(path: str):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        raise FileNotFoundError(f"Asset not found: {path}")
    return asset


def _filter_existing(paths: list[str]) -> list[str]:
    existing = []
    for p in paths:
        if unreal.EditorAssetLibrary.does_asset_exist(p):
            existing.append(p)
        else:
            unreal.log_warning(f"[ROCK] asset missing on disk: {p}")
    return existing


def _get_settings_safe(node):
    cls_name = node.get_class().get_name()
    if "Subgraph" in cls_name:
        return None
    try:
        return node.get_settings()
    except Exception:
        return None


def _make_entry(mesh_path: str, material_path: str | None, weight: int) -> object:
    entry = unreal.PCGMeshSelectorWeightedEntry()
    mesh = unreal.load_asset(mesh_path)
    desc = entry.get_editor_property("descriptor")
    desc.set_editor_property("static_mesh", mesh)
    if material_path and unreal.EditorAssetLibrary.does_asset_exist(material_path):
        mat = unreal.load_asset(material_path)
        if mat:
            for prop in ("material_overrides", "override_materials", "material_override"):
                try:
                    desc.set_editor_property(prop, [mat] if prop.endswith("s") else mat)
                    break
                except Exception:
                    continue
    entry.set_editor_property("descriptor", desc)
    entry.set_editor_property("weight", weight)
    return entry


def _configure_spawner(spawner_settings, meshes: list[str], mis: list[str]) -> bool:
    if not spawner_settings:
        unreal.log_error("[ROCK] spawner_settings is None")
        return False

    entries = []
    weight = max(1, 8 - len(meshes))
    for i, mesh_path in enumerate(meshes):
        mi_path = mis[i % len(mis)] if mis else None
        try:
            entry = _make_entry(mesh_path, mi_path, weight)
            entries.append(entry)
            weight = max(1, weight - 1)
        except Exception as exc:  # noqa: BLE001
            unreal.log_warning(f"[ROCK] entry {i} failed: {exc}")
            continue

    if not entries:
        unreal.log_warning("[ROCK] no valid entries")
        return False

    try:
        selector = spawner_settings.get_editor_property("mesh_selector_parameters")
        selector.set_editor_property("mesh_entries", entries)
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning(f"[ROCK] mesh_selector_parameters failed: {exc}")
        return False
    return True


def run() -> dict:
    graph = _load(GRAPH_PATH)
    meshes = _filter_existing(MEGASCANS_ROCK_MESHES)
    mis = _filter_existing(MEGASCANS_ROCK_MIS)

    if not meshes:
        return {"status": "FAILED", "reason": "no Megascans rock meshes on disk"}

    results = {"graph": GRAPH_PATH, "meshes": len(meshes), "materials": len(mis), "spawners_updated": 0}

    for node in list(graph.get_editor_property("nodes")):
        settings = _get_settings_safe(node)
        if settings is None:
            continue
        cls_name = settings.get_class().get_name()
        if "StaticMeshSpawner" not in cls_name:
            continue

        ok = _configure_spawner(settings, meshes, mis)
        if ok:
            results["spawners_updated"] += 1
            unreal.log(f"[ROCK] updated spawner node {node.get_name()} with {len(meshes)} Megascans meshes")

    if results["spawners_updated"] > 0:
        unreal.EditorAssetLibrary.save_asset(GRAPH_PATH, False)
        results["status"] = "OK"
        unreal.log(f"[ROCK] saved {GRAPH_PATH}")
    else:
        results["status"] = "NO_SPAWNER_FOUND"

    return results


if __name__ == "__main__":
    print(run())
