#!/usr/bin/env python3
"""
t3d_safe_wire.py - the composite, fail-closed T3D wiring operation.

WHY

`t3d_blueprint_injector.py` and `nl_to_blueprint.py` each skip some subset of
the verification loop that `_AGENT_WORKING_AGREEMENT.md` and
`Plugins/Monolith/Docs/MONOLITH_GUIDE.md` Recipe 15 make mandatory:

    export_graph (rollback record) -> get_graph_fingerprint (before)
    -> validate (dry run) -> mutate -> compile_blueprint (nested status)
    -> assert_graph_matches -> get_graph_fingerprint (after) -> save_asset
    -> re-export and compare

This module is that sequence, as one operation, enforced in order, with a
hard stop (never a retry) on any failed step -- "not clean" or
"matched: false" is a hard stop per the working agreement, not a retry
trigger. Every run writes a structured evidence manifest under
`Saved/T3D/<asset>_<timestamp>/` so a failure leaves a rollback record behind
instead of an unexplained partial state.

*** LIVE VERIFICATION: STALE. THE LEDGER ROWS DO NOT MEAN WHAT THEY SAY.

    Run live 2026-08-14 against BP_T3DSafeWireProbe; evidence manifest at
    Saved/T3D/Game_MelodiaIntegration_Tests_BP_T3DSafeWireProbe_20260814T045103Z/,
    outcome=committed, node_count 3->4, saved=true. Ledger rows `inject` and
    `blueprint_compile` PASS cite it.

    That run's assertion could not fail. Two versions of the postcondition were
    tautological in turn:
      1. asserted the PRE-edit graph in subset mode ("are the old nodes still
         there?") -- trivially true after adding a node, and equally true if the
         injection did nothing;
      2. exported the POST-edit graph and asserted it against ITSELF.

    Both proved serialization and compilation, neither proved the intended nodes
    and links were created. Repaired 2026-08-14 (owner-identified) by deriving
    request-owned nodes and the full postcondition contract -- see
    expected_postconditions_from_spec() and postcondition_satisfied().

    CONSEQUENCE: the `inject` and `blueprint_compile` PASS rows in
    Saved/gate_ledger.json (2026-08-14 04:51:33) were earned under a check that
    could not fail. They must be RE-RECORDED from a fresh run before they are
    trusted, and this has still never run against a production asset.

    Do not run production-wide Blueprint mutation through this until that re-run
    exists. See Docs/Plans/LONG_TERM_GAMEPLAY_BP_T3D_PLAN_2026-08-14.md.

USAGE

    python Tools/t3d_safe_wire.py \\
        --asset "/Game/.../BP_BattleController" --graph EventGraph \\
        --spec specs/wiring/some_patch.json \\
        --expected-fingerprint <live-hash> [--dry-run]

The patch spec is the same node/connection/pin_default shape
`build_blueprint_from_spec` already accepts (see `Docs/AGENT_TOOLS.md`
"Injection Workflow"): {"nodes": [...], "connections": [...],
"pin_defaults": [...]}. A committed request must also carry a stable
`request_id`, the same live `expected_before_fingerprint` passed to the CLI, and
an explicit `expected_postconditions.expected_delta` describing newly-created
nodes or links. Node ids in `nodes` must be unique within the spec --
duplicates are rejected before anything is sent to Monolith.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from mcp_client import monolith  # noqa: E402

EVIDENCE_ROOT = Path(PROJECT) / "Saved" / "T3D"


# --------------------------------------------------------------- pure logic
# Everything in this section takes plain dict/str/bool arguments and returns
# plain values. No network, no filesystem. This is what test_t3d_safe_wire.py
# exercises with fakes.

def find_duplicate_spec_ids(spec: dict) -> list[str]:
    """Return spec-declared node ids that appear more than once.

    A duplicate id is ambiguous the moment connections/pin_defaults reference
    it -- Monolith cannot tell which node a caller meant. Rejected before any
    mutation is sent, deterministically (order of first duplicate detection,
    not a set, so the same bad spec always reports the same order).
    """
    seen: set[str] = set()
    dupes: list[str] = []
    for node in spec.get("nodes", []):
        node_id = node.get("id") if isinstance(node, dict) else None
        if node_id is None:
            continue
        if node_id in seen and node_id not in dupes:
            dupes.append(node_id)
        seen.add(node_id)
    return dupes


def fingerprints_match(before: Any, after: Any) -> bool:
    """True only when two fingerprint payloads carry the identical hash.

    Accepts either a bare hash (str) or a dict with a "fingerprint" key,
    since that is what get_graph_fingerprint / bp_regression_checker.py
    already both handle. Missing/unparseable input is never a match --
    fail closed, not open.
    """
    def _hash(v: Any) -> str | None:
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return v.get("fingerprint")
        return None

    h1, h2 = _hash(before), _hash(after)
    return h1 is not None and h1 == h2


def usable_request_id(value: Any) -> bool:
    """Return whether a mutation request carries a stable, non-placeholder id."""
    return (
        isinstance(value, str)
        and len(value.strip()) >= 8
        and value.strip() not in {"REPLACE_REQUEST_ID", "TODO", "TBD"}
    )


def usable_expected_fingerprint(value: Any) -> bool:
    """Return whether a caller supplied a real pre-edit fingerprint value."""
    return (
        isinstance(value, str)
        and len(value.strip()) >= 8
        and value.strip() not in {"REPLACE_FROM_LIVE_QUERY", "TODO", "TBD"}
    )


def parse_compile_result(raw: dict) -> tuple[bool, int, dict]:
    """Extract (success, error_count, detail) from a compile_blueprint reply.

    `t3d_blueprint_injector.py`'s defect (per AGENTS.md) is trusting the
    outer envelope. Monolith's compile_blueprint response nests the actual
    compiler outcome under "compile_result" when present; only the outer
    call succeeding (the RPC didn't error) is not evidence the Blueprint
    compiled clean. This function looks at the nested object first and only
    falls back to top-level fields when no nested object exists.
    """
    if not isinstance(raw, dict):
        return False, -1, {"error": f"compile result is not a dict: {raw!r}"}

    nested = raw.get("compile_result")
    detail = nested if isinstance(nested, dict) else raw

    success = detail.get("success")
    if success is None:
        status = detail.get("status")
        success = status in ("ok", "clean", "success") if status is not None else False

    error_count = detail.get("error_count")
    if error_count is None:
        errors = detail.get("errors")
        error_count = len(errors) if isinstance(errors, list) else (0 if success else 1)

    return bool(success) and error_count == 0, int(error_count), detail


def expected_nodes_from_spec(spec: dict) -> list[str]:
    """Node identities the caller INTENDED to create, derived from the request.

    This is the missing half of the postcondition. Re-exporting the post-edit
    graph and asserting it against itself is tautological -- it cannot fail, so
    it proves serialization and compilation but never that the intended nodes
    were created. A real postcondition has to come from the request, which is
    the only thing that knows what was supposed to happen.

    Two request shapes are supported:
      * T3D text  -- top-level `Begin Object Class=... Name="..."` blocks
      * node spec -- the `{"nodes": [{"id": ...}]}` shape

    Returns identities in declaration order, deduplicated. An empty list means
    "the request declared nothing checkable", which callers must treat as a
    failed postcondition rather than a pass.
    """
    names: list[str] = []

    t3d = spec.get("t3d")
    if isinstance(t3d, str) and t3d:
        # Only top-level objects; nested Begin Object blocks are pins/sub-objects.
        depth = 0
        for line in t3d.splitlines():
            stripped = line.strip()
            if stripped.startswith("Begin Object"):
                if depth == 0:
                    match = re.search(r'Name\s*=\s*"([^"]+)"', stripped)
                    if match and match.group(1) not in names:
                        names.append(match.group(1))
                depth += 1
            elif stripped.startswith("End Object"):
                depth = max(0, depth - 1)

    for node in spec.get("nodes", []) or []:
        if isinstance(node, dict):
            node_id = node.get("id")
            if isinstance(node_id, str) and node_id and node_id not in names:
                names.append(node_id)

    return names


def graph_node_names(graph: Any) -> set[str]:
    """Every node identity present in an exported graph payload.

    Export shapes vary across Monolith versions, so accept the common ones and
    collect any identity-ish field rather than assuming one schema.
    """
    found: set[str] = set()
    if not isinstance(graph, dict):
        return found
    nodes = graph.get("nodes")
    if isinstance(nodes, list):
        for node in nodes:
            if isinstance(node, dict):
                for key in ("name", "node_name", "id", "node_id"):
                    value = node.get(key)
                    if isinstance(value, str) and value:
                        found.add(value)
            elif isinstance(node, str):
                found.add(node)
    return found


def _node_identity(node: Any) -> str | None:
    if not isinstance(node, dict):
        return node if isinstance(node, str) and node else None
    for key in ("name", "node_name", "id", "node_id"):
        value = node.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _connection_signature(connection: Any) -> tuple[str, str, str, str] | None:
    """Normalize common spec/export connection shapes for strict comparison."""
    if not isinstance(connection, dict):
        return None
    source = next((connection.get(key) for key in ("source", "from", "source_node", "from_node") if connection.get(key)), None)
    target = next((connection.get(key) for key in ("target", "to", "target_node", "to_node") if connection.get(key)), None)
    if not isinstance(source, str) or not isinstance(target, str):
        return None
    source_pin = next((connection.get(key) for key in ("source_pin", "from_pin", "source_port", "from_port") if connection.get(key)), "")
    target_pin = next((connection.get(key) for key in ("target_pin", "to_pin", "target_port", "to_port") if connection.get(key)), "")
    return (source, str(source_pin), target, str(target_pin))


def graph_connection_signatures(graph: Any) -> set[tuple[str, str, str, str]]:
    """Read top-level connection/link records from common export shapes."""
    if not isinstance(graph, dict):
        return set()
    found: set[tuple[str, str, str, str]] = set()
    for key in ("connections", "links"):
        records = graph.get(key)
        if isinstance(records, list):
            for record in records:
                signature = _connection_signature(record)
                if signature:
                    found.add(signature)
    return found


def expected_postconditions_from_spec(spec: dict) -> dict:
    """Return request-owned postconditions, with a legacy node-only fallback."""
    declared = spec.get("expected_postconditions")
    if isinstance(declared, dict):
        delta = declared.get("expected_delta")
        if not isinstance(delta, dict):
            delta = {"new_nodes": [], "new_connections": []}
        return {
            "required_nodes": list(declared.get("required_nodes", [])),
            "forbidden_nodes": list(declared.get("forbidden_nodes", [])),
            "required_connections": list(declared.get("required_connections", [])),
            "expected_delta": {
                "new_nodes": list(delta.get("new_nodes", [])),
                "new_connections": list(delta.get("new_connections", [])),
            },
            "compile_error_count": declared.get("compile_error_count"),
            "reexport_after_save": declared.get("reexport_after_save") is True,
        }
    return {
        "required_nodes": expected_nodes_from_spec(spec),
        "forbidden_nodes": [],
        "required_connections": [],
        "expected_delta": {
            "new_nodes": expected_nodes_from_spec(spec),
            "new_connections": [],
        },
        "compile_error_count": None,
        "reexport_after_save": False,
    }


def postcondition_satisfied(
    graph_after: Any,
    expected: list[str] | dict,
    *,
    graph_before: Any | None = None,
    compile_error_count: int | None = None,
    reexport_after_save: bool | None = None,
    require_reexport: bool = False,
) -> tuple[bool, dict]:
    """Verify request-owned nodes, forbidden nodes, links, compile, and re-export.

    Fails closed in both directions that matter:
      * nothing expected  -> False. A request that declares no checkable
        postcondition cannot be proven, and an unprovable mutation must not
        report success.
      * identities missing from the export -> False, listing which.

    If the export carries no recognisable node identities at all, this returns
    False with `reason: unreadable_export` rather than silently passing -- an
    unparseable graph is exactly the case the old tautological assert hid.
    """
    if isinstance(expected, list):
        contract = {
            "required_nodes": expected,
            "forbidden_nodes": [],
            "required_connections": [],
            "expected_delta": {"new_nodes": [], "new_connections": []},
            "compile_error_count": None,
            "reexport_after_save": False,
        }
    elif isinstance(expected, dict):
        contract = expected
    else:
        return False, {"reason": "invalid_postcondition_contract"}

    required_nodes = contract.get("required_nodes", [])
    forbidden_nodes = contract.get("forbidden_nodes", [])
    required_connections = contract.get("required_connections", [])
    expected_delta = contract.get("expected_delta") or {}
    new_nodes = list(expected_delta.get("new_nodes", []))
    new_connections = list(expected_delta.get("new_connections", []))
    expected_compile_errors = contract.get("compile_error_count")

    if not required_nodes and not forbidden_nodes and not required_connections and not new_nodes and not new_connections:
        return False, {"reason": "no_expected_nodes",
                       "detail": "request declared no checkable postcondition"}

    present = graph_node_names(graph_after)
    if not present:
        return False, {"reason": "unreadable_export",
                       "detail": "post-edit export carried no recognisable node identities",
                       "expected": required_nodes}

    missing = [name for name in required_nodes if name not in present]
    if missing:
        return False, {"reason": "missing_nodes", "missing": missing, "expected": required_nodes}

    if new_nodes:
        if graph_before is None:
            return False, {"reason": "pre_edit_export_unavailable", "expected_new_nodes": new_nodes}
        before_present = graph_node_names(graph_before)
        if not before_present:
            return False, {
                "reason": "pre_edit_export_unreadable",
                "detail": "cannot prove the requested nodes were absent before mutation",
                "expected_new_nodes": new_nodes,
            }
        missing_before = [name for name in new_nodes if name in before_present]
        if missing_before:
            return False, {
                "reason": "expected_new_nodes_already_present",
                "present_before": missing_before,
            }
        missing_after = [name for name in new_nodes if name not in present]
        if missing_after:
            return False, {
                "reason": "missing_new_nodes",
                "missing": missing_after,
                "expected_new_nodes": new_nodes,
            }

    forbidden_present = [name for name in forbidden_nodes if name in present]
    if forbidden_present:
        return False, {"reason": "forbidden_nodes", "present": forbidden_present}

    if required_connections:
        actual_connections = graph_connection_signatures(graph_after)
        expected_connections = []
        for connection in required_connections:
            signature = _connection_signature(connection)
            if signature:
                expected_connections.append(signature)
        if len(expected_connections) != len(required_connections):
            return False, {"reason": "invalid_required_connections"}
        missing_connections = [signature for signature in expected_connections if signature not in actual_connections]
        if missing_connections:
            return False, {
                "reason": "missing_connections",
                "missing": missing_connections,
                "actual": sorted(actual_connections),
            }

    if new_connections:
        if graph_before is None:
            return False, {"reason": "pre_edit_export_unavailable", "expected_new_connections": new_connections}
        before_connections = graph_connection_signatures(graph_before)
        after_connections = graph_connection_signatures(graph_after)
        expected_new_signatures = []
        for connection in new_connections:
            signature = _connection_signature(connection)
            if signature:
                expected_new_signatures.append(signature)
        if len(expected_new_signatures) != len(new_connections):
            return False, {"reason": "invalid_expected_new_connections"}
        already_present = [signature for signature in expected_new_signatures if signature in before_connections]
        if already_present:
            return False, {
                "reason": "expected_new_connections_already_present",
                "present_before": already_present,
            }
        missing_new_connections = [signature for signature in expected_new_signatures if signature not in after_connections]
        if missing_new_connections:
            return False, {
                "reason": "missing_new_connections",
                "missing": missing_new_connections,
                "actual": sorted(after_connections),
            }

    if expected_compile_errors is not None:
        if compile_error_count is None:
            return False, {"reason": "compile_result_unavailable", "expected": expected_compile_errors}
        if compile_error_count != expected_compile_errors:
            return False, {
                "reason": "compile_error_count",
                "expected": expected_compile_errors,
                "actual": compile_error_count,
            }

    if require_reexport and contract.get("reexport_after_save") is True:
        if reexport_after_save is not True:
            return False, {"reason": "reexport_after_save_missing"}

    return True, {
        "reason": "ok",
        "verified": required_nodes,
        "forbidden_absent": forbidden_nodes,
        "required_connections": required_connections,
        "expected_delta": {
            "new_nodes": new_nodes,
            "new_connections": new_connections,
        },
        "compile_error_count": compile_error_count,
        "reexport_after_save": reexport_after_save,
    }


def assertion_matched(raw: dict) -> tuple[bool, dict]:
    """True only on an explicit matched: true. Missing/absent is a miss.

    assert_graph_matches "returns success with matched: false plus
    missing_nodes/missing_connections/pin_default_mismatches" (MONOLITH_GUIDE
    Recipe 15) -- branch on that field, never on the call having returned at
    all.
    """
    if not isinstance(raw, dict):
        return False, {"error": f"assertion result is not a dict: {raw!r}"}
    return raw.get("matched") is True, raw


def build_manifest(
    asset_path: str,
    graph_name: str,
    steps: dict[str, Any],
    outcome: str,
) -> dict:
    """The structured evidence record written to Saved/T3D/<asset>_<ts>/.

    `outcome` is one of "dry_run_ok", "aborted:<step>", "committed". Every
    key in `steps` that was actually reached is recorded verbatim so a human
    (or the next agent) can read exactly what happened without re-running
    anything.
    """
    return {
        "asset_path": asset_path,
        "graph_name": graph_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "outcome": outcome,
        "request_id": steps.get("request_id"),
        "steps": steps,
    }


# ------------------------------------------------------------------ plumbing
# Everything below touches Monolith or the filesystem and is the part that
# needs a live editor to actually exercise.

def _parse_json_result(raw: Any) -> Any:
    if isinstance(raw, str):
        if raw.startswith("ERROR:"):
            return {"_mcp_error": raw}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"_unparsed": raw}
    return raw


def _write_manifest(evidence_dir: Path, manifest: dict) -> Path:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def _request_id_reused(request_id: str) -> bool:
    """Reject a request id already recorded in this workspace's T3D evidence."""
    if not EVIDENCE_ROOT.is_dir():
        return False
    for manifest_path in EVIDENCE_ROOT.glob("*/manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if manifest.get("request_id") == request_id or (
            isinstance(manifest.get("steps"), dict)
            and manifest["steps"].get("request_id") == request_id
        ):
            return True
    return False


def _rpc_t3d_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Strip envelope metadata before sending the T3D payload to Monolith.

    Authoring requests may carry schema, evidence, and ownership metadata. The
    editor action should receive only its transport contract; passing arbitrary
    envelope fields through makes the mutation boundary dependent on ignored
    parameters and weakens the fail-closed guarantee.
    """
    allowed = {"t3d", "placeholders", "dry_run", "auto_layout", "position", "compile"}
    return {key: value for key, value in spec.items() if key in allowed}


def safe_wire(
    asset_path: str,
    graph_name: str,
    spec: dict,
    expected_fingerprint: str | None,
    dry_run: bool = False,
) -> tuple[bool, dict, Path]:
    """Run the full enforced sequence for exactly one asset.

    Returns (ok, manifest, evidence_dir). `ok` is False the moment any step
    fails; the function stops there and does not attempt the remaining
    steps or any retry. One asset per transaction is enforced by this
    function's signature -- it takes a single asset_path, not a list.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = asset_path.strip("/").replace("/", "_")
    evidence_dir = EVIDENCE_ROOT / f"{safe_name}_{timestamp}"
    steps: dict[str, Any] = {}
    rpc_spec = _rpc_t3d_spec(spec)

    request_id = spec.get("request_id")
    steps["request_id"] = request_id
    if not usable_request_id(request_id):
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:request_id")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] request_id is missing, too short, or a placeholder. Rollback record: {path}")
        return False, manifest, evidence_dir
    if _request_id_reused(request_id):
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:request_id_reused")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] request_id was already used. Rollback record: {path}")
        return False, manifest, evidence_dir

    declared_fingerprint = spec.get("expected_before_fingerprint")
    if not usable_expected_fingerprint(expected_fingerprint):
        steps["precondition"] = {
            "reason": "missing_or_placeholder_expected_before_fingerprint",
            "expected": expected_fingerprint,
        }
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:precondition")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] a live expected pre-edit fingerprint is required. Rollback record: {path}")
        return False, manifest, evidence_dir
    if not usable_expected_fingerprint(declared_fingerprint) or declared_fingerprint != expected_fingerprint:
        steps["precondition"] = {
            "reason": "request_fingerprint_mismatch",
            "cli_expected": expected_fingerprint,
            "request_expected": declared_fingerprint,
        }
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:precondition_fingerprint_mismatch")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] request and CLI pre-edit fingerprints must match. Rollback record: {path}")
        return False, manifest, evidence_dir

    if not isinstance(spec.get("expected_postconditions"), dict):
        steps["precondition"] = {"reason": "explicit_expected_postconditions_required"}
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:postcondition_contract")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] explicit expected_postconditions are required. Rollback record: {path}")
        return False, manifest, evidence_dir

    expected_postconditions = expected_postconditions_from_spec(spec)
    expected_delta = expected_postconditions.get("expected_delta") or {}
    if not expected_delta.get("new_nodes") and not expected_delta.get("new_connections"):
        steps["precondition"] = {
            "reason": "expected_graph_delta_required",
            "detail": "declare expected_delta.new_nodes or expected_delta.new_connections",
        }
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:graph_delta")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] an explicit expected graph delta is required. Rollback record: {path}")
        return False, manifest, evidence_dir

    dupes = find_duplicate_spec_ids(spec)
    if dupes:
        steps["duplicate_spec_ids"] = dupes
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:duplicate_spec_ids")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] duplicate spec node id(s): {dupes}. Rollback record: {path}")
        return False, manifest, evidence_dir

    export_before = _parse_json_result(
        monolith("blueprint_query", {"action": "export_graph", "asset_path": asset_path, "graph_name": graph_name})
    )
    steps["export_before"] = export_before

    fp_before = _parse_json_result(
        monolith("blueprint_query", {"action": "get_graph_fingerprint", "asset_path": asset_path})
    )
    steps["fingerprint_before"] = fp_before

    if expected_fingerprint is not None and not fingerprints_match(fp_before, expected_fingerprint):
        steps["fingerprint_mismatch"] = {"expected": expected_fingerprint, "actual": fp_before}
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:fingerprint_mismatch")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] pre-edit fingerprint does not match --expected-fingerprint. "
              f"Rollback record: {path}")
        return False, manifest, evidence_dir

    validate = _parse_json_result(
        monolith("blueprint_query", {
            "action": "validate_nodes_t3d",
            "asset_path": asset_path,
            "graph_name": graph_name,
            **rpc_spec,
        })
    )
    steps["validate"] = validate
    validate_ok = isinstance(validate, dict) and not validate.get("_mcp_error") and validate.get("valid", validate.get("success")) is not False
    if not validate_ok:
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:validate")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] dry-run validation failed. Rollback record: {path}")
        return False, manifest, evidence_dir

    if dry_run:
        manifest = build_manifest(asset_path, graph_name, steps, "dry_run_ok")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[OK] dry run passed validation. Evidence: {path}")
        return True, manifest, evidence_dir

    mutate = _parse_json_result(
        monolith("blueprint_query", {
            "action": "inject_nodes_t3d",
            "asset_path": asset_path,
            "graph_name": graph_name,
            **rpc_spec,
        })
    )
    steps["mutate"] = mutate
    if isinstance(mutate, dict) and mutate.get("_mcp_error"):
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:mutate")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] mutation call failed. Rollback record (export_before): {path}")
        return False, manifest, evidence_dir

    compile_raw = _parse_json_result(
        monolith("blueprint_query", {"action": "compile_blueprint", "asset_path": asset_path})
    )
    steps["compile_raw"] = compile_raw
    compile_ok, error_count, compile_detail = parse_compile_result(
        compile_raw if isinstance(compile_raw, dict) else {}
    )
    steps["compile_parsed"] = {"success": compile_ok, "error_count": error_count, "detail": compile_detail}
    if not compile_ok:
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:compile")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] compile not clean (errors={error_count}). This is a hard stop, "
              f"not a retry trigger. Rollback record: {path}")
        return False, manifest, evidence_dir

    # The assertion previously passed `export_before` -- the PRE-edit graph. With the
    # server's subset mode that asks "are the 3 old nodes still present?", which is
    # trivially true after adding a node AND equally true if the injection did nothing
    # at all. It was a green light wired to nothing, and the `inject` PASS ledger row of
    # 2026-08-14 cites it as evidence. Fixed 2026-08-14.
    #
    # Assert the POST-edit graph instead, and independently verify the mutation actually
    # changed something: a node count that did not move means the injection was a no-op,
    # regardless of what the assertion returns.
    #
    # POSTCONDITION -- fixed 2026-08-14 (owner-identified defect).
    #
    # Two previous versions of this block could not fail. The first asserted the PRE-edit
    # graph in subset mode ("are the old nodes still there?" -- trivially true). The
    # replacement exported the POST-edit graph and asserted it against ITSELF, which is
    # strictly tautological. Neither proved the intended nodes were created.
    #
    # The fix is to derive the expected identities from the REQUEST -- the only thing that
    # knows what was supposed to happen -- and check the post-edit export against those.
    # `assert_graph_matches` is still called, now fed the caller's spec so its subset mode
    # asks a real question, but the load-bearing check is `postcondition_satisfied`.
    export_after_for_assert = _parse_json_result(
        monolith("blueprint_query", {
            "action": "export_graph",
            "asset_path": asset_path,
            "graph_name": graph_name,
        })
    )
    assert_raw = _parse_json_result(
        monolith("blueprint_query", {
            "action": "assert_graph_matches",
            "asset_path": asset_path,
            "spec": rpc_spec,
        })
    )
    steps["assert_raw"] = assert_raw
    matched, assert_detail = assertion_matched(assert_raw if isinstance(assert_raw, dict) else {})

    # The real postcondition: every node the request declared must exist afterwards.
    # Fails closed when the request declared nothing checkable, and when the export is
    # unreadable -- an unprovable mutation must not report success.
    post_ok, post_detail = postcondition_satisfied(
        export_after_for_assert,
        expected_postconditions,
        graph_before=export_before,
        compile_error_count=error_count,
    )
    steps["postcondition"] = {
        "expected": expected_postconditions,
        "ok": post_ok,
        "detail": post_detail,
    }
    if not post_ok:
        matched = False
        assert_detail = {"postcondition_failed": post_detail}

    # Independent no-op check. A dry-run is expected not to change the graph; a committed
    # injection that changes nothing is a silent failure and must not report success.
    def _node_count(g):
        if isinstance(g, dict):
            for k in ("node_count", "nodes"):
                v = g.get(k)
                if isinstance(v, int):
                    return v
                if isinstance(v, list):
                    return len(v)
        return None

    before_n, after_n = _node_count(export_before), _node_count(export_after_for_assert)
    if before_n is not None and after_n is not None and before_n == after_n:
        matched = False
        assert_detail = (f"NO-OP: node count unchanged ({before_n}). The injection "
                         "reported success but altered nothing.")
    steps["mutation_check"] = {"nodes_before": before_n, "nodes_after": after_n}
    steps["assert_parsed"] = {"matched": matched, "detail": assert_detail}
    if not matched:
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:assert_graph_matches")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] matched:false. This is a hard stop, not a retry trigger. "
              f"Rollback record: {path}")
        return False, manifest, evidence_dir

    fp_after = _parse_json_result(
        monolith("blueprint_query", {"action": "get_graph_fingerprint", "asset_path": asset_path})
    )
    steps["fingerprint_after"] = fp_after

    save_result = _parse_json_result(
        monolith("blueprint_query", {"action": "save_asset", "asset_path": asset_path})
    )
    steps["save_result"] = save_result

    export_after = _parse_json_result(
        monolith("blueprint_query", {"action": "export_graph", "asset_path": asset_path, "graph_name": graph_name})
    )
    steps["export_after"] = export_after

    # The request may require proof that the saved asset still satisfies the same
    # contract. This is intentionally a second check against the post-save export;
    # the pre-save assertion cannot prove persistence.
    reexport_ok, reexport_detail = postcondition_satisfied(
        export_after,
        expected_postconditions,
        graph_before=export_before,
        compile_error_count=error_count,
        reexport_after_save=True,
        require_reexport=True,
    )
    steps["postcondition_after_save"] = {
        "ok": reexport_ok,
        "detail": reexport_detail,
    }
    if not reexport_ok:
        manifest = build_manifest(asset_path, graph_name, steps, "aborted:postcondition_after_save")
        path = _write_manifest(evidence_dir, manifest)
        print(f"[ABORT] saved re-export failed the request postcondition. Rollback record: {path}")
        return False, manifest, evidence_dir

    manifest = build_manifest(asset_path, graph_name, steps, "committed")
    path = _write_manifest(evidence_dir, manifest)
    print(f"[OK] committed. Evidence: {path}")
    return True, manifest, evidence_dir


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Composite fail-closed T3D wiring operation (one asset per transaction).",
    )
    ap.add_argument("--asset", required=True, help="Blueprint asset path")
    ap.add_argument("--graph", default="EventGraph", help="Graph name (default EventGraph)")
    ap.add_argument("--spec", required=True, help="Path to a JSON patch spec (nodes/connections/pin_defaults)")
    ap.add_argument("--expected-fingerprint", required=True,
                     help="Required live pre-edit fingerprint hash; abort if the live graph doesn't match")
    ap.add_argument("--dry-run", action="store_true",
                     help="Run everything through validation, then stop before mutating")
    args = ap.parse_args()

    try:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read spec {args.spec}: {exc}")
        return 2

    ok, _manifest, _evidence_dir = safe_wire(
        args.asset, args.graph, spec, args.expected_fingerprint, dry_run=args.dry_run
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
