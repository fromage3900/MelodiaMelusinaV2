"""Verify Megascans PCG integration across Morning biome graphs.

Checks:
  - PCG_Biome_RockScatter, PCG_Biome_MorningMeadow, PCG_Biome_CrystalGarden
    each have at least one spawner with Megascans mesh references
  - MI_MossyRock_21 / MI_Rock_01 reparented to M_Master_Toon_Universal

Run inside UE editor:
    import verify_megascans_pcg_integration as vmpi
    vmpi.run()
"""

from __future__ import annotations

import json
import unreal

GRAPHS = [
    "/Game/Melodia/PCG/MassiveBiome/PCG_Biome_RockScatter",
    "/Game/Melodia/PCG/MassiveBiome/PCG_Biome_MorningMeadow",
    "/Game/Melodia/PCG/MassiveBiome/PCG_Biome_CrystalGarden",
]
MEGASCANS_PREFIX = "/Game/Megascans"
TOON_UNIVERSAL_PATH = "/Game/Melodia/Materials/Masters/M_Master_Toon_Universal"


def _load(path: str):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        raise FileNotFoundError(f"Asset not found: {path}")
    return asset


def _find_asset(pattern: str) -> str | None:
    try:
        assets = unreal.EditorAssetLibrary.list_assets("/Game/Megascans", recursive=True)
    except Exception as exc:  # noqa: BLE001
        unreal.log_error(f"[VERIFY] list_assets failed: {exc}")
        return None
    pat = pattern.lower()
    for a in assets:
        if pat in a.lower():
            return a
    return None


def _get_settings_safe(node):
    cls_name = node.get_class().get_name()
    if "Subgraph" in cls_name:
        return None
    try:
        return node.get_settings()
    except Exception:
        return None


def _spawner_megascans_count(graph) -> dict:
    """Return {spawner_node_name: (mesh_count, megascans_mesh_count, megascans_material_count)}."""
    result = {}
    for node in list(graph.get_editor_property("nodes")):
        settings = _get_settings_safe(node)
        if settings is None:
            continue
        cls_name = settings.get_class().get_name()
        if "StaticMeshSpawner" not in cls_name:
            continue

        try:
            selector = settings.get_editor_property("mesh_selector_parameters")
            entries = selector.get_editor_property("mesh_entries")
        except Exception:
            continue

        mesh_count = 0
        mega_mesh = 0
        mega_mat = 0
        for entry in entries:
            try:
                desc = entry.get_editor_property("descriptor")
                mesh = desc.get_editor_property("static_mesh")
                mesh_count += 1
                mesh_path = str(mesh.get_path_name()) if mesh else ""
                if mesh_path.startswith(MEGASCANS_PREFIX):
                    mega_mesh += 1
                for prop in ("material_overrides", "override_materials", "material_override"):
                    try:
                        mats = desc.get_editor_property(prop)
                        if mats is None:
                            continue
                        if isinstance(mats, list):
                            for m in mats:
                                if m and str(m.get_path_name()).startswith(MEGASCANS_PREFIX):
                                    mega_mat += 1
                        else:
                            if mats and str(mats.get_path_name()).startswith(MEGASCANS_PREFIX):
                                mega_mat += 1
                        break
                    except Exception:
                        continue
            except Exception:
                continue

        result[node.get_name()] = (mesh_count, mega_mesh, mega_mat)

    return result


def _graph_node_types(graph) -> list[str]:
    """Return list of node settings class names found in graph (including subgraphs)."""
    types = []
    for node in list(graph.get_editor_property("nodes")):
        settings = _get_settings_safe(node)
        if settings is not None:
            types.append(settings.get_class().get_name())
        cls_name = node.get_class().get_name()
        if "Subgraph" in cls_name:
            try:
                subgraph = node.get_editor_property("subgraph")
                if subgraph:
                    types.append(f"SUBGRAPH:{node.get_name()}")
            except Exception:
                pass
    return types


def run() -> dict:
    report = {"graphs": {}, "materials": {}, "overall": "UNKNOWN"}

    all_ok = True
    for gpath in GRAPHS:
        try:
            graph = _load(gpath)
        except FileNotFoundError:
            report["graphs"][gpath] = {"status": "ASSET_NOT_FOUND"}
            all_ok = False
            continue

        node_types = _graph_node_types(graph)
        spawners = _spawner_megascans_count(graph)

        graph_info = {
            "node_types": node_types,
            "spawner_count": len(spawners),
        }

        if not spawners:
            graph_info["status"] = "NO_SPAWNERS"
            all_ok = False
        else:
            total_mega_mesh = sum(s[1] for s in spawners.values())
            total_mega_mat = sum(s[2] for s in spawners.values())
            graph_info["status"] = "OK" if total_mega_mesh > 0 else "NO_MEGASCANS_MESH"
            graph_info["spawners"] = {k: {"meshes": v[0], "megascans_meshes": v[1], "megascans_materials": v[2]} for k, v in spawners.items()}
            graph_info["total_megascans_meshes"] = total_mega_mesh
            graph_info["total_megascans_materials"] = total_mega_mat
            if total_mega_mesh == 0:
                all_ok = False

        report["graphs"][gpath] = graph_info

    # Material reparent check
    for pattern in ("MossyRock", "Rock_01"):
        path = _find_asset(pattern)
        if path is None:
            report["materials"][pattern] = {"status": "NOT_FOUND_ON_DISK"}
            all_ok = False
            continue
        mi = _load(path)
        parent_obj = mi.get_editor_property("parent")
        parent_repr = str(parent_obj) if parent_obj else "None"
        parent_path = str(parent_obj.get_path_name()) if parent_obj else "None"
        on_toon = TOON_UNIVERSAL_PATH in parent_repr or TOON_UNIVERSAL_PATH in parent_path
        report["materials"][path] = {"status": "ON_TOON_UNIVERSAL" if on_toon else "NOT_ON_TOON_UNIVERSAL", "parent": parent_path}
        if not on_toon:
            all_ok = False

    report["overall"] = "PASS" if all_ok else "FAIL"
    unreal.log(f"[VERIFY] overall: {report['overall']}")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
