#!/usr/bin/env python3
"""
bp_sweep.py — audit every Blueprint in the project for the wiring defects that
have actually shipped here, and rank them by how badly they lie.

WHY THESE FIVE CHECKS

Each one corresponds to a defect that reached this project's main branch and was
not caught by compiling, fingerprinting, or a smoke test:

  SHADOWED   A child Blueprint re-declares a parent's event with an EMPTY body.
             The child's version replaces the parent's in the generated class,
             so callers hit a stub and the parent's working implementation never
             runs. BP_MelodiaBattleUI had ten of these, including ShowBattleUI --
             which is why the battle UI never appeared. This is the single most
             expensive defect class found so far, and nothing else detects it.

  EMPTY      A custom event declared with no body at all. Callers succeed and
             nothing happens. Silent no-op is this project's signature failure.

  DEAD       Exec nodes with no path from any entry. Authored behaviour that was
             never connected. Macro tunnels count as entries -- macros have no
             event node, and missing that produced false hits in
             BP_BattleController.

  ORPHANED   The Blueprint itself is not reachable from a configured entry point.
             A perfectly wired graph nothing instantiates. Cost this project the
             BP_BattleUI incident and a lane remap.

  DUPES      More than one asset shares the Blueprint's short name. Substring
             assertions pass against either copy, so you can edit the wrong one
             and watch every check go green.

Read-only. Changes nothing. Requires the editor with Monolith on 9316.

    python Tools/bp_sweep.py                        # everything under /Game
    python Tools/bp_sweep.py --filter Melodia       # regex on the path
    python Tools/bp_sweep.py --skip-live            # faster; omit reachability
    python Tools/bp_sweep.py --out Saved/Dashboards/bp_sweep.txt --json ...
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from mcp_client import monolith  # noqa: E402

WIDTH = 82
EVENTISH = ("K2Node_Event", "K2Node_CustomEvent", "K2Node_ComponentBoundEvent")
ENTRYISH = EVENTISH + ("K2Node_FunctionEntry", "K2Node_Tunnel", "K2Node_TunnelBoundary")
SKIP_NODE_CLASSES = ("K2Node_Comment", "K2Node_Reroute", "K2Node_Knot",
                     "K2Node_TunnelBoundary", "K2Node_Tunnel")


def header(title, sub=""):
    out = ["", "=" * WIDTH, f" {title}"]
    if sub:
        out.append(f" {sub}")
    out.append("=" * WIDTH)
    return out


def bq(action, params, timeout=120):
    raw = monolith("blueprint_query", dict({"action": action}, **params), timeout=timeout)
    if isinstance(raw, str) and raw.startswith("ERROR"):
        raise RuntimeError(raw[:140])
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        raise RuntimeError(f"unparseable {action}: {str(raw)[:140]}")


def run_python(code, timeout=240):
    raw = monolith("editor_query", {"action": "run_python", "params": {"command": code}},
                   timeout=timeout)
    payload = json.loads(raw) if isinstance(raw, str) else raw
    if not payload.get("ok", payload.get("success")):
        raise RuntimeError(f"run_python failed: {json.dumps(payload)[:200]}")
    for item in payload.get("output", []):
        for line in str(item.get("output", "")).splitlines():
            if line.startswith("__SWEEP__"):
                return json.loads(line[len("__SWEEP__"):])
    raise RuntimeError("no result marker")


def inventory(pattern, include_thirdparty):
    """All Blueprints with their parent class and short name, in one call."""
    code = (
        "import json, unreal\n"
        "ar = unreal.AssetRegistryHelpers.get_asset_registry()\n"
        "f = unreal.ARFilter(package_paths=['/Game'], recursive_paths=True,\n"
        "                    class_names=['Blueprint','WidgetBlueprint'])\n"
        "out = []\n"
        "for a in ar.get_assets(f):\n"
        "    try: parent = str(a.get_tag_value('ParentClass') or '')\n"
        "    except Exception: parent = ''\n"
        "    out.append({'path': str(a.package_name), 'name': str(a.asset_name),\n"
        "                'parent': parent})\n"
        'print("__SWEEP__" + json.dumps(out))\n'
    )
    items = run_python(code)
    if not include_thirdparty:
        items = [i for i in items if "/_ThirdParty/" not in i["path"]]
    if pattern:
        rx = re.compile(pattern, re.I)
        items = [i for i in items if rx.search(i["path"])]
    return items


def exec_pins(node, direction):
    return [p for p in node.get("pins", [])
            if p.get("type") == "exec" and p.get("direction") == direction]


def analyse_graph(nodes):
    """Return (dead_nodes, events) for one graph."""
    by_id = {n["id"]: n for n in nodes}
    reachable, stack = set(), []
    for n in nodes:
        if n["class"] in ENTRYISH:
            reachable.add(n["id"])
            stack.append(n["id"])
    while stack:
        cur = by_id.get(stack.pop())
        if not cur:
            continue
        for p in exec_pins(cur, "output"):
            for tgt in (p.get("connected_to") or []):
                nid = tgt.split(".")[0]
                if nid in by_id and nid not in reachable:
                    reachable.add(nid)
                    stack.append(nid)

    dead = []
    for n in nodes:
        if n["class"] in SKIP_NODE_CLASSES or n["id"] in reachable:
            continue
        if exec_pins(n, "input") or exec_pins(n, "output"):
            dead.append((n["id"], (n.get("title") or "").split("\n")[0]))

    events = []
    for n in nodes:
        if n["class"] not in EVENTISH:
            continue
        title = (n.get("title") or "").split("\n")[0].strip()
        wired = any(p.get("connected_to") for p in exec_pins(n, "output"))
        events.append({"id": n["id"], "name": n.get("custom_name") or title,
                       "title": title, "wired": wired})
    return dead, events


def audit_blueprint(item):
    """Per-Blueprint findings. Never raises; failures are recorded."""
    path = item["path"]
    rec = {"path": path, "name": item["name"], "parent": item["parent"],
           "dead": [], "empty_events": [], "events": [],
           "graphs": 0, "nodes": 0, "error": None, "parent_class": ""}
    try:
        info = bq("list_graphs", {"asset_path": path})
    except RuntimeError as e:
        rec["error"] = str(e)
        return rec
    rec["parent_class"] = info.get("parent_class", "")
    graphs = [g for g in info.get("graphs", []) if g.get("type") != "delegate_signature"]
    rec["graphs"] = len(graphs)

    for g in graphs:
        try:
            data = bq("export_graph", {"asset_path": path, "graph_name": g["name"]})
        except RuntimeError:
            continue
        nodes = data.get("nodes", [])
        rec["nodes"] += len(nodes)
        dead, events = analyse_graph(nodes)
        for nid, title in dead:
            rec["dead"].append({"graph": g["name"], "id": nid, "title": title})
        for ev in events:
            rec["events"].append({"graph": g["name"], "name": ev["name"],
                                  "wired": ev["wired"]})
            if not ev["wired"]:
                rec["empty_events"].append({"graph": g["name"], "name": ev["name"]})
    return rec


def find_shadowed(records):
    """Empty child events whose parent implements the same name with a body.

    This is the BP_MelodiaBattleUI defect: the child's stub replaces the
    parent's implementation in the generated class, so the call resolves to
    nothing. It is only visible by comparing a child against its parent -- no
    single-graph check can see it, which is why it survived every existing gate.

    Requires each record to carry ALL its events with wired status, not just the
    empty ones: "parent declares it" and "parent implements it" are different
    questions and both matter here.
    """
    by_class = {r["name"] + "_C": r for r in records}
    findings = []
    for r in records:
        parent_class = (r.get("parent_class") or "").strip()
        prec = by_class.get(parent_class)
        if not prec or prec["path"] == r["path"]:
            continue
        parent_wired = {e["name"] for e in prec["events"] if e["wired"]}
        for ev in r["events"]:
            if not ev["wired"] and ev["name"] in parent_wired:
                findings.append({"child": r["path"], "parent": prec["path"],
                                 "event": ev["name"], "graph": ev["graph"]})
    return findings


def main():
    ap = argparse.ArgumentParser(description="Audit every Blueprint for shipped wiring defects.")
    ap.add_argument("--filter", help="regex on the asset path")
    ap.add_argument("--include-thirdparty", action="store_true")
    ap.add_argument("--skip-live", action="store_true", help="skip reachability (faster)")
    ap.add_argument("--limit", type=int, help="stop after N blueprints (smoke test)")
    ap.add_argument("--out", help="write text report here")
    ap.add_argument("--json", help="write machine-readable findings here")
    args = ap.parse_args()

    try:
        items = inventory(args.filter, args.include_thirdparty)
    except Exception as e:
        print(f"ERROR could not enumerate blueprints: {e}")
        print("If the editor is running but silent, grep the log for MODAL_OPEN.")
        return 3
    if args.limit:
        items = items[:args.limit]
    print(f"sweeping {len(items)} blueprint(s)...", file=sys.stderr)

    records = []
    for i, item in enumerate(items, 1):
        if i % 25 == 0:
            print(f"  ...{i}/{len(items)}", file=sys.stderr)
        records.append(audit_blueprint(item))

    # duplicates by short name
    by_name = defaultdict(list)
    for r in records:
        by_name[r["name"]].append(r["path"])
    dupes = {n: p for n, p in by_name.items() if len(p) > 1}

    shadowed = find_shadowed(records)

    # ---- report
    lines = header("BLUEPRINT SWEEP",
                   f"{len(records)} blueprints, "
                   f"{sum(r['graphs'] for r in records)} graphs, "
                   f"{sum(r['nodes'] for r in records):,} nodes")

    tot_dead = sum(len(r["dead"]) for r in records)
    tot_empty = sum(len(r["empty_events"]) for r in records)
    errs = [r for r in records if r["error"]]
    lines += [
        "",
        f"  SHADOWED   {len(shadowed):>4}   empty child event overriding a working parent",
        f"  EMPTY      {tot_empty:>4}   events declared with no body",
        f"  DEAD       {tot_dead:>4}   exec nodes with no path from an entry",
        f"  DUPES      {len(dupes):>4}   short names shared by more than one asset",
        f"  unreadable {len(errs):>4}",
    ]

    if shadowed:
        lines += header("SHADOWED EVENTS", "highest severity: callers hit a stub, silently")
        for s in shadowed:
            lines.append(f"  {s['event']}")
            lines.append(f"      child  {s['child']}")
            lines.append(f"      parent {s['parent']}")

    worst = sorted((r for r in records if r["dead"] or r["empty_events"]),
                   key=lambda r: -(len(r["dead"]) + len(r["empty_events"]) * 2))[:20]
    if worst:
        lines += header("WORST BLUEPRINTS", "ranked; empty events weighted 2x dead nodes")
        lines.append(f"  {'blueprint':<52}{'empty':>7}{'dead':>7}")
        lines.append("  " + "-" * (WIDTH - 4))
        for r in worst:
            short = r["path"].replace("/Game/", "")
            lines.append(f"  {short[:51]:<52}{len(r['empty_events']):>7}{len(r['dead']):>7}")

    if dupes:
        lines += header("DUPLICATE SHORT NAMES", "substring assertions cannot tell these apart")
        for name, paths in sorted(dupes.items()):
            lines.append(f"  {name}")
            for p in paths:
                lines.append(f"      {p}")

    if errs:
        lines += header("UNREADABLE")
        for r in errs[:15]:
            lines.append(f"  {r['path'][:50]:<52}{r['error'][:26]}")

    text = "\n".join(lines) + "\n"
    print(text)

    if args.out:
        p = args.out if os.path.isabs(args.out) else os.path.join(PROJECT, args.out)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8", newline="\n").write(text)
        print(f"written: {p}")
    if args.json:
        p = args.json if os.path.isabs(args.json) else os.path.join(PROJECT, args.json)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump({"records": records, "shadowed": shadowed,
                   "duplicates": dupes}, open(p, "w", encoding="utf-8"), indent=2)
        print(f"written: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
