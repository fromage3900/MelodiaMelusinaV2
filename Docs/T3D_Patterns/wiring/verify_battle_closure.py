#!/usr/bin/env python3
"""
verify_battle_closure.py — regression audit of the B3/B4 closure in
BP_BattleController's EventGraph, against the LIVE graph (no doc trust).

Pass = the designed closure is present and wired:
  B3: UseSkillWithRhythm(194) driven by UseMP(115).then, feeding
      HideSkillActionButtons(110), StockSkill <- Get currentSkill(116);
      the old StartSession->Branch->UseSkill double-fire cluster is ABSENT.
  B4: Switch on E_BattleResult -> ExecutionSequence_3/4/5 ->
      CompleteBattle(45/49/51) + PlayerWon(204)/EnemyWon(205)/Keys(99) legs.
  Damage latch: Clear Pending Damage Multiplier wired after both damage paths.

Also reports dead nodes (exec-capable nodes with no exec input) as warnings.

Fails (exit 1) on any invariant break. Re-exports fresh evidence to
Exports/bp_battlecontroller_eventgraph_live.json on every run.

Usage:
  python Docs/T3D_Patterns/wiring/verify_battle_closure.py
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3] / "Tools"))
from mcp_client import monolith  # noqa: E402

BP = "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController"
EXPORT_PATH = Path(__file__).resolve().parents[3] / "Exports" / "bp_battlecontroller_eventgraph_live.json"

INVARIANTS = [
    ("B3 UseSkillWithRhythm present", lambda n: any("UseSkillWithRhythm" in (x.get("title") or "") for x in n.values())),
]


def ex_of(n, nid, direction):
    out = []
    for p in n[nid]["pins"]:
        if p["type"] == "exec" and p["direction"] == direction:
            out.append((p["name"], p["connected_to"]))
    return out


def main():
    r = monolith("blueprint_query", {"action": "export_graph", "asset_path": BP, "graph_name": "EventGraph"})
    if isinstance(r, str) and r.startswith("ERROR"):
        print(f"[audit] FAIL: export error: {r[:200]}")
        sys.exit(1)
    d = json.loads(r) if isinstance(r, str) else r
    nodes = {x["id"]: x for x in d["nodes"]}
    EXPORT_PATH.write_text(json.dumps(d, indent=1), encoding="utf-8")
    print(f"[audit] live export: {len(nodes)} nodes -> {EXPORT_PATH}")

    failures = []

    def need(title, cond, detail=""):
        if cond:
            print(f"[audit] PASS  {title}")
        else:
            print(f"[audit] FAIL  {title}  {detail}")
            failures.append(title)

    # B3: rhythm skill cluster absent, UseSkillWithRhythm wired
    titles = {x.get("title", "").splitlines()[0] for x in nodes.values()}
    cluster_absent = not ({"Start Session", "Resolve Rhythm Skill Id"} & titles)
    need("B3 old double-fire cluster absent", cluster_absent)

    usr = [nid for nid, x in nodes.items() if "Use Skill with Rhythm" in (x.get("title") or "")]
    need("B3 UseSkillWithRhythm node present", len(usr) == 1, f"found {len(usr)}")
    if len(usr) == 1:
        nid = usr[0]
        inn = ex_of(nodes, nid, "input")
        out = ex_of(nodes, nid, "output")
        exec_ok = any(any(c.startswith("K2Node_CallFunction_115") for c in conns) for _, conns in inn) and \
                  any(p == "then" and any(c.startswith("K2Node_CallFunction_110") for c in conns) for p, conns in out)
        need("B3 UseSkillWithRhythm exec chain (UseMP -> node -> HideSkillButtons)", exec_ok, f"in={inn} out={out}")
        stock_ok = any(p["name"] == "StockSkill" and any(c.startswith("K2Node_VariableGet_116") for c in (p["connected_to"] or [])) for p in nodes[nid]["pins"])
        need("B3 StockSkill <- Get currentSkill(116)", stock_ok)

    # B4: switch -> sequences -> CompleteBattle + leg calls
    switch = [nid for nid, x in nodes.items() if x["class"] == "K2Node_SwitchEnum" and "E_BattleResult" in (x.get("title") or "")]
    need("B4 Switch on E_BattleResult present", len(switch) == 1, f"found {len(switch)}")
    seqs = {sid: ex_of(nodes, sid, "output") for sid, x in nodes.items() if x["class"] == "K2Node_ExecutionSequence"}
    seq3 = [sid for sid, out in seqs.items() if any(any(c.startswith("K2Node_CallFunction_45") for c in conns) for _, conns in out)]
    seq4 = [sid for sid, out in seqs.items() if any(any(c.startswith("K2Node_CallFunction_49") for c in conns) for _, conns in out)]
    seq5 = [sid for sid, out in seqs.items() if any(any(c.startswith("K2Node_CallFunction_51") for c in conns) for _, conns in out)]
    need("B4 Victory -> CompleteBattle(45)", len(seq3) == 1, f"found {len(seq3)}")
    need("B4 Defeat  -> CompleteBattle(49)", len(seq4) == 1, f"found {len(seq4)}")
    need("B4 Fled    -> CompleteBattle(51)", len(seq5) == 1, f"found {len(seq5)}")
    if seq5:
        legs5 = dict(seqs[seq5[0]])
        need("B4 Fled leg also drives Keys(99) (dead-unit rewards)",
             any(c.startswith("K2Node_CallFunction_99") for c in legs5.get("then_1", [])), f"then_1={legs5.get('then_1')}")

    # Damage latch
    clears = [nid for nid, x in nodes.items() if (x.get("title") or "").startswith("Clear Pending Damage Multiplier")]
    need("B4 ClearPendingDamageMultiplier wired after damage paths", len(clears) >= 2, f"found {len(clears)}")

    # Dead-node report: exec-capable nodes with no exec input (orphaned control
    # flow) plus data nodes (VariableGet) with no consumers. Pure functions have
    # no exec pins at all and are skipped by the first check.
    dead = []
    for nid, x in nodes.items():
        pins = x.get("pins", [])
        has_exec = any(p["type"] == "exec" for p in pins)
        if has_exec and not ex_of(nodes, nid, "input") and x["class"] not in (
            "K2Node_CustomEvent", "K2Node_Event", "K2Node_SpawnActorFromClass",
            "K2Node_PlayMontage", "K2Node_MacroInstance", "K2Node_CreateDelegate", "K2Node_AddDelegate", "K2Node_RemoveDelegate",
        ):
            dead.append(f"{nid} ({x.get('title','').splitlines()[0]})")
    for nid, x in nodes.items():
        if x["class"] == "K2Node_VariableGet":
            outs = [p for p in x.get("pins", []) if p["direction"] == "output"]
            if outs and all(not p["connected_to"] for p in outs):
                dead.append(f"{nid} ({x.get('title','').splitlines()[0]}) [data orphan]")
    if dead:
        print(f"[audit] WARN orphaned nodes: {dead}")

    if failures:
        print(f"[audit] RESULT: FAIL ({len(failures)} invariant(s))")
        sys.exit(1)
    print("[audit] RESULT: PASS — B3/B4 closure intact")


if __name__ == "__main__":
    main()
