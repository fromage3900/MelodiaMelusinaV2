# BS_GodFile agent context

**Front-door review:** 2026-09-22 against `main` at `9445bcbd6caf87de233118d48af63b6e0299959c` (post #283).

## STATUS — one document

[`CURRENT_STATE.md`](CURRENT_STATE.md) is the only status document: what works (with evidence level), what is open, the owner queue, repositories, workstations, and recurring traps. If any other file in this repo states project status, it is stale — fix `CURRENT_STATE.md`, not that file. Do not create handoff, plan, receipt, or session-note files. Pre-collapse docs: `git show 7d271c15:<path>` (tag `docs-precollapse-2026-09-10`).

## BINDING RULES — every agent (Hermes, Codex, Claude, subagents)

Hermes loads this file, not `CLAUDE.md`, so the binding rules are repeated here. **Read
[`CLAUDE.md`](CLAUDE.md) in full before acting**; where the two differ, `CLAUDE.md` wins.

- **Git pipeline law.** `origin/main` is canonical. No branch, commit, merge, rebase, reset or push
  without explicit owner permission for that operation plus a written plan stated first. Never
  `reset --hard`, `checkout -- .`, `clean`, force-push or rewrite history. Workers produce patches in
  a worktree; the owner approves every git/p4 operation.
  **Storage architecture (2026-10-01).** Git carries code/docs/plans; Perforce carries bulk binary
  (`Content/`, dropped plugins, `Reference/`). **The Perforce server root is `D:\perforce\root` on
  this machine, so a p4 submit is history-tracked, NOT off-machine — GitHub is the only offsite
  copy.** Never call a p4 submit a backup. Full picture:
  [`STORAGE_ARCHITECTURE_2026-10-01.md`](Docs/Production/STORAGE_ARCHITECTURE_2026-10-01.md).
  **KNOWN ISSUE (pre-dates 2026-10-01): this file is ~46 KB against a 32 KB agent-context budget
  and is being served trimmed. Trim it, or move detail into linked docs.**
  **Standing authorization (2026-09-30).** Requiring permission for *every* commit is what produced a
  permanently dirty tree, unpushable local commits sitting on `main`, and two agents moving `HEAD`
  under each other. That is settled now: work in a lane
  ([`Docs/Production/MULTI_AGENT_LANES.md`](Docs/Production/MULTI_AGENT_LANES.md)) — committing inside
  your **own** lane needs no permission, and the integrator landing a lane needs no permission. Do not
  ask. Explicit owner permission is still required for anything that can lose work: `reset --hard`,
  `checkout -- .`, `clean`, force-push, history rewrite, deleting a branch or ref, and any p4 submit.
- **Agents do not create branches (2026-09-30).** A lane pins its work with `refs/agents/<lane>` — a
  ref, not a branch — so it never appears in `git branch` and never accumulates.
  `deploy/new_agent_lane.ps1` creates the lane worktree on a detached HEAD plus that ref. The
  integrator creates one temporary branch per landing and deletes it in the same run. The
  "create a new single-purpose branch" step in the next rule applies to the **integrator and the
  owner**, not to workers.
- **Disposable branch law.** Never resume, reopen, or push new work to a closed/superseded feature branch. Before owner-approved branch creation, fetch current `origin/main` and create a new single-purpose branch from that tip. If a lane is more than 8 commits behind `origin/main`, stop feature work: preserve the bounded intended delta, reconverge it onto a fresh branch from current main, verify the effective diff, and retire the stale lane. Do not merge a stale lane forward merely to keep it alive. `feature/spout-beauty-2026-09-26` is permanently retired.
- **Portable G: workspace law.** `G:` is an owner-controlled portable SSD and may contain the **complete runnable Melodia project**, not merely a backup or archive. When `G:` is mounted and contains a valid Melodia checkout/project root, inspect and use that root before cloning or reconstructing another workspace on `C:`. The SSD may be carried between home and Humber and used directly for Unreal/Blender/Houdini work when the host machine permits it. Git, Git LFS, and Perforce remain synchronization/version-history layers; they are not prerequisites for opening or working from a complete portable project copy. Do not describe `G:` as archive-only, backup-only, or a disposable mirror unless the owner explicitly says that specific copy is archival. Scripts and instructions should remain repo-root-relative so the project can run from `G:` or another authorized drive letter without path rewrites.
- **Never touch** `.gitignore`, `.gitattributes`, `Config/DefaultEngine.ini`, `Config/DefaultGame.ini`,
  `Content/Materials/MF_MeshBlend_*`, `deploy/run_verify.ps1`. Ask before any `Config/` or
  `Content/Materials/` edit. `L_SakuraPath` / `L_MelusinaMorning` changes are ask-first.
- **One editor, one mutating surface.** Never run two MCP surfaces (Claireon, Monolith, …) against the
  editor at once. `MelodiaIntegrationMap` is the cluttered test level: never tidy it, never
  `load_level` away from it uninvited; PIE stop → immediate `load_level` crashes the editor.
  Save approved editor work immediately. Never bulk `load_asset` (use Asset Registry tags).
- **Delegated output is not evidence.** Open the artifact (image, log, JSON) yourself before claiming
  a result. A subagent once reported a "smooth" SDF bake that was scattered dots.
- **Orchestration & Model Tier Discipline.** Hermes runs long jobs, Jev routes, Claude verifies — the one plan is
  [`.hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md`](.hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md).
  Extend it; do not start a parallel orchestration/router/lease framework. Model tiers are governed by
  [`Docs/Production/MODEL_ROUTING_CANON.md`](Docs/Production/MODEL_ROUTING_CANON.md) and
  [`specs/orchestration/model_tiers.v1.json`](specs/orchestration/model_tiers.v1.json). Before dispatching or spending
  frontier calls, query `python Tools/model_router.py tier <task>`; lower-tier bulk work must not burn frontier tokens,
  and local/bulk tiers must not alter `Source/**`, schemas, or contracts. Parallel repo work = jcode swarm
  under `.jcode/swarm-prompt.md` (one worktree per worker, patches only, no editor access).
- **Do the job asked** (`_AGENT_WORKING_AGREEMENT.md`): the request is the scope; queue work comes
  from `CURRENT_STATE.md` §4, not from new audits.

**Historical branch guard:** PR #201 is resolved/superseded by merged #213; PR #230 was closed unmerged. `cleanup/pbr-twin-landing-2026-09-10` is provenance only — never use it as a current health proxy or wholesale merge source.


## Production-tool front door — READ BEFORE CHOOSING A NEW FRAMEWORK

The canonical workflow router is [`Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md`](Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md).

Use it to select the existing lane before writing code:

- **worldbuilding:** recipe -> `Tools/world_compiler.py` -> existing UE driver; no second compiler or scatter framework;
- **Houdini:** deterministic Hython tools under `Tools/Houdini/` forge source assets/data; they do not own runtime world state;
- **Rokoko/Melusina mocap:** Blender retarget/root-motion FBX -> guarded `Content/Python/import_rokoko_mocap_batch.py` -> existing animation owner;
- **UE C++:** JetBrains Rider is the preferred navigation/debug/test surface; follow [`Docs/Production/RIDER_UE58_CANONICAL_WORKFLOW.md`](Docs/Production/RIDER_UE58_CANONICAL_WORKFLOW.md);
- **RiderLink:** always-available focused live-editor automation bridge for native tests; use it before inventing a custom test harness when a single-editor session is the right proof surface;
- **Qodana:** always-available static-analysis gate through tracked `qodana.yaml` (`ide: QDJB`); run it as a normal native/shader quality layer, not an optional experiment;
- **Jev:** always-available canonical judgment/orchestration service for bounded authored choices and next-action selection; follow [`Docs/Production/JEV_CANONICAL_WORKFLOW.md`](Docs/Production/JEV_CANONICAL_WORKFLOW.md). Jev chooses/directs; existing owners execute;
- **editor mutation:** one Unreal Editor, one Monolith writer, inspect -> mutate -> assert -> save;
- **status:** only `CURRENT_STATE.md` may declare what is currently proven/open.

If an old research/handoff file suggests creating a parallel implementation, the current front door wins unless a fresh blocker is demonstrated.

## ⛔ WORKING AGREEMENT — outranks everything below in this file

See [`_AGENT_WORKING_AGREEMENT.md`](_AGENT_WORKING_AGREEMENT.md) — binding. Do the job asked, ship it, stop; never compensate, kill means delete; owner's statements are ground truth; fix ≠ review.

---

## Skills created 2026-08-30

| Skill | Purpose |
|-------|---------|
| `melodia-daemon-monitor` | Diagnose and repair failing cron jobs (provider misconfig, HTTP 402, null provider) |
| `melodia-mesh-catalog` | Catalog static meshes, find duplicates, propose reorganization (read-only) |
| `melodia-cathedral-builder` | Recursive overnight evolution loop — wool modes, weight lab, cathedral geometry |

## Ollama daemon lane

Qwen3 8B is pulled and available for local daemon work. `Tools/model_router.py` daemon lane is functional with `qwen3:8b` as primary researcher and `qwen3-coder:30b` for code/audit tasks. Daemons using this lane produce reports in `Saved/Daemon/proposals/` for human review.

## Toolchain discovery — read first before any emerging-toolchain / render / audio work

> **Read [`CURRENT_STATE.md`](CURRENT_STATE.md) → `PROVEN CREATIVE CAPABILITY SURFACE` first.** It is the
> live status authority and tells you which affordances are live-proven, source/tool-proven, or scaffolded.
> Then use [`Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md`](Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md)
> as the detailed inventory for SpeedTree, Houdini/Copernicus, PCG, cymatics, audio reactivity and external tools.
> The index is a reference inventory, not a second status authority. Extend PRESENT lanes, finish SCAFFOLDED
> lanes with evidence, and never promote research-only or external work as live.

## Core vision - the stable core is for authored content

> **THE CORE WORKS. DEFAULT TO AUTHORING CONTENT WITH IT. EXTEND SYSTEMS ONLY WHEN A REAL CONTENT BLOCKER REQUIRES IT.**

Melodia is an authored rhythm-JRPG with a working gameplay core and a growing procedural/lookdev
production surface. The current scoped owner seam is:

```text
Quill encounter intent -> Phoenix / TurnBased JRPG selected action -> rhythm execution
  -> typed terminal result -> Quill resumes exactly once -> consequence / reward / checkpoint
```

Use the exact evidence levels in `CURRENT_STATE.md`. The scoped battle and grade-to-damage seams
are live-proven; a fresh packaged golden run and the long-chain persistence proof are separate
open gates, not reasons to reopen the owners.

### Owner-directed runtime migration — 2026-10-01

Today's gameplay-engineering direction is **playable proof before canonization**. Do not dismiss FLOW/SEQUENCE work as stale merely because the stable map is still JRPG-first, and do not declare it canonical merely because a prototype exists.

- **FLOW** means continuous world play on the canonical `BP_MelusinaJRPGCharacter`: traversal, dodge, aim/draw/release, WaveHarp and realtime encounter interaction.
- **SEQUENCE** means a deliberate authored musical-time state that uses the existing Melodia rhythm execution and then returns to FLOW.
- Both modes must share **one encounter identity, one HP owner, one damage/effect authority, one rhythm grader and one durable narrative outcome path**.
- Recover recent local/P4/runtime work first. Prefer one visible end-to-end playable interaction over broad architecture work.
- PR #367 is reference/provenance only. Never merge, rebase, revive or wholesale cherry-pick it.
- ACFU remains R&D unless the owner explicitly promotes it after a convincing runtime proof.
- Choral Sheep remains the non-combat capstone lane and must not be coupled to the combat migration.
- If runtime proof shows the stable owner map is genuinely wrong for the desired game, report the smallest owner-boundary change required; do not silently fork the authority.

The first promotion proof should be approximately: canonical Melusina → real FLOW input → WaveHarp/action hit → authoritative resolved damage → same world target/HP → readable feedback → continued movement. Add FLOW → SEQUENCE → FLOW only after FLOW itself is real.

## Default decision rule - author content before changing architecture

Before changing architecture, ask:

> Can the requested experience be authored using the systems listed in
> `CURRENT_STATE.md` -> `PROVEN CREATIVE CAPABILITY SURFACE`?

If yes, author the content. Do not alter architecture. A boss, side quest, rhythm skill, cymatic
biome, wardrobe ability, and procedural setpiece are normally content/data authored through the
existing seams. Architecture work requires a demonstrated blocker recorded against the relevant
owner seam.

The surface already supports authoring boss battles, rhythm skills/attacks, side quests, encounters,
creature episodes, outfit abilities, and musical world puzzles without another gameplay framework.

The integrated rhythm-JRPG loop remains the **production authority spine until the owner-directed FLOW/SEQUENCE promotion gate passes**:

**Stable ownership - never rebuilt, wrapped, or competed with:**
- **QuillScript** is the narrative authoring authority. `UMelodiaNarrativeSubsystem` is the runtime
  bridge and owns authored narrative facts, consequences, checkpoints, and exactly-once progression
  transactions; it does not resolve stock combat.
- **TurnBased JRPG / Phoenix** owns party, turns, targeting, skills, action resolution, damage,
  inventory, terminal battle results, and stock gameplay save state.
- **Rhythm** executes on the selected JRPG action. Grade may affect the authoritative result, but
  rhythm does not create a second combat transaction or damage authority.
- **Wardrobe** owns owned/equipped fashion state and exposes the existing traversal, battle, rhythm,
  and Convergence capability hooks.
- **One writer per UI/audio surface.** `UMelodiaUIBridgeSubsystem` owns the Melodia UI surface;
  `UMelodiaAudioReactivePresentationSubsystem` owns the canonical audio palette. Cymatics reads
  that palette and its dedicated driver contract; it does not become a second audio writer.
- **MelodiaCore** is an integration/presentation layer, not a competing combat or save authority.
  ACFU and Conversation2D remain excluded.

**The four pillars converge onto those two layers.** Rhythm input rides *on top of* JRPG command
input - same Attack/Skill/Item/Flee decisions, timed. Wardrobe is a core pillar (outfits carry
presentation *and* gameplay meaning). UI has one writer per surface. World puzzle is music-as-key
and its Piano-to-Narrative edge has a scoped live-proven world-unlock path. Deeper route/package
proof remains separately tracked in `CURRENT_STATE.md`.

Shape: OMORI. Music-as-key: Zelda. Visual/wardrobe bar: Infinity Nikki.

Status and scope: [`CURRENT_STATE.md`](CURRENT_STATE.md).

**Model lanes:** pick a task class before writing (`triage|audit|code|cpp|mcp|playtest|author|
deep|review|orchestrator|vision|daemon|docs`, plus the production lanes `wardrobe_catalog|
beatmap_author|quill_author|asset_qa|anim_bindings|spout_beauty`). Router: `python Tools/model_router.py pick
<class> --detail`. Policy + local daemon models: [`Docs/Production/MODEL_LANES_2026-08-12.md`](Docs/Production/MODEL_LANES_2026-08-12.md).
Gameplay queue: [`CURRENT_STATE.md`](CURRENT_STATE.md) §4. The handoff files this line used to point
at were removed in the 2026-09-10 docs collapse.

| Class | Use for | Must not |
|---|---|---|
| `cpp` | MelodiaIntegration C++ | Rebuild JRPG in MelodiaCore |
| `mcp` | Monolith multi-step (one editor) | Second MCP surface on same graph |
| `playtest` | Real-input `runtime` gate | Probe-only ledger `pass` |
| `daemon` | Overnight local loops (Ollama) | `.uasset` writes / gate certification |
| `audit` | bp_sweep / static gates | Compensating flags for real defects |
| `wardrobe_catalog` | Outfit rows against the catalog contract | Invent slots or bypass `MelodiaWardrobeSubsystem` |
| `beatmap_author` | Rhythm beat maps | Make rhythm a second combat authority |
| `quill_author` | QuillScript dialogue + 7-verb notifications | Emit an unallowlisted id |
| `asset_qa` | art/credits/bp gates, triage | Fabricate a file path |
| `anim_bindings` | ABP state machine + pose binding checks | Write `.uasset` |
| `spout_beauty` | Live UE→TD lookdev via the canon Spout2 `UE_Beauty` sender | Second sender name / second beauty writer |

**Every lane must not:** build a fifth wardrobe track, a fourth rhythm path, a second HUD
writer, or a second beauty-feed sender. Converge onto the named owner. A new parallel implementation is a defect, not progress.

**UI/visual-artist work:** load `.claude/skills/melodia-ui-artist/SKILL.md` (the equivalent
`.agents/skills/melodia-ui-artist/SKILL.md` is also present) — it carries the
real token SSOT (`melodia-design-system/tokens.json`), the Quill dialogue WBP chain
(`Content/Melodia/UI/Quill/`, tracked), the `ui_style_audit.py` inventory flow, and the
editor-driven apply workflow. Do not hand-edit `.uasset`; `Content/Melodia/UI/Textures/` is
intentionally gitignored, do not track it.

---

## 🚀 Rider & UE 5.8 Engineering Protocols

Canonical runbook: [`Docs/Production/RIDER_UE58_CANONICAL_WORKFLOW.md`](Docs/Production/RIDER_UE58_CANONICAL_WORKFLOW.md).

Use Rider to **find the real owner, make a smaller native change, run the right build, and prove it in Unreal**.

Core rules:
- use Unreal-aware Find Usages / reflected-asset navigation before adding a competing API;
- close Unreal and run a real `BS_GodFileEditor Win64 Development` build for reflected declarations, modules, Build.cs, generated headers, shader-directory registration, and load-topology changes;
- RiderLink is the default focused live-editor test bridge for suitable native automation; its availability is canonical, not opportunistic;
- Qodana via the tracked `qodana.yaml` / `QDJB` profile is the canonical static-analysis quality gate for native/shader work;
- RiderLink/Qodana evidence does not replace restart, PIE-input or packaged acceptance when those are required;
- use the native debugger and Unreal Insights on the existing owner seam before redesigning for performance;
- edit tracked `.usf/.ush` in Rider, but UE shader compilation + visible capture is the runtime proof;
- do not rewrite World Compiler, Rokoko ingestion, Blueprint ownership, or editor automation in C++ simply because Rider makes C++ convenient.

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

- QuillScript is the narrative authoring authority: dialogue, choices, encounter intent, and authored
  consequence content use the allowlisted Quill contract.
- `UMelodiaNarrativeSubsystem` is the runtime Quill bridge and the owner of authored narrative facts,
  checkpoints, consequences, and exactly-once reward/progression transactions; it does not resolve
  stock combat.
- TurnBased JRPG / Phoenix owns party, turns, skills, targets, action resolution, damage, inventory,
  terminal battle results, and canonical stock gameplay saves.
- Rhythm executes on the selected JRPG action and returns grade/performance data to that authority;
  it is not a second combat path.
- `UMelodiaWardrobeSubsystem` owns owned/equipped fashion state and its existing gameplay capability
  hooks. `MelodiaTraversalComponent` owns traversal behavior.
- `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter` is the canonical exploration
  heroine and the **Ultimate** designation; keep its name and the existing locomotion/Rokoko
  authority. `/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation` remains a separate
  battle-presentation role. Universe Foundry authors content for existing runtime contracts; do not
  create another pawn, animation controller, pawn-owned Foundry manager, or Niagara framework.
  Use [`SYSTEM_MAP.md` → Melusina runtime system diagram](SYSTEM_MAP.md#melusina-runtime-system-diagram)
  as the canonical visual owner map and `Docs/P1_TASK_LEDGER.json` → `melusina_work` for scoped
  work gates. See `CURRENT_STATE.md` for the full Blueprint inventory and current evidence tiers.
- One writer owns each UI/audio surface. Extend the existing UI bridge, audio-reactive palette,
  cymatic driver, and Niagara/flipbook consumers instead of introducing parallel writers.
- MelodiaCore remains presentation/integration-only; ACFU and Conversation2D are excluded.

## Project-owned paths

- C++ bridge: `Source/BS_GodFile/MelodiaIntegration/`
- Allowlist: `/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig`
- Integration GameInstance: `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance`
- Integration GameMode: `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode`
- Integration PlayerController: `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGPlayerController`
- Integration map: `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`
- Save record field: `melodiaNarrativeRecord` on `/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGSaveGame`
- QuillScript plugin: `Plugins/QuillScript/`
- Beauty-feed plugin: `Plugins/UE5_Spout2_DX12/` (Spout2_DX12 v2.1.1, re-clone per machine — `Binaries/` is gitignored)
- Beauty render target: `/Game/Melodia/Lookdev/RT_UE_Beauty` (1920×1080, RGBA8)
- Beauty sender actor: `/Game/Melodia/Lookdev/BP_UE_BeautySender` (droppable; SceneCapture → RT; Spout sender name `UE_Beauty`, the single reserved name — never embed in a production map, never invent a second name)

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
5. Use the filesystem backup at `CompatibilityLabs/ProductionPreIntegrationBackup_2026-07-26` for rollback — the working tree is ~151 GB of largely-unversioned art and a `git clean -fd` or `checkout -- .` would destroy it permanently; the git object store itself is healthy (verified by `git fsck --full` in 2026-08-28).
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

25. **Cron jobs sharing the same `workdir` lock each other out.** Two daemons with `workdir: C:\EnvironmentPortfolio\BS_GodFile` will deadlock on the TERMINAL_CWD write lock — the second job times out after 660s with `TimeoutError`. Fix: remove `workdir` from the job config (use absolute paths in prompts) or stagger schedules so they never overlap.

26. **`Saved/Audit/*.json` commits are allowed.** Daemon-produced specs and audit reports in `Saved/Audit/` are explicitly allowlisted in `.githooks/pre-commit` (line 68: `grep -Ev '^Saved/Audit/.*\.(json|md)\$'`). They do not need owner sign-off to commit.

## 5. jcode Swarm (parallel coding lane)

Primary **repo-side** parallel coding uses [jcode](https://jcode.sh) light-swarm on the Windows UE workstation — not `deploy/cursor_*_loop.ps1` wake ticks.

*   **Policy:** [`.jcode/swarm-prompt.md`](.jcode/swarm-prompt.md) — PGA/MPA/PPA/WIA/SQA/WEB/MUSE spawn scopes, concurrency cap 6, no recursive worker spawning.
*   **Bootstrap:** `.\deploy\start_jcode_swarm.ps1` then paste [`.jcode/coordinator-bootstrap.md`](.jcode/coordinator-bootstrap.md).
*   **MCP:** [`.jcode/mcp.json`](.jcode/mcp.json) → Monolith stdio proxy (`Plugins/Monolith/Scripts/monolith_proxy.bat`); requires Unreal open for editor tools.
*   **Skills:** `.\deploy\install_jcode_melodia_skills.ps1` installs Monolith skills into `%USERPROFILE%\.jcode\skills\`.
*   **Companion IDE lanes:** OpenCode in Rider (C++/PIE) via [`.opencode/opencode.jsonc`](.opencode/opencode.jsonc) + `.\deploy\start_opencode_muse_lane.ps1`; Muse Code (WSL) via [`Docs/Production/MUSE_CODE_LANE_2026-08-11.md`](Docs/Production/MUSE_CODE_LANE_2026-08-11.md).
*   **Keep running:** surreal/world/`run_verify` production loops.
*   **Deprecated for parallel coding wakes:** `deploy/cursor_*_loop.ps1` (left in tree; do not start for new work).
*   **Phone/Cursor cloud agents** remain the PR / mobile lane; do not overlap write paths with a live local swarm without coordination.

Full guide: [Docs/PhoneOps/JCODE_SWARM_PIPELINE.md](Docs/PhoneOps/JCODE_SWARM_PIPELINE.md) · [`.jcode/README.md`](.jcode/README.md)
