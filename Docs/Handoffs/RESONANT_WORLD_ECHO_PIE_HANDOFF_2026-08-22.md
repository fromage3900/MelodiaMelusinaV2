# Resonant World Echo / PIE Handoff

Date: 2026-08-22
Scope: persistent Melodia Resonant World movement and asset-constellation proof
Repository: `C:\EnvironmentPortfolio\BS_GodFile`

## Decision at handoff

The offline/read-model side is available, but the Resonant World runtime gate is **HOLD**. The current Unreal Editor process exists, while the Monolith endpoint on `127.0.0.1:9316` is unresponsive. `Saved/Logs/BS_GodFile_2.log` records a blocking `MODAL_OPEN` at `2026-08-22T03:21:16` (line 3350) followed by HTTP socket-send failures (lines 3385 and 3390). `python -B Tools/echo_run.py status --topo` therefore reports `editor reachable on 9316: no (editor gates HOLD)`.

Do not record a PIE, runtime, movement, asset-injection, or promotion PASS until the modal is dismissed, Monolith health is restored, and a fresh owner-controlled PIE run produces linked evidence.

## Authority map

Use the following sources in this order:

1. `specs/echo_pipeline.json` — Echo stages, editor holds, completion/quality gates, and the no-automatic-ledger-write contract.
2. `specs/echo_topo.json` — predecessor graph and promotion eligibility.
3. `Saved/gate_ledger.json` — authoritative gate rows and latest status. `Saved/gate_ledger_report.md` and `Saved/Echo/state.txt` are derived summaries and may be stale.
4. `specs/p0/core_p0_dream_golden_run.v1.json` — owner-controlled golden-run contract and forbidden shortcuts.
5. `specs/schemas/evidence_envelope.v1.json` — canonical evidence-envelope schema.
6. `Saved/Logs/MonolithCalls.jsonl` and `Saved/Logs/BS_GodFile_2.log` — live-call and Editor/Monolith diagnostics.
7. Resonant World artifacts under `Saved/Audit/`, with a new evidence envelope linking every runtime claim to its fresh report, frames, and logs.

The First Dream golden-run contract is the authority template for owner/PID/fresh-slot/restart evidence. Its integration proof map is not a substitute for the player route, and historical envelopes are context only.

## Exact runnable commands

Run from `C:\EnvironmentPortfolio\BS_GodFile`. Commands below are documented for the next owner run; this audit did not launch a write-producing PIE or ledger run.

### Read-only Echo and topology checks

```powershell
python -B Tools/echo_run.py list
python -B Tools/echo_run.py status --topo
python -B Tools/echo_topo.py eligible --json
python -B Tools/echo_topo.py order
```

The parser-correct wrapper form for promotion checks is:

```powershell
python -B Tools/echo_run.py topo check-promote --gate ch2_environment.env_promote
```

The direct processor form is:

```powershell
python -B Tools/echo_topo.py check-promote ch2_environment.env_promote
```

Some older Echo docs show the gate ID positionally after `check-promote`; use `--gate` with `echo_run.py`.

### Offline Resonant World preparation and validation

The deterministic constellation builder is an offline semantic binding read model. It must not be called proof of loaded UAssets, applied PCG, or PIE behavior.

```powershell
python -B Content/Python/resonant_world_asset_constellation.py --seed 3900 --movement petal_cantata --chunk-x 0 --chunk-y 0 --archetype SakuraDreamer --output Saved/Audit/resonant_world_constellation_petal_3900.json
python -B Content/Python/resonant_world_asset_constellation.py --seed 3900 --all-movements --output Saved/Audit/resonant_world_constellation_portfolio_3900.json
python -B Content/Python/resonant_world_score.py --seed 3900 --movement petal_cantata --chunk-x 0 --chunk-y 0 --archetype SakuraDreamer
python -B Tools/evidence_envelope.py validate Saved/Audit/<envelope>.json
python -m pytest -q Content/Python/test_resonant_world_asset_constellation.py
python -B Tools/test_melodia_mcp.py
```

The lookdev evidence bridge is also read-only and must remain separate from
runtime proof:

```powershell
python -B Content/Python/resonant_world_capture_manifest.py --seed 3900 --output Saved/Audit/resonant_world_capture_manifest_3900.json
'{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"melodia_resonant_world_get_capture_manifest","arguments":{"seed":3900,"movement_id":"all","chunk_x":0,"chunk_y":0}}}' | python -B deploy/melodia_mcp_server.py
```

This manifest binds the four requested lookdev slots to score/constellation
IDs, absolute source assets, intended camera/material state, and observed PNG
verdicts. It does not render, copy, publish, or approve a frame.

The current stdio MCP surface is read-only and can be exercised without Editor/Monolith. The constellation surface is now registered, policy-covered, and included in the offline MCP contract suite:

```powershell
'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"melodia_resonant_world_get_constellation","arguments":{"seed":3900,"movement_id":"petal_cantata","chunk_x":0,"chunk_y":0,"archetype_id":"SakuraDreamer"}}}' | python -B deploy/melodia_mcp_server.py
```

For the complete six-movement portfolio:

```powershell
'{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"melodia_resonant_world_get_constellation","arguments":{"seed":3900,"movement_id":"all"}}}' | python -B deploy/melodia_mcp_server.py
```

The score read model is available through the same offline MCP boundary:

```powershell
'{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"melodia_resonant_world_get_score","arguments":{"seed":3900,"movement_id":"petal_cantata","chunk_x":0,"chunk_y":0,"archetype_id":"SakuraDreamer"}}}' | python -B deploy/melodia_mcp_server.py
```

These calls establish stable IDs, role bindings, coverage, quantum-candidate
selection, call/response score events, seam endpoints, and materialization
state. They do not close `music_world_key`, `wardrobe_gameplay_hook`, or any
PIE gate.

### Editor-backed static and runtime gates

After restoring one healthy Monolith owner, run the smallest relevant checks first:

```powershell
python -B Tools/echo_run.py run static_gates
python -B Tools/echo_run.py run pie_smoke
python -B Tools/echo_run.py run runtime_gates
python -B Tools/regression_suite.py --quick
```

`runtime_gates` runs the PIE smoke, regression, and Blueprint fingerprint checks. Echo does not write the ledger automatically. Review all output and artifacts before recording anything.

The generic PIE smoke command for the Resonant proof map is:

```powershell
python -B Tools/pie_smoke_runner.py --map "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_ScaleWorldProof" --duration 20 --output "Saved/Audit/ResonantWorld/PIE_20260822_resonant_scale_world" --console-script WalkLoop --name resonant_world_scale_world_smoke --sample-vars GroundSpeed bShouldMove bIsMoving
```

The report must be `ok=true`, with clean lifecycle, no active `must_absent` hits, no missing `must_present` checks, and linked frames/samples/log matches. The current runner is generic; the Resonant-specific assertions below still require explicit Monolith/editor readback or an extended harness.

The battle-oriented harness is useful only for its stated First Dream scope:

```powershell
python -B Tools/playtest_harness.py preflight
python -B Tools/playtest_harness.py check-wiring
python -B Tools/playtest_harness.py run --map L_KaleidoNave --backend auto
```

Its probe backend is not formal real-input evidence and it cannot, by itself, prove a Resonant World constellation.

For the full Unreal automation suite, close every `UnrealEditor.exe` first. `UnrealEditor-Cmd.exe` cannot provide a second Monolith owner while the Editor is open:

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" `
  "C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" `
  -ExecCmds="Automation RunTests Melodia; Quit" `
  -unattended -nop4 -nullrhi -nosplash -nosound -log -stdout
```

Use `Automation RunTests Melodia` for the full suite; `Melodia.Integration` is only the narrower integration subset.

### Evidence envelope and ledger recording

Create/validate an envelope that links the fresh PIE report, captures, logs, and offline inputs before recording a gate. The canonical helper syntax is:

```powershell
python -B Tools/evidence_envelope.py create `
  --kind runtime `
  --status pass `
  --producer "Tools/pie_smoke_runner.py" `
  --check-name "resonant_world_constellation_pie" `
  --check-status pass `
  --gate-id music_world_key `
  --artifact "Saved/Audit/ResonantWorld/PIE_20260822_resonant_scale_world/resonant_world_scale_world_smoke_report.json" `
  --output "Saved/Audit/ResonantWorld/PIE_20260822_resonant_scale_world/resonant_world_constellation_runtime_envelope.json"
python -B Tools/evidence_envelope.py validate Saved/Audit/ResonantWorld/PIE_20260822_resonant_scale_world/resonant_world_constellation_runtime_envelope.json
```

Only after review of the fresh envelope and all linked artifacts:

```powershell
python -B Tools/echo_run.py record music_world_key pass --note "Fresh proof-map PIE envelope: <path>; movement=<id>; constellation=<id>; report=<path>; frames=<path>"
python -B Tools/echo_run.py record wardrobe_gameplay_hook pass --note "Fresh PIE envelope proves form selection, canonical traversal request, and no capability grant: <path>"
python -B Tools/echo_run.py record wardrobe_equip_roundtrip pass --note "Fresh owner-controlled save/load and re-entry evidence: <path>"
```

For topology-layer records, use the agreed layer/lane IDs from `specs/echo_topo.json` and do not use a generic PASS to hide a missing Resonant-specific check. Never record a PASS while the Editor is unavailable or while an envelope has `hold`/`fail` checks.

## Required Resonant World gate contract

Treat one movement/asset constellation as a single chain. A later stage cannot promote an earlier offline claim into runtime proof.

| Stage | Required proof | Gate disposition |
|---|---|---|
| Author / resolve | `constellation.ok=true`; stable seed + movement + chunk identity; exact movement/motif; required role coverage; no quarantined binding; real asset refs classified; exactly two quantum candidates; persisted backend/baseline/trace | Candidate for `ch2_environment.env_asset_author`; not runtime proof |
| Compose / voice | `score.ok=true`; 16-beat call/response; four beat stages; shared seam endpoints; event-level music/material/ornament/VFX/wardrobe refs; replay key; quantum selector boundary | Evidence attached to `ch2_environment.env_asset_author`; not runtime proof |
| Apply / compile | One Editor writer; healthy Monolith; additive proof map only; validated PCG plan applied; `editor_apply.performed=true`; hero graphs, data layers, and HLOD rules read back; 0 compile errors | Candidate for `ch2_environment.env_asset_inject`; HOLD if apply remains false |
| PIE / observe | Proof map loads; expected 9 chunks / 5 hero inputs and selected movement appear; no seam/cross-chunk failure; captured movement and samples; beat stages `Invocation → Unfolding → Threshold → Release`; UI is event-driven; wardrobe form routes through canonical traversal; no duplicate reward/save | Candidate for `music_world_key` and `wardrobe_gameplay_hook`; requires fresh runtime envelope |
| Persist / replay | Fresh slot, owner/PID/map/run ID, save boundary, process restart, Continue/re-entry, same constellation identity and idempotent result; no historical envelope substitution | Candidate for `wardrobe_equip_roundtrip`, `save_load`, and `repeat_consume` only when the run proves those behaviors |
| Promote | All predecessor rows PASS; evidence paths are present and valid; `echo_topo.py check-promote` is PASS/eligible | Only then promote the environment/project node |

The PIE evidence must explicitly assert:

- the movement ID and constellation ID selected by the run;
- the loaded proof-map path `/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_ScaleWorldProof`;
- the five hero graphs and nine generated chunks expected by the proof handoff;
- gameplay data layer versus static architecture/biome dressing separation and HLOD exclusion of gameplay data;
- the movement phrase driving the existing passage/stage bridge, with `OnStageChanged` observed on the music-clock beat rather than frame polling;
- Sakura/wardrobe form selection as presentation/voicing, not a new save or capability authority;
- the canonical `UMelodiaTraversalComponent` request path and one canonical notification/reward path;
- no second save authority, duplicate reward, or duplicate HUD writer;
- captured frames, event/log evidence, and a reproducible fresh-slot/restart boundary.

## Audited evidence and current findings

Current authoritative or relevant paths:

- `Saved/Audit/resonant_world_asset_atlas.json` — present and `ok=true`; a large reference atlas. It proves discovered/logical references, not loaded, compiled, streamed, or performance-tested UAssets.
- `Saved/Audit/resonant_world_pcg_plan_3900.json` — present and `ok=true`; nine chunks, five hero inputs/volumes, and 162 static specs. It says `editor_apply.required=true` and `performed=false`.
- `Saved/Audit/resonant_world_proof_handoff_3900.json` — present and `ok=true`; same proof-map contract, with `editor_apply.performed=false` and no production maps touched.
- `Saved/Audit/resonant_movement_rank_3900.json` — present; requested `qsharp-simulator`, but actual backend is `classical-baseline`, with `qsharp_available=false`. Persist and replay the recorded winner/baseline/trace; make no quantum-advantage claim.
- `Saved/Audit/resonant_world_phrase_128bpm.json`, `Saved/Audit/resonant_wardrobe_voicing_sakura_3900.json`, and `Saved/Audit/resonant_magic_passage_petal_3900.json` — offline design/read-model inputs, not PIE proof.
- `Saved/Audit/resonant_world_capture_manifest_3900.json` — read-only lookdev contract for the four canonical PNG slots; current clean-approved count is zero. The exact SakuraDream candidate `Saved/Screenshots/Monolith/LookdevLane3/L_Render_SakuraDream_beauty_raw.png` is rejected after black/checker frames and post-marker `Error`/`Ensure` matches. Do not route it to webfront.
- `Saved/Audit/resonant_world_asset_constellation_petal_3900.json` — absent at audit time. The builder’s documented output is `Saved/Audit/resonant_world_constellation_petal_3900.json`; generate a fresh, validated artifact when the next owner run begins.
- `Saved/Evidence/{package_id}/chapter_golden_run.json` — required by the content-package template but `Saved/Evidence` and this artifact are absent. No chapter golden-run claim is closed.
- `Saved/gate_ledger.json` — latest ledger authority. Existing `runtime`, `save_load`, `repeat_consume`, and `package_launch` rows are historical First Dream/gameplay evidence; the latest `static_gates` row is FAIL. Current Resonant-relevant completion gates including `music_world_key`, `wardrobe_gameplay_hook`, and `wardrobe_equip_roundtrip` are OPEN.
- `Saved/Audit/PIE_Verify_20260812_155813/` and `Saved/Playtest/PLAYTEST_1786564931_report.json` — historical only: the latter is probe-only with empty damage deltas and explicitly is not formal ledger packaging; the old run also recorded a missing `L_KaleidoNave` load and missing legacy `BP_BattleUI` wiring.
- `Saved/RegressionReports/` and `Saved/Screenshots/` — expected output locations for a new regression run; no historical report should be reused as current Resonant proof.

The current Echo topology has no Resonant-specific nodes for constellation identity, binding coverage, proof-map application, chunk seams, passage-stage events, or wardrobe/traversal semantics. Generic `ch2_environment` gates can organize the work, but they cannot be marked from atlas/read-model output alone.

## Explicit gaps and owner actions

1. **Editor/Monolith unavailable:** dismiss the modal in the single owner Editor, then verify `/health`, `monolith_status`, and one read-only editor query before any PIE. Do not launch another Editor or `UnrealEditor-Cmd` concurrently.
2. **Proof map not applied:** the PCG plan and proof handoff both say `editor_apply.performed=false`. Apply only to the additive proof map and capture readback before `env_asset_inject` can pass.
3. **No fresh golden-run evidence:** create the required owner/PID/fresh-slot/restart envelope under `Saved/Evidence/{package_id}/` and link it to the Resonant PIE envelope. The existing First Dream spec must not be shortened to an integration-map-only run.
4. **PIE harness coverage gap:** `pie_smoke_runner.py` checks lifecycle/log/must-present/must-absent behavior but does not currently assert Resonant constellation IDs, PCG chunk seams, data-layer/HLOD routing, passage stage events, canonical traversal, or duplicate-save/reward behavior. Add those checks in the responsible gameplay/test lane before calling the generic report sufficient.
5. **MCP/read-model boundary:** `melodia_resonant_world_get_atlas`, `melodia_resonant_world_get_constellation`, `melodia_resonant_world_compile_passage`, `melodia_resonant_world_get_handoff`, and `melodia_resonant_world_validate` are offline/read-only surfaces. They do not load/spawn/apply runtime state or run PIE. Registry/schema/policy alignment and the offline constellation call are now covered by `Tools/test_melodia_mcp.py`.
6. **Asset promotion:** the atlas contains logical manifest references that still need promoted asset/load/compile/readback evidence. Water/material promotion and PIE remain open.
7. **Quantum backend:** Q# is unavailable in the audited environment; the classical baseline is the honest current result. Persisted ranking is useful for deterministic replay, not a proof of quantum execution.
8. **Existing gate drift:** Echo does not auto-write ledger rows, and `Tools/record_gate.py` does not enforce all predecessor checks at record time. Always run the topology check separately and use `Saved/gate_ledger.json` as authority.

## Handoff completion criterion

This handoff is complete only when a fresh run has: a validated constellation envelope; `editor_apply.performed=true`; a healthy single-owner Monolith; a clean Resonant proof-map PIE report with movement/asset/event assertions; saved frames/logs and a restart/re-entry record; valid evidence envelopes; and explicit ledger rows whose promotion predecessors are satisfied. Until then, the Resonant World movement/asset constellation remains **HOLD**, regardless of offline atlas, MCP, or historical First Dream PASS rows.
