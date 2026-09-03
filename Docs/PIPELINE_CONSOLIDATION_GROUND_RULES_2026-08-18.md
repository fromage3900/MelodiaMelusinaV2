# Pipeline Consolidation & Ground Rules — 2026-08-18

**Context:** T3D dated, Echo needs refresh, Melodia MCP solid but text injection needs rules.
**Status:** READ-ONLY assessment. Proposes consolidation, not executes it.

---

## 1. Current Pipeline Inventory

### 1.1 T3D Pipeline (RETIRE)

| File | Size | Purpose | Status |
|------|------|---------|--------|
| `t3d_safe_wire.py` | 855 LOC | 9-step fail-closed wiring gate | **STALED** — self-tautological verification per 08-14 postmortem |
| `t3d_blueprint_injector.py` | 147 LOC | Hand-rolled T3D Blueprint mutation | **RETIRED** — use Monolith `blueprint_query` actions |
| `t3d_anim_injector.py` | 360 LOC | Hand-rolled T3D animation mutation | **RETIRED** — use Monolith `animation_query` actions |
| `t3d_niagara_injector.py` | 632 LOC | Niagara VFX T3D injection | **RETIRED** — use Monolith `editor_query.run_python` |
| `t3d_material_curve_injector.py` | 422 LOC | Material curve T3D injection | **RETIRED** — use Monolith `material_query` actions |
| `t3d_mesh_lod_injector.py` | 277 LOC | Mesh LOD T3D injection | **RETIRED** — use Monolith `mesh_query` actions |
| `t3d_dashboard.py` | 277 LOC | T3D monitoring dashboard | **RETIRED** — superseded by Monolith live status |
| `t3d_wardrobe_ch2_injector.py` | 125 LOC | Wardrobe chapter 2 injection | **RETIRED** — no longer needed |
| 5x `*_demo.py` files | ~120 LOC total | Demo scripts | **RETIRED** |

**Why retire:** Monolith MCP exposes 1330 first-class C++-backed actions across 24 namespaces. Hand-rolling T3D injection is error-prone, cannot be compile-checked, and duplicates what Monolith already does. The 9-step T3D gate's postcondition check was tautological (proved serialization, not correctness) per 08-14 postmortem.

**Migration path:** All T3D writes → Monolith MCP first-class actions. T3D export remains useful for rollback records and audit trails.

### 1.2 Echo Pipeline (REFRESH)

| File | Size | Purpose | Status |
|------|------|---------|--------|
| `echo_run.py` | 686 LOC | Integration gate chain runner | **NEEDS REFRESH** — still relevant, needs new stages |
| `specs/echo_pipeline.json` | — | Gate manifest (author → validate → inject → compile → test → record → promote) | **NEEDS UPDATE** — remove T3D stages, add Monolith stages |

**Why keep:** Echo is a verification pipeline, not an authoring pipeline. It runs static gates (offline spec validation), runtime gates (PIE smoke, regression, fingerprint), and records ledger rows. The 7-verb Quill dispatch contract (`melodia:battle:`, `melodia:quest:`, etc.) is still the narrative authority.

**Refresh plan:**
- Remove T3D injection stages
- Add Monolith-backed static gates (e.g., `animation_query.get_state_machines` validation)
- Add `melodia_mcp_server` health check stage
- Keep the gate_ledger.json contract: no row = not done

### 1.3 Melodia MCP Server (KEEP + EXPAND)

| File | Size | Purpose | Status |
|------|------|---------|--------|
| `deploy/melodia_mcp_server.py` | 926 LOC | 13 read-only tools for persona, Quill, rhythm, narrative, fixtures | **SOLID** — offline-capable, policy-gated, JSON Schema validated |
| `Tools/mcp_policy.py` | 95 LOC | Authorization layer (default-deny, approval hierarchy, forbidden paths) | **KEEP** — needs expansion for new tools |
| `specs/mcp/melodia_mcp_tools.v1.json` | — | JSON Schema spec for 13 tools | **KEEP** — add new tools as needed |
| `Tools/test_melodia_mcp.py` | 238 LOC | 13 standalone tests (no pytest required) | **KEEP** — expand with new tool tests |

**Why keep:** This is the cleanest part of the pipeline. Offline-safe, read-only, policy-gated, spec-validated. The 13 tools map to real gameplay systems (persona stats, Quill notifications, rhythm skills, narrative record, Blueprint fixtures).

**Expansion plan:**
- Add `melodia_animation_validate_state_machine` — read-only ABP state machine health check
- Add `melodia_animation_validate_bindings` — verify all states have connected pose outputs
- Add `melodia_animation_validate_no_tpose` — detect disconnected blendspace/sequence players
- Add `melodia_animation_get_runtime_abp` — return which ABP is assigned to the live character BP

### 1.4 Monolith MCP (THE WRITER)

| Namespace | Actions | Role |
|-----------|---------|------|
| `animation_query` | 200 | State machines, blendspaces, montages, curves, IK rigs, retargeters |
| `blueprint_query` | ~150 | BP graph export, compilation, CDO properties, T3D injection |
| `editor_query` | ~100 | Actor spawning, level loading, PIE, run_python |
| `material_query` | ~80 | Material graph editing, parameter wiring |
| `mesh_query` | ~60 | Mesh analysis, raycasting, LOD |
| `niagara_query` | ~50 | VFX system editing |
| `cppreflect` | ~30 | C++ reflection, CDO properties |

**This is the ONLY sanctioned writer.** All mutations go through first-class Monolith actions. No hand-rolled T3D.

---

## 2. Proposed Ground Rules

### Rule 1: Monolith MCP is the ONLY Writer

All mutations to UE5 assets (Blueprints, animations, materials, meshes, Niagara) MUST go through Monolith MCP first-class actions.

```
❌ t3d_blueprint_injector.py  → hand-rolled T3D  (DANGEROUS, UNVERIFIABLE)
✅ blueprint_query.add_variable → C++-backed action (VALIDATED, COMPILED)
```

Exception: `editor_query.run_python` for one-off scripts that have no first-class action. These must be reviewed and converted to skills or tools when stable.

### Rule 2: Melodia MCP Server is the READ Surface

All read-only queries (persona stats, Quill validation, fixture checks, system health, narrative state) go through the Melodia MCP server. It is offline-capable and policy-gated.

```
READ  → Melodia MCP server (offline-safe, policy-gated, JSON Schema validated)
WRITE → Monolith MCP (C++-backed, compiled, ledger-recorded)
```

### Rule 3: Echo Pipeline is the VERIFIER

After Monolith writes, Echo pipeline verifies:
- Static gates: spec validation, contract checks, fixture readiness
- Runtime gates: PIE smoke, regression tests, fingerprint comparison
- Ledger: every pass/fail produces a row in `gate_ledger.json`

No ledger row = not done.

### Rule 4: No Handwritten T3D for Mutation

T3D (Textual Blueprint) export is sanctioned for:
- Rollback records (before/after snapshots)
- Audit trails (evidence manifests)
- Debug inspection (read-only graph export)

T3D is NOT sanctioned for:
- Node injection
- Pin connection
- State machine editing
- Blendspace editing

Use Monolith first-class actions instead.

### Rule 5: Kimi Integration Protocol

Kimi (or any AI agent) interacts with the pipeline as follows:

```
1. READ    → Melodia MCP server (read-only, offline-safe)
2. PLAN    → Generate a mutation plan (which Monolithic actions to call)
3. VERIFY  → Echo static gates (spec validation)
4. WRITE   → Monolith MCP first-class actions (one at a time, abort on failure)
5. COMPILE → blueprint_query.compile_blueprint (immediate, no deferral)
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

If the retry also fails, escalate to owner. Never retry blindly.

### Rule 7: Text Injection Safety

For `editor_query.run_python` text injection (the only sanctioned "text" path):
- Must be full Python scripts, not T3D fragments
- Must be reviewed by a human before execution on production assets
- Must include error handling (no silent no-ops)
- Must produce a ledger row or audit log entry

### Rule 8: Policy Gate is Enforced

`Tools/mcp_policy.py` is the authorization layer:
- **Default-deny:** Unlisted tools are rejected
- **Approval hierarchy:** none (read) → editor (mutate) → owner (schema)
- **Forbidden paths:** Protected directory tokens trigger immediate violation

Every tool call passes through `authorize_tool()` before execution.

---

## 3. Consolidation Map

```
BEFORE (scattered):
  T3D injectors → Blueprint mutation
  Echo run.py   → Gate chain (mixed T3D + Monolith)
  Melodia MCP   → Read-only tools
  Monolith MCP  → Read + Write (no policy layer)

AFTER (consolidated):
  Melodia MCP server  → READ surface (13+ tools, offline-safe, policy-gated)
  Monolith MCP        → WRITE surface (1330 actions, C++-backed, compiled)
  Echo pipeline       → VERIFY surface (static + runtime gates, ledger-backed)
  mcp_policy.py       → AUTHORIZATION layer (default-deny, approval hierarchy)
  T3D injectors       → RETIRED (read-only T3D export for rollback/audit only)
```

---

## 4. Immediate Actions (when approved)

1. **Archive T3D injectors** → move to `_Archive/T3D_20260818/`
2. **Refresh Echo pipeline** → remove T3D stages, add Monolith stages
3. **Expand Melodia MCP** → add animation validation tools (state machine health, binding checks, T-pose detection)
4. **Add policy entries** → cover new Melodia MCP animation tools
5. **Document Kimi protocol** → write `Docs/KIMI_INTEGRATION_PROTOCOL.md`
6. **Run Echo gates** → verify the animation pipeline work from this session

---

*Document: PIPELINE_CONSOLIDATION_GROUND_RULES_2026-08-18.md*
*Status: READ-ONLY proposal. No mutations made.*
