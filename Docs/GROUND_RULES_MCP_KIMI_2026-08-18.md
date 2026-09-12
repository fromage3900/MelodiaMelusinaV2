# Ground Rules: Text Injection, MCP Server, and Kimi Integration

**Date:** 2026-08-18
**Status:** READ-ONLY proposal. Awaiting approval before execution.
**Context:** T3D pipeline retired. Echo pipeline needs refresh. Melodia MCP solid. Kimi needs protocol.

---

## 1. The 8 Ground Rules

### Rule 1: Monolith MCP is the ONLY Writer

All mutations to UE5 assets go through Monolith first-class actions.

| ❌ NEVER | ✅ ALWAYS |
|----------|-----------|
| Hand-rolled T3D injection | `blueprint_query.add_variable` |
| `t3d_blueprint_injector.py` | `animation_query.set_state_animation` |
| Raw T3D text fragments | `material_query.set_material_parameter` |
| Hard-coded node GUIDs | `editor_query.run_python` (reviewed scripts only) |

### Rule 2: Melodia MCP is the READ Surface

All read-only queries go through the Melodia MCP server:
- Persona stats, quests, social records
- Quill notification validation (7-verb contract)
- Rhythm skill catalog
- Narrative record schema
- Blueprint fixture readiness
- System health checks
- Animation state machine validation (NEW this session)
- Animation binding validation / T-pose detection (NEW this session)
- Runtime ABP assignment query (NEW this session)

Offline-safe. Policy-gated. JSON Schema validated.

### Rule 3: Echo Pipeline is the VERIFIER

After Monolith writes, Echo verifies:
- Static gates: spec validation, fixture readiness, graph reachability
- Runtime gates: PIE smoke, regression, fingerprint comparison
- Ledger: every pass/fail → row in `gate_ledger.json`

No ledger row = not done.

### Rule 4: No Handwritten T3D for Mutation

T3D export is sanctioned for:
- Rollback records (before/after snapshots)
- Audit trails (evidence manifests)
- Debug inspection (read-only graph export)

T3D is NOT sanctioned for:
- Node injection, pin connection, state machine editing, blendspace editing

All 12 T3D injectors archived to `Tools/_Archive/T3D_20260818/`.

### Rule 5: Kimi Integration Protocol

```
1. READ    → Melodia MCP server (read-only, offline-safe)
2. PLAN    → Generate mutation plan (which Monolith actions to call)
3. VERIFY  → Echo static gates (spec validation, fixture checks)
4. WRITE   → Monolith MCP first-class actions (one at a time)
5. COMPILE → blueprint_query.compile_blueprint (immediate)
6. SAVE    → editor_query.run_python (modify + save)
7. VERIFY  → Echo runtime gates (regression, fingerprint)
8. RECORD  → gate_ledger.json row
```

### Rule 6: All Writes Abort on First Failure

No retry loops. If a write fails:
1. Stop immediately
2. Read the error
3. Diagnose root cause
4. Fix the params
5. Retry once

If retry also fails, escalate to owner.

### Rule 7: Text Injection Safety

`editor_query.run_python` is the only sanctioned "text" path:
- Full Python scripts, NOT T3D fragments
- Must be reviewed by human before execution on production assets
- Must include error handling (no silent no-ops)
- Must produce a ledger row or audit log entry

### Rule 8: Policy Gate is Enforced

`Tools/mcp_policy.py`:
- **Default-deny:** Unlisted tools rejected
- **Approval hierarchy:** none (read) → editor (mutate) → owner (schema)
- **Forbidden paths:** Protected directory tokens trigger immediate violation

Every tool call passes through `authorize_tool()` before execution.

---

## 2. Pipeline Consolidation Map

```
BEFORE (scattered):
├── T3D injectors (12 files)     → Blueprint mutation (DANGEROUS)
├── Echo run.py (686 LOC)        → Gate chain (mixed T3D + Monolith)
├── Melodia MCP server (926 LOC) → 13 read-only tools
└── Monolith MCP (1330 actions)  → Read + Write (no policy layer)

AFTER (consolidated):
├── Melodia MCP server           → READ surface (16 tools, offline-safe)
├── Monolith MCP                 → WRITE surface (1330 actions, C++-backed)
├── Echo pipeline                → VERIFY surface (static + runtime gates)
├── mcp_policy.py                → AUTHORIZATION layer (default-deny)
└── T3D injectors                → RETIRED (archived)
```

---

## 3. New Animation Validation Tools (Added This Session)

### melodia_animation_validate_state_machine
Validates an ABP's state machine health:
- Entry state exists in states list
- All states have sequence/blendspace players
- No orphan transitions (from/to must exist)

**Output:** `all_ok` boolean + findings list.

### melodia_animation_validate_bindings
Verifies all animation nodes have connected pose outputs:
- Detects blendspace/sequence players with 0 connections
- Detects missing pose output pins
- Direct T-pose cause detection

**Output:** `all_ok` boolean + findings list.

### melodia_animation_get_runtime_abp
Returns which ABP is assigned to a character BP's Mesh component:
- Detects skeleton mismatches between mesh and anim class
- Reports inherited vs explicitly set AnimClass
- Flags potential T-pose causes

**Output:** `status` (matched/inherited/check_mesh) + skeleton info.

---

## 4. Echo Pipeline Refresh Plan

### Remove (T3D stages):
- `inject` stage (t3d_blueprint_injector.py)
- `static_gates` → graph_reachability, bp_live_path, ui_lint, bp_sweep, verify_baseline (all T3D-based)

### Add (Monolith stages):
- `spec_validate` → keep (Quill notification validation)
- `monolith_static` → animation state machine validation, binding validation
- `monolith_compile` → blueprint_query.compile_blueprint
- `runtime_gates` → keep (PIE smoke, regression, fingerprint)

### New gate_ledger IDs:
- `monolith_static` — animation validation passes
- `monolith_compile` — 0 errors
- `animation_bindings` — no disconnected pose outputs

---

## 5. Implementation Checklist

- [x] Archive T3D injectors to `Tools/_Archive/T3D_20260818/`
- [x] Add 3 animation validation tools to Melodia MCP server
- [x] Add 3 policy entries to `specs/mcp_tool_policy.v1.json`
- [x] Add 3 JSON Schema entries to `specs/mcp/melodia_mcp_tools.v1.json`
- [x] Add 3 tests to `Tools/test_melodia_mcp.py`
- [ ] Refresh `specs/echo_pipeline.json` (remove T3D, add Monolith)
- [ ] Refresh `Tools/echo_run.py` (remove T3D stages, add animation validation)
- [ ] Write Kimi integration protocol doc
- [ ] Run full Echo gate suite
- [ ] Commit all changes

---

*Document: GROUND_RULES_MCP_KIMI_2026-08-18.md*
*Status: READ-ONLY proposal. No mutations made except where noted.*
