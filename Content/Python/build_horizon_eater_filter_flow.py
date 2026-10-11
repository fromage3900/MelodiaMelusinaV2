"""Build PCG_HorizonEater_FilterFlow graph — Phase 2 of the Horizon System Plan.

Re-wires the existing PCG nodes (filter bypassed unless use_filter=True):
  CreatePoints -> [FilterByAttribute] -> TransformPoints -> StaticMeshSpawner -> Output

Run inside the editor (Monolith run_python):
  import build_horizon_eater_filter_flow as b; b.build()
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

GRAPH_PATH = "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_HorizonEater_FilterFlow"
REPORT = Path(__file__).resolve().parents[1] / ".." / "Saved" / "Audit" / "horizon_eater_filter_flow.json"


def build(use_filter: bool = False) -> dict:
    """Wire the PCG_HorizonEater_FilterFlow graph nodes."""
    import unreal

    g = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    if g is None:
        raise RuntimeError(f"Graph not found: {GRAPH_PATH}")

    output_node = g.get_output_node()

    # Find existing nodes by settings class. The node SETTINGS (CreatePoints
    # translation/bounds, spawner mesh) were authored in-editor and are not
    # reproduced by this script, so existing nodes are re-wired, never rebuilt.
    nodes_by_type = {}
    for n in g.nodes:
        class_name = n.get_settings().get_class().get_name()
        if class_name not in nodes_by_type:
            nodes_by_type[class_name] = n

    n_create = nodes_by_type.get("PCGCreatePointsSettings")
    n_filter = nodes_by_type.get("PCGFilterByAttributeSettings")
    n_transform = nodes_by_type.get("PCGTransformPointsSettings")
    n_spawn = nodes_by_type.get("PCGStaticMeshSpawnerSettings")

    if not all([n_create, n_transform, n_spawn]):
        raise RuntimeError(f"Missing nodes. Found: {list(nodes_by_type.keys())}")

    # Pin labels follow every proven builder in this repo (build_pcg_escher.py,
    # build_pcg_carve_test.py, pcg_graph_builder.py): the OUTPUT node's input pin
    # is labelled "Out". PCG only executes nodes upstream of the output node, so a
    # spawner that is not wired to the output node generates nothing. The first
    # version of this script used "In" there and "Out" on the input node, which
    # left the saved graph with 3 edges and a disconnected spawner.
    #
    # CreatePoints is a source node (no input pin), so nothing is wired from the
    # graph input node.
    #
    # A DISABLED node emits nothing (Docs/Production/PCG/README.md section 3), so the
    # filter is bypassed rather than disabled. Pass use_filter=True only after its
    # attribute rule is configured, otherwise it can drop every point.
    chain = [n_create]
    if use_filter and n_filter is not None:
        chain.append(n_filter)
    chain += [n_transform, n_spawn]

    # Best-effort removal of stale edges between the known nodes (including the
    # old filter hop) so a rerun cannot leave a second path behind.
    stale_pairs = [
        (n_create, n_filter),
        (n_filter, n_transform),
        (n_create, n_transform),
        (n_transform, n_spawn),
        (n_spawn, output_node),
    ]
    for a, b in stale_pairs:
        if a is None or b is None:
            continue
        try:
            g.remove_edge(a, "Out", b, "Out" if b == output_node else "In")
            if b == output_node:
                g.remove_edge(a, "Out", b, "In")  # legacy wrong-label edge (2026-10-07 audit)
        except Exception:
            pass

    wired = []
    for a, b in zip(chain, chain[1:]):
        if g.add_edge(a, "Out", b, "In") is None:
            raise RuntimeError(f"add_edge failed: {a.get_name()} -> {b.get_name()}")
        wired.append(f"{a.get_name()} -> {b.get_name()}")
    if g.add_edge(chain[-1], "Out", output_node, "Out") is None:
        raise RuntimeError(f"add_edge failed: {chain[-1].get_name()} -> Output")
    wired.append(f"{chain[-1].get_name()} -> Output")

    unreal.EditorAssetLibrary.save_loaded_asset(g)

    result = {
        "ok": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "graph": GRAPH_PATH,
        "use_filter": use_filter,
        "nodes": [n.get_name() for n in chain],
        "edges": wired,
        "note": "wired only; generation is NOT proven until instances are read back on a later tick",
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"PCG_HorizonEater_FilterFlow wired | nodes={len(result['nodes'])} | edges={len(result['edges'])}")
    return result


if __name__ == "__main__":
    build()
