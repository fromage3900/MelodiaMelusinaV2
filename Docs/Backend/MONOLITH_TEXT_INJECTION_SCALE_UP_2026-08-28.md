# Monolith / T3D Text-Injection Scale-Up — Long-Term Deep Dive (2026-08-28)

**Status:** planning/draft, offline, no editor
**Author:** Melusina (Hermes agent, no-editor lane)
**Live with:** Junie (Rider, editor lock) — this lane stays offline until she frees it
**Companion:** `Docs/Backend/MELODIA_BACKEND_INTEGRATION_PLAN_2026-08-28.md` (§3 — the summary;
this is the deep dive)

---

## Purpose

A deep dive on the T3D/Monolith text-injection pipeline at scale — what exists today, what "at
scale" means, the batch spec format, the one-baseline-many-assertions pattern, the Echo ledger rows
per family, and the gap to fill. Written so that any agent — this lane or a future one — can pick it
up and know exactly how to author a batch of content, how to verify it, and how to record it.

This is the "updated integration using text injection" piece the user asked for.

---

## 1. What "text injection" means in this project

### The pipeline

The T3D/Monolith pipeline is the project's declarative content-authoring path: a JSON spec is read by
a Python harness, injected into the running editor via Monolith JSON-RPC, compiled, fingerprinted,
asserted, and promoted. The canonical sequence (from `AGENTS.md` § T3D Wiring Pipeline and
`Docs/Production/T3D_MONOLITH_REFERENCE.md`):

```
Spec Change → T3D Inject → Compile → Fingerprint → Regression Test → Promote
```

Echo orchestration (added 2026-08-09) layers an evidence ledger on top: agents author content, gates
score it, nothing is believed without a ledger row. The Echo manifest is `specs/echo_pipeline.json`;
the runner is `Tools/echo_run.py`.

### What "text" means

"Text injection" here is T3D — the serialized text form of Unreal assets. The pipeline reads a JSON
spec, builds the T3D, injects it into the editor, and the editor deserializes it into a `.uasset`. The
key Monolith actions:
- `project_query:export_asset_text` — export an asset as T3D text (universal escape hatch)
- `blueprint_query:build_blueprint_from_spec` — inject T3D spec in a single transaction
- `blueprint_query:compile_blueprint` — compile the Blueprint
- `blueprint_query:get_graph_fingerprint` — topology fingerprint
- `blueprint_query:assert_graph_matches` — verify no unintended rewire
- `material_query:set_instance_parameter` / `set_instance_parameters` — set scalar/vector/texture on
  a material instance
- `material_query:build_material_graph` — build a material graph from a JSON spec
- `material_query:recompile_material` — force a material recompile

### What exists today (the one-off scale)

- Toon profile specs: `specs/toon_profiles/tp_melusina.json` (and others)
- Niagara MPC binding specs: `specs/niagara_mpc_bindings.json`
- Material-curve injector: `Tools/t3d_material_curve_injector.py` with `apply_toon_profile_spec()`
- Blueprint injector: `Tools/t3d_blueprint_injector.py` with `T3DBlueprintInjector.inject_into()`
- Material inject demo: `Tools/t3d_material_inject_demo.py` (read/verify/all CLI)
- CI gates: `ci_gates.json` (graph fingerprint exact_match, blueprint_compile 0_errors,
  material_compile 0_errors, shader_instructions max_150, triangle_budget max_250k,
  pie_smoke 0_crashes, animation_delta threshold_0.05, accessibility pass)

These work for one-off assets — one toon profile, one material instance, one Blueprint. "At scale" is
the point where the same pipeline authors whole families in one batch.

---

## 2. What "at scale" means

### The scale jump

| Scale | What it looks like | What's missing |
|-------|-------------------|----------------|
| One-off | One spec file → one asset → one fingerprint → one assertion | Nothing — it works today |
| Batch (one family) | One manifest → N assets → one pre-inject baseline → N post-inject assertions → one Echo row | Batch spec format, batch injector, batch verifier |
| Batch (many families) | Many manifests → many families → one static-chain pass → many Echo rows | Full static chain rerun, many Echo rows, promote step |

### Why batch matters

The P0 content pillar is four scripts + one config edit. That is a one-off. But the long-term items —
multiple toon profiles, multiple Niagara systems, multiple material instances, multiple Blueprint
fixtures — are batches. The pipeline needs to:
1. **Batch specs** — one spec file per family, not per asset, with a manifest that lists the asset
   paths and the expected post-inject state.
2. **One baseline, many assertions** — `bp_regression_checker.py` compares fingerprints; at scale you
   want one pre-inject baseline and one post-inject assertion per family, not per asset.
3. **Echo ledger rows per family** — each family gets a gate-id and a `record <id> pass|fail` row.
   The Echo contract says a lane is "done" only when the gate it claims has a ledger row.

---

## 3. The batch spec format (a planning sketch, not yet implemented)

### Sketch

```json
{
  "batch_id": "batch.toon_profiles.v1",
  "manifest_version": "1.0",
  "families": [
    {
      "family_id": "family.melusina_toon",
      "asset_paths": [
        "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina",
        "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina_Alpha"
      ],
      "spec_paths": [
        "specs/toon_profiles/tp_melusina.json",
        "specs/toon_profiles/tp_melusina_alpha.json"
      ],
      "expected": {
        "compile": "0_errors",
        "fingerprint": "<per-asset, recorded pre-inject>",
        "material_compile": "0_errors"
      }
    }
  ]
}
```

### Caveats

- This is a planning sketch. The real format will be driven by what `bp_regression_checker.py` and
  `t3d_blueprint_injector.py` already accept — don't invent a new contract until you've read those.
- The `fingerprint` field is per-asset — each asset gets its own pre-inject fingerprint. The batch
  injector walks the manifest, injects each asset, compiles, fingerprints, asserts.
- The `expected.compile` and `expected.material_compile` are gate-level assertions (0_errors, from
  `ci_gates.json`).

### What the batch injector must do

1. Walk the manifest.
2. For each family:
   a. Record the pre-inject fingerprints for all assets in the family (one baseline).
   b. Inject each asset via `blueprint_query:build_blueprint_from_spec` or
      `material_query:build_material_graph`.
   c. Compile each asset via `blueprint_query:compile_blueprint` or
      `material_query:recompile_material`.
   d. Assert each asset's fingerprint via `blueprint_query:assert_graph_matches`.
   e. Record the post-inject fingerprints.
3. For the whole batch:
   a. Run the full static chain (graph reachability + bp_live_path + bp_sweep + ui_style_audit +
      material baseline) against the post-inject tree.
   b. Record one Echo row per family via `Tools/echo_run.py record <family_id> pass|fail`.

---

## 4. The one-baseline-many-assertions pattern

### Why one baseline

A fingerprint is a topology hash. If you inject 10 assets in one batch and record 10 pre-inject
fingerprints, then post-inject you have 10 assertions to make. That is fine for 10 assets. But if the
batch is 100 assets, you want one pre-inject baseline (the whole tree) and one post-inject assertion
(the whole tree) — the difference is the injected content, and the assertion is that the difference
matches the spec.

### Why many assertions still matter

One baseline + one assertion is fast, but it can mask a bad inject in one asset if another asset's
fingerprint drift cancels it out. The safe pattern is:
- One pre-inject baseline (the whole tree).
- One post-inject assertion (the whole tree).
- Per-asset fingerprint assertions for the assets that matter most (the ones with the highest risk of
  an unintended rewire).

### The risk

The `bp_regression_checker.py` compares fingerprints. If the post-inject tree has a drift that is not
in the spec (an unintended rewire), the assertion catches it. If the drift is in the spec (an intended
rewire), the assertion must be updated to match — that is the "record both fingerprints" step in the
apply workflow.

---

## 5. The Echo ledger rows per family

### The Echo contract

The Echo contract (from `AGENTS.md` § Echo orchestration, item: "a lane/agent is 'done' only when the
gate it claims has a ledger row") applies at the family level:
- Each family gets a gate-id.
- Each family gets a `record <family_id> pass|fail` row.
- The row is the evidence that the family was authored and verified.

### What a family Echo row looks like

```json
{
  "id": "batch.toon_profiles.v1.family.melusina_toon",
  "status": "pass",
  "date": "2026-08-28",
  "note": "Injected 2 toon profiles, compiled clean, fingerprints matched, static chain passed. Evidence: Saved/Echo/BatchToonProfiles/..."
}
```

### The promote step

The pipeline ends with `Promote` — the promoted asset is the one that is believed. At the one-off
scale, promote is "the asset is saved and the fingerprint is recorded." At the batch scale, promote is
"the whole family is saved, the fingerprints are recorded, the static chain passed, and the Echo row is
written." Nothing is believed without the row.

---

## 6. The gap to fill (what's missing for batch scale)

### Missing pieces

1. **Batch spec format** — a manifest that lists multiple asset paths + per-asset expected state (a
   manifest, not a flat spec). The sketch in §3 is a starting point.
2. **Batch injector** — a Python harness that walks the manifest, injects each asset, compiles,
   fingerprints, asserts. Built on top of `t3d_blueprint_injector.py` and `t3d_material_curve_injector.py`.
3. **Batch verifier** — a Python harness that runs the full static chain (graph reachability + bp_live_path
   + bp_sweep + ui_style_audit + material baseline) against the post-inject tree.
4. **Echo record step** — a Python harness that writes one row per family via `Tools/echo_run.py record
   <family_id> pass|fail`.

### What's not missing

- The Monolith actions (build_blueprint_from_spec, compile_blueprint, get_graph_fingerprint,
  assert_graph_matches, set_instance_parameters, build_material_graph, recompile_material) all exist.
- The CI gates (`ci_gates.json`) all exist.
- The Echo runner (`Tools/echo_run.py`) exists.
- The static-chain tools (bp_live_path, bp_sweep, ui_style_audit, t3d_dashboard) exist (editor-bound).

### Implementation sequence (draft)

1. Read `t3d_blueprint_injector.py` and `t3d_material_curve_injector.py` — confirm the exact API they
   expose (the batch injector is built on top of them, not a replacement).
2. Read `bp_regression_checker.py` — confirm the exact fingerprint comparison API (the batch verifier
   is built on top of it).
3. Read `Tools/echo_run.py` — confirm the exact record API (the Echo step is built on top of it).
4. Draft the batch spec format (the sketch in §3, refined against what the injector/verifier/echo
   actually accept).
5. Write the batch injector (Python, no new C++).
6. Write the batch verifier (Python, no new C++).
7. Write the Echo record step (Python, no new C++).
8. Test with one family (one-off scale first, then batch scale).
9. Record the Echo row.

### What this lane can do offline

- Read the existing tools (`t3d_blueprint_injector.py`, `t3d_material_curve_injector.py`,
  `bp_regression_checker.py`, `Tools/echo_run.py`) and draft the batch spec format + batch injector +
  batch verifier + Echo step.
- Write the batch spec format as a JSON schema draft.
- Write the batch injector/verifier/Echo step as Python harnesses (no new C++).

### What this lane cannot do offline

- Test the batch injector/verifier/Echo step — that requires the editor (Monolith).
- Run the static chain — that requires the editor.
- Record the Echo row — that requires the editor.

---

## 7. The updated integration using text injection (the user's ask)

### What "updated integration" means

The user asked for "updated integration using text injection." This is the path where content authoring
moves from manual Blueprint edits in the editor to declarative JSON specs injected via Monolith. The
pipeline is:

```
Author JSON spec → inject via Monolith → compile → fingerprint → assert → verify → promote
```

### What's already integrated

- Toon profiles: `specs/toon_profiles/tp_melusina.json` → injected via `t3d_material_curve_injector.py`.
- Niagara MPC bindings: `specs/niagara_mpc_bindings.json` → injected via Monolith.
- Material instances: injected via `t3d_material_curve_injector.py` and `t3d_material_inject_demo.py`.

### What needs updating for scale

- The batch spec format (a manifest, not a flat spec).
- The batch injector (a harness that walks the manifest).
- The batch verifier (a harness that runs the static chain).
- The Echo record step (a harness that writes one row per family).
- The CI gates (already exist — `ci_gates.json` — but need to be applied per family, not per asset).

### What's not an integration change

- No new C++. The batch injector/verifier/Echo step are Python harnesses built on top of existing
  Monolith actions.
- No new Monolith actions. The existing actions (build_blueprint_from_spec, compile_blueprint,
  get_graph_fingerprint, assert_graph_matches, set_instance_parameters, build_material_graph,
  recompile_material) are sufficient.
- No editor workflow change. The apply workflow (export → fingerprint → inject → compile → assert →
  fingerprint → save → re-read) is the same — the batch injector just does it for many assets at once.

---

## 8. File map

| File | Purpose |
|------|---------|
| `Docs/Backend/MONOLITH_TEXT_INJECTION_SCALE_UP_2026-08-28.md` | **this file** — deep dive on T3D/Monolith batch scale-up |
| `Docs/Backend/MELODIA_BACKEND_INTEGRATION_PLAN_2026-08-28.md` | Single plan for backend work (§3 is the summary of this) |
| `Docs/Production/T3D_MONOLITH_REFERENCE.md` | The Monolith/T3D reference (spec format, injection workflow, CI gates, action tables) |
| `specs/echo_pipeline.json` | The Echo pipeline manifest |
| `Tools/t3d_blueprint_injector.py` | Batch Blueprint subgraph injection via T3D |
| `Tools/t3d_material_curve_injector.py` | Material curve/scalar/color/texture injection via Monolith |
| `Tools/bp_regression_checker.py` | Graph fingerprint + baseline comparison |
| `Tools/echo_run.py` | Echo pipeline runner |
| `ci_gates.json` | CI gates (graph fingerprint, compile, material, shader, triangle, PIE, animation, accessibility) |
