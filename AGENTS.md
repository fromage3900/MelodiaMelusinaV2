# BS_GodFile agent context

## ⛔ WORKING AGREEMENT — outranks everything below in this file

See [`_AGENT_WORKING_AGREEMENT.md`](_AGENT_WORKING_AGREEMENT.md) — binding. Do the job asked, ship it, stop; never compensate, kill means delete; owner's statements are ground truth; fix ≠ review.

---

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

### Evidence standard — runtime/rhythm gates (2026-08-11)

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

### Declarative Spec Format

#### Toon Profile Spec (`specs/toon_profiles/tp_melusina.json`)
```json
{
  "asset_path": "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina",
  "class": "ToonProfile",
  "settings": {
    "DiffuseIndirectScale": 0.3,
    "SpecularIndirectScale": 0.3,
    "ShadowExtinctionCoefficient": 0.3,
    "DiffuseRamp": [
      {"time": 0.0, "color": {"r": 0.034, "g": 0.022, "b": 0.047, "a": 1.0}},
      {"time": 0.3, "color": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}},
      {"time": 1.0, "color": {"r": 1.08, "g": 1.04, "b": 0.98, "a": 1.0}}
    ],
    "SpecularRamp": [
      {"time": 0.9, "color": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}}
    ],
    "ShadowHatchingPattern": "/Game/EnvSandbox/Materials/ToonProfiles/T_HatchPattern",
    "ShadowingExtinction": 0.3
  }
}
```

#### Niagara MPC Binding (`specs/niagara_mpc_bindings.json`)
```json
{
  "NS_Uni_WaterMist": {
    "WaterMist": {
      "emitter_update": {
        "ProximityDriver": {
          "type": "ModuleScript",
          "source": "MPC_ScalarParameterCollection = Engine.MaterialParameterCollection'/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette';\nfloat Proximity = MPC_ScalarParameterCollection.GetScalarParameterValue('PlayerProximity');\nProximitySpawnRateMultiplier = 1.0 + (1.0 - Proximity) * 4.0;"
        }
      }
    }
  }
}
```

### Injection Workflow

#### Blueprint Graph Injection
```python
# 1. Load spec
spec = json.load(open("specs/toon_profiles/tp_melusina.json"))

# 2. Inject via Monolith
monolith("blueprint_query", {"action": "build_blueprint_from_spec", "spec": spec})

# 3. Compile & verify
monolith("blueprint_query", {"action": "compile_blueprint", "asset_path": spec["asset_path"]})

# 4. Fingerprint & assert
monolith("blueprint_query", {"action": "get_graph_fingerprint", "asset_path": spec["asset_path"]})
monolith("blueprint_query", {"action": "assert_graph_matches", "asset_path": spec["asset_path"], "expected_fingerprint": "..."})
```

#### Material Curve Injection (Toon Profiles, MPCs)
```python
from t3d_material_curve_injector import T3DMaterialCurveInjector

inj = T3DMaterialCurveInjector()

# Apply full toon profile spec (curves + scalars + textures in one pass)
result = inj.apply_toon_profile_spec(spec)

# Or individual operations:
inj.set_scalar_parameter(asset_path, "DiffuseIndirectScale", 0.3)
inj.set_color_parameter(asset_path, "SomeColor", {"r": 1.0, "g": 0.5, "b": 0.0, "a": 1.0})
inj.write_curve_to_asset(asset_path, "DiffuseRamp", curve_points)
inj.compile_and_verify(asset_path)

# CLI mode:
# python Tools/t3d_material_curve_injector.py --spec specs/toon_profiles/tp_melusina.json
# python Tools/t3d_material_curve_injector.py --asset <path> --set-scalar Brightness=0.5
# python Tools/t3d_material_curve_injector.py --asset <path> --read-curve DiffuseRamp
```

### CI/CD Pipeline (`.github/workflows/melodia_ci.yml`)
```yaml
name: Melodia CI
on: [push, pull_request]
jobs:
  verify:
    runs-on: windows-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - name: Start Monolith
        run: |
          Start-Process "Plugins/Monolith/Binaries/monolith_proxy.exe" -WorkingDirectory "BS_GodFile"
          Start-Sleep 15
      - name: Verify Blueprints
        run: python Tools/bp_regression_checker.py --all
      - name: Run Continuous Loop
        run: python Tools/continuous_loop.py --max-failures 0
      - name: Run Regression Suite
        run: python Tools/regression_suite.py --full
      - name: PIE Smoke Test
        run: python Tools/pie_smoke_runner.py --smoke
```

### Quality Gates (from `ci_gates.json`)
```json
{
  "graph_fingerprint": "exact_match",
  "blueprint_compile": "0_errors",
  "material_compile": "0_errors", 
  "shader_instructions": "max_150",
  "triangle_budget": "max_250k",
  "pie_smoke": "0_crashes",
  "animation_delta": "threshold_0.05",
  "accessibility": "pass"
}
```

### Monolith MCP Commands Reference

#### Blueprint
| Action | Purpose |
|--------|---------|
| `blueprint_query:build_blueprint_from_spec` | Inject T3D spec in single transaction |
| `blueprint_query:compile_blueprint` | Compile Blueprint |
| `blueprint_query:get_graph_fingerprint` | Topology fingerprint |
| `blueprint_query:assert_graph_matches` | Verify no unintended rewire |
| `blueprint_query:get_cdo_properties` | Read CDO property values |

#### Material (63 actions)
| Action | Purpose |
|--------|---------|
| `material_query:set_instance_parameter` | Set scalar/vector/texture on material instance |
| `material_query:set_instance_parameters` | Batch-set, single recompile |
| `material_query:get_instance_parameters` | Read all overrides from instance |
| `material_query:recompile_material` | Force material recompile |
| `material_query:get_compilation_stats` | VS/PS instruction counts, compile status |
| `material_query:build_material_graph` | Build material graph from JSON spec |
| `material_query:get_material_properties` | Read material settings (blend, shading, etc.) |
| `material_query:validate_material` | Check for broken connections, unused nodes |
| `material_query:get_all_expressions` | List all expression nodes |
| `material_query:export_material_graph` | Serialize graph to JSON |
| `material_query:import_material_graph` | Import graph from JSON |
| `material_query:begin_transaction` | Start undo group |
| `material_query:end_transaction` | End undo group |

#### Editor
| Action | Purpose |
|--------|---------|
| `editor_query:run_python` | Run headless Python scripts |
| `editor_query:trigger_build` | Trigger full C++ build |
| `editor_query:run_pie_smoke` | Headless PIE smoke test |

#### Project
| Action | Purpose |
|--------|---------|
| `project_query:export_asset_text` | Export asset as T3D text (universal escape hatch) |
| `project_query:search` | Find assets by name/type |
| `project_query:get_asset_details` | Get indexed asset metadata |

#### Niagara
| Action | Purpose |
|--------|---------|
| `niagara_query:add_module` | Add ModuleScript to Niagara |

---

Read this file before changing gameplay integration.

## Current phase

Production JRPG + QuillScript integration in UE 5.8. The target loop is:

`QuillScript dialogue -> allowlisted encounter request -> JRPG battle with Melusina -> typed result -> QuillScript resumes once -> exploration`

The loop is not yet fully proven. Do not report completion until the runtime, save/load, repeat-callback, and Development-package gates are recorded.

## Quantum usage

Use quantum computing only as an asynchronous decision service for narrow, measurable gameplay problems.

Approved uses:

- ranking authored rhythm or encounter patterns
- choosing among candidate room/layout seeds
- route, puzzle, or reward selection under constraints
- offline experimentation that compares quantum vs classical baselines

Do not use quantum code for frame-by-frame combat, input timing, or any gameplay loop that must stay deterministic at frame rate. The rhythm system should keep classical hit detection and grading in UE; quantum may only select or rank the authored pattern set before play begins.

Implementation rules:

1. Keep the UE request/response contract small and JSON-based.
2. Run the quantum solve step in Python or a service boundary, not inside Blueprint tick.
3. Keep a classical fallback path so the workflow still functions before the quantum backend is enabled.
4. Preserve the contract in `Docs/Handoffs/QUANTUM_GAMEPLAY_EXPERIMENT_PROTO_2026-08-06.md` when replacing the backend with a real Q# target.
5. For rhythm gameplay, use the quantum result to pick pattern density, lane arrangement, accent placement, or tempo band; do not use it to decide whether a hit is perfect/great/good/miss.

## Ownership

- JRPG template owns party, turns, skills, damage, quests, inventory, battle transitions, battle results, and canonical saves.
- `UMelodiaNarrativeSubsystem` owns only the narrow narrative-to-JRPG bridge and versioned narrative record.
- QuillScript supplies authored narrative and stable notifications only.
- MelodiaCore assets are presentation-only in this phase.
- ACFU and Conversation2D are excluded.

## Project-owned paths

- C++ bridge: `Source/BS_GodFile/MelodiaIntegration/`
- Allowlist: `/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig`
- Integration GameInstance: `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance`
- Integration GameMode: `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode`
- Integration PlayerController: `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGPlayerController`
- Integration map: `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`
- Save record field: `melodiaNarrativeRecord` on `/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGSaveGame`
- QuillScript plugin: `Plugins/QuillScript/`

## Stable notification contract

The subsystem recognizes only these seven verbs (`UMelodiaNarrativeSubsystem::HandleQuillNotification`
dispatch table, `MelodiaNarrativeSubsystem.cpp`):

- `melodia:battle:<EncounterId>`
- `melodia:quest:<QuestId>`
- `melodia:flag:<FlagId>:<true|false>`
- `melodia:travel:<LevelId>`
- `melodia:reward:<RewardId>`
- `melodia:stat:<IntentId>:<StatId>:<Delta>`
- `melodia:item:give:<ItemId>:<Count>`

`melodia:stat:` is idempotent per `<IntentId>`, not per `<StatId>`: the intent id is recorded in
`FMelodiaNarrativeRecord::ConsumedIntentIds` (SaveGame), so replaying the same authored beat after a
Quill resume or a save reload is a no-op. Two different beats may both award the same stat.

`melodia:item:` is a **logging stub** — it validates arity and count and writes
`MELUSINA_LOOP_ITEM_GRANT`, then stops. There is no inventory/wallet consumer. Do not author content
that depends on it granting anything.

Current allowlisted IDs are documented in `Docs/MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md` (§ "Initial allowlist"); the live authority is `DA_MelodiaIntegrationConfig -> TravelLevelIds`. Do not add identifiers casually.

## ⛔ NEVER RUN THESE — they destroy unrecoverable work

On 2026-08-08 an agent ran `git checkout -- .` and started `git clean -fd` on this project
while trying to undo a bad FBX import. The `clean` was interrupted before it deleted
anything. **That interruption is the only reason the project still has its protagonist.**

| Command | Why it is catastrophic here |
|---|---|
| `git clean -fd` / `-fdx` | Bulk `Content/` is **untracked** (commit `f89fccd5` stopped tracking it). `clean` deletes untracked files. It would permanently erase every character, mesh, material and animation in the project. There is no LFS copy to restore from. |
| `git checkout -- .` | Reverts every modified tracked file to HEAD, including work in progress from other agents and sessions. Uncommitted edits are **not** in the object store, so `reflog` and `fsck` cannot bring them back. It silently destroyed five Python files this way. |
| `delete_asset` on anything you did not create | Tells the running engine to forget an object. The registry then reports the asset as valid on disk while `load_asset` returns False, which looks exactly like file corruption and is not. It cost hours of misdiagnosis. |
| FBX import into a path that already holds an asset | Creates a redirector over the existing asset. Rolling it back by deleting the folder leaves a dead redirector pointing at nothing. |

If you believe one of these is the right move: **stop and ask the owner.** There is no
situation in this project where an agent should run a destructive git command unprompted.

### Python + skill Blueprints = instant editor death (2026-08-08)

**Never touch anything under `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` from Python.**
Calling `load_blueprint_class()` / `get_default_object()` on a skill Blueprint forces UE to
generate Python glue for the user-defined enum `D_DamageType`, which fails **fatally**:

```
Fatal error: PyWrapperTypeRegistry.cpp:2641
Failed to generate Python glue code for enum
  '/Game/TurnBasedJRPGTemplate/Blueprints/Skills/D_DamageType.D_DamageType'
```

This is not recoverable and not a warning — the editor dies immediately, taking every
unsaved package with it. It will happen to any agent that inspects a skill, every time.

**Use Monolith's native path instead.** `blueprint_query` is C++, not Python, so
`get_cdo_properties`, `get_graph_data` and `export_graph` all read skill Blueprints safely.
Only the `editor_query run_python` route is dangerous here.

Root cause is unfixed: `D_DamageType` is a Blueprint user-defined enum whose enumerators
cannot be wrapped — usually a duplicate display name, a name that is not a valid Python
identifier, or a reserved word. Fixing the enum removes the landmine.

### If an asset "disappears", check this order before concluding anything

1. Is the file on disk? (`Get-ChildItem -Recurse Content -Filter "<name>.uasset"`)
2. Does the registry still see it? Force a rescan:
   `ar.scan_paths_synchronous([folder], force_rescan=True)` — a `delete_asset` in this
   session hides an asset that is perfectly intact on disk.
3. Compare `does_asset_exist` / `find_asset_data` against `load_asset`. Valid metadata plus
   a failed load means **in-session state, not file damage** — restart the editor.
4. Check for a redirector: the canonical path may resolve elsewhere. `unreal.load_package`
   returns the package it actually resolved to, which is how the two Melusina paths were
   found.
5. Only then look for backups. This project has `Saved/Recovery/`,
   `CompatibilityLabs/`, and per-asset `_OLD` variants in place.

**Never delete or overwrite a candidate backup while diagnosing.** Copy everything
plausible to a folder outside `Content/` first.

## Safe working rules

1. Check `list_errored_blueprints` and dirty packages before editing.
2. Do not save existing portfolio/Melodia maps or unrelated materials.
3. Duplicate before changing template assets.
4. Prefer one small, verifiable change per session.
5. Use the filesystem backup at `CompatibilityLabs/ProductionPreIntegrationBackup_2026-07-26` for rollback; Git object storage is damaged.
6. Static graph inspection is not runtime proof.
7. **One editor instance. Always.** On 2026-08-08 three ran concurrently on this project:
   five crash reports in one hour, assets changing mid-edit, and 39 unsaved packages lost to
   a forced kill. Check `Get-Process UnrealEditor` and that port 9316 has exactly one
   listener before any editor work. Decision 025 forbids two MCP surfaces on one graph; this
   is the same hazard one level up.
8. **`MODAL_OPEN` in the log is not a hang.** A modal dialog blocks the game thread, so
   Monolith goes silent and Windows reports "Not Responding". Grep for it before concluding
   the editor is dead — killing it there costs every unsaved package for nothing. An FBX
   import dialog caused exactly this today.
9. **Verify by re-reading.** `success: true` only means nothing threw. `save_asset` returned
   inconclusive at least once; confirm via `list_dirty_packages`.
10. **Search both name forms.** `UnitHasEnoughMP` vs `Unit Has Enough MP` — node instance
    titles are spaced. A substring search on the identifier form missed a live macro and
    produced a confidently wrong "this macro is never called" conclusion.
11. **`ORPHAN` means prove it, not delete it.** `bp_live_path` cannot see `TSoftObjectPtr`
    (Decision 049) or `.umap` actor references (Decisions 020/029d/037a).
12. **A committed export is an output, not an input.** Verifiers here re-derive from the
    live graph every run; do not add a script that asserts against a stored export. The one
    exception is `bp_regression_checker.py`, whose baseline is therefore tracked at
    `Docs/T3D_Baseline/bp_fingerprints.json` and hard-fails when missing.
13. **A variable-reference census misses expose-on-spawn pins.** `find_variable_references`
    counts `K2Node_VariableSet` nodes only. On 2026-08-09 this produced a confident
    "`BP_BattleUI::battleController` has 4 reads and 0 writes" — false: `K2Node_CreateWidget`
    writes it through an expose-on-spawn input pin. Before declaring a property unwritten,
    check CreateWidget/SpawnActor nodes that construct the object.
14. **Verify the editor lock directly; never trust a report of it.** Attempt a write-open on
    `Binaries/Win64/UnrealEditor-BS_GodFile.dll`. Twice on 2026-08-09 a lane reported the DLL
    locked when it was writable, and the real blocker was a compile error that would have
    failed the build the moment anyone tried. A "blocked on the editor" claim from another
    lane is a hypothesis, not a fact.
15. **Live Coding cannot introduce new imports.** `.cpp`-only edits hot-patch fine
    (`editor_query live_compile`). The moment a change calls a symbol the compiled binary
    never imported, it fails with no useful message in the editor log. Any header change —
    new class, new `UFUNCTION`, new `UPROPERTY` — always needs a full closed-editor build.
16. **Do not hand-build engine data structures.** A runtime `UMidiFile` carrying only a tempo
    change crashed the editor (`EXCEPTION_ACCESS_VIOLATION` reading `0x4` inside HarmonixMidi)
    because a valid song map also needs `Init(ticksPerQuarter)` and a **bar map**. Copy the
    engine's own construction path — `UMusicClockComponent::MakeDefaultSongMap()` — or use a
    properly imported asset. Guarding around a malformed structure is the wrong fix.
17. **Parallelise research, never the editor.** Six read-only explorer agents ran concurrently
    on 2026-08-09 with no incident because none touched the editor. Source/C++ work also
    parallelises — it builds while the editor is closed. All editor work (PIE, CDO edits, T3D,
    graph reads) must serialise through one holder. Another MCP server does not help; Monolith
    runs in-process, so a second surface is a second writer on the same lock.
18. **The allowlist does NOT fail closed in editor builds.** `bRelaxedAllowlistInEditor = true`
    on `DA_MelodiaIntegrationConfig` lets unregistered narrative ids pass with a warning in
    every non-shipping build; it fails closed only in `UE_BUILD_SHIPPING`. An authored typo
    therefore works in PIE and breaks in a packaged demo. Run a verification pass with it off.
19. **`Content/_ThirdParty/TurnBasedJRPGTemplate/` is not a pristine copy** — 156 Blueprints vs
    205/206, missing whole subsystems, and its `BP_BattleController` was edited after copying.
    The trustworthy stock reference is the standalone project at
    `CompatibilityLabs/TurnBasedJRPGUE58`. Copy **node clusters, never whole files**: live
    `BP_BattleUI` is 667KB vs 457KB stock, and that difference is authored rhythm-HUD work.
20. **A dump cannot prove absence.** On 2026-08-09 a full string dump of
    `DA_MelodiaIntegrationConfig` concluded `StockSkillRhythmIds` had "no such property and no
    `MapProperty`", and the whole rhythm investigation was built on that. It had an entry the
    entire time. This is rule 13 generalised: **census and dump methods can confirm presence,
    never absence.** To establish that something is missing, read it through reflection —
    `get_cdo_properties`, not a text search of the asset.
21. **"The build is green" decays into a lie.** Adaptive unity keeps recently-changed files in
    separate translation units, so a tree can build incrementally for days while being
    unbuildable from clean. On 2026-08-10 three of four blockers were unity-build symbol
    collisions (two anonymous-namespace constants, one third-party plugin pair) that only
    appeared on a full rebuild. **Do a full closed-editor build before trusting a green claim,
    and before starting editor work** — discovering it after an hour in the editor wastes the
    session. Fix collisions by qualifying the name or, for vendored plugins, `bUseUnity =
    false` on that module only.
22. **A file existing is not a file compiling.** `MelodiaJRPGPostBattleLibrary.cpp` sat in the
    tree for a day looking like finished work; it had never once compiled — a UE 5.7 include
    path, a typed accessor called on a base `FProperty*`, and `&` of a temporary. Before
    planning around code another lane left behind, **build it**. Note UE 5.8 moved
    `UserDefinedStruct.h` from `Engine/` to CoreUObject's `StructUtils/`.
23. **Check Monolith's own namespace before declaring something impossible.** Moving actors
    between levels is `mesh_query manage_sublevel {sub_action: "move_actors"}`. On 2026-08-10 an
    agent burned an hour on `EditorLevelUtils` (both variants demand a `LevelStreaming`
    destination, so neither can target the persistent level) and `ACTOR COPY`/`ACTOR PASTE`
    (no-ops headlessly, via both the Python console and `run_console_command`), then wrote
    "cannot be automated" into a handoff — with the correct action sitting in a `monolith_discover`
    result already in context. **1330 actions across 24 namespaces: search the list before
    concluding a capability is absent.** Related trap: `manage_sublevel` takes actor *names*,
    not labels, and names repeat across levels (`StaticMeshActor_1`, `PointLight_0`, `PCGVolume_0`
    all exist in more than one). Move unambiguous actors first and verify per-level counts after
    every batch — a silent no-op and a silent wrong-actor move look identical from the return value.
24. **A level actor listing aggregates sublevels.** `get_level_actors` reports actors from
    streaming sublevels alongside the persistent level, which is how "the encounter actor is in
    `L_KaleidoNave`" survived a session — it is in `L_Melodia_Dreamstate`, streamed in. The
    distinction is load-bearing: a sublevel that is not set to load at startup is **absent from
    the PIE world**. Read the `sublevel` field, and confirm at runtime with a tag probe.

## Next work, in order

Full detail: `Docs/Handoffs/CORE_SYSTEMS_HANDOFF_2026-08-10.md`.

1. ~~**Give the song map a beat map.**~~ **DONE 2026-08-11** — `MelodiaMusicClockSubsystem`
   loads the imported `128BPMarpeggiomelody_beatgrid` MIDI (tempo+bar+beat maps validated,
   never hand-built).
2. **Certify the `runtime` gate with formal evidence — owner PIE saw it PLAY; ledger still OPEN.**
   Owner PIE 2026-08-13: after Melusina's unique skill, rhythm highway worked (clunky), damage
   procced, next turn applied on skill finish. That is play evidence; it is **not** a ledger row.
   Still owed: (a) Decision 024 A/B on `melodia.Rhythm.Disable 1`, (b) assertion report JSON
   next to frames from the committed harness, (c) `record_gate.py runtime pass|fail`. Probe-only
   Python hits remain non-evidence.
3. ~~**Build and verify the highway-ownership fix.**~~ **Owner PIE 2026-08-13 observed a working
   highway** after Melusina unique. If clunk/wipe recurs, confirm `bExecutionDrivingHighway` is
   in the running binary (closed-editor build) before redesigning feel.
4. **Verify the damage-scalar sequencing** before trusting any A/B numbers — the damage notify
   may fire ~2.5s before the scalar latches. Owner saw damage proc; A/B delta still unrecorded.
5. **Highway note rendering / feel** — clunk reported in owner PIE; genuine T3D target for note
   presentation. Re-export baselines and resolve `unresolved_member_parent` first.
6. ~~Wire a call site for `RestorePartyAfterBattle`.~~ **DONE on `main` via #6** (`6715d51`) —
   `BP_BattleController` lookup path. Confirm `MELODIA_RECOVERY` log in a battle-end PIE.
7. Re-run `python Tools/bp_sweep.py` project-wide. It died mid-run during the three-editor
   incident; scoped runs are clean.
8. Damage progression smoothing — owner has a recorded contact sheet. Ask for it; do not
   guess at the curve, and do not add a multiplier that cancels out a bad one.
9. Resolve the duplicate content trees (two `BP_BattleUI`, the 33-asset mirror). Owner
   sign-off before deleting — the mirror is untracked and unrecoverable.

Done 2026-08-09/10: Sir rescue trigger (A4); `StockSkillRhythmIds` populated;
`BP_BattleController` placed in `L_KaleidoNave`; `L_Melodia_Dreamstate` merged into
`L_KaleidoNave` and deleted (allowlist stripped; backup in `Saved/Recovery/`).
Done 2026-08-11: beat map; `rhythm_battle_runtime_probe.py` made runnable
(`skill_class` NameError fixed); highway-ownership fix staged in
`MelodiaRhythmHUDWidget`; ledger truth recorded (no rhythm gate row exists —
see evidence standard §1).
Done 2026-08-12/13: #4+#6 on `main`; owner PIE — Melusina unique → highway (clunky) →
damage → next turn on skill finish.

Parallel work for other agents, partitioned by contended resource:
`Docs/Handoffs/PARALLEL_LANES_2026-08-08.md`.

---

## 5. jcode Swarm (parallel coding lane)

Primary **repo-side** parallel coding uses [jcode](https://jcode.sh) light-swarm on the Windows UE workstation — not `deploy/cursor_*_loop.ps1` wake ticks.

*   **Policy:** [`.jcode/swarm-prompt.md`](.jcode/swarm-prompt.md) — PGA/MPA/PPA/WIA/SQA/WEB/MUSE spawn scopes, concurrency cap 6, no recursive worker spawning.
*   **Bootstrap:** `.\deploy\start_jcode_swarm.ps1` then paste [`.jcode/coordinator-bootstrap.md`](.jcode/coordinator-bootstrap.md).
*   **MCP:** [`.jcode/mcp.json`](.jcode/mcp.json) → Monolith stdio proxy (`Plugins/Monolith/Scripts/monolith_proxy.bat`); requires Unreal open for editor tools.
*   **Skills:** `.\deploy\install_jcode_melodia_skills.ps1` installs Monolith skills into `%USERPROFILE%\.jcode\skills\`.
*   **Companion IDE lanes:** OpenCode in Rider (C++/PIE) via [`.opencode/opencode.jsonc`](.opencode/opencode.jsonc) + `.\deploy\start_opencode_muse_lane.ps1`; Muse Code (WSL) via [`Docs/Production/MUSE_CODE_LANE_2026-08-11.md`](Docs/Production/MUSE_CODE_LANE_2026-08-11.md). Tonight prep: [`Docs/Handoffs/TONIGHT_FIRST_DREAM_OPENCODE_2026-08-11.md`](Docs/Handoffs/TONIGHT_FIRST_DREAM_OPENCODE_2026-08-11.md).
*   **Keep running:** surreal/world/`run_verify` production loops.
*   **Deprecated for parallel coding wakes:** `deploy/cursor_*_loop.ps1` (left in tree; do not start for new work).
*   **Phone/Cursor cloud agents** remain the PR / mobile lane; do not overlap write paths with a live local swarm without coordination.

Full guide: [Docs/PhoneOps/JCODE_SWARM_PIPELINE.md](Docs/PhoneOps/JCODE_SWARM_PIPELINE.md) · [`.jcode/README.md`](.jcode/README.md)
