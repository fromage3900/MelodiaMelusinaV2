# T3D / Echo Automation Pipeline — full reference

Moved out of `AGENTS.md` on 2026-10-01 for the same 32 KB budget reason.
`AGENTS.md` keeps the short form; this is the authoritative detail.

Companion: [`T3D_MONOLITH_REFERENCE.md`](T3D_MONOLITH_REFERENCE.md) for spec
injection recipes, Monolith action tables, and `ci_gates.json`.

## T3D Wiring Pipeline (Automation Pipeline)

### Pipeline Overview
```
Spec Change → T3D Inject → Compile → Fingerprint → Regression Test → Promote
```

### Echo orchestration (added 2026-08-09)

The pipeline above now has one runnable face and one evidence ledger — model
HoYoverse's in-house "Echo" AI platform: agents author content, gates score it,
nothing is believed without a ledger row.

- Manifest: `specs/echo_pipeline.json` (stages: author → spec_validate → inject
  → compile → static_gates → runtime_gates → record → promote)
- Runner: `Tools/echo_run.py` — `list`, `status`, `run static_gates`,
  `validate-spec <file>`, `record <gate-id> pass|fail`
- Control panel: `Tools/project_state.py --view integration` (four completion
  gates ledger-backed) and `--view staleness` (docs older than their subject
  are UNVERIFIED, not wrong). Output also at `Saved/Echo/state.txt`.
- Contract: a lane/agent is "done" only when the gate it claims has a ledger
  row. See `Docs/ECHO_PIPELINE_2026-08-09.md`.

### Core Tools (Already Built)
| Tool | Purpose | Entry Point |
|------|---------|-------------|
| `t3d_blueprint_injector.py` | Batch inject Blueprint subgraphs via T3D | `T3DBlueprintInjector.inject_into()` |
| `bp_regression_checker.py` | Graph fingerprinting + baseline comparison (fixed 2026-08-06: JSON-RPC envelope to `http://localhost:9316/mcp`) | `fetch_fingerprint()`, `compare_fingerprints()` |
| `continuous_loop.py` | Auto-detect → T3D fix → verify loop | `ContinuousLoop.check_and_fix()` |
| `nl_to_blueprint.py` | NL → LLM → spec → inject → verify | `main()` with `--bp` + `--prompt` |
| `pie_smoke_runner.py` | Headless PIE + Monolith polling | `PieSmokeRunner.run()` / `main()` |
| `regression_suite.py` | Quick/full OOD passes | `run_suite()` |
| `t3d_material_curve_injector.py` | Inject material curves, scalars, colors, textures via Monolith | `T3DMaterialCurveInjector.apply_toon_profile_spec()` |
| `t3d_material_inject_demo.py` | Demo: apply TP_Melusina spec with read/apply/verify | `main()` with `--read`, `--verify`, `--all` |

### Verification tools (added 2026-08-08)

Read-only. Each answers a question that a compile, a fingerprint and a smoke test all
answer wrongly.

| Tool | Question it answers |
|------|---------------------|
| `bp_live_path.py` | Is this asset reachable from a configured entry point? `LIVE` / `ORPHAN` / `AMBIGUOUS(n)`. Catches the "perfectly wired graph nothing instantiates" defect. |
| `bp_sweep.py` | Project-wide audit for five shipped defect classes: shadowed parent events, empty-bodied events, dead exec islands, unreachable assets, duplicate short names. |
| `ui_style_audit.py` | What fonts/colours/paddings are actually authored across every widget, and what is the smallest token set covering them. |
| `t3d_dashboard.py` | Where the material-spine complexity lives (offline; `--live` adds drift). |
| `project_state.py` | Derived project state + doc staleness radar. Reads state, never prose. |
| `graph_reachability.py` | Dead exec islands *inside* a graph. Complements `bp_live_path` — a graph can pass this and still be an asset nothing constructs. |
| `rhythm_battle_runtime_probe.py` | Direct-invocation driver for the stock-skill rhythm seam (subsystem + controller events called straight from Python). **Not** gate evidence — see below. |

Two of these have committed assertions because loosening a check is how you blind one:
`Docs/T3D_Baseline/test_canonical.py` and `Tools/test_ui_style_audit.py`. Run them after
touching the corresponding tool.

### Evidence standard — runtime/rhythm gates (2026-08-11; scoped claims still matter)

The current scoped `battle_integration_map` and `rhython_grade_to_result` rows are real evidence
for the owner seams above. This section remains intentionally stricter about a new player-input,
restart, or packaged claim: those proofs cannot be inferred from the scoped rows.

The `runtime` completion gate (rhythm→damage delta, campaign
`Docs/ECHO/campaign_01_rhythm_damage_delta.md`) was reported "certified" with none of the
following in place. Inherit the standard, not the claim:

1. **A gate is certified only when `record_gate.py <id> pass` has a ledger row.** The Echo
   contract already says this; on 2026-08-10 a "rhythm gate runtime-certified" claim was made
   while `Saved/gate_ledger.json` had no row for it and `Saved/Echo/state.txt` still showed
   `runtime` OPEN. Prose in a session log is not a ledger row.
2. **Probe-injected calls are not play evidence.** Calling
   `subsystem.register_lane_hit()` / `controller.use_skill()` from Python proves the native
   seam responds when invoked — it does NOT prove a player pressing Q/W/O/P sees a highway.
   The campaign's acceptance requires real keyboard input through `BP_BattleUI::OnKeyDown`
   (or a documented `InputKey` injection path into the focused widget). A probe-only green
   run is a HOLD, and the campaign doc's record command must not be run from it.
3. **Frames without a report are not evidence.** PNG captures with no accompanying JSON
   (state assertions, damage numbers, error counts) and no committed verifier cannot be
   re-checked. Save the assertion report next to the frames, and keep the harness that
   produced both.
4. **The committed harness must be the harness that ran.** The 2026-08-10 probe committed
   at `Content/Python/rhythm_battle_runtime_probe.py` crashed on entry
   (`skill_class` referenced from `start_petal_cadence` but only defined inside
   `prepare_petal_cadence`), so the claimed "certified" runs used a driver that was never
   committed. Unreproducible evidence is unusable — fix the probe, then rerun.
5. **The HUD is shared, and the owning lane clears.** `UMelodiaRhythmHUDWidget` is driven by
   both the ambient `UMelodiaBattleSession`/execution-component sync lane and the stock
   `UMelodiaRhythmCombatSubsystem::PushHighwayToHUD`. The ambient lane must only clear a
   highway it set (`bExecutionDrivingHighway`); an unconditional
   `SetNoteHighwayActive(false, …)` every tick erased the other integration's notes one
   frame after they were pushed. Same family as sibling-graph drift — two writers on one
   surface with no ownership.

### The defect classes these exist for

Every one of these reached main and survived review, because the thing that was wrong
looked correct in every graph read:

- **Shadowed events.** A child Blueprint re-declares a parent's custom event with an empty
  body. The child's version replaces the parent's in the generated class, so callers hit a
  stub. `BP_MelodiaBattleUI` had ten, including `ShowBattleUI` — which is why the battle UI
  never appeared. Compiles clean, fingerprints clean, smoke-tests clean.
- **Unreachable graphs.** `BP_BattleUI` had a live exec chain nothing constructed. A lane
  remap landed on a component only an unconfigured GameMode adds.
- **Sibling-graph drift.** `OnKeyDown` was remapped to Q/W/O/P while `OnKeyUp` stayed on
  D/F/J/K, so lanes latched lit. A fingerprint covers one graph; contracts span several.
- **Duplicate short names.** Substring assertions pass against either copy. There are
  currently two `BP_BattleUI` and a 33-asset mirror at
  `Content/MelodiaIntegration/Content_MelodiaIntegration/`.
- **Silent no-op.** Travel via allowlist, `StartSession` on an unregistered skill, and an
  unallowlisted Quill id all fail by returning nothing.

### Specs, injection recipes, CI gates, Monolith action tables

Full reference (toon profiles, Niagara MPC, inject snippets, `ci_gates.json`, Monolith
blueprint/material/editor/project/niagara actions):
[`Docs/Production/T3D_MONOLITH_REFERENCE.md`](Docs/Production/T3D_MONOLITH_REFERENCE.md).

---

Read this file before changing gameplay integration.
