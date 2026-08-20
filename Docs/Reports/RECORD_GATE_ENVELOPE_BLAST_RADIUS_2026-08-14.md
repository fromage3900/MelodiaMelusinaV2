# Blast Radius & Migration Plan: Enforcing Conforming Evidence Envelopes in `record_gate.py`

**Date:** 2026-08-14  
**Author:** Antigravity  
**Target:** Handoff / Claude Worktree  
**Goal:** Map the blast radius and migration steps before modifying `Tools/record_gate.py` to reject ledger writes without a conforming evidence envelope.

---

## 1. Executive Summary

`Tools/record_gate.py` currently appends unstructured pass/fail records to `Saved/gate_ledger.json` based purely on CLI arguments (`gate_id`, `status`, `--note`, `--session`). 

Enforcing conforming evidence envelopes (`specs/schemas/evidence_envelope.v1.json` via `Tools/evidence_envelope.py`) introduces a strict prerequisite: **every gate row written must be backed by a verified envelope containing metadata (`run_id`, `repository`, `producer`, `checks`, `artifacts`)**.

This document details every caller in the codebase, the exact gap between evidence-in-hand and schema conformance, the 2-state vs 3-state (`hold`) ledger assumptions, coverage-floor mechanics in contract tests, and a phased, risk-ordered migration plan.

---

## 2. Comprehensive Caller Inventory

| Invocation Type | Source Location | Exact Invocation Pattern | Context & Responsibility |
| :--- | :--- | :--- | :--- |
| **Python Import** | `Tools/playtest_harness.py:299` | `from record_gate import record_gate as write_gate` | `playtest_harness.record_gate(status, note, session)` called when executing `python Tools/playtest_harness.py record <pass\|fail>`. |
| **Python Import** | `Tools/test_echo_contract.py:26` | `import record_gate` | Contract test invoking `record_gate._all_known_gates()` (line 118) to verify all pipeline stage gates are recognized. |
| **Subprocess Call** | `Tools/echo_run.py:668` | `run_py("Tools/record_gate.py", args.gate_id, args.status, "--note", args.note)` | Subcommand `python Tools/echo_run.py record <id> pass\|fail`. |
| **Subprocess Call** | `Tools/overnight_analysis.py:163` | `_sh(sys.executable, str(ROOT / "Tools" / "record_gate.py"), "--list")` | Injects output of `record_gate.py --list` into prompt for ledger vs prose contradiction auditing. |
| **CI Workflow** | `.github/workflows/echo_gates.yml:117` | `python Tools/record_gate.py static_gates pass --note "CI echo_gates.yml ${{ github.sha }}"` | CI step writing `static_gates pass` into `Saved/gate_ledger.json` prior to artifact upload. |
| **Pipeline Spec** | `specs/echo_pipeline.json:63` | `"impl": "record_gate.py <gate-id> pass\|fail"` | Stage implementation mapping for `record` stage. |
| **Runner Spec** | `specs/echo_pipeline.json:124` | `"record_command": "python Tools/echo_run.py record <gate-id> pass\|fail --note \"...\""` | Contract for runner recording commands. |
| **Prose / Runbooks** | `AGENTS.md:66`<br>`Docs/AGENT_TOOLS.md:90`<br>`Docs/Reports/REPEAT_CONSUME_VERDICT_2026-08-14.md:78`<br>`Docs/Handoffs/PARALLEL_LANES_2026-08-12.md:71` | `python Tools/record_gate.py <gate-id> pass --note "..."` | Instructions establishing invariant: *"A gate is certified only when record_gate.py writes a ledger row."* |

---

## 3. Evidence In-Hand vs. Envelope Conformance Gap

Conforming envelopes (`specs/schemas/evidence_envelope.v1.json`) require:
- `schema`: `"melodia.evidence_envelope.v1"`
- `evidence_id`, `run_id`, `recorded_at_utc`
- `kind`: `gate | static | runtime | t3d_mutation | build | package | model`
- `status`: `pass | fail | hold`
- `repository`: `{ "root": str, "commit": str, "branch": str }`
- `producer`: `{ "tool": str, "version": str }`
- `checks`: Non-empty list of `{ "name": str, "status": "pass"|"fail"|"hold", "note": str }`
- `artifacts`: List of `{ "path": str, "sha256"?: str, "role"?: str }`

### Caller Migration Table

| Caller | Evidence in Hand at Recording Point | Feasibility | Migration Gap / Action Needed |
| :--- | :--- | :--- | :--- |
| **`Tools/playtest_harness.py`** (`record` command) | Only CLI arguments (`status`, `note`, `session`). When running `run`/`ab`: snapshot damage dictionary, key injection timings, and screen captures. | **Incomplete at `record` step** | The `record` CLI subcommand is separated from `run`/`ab`. `run`/`ab` must emit an envelope JSON file into `Saved/Envelopes/` (via `evidence_envelope.make_envelope`) with screenshot artifact paths and damage assertions, and pass `--envelope` to `write_gate`. |
| **`Tools/echo_run.py`** (`record` command) | Only CLI strings (`gate_id`, `status`, `note`). | **Unpackaged** | `echo_run` runs individual sub-tools in `run static_gates` / `run runtime_gates` but discards structured results before calling `record`. Must generate an envelope using `make_envelope` summarizing sub-checks before delegating to `record_gate`. |
| **`.github/workflows/echo_gates.yml`** | Commit SHA (`${{ github.sha }}`), runner exit codes (`$LASTEXITCODE`), JSON files in `$env:TEMP` (`bp_sweep_ci.json`, `ui_audit_ci.json`, `art_gates` summary). | **Ready for Envelope Assembly** | All raw data exists in runner workspace. Needs an explicit step: `python Tools/evidence_envelope.py create --kind static --status pass --producer github-actions --check-name static_gates --check-status pass --artifact ... --output Saved/Envelopes/static_gates.json`, then pass `--envelope Saved/Envelopes/static_gates.json` to `record_gate.py`. |
| **`Tools/overnight_analysis.py`** | Read-only invocation (`--list`). | **N/A** | No ledger write occurs; zero migration gap. |
| **`Tools/test_echo_contract.py`** | Introspects `_all_known_gates()`. | **N/A** | No ledger write occurs; zero migration gap. |
| **Direct Human / Agent CLI** | User input string and observation notes. | **Blocked without helper** | Humans cannot write full conforming JSON envelopes by hand in shell. Needs either `--envelope <path>` support with helper creation commands, or a `--synthesize-envelope` fallback in `record_gate.py`. |

---

## 4. Two-State vs. Three-State (`hold`) Ledger Assumptions

`specs/echo_pipeline.json` lines 112–122 define `holds_without_editor` across 9 gates (`bp_live_path`, `graph_reachability`, `bp_sweep`, `ui_lint`, `verify_baseline`, `pie_smoke`, `regression`, `fingerprint`, `runtime_gates`). While `evidence_envelope.py` supports `"hold"`, the ledger ecosystem is strictly binary (`pass` | `fail`).

### Code Locations Assuming Two-State Ledger:

1. **`Tools/record_gate.py:126-127`**: `if status not in ("pass", "fail"): raise ValueError("status must be pass or fail")`.
2. **`Tools/record_gate.py:151`**: `target_list = session.setdefault("gates_passed" if status == "pass" else "gates_failed", [])` — binary session partitioning; `hold` would default into `gates_failed`.
3. **`Tools/record_gate.py:190-192`**: `passed = sum(...)`, `failed = sum(...)` — `total = len(gates)` ignores `hold` in breakdown totals.
4. **`Tools/record_gate.py:230`**: CLI argument choices restricted to `choices=["pass", "fail"]`.
5. **`Tools/echo_run.py:19-20, 646, 679`**: Hard invariant: *"A HOLD is not a pass and never writes a ledger row."* Subcommand `record` enforces `choices=["pass", "fail"]` and exits `0 if args.status == "pass" else 1`.
6. **`Tools/playtest_harness.py:328`**: Subcommand `record` enforces `choices=["pass", "fail"]`.
7. **`Tools/project_state.py:358-365`**: Maps status `pass -> PASS`, `fail -> FAIL`, anything else `-> OPEN`.
8. **`Tools/build_milestone_page.py:119, 125`**: Sums only `PASS` statuses and marks non-pass rows with CSS class `"open"`.
9. **`.github/workflows/release_tag.yml:52`**: Blocks release tags on `gates[g].get("status") != "pass"`.

> [!IMPORTANT]
> **Architectural Invariant:** Current system design dictates that `HOLD` is an in-memory execution state when the Unreal Editor / Monolith is offline. **`HOLD` should never write a row to `gate_ledger.json`**. If `HOLD` rows are ever permitted into the ledger, all 9 locations above must be updated simultaneously.

---

## 5. Coverage Floor Mechanics in `Tools/run_contract_tests.py`

When adding tests for the new envelope requirement, `Tools/run_contract_tests.py` enforces a strict coverage floor:

- **Suite Declaration:** `SUITES` tuple (`Tools/run_contract_tests.py:39-57`) maps suite paths to regex patterns.
- **Coverage Floor Constant:** `MINIMUM_SUITE_COUNT = 17` (`line 61`).
- **Assertion Matcher:**
  - Child process execution must return code 0.
  - Combined stdout/stderr must match `success_pattern`. If regex has $\ge 2$ capture groups (`=== (\d+)/(\d+) passed ===`), requires `observed > 0 and observed == total`.
- **Pass Invariant (`lines 139-143`):**
  ```python
  return 0 if (
      report["failed"] == 0
      and report["passed"] == len(SUITES)
      and len(SUITES) >= report["coverage_floor"]
  ) else 1
  ```

### How to Add a Test Suite Without Breaking the Gate:
1. Ensure test output emits standard `unittest` format (`Ran \d+ tests... OK`) or custom assertion string (`=== X/X passed ===`).
2. Add `Suite("Tools/test_evidence_envelope_ledger.py", <pattern>)` to `SUITES`.
3. Increment `MINIMUM_SUITE_COUNT = 18`.

---

## 6. Minimal Implementation Order (Ordered by Risk)

### Step 1: Core Schema & Envelope Validator in `record_gate.py` (Lowest Risk)
- Add `--envelope <path>` argument to `record_gate.py` CLI and `record_gate()` function signature.
- Import `validate_envelope` from `Tools/evidence_envelope.py`.
- Reject ledger writes if envelope is missing or invalid.
- Store envelope reference (`evidence_id`, `run_id`, `artifacts`) inside ledger rows.
- Extend `Tools/test_evidence_envelope.py` to verify envelope rejection / acceptance.

### Step 2: CI Workflow Update (Low Risk)
- In `.github/workflows/echo_gates.yml`, add a step before recording:
  ```powershell
  python Tools/evidence_envelope.py create `
    --kind static `
    --status pass `
    --producer github-actions `
    --check-name static_gates `
    --check-status pass `
    --artifact "$env:TEMP\bp_sweep_ci.json" `
    --artifact "$env:TEMP\ui_audit_ci.json" `
    --output "$env:TEMP\static_gates_envelope.json"
  python Tools/record_gate.py static_gates pass --envelope "$env:TEMP\static_gates_envelope.json" --note "CI echo_gates.yml ${{ github.sha }}"
  ```

### Step 3: Tooling Adaptation (`echo_run.py`, `playtest_harness.py`) (Medium Risk)
- Update `Tools/echo_run.py` subcommand `record` to accept and forward `--envelope`.
- Update `Tools/playtest_harness.py`: have `run` and `ab` construct and output an envelope into `Saved/Envelopes/`, then supply it to `write_gate`.

### Step 4: Runbook & Agent Invariant Documentation (Low Risk)
- Update `Docs/AGENT_TOOLS.md` and `AGENTS.md` to specify envelope generation before ledger recording.
