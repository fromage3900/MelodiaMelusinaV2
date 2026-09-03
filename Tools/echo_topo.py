#!/usr/bin/env python3
"""
echo_topo.py - Topological DAG processor for the Echo gate layer.

Loads the topological manifest at specs/echo_topo.json, computes in-degree for
every gate across all layers, and provides:

  * eligible            - gates whose predecessors all have PASS ledger rows
  * order               - full topological sort (Kahn's algorithm)
  * schedule            - classify eligible gates into model_router lanes
  * check-promote       - verify a promote gate's predecessors are satisfied
  * summary             - ASCII DAG + per-layer status matrix

The manifest uses dot-notation for cross-layer references:
  "predecessors": ["ch1_gameplay.promote"]

A bare predecessor ("runtime") resolves within the gate's own layer.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# ── paths ──────────────────────────────────────────────────────────────────

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_MANIFEST = _ROOT / "specs" / "echo_topo.json"
_LEDGER = _ROOT / "Saved" / "gate_ledger.json"

# Map topological lane names to model_router task classes
LANE_TO_CLASS = {
    "gameplay": "code",
    "code": "code",
    "audit": "audit",
    "author": "author",
    "vision": "vision",
    "orchestrator": "orchestrator",
    "review": "review",
}


# ── manifest loading ─────────────────────────────────────────────────────────

def load_topo_manifest() -> dict[str, Any]:
    """Load and return the echo_topo.json manifest."""
    with open(_MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


def _flatten_gates(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Flatten all layers into a single gate dict keyed by full-id.

    Full-id format: ``layer_id.gate_id`` (e.g. ``ch1_gameplay.runtime``).
    Each entry is the gate dict augmented with ``layer`` and ``full_id``.
    """
    flat: dict[str, dict[str, Any]] = {}
    layers = manifest.get("layers", {})
    for layer_id, layer in layers.items():
        gates = layer.get("gates", {})
        for gate_id, gate in gates.items():
            full = f"{layer_id}.{gate_id}"
            entry = dict(gate)
            entry["full_id"] = full
            entry["layer"] = layer_id
            entry["chapter"] = layer.get("chapter", 0)
            flat[full] = entry
    # Handle the project-level promote gate (top-level, not in a layer)
    if "project_promote" in manifest:
        gate = manifest["project_promote"]
        entry = dict(gate)
        entry["full_id"] = "project_promote"
        entry["layer"] = "project"
        entry["chapter"] = 0
        flat["project_promote"] = entry
    return flat


def _resolve_predecessor(pred: str, default_layer: str) -> str:
    """
    Resolve a predecessor reference to a full-id.

    Dot-notation (e.g. ``ch1_gameplay.promote``) is unambiguous.
    Bare id (e.g. ``runtime``) resolves within ``default_layer``.
    """
    if "." in pred:
        return pred
    return f"{default_layer}.{pred}"


def build_adjacency(manifest: dict[str, Any]) -> tuple[
    dict[str, dict[str, Any]], dict[str, set[str]], dict[str, int]
]:
    """
    Build adjacency structures from the manifest.

    Returns:
      gates      - {full_id: gate_dict}
      preds      - {full_id: set(pred_full_ids)}
      in_degree  - {full_id: int}
    """
    gates = _flatten_gates(manifest)
    preds: dict[str, set[str]] = {}
    for full_id, gate in gates.items():
        raw_preds = gate.get("predecessors", [])
        resolved = {_resolve_predecessor(p, gate["layer"]) for p in raw_preds}
        preds[full_id] = resolved

    in_degree = {gid: len(p) for gid, p in preds.items()}
    return gates, preds, in_degree


# ── ledger ───────────────────────────────────────────────────────────────────

def _load_ledger() -> dict[str, dict[str, Any]]:
    """Return {gate_full_id: latest_ledger_entry}."""
    if not _LEDGER.exists():
        return {}
    try:
        with open(_LEDGER, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    latest: dict[str, dict[str, Any]] = {}
    for g in data.get("gates", []):
        latest[g["id"]] = g
    return latest


def gate_status(full_id: str, ledger: dict[str, dict[str, Any]]) -> str:
    """Return PASS / FAIL / OPEN for a gate full-id."""
    rec = ledger.get(full_id)
    if rec:
        return rec.get("status", "OPEN").upper()
    # Also check bare id (legacy ledger entries don't use dot notation)
    bare = full_id.split(".", 1)[-1] if "." in full_id else full_id
    rec = ledger.get(bare)
    if rec:
        return rec.get("status", "OPEN").upper()
    return "OPEN"


# ── topological scheduler ────────────────────────────────────────────────────

def topological_order(
    gates: dict[str, dict[str, Any]],
    preds: dict[str, set[str]],
    in_degree: dict[str, int],
) -> list[str]:
    """
    Kahn's algorithm over the full DAG. Returns gate full-ids in topo order.
    Gates with unsatisfied predecessors appear after their deps.
    """
    indeg = dict(in_degree)
    adj: dict[str, list[str]] = {gid: [] for gid in gates}
    for gid, ps in preds.items():
        for p in ps:
            if p in adj:
                adj[p].append(gid)
    queue = sorted(gid for gid in gates if indeg[gid] == 0)
    order: list[str] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for dependent in adj.get(node, []):
            indeg[dependent] -= 1
            if indeg[dependent] == 0:
                queue.append(dependent)
                queue.sort()
    # Any remaining have cycles - append them (they'll show as BLOCKED)
    for gid in gates:
        if gid not in order:
            order.append(gid)
    return order


def eligible_gates(
    gates: dict[str, dict[str, Any]],
    preds: dict[str, set[str]],
    ledger: dict[str, dict[str, Any]],
) -> list[str]:
    """
    Return gates whose predecessors are ALL PASS (or have no predecessors).
    These are the nodes ready to be scheduled/run now.
    """
    ready: list[str] = []
    for full_id, gate in gates.items():
        ps = preds.get(full_id, set())
        if not ps:
            ready.append(full_id)
            continue
        if all(gate_status(p, ledger) == "PASS" for p in ps):
            ready.append(full_id)
    # Filter out gates that are already PASS
    return [g for g in ready if gate_status(g, ledger) != "PASS"]


def classify_gate(full_id: str, gate: dict[str, Any]) -> str:
    """Return the model_router task class for this gate."""
    lane = gate.get("lane", "code")
    return LANE_TO_CLASS.get(lane, "code")


def check_promote(full_id: str) -> tuple[bool, list[str]]:
    """
    Verify a promote gate's predecessors are all PASS.

    Returns (ok, list_of_failed_predecessors).
    """
    manifest = load_topo_manifest()
    gates, preds, _ = build_adjacency(manifest)
    gate = gates.get(full_id)
    if not gate:
        return False, [f"unknown gate: {full_id}"]
    ps = preds.get(full_id, set())
    ledger = _load_ledger()
    failed = [p for p in ps if gate_status(p, ledger) != "PASS"]
    return len(failed) == 0, failed


# ── output formatters ────────────────────────────────────────────────────────

def _format_gates_for_schedule(eligible: list[str], gates: dict) -> list[dict]:
    """Format eligible gates into assignment rows for model_router dispatch."""
    rows = []
    for full_id in eligible:
        gate = gates[full_id]
        rows.append({
            "gate_id": full_id,
            "title": gate.get("label", gate.get("id", full_id)),
            "chapter": gate.get("chapter", 0),
            "layer": gate.get("layer", "?"),
            "lane": gate.get("lane", "code"),
            "task_class": classify_gate(full_id, gate),
            "is_promote": gate.get("is_promote", False),
            "predecessors": gate.get("predecessors", []),
        })
    return rows


def cmd_eligible(as_json: bool = False) -> int:
    manifest = load_topo_manifest()
    gates, preds, in_degree = build_adjacency(manifest)
    ledger = _load_ledger()
    ready = eligible_gates(gates, preds, ledger)
    order = topological_order(gates, preds, in_degree)
    all_statuses = {gid: gate_status(gid, ledger) for gid in gates}

    if as_json:
        out = {
            "eligible": _format_gates_for_schedule(ready, gates),
            "topo_order": order,
            "statuses": all_statuses,
        }
        print(json.dumps(out, indent=2))
        return 0

    print("# Topological gate readiness")
    print(f"  total gates: {len(gates)}  eligible now: {len(ready)}\n")
    print(f"  {'gate':<40} {'ch':<4} {'status':<6} {'ready':<7} {'preds'}")
    print(f"  {'-' * 40} {'-' * 4} {'-' * 6} {'-' * 7} {'-' * 30}")
    for full_id in order:
        gate = gates[full_id]
        status = all_statuses[full_id]
        is_eligible = "YES" if full_id in ready else "-"
        ps = gate.get("predecessors", [])
        pred_str = ", ".join(ps) if ps else "(none)"
        print(f"  {full_id:<40} {gate.get('chapter', 0):<4} {status:<6} {is_eligible:<7} {pred_str[:30]}")

    if ready:
        print("\n  Eligible gates (dispatch to model lanes):")
        for full_id in ready:
            gate = gates[full_id]
            cls = classify_gate(full_id, gate)
            print(f"    [{gate.get('lane', '?'):<11}] {cls:<12} {full_id}")
    else:
        print("\n  No gates eligible - all remaining have unmet predecessors.")
    return 0


def cmd_order() -> int:
    manifest = load_topo_manifest()
    gates, preds, in_degree = build_adjacency(manifest)
    order = topological_order(gates, preds, in_degree)
    print("# Topological order (Kahn's algorithm)")
    for i, full_id in enumerate(order, 1):
        gate = gates[full_id]
        print(f"  {i:>2}. {full_id}  [ch{gate.get('chapter', 0)} / {gate.get('lane', '?')}]")
    return 0


def cmd_check_promote(gate_id: str, manifest: dict | None = None) -> int:
    manifest = manifest or load_topo_manifest()
    gates, _, _ = build_adjacency(manifest)
    if gate_id not in gates:
        candidates = [g for g in gates if g.endswith(f".{gate_id}")]
        if len(candidates) == 1:
            gate_id = candidates[0]
        else:
            print(f"ERROR: unknown gate '{gate_id}'")
            print(f"Known gates: {', '.join(sorted(gates))}")
            return 2

    ok, failed = check_promote(gate_id)
    if ok:
        print(f"[OK] {gate_id} - all predecessors satisfied, promote is eligible.")
        return 0
    else:
        print(f"[BLOCKED] {gate_id} - predecessors not yet PASS:")
        for f in failed:
            print(f"  {f}")
        return 1


def cmd_schedule(as_json: bool = False) -> int:
    """Classify eligible gates into model_router task classes for dispatch."""
    manifest = load_topo_manifest()
    gates, preds, in_degree = build_adjacency(manifest)
    ledger = _load_ledger()
    ready = eligible_gates(gates, preds, ledger)
    rows = _format_gates_for_schedule(ready, gates)

    if as_json:
        print(json.dumps(rows, indent=2))
        return 0

    by_class: dict[str, list[dict]] = {}
    for row in rows:
        by_class.setdefault(row["task_class"], []).append(row)

    print("# Topo scheduling - eligible gates classified into model lanes")
    print(f"  {len(rows)} gate(s) ready for dispatch\n")
    for cls in sorted(by_class):
        print(f"  [{cls}]")
        for row in by_class[cls]:
            marker = " PROMOTE" if row["is_promote"] else ""
            print(f"    {row['gate_id']:<38} ch{row['chapter']} {row['lane']}{marker}")
        print()
    return 0


def cmd_summary() -> int:
    """ASCII DAG + status matrix."""
    manifest = load_topo_manifest()
    gates, preds, in_degree = build_adjacency(manifest)
    ledger = _load_ledger()
    statuses = {gid: gate_status(gid, ledger) for gid in gates}

    print("# Echo Topo DAG - Project Gate Summary")
    print(f"  layers: {len(manifest.get('layers', {}))}")
    print(f"  gates:  {len(gates)}")
    print(f"  ledger: {_LEDGER.parent.name}/{_LEDGER.name}")
    print()

    for layer_id, layer in manifest.get("layers", {}).items():
        print(f"  ## Chapter {layer.get('chapter', '?')} - {layer.get('label', layer_id)}")
        for gid, gate in layer.get("gates", {}).items():
            full = f"{layer_id}.{gid}"
            s = statuses.get(full, "OPEN")
            mark = {"PASS": "PASS", "FAIL": "FAIL", "OPEN": "OPEN"}.get(s, "OPEN")
            promo = " [promote]" if gate.get("is_promote") else ""
            print(f"      [{mark:<5}] {full:<38} {gate.get('label', gid)}{promo}")
        print()

    if "project_promote" in manifest:
        ps = manifest["project_promote"]
        s = statuses.get("project_promote", "OPEN")
        mark = {"PASS": "PASS", "FAIL": "FAIL", "OPEN": "OPEN"}.get(s, "OPEN")
        print(f"  ## Project promote")
        print(f"      [{mark:<5}] project_promote  {ps.get('label', 'project-level converge')}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Topological DAG processor for Echo gates")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_elig = sub.add_parser("eligible", help="Show gates whose predecessors are all PASS")
    p_elig.add_argument("--json", action="store_true")

    sub.add_parser("order", help="Full topological sort (Kahn's algorithm)")

    p_sched = sub.add_parser("schedule", help="Classify eligible gates into model lanes")
    p_sched.add_argument("--json", action="store_true")

    p_check = sub.add_parser("check-promote", help="Verify a promote gate's predecessors are satisfied")
    p_check.add_argument("gate_id")

    sub.add_parser("summary", help="ASCII DAG + per-layer status matrix")

    args = ap.parse_args()

    if args.cmd == "eligible":
        return cmd_eligible(args.json)
    elif args.cmd == "order":
        return cmd_order()
    elif args.cmd == "schedule":
        return cmd_schedule(args.json)
    elif args.cmd == "check-promote":
        return cmd_check_promote(args.gate_id)
    elif args.cmd == "summary":
        return cmd_summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())
