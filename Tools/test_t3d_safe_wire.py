#!/usr/bin/env python3
"""Assertions for t3d_safe_wire's pure logic. No editor required.

Covers the four things that are load-bearing for "fail closed" and are cheap
to get subtly wrong: fingerprint comparison, duplicate spec-id detection,
nested compile-result parsing, and the manifest shape actually being written.
Matches the repo convention set by `Tools/test_ui_style_audit.py` and
`Docs/T3D_Baseline/test_canonical.py` -- committed assertions for gate tools.

    python Tools/test_t3d_safe_wire.py
"""
import sys

from t3d_safe_wire import (
    assertion_matched,
    build_manifest,
    expected_nodes_from_spec,
    expected_postconditions_from_spec,
    find_duplicate_spec_ids,
    fingerprints_match,
    graph_connection_signatures,
    graph_node_names,
    parse_compile_result,
    postcondition_satisfied,
    usable_expected_fingerprint,
    usable_request_id,
    _rpc_t3d_spec,
)

T3D_TWO_NODES = '''Begin Object Class=/Script/BlueprintGraph.K2Node_CallFunction Name="Call_0"
   Begin Object Class=/Script/EdGraph.EdGraphPin Name="Pin_0"
   End Object
End Object
Begin Object Class=/Script/BlueprintGraph.K2Node_Knot Name="Knot_1"
End Object
'''


def main() -> int:
    results = []

    # --- find_duplicate_spec_ids ---------------------------------------
    dupes = find_duplicate_spec_ids({"nodes": [{"id": "A"}, {"id": "B"}, {"id": "A"}]})
    results.append((dupes == ["A"], "duplicate node id detected", f"got {dupes}"))

    dupes = find_duplicate_spec_ids({"nodes": [{"id": "A"}, {"id": "B"}]})
    results.append((dupes == [], "no false positive on unique ids", f"got {dupes}"))

    dupes = find_duplicate_spec_ids({"nodes": []})
    results.append((dupes == [], "empty node list is not a duplicate", f"got {dupes}"))

    # --- fingerprints_match ----------------------------------------------
    results.append((fingerprints_match("abc123", "abc123"), "identical bare hashes match", ""))
    results.append((not fingerprints_match("abc123", "def456"), "different bare hashes do not match", ""))
    results.append((fingerprints_match({"fingerprint": "abc"}, {"fingerprint": "abc"}),
                    "identical dict-wrapped hashes match", ""))
    results.append((fingerprints_match({"fingerprint": "abc"}, "abc"),
                    "dict vs bare hash of same value matches", ""))
    results.append((not fingerprints_match(None, "abc"), "missing before-hash fails closed", ""))
    results.append((not fingerprints_match({}, {}), "two empty dicts do not match (fail closed)", ""))
    results.append((usable_request_id("t3d-probe-v2"), "stable request id is accepted", ""))
    results.append((not usable_request_id("REPLACE_REQUEST_ID"), "placeholder request id is rejected", ""))
    results.append((usable_expected_fingerprint("abcdef0123456789"), "live fingerprint value is accepted", ""))
    results.append((not usable_expected_fingerprint("REPLACE_FROM_LIVE_QUERY"), "placeholder fingerprint is rejected", ""))

    # --- parse_compile_result ---------------------------------------------
    ok, count, _ = parse_compile_result({"compile_result": {"success": True, "error_count": 0}})
    results.append((ok and count == 0, "nested clean compile parses as success", f"ok={ok} count={count}"))

    ok, count, _ = parse_compile_result({"compile_result": {"success": False, "error_count": 3}})
    results.append((not ok and count == 3, "nested dirty compile parses as failure", f"ok={ok} count={count}"))

    ok, count, _ = parse_compile_result({"success": True, "compile_result": {"success": False, "error_count": 1}})
    results.append((not ok, "nested result overrides a clean outer envelope",
                    f"ok={ok} (outer envelope success must not mask a dirty nested result)"))

    ok, count, _ = parse_compile_result({"status": "ok"})
    results.append((ok, "top-level status fallback when no nested object exists", f"ok={ok}"))

    ok, count, _ = parse_compile_result("not a dict")
    results.append((not ok and count == -1, "non-dict compile result fails closed", f"ok={ok} count={count}"))

    # --- assertion_matched -------------------------------------------------
    matched, _ = assertion_matched({"matched": True})
    results.append((matched, "explicit matched:true is a match", ""))

    matched, _ = assertion_matched({"matched": False, "missing_nodes": ["X"]})
    results.append((not matched, "explicit matched:false is a miss", ""))

    matched, _ = assertion_matched({"success": True})
    results.append((not matched, "success without a matched key is NOT a match (fail closed)", ""))

    matched, _ = assertion_matched("not a dict")
    results.append((not matched, "non-dict assertion result fails closed", ""))

    # --- build_manifest -----------------------------------------------------
    manifest = build_manifest("/Game/X/BP_Y", "EventGraph", {"a": 1}, "committed")
    shape_ok = (
        manifest.get("asset_path") == "/Game/X/BP_Y"
        and manifest.get("graph_name") == "EventGraph"
        and manifest.get("outcome") == "committed"
        and manifest.get("steps") == {"a": 1}
        and "generated_at" in manifest
    )
    results.append((shape_ok, "manifest carries asset/graph/outcome/steps/timestamp", f"{manifest}"))

    # --- transport boundary -----------------------------------------------
    rpc_spec = _rpc_t3d_spec({
        "t3d": "Begin Object...",
        "placeholders": {"message": "probe"},
        "schema": "melodia.t3d_mutation_request.v1",
        "request_id": "request-1",
        "expected_before_fingerprint": "abc",
        "verification": {"compile_zero_errors": True},
    })
    results.append((
        rpc_spec == {"t3d": "Begin Object...", "placeholders": {"message": "probe"}},
        "transport strips envelope metadata before editor mutation",
        f"got {rpc_spec}",
    ))

    # --- expected_nodes_from_spec -----------------------------------------
    # The postcondition's whole value is that it comes from the REQUEST, not from
    # a re-export of whatever the server happened to produce.
    names = expected_nodes_from_spec({"t3d": T3D_TWO_NODES})
    results.append((names == ["Call_0", "Knot_1"],
                    "T3D top-level node names extracted, nested pins ignored", f"got {names}"))

    names = expected_nodes_from_spec({"nodes": [{"id": "A"}, {"id": "B"}]})
    results.append((names == ["A", "B"], "node-spec ids extracted", f"got {names}"))

    results.append((expected_nodes_from_spec({}) == [],
                    "empty spec declares no postcondition", ""))

    # --- graph_node_names --------------------------------------------------
    results.append((graph_node_names({"nodes": [{"name": "A"}, {"node_name": "B"}]}) == {"A", "B"},
                    "node identities read across export shapes", ""))
    results.append((graph_node_names("not a dict") == set(),
                    "unparseable export yields no identities", ""))

    # --- postcondition_satisfied ------------------------------------------
    ok, detail = postcondition_satisfied({"nodes": [{"name": "Call_0"}, {"name": "Knot_1"}]},
                                         ["Call_0", "Knot_1"])
    results.append((ok, "all intended nodes present passes", f"got {detail}"))

    ok, detail = postcondition_satisfied({"nodes": [{"name": "Call_0"}]}, ["Call_0", "Knot_1"])
    results.append((not ok and detail.get("missing") == ["Knot_1"],
                    "a missing intended node fails and names it", f"got {detail}"))

    # These three are the regression guards for the tautology this replaced.
    ok, detail = postcondition_satisfied({"nodes": [{"name": "Anything"}]}, [])
    results.append((not ok and detail.get("reason") == "no_expected_nodes",
                    "no declared postcondition fails closed (was: silently passed)", f"got {detail}"))

    ok, detail = postcondition_satisfied({}, ["Call_0"])
    results.append((not ok and detail.get("reason") == "unreadable_export",
                    "unreadable export fails closed (was: silently passed)", f"got {detail}"))

    ok, _ = postcondition_satisfied({"nodes": []}, ["Call_0"])
    results.append((not ok, "empty post-edit graph never satisfies a postcondition", ""))

    delta_contract = {
        "required_nodes": ["Call_0", "Knot_1"],
        "forbidden_nodes": [],
        "required_connections": [],
        "expected_delta": {"new_nodes": ["Knot_1"], "new_connections": []},
        "compile_error_count": 0,
        "reexport_after_save": True,
    }
    before_graph = {"nodes": [{"name": "Call_0"}]}
    after_graph = {"nodes": [{"name": "Call_0"}, {"name": "Knot_1"}]}
    ok, detail = postcondition_satisfied(
        after_graph,
        delta_contract,
        graph_before=before_graph,
        compile_error_count=0,
    )
    results.append((ok, "expected new node is absent before and present after", f"got {detail}"))
    ok, detail = postcondition_satisfied(
        after_graph,
        delta_contract,
        graph_before=after_graph,
        compile_error_count=0,
    )
    results.append((not ok and detail.get("reason") == "expected_new_nodes_already_present",
                    "pre-existing required node cannot masquerade as a mutation", f"got {detail}"))
    ok, detail = postcondition_satisfied(
        after_graph,
        delta_contract,
        graph_before={},
        compile_error_count=0,
    )
    results.append((not ok and detail.get("reason") == "pre_edit_export_unreadable",
                    "unreadable pre-edit graph cannot prove a new node", f"got {detail}"))

    contract = {
        "required_nodes": ["Call_0"],
        "forbidden_nodes": ["Forbidden"],
        "required_connections": [{
            "source": "Call_0",
            "source_pin": "then",
            "target": "Knot_1",
            "target_pin": "execute",
        }],
        "compile_error_count": 0,
        "reexport_after_save": True,
    }
    graph = {
        "nodes": [{"name": "Call_0"}, {"name": "Knot_1"}],
        "connections": [{
            "source": "Call_0",
            "source_pin": "then",
            "target": "Knot_1",
            "target_pin": "execute",
        }],
    }
    results.append((
        graph_connection_signatures(graph) == {("Call_0", "then", "Knot_1", "execute")},
        "connection signatures normalize the request/export shape",
        "",
    ))
    ok, detail = postcondition_satisfied(
        graph,
        contract,
        compile_error_count=0,
        reexport_after_save=True,
        require_reexport=True,
    )
    results.append((ok, "full request postcondition passes nodes/links/compile/reexport", f"got {detail}"))

    forbidden_graph = {"nodes": [{"name": "Call_0"}, {"name": "Forbidden"}]}
    ok, detail = postcondition_satisfied(forbidden_graph, contract, compile_error_count=0)
    results.append((not ok and detail.get("reason") == "forbidden_nodes",
                    "forbidden node fails closed", f"got {detail}"))

    ok, detail = postcondition_satisfied(graph, contract, compile_error_count=0, require_reexport=True)
    results.append((not ok and detail.get("reason") == "reexport_after_save_missing",
                    "required saved re-export fails when not proven", f"got {detail}"))

    derived = expected_postconditions_from_spec({
        "nodes": [{"id": "Probe"}],
        "expected_postconditions": {"required_nodes": ["Probe"], "forbidden_nodes": []},
    })
    results.append((derived["required_nodes"] == ["Probe"] and derived["reexport_after_save"] is False,
                    "request-owned postconditions are read independently", f"got {derived}"))

    # Render LAST. Appending a case after this loop silently excludes it from both
    # the printout and the failure count -- a green light wired to nothing, which is
    # exactly the defect this suite now guards against. Keep every append above here.
    print("t3d_safe_wire pure-logic assertions\n")
    failed = 0
    for ok, label, note in results:
        print(f"  {'PASS' if ok else '*** FAIL ***'}  {label}" + (f"  [{note}]" if note else ""))
        failed += 0 if ok else 1

    print(f"\n=== {len(results) - failed}/{len(results)} passed ===")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
