# Gate-test coverage gap and resolution (2026-08-14)

**Initial finding:** ~140 assertions were present but CI executed zero of the
script-style suites. **Resolution:** `Tools/run_contract_tests.py` now invokes an
explicit suite manifest, requires a success marker from every suite, and is wired
into `echo_gates.yml` and `BuildGraph/MelodiaBuildGraph.xml`.

Found while sweeping the pure-logic suites for cross-lane breakage after several agents
edited concurrently. The suites are healthy. **CI never runs any of them.**

---

## 1. The finding

| Workflow | What it runs | Covers `Tools/test_*.py`? |
|---|---|---|
| `unreal_build.yml:65-68` | `python -m pytest`, **`working-directory: Content/Python`** | **No** — scoped to another directory |
| `echo_gates.yml` | `echo_run.py`, `graph_reachability.py`, `bp_sweep.py`, `ui_style_audit.py`, `art_gates.py`, `git_safe_push.py`, `lfs_health_audit.py`, `record_gate.py` | **No** — gate *scripts*, never test suites |

Twelve suites, roughly **140 assertions**, executed only when a human remembers:

```
test_t3d_safe_wire.py           ~41   the postcondition-fix guards
test_melodia_content_fixtures.py ~40
test_t3d_request_contract.py    ~18
test_echo_contract.py           ~11   (reports 54/54 internally)
test_melodia_bp_readiness.py    ~11
test_mcp_policy.py               ~8
test_ui_style_audit.py           ~6
test_mcp_registration.py         ~4
+ evidence_envelope, ollama_health, melusina_anim_unit_guard, cute_gn_ornaments
```

`test_t3d_safe_wire.py` is the sharp one. Its 41 assertions are the only thing standing
between the repaired T3D postcondition and a silent regression back to the tautology that
made two ledger rows meaningless. **Nothing automated runs them.**

## 2. Why a naive fix makes it worse

The suites are split across two invocation styles, and each runner is silently wrong about
the other:

| Style | Files | `python <file>` | `pytest <file>` |
|---|---|---|---|
| script (`main()` + `results.append`) | 9 | runs, reports N/N | **`collected 0 items — no tests ran`** |
| pytest (`def test_*` + `assert`) | 3 | import error, or defines functions and exits 0 | runs |

**Adding `pytest Tools/` to CI would collect zero tests from the nine script-style suites and
report success.** That is the same green-light-wired-to-nothing failure this project has now
hit three separate times today — the T3D assertion, my own test-harness edit, and this.

Verified directly: `python -m pytest Tools/test_t3d_safe_wire.py` → *collected 0 items*.
Those 41 assertions do not exist as far as pytest is concerned.

## 3. It is not a broken test

`test_mcp_registration.py` fails as `python Tools/test_mcp_registration.py`
(`ModuleNotFoundError: No module named 'Tools'`) but passes as
`python -m pytest Tools/test_mcp_registration.py` (1 passed) and as
`python -m Tools.test_mcp_registration` (exit 0).

My sweep used the wrong runner for it. Recording that because the traceback looks exactly
like a defect and will waste someone's time otherwise.

`test_cute_gn_ornaments.py` needs `bpy` and only runs inside Blender. Correct by design.

## 4. Most of them are also untracked

`git ls-files` says **8 of 12 are not in git** — `Tools/*` again:

```
tracked:    test_echo_contract, test_melusina_anim_unit_guard,
            test_t3d_safe_wire, test_ui_style_audit
UNTRACKED:  test_cute_gn_ornaments, test_evidence_envelope, test_mcp_policy,
            test_mcp_registration, test_melodia_bp_readiness,
            test_melodia_content_fixtures, test_ollama_health, test_t3d_request_contract
```

`validate_mcp_registration.py` — the module one of them imports — is untracked too.

This compounds `LOST_TOOL_SOURCES_2026-08-14.md`: ~91 tool sources already went that way. Eight
test suites are sitting in the same position, and losing a test is quieter than losing a tool
because nothing stops working.

## 5. Fix

1. **Make invocation uniform first.** Either give the nine script-style suites a
   `def test_main(): assert main() == 0` wrapper so pytest collects them, or standardise on
   the script style and have CI call each explicitly. **Uniform matters more than which** —
   the split is what makes a runner silently under-collect.
2. **Then add a CI step** that runs them. `echo_gates.yml` is the right home; it already runs
   `Tools/*` scripts on PR and push.
3. **Assert a floor.** Whatever runner is used must fail when the collected count drops —
   `pytest --collect-only` reporting 0 has to be an error, not a pass. Otherwise step 2
   reintroduces the same hole.
4. **Track the eight untracked suites** — same `.gitignore` carve-out decision as
   `wardrobe_draft_lint.py` and `doc_link_check.py`, and the same argument for inverting the
   `Tools/` rule rather than extending the allowlist a ninth time.

## 6. Resolution applied

The runner is dependency-free and does not contact Unreal, Monolith, AWS, or the
network. It runs the script-style suites as subprocesses, requires a non-empty
assertion-bearing marker, and fails if any suite is missing, non-zero, or returns
zero without its marker. The MCP registration test now has a direct `main()` entry
point, so the coverage floor does not depend on pytest being installed. Required
runner/test sources are carved out of the broad `Tools/*` ignore rule so a clean CI
checkout receives them.

The Blender-only `test_cute_gn_ornaments.py` remains outside this runner by design;
it requires Blender and is not an Unreal contract gate.

## 7. Scope

Enumerates and verifies only. No test, workflow, or `.gitignore` was modified — the
invocation-uniformity decision in §5.1 shapes everything after it, and it is an owner call.

Current state, for the record: all listed offline suites **pass** when invoked correctly
(`test_t3d_safe_wire` 41/41, `test_echo_contract` 54/54, `test_mcp_policy` 8/8,
`test_ui_style_audit` 5/5, `test_mcp_registration` direct policy pass,
`test_melodia_skill_bridge_contract` pass, `test_evidence_envelope` OK,
`test_ollama_health` OK). Nothing here is failing. It is simply
unguarded.
