# BS_GodFile agent context

**Front-door review:** 2026-10-05 against `main` at `e25682b3a83c5f6453a355f60a08b772309d3dad`.

## STATUS — one document

[`CURRENT_STATE.md`](CURRENT_STATE.md) is the only status document: what works (with evidence level), what is open, the owner queue, repositories, workstations, and recurring traps. If any other file in this repo states project status, it is stale — fix `CURRENT_STATE.md`, not that file. Do not create handoff, plan, receipt, or session-note files. Pre-collapse docs: `git show 7d271c15:<path>` (tag `docs-precollapse-2026-09-10`).

## ⚑ MELUSINA RUNTIME RIG + RETARGET CANON — 2026-10-05

**Read [`Docs/Production/MELUSINA_RUNTIME_CANON_2026-10-05.md`](Docs/Production/MELUSINA_RUNTIME_CANON_2026-10-05.md) before any retarget, animation or rig work.** It supersedes older rig/retarget docs.

- **Raw retarget output into `SK_Melusina_Skeleton` is known-defective — never ship it.** Every retarget needs the canon arm correction, then verification: `15.774 | 28.561 | 28.615` (world cm, `shoulder→arm_stretch→forearm_stretch→hand`). Reject `34.789 | 9.520 | 28.615` — that is the reference-pose interruption.
- Her rig is **not mannequin**: `shoulder_l → arm_stretch_l → forearm_stretch_l → hand_l`; legs `thigh_stretch_l → leg_stretch_l → foot_l → toes_01_l`; **no `pelvis`**, **no `ik_foot_l/r`**.
- The `UpperBody` slot feeds a **layered blend** — its branch mask must carry the 11 spine+arm filters or draw/cast montages are silently blended away.
- **Caster/archer hybrid is intentional**: LMB = caster + floating astrolabe; RMB = Sparrow charged draw/hold/fire. Preserve it.
- `batch_retarget_animations` + `overwrite=true` **crashes the editor**. Never pass it.
- **Open:** the six owner-approved SparrowArchery clips still carry the arm defect (frozen — owner decision).

## ⚑ OWNER SOURCE-OF-TRUTH RULING — 2026-10-29

**`C:\EnvironmentPortfolio\BS_GodFile` is the source of truth.** Git and Perforce are backup and transport, not authority. No agent may overwrite the owner's checkout from them: never `p4 sync`, `p4 revert`, `p4 sync -f`, `git checkout`, `git reset`, `git stash`, or `git clean` against this checkout without explicit owner approval. Agents work in their own lane worktrees and copy in only reviewed artifacts. Recovery layers: `Tools/loss_vault.ps1` snapshots modified Content to `D:\MelodiaVault` every 5 minutes from logon; `Tools/lane_guard.ps1` diffs the Content manifest and reports missing files. A save on C: is the work; a submit or commit is the backup.

## BINDING RULES — every agent (Hermes, Codex, Claude, subagents)

Hermes loads this file, not `CLAUDE.md`, so the binding rules are repeated here. **Read
[`CLAUDE.md`](CLAUDE.md) in full before acting.** `_AGENT_WORKING_AGREEMENT.md` outranks every
agent doc. For Git, storage, branch/lane, and integration policy, this file plus the linked current
production contracts are canonical; `CLAUDE.md` may add Claude-specific execution notes but must
not override a newer repo-wide contract.

- **Git pipeline law.** `origin/main` is canonical and is a landing target, never an agent workspace.
  Workers use detached lane worktrees pinned by `refs/agents/<lane>` and do not push/open PRs themselves.
  Commits inside a worker's own lane and normal integrator landing are covered by the standing authorization
  below. Explicit owner approval is still required for destructive history/worktree operations, deleting
  refs/branches, force-push/history rewrite, and any Perforce submit.
  **Storage architecture (2026-10-01).** Git carries code/docs/plans; Perforce carries bulk binary
  (`Content/`, dropped plugins, `Reference/`). **The Perforce server root is `D:\perforce\root` on
  this machine, so a p4 submit is history-tracked, NOT off-machine — GitHub is the only offsite
  copy.** Never call a p4 submit a backup. Full picture:
  [`STORAGE_ARCHITECTURE_2026-10-01.md`](docs/Production/STORAGE_ARCHITECTURE_2026-10-01.md).
  Exact casing matters: the October 1 storage/closeout records live under lowercase `docs/`; the repo also
  contains an uppercase `Docs/` tree. Do not case-normalize or case-move either tree casually on Windows.
  **This file was over the 32 KB agent-context budget and being served truncated. Trimmed
  2026-10-01 to 30,659 bytes by relocating three sections to linked docs — no rule was deleted.
  If you add to it, keep the total under 32,768.**
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
- ACFU is no longer R&D-only: the turn-based ARPG / ACFU hybrid is CANON (owner, 2026-10-11; open ownership questions are listed in `CURRENT_STATE.md` "OWNER CANON"). Production promotion still needs runtime proof (possession + one ACF melee exchange in PIE).
- Choral Sheep remains the non-combat capstone lane and must not be coupled to the combat migration.
- If runtime proof shows the stable owner map is genuinely wrong for the desired game, report the smallest owner-boundary change required; do not silently fork the authority.

The first promotion proof should be approximately: canonical Melusina → real FLOW input → WaveHarp/action hit → authoritative resolved damage → same world target/HP → readable feedback → continued movement. Add FLOW → SEQUENCE → FLOW only after FLOW itself is real.

## Default decision rule - author content before changing architecture

> Can the requested experience be authored using the systems listed in
> `CURRENT_STATE.md` -> `PROVEN CREATIVE CAPABILITY SURFACE`?

If yes, author the content. Do not alter architecture. A boss, side quest, rhythm skill, cymatic
biome, wardrobe ability, and procedural setpiece are normally content/data authored through the
existing seams. Architecture work requires a demonstrated blocker recorded against the relevant
owner seam. A new parallel implementation is a defect, not progress.

**Full authority map, stable ownership list, model-lane table, and the UI-artist skill pointer:
[`AUTHORING_AUTHORITY_AND_MODEL_LANES.md`](Docs/Production/AUTHORING_AUTHORITY_AND_MODEL_LANES.md)** —
binding, read before gameplay or lane work. Pick a task class with
`python Tools/model_router.py pick <class> --detail`; gameplay queue is `CURRENT_STATE.md` §4.

The rhythm-JRPG loop is the **production authority spine until the owner-directed FLOW/SEQUENCE
promotion gate passes.** Shape: OMORI. Music-as-key: Zelda. Wardrobe bar: Infinity Nikki.

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

## T3D / Echo Automation Pipeline

```text
Spec Change → T3D Inject → Compile → Fingerprint → Regression Test → Promote
```

**Full reference: [`T3D_PIPELINE_FULL_REFERENCE.md`](Docs/Production/T3D_PIPELINE_FULL_REFERENCE.md)**
(tool tables, verification tools, evidence standard, defect classes) and
[`T3D_MONOLITH_REFERENCE.md`](Docs/Production/T3D_MONOLITH_REFERENCE.md) (spec recipes,
Monolith action tables, `ci_gates.json`).

- **Ledger, not prose.** A lane is "done" only when `record_gate.py <id> pass` has a row.
  Manifest `specs/echo_pipeline.json`; runner `Tools/echo_run.py`; control panel
  `Tools/project_state.py --view integration | staleness`. Contract: `Docs/ECHO_PIPELINE_2026-08-09.md`.
- **Read-only verifiers, each answering a question a compile cannot:**
  `bp_live_path.py` (is it reachable at all?), `bp_sweep.py` (five shipped defect classes),
  `graph_reachability.py` (dead islands *inside* a graph), `ui_style_audit.py`, `t3d_dashboard.py`.
  `Docs/T3D_Baseline/test_canonical.py` and `Tools/test_ui_style_audit.py` have committed
  assertions — loosening a check is how you blind one. Run them after touching those tools.
- **A probe is not play evidence.** Real-input runtime claims need real input through
  `BP_BattleUI::OnKeyDown` (or a documented injection path), an accompanying JSON assertion
  report, and the committed harness being the harness that ran. A probe-only green run is a HOLD.
- **The HUD is shared.** `UMelodiaRhythmHUDWidget` has two drivers; the ambient lane must only
  clear a highway it set (`bExecutionDrivingHighway`). Two writers on one surface with no
  ownership is the defect class this whole section exists to prevent.

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
- MelodiaCore remains presentation/integration-only; Conversation2D is excluded. The turn-based ARPG / ACFU hybrid is CANON (owner, 2026-10-11; open ownership questions are listed in `CURRENT_STATE.md` "OWNER CANON").

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

The live allowlist authority is `DA_MelodiaIntegrationConfig` (`TravelLevelIds`, `EncounterIds`, …). Do not add identifiers casually.


## ⚔ Hybrid combat canon — FLOW tunes, SEQUENCE plays (binding)

The turn-based ARPG / ACFU hybrid is the game (owner, 2026-10-11). Any doc that still says "ACFU excluded"
is stale — delete it, do not obey it. The convergence is built on `UMelodiaHybridEncounterComponent` and is
PIE-proven on the `First Resonance` fixture (`CURRENT_STATE.md` → "First Resonance"):

- **FLOW** = realtime play on the canonical `BP_MelusinaJRPGCharacter` (WaveHarp now, ACF melee/dodge next).
  Each landed hit **tunes** the target's resonance — on-beat a full step, off-beat a partial one, judged at the
  moment of the player's action (an arrow's release, a swing's start), never at impact.
- **Resonance lock** opens **SEQUENCE** = the turn/rhythm phrase. Cancel shatters the lock; Exit spends it,
  so every phrase is earned again in FLOW.
- **One of everything across both modes:** one encounter identity, one HP owner (the encounter actor), one
  damage authority (the stock Phoenix resolver produces `FinalDamage` in both modes; FLOW passes ×1.0,
  SEQUENCE passes the rhythm grade's multiplier), one rhythm grader, one durable narrative outcome.
- **New FLOW attack sources** (ACF melee, dodge-counters, Wardrobe abilities) call
  `UMelodiaExternalJRPGBridgeSubsystem::ResolveWorldFlowAttack(Encounter, ActionBeatPhase)` — never their own
  damage math, never a second HP.
- **Presentation reads, never writes gameplay.** The Chladni figure is driven from `OnResonanceChanged` /
  `GetResonanceNormalized` on a per-actor MID (Nikki Chladni MI path, no new masters, no MPC writes).
- Ownership answers are working-proven but **owner ratification is still owed** (`CURRENT_STATE.md` "OWNER
  CANON" table). Until ratified the JRPG GameMode + canonical pawn stay the only production boot path; ACF
  arrives as components on that pawn, not by reparenting.

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

**Full text with rationale and incident history:
[`UNREAL_EDITOR_SAFE_RULES_FULL.md`](Docs/Production/UNREAL_EDITOR_SAFE_RULES_FULL.md)** — all 26
rules are binding; read it before editor work. Index of the ones that bite hardest:

**Destroying work (never run, even "to undo something"):** `git clean -fd`/`-fdx` (bulk `Content/`
is untracked and unrecoverable), `git checkout -- .` (destroys other lanes' uncommitted work),
`delete_asset` on anything you did not create, FBX import over an existing asset (leaves a dead
redirector). Ask the owner first; there is no situation where an agent runs these unprompted.

**Editor safety:** one editor instance, always (three at once cost 39 unsaved packages on
2026-08-08 — check `Get-Process UnrealEditor` and that port 9316 has one listener). `MODAL_OPEN`
in the log is a modal dialog, not a hang; grep before killing the editor. **Parallelise research
and C++ freely; serialise all editor work through one holder.** Never trust a report that
something is "blocked by the editor" — write-open the DLL and see for yourself.

**Evidence:** `success: true` only means nothing threw — verify by re-reading
(`list_dirty_packages`). Static graph inspection is not runtime proof. A **dump cannot prove
absence** — a string dump of `DA_MelodiaIntegrationConfig` once produced a confident, wrong
"this property doesn't exist" and an investigation built on it. Use reflection
(`get_cdo_properties`), not text search, to establish that something is missing. Likewise a
variable-reference census misses expose-on-spawn pins, and a **committed export is an output,
not an input** — verifiers re-derive from the live graph every run.

**Builds:** "the build is green" decays into a lie — adaptive unity hides symbol collisions that
only appear on a full rebuild, so do a full closed-editor build before trusting green and before
starting editor work. A file existing is not a file compiling: **build code another lane left
before planning around it.** Live Coding cannot introduce new imports; any header change needs
a full closed-editor build.

**Blueprint/asset archaeology:** search both name forms (`UnitHasEnoughMP` vs `Unit Has Enough MP`
— node titles are spaced, and a miss once produced a confidently wrong "never called").
`ORPHAN` means prove it, not delete it. A level actor listing **aggregates streaming sublevels**,
so read the `sublevel` field — a sublevel not set to load at startup is absent from PIE. Copy node
clusters, never whole files, from template projects: `Content/_ThirdParty/TurnBasedJRPGTemplate/`
is not pristine and the live `BP_BattleUI` delta is authored work. Check Monolith's own namespace
(1,330 actions / 24 namespaces) before concluding a capability is impossible.

**Config/runtime:** the narrative allowlist does **not** fail closed in editor builds
(`bRelaxedAllowlistInEditor = true`), so an authored typo works in PIE and breaks packaged — verify
with it off. Never hand-build engine data structures (a malformed `UMidiFile` crashed the editor);
copy the engine's own construction path. Do not touch anything under
`Content/TurnBasedJRPGTemplate/Blueprints/Skills/` from Python — it kills the editor fatally;
use Monolith's native `blueprint_query` instead.

**Housekeeping:** `Saved/Audit/*.json` is allowlisted in the pre-commit hook and needs no
sign-off. Two cron jobs sharing one `workdir` deadlock on the TERMINAL_CWD lock — drop `workdir`
or stagger them.

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
