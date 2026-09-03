#!/usr/bin/env python3
"""
battleui_unshadow.py — remove empty custom events in BP_MelodiaBattleUI that
shadow working implementations in its parent, BP_BattleUI.

THE DEFECT

BP_MelodiaBattleUI is a child of BP_BattleUI_C and re-declares 28 of the
parent's custom events. Ten of those re-declarations have an empty body: the
event node exists, and its `then` exec output goes nowhere.

A same-named custom event in a child replaces the parent's in the generated
class. So BP_BattleController's `ShowBattleUI` call -- which dispatches on the
live object, a BP_MelodiaBattleUI -- runs the child's empty body, and the
parent's implementation (which creates and binds the rhythm highway) never
executes. That is why the battle UI does not appear.

Removing a child override is the whole fix: with no override present, the call
resolves to the parent's working implementation. Nothing is added to compensate.

WHY FAIL-CLOSED

An empty event is only safe to remove if it is genuinely empty AND nothing binds
to it. `then` unwired proves the first; `OutputDelegate` unwired proves the
second (a bound event has a consumer on that pin). Any connection on any pin
aborts the whole run before the graph is touched.

Usage:
  python Docs/T3D_Patterns/wiring/battleui_unshadow.py         # dry run
  python Docs/T3D_Patterns/wiring/battleui_unshadow.py --go    # apply
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3] / "Tools"))
from mcp_client import monolith  # noqa: E402

CHILD = "/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI"
PARENT = "/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI"

# Expected custom_name per node id. The id is how we address the node; the name
# is what we VERIFY before removing anything -- node ids in these graphs have
# drifted before, and Decision 024 forbids trusting them as identity.
TARGETS = {
    "K2Node_CustomEvent_0":  "ShowBattleUI",
    "K2Node_CustomEvent_2":  "HideSkills",
    "K2Node_CustomEvent_3":  "ShowUsableItemInventory",
    "K2Node_CustomEvent_7":  "HideSkillActionButtons",
    "K2Node_CustomEvent_9":  "UnbindAllItemEvents",
    "K2Node_CustomEvent_13": "UpdateTargetUnitBattleDetails",
    "K2Node_CustomEvent_15": "UpdateAttackingUnitBattleDetails",
    "K2Node_CustomEvent_16": "UnbindAllSkillEvents",
    "K2Node_CustomEvent_22": "HideUsableItemInventory",
    "K2Node_CustomEvent_23": "HideItemsActionButtons",
}

EVENTISH = ("K2Node_Event", "K2Node_CustomEvent", "K2Node_ComponentBoundEvent")


def err(msg):
    print(f"[unshadow] FAIL: {msg}")
    sys.exit(1)


def call(args):
    r = monolith("blueprint_query", args)
    if isinstance(r, str) and r.startswith("ERROR"):
        err(f"transport: {r[:200]}")
    try:
        return json.loads(r) if isinstance(r, str) else r
    except json.JSONDecodeError:
        err(f"unparseable response: {str(r)[:200]}")


def parent_live_events():
    """Names the parent implements with a wired body. Removing a child override
    is only safe if the parent actually has something to fall back to."""
    d = call({"action": "export_graph", "asset_path": PARENT, "graph_name": "EventGraph"})
    live = set()
    for n in d["nodes"]:
        if n["class"] not in EVENTISH:
            continue
        outs = [p for p in n.get("pins", [])
                if p.get("type") == "exec" and p.get("direction") == "output"]
        if any(p.get("connected_to") for p in outs):
            live.add((n.get("title") or "").split("\n")[0].strip())
    return live


def main():
    go = "--go" in sys.argv
    if not go:
        print("[unshadow] DRY RUN -- pass --go to apply")

    parent_ok = parent_live_events()
    print(f"[unshadow] parent implements {len(parent_ok)} wired events")

    details = {}
    for nid, expected in TARGETS.items():
        d = call({"action": "get_node_details", "asset_path": CHILD, "node_id": nid})
        if not isinstance(d, dict) or d.get("error"):
            err(f"{nid} ({expected}) not found -- graph moved; re-export and re-derive")
        actual = d.get("custom_name")
        if actual != expected:
            err(f"{nid} is '{actual}', expected '{expected}' -- node ids have drifted, "
                "re-derive the target list from a fresh export")
        if expected not in parent_ok:
            err(f"parent has no wired '{expected}' to fall back to -- removing the child "
                "override would delete the behaviour outright, not restore it")
        wired = [p["name"] for p in d.get("pins", []) if p.get("connected_to")]
        if wired:
            err(f"{nid} ({expected}) has connections {wired} -- not an empty override")
        details[nid] = expected
        print(f"[unshadow] verified empty + parent has impl: {expected}")

    if not go:
        print(f"[unshadow] would remove {len(details)} shadowing events; compile; save")
        return

    before = call({"action": "get_graph_fingerprint", "asset_path": CHILD, "mode": "topology"})
    ops = [{"op": "remove_node", "node_id": nid} for nid in details]
    d = call({"action": "batch_execute", "asset_path": CHILD,
              "operations": ops, "compile_on_complete": True})
    if d.get("failed"):
        err(f"batch_execute reported {d['failed']} failure(s): {json.dumps(d)[:400]}")
    if not d.get("compile_success"):
        err(f"compile not clean: {json.dumps(d.get('compile_result'))[:400]}")
    print(f"[unshadow] removed {d.get('succeeded')} node(s); compile clean")

    after = call({"action": "get_graph_fingerprint", "asset_path": CHILD, "mode": "topology"})
    if before == after:
        err("fingerprint unchanged -- removal did not land")

    # Absence check. NOTE: get_node_details answers a missing node with a plain
    # string ("Node not found: X"), not JSON and not an {"error":...} dict, so
    # this must not go through call() -- doing so fails on the success path.
    still = []
    for nid in TARGETS:
        raw = monolith("blueprint_query", {"action": "get_node_details",
                                           "asset_path": CHILD, "node_id": nid})
        text = raw if isinstance(raw, str) else json.dumps(raw)
        if "not found" not in text.lower():
            still.append(nid)
    if still:
        err(f"nodes still present after removal: {still}")
    print(f"[unshadow] confirmed absent: {len(TARGETS)} node(s)")

    saved = call({"action": "save_asset", "asset_path": CHILD})
    if not saved.get("saved"):
        err(f"save failed or inconclusive: {json.dumps(saved)[:200]}")
    print("[unshadow] saved. Re-run Tools/graph_reachability.py --bp " + CHILD)


if __name__ == "__main__":
    main()
