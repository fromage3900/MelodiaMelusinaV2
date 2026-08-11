"""Inventory Melodia _PROJECT/PCG reference graphs for salvage tiers.

  python Content/Python/audit_melodia_pcg_reference.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcg_portfolio_standards as std

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "melodia_pcg_reference.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def _audit_in_ue() -> dict:
    import unreal

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    try:
        ar.search_all_assets(True)
    except Exception:
        pass

    graphs: list[dict] = []
    collections: list[dict] = []
    test_levels: list[str] = []

    filter_data = unreal.ARFilter(
        package_paths=[std.MELODIA_PCG_ROOT],
        recursive_paths=True,
    )
    for asset_data in ar.get_assets(filter_data) or []:
        path = str(asset_data.package_name)
        name = path.rsplit("/", 1)[-1]
        cls = str(asset_data.asset_class_path.asset_name) if asset_data.asset_class_path else ""
        entry = {
            "path": path,
            "name": name,
            "class": cls,
            "tier": std.melodia_tier(name),
        }
        if "PCGGraph" in cls or name.startswith("PCG_"):
            if "Collection" in cls or name.startswith("PCGCol_"):
                collections.append(entry)
            elif name.startswith("L_PCGTest"):
                test_levels.append(path)
            else:
                node_types: list[str] = []
                if unreal.EditorAssetLibrary.does_asset_exist(path):
                    graph = unreal.load_asset(path)
                    if graph and hasattr(graph, "get_nodes"):
                        for node in graph.get_nodes() or []:
                            settings = node.get_settings() if hasattr(node, "get_settings") else None
                            if settings:
                                node_types.append(type(settings).__name__)
                entry["node_types"] = sorted(set(node_types))[:40]
                entry["node_count"] = len(entry["node_types"])
                graphs.append(entry)

    tier_counts: dict[str, int] = {}
    for g in graphs + collections:
        tier_counts[g["tier"]] = tier_counts.get(g["tier"], 0) + 1

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "root": std.MELODIA_PCG_ROOT,
        "graph_count": len(graphs),
        "collection_count": len(collections),
        "test_level_count": len(test_levels),
        "tier_counts": tier_counts,
        "graphs": sorted(graphs, key=lambda x: x["name"]),
        "collections": sorted(collections, key=lambda x: x["name"]),
        "test_levels": sorted(test_levels),
    }


def main() -> int:
    try:
        import unreal  # noqa: F401
        report = _audit_in_ue()
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"MELODIA_PCG_AUDIT_OK graphs={report['graph_count']} -> {REPORT}")
        return 0
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/audit_melodia_pcg_reference.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
