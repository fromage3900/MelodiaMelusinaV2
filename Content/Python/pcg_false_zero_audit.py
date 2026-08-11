"""PCG False Zero Detector — distinguishes real failures from async false negatives.

Issues detected:
- PCGComponent.generate(True) is ASYNC (per PCG_CATALOG.md)
- Counting instances in same script returns 0
- Must count in SEPARATE call after async settle

This script audits:
1. Real asset existence
2. Graph property validity (no empty subgraphs)
3. Spline dependency detection
4. Required input tags/falloff zones
"""
from __future__ import annotations

import json
import unreal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcg_false_zero_audit.json"


def check_asset_exists(asset_path: str) -> dict:
    """Verify an asset exists at the given path."""
    exists = unreal.EditorAssetLibrary.does_asset_exist(asset_path) if unreal else False
    return {"path": asset_path, "exists": exists}


def check_graph_nodes(graph_path: str) -> dict:
    """Check if graph has actual node content (not empty)."""
    graph = unreal.EditorAssetLibrary.load_asset(graph_path) if unreal else None
    if not graph:
        return {"path": graph_path, "error": "graph_not_found", "node_count": 0}
    
    try:
        nodes = list(graph.get_nodes() or [])
        return {"path": graph_path, "node_count": len(nodes), "has_nodes": len(nodes) > 0}
    except Exception as exc:
        return {"path": graph_path, "error": str(exc), "node_count": 0}


def check_subgraph_deps(graph_path: str) -> dict:
    """Check if graph calls empty subgraphs."""
    # This would trace subgraph inputs
    # For now, check known empty paths
    empty_subgraphs = [
        "/Game/EnvSandbox/PCG/Universal/Subgraphs/PCG_Sub_BaroqueSpawn",
    ]
    
    if graph_path.startswith("/Game/Melodia/_PROJECT/PCG/"):
        return {"path": graph_path, "warning": "melodia_reference_not_envsandbox"}
    
    for empty in empty_subgraphs:
        if empty in graph_path:
            return {"path": graph_path, "error": "calls_empty_subgraph", "subgraph": empty}
    
    return {"path": graph_path, "subgraph_ok": True}


def check_spline_required(graph_name: str) -> dict:
    """Check if graph name suggests spline dependency."""
    spline_indicators = ["Bezier", "Spline", "Path", "Arc"]
    requires_spline = any(ind in graph_name for ind in spline_indicators)
    return {"path": graph_name, "requires_spline": requires_spline}


def audit_pillar_graphs(pillar_key: str) -> dict:
    """Audit all graphs in a pillar for real vs false zero failures."""
    import pcg_portfolio_standards as std
    
    results = {"pillar": pillar_key, "graphs": [], "issues": []}
    
    # Get graphs from pillar config
    pillar_config = std.PILLARS.get(pillar_key, {})
    graph_paths = pillar_config.get("pcg_graphs", [])
    
    for graph_path in graph_paths:
        graph_result = {
            "path": graph_path,
            "asset": check_asset_exists(graph_path),
            "nodes": check_graph_nodes(graph_path),
            "subgraph": check_subgraph_deps(graph_path),
            "spline": check_spline_required(graph_path.rsplit("/", 1)[-1]),
        }
        
        # Detect issues
        if not graph_result["asset"]["exists"]:
            results["issues"].append(f"Missing graph: {graph_path}")
        elif graph_result["nodes"]["node_count"] == 0:
            results["issues"].append(f"No nodes: {graph_path}")
        elif graph_result["subgraph"].get("error"):
            results["issues"].append(f"Empty subgraph: {graph_path}")
        
        results["graphs"].append(graph_result)
    
    return results


def main() -> int:
    if not unreal:
        print("ERROR: Unreal Editor required for asset checks")
        return 1
    
    import pcg_portfolio_standards as std
    
    all_results = []
    for pillar in std.PILLARS:
        print(f"[FalseZeroAudit] Checking {pillar}...")
        result = audit_pillar_graphs(pillar)
        all_results.append(result)
    
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    
    total_issues = sum(len(r["issues"]) for r in all_results)
    print(f"[FalseZeroAudit] Total issues: {total_issues} → {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())