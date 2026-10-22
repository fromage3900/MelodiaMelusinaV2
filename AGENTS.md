# BS_GodFile agent context

**Front-door review:** 2026-10-21, P0 canon landed on `refs/agents/canon-full-french-20261021`.

## STATUS — one document

[`CURRENT_STATE.md`](CURRENT_STATE.md) is the only status document: what works (with evidence level), what is open, the owner queue, repositories, workstations, and recurring traps. If any other file in this repo states project status, it is stale — fix `CURRENT_STATE.md`, not that file. Do not create handoff, plan, receipt, or session-note files. Pre-collapse docs: `git show 7d271c15:<path>` (tag `docs-precollapse-2026-09-10`).

## ⚑ WORLD IDENTITY + P0 ROUTE CANON — 2026-10-21

**Creative north star: [`Docs/MELODIA_MELUSINA_WORLD_IDENTITY_CANON_2026-10-20.md`](Docs/MELODIA_MELUSINA_WORLD_IDENTITY_CANON_2026-10-20.md)** (v0.2, tracked). One line: *a French cathedral-world where architecture is music and water remembers — the living legend of Mélusina, made into a place you can walk.* Tone words: **sunlit, reverent, grieving**. It governs feeling, look and mythos — not status (`CURRENT_STATE.md`), not UI (`Docs/DESIGN_SYSTEM.md`), not the build (`Docs/Production/MELUSINA_FINAL_ENVIRONMENT_CONVERGENCE_GOAL.md`).

**One governing meter, both docs defer to it:** grid **0.6 m** = 1 beat, bar/bay **2.4 m** = 1 bar of 4/4, **128 BPM 4/4** (beat 0.469 s, bar 1.875 s, walk 1.28 m/s). The older "2.4 m = allegro 3/4 / 3.6 m = andante 4/4" phrasing is superseded everywhere.

**The P0 route is the Poitou P0 Golden Walk, M00-M09** - an 8-12 min exploration-led opening (target 10:00): bedroom -> house -> village -> canal -> departure. Authority `Docs/Plans/POITOU_P0_GOLDEN_WALK_2026-10-21.md`; machine form `specs/p0/poitou_p0_golden_walk.v1.json`. **Two proofs, not one:** this experience P0, and the separate integration P0 `specs/p0/core_p0_dream_golden_run.v1.json` (Morning -> KaleidoNave -> encounter -> save/restart), which must stay intact. Every M00-M09 beat is `PROPOSED`. **Live level is `/Game/EnvSandbox/Poitou/L_Poitou_v2`**; `L_MelusinaMorning` is a 37 KB shell and the house leg's ownership is an open owner decision. **Zen Forest is NOT core canon.** No combat beat in the walk - that does *not* change the hybrid canon below; the four ownership questions remain unratified (`CURRENT_STATE.md` "OWNER CANON").

## ⚑ MELUSINA RUNTIME RIG + RETARGET CANON — 2026-10-05

**Read [`Docs/Production/MELUSINA_RUNTIME_CANON_2026-10-05.md`](Docs/Production/MELUSINA_RUNTIME_CANON_2026-10-05.md) before any retarget, animation or rig work.** It supersedes older rig/retarget docs.

- **Raw retarget output into `SK_Melusina_Skeleton` is known-defective — never ship it.** Every retarget needs the canon arm correction, then verification: `15.774 | 28.561 | 28.615` (world cm, `shoulder→arm_stretch→forearm_stretch→hand`). Reject `34.789 | 9.520 | 28.615` — that is the reference-pose interruption.
- Her rig is **not mannequin**: `shoulder_l → arm_stretch_l → forearm_stretch_l → hand_l`; legs `thigh_stretch_l → leg_stretch_l → foot_l → toes_01_l`; **no `pelvis`**, **no `ik_foot_l/r`**.
- The `UpperBody` slot feeds a **layered blend** — its branch mask must carry the 11 spine+arm filters or draw/cast montages are silently blended away.
- **Caster/archer hybrid is intentional**: LMB = caster + floating astrolabe; RMB = Sparrow charged draw/hold/fire. Preserve it.
- `batch_retarget_animations` + `overwrite=true` **crashes the editor**. Never pass it.
- **Open:** the six owner-approved SparrowArchery clips still carry the arm defect (frozen — owner decision).

## BINDING RULES — every agent (Hermes, Codex, Claude, subagents)

Hermes loads this file, not `CLAUDE.md`, so the binding rules are repeated here. **Read [`CLAUDE.md`](CLAUDE.md) in full before acting.** `_AGENT_WORKING_AGREEMENT.md` outranks every agent doc. For Git, storage, branch/lane, and integration policy, this file plus the linked current production contracts are canonical; `CLAUDE.md` may add Claude-specific execution notes but must not override a newer repo-wide contract.

- **Git pipeline law.** `origin/main` is canonical and is a landing target, never an agent workspace.
  Workers use detached lane worktrees pinned by `refs/agents/<lane>` and do not push/open PRs themselves. Commits inside a worker's own lane and normal integrator landing are covered by the standing authorization below. Explicit owner approval is still required for destructive history/worktree operations, deleting refs/branches, force-push/history rewrite, and any Perforce submit.
  **Storage architecture (2026-10-01).** Git carries code/docs/plans; Perforce carries bulk binary (`Content/`, dropped plugins, `Reference/`). **The Perforce server root is `D:\perforce\root` on this machine, so a p4 submit is history-tracked, NOT off-machine — GitHub is the only offsite copy.** Never call a p4 submit a backup. Full picture: [`STORAGE_ARCHITECTURE_2026-10-01.md`](docs/Production/STORAGE_ARCHITECTURE_2026-10-01.md). Casing matters: the October 1 records live under lowercase `docs/`; the repo also has an uppercase `Docs/` tree. Do not case-move either tree on Windows.
  **Keep this file under 32,768 bytes; oversized agent context may be truncated.**
  **Standing authorization (2026-09-30).** Requiring permission for *every* commit is what produced a
  permanently dirty tree, unpushable local commits on `main`, and two agents moving `HEAD` under each other. That is settled now: work in a lane ([`Docs/Production/MULTI_AGENT_LANES.md`](Docs/Production/MULTI_AGENT_LANES.md)) — committing inside your **own** lane needs no permission, and the integrator landing a lane needs no permission. Do not ask. Explicit owner permission is still required for anything that can lose work: `reset --hard`, `checkout -- .`, `clean`, force-push, history rewrite, deleting a branch or ref, and any p4 submit.
- **Agents do not create branches (2026-09-30).** A lane pins its work with `refs/agents/<lane>` — a
  ref, not a branch — so it never appears in `git branch` and never accumulates. `deploy/new_agent_lane.ps1` creates the lane worktree on a detached HEAD plus that ref. The integrator creates one temporary branch per landing and deletes it in the same run. That branch-creation step applies to the **integrator and owner**, not workers.
- **Disposable branch law.** Never resume, reopen, or push new work to a closed/superseded feature branch. Before owner-approved branch creation, fetch current `origin/main` and branch from that tip. If a lane is >8 commits behind `origin/main`, stop feature work: preserve the bounded delta, reconverge it onto a fresh branch from current main, verify the effective diff, retire the stale lane. Do not merge a stale lane forward just to keep it alive. `feature/spout-beauty-2026-09-26` is permanently retired; PR #201 was resolved by #213, #230 was closed unmerged, and `cleanup/pbr-twin-landing-2026-09-10` is provenance only - never a health proxy or merge source.
- **Portable G: workspace law.** `G:` is an owner-controlled portable SSD and may contain the **complete runnable Melodia project**, not merely a backup or archive. When `G:` is mounted with a valid Melodia checkout/project root, inspect and use that root before cloning or reconstructing a workspace on `C:`. The SSD may be carried between home and Humber and used directly for Unreal/Blender/Houdini work when the host permits. Git, Git LFS and Perforce are synchronization/version-history layers, not prerequisites for working from a complete portable copy. Do not describe `G:` as archive-only or a disposable mirror unless the owner says that copy is archival. Scripts stay repo-root-relative so the project runs from `G:` or any authorized drive letter without path rewrites.
- **Never touch** `.gitignore`, `.gitattributes`, `Config/DefaultEngine.ini`, `Config/DefaultGame.ini`,
  `Content/Materials/MF_MeshBlend_*`, `deploy/run_verify.ps1`. Ask before any `Config/` or `Content/Materials/` edit. `L_SakuraPath` / `L_MelusinaMorning` / `L_Poitou_v2` changes are ask-first (Poitou is the live level since 2026-10-21).
- **One editor, one mutating surface.** Never run two MCP surfaces (Claireon, Monolith, …) against the
  editor at once. `MelodiaIntegrationMap` is the cluttered test level: never tidy it, never `load_level` away from it uninvited; PIE stop → immediate `load_level` crashes the editor. Save approved editor work immediately. Never bulk `load_asset` (use Asset Registry tags).
- **Delegated output is not evidence.** Open the artifact (image, log, JSON) yourself before claiming
  a result. A subagent once reported a "smooth" SDF bake that was scattered dots.
- **Orchestration & Model Tier Discipline.** Hermes runs long jobs, Jev routes, Claude verifies; the plan is [`.hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md`](.hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md). Extend it; do not start a parallel orchestration/router/lease framework. Model tiers are governed by [`MODEL_ROUTING_CANON.md`](Docs/Production/MODEL_ROUTING_CANON.md) and [`model_tiers.v1.json`](specs/orchestration/model_tiers.v1.json). Before spending frontier calls, query `python Tools/model_router.py tier <task>`; lower-tier bulk work must not burn frontier tokens, and local/bulk tiers must not alter `Source/**`, schemas, or contracts. Parallel repo work = jcode swarm under `.jcode/swarm-prompt.md` (one worktree per worker, patches only, no editor access).
- **Do the job asked** (`_AGENT_WORKING_AGREEMENT.md`): the request is the scope; queue work comes
  from `CURRENT_STATE.md` §4, not from new audits.



## Production-tool front door — READ BEFORE CHOOSING A NEW FRAMEWORK

The canonical workflow router is [`Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md`](Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md).

Use it to select the existing lane before writing code:

- **worldbuilding:** recipe -> `Tools/world_compiler.py` -> existing UE driver. **Houdini:** deterministic Hython tools under `Tools/Houdini/` forge source assets/data; they do not own runtime world state. No second compiler or scatter framework.
- **Rokoko/Melusina mocap:** Blender retarget/root-motion FBX -> guarded `Content/Python/import_rokoko_mocap_batch.py` -> existing animation owner.
- **UE C++:** JetBrains Rider is the preferred navigation/debug/test surface ([`RIDER_UE58_CANONICAL_WORKFLOW.md`](Docs/Production/RIDER_UE58_CANONICAL_WORKFLOW.md)). **RiderLink:** the always-available focused live-editor automation bridge for native tests - use it before inventing a custom harness. **Qodana:** the always-available static-analysis gate via tracked `qodana.yaml` (`ide: QDJB`), run as a normal quality layer.
- **Jev:** canonical judgment/orchestration service for bounded authored choices ([`JEV_CANONICAL_WORKFLOW.md`](Docs/Production/JEV_CANONICAL_WORKFLOW.md)). Jev chooses/directs; existing owners execute.
- **editor mutation:** one Unreal Editor, one Monolith writer, inspect -> mutate -> assert -> save. **status:** only `CURRENT_STATE.md` may declare what is proven/open.

If old research suggests a parallel implementation, this front door wins unless a fresh blocker is demonstrated.

## Cymatics-first Melodia canon (binding)

Melodia is fundamentally structured by music, harmony, resonance and cymatic mathematics, not merely decorated with audio-reactive effects. Before suggesting replacements, trace existing MIDI/chord mappings, Harmonic State (`UMelodiaHarmonicStateSubsystem`), Cymatics Subsystem (`UMelodiaCymaticsSubsystem`), World Field Bus (`UWorldFieldBus`), Houdini/PCG producers and runtime consumers. Follow the [World-Building Source of Truth](Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md) and [Audio-Reactive Canon](Docs/Architecture/AUDIO_REACTIVE_CANON.md). Preserve gameplay/save authority and single-writer contracts; do not create a new harmonic engine, World Compiler, model router, documentation authority or redundant subsystem.

## ⛔ WORKING AGREEMENT — outranks everything below in this file

See [`_AGENT_WORKING_AGREEMENT.md`](_AGENT_WORKING_AGREEMENT.md) — binding. Do the job asked, ship it, stop; never compensate, kill means delete; owner's statements are ground truth; fix ≠ review.

---

## Existing skills and local lanes

`melodia-daemon-monitor` (cron repair), `melodia-mesh-catalog` (read-only mesh catalog), `melodia-cathedral-builder` (wool/weight lab). `Tools/model_router.py` routes local daemons through `qwen3:8b` / `qwen3-coder:30b`; daemon proposals need human review.

## Toolchain discovery - emerging-toolchain, render, or audio work

Read [`CURRENT_STATE.md`](CURRENT_STATE.md) for `PROVEN CREATIVE CAPABILITY SURFACE` evidence level, then [`EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md`](Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md) for the SpeedTree, Houdini/PCG, cymatics and audio inventory. Not a status authority: extend PRESENT lanes, prove SCAFFOLDED lanes, never promote research-only work to live.

## Core vision - the stable core is for authored content

> **THE CORE WORKS. DEFAULT TO AUTHORING CONTENT WITH IT. EXTEND SYSTEMS ONLY WHEN A REAL CONTENT BLOCKER REQUIRES IT.**

Melodia is an authored rhythm-JRPG with a working gameplay core and a growing procedural/lookdev production surface. The scoped owner seam is:

`Quill encounter intent -> Phoenix / TurnBased JRPG selected action -> rhythm execution -> typed terminal result -> Quill resumes exactly once -> consequence / reward / checkpoint`

Use the exact evidence levels in `CURRENT_STATE.md`. The scoped battle and grade-to-damage seams are live-proven; a packaged golden run and the long-chain persistence proof are separate open gates, not reasons to reopen the owners.

### Owner-directed runtime migration - 2026-10-01

Gameplay-engineering direction is **playable proof before canonization**. Do not dismiss FLOW/SEQUENCE work as stale because the stable map is still JRPG-first, and do not declare it canonical because a prototype exists. FLOW/SEQUENCE are defined in **Hybrid combat canon** below.

- Recover recent local/P4/runtime work first; prefer one visible end-to-end playable interaction over broad architecture work. PR #367 is reference/provenance only - never merge, rebase, revive or wholesale cherry-pick it.
- Choral Sheep remains the non-combat capstone lane and must not be coupled to the combat migration.
- If runtime proof shows the stable owner map is genuinely wrong for the desired game, report the smallest owner-boundary change required; do not silently fork the authority.

## Default decision rule - author content before changing architecture

Can the experience be authored through `CURRENT_STATE.md` -> `PROVEN CREATIVE CAPABILITY SURFACE`? If yes, author it as content/data through existing seams. Architecture requires a demonstrated blocker against its owner; a parallel implementation is a defect.

Before gameplay/lane work, read the binding [`AUTHORING_AUTHORITY_AND_MODEL_LANES.md`](Docs/Production/AUTHORING_AUTHORITY_AND_MODEL_LANES.md) for ownership, model lanes and the UI-artist skill. Pick a class with `python Tools/model_router.py pick <class> --detail`; gameplay queue: `CURRENT_STATE.md` section 4.

The rhythm-JRPG remains the production spine until FLOW/SEQUENCE passes its owner proof gate (PIE-proven on `First Resonance`; owner ratification still owed - `CURRENT_STATE.md` "OWNER CANON"). The First Day route having no combat beat does not change this. Shape: OMORI. Music-as-key: Zelda. Wardrobe bar: Infinity Nikki.

## 🚀 Rider & UE 5.8 Engineering Protocols

Canonical runbook: [`Docs/Production/RIDER_UE58_CANONICAL_WORKFLOW.md`](Docs/Production/RIDER_UE58_CANONICAL_WORKFLOW.md).

Use Rider to **find the real owner, make a smaller native change, run the right build, and prove it in Unreal**.

Core rules (full detail in the runbook above):
- use Unreal-aware Find Usages / reflected-asset navigation before adding a competing API;
- close Unreal and run a real `BS_GodFileEditor Win64 Development` build for reflected declarations, modules, Build.cs, generated headers, shader-directory registration, and load-topology changes;
- RiderLink is the default focused live-editor test bridge; Qodana (`qodana.yaml` / `QDJB`) is the static-analysis gate. Neither replaces restart, PIE-input or packaged acceptance when those are required;
- use the native debugger and Unreal Insights on the existing owner seam before redesigning for performance;
- edit tracked `.usf/.ush` in Rider, but UE shader compilation + visible capture is the runtime proof;
- do not rewrite World Compiler, Rokoko ingestion, Blueprint ownership, or editor automation in C++ simply because Rider makes C++ convenient.

---

## T3D / Echo Automation Pipeline

Pipeline: `Spec Change -> T3D Inject -> Compile -> Fingerprint -> Regression Test -> Promote`. Full reference: [`T3D_PIPELINE_FULL_REFERENCE.md`](Docs/Production/T3D_PIPELINE_FULL_REFERENCE.md) and [`T3D_MONOLITH_REFERENCE.md`](Docs/Production/T3D_MONOLITH_REFERENCE.md).

- **Ledger, not prose.** A lane is "done" only when `record_gate.py <id> pass` has a row. Manifest `specs/echo_pipeline.json`; runner `Tools/echo_run.py`; control panel `Tools/project_state.py --view integration | staleness`; contract `Docs/ECHO_PIPELINE_2026-08-09.md`.
- **Read-only verifiers, each answering a question a compile cannot:** `bp_live_path.py` (reachable at all?), `bp_sweep.py` (five shipped defect classes), `graph_reachability.py` (dead islands *inside* a graph), `ui_style_audit.py`, `t3d_dashboard.py`. `Docs/T3D_Baseline/test_canonical.py` and `Tools/test_ui_style_audit.py` have committed assertions - loosening a check is how you blind one. Run them after touching those tools.
- **A probe is not play evidence.** Real-input runtime claims need real input through `BP_BattleUI::OnKeyDown` (or a documented injection path), an accompanying JSON assertion report, and the committed harness being the harness that ran. A probe-only green run is a HOLD.
- **The HUD is shared.** `UMelodiaRhythmHUDWidget` has two drivers; the ambient lane must only clear a highway it set (`bExecutionDrivingHighway`). Two writers on one surface with no ownership is the defect class this whole section exists to prevent.

## Quantum usage

Quantum computing is an **asynchronous decision service** for narrow, measurable gameplay problems only: ranking authored rhythm/encounter patterns, choosing among candidate room/layout seeds, route/puzzle/reward selection under constraints, and offline experiments comparing quantum vs classical baselines. Full contract: [`QUANTUM_GAMEPLAY_EXPERIMENT_PROTO_2026-08-06.md`](Docs/Handoffs/QUANTUM_GAMEPLAY_EXPERIMENT_PROTO_2026-08-06.md).

Hard bans: **never** quantum code for frame-by-frame combat, input timing, or anything that must stay deterministic at frame rate. Hit detection and grading stay classical in UE; quantum may only rank the authored pattern set before play begins and must never decide perfect/great/good/miss. Keep the UE contract small and JSON-based, run the solve in Python or a service boundary (never in Blueprint tick), keep a classical fallback.

## Ownership

- QuillScript is the narrative authoring authority: dialogue, choices, encounter intent and authored consequence content use the allowlisted Quill contract. `UMelodiaNarrativeSubsystem` is the runtime Quill bridge and owner of authored narrative facts, checkpoints, consequences and exactly-once reward/progression transactions; it does not resolve stock combat.
- TurnBased JRPG / Phoenix owns party, turns, skills, targets, action resolution, damage, inventory, terminal battle results and canonical stock gameplay saves. Rhythm executes on the selected JRPG action and returns grade/performance data to that authority; it is not a second combat path.
- `UMelodiaWardrobeSubsystem` owns owned/equipped fashion state and its gameplay capability hooks. `MelodiaTraversalComponent` owns traversal behavior.
- `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter` is the canonical exploration heroine and the **Ultimate** designation; keep its name and the existing locomotion/Rokoko authority. `/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation` remains a separate battle-presentation role. Universe Foundry authors content for existing runtime contracts; do not create another pawn, animation controller, pawn-owned Foundry manager or Niagara framework. Owner map: [`SYSTEM_MAP.md`](SYSTEM_MAP.md#melusina-character-assembly-canonized-2026-09-23); work gates: `Docs/P1_TASK_LEDGER.json` -> `melusina_work`; inventory and evidence tiers: `CURRENT_STATE.md`.
- One writer owns each UI/audio surface. Extend the existing UI bridge, audio-reactive palette, cymatic driver and Niagara/flipbook consumers instead of introducing parallel writers.
- MelodiaCore remains presentation/integration-only; Conversation2D is excluded.

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
- Beauty sender actor: `/Game/Melodia/Lookdev/BP_UE_BeautySender` (droppable; SceneCapture → RT; Spout sender name `UE_Beauty` is the single reserved name — never embed in a production map, never invent a second name)

## Stable notification contract

The subsystem recognizes only these seven verbs (`UMelodiaNarrativeSubsystem::HandleQuillNotification` dispatch table, `MelodiaNarrativeSubsystem.cpp`):

- `melodia:battle:<EncounterId>`
- `melodia:quest:<QuestId>`
- `melodia:flag:<FlagId>:<true|false>`
- `melodia:travel:<LevelId>`
- `melodia:reward:<RewardId>`
- `melodia:stat:<IntentId>:<StatId>:<Delta>`
- `melodia:item:give:<ItemId>:<Count>`

`melodia:stat:` is idempotent per `<IntentId>`, not per `<StatId>`: the intent id is recorded in `FMelodiaNarrativeRecord::ConsumedIntentIds` (SaveGame), so replaying the same authored beat after a Quill resume or a save reload is a no-op. Two different beats may both award the same stat.

`melodia:item:` is a **logging stub** — it validates arity and count and writes `MELUSINA_LOOP_ITEM_GRANT`, then stops. There is no inventory/wallet consumer. Do not author content that depends on it granting anything.

The live allowlist authority is `DA_MelodiaIntegrationConfig` (`TravelLevelIds`, `EncounterIds`, …). Do not add identifiers casually.


## ⚔ Hybrid combat canon — FLOW tunes, SEQUENCE plays (binding)

The turn-based ARPG / ACFU hybrid is the game (owner, 2026-10-11). Any doc that still says "ACFU excluded" is stale — delete it, do not obey it. The convergence is built on `UMelodiaHybridEncounterComponent` and is PIE-proven on the `First Resonance` fixture (`CURRENT_STATE.md` → "First Resonance"):

- **FLOW** = realtime play on the canonical `BP_MelusinaJRPGCharacter` (WaveHarp now, ACF melee/dodge next).
  Each landed hit **tunes** the target's resonance — on-beat a full step, off-beat a partial one, judged at the moment of the player's action (an arrow's release, a swing's start), never at impact.
- **Resonance lock** opens **SEQUENCE** = the turn/rhythm phrase. Cancel shatters the lock; Exit spends it,
  so every phrase is earned again in FLOW.
- **One of everything across both modes:** one encounter identity, one HP owner (the encounter actor), one
  damage authority (the stock Phoenix resolver produces `FinalDamage` in both modes; FLOW passes ×1.0, SEQUENCE passes the rhythm grade's multiplier), one rhythm grader, one durable narrative outcome.
- **New FLOW attack sources** (ACF melee, dodge-counters, Wardrobe abilities) call
  `UMelodiaExternalJRPGBridgeSubsystem::ResolveWorldFlowAttack(Encounter, ActionBeatPhase)` — never their own damage math, never a second HP.
- **Presentation reads, never writes gameplay.** The Chladni figure is driven from `OnResonanceChanged` /
  `GetResonanceNormalized` on a per-actor MID (Nikki Chladni MI path, no new masters, no MPC writes).
- Ownership answers are working-proven but **owner ratification is still owed** (`CURRENT_STATE.md` "OWNER
  CANON" table). Until ratified the JRPG GameMode + canonical pawn stay the only production boot path; ACF arrives as components on that pawn, not by reparenting.

## ⛔ NEVER RUN THESE — they destroy unrecoverable work

On 2026-08-08 an agent ran `git checkout -- .` and started `git clean -fd` on this project while trying to undo a bad FBX import. The `clean` was interrupted before it deleted anything. **That interruption is the only reason the project still has its protagonist.**

| Command | Why it is catastrophic here |
|---|---|
| `git clean -fd` / `-fdx` | Bulk `Content/` is **untracked** (commit `f89fccd5` stopped tracking it). `clean` deletes untracked files. It would permanently erase every character, mesh, material and animation in the project. There is no LFS copy to restore from. |
| `git checkout -- .` | Reverts every modified tracked file to HEAD, including work in progress from other agents and sessions. Uncommitted edits are **not** in the object store, so `reflog` and `fsck` cannot bring them back. It silently destroyed five Python files this way. |
| `delete_asset` on anything you did not create | Tells the running engine to forget an object. The registry then reports the asset as valid on disk while `load_asset` returns False, which looks exactly like file corruption and is not. It cost hours of misdiagnosis. |
| FBX import into a path that already holds an asset | Creates a redirector over the existing asset. Rolling it back by deleting the folder leaves a dead redirector pointing at nothing. |

If you believe one of these is the right move: **stop and ask the owner.** There is no situation in this project where an agent should run a destructive git command unprompted.

### Python + skill Blueprints = instant editor death (2026-08-08)

**Never touch anything under `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` from Python.**
Calling `load_blueprint_class()` / `get_default_object()` on a skill Blueprint forces UE to generate Python glue for the user-defined enum `D_DamageType`, which fails **fatally**:

```
Fatal error: PyWrapperTypeRegistry.cpp:2641
Failed to generate Python glue code for enum
  '/Game/TurnBasedJRPGTemplate/Blueprints/Skills/D_DamageType.D_DamageType'
```

This is not recoverable and not a warning — the editor dies immediately, taking every unsaved package with it. It will happen to any agent that inspects a skill, every time.

**Use Monolith's native path instead.** `blueprint_query` is C++, not Python, so `get_cdo_properties`, `get_graph_data` and `export_graph` all read skill Blueprints safely. Only the `editor_query run_python` route is dangerous here.

Root cause is unfixed: `D_DamageType` is a Blueprint user-defined enum whose enumerators cannot be wrapped — usually a duplicate display name, a name that is not a valid Python identifier, or a reserved word. Fixing the enum removes the landmine.

### If an asset "disappears", check this order before concluding anything

1. Is the file on disk? (`Get-ChildItem -Recurse Content -Filter "<name>.uasset"`)
2. Does the registry still see it? Force a rescan: `ar.scan_paths_synchronous([folder], force_rescan=True)` - a `delete_asset` in this session hides an asset that is perfectly intact on disk.
3. Compare `does_asset_exist` / `find_asset_data` against `load_asset`. Valid metadata plus a failed load means **in-session state, not file damage** - restart the editor.
4. Check for a redirector: the canonical path may resolve elsewhere; `unreal.load_package` returns the package it actually resolved to.
5. Only then look for backups (`Saved/Recovery/`, `CompatibilityLabs/`, per-asset `_OLD` variants). **Never delete a candidate backup while diagnosing.**

## Safe working rules

**Full text: [`UNREAL_EDITOR_SAFE_RULES_FULL.md`](Docs/Production/UNREAL_EDITOR_SAFE_RULES_FULL.md)** — all 26 rules are binding; read it before editor work. The ones that bite hardest:

**Destroying work** (never run, even "to undo something") is the table above: `git clean`, `git checkout -- .`, `delete_asset`, FBX import over an existing asset. Ask the owner first.

**Editor safety:** one editor instance, always (three at once cost 39 unsaved packages on 2026-08-08 — check `Get-Process UnrealEditor` and that port 9316 has one listener). `MODAL_OPEN` in the log is a modal dialog, not a hang; grep before killing the editor. **Parallelise research and C++ freely; serialise all editor work through one holder.** Never trust a report that something is "blocked by the editor" — write-open the DLL and see for yourself.

**Evidence:** `success: true` only means nothing threw — verify by re-reading (`list_dirty_packages`). Static graph inspection is not runtime proof. A **dump cannot prove absence** — a string dump of `DA_MelodiaIntegrationConfig` once produced a confident, wrong "this property doesn't exist". Use reflection (`get_cdo_properties`), not text search. A variable-reference census misses expose-on-spawn pins, and a **committed export is an output, not an input** — verifiers re-derive from the live graph every run.

**Builds:** "the build is green" decays into a lie — adaptive unity hides symbol collisions that only appear on a full rebuild, so do a full closed-editor build before trusting green and before starting editor work. A file existing is not a file compiling: **build code another lane left before planning around it.** Live Coding cannot introduce new imports; any header change needs a full closed-editor build.

**Blueprint/asset archaeology:** search both name forms (`UnitHasEnoughMP` vs `Unit Has Enough MP` — node titles are spaced, and a miss once produced a confidently wrong "never called"). `ORPHAN` means prove it, not delete it. A level actor listing **aggregates streaming sublevels** — read the `sublevel` field; a sublevel not set to load at startup is absent from PIE. Copy node clusters, never whole files, from template projects: `Content/_ThirdParty/TurnBasedJRPGTemplate/` is not pristine. Check Monolith's own namespace before concluding a capability is impossible.

**Config/runtime:** the narrative allowlist does **not** fail closed in editor builds
(`bRelaxedAllowlistInEditor = true`), so an authored typo works in PIE and breaks packaged — verify with it off. Never hand-build engine data structures (a malformed `UMidiFile` crashed the editor); copy the engine's own construction path. Do not touch anything under `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` from Python — it kills the editor fatally; use Monolith's native `blueprint_query` instead.

**Housekeeping:** `Saved/Audit/*.json` is allowlisted in the pre-commit hook and needs no
sign-off. Two cron jobs sharing one `workdir` deadlock on the TERMINAL_CWD lock — drop `workdir` or stagger them.

## 5. jcode Swarm (parallel coding lane)

Primary **repo-side** parallel coding uses [jcode](https://jcode.sh) light-swarm on the Windows UE workstation.

*   **Policy:** [`.jcode/swarm-prompt.md`](.jcode/swarm-prompt.md) — PGA/MPA/PPA/WIA/SQA/WEB/MUSE spawn scopes, concurrency cap 6, no recursive worker spawning.
*   **Bootstrap:** `.\deploy\start_jcode_swarm.ps1` then paste [`.jcode/coordinator-bootstrap.md`](.jcode/coordinator-bootstrap.md). MCP: [`.jcode/mcp.json`](.jcode/mcp.json) → Monolith stdio proxy (needs Unreal open). Skills: `.\deploy\install_jcode_melodia_skills.ps1`.
*   **Companion IDE lanes:** OpenCode in Rider (C++/PIE) via [`.opencode/opencode.jsonc`](.opencode/opencode.jsonc) + `.\deploy\start_opencode_muse_lane.ps1`; Muse Code (WSL) via [`MUSE_CODE_LANE_2026-08-11.md`](Docs/Production/MUSE_CODE_LANE_2026-08-11.md).
*   **Do not** start `deploy/cursor_*_loop.ps1` for new work (deprecated, left in tree). Phone/Cursor cloud agents stay the PR / mobile lane and must not overlap write paths with a live local swarm.

Full guide: [Docs/PhoneOps/JCODE_SWARM_PIPELINE.md](Docs/PhoneOps/JCODE_SWARM_PIPELINE.md) · [`.jcode/README.md`](.jcode/README.md)
