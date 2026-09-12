# QUEUE — environment-art / portfolio tracker

**As of 2026-07-30: this file is scoped to environment-art/portfolio work only.** Gameplay/vertical-slice tracking has moved to the project-root canonical docs:
- `_TASK_QUEUE.md` — the real, live, granular task tracker (P0/P1/P2/P3, per-task status/agent).
- `_VERTICAL_SLICE_SCOPE.md` — current scope authority. Explicitly states: *"This document supersedes the historical Phase 2/SakuraDream/MelodiaCore scope. That plan predated the working JRPG/Quill route and is not an active implementation instruction."*
- `_DECISION_LOG.md` — append-only strategic decisions (**through Decision 045 as of 2026-08-07**;
  this pointer previously read "011" and was ~26 decisions stale — check its mtime before trusting it).
  Updated 2026-08-07 to reflect Decisions 038–045 and the Blueprint wiring contract/skill docs.
- `_SESSION_HANDOFF.md` — most recent session's accomplished/pending/do-not-do list.

Everything below the historical markers in this file (PIVOT/SCOPE CORRECTION/FOUNDATION CORRECTION/SOLO GAMEPLAY GOVERNANCE/GAMEPLAY RESUME GATES/PAUSED-gameplay sections) is **historical** — the "portfolio-first, gameplay fully paused" stance they describe was superseded by Decision 008 (2026-07-29): both tracks now run in parallel, portfolio via delegated AI agents. Read the root docs above for current gameplay state, not the sections below.

Superseded: `Docs/AI_ORCHESTRATION_HANDOFFS_2026-07-17.md` (read-only history now). Lanes edit **this file** for portfolio/environment-art work; edit `_TASK_QUEUE.md` for gameplay work.

## Architectural rules (read before touching anything)

1. **Finish existing systems. Never invent a parallel one.** Search Docs/ + code for prior art first; cite what you extend.
2. **Musical Influence is ONE canonical project-wide channel, not a per-system reinvention.** `UMelodiaRhythmReactivitySubsystem` already publishes beat/grade/combo/crescendo signals into MPC scalars — that IS the project's musical-influence parameter. Any new system (PCG dressing intensity, environment reactivity, future UI) that wants to react to music **reads this MPC / subscribes to this subsystem's signals**. It does not compute its own beat clock, its own audio analysis, or its own reactivity scalar.
3. **One verification pass, by the agent that made the change, then move on.** No lane re-verifies another lane's already-finished work. This is the direct fix for the two days lost to over-verification.
4. **Acceptance criteria are written before work starts and are binary** (a log line, a PIE observation, `Result: Succeeded`). Meet it, stop, commit, move to the next item.
5. **Turn-budget discipline**: if a task is taking much longer than its acceptance test implies, stop and report rather than grind.
6. **Gameplay authority (corrected 2026-07-26)**: for the eventual authored
   game, the complete TurnBased JRPG template is the provisional mechanical
   authority. MelodiaCore is quarantined because it is runtime-unstable;
   salvage only bounded concepts or presentation work after independent proof.
   Blueprints may own template-native mechanics where the proven template
   already does so. Do not rebuild those mechanics in MelodiaCore, ACFU,
   QuillScript, or a parallel Blueprint graph. See
   `Docs/MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md`.
7. Escalate design decisions to the coordinator instead of deciding unilaterally.
8. Scoped commits, exact paths, per completed item. No `git add -A`. No rebase/force-push without explicit go.
9. **Session start-of-work MCP check**: this project runs Unreal-side agents on TWO MCP bridges simultaneously — `monolith` (deep editor/asset/blueprint queries) and `it-is-unreal` (actor/level/PIE-adjacent tools) — used together to round each other out, not as alternatives. At the start of any session touching Unreal, verify BOTH are actually present in the tool list (not just "the editor is running" — the bridge plugin being installed does not mean the MCP connection is live). If one is missing, say so immediately and ask the user to reconnect it before assuming a tool is simply unavailable for the task.

## [HISTORICAL — superseded by Decision 008, 2026-07-29] PIVOT (2026-07-25) — Environment Portfolio Only, No Gameplay/C++

**Current status record:** `Docs/PROJECT_STATUS_2026-07-25.md` consolidates the
latest project assessment. Storage relocation/DDC migration and the staged water
shader pass are complete; neither is an active gate.

**Hard rule for the duration of this push**: no `Plugins/MelodiaCore` touches, no battle/roguelike/save/C++ work, full stop. Goal is AAA-quality environment art + a real render pipeline, fast, for hire/income before the school semester restarts. All gameplay work below is paused, not abandoned — nothing deleted, resume post-portfolio-push. See `Docs/SCAFFOLDING_DEEP_REVIEW_2026-07-24.md` and the render/environment audit in this session for full findings.

### SCOPE CORRECTION (2026-07-25, next morning) — engine + reference decisions, gameplay target
- **Engine**: staying in UE5.8 for both the portfolio AND the eventual game. Earlier same-day recommendation to move the RPG/VN to Godot is retracted — real, PIE-verified combat and exploration systems already exist integrated with the environment art in MelodiaCore; discarding that to rebuild in a new engine was the wrong call.
- **Reference case**: OMORI/OMOCAT retracted as a production-culture reference (documented labor allegations — see plan file for sources) and as a timeline comparison (2D pixel-art production cost ≠ 3D environment-art production cost).
- **Corrected gameplay target, once the portfolio push is done**: "a watered down version of Persona but 10000x more simple" — bedroom (VN/dialogue) → overworld exploration → simple fixed turn-based battle (no procedural/roguelike run structure) → talk to buddy (VN) → bed → repeat. Procedural/roguelike depth explicitly cut from the MVP; VN/dialogue is the one genuinely new system needed (current stub: flat `TArray<FText>`, no branching). Full detail in `C:\Users\froma\.claude\plans\let-s-start-with-the-quiet-petal.md`.
- **Staffing**: plan is to hire a real, accountable C++ developer for the gameplay side once portfolio push is done, scoped to a short fixed brief (strip roguelike/procedural-encounter code to the fixed-loop model, build VN/dialogue, own MelodiaCore module cleanup) — explicitly NOT an open-ended "own the architecture" mandate, to avoid repeating the original problem of no single owner across multiple uncoordinated AI agents. User remains creative/product architect.
- **This section supersedes** any earlier PAUSED-gameplay items below that assume procedural/roguelike depth (M2/M3 anchors, seed-push loot) — those stay paused and will likely be cut, not resumed, once the hire scopes the corrected loop.

### FOUNDATION CORRECTION (2026-07-26)

The complete standalone TurnBased JRPG template, not MelodiaCore, is the
runtime-proven gameplay baseline. The UE5.8 lab compiles cleanly and its three
maps initialize; interactive UE5.8 and packaging gates remain. MelodiaCore is
runtime-unstable and is quarantined as an authority. QuillScript is an isolated
narrative candidate. ACFU is an alternate action-RPG foundation and must not
coexist with the chosen JRPG authority.

This correction supersedes the earlier statements above that gameplay was
already proven through MelodiaCore or that a future hire must make MelodiaCore
cleanup the foundation. A future gameplay owner should preserve the JRPG
baseline, own the narrative adapter and save migration, and integrate Melodia
presentation through bounded slices.

## NOW (max 3)
- [x] Phase 0 — machine speed: killed nothing unsafe (leftover gameplay daemons already self-exited), cleared Temp+CrashDumps (~6GB), moved 3 large installers/assets off Downloads + deleted 1 exact-duplicate installer (~5.5GB), disabled Wallpaper Engine/Riot Client/Teams/Discord from startup. `C:\Windows\Installer` (15.1GB, MSI cache) and Blender Roaming (8.2GB, diffuse across many small files) flagged but NOT touched — need a dedicated tool (PatchCleaner) or manual review, not a blind delete.
- [x] Phase 2a — fixed `run_portfolio_capture.py` stale level-path bug (was `/Game/EnvSandbox/Levels/L_SakuraPath`, real path `/Game/EnvSandbox/Environments/Sakura/L_SakuraPath`; also fixed a Git-Bash env-var path-mangling gotcha when testing — use `MSYS_NO_PATHCONV=1`). `render_exporter.py` confirmed working end-to-end: 2 real hero renders produced, correct geometry/lighting. `scene_metadata_exporter.py` still returns null/empty for reasons not fully diagnosed (see OPEN section) — non-blocking, revisit later.
- [x] Phase 2b — **MRQ genuinely stood up**, both presets created and verified on disk (`Content/EnvSandbox/MRQ/Presets/MRQ_Preset_Cinematic.uasset` 4K 16-bit multilayer EXR, `MRQ_Preset_MI_Loop_1080.uasset` 1080 PNG). `setup_mrq_presets.py` was rewritten against a live UE 5.8 API dump, not guesses — real bugs found and fixed: (1) `MoviePipelineDeferredPass` doesn't exist, real name `MoviePipelineDeferredPassBase`; (2) the whole construction pattern was wrong — real API is `preset.find_or_add_setting_by_class(SettingClass)`, not property assignment on `.get_settings()`; (3) resolution/output-directory live on a separate `MoviePipelineOutputSetting`, not the per-format output class. Explicitly enabled `MovieRenderPipeline` plugin in `.uproject` (was only pulled in transitively via `RenderGrid`). **Next**: `run_mrq_capture.py` (actually queuing/executing a render) still needs the same live-verification treatment before trusting it — same class of risk as the presets had.
- [ ] Phase 3 — retire/rewrite `Docs/PCG_CATALOG.md` (stale, describes a renamed library) + resolve `PCG_RockScatter` vs `PCG_Universal_RockScatter` naming (not a dupe — needs a naming decision, your call).

## NEXT (max 5) — Phase 4 hero shots, in priority order
- [ ] **L_EscherAscent**: add CineCameraActor composition(s) + real PBR trim/tileable texture pass through `M_Master_Toon_Universal`'s existing triplanar slots (currently pure procedural SDF — will read flat without real texturing). Fastest path to one undeniable image; zero placeholder meshes already.
- [ ] **L_FallenMoon**: camera + rim-light/bounce-card pass against the moon key light (shard undersides currently dead — only 1 directional + 2 skylights).
- [ ] **ZenForestTest**: swap 5 placeholder assets (`SM_SM_Torii`, 2 generic trees, a placeholder bridge, one wall) for real library/Fab meshes — prescribed by `ART_DIRECTOR_REVIEW.md`, never landed. Already has 5 cine cameras; pick/polish the best one after the swap.
- [ ] Assemble via existing `portfolio_aggregator.py` → `portfolio_package.json`, following `ART_DIRECTOR_REVIEW.md`'s shot list: hero still → material grid (13-14 `MI_Show_*`) → breakdown/wireframe sheet → procedural-axis diagram → perf spec card → second environment → flythrough video.
- [ ] Verify the Blender→UE world-manifest bridge (`deploy/surreal_world/`, per `MELODIA_GMM_FAMILY_ARCHITECTURE_PLAN.md`) end-to-end on one simple test case — the actual "bridge Blender GN to UE" ask, testing the existing contract rather than building new.

## BLOCKED — environment-art/portfolio lane only
*(none right now)*

> Scope reminder: this heading covers **this file's lane only** (environment art / portfolio). It is
> not a project-wide "nothing is blocked" statement — it used to read that way and misled a reader.
> Project-wide blockers live in [`_ROADBLOCKS_2026-07-31.md`](../_ROADBLOCKS_2026-07-31.md); gameplay
> tasks live in [`_TASK_QUEUE.md`](../_TASK_QUEUE.md).

## OPEN — non-blocking (revisit in a live editor session, not headless)
- [ ] `scene_metadata_exporter.py` returns all-null/empty even when `render_exporter.py` (runs right after, same loaded level) produces a correct real render. Fixed the known stale-level-path bug + reorder + longer settle time — none of it changed the result. Added `DIAG` log lines to trace `_get_editor_world()`/`get_current_level()`/`get_all_level_actors()` step by step, but **the diagnostic lines never appeared in any log file across 3 rapid headless relaunches** — strong sign the actual blocker here is log-file rotation/read races from launching `UnrealEditor-Cmd` repeatedly in quick succession, not necessarily the exporter logic itself. **Not blocking**: `render_exporter.py` is the actual pixel-producing tool and works correctly end-to-end (2 confirmed real renders, correct geometry/lighting). Debug this later in one persistent interactive editor session (`py Content/Python/scene_metadata_exporter.py` from the in-editor console) where DIAG output is immediately visible, instead of blind headless relaunch cycles.
- [ ] Cosmetic: `render_exporter.py`'s reported filename in the JSON result doesn't always match the actual file written to disk (timestamp differs slightly) — likely `take_high_res_screenshot`'s async capture re-timestamping internally. File is still found on disk, just under a different name than reported.

## [HISTORICAL, 2026-07-26 — superseded, see _TASK_QUEUE.md for current gameplay tasks] SOL — that day's entry point

Left as historical record of a specific day's handoff. For current gameplay tasks/status, read `_TASK_QUEUE.md` and `_VERTICAL_SLICE_SCOPE.md` at the project root instead.

**Git infra note — SUPERSEDED 2026-07-31. Do not follow the struck text below.**

~~In practice, plain `git add`/`git commit` in `BS_GodFile\.git` has continued to work reliably (only `git status`/`git fsck` ever touched the corrupt object) — confirmed again 2026-07-30.~~

**2026-08-05 RESOLVED:** `BS_GodFile/.git` has been recovered from `.git.backup.mirror` and is now a normal git repo on `main` with a clean working tree. Plain `git add`/`git commit` works reliably again. The recovery Git directory is no longer needed.

`_SESSION_HANDOFF.md` (2026-07-30 21:11) is the newer authority and says this explicitly. The struck
sentence directly invited the opposite behaviour while citing the same date, which is exactly the
kind of drift `_ROADBLOCKS_2026-07-31.md` tracks (contradiction C9). The corrupt loose object
`a0dfa89499ed206a677a3e8a39424faffa266060` is still unrepaired and `git fsck --full` still times out.

## [HISTORICAL — superseded, see _TASK_QUEUE.md] PAUSED — gameplay (resume post-portfolio-push, do not touch until then)
- [ ] Fix/quarantine `L_MelodiaGrove` entrance-ground-validation bug (dungeon generation). Owner: Cline (raycast sweep script) → Sonnet.
- [ ] Repair the corrupt git loose object `a0dfa89499ed206a677a3e8a39424faffa266060` (dated 2026-07-20; `git fsck --full` times out on this repo — needs a dedicated session).
- [ ] PCG M2 — `PCG_Sub_GameplayAnchors` subgraph; PCG-spawned `AMelodiaEncounterTrigger` via Spawn-Actor attribute overrides.
- [ ] Hoist `IsAnyStreamedRoomPCGGenerating()` guard in `MelodiaDungeonRunCoordinator.cpp:218-227` out of the relocate-only conjunction.
- [ ] PCG M3 — seed push from `AuthoritativeStage.StageSeed`, loot branch grants Heart/Swirl tokens.
- [ ] Verify in-editor whether Melusina's BP/ABP implements `MelodiaCombatPresentationInterface`/`MelodiaEnemyPresentationInterface` (7 events, inconclusive text search of the binary asset — needs a real editor check).
- [ ] Content layer for `UMelodiaOutfitComponent`: a `UMelodiaCosmeticDefinition` DataAsset mapping the wardrobe drafts in `Imports/Data/Cosmetics/` to garment meshes/slots.
- [ ] Stop/archive `deploy/start_ollama_fleet.ps1` gameplay-content daemon launcher — scripts stay, just don't run them during the portfolio push.

## [HISTORICAL — superseded, see _VERTICAL_SLICE_SCOPE.md's "Foundation gate before combat expansion"] GAMEPLAY RESUME GATES (post-portfolio only)

- [ ] Run the independent UE5.8 JRPG and QuillScript acceptance gates described
  in `Docs/MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md`.
- [ ] Complete the lab-only Melusina attack slice, then one heal; preserve JRPG
  mechanical authority and use exactly one impact notify.
- [ ] If QuillScript passes independently, prove
  `dialogue -> battle -> result -> dialogue` through an allowlisted adapter.
- [ ] Define and migrate one versioned JRPG-owned narrative save record.
- [ ] Treat older MelodiaCore roguelike, PCG encounter-anchor, seed/reward, and
  presentation-interface tasks as historical backlog. Do not resume them unless
  the product scope explicitly restores those systems.

## DONE (most recent first)
- 2026-07-24 — **PCG M1 complete**: all 22/22 room `<Room>_PCGVolume` actors assigned real graphs via `Content/Python/assign_room_pcg_graphs.py` (archetype-keyed, idempotent, handles V2/V3 variants). Hit and fixed two real bugs: `PCGComponent.Graph` is reflection-protected (needs `set_graph()`, not `set_editor_property`), and the batch had no per-room error isolation (one failure aborted all 22 — fixed). PCG structural health pass: `Docs/PCG_CATALOG.md` confirmed stale (references a fully renamed/reorganized graph library); `PCG_RockScatter`/`PCG_Universal_RockScatter` confirmed NOT a duplicate (deliberate succession, needs a naming decision, not a fix); `_Deprecated`/`_Scratch`/`Legacy_Portfolio` folders are correctly and minimally quarantined (good hygiene, not clutter). Coordinator.
- 2026-07-24 — Portfolio render pipeline (`deploy/portfolio_render.ps1`) run headless against freshly-dressed `L_SakuraPath` (Kimi's baroque arch + rose window ornaments). Coordinator.
- 2026-07-24 — Fixed real per-frame lag in `UMelodiaRhythmReactivitySubsystem` (14x/frame LoadObject-by-string + unconditional OSC/broadcast spam at idle) + live-integration deep review. Coordinator.
- 2026-07-24 — Shared `AMelodiaCharacterBase` (camera rig, party-switch, mapping-context cleanup) + `UMelodiaOutfitComponent` (modular garment-slot seed) — both characters migrated, zero behavior change, compiled clean. Coordinator.
- 2026-07-24 — Deep scaffolding review across character/outfit, content-authoring, and module-architecture pillars (`Docs/SCAFFOLDING_DEEP_REVIEW_2026-07-24.md`). Coordinator.
- 2026-07-24 — Reconciled `feature/touchdesigner-mcp-integration` (unrelated-history import, 56 files) + `codex/integration-gameplay-loop-20260718` → `main` (fast-forward). Coordinator.
- 2026-07-24 — Fixed the actual `.mcp.json` monolith path (was pointing at a stale pre-consolidation project); removed an unrationale'd MeshBlend git-hook protection; scoped git tracking from 15,790 to ~5,000 files. Coordinator.
- 2026-07-24 — Diagnosed BP_Melusina "broken" as blocked PlayerStart (not a compile error); fixed `SpawnCollisionHandlingMethod` in `MelodiaSmokeCharacter.cpp`; cold rebuild verified `Result: Succeeded`. Coordinator.

## [HISTORICAL — this section's "NOW contains one task" is superseded by _TASK_QUEUE.md's full granular list] SOLO GAMEPLAY GOVERNANCE (2026-07-27)

Active constitution: `Docs/MELODIA_SOLO_GAMEPLAY_CONSTITUTION_2026-07-27.md` (the constitution itself is still current; only the single-task "NOW" framing below it has been superseded by the richer `_TASK_QUEUE.md` tracker).

The project is one-person development, not a multi-agent studio. During the
post-portfolio gameplay phase:

- NOW contains one task: prove Quill dialogue -> JRPG battle -> typed result -> Quill resume.
- NEXT contains at most three tasks.
- No recursive/background mutation loops or parallel gameplay authorities.
- JRPG owns battle, party, quests, travel, inventory, and canonical save.
- Quill owns authored narrative flow only, behind the allowlisted Melodia adapter.
- Melodia owns bounded presentation only.
- Roguelike depth, MelodiaCore authority, ACFU, broad wardrobe, companion flight,
  rhythm turn authority, TouchDesigner gameplay orchestration, and unrelated
  framework cleanup are frozen until the persona-lite loop passes.

The smallest product target is:

```text
bedroom -> dialogue -> compact exploration -> one encounter -> battle
-> buddy reaction -> bed/save -> visible narrative consequence
```

Every active item must state a binary acceptance gate before work begins. If a
session cannot finish the gate, record the blocker and stop rather than expanding
scope or creating a parallel system.
