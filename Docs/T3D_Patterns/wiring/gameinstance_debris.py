#!/usr/bin/env python3
"""
gameinstance_debris.py — remove the orphaned shouldLoadTransform_0 /
shouldLoadEnemyPawns_0 setter pair + 3 dead Print String nodes in
BP_MelodiaJRPGGameInstance (Task 2, SONNET_CORE_MECHANICS_2026-08-08.md).

All 16 event entries in this Blueprint are wired and the two flags above have
many LIVE setters elsewhere in the save flow -- only this one orphaned pair
(K2Node_VariableSet_12 -> K2Node_VariableSet_28, HEAD unwired, tail goes
nowhere) plus 3 Print String debris nodes are dead. Do not wire the pair into
anything -- there is no missing behaviour to restore here.

Same fail-closed shape as battleui_debris.py: re-derive from a fresh
export_graph, abort on any mismatch with the handoff snapshot, fingerprint
before/after, batch remove, verify absence, save, verify saved.
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3] / "Tools"))
from mcp_client import monolith  # noqa: E402
import graph_reachability as gr  # noqa: E402

BP = "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance"

EXPECTED_SNAPSHOT = {
    "K2Node_VariableSet_12", "K2Node_VariableSet_28",
    "K2Node_CallFunction_74", "K2Node_CallFunction_75", "K2Node_CallFunction_76",
}


def err(msg):
    print(f"[gi-debris] FAIL: {msg}")
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
    raw = monolith("blueprint_query", {"action": "export_graph", "asset_path": BP, "graph_name": "EventGraph"})
    data = json.loads(raw) if isinstance(raw, str) else raw
    nodes = data.get("nodes", data.get("nodes_data", []))

    exec_downstream, exec_upstream = {}, {}
    for node in nodes:
        uid = node.get("uuid", node.get("node_id", node.get("id", node.get("name", ""))))
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
        print("[gi-debris] DRY RUN -- pass --go to apply")

    dead = derive_dead_ids()
    print(f"[gi-debris] re-derived {len(dead)} dead node(s) from fresh export_graph")

    if dead != EXPECTED_SNAPSHOT:
        missing = EXPECTED_SNAPSHOT - dead
        extra = dead - EXPECTED_SNAPSHOT
        err(f"recomputed set differs from handoff snapshot -- graph moved. "
            f"missing={missing} extra={extra}. STOP, do not proceed, do not auto-fix.")
    print("[gi-debris] recomputed set matches handoff snapshot exactly")

    if not go:
        print(f"[gi-debris] would remove {len(dead)} node(s); compile; save")
        return

    before = call({"action": "get_graph_fingerprint", "asset_path": BP, "mode": "topology"})
    ops = [{"op": "remove_node", "node_id": nid} for nid in dead]
    d = call({"action": "batch_execute", "asset_path": BP,
              "operations": ops, "compile_on_complete": True})
    if d.get("failed"):
        err(f"batch_execute reported {d['failed']} failure(s): {json.dumps(d)[:400]}")
    if not d.get("compile_success"):
        err(f"compile not clean: {json.dumps(d.get('compile_result'))[:400]}")
    print(f"[gi-debris] removed {d.get('succeeded')} node(s); compile clean")

    after = call({"action": "get_graph_fingerprint", "asset_path": BP, "mode": "topology"})
    if before == after:
        err("fingerprint unchanged -- removal did not land")

    still = []
    for nid in dead:
        raw = monolith("blueprint_query", {"action": "get_node_details",
                                           "asset_path": BP, "node_id": nid})
        text = raw if isinstance(raw, str) else json.dumps(raw)
        if "not found" not in text.lower():
            still.append(nid)
    if still:
        err(f"nodes still present after removal: {still}")
    print(f"[gi-debris] confirmed absent: {len(dead)} node(s)")

    saved = call({"action": "save_asset", "asset_path": BP})
    if not saved.get("saved"):
        err(f"save failed or inconclusive: {json.dumps(saved)[:200]}")
    print("[gi-debris] saved. Re-run Tools/graph_reachability.py --bp " + BP)


if __name__ == "__main__":
    main()
