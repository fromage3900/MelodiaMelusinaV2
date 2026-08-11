#!/usr/bin/env python3
"""
battleui_debris.py — remove 12 dead-exec-island node fragments in
BP_MelodiaBattleUI (Task 1, SONNET_CORE_MECHANICS_2026-08-08.md).

These are leftover fragments of the parent's implementations, partially
pasted into the child and never connected to any event entry. The parent
implements the real behaviour; these fragments never executed.

Follows the battleui_unshadow.py fail-closed shape: re-derive the dead set
from a fresh export_graph (never trust a hardcoded snapshot), abort on any
mismatch, fingerprint before/after, batch remove with compile_on_complete,
verify absence with the corrected (non-JSON) check, save, verify saved.
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3] / "Tools"))
from mcp_client import monolith  # noqa: E402
import graph_reachability as gr  # noqa: E402

BP = "/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI"

# Snapshot from the handoff — CROSS-CHECK ONLY, not truth.
EXPECTED_SNAPSHOT = {
    "K2Node_CallFunction_2", "K2Node_CallFunction_25", "K2Node_CallFunction_28",
    "K2Node_AssignDelegate_2", "K2Node_AddDelegate_3",
    "K2Node_CallFunction_54",
    "K2Node_AddDelegate_0",
    "K2Node_CallFunction_40",
    "K2Node_CallFunction_13",
    "K2Node_AddDelegate_5",
    "K2Node_CallFunction_30",
    "K2Node_CallFunction_7",
}


def err(msg):
    print(f"[debris] FAIL: {msg}")
    sys.exit(1)


def call(args):
    r = monolith("blueprint_query", args)
    if isinstance(r, str) and r.startswith("ERROR"):
        err(f"transport: {r[:200]}")
    try:
        return json.loads(r) if isinstance(r, str) else r
    except json.JSONDecodeError:
        err(f"unparseable response: {str(r)[:200]}")


def derive_dead_ids():
    """Fresh export_graph -> forward+backward exec reachability from every
    event entry -> exec-capable nodes not reachable. Mirrors
    graph_reachability.py's _scan_graph exactly (same module, reused)."""
    raw = monolith("blueprint_query", {"action": "export_graph", "asset_path": BP, "graph_name": "EventGraph"})
    data = json.loads(raw) if isinstance(raw, str) else raw
    nodes = data.get("nodes", data.get("nodes_data", []))

    exec_downstream, exec_upstream, node_map = {}, {}, {}
    for node in nodes:
        uid = node.get("uuid", node.get("node_id", node.get("id", node.get("name", ""))))
        node_map[uid] = node
        exec_downstream.setdefault(uid, set())
        exec_upstream.setdefault(uid, set())
        for pin in node.get("pins", []):
            pin_type = pin.get("pin_type", pin.get("type", ""))
            if pin_type not in ("exec", "EGPD_Output", "EGPD_Input"):
                continue
            direction = pin.get("direction", "")
            conns = pin.get("connections", pin.get("connected_to", pin.get("links", [])))
            if direction in ("output", "EGPD_Output"):
                for conn in conns:
                    target = conn if isinstance(conn, str) else conn.get("target_uuid", conn.get("target_node", conn.get("node_id", "")))
                    if isinstance(target, str) and "." in target:
                        target = target.split(".")[0]
                    if target:
                        exec_downstream[uid].add(target)
                        exec_upstream.setdefault(target, set()).add(uid)

    event_entries = [n.get("uuid", n.get("node_id", n.get("id", n.get("name", ""))))
                      for n in nodes if gr._looks_like_event(n)]
    for node in nodes:
        uid = node.get("uuid", node.get("node_id", node.get("id", node.get("name", ""))))
        if uid in event_entries:
            continue
        cls = node.get("class", "")
        title = node.get("title", node.get("name", "")) or ""
        if cls == "K2Node_VariableSet" and ("Event" in title or "On" in title):
            has_exec_input = any(
                p.get("pin_type", p.get("type", "")) in ("exec", "EGPD_Input")
                and p.get("direction", "") in ("input", "EGPD_Input")
                and p.get("connections", p.get("connected_to", []))
                for p in node.get("pins", [])
            )
            if not has_exec_input:
                event_entries.append(uid)

    reachable = set()
    stack = list(event_entries)
    while stack:
        uid = stack.pop()
        if uid in reachable:
            continue
        reachable.add(uid)
        for pred in exec_upstream.get(uid, set()):
            if pred not in reachable:
                stack.append(pred)
        for succ in exec_downstream.get(uid, set()):
            if succ not in reachable:
                stack.append(succ)

    dead = set()
    for node in nodes:
        uid = node.get("uuid", node.get("node_id", node.get("id", node.get("name", ""))))
        cls = node.get("class", node.get("node_class", ""))
        has_exec = any(p.get("pin_type", p.get("type", "")) in ("exec", "EGPD_Output", "EGPD_Input")
                       for p in node.get("pins", []))
        if not has_exec:
            continue
        if cls in ("K2Node_Comment", "K2Node_Reroute", "K2Node_TunnelBoundary", "K2Node_Tunnel", "K2Node_Knot"):
            continue
        if uid in event_entries:
            continue
        if uid not in reachable:
            dead.add(uid)
    return dead


def main():
    go = "--go" in sys.argv
    if not go:
        print("[debris] DRY RUN -- pass --go to apply")

    dead = derive_dead_ids()
    print(f"[debris] re-derived {len(dead)} dead node(s) from fresh export_graph")

    if dead != EXPECTED_SNAPSHOT:
        missing = EXPECTED_SNAPSHOT - dead
        extra = dead - EXPECTED_SNAPSHOT
        err(f"recomputed set differs from handoff snapshot -- graph moved. "
            f"missing={missing} extra={extra}. STOP, do not proceed, do not auto-fix.")
    print("[debris] recomputed set matches handoff snapshot exactly (12/12)")

    if not go:
        print(f"[debris] would remove {len(dead)} node(s); compile; save")
        return

    before = call({"action": "get_graph_fingerprint", "asset_path": BP, "mode": "topology"})
    ops = [{"op": "remove_node", "node_id": nid} for nid in dead]
    d = call({"action": "batch_execute", "asset_path": BP,
              "operations": ops, "compile_on_complete": True})
    if d.get("failed"):
        err(f"batch_execute reported {d['failed']} failure(s): {json.dumps(d)[:400]}")
    if not d.get("compile_success"):
        err(f"compile not clean: {json.dumps(d.get('compile_result'))[:400]}")
    print(f"[debris] removed {d.get('succeeded')} node(s); compile clean")

    after = call({"action": "get_graph_fingerprint", "asset_path": BP, "mode": "topology"})
    if before == after:
        err("fingerprint unchanged -- removal did not land")

    # Absence check. get_node_details answers a missing node with the plain
    # string "Node not found: X" -- not JSON, not an {"error":...} dict. Must
    # not go through call(), which would fail on this success path.
    still = []
    for nid in dead:
        raw = monolith("blueprint_query", {"action": "get_node_details",
                                           "asset_path": BP, "node_id": nid})
        text = raw if isinstance(raw, str) else json.dumps(raw)
        if "not found" not in text.lower():
            still.append(nid)
    if still:
        err(f"nodes still present after removal: {still}")
    print(f"[debris] confirmed absent: {len(dead)} node(s)")

    saved = call({"action": "save_asset", "asset_path": BP})
    if not saved.get("saved"):
        err(f"save failed or inconclusive: {json.dumps(saved)[:200]}")
    print("[debris] saved. Re-run Tools/graph_reachability.py --bp " + BP)


if __name__ == "__main__":
    main()
