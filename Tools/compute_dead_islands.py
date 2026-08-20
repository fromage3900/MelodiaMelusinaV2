"""Compute genuinely dead (unreachable) expression islands on the Universal master.

Repo-side, read-only. Uses the full connection graph
(Saved/Audit/universal_full_graph.json, from material_query get_full_connection_graph)
to compute which expressions have NO path to any material output.

Schema in the dump:
  {"asset_path": ..., "connections": [
     {"from": "MaterialExpressionComponentMask_148", "from_output_index": 0,
      "from_output": "None", "to": "MaterialExpressionStaticSwitchParameter_48",
      "to_input": "True"}, ...]}
Outputs are found by scanning expressions for MaterialOutput / SubstrateToonBSDF
classes; the dump also exposes expression classes via get_all_expressions.

Prints the verified dead-island list for Phase 3 deletion.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from pathlib import Path

GRAPH = Path(__file__).resolve().parents[1] / "Saved" / "Audit" / "universal_full_graph.json"
EXPRS = sorted((Path(__file__).resolve().parents[1] / "Saved" / "Audit").glob("master_graphs_*/M_Master_Toon_Universal.json"))

OUTPUT_CLASSES = ("MaterialExpressionMaterialOutput", "MaterialExpressionSubstrateToonBSDF",
                  "MaterialExpressionSubstrateFrontMaterial", "MaterialExpressionFrontMaterial")


def main() -> int:
    graph = json.loads(GRAPH.read_text(encoding="utf-8-sig"))
    conns = graph.get("connections") or []

    # Node classes from the export (name -> class)
    classes: dict[str, str] = {}
    exprs_file = sorted(EXPRS)[-1]
    export = json.loads(exprs_file.read_text(encoding="utf-8"))
    for e in export["get_all_expressions"].get("expressions") or []:
        classes[e.get("name")] = e.get("class") or ""

    nodes = set(classes.keys())
    for c in conns:
        nodes.add(c.get("from"))
        nodes.add(c.get("to"))

    adj: dict[str, list[str]] = defaultdict(list)
    rev: dict[str, list[str]] = defaultdict(list)
    for c in conns:
        src, dst = c.get("from"), c.get("to")
        if src and dst:
            adj[src].append(dst)
            rev[dst].append(src)

    # Seeds: output-class nodes.
    seeds = [n for n in nodes if any(oc in classes.get(n, "") for oc in OUTPUT_CLASSES)]

    reachable: set[str] = set()
    dq = deque(seeds)
    while dq:
        cur = dq.popleft()
        if cur in reachable:
            continue
        reachable.add(cur)
        for nxt in rev.get(cur, []):
            if nxt not in reachable:
                dq.append(nxt)

    dead = sorted(n for n in nodes if n not in reachable)

    # Cluster check: a node is a *safe-to-delete island* when all of its
    # consumers are dead too (it cannot feed anything live).
    safe: list[str] = []
    for i in dead:
        consumers = adj.get(i, [])
        if not consumers or all(c in dead for c in consumers):
            safe.append(i)

    print(json.dumps({
        "node_count": len(nodes),
        "reachable": len(reachable),
        "dead_count": len(dead),
        "dead": dead,
        "safe_islands": safe,
    }, indent=1))


if __name__ == "__main__":
    raise SystemExit(main())
