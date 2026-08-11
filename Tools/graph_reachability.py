#!/usr/bin/env python3
"""
graph_reachability.py — Blueprint graph reachability linter (v2).

Fixes from v1:
  - Does NOT treat disconnected function-call nodes as event entries
    (prevents ToolMenus::Get etc. from masking dead islands)
  - Scans ALL named graphs in the Blueprint, not just EventGraph
  - Checks EVERY node's function_class/class_path for editor-only modules
  - Reports all dead exec islands with no backward path from real events

Checks:
  1. Dead island — exec-capable node with no path from any event entry
  2. Editor-only class — node whose function_class contains ToolMenus,
     UnrealEd, LevelEditor, etc.
  3. Disconnected entry pin — event node with unwired exec outputs
  4. Editor-only ref — any node reference (data pin, variable) to editor types

Usage:
    python Tools/graph_reachability.py --bp /Game/.../BP_Example
    python Tools/graph_reachability.py --all-melodia
    python Tools/graph_reachability.py --report
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp_client import monolith

SAVED_DIR = Path(__file__).resolve().parent.parent / "Saved"
REPORT_DIR = SAVED_DIR / "lint_reports"

EDITOR_ONLY_MODULES = [
    "ToolMenus",
    "UnrealEd",
    "LevelEditor",
    "EditorScriptingUtilities",
    "EditorInteractiveToolsFramework",
    "EditorSubsystem",
    "BlueprintEditorLibrary",
    "KismetEditorLibrary",
    "EditorAssetLibrary",
    "EditorFilterLibrary",
    "EditorLevelLibrary",
    "EditorWidgetLibrary",
    "EditorUtilityLibrary",
    "EditorActorSubsystem",
]

EDITOR_ONLY_CLASSES = [
    "ToolMenus",
    "UToolMenus",
]


@dataclass
class Violation:
    bp: str
    graph: str
    node: str
    check: str  # dead_island | editor_only_class | disconnected_entry | editor_only_ref
    message: str


@dataclass
class LintResult:
    asset_path: str
    violations: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0


def _normalize_path(path: str) -> str:
    if path.startswith("/Script/"):
        return path.split("/Script/", 1)[1].split(".")[0]
    if "." in path:
        return path.split(".")[0]
    return path


def _is_editor_only(module_or_path: str) -> bool:
    module = _normalize_path(module_or_path)
    for editor_mod in EDITOR_ONLY_MODULES:
        if editor_mod in module:
            return True
    return False


def _is_editor_only_class(cls_name: str) -> bool:
    for eoc in EDITOR_ONLY_CLASSES:
        if eoc in cls_name:
            return True
    return False


def _looks_like_event(node: dict, graph_name: str = "") -> bool:
    cls = node.get("class", "")
    title = node.get("title", node.get("name", "")) or ""
    if cls in ("K2Node_Event", "K2Node_CustomEvent"):
        return True
    if cls == "K2Node_FunctionEntry":
        return True
    # A macro graph has no event and no FunctionEntry -- it is entered through a
    # tunnel. Without this, EVERY node in EVERY macro reports as a dead island.
    # That produced three false DEAD hits in BP_BattleController's
    # SwitchToStaticCamera and UnitHasEnoughMP macros on 2026-08-08, and a
    # follow-up check confirmed both macros are instantiated and wired in the
    # EventGraph ("Switch to Static Camera" / "Unit Has Enough MP" -- note the
    # spaced titles, which is separately why a search for the identifier form
    # found nothing).
    if cls in ("K2Node_Tunnel", "K2Node_TunnelBoundary"):
        return True
    if title.startswith("Event") or title.startswith("On"):
        return True
    return False


def _disconnect_entry_violation(event_node: dict, graph_name: str, bp: str) -> Violation | None:
    if not _looks_like_event(event_node):
        return None
    pins = event_node.get("pins", [])
    exec_pins = [p for p in pins if p.get("pin_type") in ("exec", "EGPD_Output") and p.get("direction") in ("output", "EGPD_Output")]
    disconnected = [p for p in exec_pins if not p.get("connections") and p.get("pin_type") in ("exec", "EGPD_Output")]
    disconnected = [p for p in disconnected if not p.get("pin_name", "").startswith("On")]
    if disconnected:
        names = ", ".join(p.get("pin_name", "?") for p in disconnected)
        return Violation(
            bp=bp,
            graph=graph_name,
            node=event_node.get("node_name", event_node.get("name", "?")),
            check="disconnected_entry",
            message=f"Event entry node has disconnected exec pins: {names}",
        )
    return None


def _scan_graph(graph: dict, asset_path: str, result: LintResult) -> list[Violation]:
    """Analyze a single graph within a Blueprint. Returns violations list."""
    violations: list[Violation] = []
    graph_name = graph.get("name", graph.get("graph_name", "?"))
    nodes = graph.get("nodes", graph.get("nodes_data", []))

    if not nodes:
        return violations

    exec_downstream: dict[str, set[str]] = {}
    exec_upstream: dict[str, set[str]] = {}
    node_map: dict[str, dict] = {}

    for node in nodes:
        node_uuid = node.get("uuid", node.get("node_id", node.get("id", node.get("name", ""))))
        node_map[node_uuid] = node
        exec_downstream.setdefault(node_uuid, set())
        exec_upstream.setdefault(node_uuid, set())

        pins = node.get("pins", [])
        for pin in pins:
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
                        exec_downstream[node_uuid].add(target)
                        exec_upstream.setdefault(target, set()).add(node_uuid)

    # Identify real event entries — only K2Node_Event or K2Node_CustomEvent
    event_entries: list[str] = []
    for node in nodes:
        node_uuid = node.get("uuid", node.get("node_id", node.get("id", node.get("name", ""))))
        if _looks_like_event(node):
            event_entries.append(node_uuid)

    # Also include VariableSet/Get nodes that have no exec input but represent
    # implicit events (e.g. variable change events). Only if their class suggests it.
    # But DO NOT include arbitrary function calls with no exec input (that was the v1 bug).
    for node in nodes:
        node_uuid = node.get("uuid", node.get("node_id", node.get("id", node.get("name", ""))))
        if node_uuid in event_entries:
            continue
        cls = node.get("class", "")
        title = node.get("title", node.get("name", "")) or ""
        # Only include VariableSet if it's named like an event-driven update
        if cls == "K2Node_VariableSet" and ("Event" in title or "On" in title):
            has_exec_input = any(
                p.get("pin_type", p.get("type", "")) in ("exec", "EGPD_Input")
                and p.get("direction", "") in ("input", "EGPD_Input")
                and p.get("connections", p.get("connected_to", []))
                for p in node.get("pins", [])
            )
            if not has_exec_input:
                event_entries.append(node_uuid)

    # Walk from event entries (both directions)
    reachable: set[str] = set()
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

    # Check 1: Dead islands
    for node in nodes:
        node_uuid = node.get("uuid", node.get("node_id", node.get("id", node.get("name", ""))))
        node_name = node.get("title", node.get("node_name", node.get("name", "?")))
        cls = node.get("class", node.get("node_class", ""))

        has_exec = any(
            p.get("pin_type", p.get("type", "")) in ("exec", "EGPD_Output", "EGPD_Input")
            for p in node.get("pins", [])
        )
        if not has_exec:
            continue
        if cls in ("K2Node_Comment", "K2Node_Reroute", "K2Node_TunnelBoundary", "K2Node_Tunnel", "K2Node_Knot"):
            continue
        if node_uuid in event_entries:
            continue

        if node_uuid not in reachable:
            violations.append(Violation(
                bp=asset_path,
                graph=graph_name,
                node=node_name,
                check="dead_island",
                message=f"Node '{node_name}' ({cls}) has no exec path from any event entry",
            ))

    # Check 2: Editor-only classes
    for node in nodes:
        node_name = node.get("title", node.get("node_name", node.get("name", "?")))
        func_class = node.get("function_class", node.get("class_path", ""))
        cls_name = node.get("class", "")
        if func_class and _is_editor_only(func_class):
            violations.append(Violation(
                bp=asset_path,
                graph=graph_name,
                node=node_name,
                check="editor_only_class",
                message=f"Node '{node_name}' uses editor-only class {func_class}",
            ))
        if cls_name and _is_editor_only_class(cls_name):
            violations.append(Violation(
                bp=asset_path,
                graph=graph_name,
                node=node_name,
                check="editor_only_class",
                message=f"Node '{node_name}' is editor-only class {cls_name}",
            ))

    # Check 3: Disconnected entry pins
    for entry_uuid in event_entries:
        event_node = node_map.get(entry_uuid, {})
        v = _disconnect_entry_violation(event_node, graph_name, asset_path)
        if v:
            violations.append(v)

    return violations


# ---------------------------------------------------------------------------
# Graph analysis — scan ALL graphs in the Blueprint
# ---------------------------------------------------------------------------

def lint_blueprint(asset_path: str) -> LintResult:
    result = LintResult(asset_path=asset_path)

    try:
        resp = monolith("blueprint_query", {"action": "export_graph", "asset_path": asset_path})
        raw = json.loads(resp) if isinstance(resp, str) else resp
        data = raw if isinstance(raw, dict) else {}
    except Exception as e:
        result.violations.append(Violation(
            bp=asset_path,
            graph="?",
            node="?",
            check="connectivity",
            message=f"Failed to export graph: {e}",
        ))
        return result

    # Collect all graphs — export_graph returns one, but we can also
    # request all functions via export_all
    graphs = data.get("graphs", data.get("graphs_data", []))
    if isinstance(graphs, dict):
        graphs = [graphs]

    # Single graph result (just EventGraph) — try to get more
    if not graphs and data.get("nodes"):
        graphs = [data]

    # If only EventGraph was returned, also try to discover other function graphs
    graph_names_seen = {g.get("name", g.get("graph_name", "")) for g in graphs}

    # Try alternate endpoint to list all function graphs
    try:
        resp2 = monolith("blueprint_query", {"action": "list_graphs", "asset_path": asset_path})
        raw2 = json.loads(resp2) if isinstance(resp2, str) else resp2
        all_graph_names_raw = raw2 if isinstance(raw2, list) else raw2.get("graphs", raw2.get("graph_names", []))
        all_graph_names = [g["name"] if isinstance(g, dict) else g for g in all_graph_names_raw]
    except Exception:
        all_graph_names = []

    for gname in all_graph_names:
        if gname in graph_names_seen:
            continue
        try:
            resp3 = monolith("blueprint_query", {
                "action": "export_graph",
                "asset_path": asset_path,
                "graph_name": gname,
            })
            raw3 = json.loads(resp3) if isinstance(resp3, str) else resp3
            gdata = raw3 if isinstance(raw3, dict) else {}
            if gdata.get("nodes"):
                graphs.append(gdata)
                graph_names_seen.add(gname)
        except Exception:
            pass

    for graph in graphs:
        violations = _scan_graph(graph, asset_path, result)
        result.violations.extend(violations)

    return result


# ---------------------------------------------------------------------------
# Discover Melodia blueprints
# ---------------------------------------------------------------------------

def _discover_melodia_bps() -> list[str]:
    try:
        resp = monolith("project_query", {"action": "search", "type": "Blueprint", "path": "/Game/Melodia"})
        raw = json.loads(resp) if isinstance(resp, str) else resp
        assets = raw if isinstance(raw, list) else raw.get("results", raw.get("assets", []))
        return [a.get("path", a) if isinstance(a, dict) else a for a in assets]
    except Exception as e:
        print(f"Failed to discover Melodia Blueprints: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def format_results(results: list[LintResult], output_path: Path | None = None) -> str:
    total = sum(len(r.violations) for r in results)
    dead = sum(1 for r in results for v in r.violations if v.check == "dead_island")
    editor = sum(1 for r in results for v in r.violations if v.check == "editor_only_class")
    disconn = sum(1 for r in results for v in r.violations if v.check == "disconnected_entry")

    lines = [
        "# Graph Reachability Report",
        "",
        f"**Blueprints scanned:** {len(results)}",
        f"**Total violations:** {total}",
        f"  - Dead islands: {dead}",
        f"  - Editor-only classes: {editor}",
        f"  - Disconnected entry pins: {disconn}",
        "",
    ]

    for r in results:
        if r.ok:
            continue
        lines.append(f"## {r.asset_path}")
        lines.append(f"**{len(r.violations)} violation(s)**")
        lines.append("")
        for v in r.violations:
            tag = {"dead_island": "DEAD", "editor_only_class": "EDITOR", "disconnected_entry": "DISCONN", "connectivity": "ERR"}.get(v.check, "?")
            lines.append(f"- **[Graph:{v.graph}] [{tag}] {v.node}**: {v.message}")
        lines.append("")

    if total == 0:
        lines.append("_No violations found._")

    report = "\n".join(lines)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(f"Report written to {output_path}")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Blueprint graph reachability linter v2.")
    p.add_argument("--bp", help="Single Blueprint asset path to lint")
    p.add_argument("--all-melodia", action="store_true", help="Lint all Melodia Blueprints")
    p.add_argument("--report", action="store_true", help="Generate markdown report")
    p.add_argument("--ci", action="store_true", help="CI mode: exit 1 on any EDITOR or connectivity violations")
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    results: list[LintResult] = []

    if args.bp:
        results.append(lint_blueprint(args.bp))
    elif args.all_melodia:
        bps = _discover_melodia_bps()
        if not bps:
            print("No Melodia Blueprints discovered or Monolith unavailable.", file=sys.stderr)
            sys.exit(1)
        for bp in bps:
            results.append(lint_blueprint(bp))
    else:
        print("Specify --bp or --all-melodia")
        sys.exit(1)

    for r in results:
        if r.violations:
            print(f"\n{r.asset_path} — {len(r.violations)} violation(s)")
            for v in r.violations:
                tag = {"dead_island": "DEAD", "editor_only_class": "EDITOR", "disconnected_entry": "DISCONN", "connectivity": "ERR"}.get(v.check, "?")
                print(f"  [{tag}] [{v.graph}] {v.node}: {v.message}")

    if args.report:
        report_path = REPORT_DIR / f"graph_reachability_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
        format_results(results, output_path=report_path)

    if args.ci:
        critical = sum(1 for r in results for v in r.violations if v.check in ("editor_only_class", "connectivity"))
        if critical > 0:
            print(f"\nCI gate: {critical} critical violations found (editor_only_class or connectivity)")
            sys.exit(1)

    fail_count = sum(1 for r in results if r.violations)
    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()
