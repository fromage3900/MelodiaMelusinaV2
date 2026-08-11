#!/usr/bin/env python3
"""
sir_cleanup.py — remove legacy dead nodes from BP_MelodiaSirMelodiousMorningIntro.

Verified (Saved/Sessions/2026-08-07/_sirmel_full.txt + compiled MorningIntro export):
- K2Node_CustomEvent_1 (HandleMorningIntroEnded) has no callers.
- K2Node_CallFunction_1 (Begin Window Departure) has no exec input.
- The MorningIntro Quill script is the departure authority (emits
  melodia:battle:melodia_smoke_encounter); no travel / BeginWindowDeparture path exists.

Removal is only safe if both nodes are fully disconnected (no exec in, no exec out,
no data consumers). Fail-closed: verify first, abort on any connection.

Usage:
  python Docs/T3D_Patterns/wiring/sir_cleanup.py          # dry run
  python Docs/T3D_Patterns/wiring/sir_cleanup.py --go     # apply
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3] / "Tools"))
from mcp_client import monolith  # noqa: E402

BP = "/Game/MelodiaIntegration/Blueprints/Opening/BP_MelodiaSirMelodiousMorningIntro"
TARGETS = {
    "K2Node_CustomEvent_1": "HandleMorningIntroEnded",
    "K2Node_CallFunction_1": "Begin Window Departure",
}


def err(msg):
    print(f"[sir] FAIL: {msg}")
    sys.exit(1)


def main():
    go = "--go" in sys.argv
    if not go:
        print("[sir] DRY RUN — pass --go to apply")

    d = {}
    for nid, title in TARGETS.items():
        r = monolith("blueprint_query", {"action": "get_node_details", "asset_path": BP, "node_id": nid})
        try:
            d[nid] = json.loads(r) if isinstance(r, str) else r
        except json.JSONDecodeError:
            err(f"unparseable get_node_details for {nid}: {r[:200]}")
        if not isinstance(d[nid], dict) or d[nid].get("error"):
            err(f"node {nid} ({title}) not found — graph moved; re-export and re-derive")

    for nid, title in TARGETS.items():
        pins = d[nid].get("pins", [])
        wired = [p["name"] for p in pins if p.get("connected_to")]
        if wired:
            err(f"node {nid} ({title}) still has connections: {wired} — not safe to remove")
        print(f"[sir] verified disconnected: {nid} ({title})")

    if not go:
        print("[sir] ops: remove HandleMorningIntroEnded + Begin Window Departure; compile; fingerprint; save")
        return

    before = monolith("blueprint_query", {"action": "get_graph_fingerprint", "asset_path": BP, "mode": "topology"})
    ops = [{"op": "remove_node", "node_id": nid} for nid in TARGETS]
    r = monolith("blueprint_query", {"action": "batch_execute", "asset_path": BP, "operations": ops, "compile_on_complete": False})
    d2 = json.loads(r) if isinstance(r, str) else r
    if not isinstance(d2, dict) or d2.get("errors"):
        err(f"batch_execute failed: {json.dumps(d2)[:500]}")
    print(f"[sir] removed: {json.dumps(d2.get('results', d2))[:300]}")

    r = monolith("blueprint_query", {"action": "compile_blueprint", "asset_path": BP})
    d3 = json.loads(r) if isinstance(r, str) else r
    if not isinstance(d3, dict) or d3.get("error_count", 1) != 0:
        err(f"compile not clean: {json.dumps(d3)[:500]}")
    print(f"[sir] compile clean: {d3}")

    after = monolith("blueprint_query", {"action": "get_graph_fingerprint", "asset_path": BP, "mode": "topology"})
    if before == after:
        err("fingerprint unchanged — removal did not land")
    print(f"[sir] fingerprint moved: {str(before)[:40]} -> {str(after)[:40]}")

    r = monolith("blueprint_query", {"action": "save_asset", "asset_path": BP})
    d4 = json.loads(r) if isinstance(r, str) else r
    if not (isinstance(d4, dict) and d4.get("success")):
        print("[sir] save_asset inconclusive — falling back to run_python save")
        monolith("editor_query", {"action": "run_python",
                                  "code": "import unreal; unreal.EditorAssetLibrary.save_loaded_asset('/Game/MelodiaIntegration/Blueprints/Opening/BP_MelodiaSirMelodiousMorningIntro')"})
    print("[sir] DONE. Re-run Docs/T3D_Patterns/wiring/verify_battle_closure.py + reachability lint.")


if __name__ == "__main__":
    main()
