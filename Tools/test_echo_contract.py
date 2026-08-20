#!/usr/bin/env python3
"""Assertions over specs/echo_pipeline.json's own shape. No editor required.

The manifest is read by three different consumers (`echo_run.py`,
`record_gate.py`'s `_all_known_gates()`, and this project's various gate
tools) that each trust it a little differently. Nothing previously checked
that the manifest is internally consistent: every stage has an id, every
gate `completion_gates` names actually exists somewhere a human could point
to, and no stage claims a `ledger_id` that no tool in this repo can produce.
Loosening any of these checks later is how the manifest quietly drifts from
what the pipeline actually does -- same reasoning as
`Docs/T3D_Baseline/test_canonical.py` and `Tools/test_ui_style_audit.py`.

    python Tools/test_echo_contract.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MANIFEST_PATH = os.path.join(PROJECT, "specs", "echo_pipeline.json")

sys.path.insert(0, HERE)
import record_gate  # noqa: E402

_PY_BASENAMES: set[str] | None = None


def _all_py_basenames() -> set[str]:
    """Every .py filename anywhere in the repo, computed once and cached.

    Manifest impl strings name scripts by basename regardless of which
    directory they actually live in (`verify_baseline.py` is under
    `Docs/T3D_Baseline/`, not `Tools/`) -- a directory-scoped existence
    check would report those as missing.
    """
    global _PY_BASENAMES
    if _PY_BASENAMES is None:
        names: set[str] = set()
        skip_dirs = {".git", "Saved", "Intermediate", "Binaries", "DerivedDataCache"}
        for root, dirs, files in os.walk(PROJECT):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for f in files:
                if f.endswith(".py"):
                    names.add(f)
        _PY_BASENAMES = names
    return _PY_BASENAMES


def _tool_exists(impl: str) -> bool:
    """Best-effort: does *something* in the repo look like it can produce this.

    `impl` strings in the manifest are things like "echo_run.py:validate_spec",
    "blueprint_query:compile_blueprint", or a slash-separated list of script
    names. This is intentionally permissive (a substring/tokenized presence
    check, not an import) because the manifest mixes Tools/ scripts, Monolith
    MCP actions, and prose descriptions of manual/human steps in the same
    field -- the contract worth enforcing is "not obviously nothing", not a
    full static-analysis proof.
    """
    if not impl:
        return False
    # Monolith action references (namespace:action) are trusted -- verifying
    # against the live registry would require the editor, which this test
    # deliberately does not need.
    if ":" in impl and not impl.endswith(".py"):
        return True
    candidates = re.split(r"[\s/]+", impl)
    for cand in candidates:
        cand = cand.split(":")[0].split("(")[0].strip()
        if not cand:
            continue
        if cand.endswith(".py"):
            if cand in _all_py_basenames():
                return True
        else:
            # A bare prose word ("human_or_agent", "commit", "Automation") --
            # not a tool claim, so it can't be missing a tool.
            return True
    return False


def main() -> int:
    results = []

    manifest = json.loads(open(MANIFEST_PATH, encoding="utf-8").read())
    results.append((True, "manifest parses as JSON", ""))

    stages = manifest.get("stages", [])
    results.append((bool(stages), "manifest declares at least one stage", f"{len(stages)} stages"))

    stage_ids = set()
    for i, stage in enumerate(stages):
        sid = stage.get("id")
        ok = bool(sid)
        results.append((ok, f"stages[{i}] has an id", f"got {sid!r}"))
        if sid:
            dup = sid in stage_ids
            results.append((not dup, f"stage id '{sid}' is unique", "duplicate" if dup else ""))
            stage_ids.add(sid)

        impl = stage.get("impl") or stage.get("impls")
        results.append((bool(impl), f"stage '{sid}' declares impl or impls", ""))

        if isinstance(impl, list):
            found = [_tool_exists(x) for x in impl]
        else:
            found = [_tool_exists(impl)] if impl else [False]
        results.append((all(found), f"stage '{sid}' impl(s) resolve to something in the repo",
                        f"impl={impl}"))

    # Every gate a stage claims to produce must be recognized by record_gate.py,
    # or a "passing" gate can be recorded under an id nothing else ever looks
    # for -- a gate that no ledger consumer can find is indistinguishable from
    # a gate that never ran.
    known_gates = set(record_gate._all_known_gates())
    for i, stage in enumerate(stages):
        lid = stage.get("ledger_id")
        if lid:
            ok = lid in known_gates
            results.append((ok, f"stage '{stage.get('id')}' ledger_id '{lid}' is a known gate", ""))

    completion_gates = manifest.get("completion_gates", [])
    results.append((bool(completion_gates), "manifest declares completion_gates", f"{completion_gates}"))
    for gid in completion_gates:
        ok = gid in known_gates
        results.append((ok, f"completion gate '{gid}' is recognized by record_gate.py", ""))

    definitions = manifest.get("completion_definitions", {})
    for gid in completion_gates:
        ok = gid in definitions and bool(definitions[gid])
        results.append((ok, f"completion gate '{gid}' has a non-empty definition", ""))
    for gid in definitions:
        ok = gid in completion_gates
        results.append((ok, f"completion_definitions key '{gid}' is a declared completion gate",
                        "" if ok else "defined but not in completion_gates -- dead entry"))

    print("echo_pipeline.json contract assertions\n")
    failed = 0
    for ok, label, note in results:
        print(f"  {'PASS' if ok else '*** FAIL ***'}  {label}" + (f"  [{note}]" if note else ""))
        failed += 0 if ok else 1
    print(f"\n=== {len(results) - failed}/{len(results)} passed ===")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
