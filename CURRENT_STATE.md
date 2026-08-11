# Current State - Melodia

Status labels: `Implemented`, `Partial`, `Broken`, `Planned`, `Research`, `Deprecated`.

> **READ THIS FIRST.** This file's older sections are a **historical record** of the
> environment-art platform work (materials, PCG, portfolio). The project has since **pivoted
> to a gameplay vertical slice ("First Dream")** as the primary track. The authoritative,
> current state lives in the gameplay docs listed below — not in the older sections of this
> file. See `DOC_INDEX.md` for the full map.

## Current State (2026-08-09) — handoff checkpoint

This checkpoint is the state to use when resuming on another PC. The active Unreal repository is
on local branch `codex/melodia-main-sync-20260809`; the final handoff-ledger commit containing this
file is the authority for the exact HEAD. The working tree contains the 2026-08-09 core-systems,
water/audio/Niagara, PCG musical-scene, VRM4U, Python, source, plugin,
asset, and handoff-document changes that are being committed in isolated batches.

- A clean `core_rhythm_data_smoke` evidence report was produced on 2026-08-09 and is tracked as
  `core_rhythm_data_smoke_report.json`; it is evidence of that smoke run, not a claim that the
  complete First Dream loop is playable.
- The 2026-08-09 water finalization handoff records a successful native C++ build; the remaining
  runtime/editor gates are still called out in the dated handoffs and must not be inferred from a
  compile alone.
- Generated Python caches and transient editor outputs remain ignored. The two stray
  `Content/Python/_*.uasset` files are local generated artifacts and are intentionally excluded
  from the handoff.
- Older branch, push, and checkpoint statements in the historical sections below are superseded by
  this 2026-08-09 checkpoint; use `Docs/Handoffs/PROJECT_HANDOFF_2026-08-09.md` for the live ledger.
- The exact C:→G: mirror and Google Drive results are recorded in the project handoff document.

For the resume sequence, read `Docs/Handoffs/PROJECT_HANDOFF_2026-08-09.md`, then
`Docs/Handoffs/SESSION_CLOSEOUT_2026-08-09.md`, `Docs/Handoffs/CORE_SYSTEMS_HANDOFF_2026-08-09.md`,
and `Docs/Reviews/CORE_GAMEPLAY_LOOSE_ENDS_2026-08-09.md`.

## Current State (2026-08-08) — T3D tooling landed, TD bridge OSC now works both directions, several gameplay fixes build-green

**Status update from the 2026-08-07/08 session.** A full editor rebuild succeeded 2026-08-08 with all
of the below (`Result: Succeeded, 0 errors`). This does not by itself prove the gameplay is playable —
see "Still open" below; the 2026-08-06 owner verification (dialogue not visible, battle non-functional)
has not been re-run, so treat that finding as still current until a fresh PIE walk says otherwise.

**T3D tooling (new):**
- `Docs/T3D_Baseline/` — 55 hash-verified T3D exports of the toon/material spine (10 master materials,
  27 material functions, 17 toon profiles, 1 MPC; 6,636,489 payload bytes / 5,303 nodes) plus
  `verify_baseline.py`, a drift gate that re-exports from the live editor and exits non-zero on drift.
  Committed under tracked `Docs/` (not `Saved/`, which is gitignored) — this is why every earlier T3D
  catalog was an untracked one-off.
- `Docs/T3D_Patterns/` — 5 parameterised T3D snippets (subsystem_call, delay_then_call, guarded_call,
  sequence_fanout, probe_print) + `t3d.py` CLI. Each verified by injecting into a live throwaway
  Blueprint: links formed, compile 0 errors.
- Monolith gained 2 actions (1328 → 1330): `blueprint/inject_nodes_t3d` and `blueprint/validate_nodes_t3d`
  — atomic T3D injection with a reflection pre-flight; a pre-flight failure leaves the graph untouched.
  Documented in `Plugins/Monolith/Docs/MONOLITH_GUIDE.md` Recipe 16 and `Docs/specs/SPEC_MonolithBlueprint.md`.
- **Gotcha:** `export_asset_text` defaults to a 256 KiB budget and returns a ~166-byte plain-text notice
  over budget while still reporting success — this produced the bogus 171-byte `BP_QuestNotification`
  stub in the 08-05 catalog. Always assert `full_bytes == returned_bytes`.

**TouchDesigner bridge:**
- The real TD project lives at `G:\EnvironmentPortfolio\_TouchDesigner\grandmaster_melodia\` (G: is a
  real mounted drive). `BS_GodFile\_TouchDesigner\` is a stale 2026-07-24 fragment — treat as dead.
  The `G:\` paths in `Content/Python/td_bridge.py` and `deploy/start_*.ps1` are correct, not bugs.
  `deploy/touchdesigner_validator.py`'s `PROJECT_ROOT` was wrongly pointed at `G:` (the UE project's
  drive) and has been repointed to `C:`.
- **TD→UE OSC (port 8000) now works** — it never had. Three defects fixed in
  `Content/Python/osc_server.py`: MPC writes were being made from the OSC listener's daemon thread
  (silent no-op) — now staged and flushed on the game thread via a Slate post-tick callback;
  `_get_mpc` used `find_object` on a package path and got the Package, not the asset; it called
  `MaterialEditingLibrary` (the MaterialInstance API) instead of `MaterialLibrary` (the parameter-
  collection API). Verified: all six of Bass/BassIntensity/Mid/Treble/TrebleIntensity/
  GlobalAudioReactivity move with TD's audio. New routes: `/audio/band/{sub,low,mid,high,air}`,
  `/audio/beat`, `/audio/pitch` (band ordering verified from TD's audiofilterCHOP cutoffs, ~80/250/1k/4k/8k Hz).
- **UE→TD OSC (port 9000) now emits** — previously dead because every `UMelodiaRhythmReactivitySubsystem::Notify*()`
  caller lived in quarantined MelodiaCore classes nothing instantiates. Two edges added:
  grade via `MelodiaJRPGPresentationRhythmComponent::HandleRhythmSessionCompleted`, beat via
  `MelodiaAudioReactivePresentationSubsystem::TickPresentation` on the beat-phase wrap, plus a 2 Hz
  idle heartbeat. Verified in PIE: 73 datagrams in 8s across all six `/rhythm/*` addresses.
- **Known constraint:** TouchDesigner only cooks while its timeline is playing (`me.time.play`) and its
  window is not minimised — paused/minimised delivers nothing. The Envoy MCP on 9870 is a manually-
  installed third-party Embody `.tox` and must be re-enabled after any TD restart.

**Gameplay:**
- B5 done: `Dreamstate_WakePortal` `DestinationLevelName` `/Game/ZenForestTest` → `/Game/EnvSandbox/Environments/L_KaleidoNave`, reload-verified.
  **Correction:** there is only ONE portal actor — `L_KaleidoNave` streams `L_Melodia_Dreamstate` as a
  sublevel, so earlier reports of "a portal in each level" were the same actor seen twice. Open risk:
  the portal now targets a level that streams the level it lives in — watch for a re-entry loop.
- Lane keys remapped D/F/J/K → Q/W/O/P to stop clashing with JRPG commands (Attack=J, Skill=K, Flee=F,
  MoveRight=D). The C++ change in `MelodiaBattleInputComponent` (MelodiaCore) is **inert** — that
  component is only created by `AMelodiaGameMode`, and the live game mode is `BP_MelodiaJRPGGameMode`.
  The effective fix was to `BP_BattleUI.OnKeyDown`'s four `Equal(Key)` nodes.
  **`WBP_MelodiaRhythmHighway`'s lane legend still displays the old D/F/J/K — not yet fixed.**
- A lane hit now pulses `MPC_Melodia_Palette` via `PulseImpact` (wired into `BP_BattleUI.OnKeyDown`).
  Before this, `PulseImpact()` had zero callers and RhythmPulse/Mid were permanently 0. Only
  `MF_Madoka` currently reads those params, so the visible surface stays narrow until
  `M_Master_Toon_Universal` also reads RhythmPulse. Not yet observed in a real battle — needs a PIE walk.
- `NotifySirRescued()` fixed by another agent at `MelodiaDungeonRunCoordinator.cpp:474`, tests extended
  in `MelodiaCoreRulesTests.cpp`. Previously Sir Melodious could never join the party.
- **Retraction:** the earlier claim that `MelodiaQuillTwilightDancer` was orphaned is false.
  `QuillDialogue` is a `TSoftObjectPtr`, so asset-registry `referenced_by` is `[]` by design for all
  five Quill assets. All five are wired in `ZenForestTest.umap`. Do not chase this again.

**Still open:**
- `WBP_MelodiaRhythmHighway` lane legend still shows D/F/J/K (fix pending, separate task).
- A2's beat/grade OSC edges are compiled and wired but not yet observed in a real battle — needs a PIE walk.
- `UMelodiaOrreryRegistry::IsSphereUnlocked` has zero callers; spheres gated at `RequiredPhase >= SirRescued` stay locked regardless of unlock state.
- 61+ commits ahead of origin; `github.com:443` still unreachable.

---

## Current State (2026-08-07) — Gameplay Vertical Slice is the primary track

**Status: production-foundation closeout before combat expansion. The gameplay is NOT yet playable.**

Per the owner's live verification on 2026-08-06, Quill dialogue is not visible, battle systems are
non-functional, and the game is unplayable. The 12 P0 foundation gates are unclaimed, Live Coding is
currently blocked, and push to `origin` is blocked by network connectivity to `github.com:443`.
Treat the "proven" bullets in older docs as **unverified** until PIE proof is recorded.

### Authoritative gameplay docs (read these, not the older sections below)

| Doc | Purpose |
|-----|---------|
| [`_VERTICAL_SLICE_SCOPE.md`](_VERTICAL_SLICE_SCOPE.md) | Current scope authority for the First Dream vertical slice |
| [`_SESSION_HANDOFF.md`](_SESSION_HANDOFF.md) | Most recent session's accomplished/pending/do-not-do list |
| [`_TASK_QUEUE.md`](_TASK_QUEUE.md) | Live, granular task tracker — P0/P1/P2/P3, per-task status/agent |
| [`_DECISION_LOG.md`](_DECISION_LOG.md) | Append-only strategic decisions |
| [`_ROADBLOCKS_2026-07-31.md`](_ROADBLOCKS_2026-07-31.md) | Consolidated roadblock inventory + contradiction register |
| [`Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md`](Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md) | Canonical wiring source of truth (verified against source headers) |

### The loop

```text
sanctuary conversation
  -> authored departure
  -> short dream traversal
  -> one stock JRPG encounter
  -> typed terminal result
  -> narrative consequence
  -> stable checkpoint/save
```

### Playable route (target)

`L_MelusinaMorning` → `L_Melodia_Dreamstate` → `L_KaleidoNave`

Real paths:
- `/Game/Melodia/Levels/Opening/L_MelusinaMorning`
- `/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate`
- `/Game/EnvSandbox/Environments/L_KaleidoNave`

### Core systems (build-green, runtime-unproven unless noted)

| System | Status | Notes |
|--------|--------|-------|
| QuillScript dialogue | Build-green | NPC interaction + typed terminal results; not PIE-verified |
| Stock JRPG combat | Build-green | Turn/target/damage/result authority (TurnBasedJRPGTemplate) |
| Rhythm combat | Build-green | Harmonix clock + `UMelodiaRhythmCombatSubsystem`; optional |
| Canonical save/load | Build-green | `BP_JRPGSaveGame` slot; process-restart round-trip unproven |
| Travel authority | Build-green | `UMelodiaTravelSubsystem`; allowlist validation |
| Input authority | Build-green | `UMelodiaInputContextSubsystem`; runtime push/pop balance unverified |
| Melody Token economy | In progress | `UMelodiaTokenWalletSubsystem`; pickups/HUD are Blueprint (Kiro) |
| Co-op skills | Partial | Petal Cadence/Skybound Refrain/Resonance; conditional bonus unwired |

### Build status

- **Last rebuild:** 2026-08-03 14:38, 12.66s, **0 errors 0 warnings**.
- **Regression gate:** `Automation RunTests Melodia` = 49 tests. NPC interaction now passes. 2 roguelike failures known/P3.
- **Live Coding currently BLOCKED** (2026-08-06): `editor:trigger_build` fails ~30s in with a blocking modal. Environment issue, not agent-caused. Until a real rebuild or Live-Coding fix, the Monolith enum-pin fix cannot be baked.

### Open P0 foundation gates (all runtime-unproven)

- Identify instantiated stock battle widget package at runtime
- Prove Attack/Skill/Item/Flee mouse, keyboard, controller parity
- Pass Victory/Defeat/Fled/unavailable result matrix
- Create/load canonical `BP_JRPGSaveGame` slot across process restart
- Prove one narrative flag + one reward restore without duplication
- Load canonical JRPG slot with Quill unavailable, preserve state
- Route missing/unknown script to authored safe location
- Test interpreter invalidation during terminal-result broadcast
- Keep manual saving disabled during active narrative battle
- Wire Main Menu New Game/Continue/Load to canonical JRPG GameInstance
- Repair or revise `Morning_RoomShell` validator contract
- **Launch-test the packaged build** (only open packaging item)

### Git recovery + collaborator environment (2026-08-05)

- `BS_GodFile/.git` is the active Unreal repository on branch `sonnet-core-mechanics-20260808`; the
  final handoff-ledger commit containing the current handoff is the authority, and the C: and G:
  tracked worktrees are being refreshed to match it.
- The active HEAD tree is readable and Git LFS checks pass on both local copies. Repository-wide
  fsck now reports one inherited missing/broken historical tree after twelve valid historical
  objects were restored from the G: mirror. No history rewrite or prune was performed.
- Checkpoint commit `6154cc1e` captures full live working tree on recovered history.
- Push to `origin` is not verified: SSH/HTTPS access to GitHub is unavailable from this environment,
  and no remote push has been performed.
- Added collaborator tier model artifacts: `deploy/collaborator_onboarding.sh`, `deploy/validate_collaborator_setup.sh`, and updated `COLLABORATOR_SETUP.md` and `DOC_INDEX.md`.

## MeshBlend integration added to `M_Master_Toon_Universal` (`Implemented`, additive/safe)

Wired `MF_MeshBlend_Activator_Index_1` (real, already-authored function — reads `PerInstanceCustomData` index 1 as a per-instance "AutoBlendID" driven by runtime code like `BP_MeshBlend_Activator`, or falls back to a static scalar via its own internal "Use Static Value" switch) into the existing `LayerManualMix → Lerp(Alpha)` connection, gated behind a **new** `bMeshBlendActivator_Active` static switch (default `False`). 916 → 918 expressions, 10 → 11 top-level switches (plus the function's own internal "Use Static Value" switch, exposed on instances).

**Does not touch `r.MeshBlend.Enable`** (still `0`, disabled since June 20 for the documented UE5.7-vs-5.8 plugin incompatibility) — this only calls a standard material function reading per-instance custom data, not the plugin's proprietary runtime rendering path, so it works regardless of that cvar. Verified additive/non-disruptive before touching production: prototyped identically in `_Scratch/` first, confirmed via instance readback that toggling the new switch and its `AutoBlendID` param work correctly, then applied the same proven wiring to production and re-verified (BSDF intact, all 10 original switches unchanged, `LayerManualMix` default unchanged at 0.5, new switch defaults off — zero behavior change for any existing instance unless explicitly opted in).

**How to use it**: on any instance, set `bMeshBlendActivator_Active=True`. With `Use Static Value=False` (default), the blend follows `PerInstanceCustomData` index 1 set at runtime (e.g. by a `BP_MeshBlend_Activator` component on an ISM). With `Use Static Value=True`, it uses the `StaticAutoBlendID`/`AutoBlendID` scalar param instead — useful for authoring/testing without a live activator actor.

## Sakura Level Push Stage 6 complete: real NASA starmap wired in, constellation VFX confirmed already-correct (`Implemented`)

- **Found real, already-imported 4K NASA textures never used**: `/Game/EnvSandbox/Materials/Space/Textures/T_NASA_StarMap_4K` (4096×2048, real equirectangular starmap projection, confirmed via `inspect_texture_channels`) and `T_NASA_MilkyWay_4K`. The `StarMap` param on `MF_SpaceParallax`/`MI_Show_CelestialNebula` had been reusing a sparkle alpha texture (`T_Spark_Twinkle8`) as a placeholder stand-in the whole time.
- **Wired `T_NASA_StarMap_4K` into `MI_Show_CelestialNebula`'s `StarMap` param**, verified via readback.
- **`NS_ConstellationDraw`** (`/Game/EnvSandbox/VFX/Systems/Sakura/`, real Sakura-specific system, 10 modules, real `DreamIntensity`/`DreamTwinkleSpeed`/`DreamVisibility` user params, compile-clean) checked and confirmed **already correctly built** — uses its own dedicated glow sprite material (`M_StardustParticle_Glow`), not the `StarMap` texture. This is architecturally correct: a twinkling star sprite needs a small glow/point-light texture, not a full equirectangular NASA image — that belongs on surface/nebula materials (where it's now wired). No change needed here; the "tie NASA starmap to Sakura effects" ask is satisfied by the `MI_Show_CelestialNebula` wiring, which is the actual material-level integration point, not the sprite VFX.

## Vertex blending for trimsheet use (Stage 5): `MF_VertexPaintBlend` exists, real inputs understood, wiring scoped not attempted (`Partial`)

Confirmed no vertex-color-driven blend exists on `M_Master_Toon_Universal` right now (only `MaterialExpressionVertexNormalWS` present, no `MaterialExpressionVertexColor`, no function calls referencing paint/vertex). But `/Game/EnvSandbox/Materials/Functions/MF_VertexPaintBlend` **does exist as a real, complete, already-authored function** — git history shows it was wired into the Universal master once (`a2f9eec Wire MF_VertexPaintBlend into Universal master`) and apparently dropped during a later `regenerate`/`finalize`/`lock` pass (several such commits followed).

**Function structure (inspected via `get_material_function_expressions`, 24 exprs)**: takes 4 `Vector3` inputs (`LayerR`/`LayerG`/`LayerB`/`LayerA`), samples `MaterialExpressionVertexColor`, extracts each RGBA channel via `ComponentMask` as a blend weight, multiplies each Layer input by its channel weight, sums all 4, divides by the total weight (normalized weighted blend) → single `BlendedColor` output. This is a genuine 4-way hand-paintable vertex-color blend, exactly suited for trimsheet work (paint which of up to 4 layers shows where, per-vertex).

**Not wired in this pass, deliberately**: the Universal master's Layer A/B/C system has an extensive history of `Lock`/`Finalize` commits — touching its core blend chain live carries real risk of breaking already-tuned, portfolio-ready behavior. The safe path (matching this session's own proven MF-extraction discipline, `MF_IridescenceSheen`) is to prototype the wiring in `_Scratch/` first — feed it real LayerA/LayerB/LayerC/BaseTint color sources, verify `BlendedColor` propagation via readback, and only then wire it into production as a new **additive, switch-gated** feature (a new `bVertexPaintBlend_Active` static switch, default off, so existing tuned behavior is unaffected when disabled) — not a replacement for the existing height-based `LayerBlend` system. Real next step, precisely scoped, not attempted blind.

## Real gotcha found: `EditorAssetLibrary.save_asset(path)` can silently no-op on in-place parameter edits

While expanding iridescence/sheen/sparkle on 3 Sakura instances, `set_material_instance_scalar_parameter_value`/`set_material_instance_vector_parameter_value` calls correctly updated the in-memory value (confirmed via immediate readback), but the follow-up `EditorAssetLibrary.save_asset(path)` (default `only_if_is_dirty=True`) silently did nothing — the on-disk `.uasset` file timestamp didn't change at all. The parameter setters don't reliably mark the package dirty in this UE Python binding, at least for existing instances edited with *only* scalar/vector parameter changes (no texture change, no `recompile_material`, no parent reassignment). Confirmed narrow scope via spot-check: every other material save earlier this same session (new instance creation via `create_asset` + `set_material_instance_parent`, or texture parameter changes) genuinely persisted — this only bit in-place scalar/vector-only edits on already-existing instances.

**Always call `save_asset(path, only_if_is_dirty=False)` for in-place material instance parameter edits** — don't trust the default. Verify with a real file-timestamp/size check (`ls -la` before/after, or `git status`) after any such save, not just an in-memory readback — an in-memory readback will report the new value correctly even when the disk write silently failed, giving false confidence.

## IMPORTANT: the capture-pipeline fix needs `trigger_build` re-run after every editor restart until a real rebuild happens

The `r.PSOPrecaching` capture fix (committed in `Plugins/Monolith/Source/MonolithEditor/Private/MonolithEditorActions.cpp`) was applied via **Live Coding**, which patches the *running process* only — it does not get baked into the on-disk `UnrealEditor-MonolithEditor.dll`. Confirmed directly: after a routine editor crash + `-unattended` relaunch (a fresh process, loading the original unpatched DLL from disk), `capture_material_grid` immediately showed the checkerboard fallback again — the source fix is safely committed to git and structurally correct, but the *currently running* editor process wasn't using it until Live Coding was re-triggered in this new session too.

**Until a proper full (non-Live-Coding) rebuild happens, call `editor:trigger_build` once after every fresh editor launch, before trusting any capture output.** Verify with a quick `capture_material_grid` test on a known material after the build reports `patch_applied=true` — a checkerboard result means the patch didn't take (or this is a stale process), not that the fix itself is wrong.

## Sakura Level Push Stage 3: real mesh-alignment bug found + fixed in `PCG_Sakura_Showcase` (`Implemented`)

Checked the 2 loadable Sakura PCG graphs (`PCG_Sakura_PetalDrift` remains an orphaned/unresolvable asset in this registry view — same drift pattern as `PCG_RockScatter` documented earlier, not touchable). `PCG_SakuraGrove`'s `PCGTransformPointsSettings` nodes were already correct (`rotation_min=(0,0,0) → rotation_max=(0,360,0)`, i.e. yaw-only randomization, upright vegetation). `PCG_Sakura_Showcase`'s 3 spawner chains had a genuine bug: `rotation_max=(359,0,0)` — **pitch** randomized instead of **yaw**, meaning every scattered mesh (`SM_Block_Cube_1`/`Cone`/`Cylinder`) got randomly tipped/tumbled onto its side instead of standing upright and just spinning around its vertical axis. Fixed to `rotation_min=(0,0,0) → rotation_max=(0,359,0)`, matching the correct `SakuraGrove` pattern. Verified via a fresh asset reload (not just same-session memory) after the fix.

**Real API gotcha found while fixing this**: `unreal.Rotator(0, 359, 0)`'s positional constructor does **not** reliably map to `(pitch, yaw, roll)` when passed to `set_editor_property` on a PCG settings struct field — the value silently failed to apply (verified: immediate same-object readback after the "successful" set call still showed the old value, no exception thrown). Fix: construct the `Rotator` via `unreal.Rotator()` (no-args) then per-field `set_editor_property('pitch', ...)`/`'yaw'`/`'roll'` before assigning the whole struct — that path took correctly. Use this pattern for any future `Rotator`-typed PCG property write, not the positional constructor.

## Sakura Level Push Stage 2 complete: real Nanite petal mesh imported, wired into both Sakura Niagara systems (`Implemented`)

- **Imported `sakurapetal.usdz`** (user-provided, `C:\Users\froma\Downloads\sakurapetal.usdz`) via `unreal.UsdStageImportFactory`/`AssetImportTask`, forcing `nanite_triangle_threshold=0` (the importer's default is `2147483647`, i.e. Nanite effectively off by default — a real gotcha worth remembering for any future USD import). Landed at `/Game/EnvSandbox/Meshes/Sakura/SM_SakuraPetal_Nanite/StaticMeshes/SM_UMesh_PolySphere5` — generic auto-name from the source USD authoring tool (not literally a sphere; per the standing `rename_asset` ban, left as-is rather than renamed). Verified real: 1162 triangles, real-world petal scale (~2cm elongated asymmetric bounds, not a placeholder primitive), `nanite_settings.enabled=True`.
- **`NS_SakuraGroundPetals`** (real, working system — 12 modules, mesh renderer already present): swapped its mesh from `/Engine/BasicShapes/Plane` (flat card fallback) to the new Nanite mesh via `set_renderer_mesh`. Compile-clean (0 errors/warnings), verified via readback.
- **`NS_SakuraPetals`** (confirmed to be an empty "Fountain" scaffold, 0 modules, no renderers — matches the documented pattern of other loop-built `NS_*` systems never being finished) was built fresh using `import_system_spec`, inheriting cleanly from the real project template `/Game/EnvSandbox/VFX/Templates/E_GroundPetalsPile` (same base as the working GroundPetals system) — **do not pass a `modules` array in the spec when an `emitter_asset`/template is already given**, it gets added on top of the template's own inherited modules instead of overriding them, producing duplicated/conflicting modules (confirmed by trial: first attempt produced 2x every module, some enabled/disabled inconsistently, which was the actual cause of a black preview — not a spawn-rate or mesh issue). Second attempt (template reference + renderer override only, no modules list) compiled with op-counts exactly matching GroundPetals (183/22 spawn, 87/32 update) — genuine structural parity with proven-working content.
- **Visual verification limitation (not a system bug)**: both systems render fully black via `preview_system`/`capture_scene_preview(asset_type=niagara)`, confirmed via a proper control test — even the untouched, known-good `NS_SakuraGroundPetals` shows identically black regardless of camera position/distance. Root cause: `CaptureNiagaraFrame`'s preview scene is deliberately fully unlit (`bDefaultLighting=false`, zero light/sky brightness — tuned for evaluating glowing/emissive VFX like fire and sparks), and `M_SakuraPetal` is a plain lit material (`Tint` vector param only, no emissive, no texture) — a lit mesh material genuinely cannot render visible in a zero-light scene, independent of whether particles are spawning correctly. Verified structurally instead (compile diagnostics, op-count parity with known-working content, mesh/material assignment readback) — this is the appropriate substitute verification for this specific gap, not a shortcut.
- **Real follow-up worth flagging for Stage 4/5 (material work)**: `M_SakuraPetal` currently has no texture and no emissive at all — just a flat white tint. Once real in-level/in-editor viewport verification is possible, this material likely needs actual petal-appropriate texture/color work, separate from the mesh swap done here.

## CLEAN REVIEW CHECKPOINT 2026-07-02 (afternoon session close): `M_Master_Toon_Universal` finalized as `Implemented`, stable

Final live re-verification before closing this session's material work: **916 expressions, 10 static switches** (`bUseSeparateRoughnessMap`/`bUseSeparateMetallicMap`/`bUseHeightToNormal`/`bLayerA_Active`/`bLayerB_Active`/`bLayerC_Active`/`bSparkleAdvanced`/`bSheenUsesNormal`/`UseUDSTimeOfDay`/`bNikkiHero`), all traced with 0 orphans in an earlier pass. **0 duplicate parameter declarations** across 241 total param nodes / 241 unique names — the "duplicate material params" item in Known Technical Debt does not currently manifest on the master itself (may have referred to instance-level duplication, or was already resolved by an earlier session). BSDF (`MaterialExpressionSubstrateToonBSDF`) present and fully wired (BaseColor/Metallic/Roughness/Normal/EmissiveColor all non-null, confirmed earlier this session). No changes made this pass — this is a verification/finalization checkpoint, not a rebuild. **Status: stable, ready for production/portfolio use as-is.**

Everything touched this extended session (overnight autonomous + afternoon) is committed with clear reasoning per-commit; nothing of this session's work is left uncommitted. Pre-existing uncommitted drift from other parallel tooling sessions (`generate_portfolio.py`, `material_family_manifest_full.py`, several PCG graphs, `Docs/AgentMemory/Decisions.md`, `NEXT_ACTIONS.md`, `_github_deploy`, a few Zen/Showcase material instances) remains untouched and uncommitted — not this session's work, not verified, left for whoever owns those changes.

## `capture_material_grid`/`capture_scene_preview` FIXED (2026-07-02, `Implemented`) — root cause was `r.PSOPrecaching`, patched in Monolith source, verified live

Was `Broken` for the whole overnight+afternoon session (checkerboard `WorldGridMaterial` on every single capture). Root-caused and fixed at the source this session:
- **Real root cause**: UE5.8's default async PSO precaching. `RenderAndSaveCapture()` (the shared helper behind all 3 capture actions) spawns a mesh component into a transient preview scene and captures it in the same game-thread call — the primitive has no PSO ready yet for its material/vertex-factory/render-pass combination, so the renderer substitutes a placeholder for that frame. Since the preview scene never lives past one frame, this happened on *every* capture, not intermittently.
- **First hypothesis tested and disproven**: async shader compilation not finished. Added `GShaderCompilingManager::FinishAllCompilation()` + world ticks, recompiled via Live Coding, tested — still checkerboard. Not reverted (harmless synchronization safety net), but not the actual fix.
- **Real fix, confirmed via a cheap console-variable A/B test before touching code again**: `r.PSOPrecaching 0` immediately fixed the capture. Implemented properly in `Plugins/Monolith/Source/MonolithEditor/Private/MonolithEditorActions.cpp`'s `RenderAndSaveCapture` — scopes the cvar to 0 only around the `CaptureScene()` call, saving/restoring the prior value (not a global editor behavior change). Compiled via Live Coding, verified: real toon-shaded material renders correctly (banded rings + sparkle texture on `M_Master_Toon_Universal_Inst`, not checkerboard), and the cvar correctly reads back to `1` after the call.
- **Bonus finding, worth remembering**: `/Engine/EngineMaterials/DefaultMaterial` is genuinely checkerboard-patterned by design (not a placeholder-for-missing-material indicator in this context). The overnight "stock engine sphere with no custom material" control test used to conclude the bug was content-independent was actually rendering *correctly* the whole time — a misleading baseline, not a confirming one. Don't reuse that specific control test to diagnose a similar issue without re-verifying what the control asset's real material looks like first.

**Status: trust `capture_material_grid`/`capture_scene_preview`/`capture_with_overlay` again** — this was the gate blocking visual verification for iridescence tuning, instance organization, and Niagara tie-in work; all now unblocked.

## Spline-blocked Baroque `*Ex` spot-check: real fix confirmed on 1, blocked on another, unresolved on a third (afternoon session)

Spot-checked the `BP_PathSplineProvider` direct-host spline pattern (proven this session on `PCG_WallDetail`) against 3 of the 5 spline-blocked Baroque `*Ex` graphs. Spawned `BP_PathSplineProvider_C`, gave it a real 3-point spline (`unreal.SplineComponent.set_spline_points`, plain `Vector` list — not `SplinePoint` structs, that API throws a nativize error), assigned each graph, generated:
- **`CorniceEx`: genuinely fixed.** 0 → 40 instances. Confirms the direct-host spline pattern is the correct fix for graphs ending in a direct `PCGStaticMeshSpawnerSettings` (no subgraph indirection).
- **`BalconyEx`: still 0, blocked by an opaque `PCGSubgraphSettings`.** Its `PCGExSplineToPathSettings → PCGExOffsetPathSettings → PCGSubgraphSettings` chain generated without crashing (spline input correctly wired, confirmed via `PCGGraphInputOutputSettings` edge trace), but the terminal `PCGSubgraphSettings` node's `subgraph` property is C++-protected and unreadable via Python reflection — can't trace what's inside it without opening it in the PCG Graph Editor UI directly.
- **`NaveVaultEx`: still 0, cause not identified.** Same spline-host fix applied (no subgraph in its chain — `PCGExSplineToPathSettings → PCGExPathHatchSettings → PCGStaticMeshSpawnerSettings`), still produced 0 instances. Not diagnosed further this session — the spline-hosting mechanism itself is confirmed correct (proven on CorniceEx), so the remaining blocker is specific to `PCGExPathHatchSettings`'s own config, not the spline input.

`PilasterEx`/`GothicCorridorEx` not re-tested this pass (time-boxed spot-check, not exhaustive). Real, verified, partial progress — 1 of 5 graphs genuinely unblocked, 2 more require deeper in-editor tracing than a spot-check allows.

## Real cathedral grammar system built + verified M1-M3 (afternoon session, `Partial` — M4/M5 need the user's own eyes)

`Content/Python/build_cathedral_grammar.py` — the genuine version of what `PCG_FractalButtress_BS`/`PCG_M1_GrammarNave_BS` were supposed to be, built fresh (does NOT touch those legacy scaffolds). A real grammar: `ROLES = {"bay": ..., "buttress": ..., "pinnacle": ...}` dispatched by role. A real fractal: `_rule_buttress` recurses into a smaller self-similar copy of itself (scale halves each level), terminating into `_rule_pinnacle`. `bay_count` controls spine length, `buttress_depth` controls recursion depth — both genuinely drive instance count via a hand-derived formula (`predicted_instance_count()`), not a hardcoded scatter.

Milestone-verified per the plan's staged discipline:
- **M1** (`bay_count=1, buttress_depth=2`): 12 instances, exact match to the formula.
- **M2**: all 3 roles produced boxes in the M1 test (bay=4, buttress=6, pinnacle=2) — dispatch table genuinely reached.
- **M3** (`bay_count=8, buttress_depth=4`): 128 instances, exact formula match; sampled real-world Y-bounds span exactly 4200cm = `(bay_count-1) × BAY_LEN` — confirms genuine scale-with-parameter behavior, not a bigger fixed number.
- **M4/M5 not attempted** — need a human at the keyboard looking at the actual viewport (does the recursive buttress silhouette read as a real fractal facade?) and material/mesh judgment calls. Asset: `/Game/EnvSandbox/PCG/Styles/Baroque/PCG_CathedralGrammar_Nave`, currently unit-cube blockout.

**Real bug found in shared tooling**: `pcg_graph_builder.load_or_create_graph(force=True)` calls `PCGGraph.remove_nodes()` to clear an existing graph before rebuilding — **that method is a no-op in this engine build**. Confirmed directly: rebuilding `PCG_CathedralGrammar_Nave` from `bay_count=1` to `bay_count=8` left BOTH old and new `PCGCreatePointsSettings`/`PCGStaticMeshSpawnerSettings` node pairs in the graph (4 nodes total, silently doubling instance counts on the M3 first attempt: 12 real + 128 real = confusing partial reads). Same bug category as the already-documented `build_material_graph` clear-existing bug (`monolith-build-material-graph-wipes-existing-graph-bug` memory). **Worked around locally** in `build_cathedral_grammar.py`'s `build_nave()` by clearing nodes explicitly (`graph.remove_node(n)` per node) instead of trusting the shared helper — **this same bug likely affects any other script using `load_or_create_graph(force=True)` for a REBUILD** (first-time builds are unaffected since there's nothing to clear). The 6 Escher room generators (`build_escher_relativity_room.py`) were each built exactly once this session and are unaffected today, but would double up identically if anyone reruns `build_all()` a second time without the same fix. Fix `pcg_graph_builder.clear_graph_nodes()` itself (not just work around it per-script) as a real next step — check whether `remove_node()` per-node (proven working here) is the right general fix, or whether there's a different correct API.

Checked the Blender addon for more translatable algorithms after the 6th Escher generator. `build_gb_umemoto_vault_cluster` (line 7300, barrel-vaulted chamber grid) is a real, well-formed generator, but unlike the 6 already-ported Escher rooms (pure box-placement math), its vault ceiling uses a genuine curved sweep (`GeometryNodeCurveArc → GeometryNodeCurveToMesh` with a rect profile) — not directly representable as a `PCGCreatePointsSettings` box list without first discretizing the arc into N rotated box segments (the same technique already used for Penrose Loop's curved arms, just needs deliberate design of the segment count/angle math here). Worth doing well rather than rushing an approximation blind at the end of an unattended session — scoped as a precise next step, not attempted. Other remaining `build_gb_*` functions (`umemoto_terrace/lattice_block/fortress_room`, `woods_*`, `room_circular/apsidal/rotunda`, `corridor_arc*`) not yet individually assessed for the same curved-vs-box distinction.

## Escher room generators: now 6 total (2 more added 2026-07-02 near dawn)

`Content/Python/build_escher_relativity_room.py` (name is historical, module now covers all 6). Added `build_belvedere()` and `build_waterfall()`, translating `build_gb_escher_belvedere`/`build_gb_escher_waterfall` from the Blender addon — Escher's two most iconic impossible-structure pieces (Belvedere 1958, Waterfall 1961), previously read this session but not yet ported. Both live-verified via the proven spawn/generate/count-in-separate-call pattern: `PCG_EscherBelvedere` 17 instances, `PCG_EscherWaterfall` 16 instances, both exactly matching build output, no crash. Full set: Relativity Room, Penrose Loop, Recursive Room, Gravity Shift Corridor, Belvedere, Waterfall — all in `/Game/EnvSandbox/PCG/Styles/Escher/`, all built from real translated transform math, not hand-placed test points.

## PLAN STEP 3 SCOPING 2026-07-02 (overnight): `AncientTempleRuins` migration needs a different script pattern than `migrate_props_from_source.py`

Inspected `G:/ueprojects/Shepherd_Brennan_10/Content/AncientTempleRuins/` structure: it's organized by **asset type** (`Blueprints/`, `Materials/`, `Textures/`, `Environment/{Construction,Foliage,GroundScatter,Prop,Rock}/`), not by **self-contained per-prop subfolder** like `migrate_props_from_source.py`'s existing `SOURCES` (MagiciansLibrary, Melodia) assume. That script's material-slot repair heuristic ("if a copied subfolder has exactly 1 material, reassign every mesh's slots to it") doesn't apply here — meshes and their materials live in separate top-level folders with many-to-many relationships, not a 1-mesh-1-material-per-folder pattern.

Migrating this correctly needs: (1) raw-copy `Materials/`, `Textures/`, and all of `Environment/*` together (not per-subfolder), (2) a different repair pass that resolves each mesh's actual per-slot material reference (not just "the 1 material in this folder") — likely by reading each source `.uasset`'s dependency list via `AssetRegistryHelpers` before copying, then remapping paths post-copy rather than guessing from folder co-location. Not attempted tonight — a broken migration would produce assets with silently-wrong materials I can't visually verify without the user, and is worse than not migrating at all. Real next step, scoped precisely, not just "do the migration."

## PLAN STEP 2 FINDING 2026-07-02 (overnight, `Broken`, honest report before any fix attempt): `PCG_FractalButtress_BS` and `PCG_M1_GrammarNave_BS` are NOT working recursive/grammar systems — they're scaffolded placeholders

Live-inspected both (safe, static node/property reads, no generate calls needed):

- **`PCG_M1_GrammarNave_BS`** (12 nodes: `PCGCreatePointsSettings → PCGSubdivideSegmentSettings → 5x PCGAttributeFilteringSettings → 5x PCGStaticMeshSpawnerSettings`): the shape looks like real architectural grammar (a spine, subdivided into segments, routed by attribute filters to 5 different element-type spawners) — but the `PCGCreatePointsSettings` source has **only 1 point** (not a spine), and **4 of the 5 `PCGStaticMeshSpawnerSettings` nodes have no mesh assigned (`None`)**. Only 1 of 5 has a mesh, and it's `/Engine/BasicShapes/Sphere` — an engine primitive placeholder, not real content.
- **`PCG_FractalButtress_BS`** (4 nodes: `PCGCreatePointsSettings → PCGSubdivideSegmentSettings → PCGAttributeFilteringSettings → PCGStaticMeshSpawnerSettings`): same pattern — single seed point (no actual recursive/self-similar subdivision visible), 1 spawner using `/Engine/BasicShapes/Cylinder`, another placeholder primitive.

**Conclusion: the "grammar"/"fractal" naming reflects design intent, not implemented behavior.** This is NOT the genuine massive-scale recursion lever the plan hoped for — it's an early scaffold (single-point source, mostly-unwired spawners, placeholder primitive meshes) that was never finished. Building a real self-similar/recursive architectural generator here would be new work, not a fix — a good candidate for a dedicated focused session (ideally leaning on the math-translation technique already proven with the 4 Escher room generators) rather than a late-night patch. Not attempted tonight; flagging honestly per the plan's Step 2 instruction to report the traced structure before proposing changes.

## RESOLVED 2026-07-02 (overnight): unattended-boot hang was TWO stacked issues, both fixed

The editor appeared to "crash on relaunch" repeatedly overnight, but the real problem for most of the night was a **hang**, not a crash: process alive, memory flat, log frozen — not the PCGExCreateShapes bug (that only fires when a Baroque graph is generated, and boot never got that far).

1. **`GaeaUnrealTools` plugin version mismatch** (built for 5.7.0, project runs 5.8) logs a warning right before the hang point every time. Fixed: disabled it in `BS_GodFile.uproject` (`"Enabled": false`).
2. **A second, separate blocking modal** (`LogMonolith: Warning: MODAL_OPEN ... title='' text=''`) opens immediately after `LogInit: Display: Engine is initialized` — Monolith itself logs this and confirms MCP is unresponsive until dismissed, which is exactly the observed symptom (frozen log/memory, `monolith_status` failing). With no one at the keyboard overnight, this blocked every relaunch after the Gaea fix too.

**Fix: launch with the `-unattended` command-line flag**, which auto-dismisses blocking modal dialogs. Confirmed working — `monolith_status` responded immediately after an `-unattended` launch where every prior relaunch attempt (via `cmd.exe /c start`, direct exe, and PowerShell `Start-Process` without the flag) hung indefinitely.

**Going forward, always launch this project as:**
```powershell
Start-Process -FilePath "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" -ArgumentList '"G:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject"','-unattended' -PassThru
```
via the PowerShell tool (not Bash's `cmd.exe /c start`, which did not reliably produce a surviving process in this environment — verify with `Get-Process -Id $p.Id`, not just `tasklist`, immediately after).

## CRASH BUG FOUND 2026-07-02 (overnight, `Broken`): one of the 9 Baroque `*Ex` graphs contains a `PCGExCreateShapes` node that hard-crashes the engine on generate

Root-caused via log inspection (`Saved/Logs/BS_GodFile.log`) after two consecutive editor crashes during the Step 1 batch-verification sweep. Crash signature: native C++ crash (unrecoverable from Python, `try/except` does not help) inside `UnrealEditor-PCGExElementsShapes.dll!PCGExCreateShapes::FProcessor::OutputPerSeed()` → `PCGExPointArrayDataHelpers::SetNumPointsAllocated()` — a background-worker-thread crash during `ParallelFor`, consistent with a bad/negative point count being requested by a `PCGExCreateShapes` node. Timestamp of the crash lines up exactly with the batch-spawn-and-generate script that triggered all 9 `TEST_Baroque_*Ex` actors in one shot (`AtriumEx/BalconyEx/ColonnadeEx/CorniceEx/FacadeEx/NaveVaultEx/PilasterEx/RotundaEx/EntryEx`) — meaning **one of these 9 graphs, not yet identified, contains the crashing node**.

**Do not batch-generate these 9 graphs again.** Test them ONE AT A TIME with an editor-status check between each (`monolith_status`), so a crash can be attributed to the specific graph instead of taking down the whole batch. Once identified, either delete/disable the `PCGExCreateShapes` node in that graph or replace it with a vanilla `PCGCreatePointsSettings` node (the pattern already proven working in the Escher `*Ex` fixes and the 4 new Escher room generators).

`GothicCorridorEx`'s real path resolved: `/Game/EnvSandbox/PCG/Styles/Baroque/PCG_GothicCorridorEx` (no `Baroque` prefix, unlike its 9 siblings).

**Step 1 (Baroque `*Ex` sweep) complete, live-verified, all 10 graphs:**
- **Risky (contains `PCGExCreateShapesSettings`, NOT generated this session, avoid batch-testing)**: `AtriumEx`, `ColonnadeEx`, `FacadeEx`, `RotundaEx` — all 4 share the same `PCGVolumeSamplerSettings → PCGExCreateShapesSettings → PCGExCreateShapeGridSettings → ... → PCGSubgraphSettings` shape. One (unidentified which) of these 4 is confirmed to hard-crash the engine on generate.
- **Safe, tested, 0 instances (need a spline/path input — same root cause as the ~13 Bezier-blocked graphs elsewhere, not yet fixed)**: `BalconyEx`, `CorniceEx`, `NaveVaultEx`, `PilasterEx`, `GothicCorridorEx` — all use `PCGExSplineToPathSettings` or similar as their first node, which needs a real spline actor input (the `BP_PathSplineProvider` pattern), not a bare `PCGVolume`.
- **Safe, tested, WORKING**: `EntryEx` — 845 instances, uses the plain `PCGVolumeSamplerSettings → PCGStaticMeshSpawnerSettings` pattern (the already-proven "Volume" pin fix).

**Step 1 fully closed. Crash bug isolated to a specific node PATTERN, not the `PCGExCreateShapesSettings` node type in general:**
- **Crash confirmed**: `AtriumEx`, `ColonnadeEx`, `RotundaEx` — all 3 share `PCGVolumeSamplerSettings → PCGExCreateShapesSettings → PCGExCreateShapeGridSettings → ...`. All 3 crashed the engine identically on generate; all 3 recovered cleanly via `-unattended` relaunch (~1 min each).
- **Safe (no crash), but non-functional (0 instances)**: `FacadeEx` — same `PCGExCreateShapesSettings`/`PCGExCreateShapeGridSettings` pair, but fed from `PCGSurfaceSamplerSettings` instead of `PCGVolumeSamplerSettings`. Strongly suggests the crash is specifically about what a bare `PCGVolume`'s volume sampler feeds into `CreateShapes` (likely a degenerate/huge point count from the default volume bounds hitting `SetNumPointsAllocated` with a bad value) — not a defect in the `CreateShapes`/`ShapeGrid` nodes themselves.
- Static Python reflection on `PCGExCreateShapesSettings` properties didn't work cleanly for diagnosis (most fields are C++-protected, `dir()`-based enumeration throws on protected getters) — direct one-at-a-time live testing was faster and more conclusive once `-unattended` made crash recovery cheap.

**Afternoon follow-up attempt (negative result, informative)**: tried the leading hypothesis that `unbounded=True` on the `PCGVolumeSamplerSettings` feeding `PCGExCreateShapesSettings` was generating an astronomically large 3D voxel point count (all 3 crashing graphs share `unbounded=True` + small `voxel_size` 600×600×100cm; the one safe-but-non-functional graph, `FacadeEx`, uses a 2D `PCGSurfaceSamplerSettings` instead, which wouldn't blow up the same way even with `unbounded=True`). Set `AtriumEx`'s `unbounded` to `False` and tested generate with a real, sanely-scaled `PCGVolume` actor (scale 20/20/10, ~2000×2000×1000cm — a modest ~90-voxel volume at that voxel size) instead of a bare default-bounds test volume. **Still crashed identically.** This rules out both the "unbounded 3D blowup" theory and the "test-harness artifact" theory from the overnight write-up — the bad value is genuinely internal to `PCGExCreateShapesSettings`'s own config (seed/shape count fields), not something upstream feeds it. Reverted `unbounded` back to `True` on `AtriumEx` afterward (the change didn't fix anything and shouldn't be left as an unexplained edit to real content). Confirms the overnight assessment: this needs in-editor `PCGExCreateShapesSettings` parameter tracing in the PCG Graph Editor UI (visually stepping through its config, not more headless parameter guessing) to find the actual bad field.

**Fix scope decision**: NOT attempted tonight. Replacing `PCGExCreateShapesSettings` with vanilla `PCGCreatePointsSettings` (the proven Escher `*Ex` pattern) would erase real authored shape-grid content (these are architectural room-shape generators, not simple point scatters) without understanding what art direction they were producing — a guess-replacement risks losing real work, unlike the Escher `*Ex` fixes which were re-deriving simple test points from scratch. Needs either: (a) a real Volume actor with sane bounds instead of a bare test `PCGVolume` (the crash may be purely a test-harness artifact — a properly-placed/sized volume in the real level might never hit the bad path), or (b) tracing `PCGExCreateShapesSettings`'s actual seed/count inputs in-editor (Material/Graph Editor UI, not headless Python) to find the real bad param. Flagging as a clear next step rather than guessing at a destructive fix.

## RESEARCH 2026-07-02 (overnight): UE5.8 PCG capabilities + Escher precedent, both `Research` status

- **UE5.8 added "Mesh Terrain"** — a terrain system based on 3D meshes instead of heightmaps, natively PCG-integrated, explicitly supports overlapping geometry (caves, overhangs, complex structures). [Unreal Engine 5.8 Preview](https://www.biunivoca.com/en/blog/unreal-engine-5-8-preview), [UE 5.8 release notes](https://www.unrealengine.com/news/unreal-engine-5-8-is-now-available)
  - **Investigated 2026-07-02, `Broken`/no-API confirmed**: Mesh Terrain has **no Python-exposed creation/authoring class** (`unreal.MeshTerrain*`, `AMeshTerrain`, `/Script/Landmass.MeshTerrain` all resolve to nothing) — same limitation as classic Landscape. What IS exposed: 5 PCG-side classes for reading/baking an *already-authored* Mesh Terrain (`PCGGetMeshTerrainSectionSettings`, `PCGGetMeshTerrainSectionActorSettings`, `PCGGetMeshTerrainSectionChannelTexturesSettings`, `PCGBakeMeshTerrainSectionMeshSettings`, `PCGMeshTerrainSectionData`). **Conclusion: does not unblock the "landscape creation has no API" gap** — a human still has to create the Mesh Terrain in-editor first; PCG can then query/bake from it. Worth remembering for later (once a Mesh Terrain exists in a level, these 5 nodes are real scriptable integration points), but not a path to headless terrain authoring.
- **UE5.8 PCG also added edit-on-top-of-procedural-content** — manual art-direction edits no longer break the underlying procedural graph, so upstream params stay live-adjustable after hand-tweaking. Relevant to any future "hand-finish a generated cathedral" pass. [PCG Framework Node Reference (5.8 docs)](https://dev.epgames.com/documentation/unreal-engine/procedural-content-generation-framework-node-reference-in-unreal-engine)
- **No existing UE PCG literature documents Escher-style impossible-geometry generation** — confirmed via search, this remains a genuine gap; the closest precedent (Monument Valley, Scott Kim's 1994 "Escher Interactive") is hand-authored puzzle content, not procedural. This project's math-translated room generators (Relativity/Penrose Loop/Recursive/Gravity-Shift, see MAJOR FINDING below) are, as far as this research found, a novel application — not derivative of a known PCG technique. Worth stating that plainly in any portfolio write-up rather than implying prior art exists.
- Escher's technique in art-historical terms: locally-consistent, globally-inconsistent geometry (Penrose Triangle-style) — useful framing for future room generators: each individual box/segment must obey normal Euclidean placement rules relative to its neighbor, only the *global loop closure* breaks consistency. This matches exactly what `_penrose_loop_points()` and `_gravity_shift_corridor_points()` already do (each arm/segment placed consistently, the paradox is only apparent over the full loop) — validates the existing math approach rather than suggesting a new one.

## MAJOR FINDING 2026-07-02 (overnight autonomous session): a far more sophisticated Escher/surreal architecture generator already exists outside the PCG system

`deploy/surreal_architecture_gen.py` (~15,700 lines, Blender addon, currently v2.131.0 in this repo -- confirmed newer than a June 4 backup zip found on the user's OneDrive Desktop, which was v2.55.0 and explicitly a "base" recovery snapshot for baroque interior presets lost on 2026-06-03 and never recovered) contains real, fully-wired Escher room generators built as Blender GeometryNodes, e.g.:
- `build_gb_escher_relativity()` (line ~6332) — "Relativity Room: a chamber where 3 gravity directions coexist. Based on Escher's 'Relativity' (1953)" — floor/wall/ceiling staircases in one room, real UI preset (`SURREAL_ARCH_OT_preset_gb_escher_relativity`), fully operator-wired.
- A "Print Gallery"/"Smaller and Smaller" recursive room generator (line ~6705) — "hub room for recursive puzzle levels."
- Also: real spiral staircase mesh generator (`_make_spiral_staircase_mesh`), Rotunda with gallery+oculus dome, Vault Cluster (barrel-vaulted chamber grid), Lighthouse, Greybox Pillar Hall.

This is **architecturally more sophisticated than the current UE-native PCG Baroque/Escher work** (which uses hand-placed `PCGCreatePointsSettings` points, not real room-grammar generation). It outputs Blender meshes + a `.world.json` manifest (see `deploy/SURREAL_WORLD_RESEARCH.md`, `surreal_world/compose.py`/`export.py`) meant for HISM import into UE — that bridge exists in concept but its actual current working state (does it run, does the export produce valid UE-importable data) has NOT been verified this session. This is a serious candidate for the "massive scale cathedral + Escher environment" goal — likely more powerful than continuing to iterate on the UE-side PCG graphs alone. Needs a dedicated investigation pass: (1) confirm the Blender addon still runs cleanly in the user's current Blender version, (2) generate a test Relativity Room + export via the world.json pipeline, (3) confirm the UE import side (`surreal_world` Python package or manual HISM import) actually works end-to-end, (4) only then decide whether to lean on this system vs. continuing pure-PCG expansion.

**READ THIS FILE FIRST, before trusting any other plan doc's asset-state claims.** Multiple
tools/sessions edit the same materials and PCG graphs without reading each other's history —
confirmed concretely on 2026-07-01/02: `PCG_Sub_BaroqueSpawn` got fixed by another session with
no record; `bNikkiFast`/`bNikkiHero` orphan switches were deleted then silently recreated;
`M_Master_Toon_Universal`'s `bTriplanar` switch and `TriplanarTileSize`/`TriplanarBlendSharpness`
scalars were removed/renamed to `TriplanarTiling`/`TriplanarBlend` (no boolean gate) within the
same session; `PCG_RockScatter` was renamed or removed entirely between two checks an hour apart.
**Numbers below are last-verified live reads, not assumptions — if you're about to script an edit
against a specific parameter/node name, re-verify it exists first (`get_material_expressions` /
`list_assets`), don't trust this table blindly either.**

**Last verified:** 2026-07-02, by Claude (live `MaterialEditingLibrary`/`EditorAssetLibrary` reads, not doc inference)
- `M_Master_Toon_Universal`: 916 expressions, 10 static switches (`UseUDSTimeOfDay`, `bLayerA_Active`, `bLayerB_Active`, `bLayerC_Active`, `bNikkiHero`, `bSheenUsesNormal`, `bSparkleAdvanced`, `bUseHeightToNormal`, `bUseSeparateMetallicMap`, `bUseSeparateRoughnessMap`), 0 orphaned switches, BSDF fully wired (BaseColor/Metallic/Roughness/Normal/EmissiveColor all non-null).
- `M_Master_Toon_Landscape_HeightBlend`: 280 exprs, 7 switches, 0 orphans. `M_Water_Master_Grand_v6`: 61 exprs, 0 switches. `M_Master_Impressionist_Toon`: 122 exprs, 2 switches, 0 orphans.
- Iridescence/Sheen family confirmed live on Universal: `Iridescence`/`IridescencePower`/`IridescenceBias`/`IridescenceRoughnessAtten`, `FabricSheen`/`SheenPower`/`SheenWidth`/`SheenBias`, `HairSheenStrength`/`HairSheenPower`, 3 Fresnel nodes, all consumed.
- `Content/EnvSandbox/PCG/`: 77 total assets (Styles 53, Universal 20, Collections 2, Legacy_Portfolio 1, _Deprecated 1) — down from an 89-asset count observed earlier the same session; some Universal graphs (e.g. `PCG_RockScatter`) were renamed/consolidated mid-session, re-verify exact paths before scripting against them.
- Escher `*Ex` graphs: `PCG_EscherFloatingIslandEx`/`GravityBridgeEx`/`ImpossibleArchEx` fixed and live-verified generating (8/5/8 instances respectively) via disconnected-StaticMeshSpawner repair. `PCG_EscherPenroseStairEx` still produces 0 — needs a spline/path input (same root cause as the ~13 Bezier-blocked graphs, not yet fixed).
- 4-scene flagship Material Instances built/upgraded: `MI_Sakura_ToriiRed`, `MI_Baroque_GildedFiligree`, `MI_Escher_ImpossibleTile`, `MI_Grotto_CrystallineSpire` (this last one had a dead parent reference — WorldGridMaterial fallback — reparented to Universal as part of the fix).
- 54 prop folders (`Content/Library/Migrated/{MagiciansLibrary,Melodia}/`) migrated via raw-copy + material-slot repair script (`Content/Python/migrate_props_from_source.py`) — not yet wired into any `SCATTER_MESHES` role.
- Master split experiment (Step 8, `Content/EnvSandbox/Materials/_Scratch/`): proved the pattern works -- `MF_IridescenceSheen` extracted as a standalone Material Function, wired into a duplicate base, verified via instance parameter readback. API note: `MaterialEditingLibrary.duplicate_material_expression` only works within one graph, can't copy nodes across into a Function -- extraction means faithful reimplementation, not literal copy-paste. Production master untouched (916 exprs confirmed before/after). Layer A/B/C blend chains (now cleanly grouped, see param-group entry below) are the next extraction candidates.
- PCGEx: 381 `PCGExSettings` classes confirmed available (`Content/Python/probe_pcgex_nodes.py` → `Saved/Audit/pcgex_node_probe.json`). Concrete unused-but-relevant candidates for organic Nikki-style scatter: `PCGExLloydRelax2DSettings`/`PCGExLloydRelaxSettings` (even point distribution, prevents clumping), `PCGExFusePointsSettings` (dedupe near-overlapping instances), `PCGExDistanceFilterProviderSettings` (already in use in `PCG_Sub_WalkabilityFilter`).
- `PCG_SimpleScatter` + `PCG_ClusteringScatter` (8 spawners) remapped from `/Engine/BasicShapes/Cube` to real migrated meshes, live-verified via post-save re-read. Both currently still produce 0 generated instances for reasons unrelated to the mesh fix — `PCG_SimpleScatter` needs a landscape/surface for its `PCGSurfaceSamplerSettings` node, `PCG_ClusteringScatter` has a pre-existing input-chain issue and was never in the confirmed-14-working set. Fix the point-source problem and the correct meshes are already waiting.
- **`MF_Gemstone` built** (`Content/EnvSandbox/Materials/_Scratch/`, scratch only, production master untouched at 916 exprs) -- jewelry-material family (chromatic dispersion Fresnel + facet specular variance), distinct from Iridescence/Sheen, params verified propagating via readback. Honest limitation: no clearly distinguishable visual difference in `capture_material_grid` even after 4x magnitude amplification -- needs real-time in-editor tuning (Material Editor live preview), not resolvable via headless scripting alone. Don't re-attempt the same headless amplification approach; if picking this up again, either tune interactively in-editor or trace why the additive contribution is being visually absorbed (check interaction with the co-installed MF_IridescenceSheen on the same scratch base, or the SubstrateToonBSDF's response to small BaseColor deltas).
- **`capture_material_grid` (Monolith `editor` action) is a genuinely trustworthy visual verification path** for M_Master_Toon_Universal instances -- unlike `render_preview` (documented unreliable, shows identical output regardless of color params), a before/after test on 4 flagship instances showed real, visible hue/richness differences matching the parameter changes made. Call params must be nested under a `params` object (not top-level) when using the generic `editor_query` action dispatcher. Use this, not `render_preview`, for future material instance visual checks on this master.
- **`BaseTint` (group "01 | Base Surface", default flat 0.5/0.5/0.5 grey) is the actual base color driving every instance's overall hue** -- every prior session's flagship-instance work (including the "4-scene Nikki-styled library" built earlier) only touched effect-layer params (Iridescence/Sheen/Layer blends) on top of this untouched grey default, which is why they read as washed-out/pale rather than richly colored. Also unused until now: `DreamTint`, `IridescenceTint`, `GoldTint` (group "11 | Gilding"), `ShadowDreamTint` (group "13 | Shadow Dream") -- a full tint ecosystem. Check `BaseTint` first on any instance that "doesn't read well."
- **`bSparkleAdvanced` + the full "09 | Nikki Sparkle" family (`SparkleScale/Intensity/Threshold/Contrast/DriftSpeed/TwinkleSpeed/NoiseScale/ColorLerp`, `SparkleColor/Low/High`) is fully wired and unused** -- traced end-to-end this session (both switch branches populated, reaches a real TextureSampleParameter2D chain, not an orphan). Now activated on the 4 flagship instances.
- **`PCGVolumeSamplerSettings` wiring fix (broadly useful)**: its "Volume" input pin must be wired from the graph's own Input node's "In" output pin using the exact target pin name `"Volume"`, not the generic `"In"` name used elsewhere in PCG -- easy typo, silently produces 0 points with no error. Confirmed live: 0 -> 27,000 instances once corrected. Check any future VolumeSampler-based graph showing 0 output for this exact mistake before assuming a deeper problem.
- **`PCGExAssetStagingSettings` -> `PCGExMeshSelectorStaged` handoff confirmed still broken/unclear** even with the VolumeSampler fix applied and points correctly reaching the staging node (tested with both a broken collection and a clean 3-entry collection, `output_mode=ATTRIBUTES`, correct `In`/`Out` pin wiring) -- staging node produces 0 spawned instances downstream. The blocker is specifically in this node pairing's attribute contract (likely a `asset_path_attribute_name` mismatch between what staging writes and what the selector reads, or missing required config on `PCGExMeshSelectorStaged` not discoverable from CDO property inspection alone). Needs PCGEx source reading, not more trial-and-error -- two separate sessions have now hit this same wall.
- `PCGCol_Environment_GroundCover`/`PCGCol_Environment_Rocks` (`PCGExMeshCollection` assets, real weighted mesh entries, built by parallel tooling) are 100% unreferenced by any graph — same "built but not wired" pattern as `PCG_Sub_BaroqueSpawn` was. `PCGExAssetStagingSettings` is the PCGEx node meant to consume them but its wiring contract (property `collection_source`, `selector_mode`, output pin behavior) wasn't reverse-engineered this session — needs dedicated investigation before attempting.

## Ownership Boundary

`L_SakuraPath` art direction, hero composition, set dressing, and final scene polish are human-owned. Japanese/Sakura-themed materials and instances are allowed as reusable platform/look-dev work. This state file tracks the reusable platform around that work.

## Platform Systems

| System | Status | Current Truth | Next Platform Action |
|---|---|---|---|
| Universal master material | Implemented | `M_Master_Toon_Universal` is the central mesh/prop/trimsheet master with many style families. | Keep architecture; audit latest update, parameter metadata, duplicate params, stale refs. |
| Landscape height blend | Implemented | `M_Master_Toon_Landscape_HeightBlend` supports reusable terrain look-dev. | Document generic usage presets and capture requirements. |
| Grand water | Implemented | `M_Water_Master_Grand_v6` is canonical reusable water. | Treat as platform pillar; capture generic pond/shoreline examples in template context. |
| Material instances | Implemented | `MI_Show_*`, `MI_Landscape_*`, `MI_GrandWater_*`, trimsheet, Zen, Baroque families exist. | Generate material family manifest and preview readiness report. |
| Material manifest | Partial | Portfolio schema expects material metadata, but no stable producer existed. | Use `Content/Python/material_family_manifest.py` as the thin contract producer. |
| L_Template look-dev stage | Partial | Template stage exists and is referenced by setup scripts. | Promote as generic look-dev validation stage; avoid Sakura dependency. |
| PCG universal stack | Implemented | Universal and style wrapper PCG graphs are documented and audited. | Keep generic scatter contracts separate from Sakura art pass. |
| Capture/package stack | Implemented | Render exporter, plate compiler, output layout, and aggregator exist. | Add completeness reports and generic material preview inputs. |
| Website deploy lane | Implemented | `_github_deploy/generated` contains generated web artifacts. | Add package-to-website metadata handoff map. |
| Figma/design system | Implemented | Design system and Figma guide are mature. | Connect package schema to design tokens via adapter docs. |
| Recursive agents | Partial | Agent roles, boundaries, and loops exist. | Add Producer, Material TD, Look-Dev Capture roles and autonomy lanes. |

## Known Technical Debt

| Area | Status | Detail |
|---|---|---|
| Universal inline vs MF duplication | Partial | `MATERIAL_SYSTEM_REVIEW.md` flags Nikki/Parallax duplication. |
| Duplicate material params | Partial | Duplicate declarations are tracked in audits; should be reduced cautiously. |
| Archive instance duplication | Partial | `_Archive` mirrors active instance trees in places. Do not delete without explicit approval. |
| Material preview producer | Partial | Existing preview capture was under-wired; manifest producer now supplies metadata, not images. |
| Figma API sync | Planned | Design contract exists; automatic package consumption is not the priority until generic package is stable. |

## Out Of Scope For Automation

- Editing `L_SakuraPath` composition.
- Replacing Sakura hero props.
- Publishing external portfolio updates without approval.
- Broad shader-family redesign.
- Destructive cleanup of legacy assets.
