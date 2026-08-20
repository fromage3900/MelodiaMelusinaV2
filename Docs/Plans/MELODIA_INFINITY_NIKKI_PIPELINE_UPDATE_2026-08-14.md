# Melodia / Infinity Nikki Pipeline Update

**Date:** 2026-08-14  
**Scope:** closed-editor rebuild, Melodia integration layer, long-term gameplay BP readiness, procedural content, and traversal/ability architecture.

**Execution state:** the recorded closed-editor native rebuild passed, but the latest
owner check is not a live-authoring session: it finds 0 `UnrealEditor`, 0 commandlet
processes, eight `monolith_proxy` processes, and no listener on port `9316`. Claude
owns the current build lane; this plan does not launch a competing build or claim
success from process absence. The next usable session is one clean editor re-entry
after Monolith returns.

## Goal

Make the Melodia integration layer safe to extend for the next gameplay slice while preserving one authority per concern:

- one runtime game-mode/world authority;
- one canonical narrative/save record;
- data-driven definitions for skills, enemies, portals, traversal, challenges, and state anchors;
- deterministic Blueprint/T3D evidence before a template is reused;
- sandboxed procedural content that cannot silently become a second persistence system.

This is a long-term foundation goal. “All BPs ready” means every reusable template reaches a documented L0-L4 readiness bar; it does not mean every future skill or enemy is authored now.

## Current status

### Proven or materially advanced

1. **T3D safety:** `Tools/test_t3d_safe_wire.py` passed 42/42 after replacing tautological assertions with request-owned node, forbidden-node, link, explicit before→after graph-delta, compile-count, and saved-re-export postconditions. Non-placeholder request IDs and live pre-edit fingerprints are now mandatory. Fresh live probe evidence is still required before scaling T3D mutations.
2. **Native rebuild:** a recorded `BS_GodFile Win64 Development` UBT/UHT/compile/link run passed with `-NoMutex -NoHotReloadFromIDE -NoUnity -Verbose`; see `Docs/Handoffs/TRAVERSAL_API_BUILD_EVIDENCE_2026-08-14.md`. The later capability-provider and Blueprint-extensibility edits still require one clean post-change compile after the current editor owner exits.
3. **GameMode authority:** `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode` was live-queried as a compiled, data-only child of `GameModeBase`. It is the configured authority in `Config/DefaultEngine.ini`; legacy `AMelodiaGameMode` remains quarantined.
4. **Kawaii placement probe:** `/Game/MelodiaIntegration/Tests/BP_KawaiiPhysicsPlacementProbe` is live-repaired and saved with `PreviewMesh`, `PreviewCamera`, `ResetAnchor`, compatible `SK_MelusinaHair` + `ABP_Melusina_WaterHair`, a hair physics-asset override, `InitialTransform`, `bKawaiiDebug`, `ResetSimulation`, and `ToggleKawaiiDebug`. Compile and graph export are proven; a live actor spawn was observed, but the integration map was read-only and the save crashed before persistence. The read-only attribute is now cleared, but the map still needs a clean-session save. Map reachability, AnimBP playback, physics-asset compatibility, and deterministic PIE reset remain pending.
5. **Procedural dungeon reactivation:** the clean room-builder path is identified: `RoguelikeRoomCustomData`, `MelodiaRoguelikeDefinitions`, `MelodiaRoomEntrance`, `MelodiaRoomExit`, and `MelodiaFirstDungeonGate`. Coordinator/run-subsystem/persistence remain quarantined until the Sir ladder and canonical narrative-record path are closed.
6. **Contracts:** the gameplay BP kit and Kawaii probe JSON contracts exist under `specs/blueprints/` with L0-L4 evidence rules.
7. **Resonant Form bridge:** Wardrobe exposes read-only form/capability queries and now registers through a module-neutral game-module registry. Traversal requests and jump-to-glide input consume the provider when opt-in is enabled; clean-editor build and live evidence are still pending.

### Current blocker / why work paused

The editor re-entry is stalled in Turnkey SDK detection; the latest usable editor log
also contains a historical fatal D3D12 bindless descriptor allocation failure while a
long material-save batch was active:

> `Hit D3D12 device limits on descriptors when attempting to allocate larger descriptor heap of size 1000000.`

The map save also exposed two separate live-session risks: the map package had the
Windows read-only attribute set, and the probe's physics-asset override logged
`Could not find root physics body`. The attribute has been cleared; the physics
override must be verified or removed in the next clean session. The source tree is now
**native-build green**, but the rebuild/re-entry is not yet editor/PIE green. The next
usable editor session must still prove the Kawaii map save, PIE reset, and live T3D
postconditions.
The worktree is intentionally dirty with parallel art, gameplay, automation, and
task-ledger changes. Do not reset, clean, or rewrite unrelated files;
`_TASK_QUEUE.md` is being edited by another agent.

### Latest offline execution snapshot

- `Tools/melodia_bp_materialization_preflight.py` is now a read-only, offline-first
  gate for the seven canonical template paths. It creates no `.uasset` or `.umap`.
- The preflight currently classifies **6/7** templates as specified enough to enter
  a live authoring session: TraversalGate, Enemy, Encounter, Portal, WorldChallenge,
  and StateAnchor.
- **1/7** remains a deliberate design stop: Skill (definition/cooldown/request-id
  bridge). WorldChallenge and StateAnchor now have source-wired atomic adapters;
  clean native compile/reflection and live fixture proof remain pending.
- The explicit materialization order is now registry-owned:
  `Skill -> TraversalGate -> Enemy -> Encounter -> Portal -> WorldChallenge -> StateAnchor`.
- WorldChallenge and StateAnchor now have L1 contract-only first fixtures plus
  source-wired atomic adapter contracts. They specify stable keys, canonical
  narrative operations, context locks, replay-safe presentation, and reload/reset
  evidence without creating a second save authority.
- The new preflight regression is included in `BuildGraph/MelodiaBuildGraph.xml`;
  offline contract gates remain green and live graph/PIE proof remains unavailable.

## Infinity Nikki research: useful pipeline patterns

These are architecture lessons only; do not copy monetization, gacha, or live-service business logic.

### 1. Treat an ability as a content package

Infinity Nikki’s official material connects outfit theme, exploration movement, transformations, animation, VFX, restrictions, and upgrades. The Melodia equivalent should be one versioned package:

`AbilityId -> definition DataAsset -> state/movement contract -> presentation assets -> restrictions -> upgrade/evolution -> fixture`

The reusable BP should orchestrate the contract, not contain the entire ability’s data or presentation graph.

### 2. Separate identity, unlock, equipment, and presentation

Ability availability and appearance should not be hardcoded to one outfit or one character mesh. Use stable IDs and compatible variant sets:

- `CapabilityId` — what the player can do;
- `UnlockConditions` — quest, node, region, or narrative requirements;
- `EquippedVariantId` — current style/mesh/animation presentation;
- `AllowedContexts` — open world, dungeon, boss, menu, co-op;
- `EvolutionStage` — optional upgrade/effect tier.

This keeps future skills and wardrobe variants additive instead of forcing another authority into the character BP.

### 3. Make traversal an explicit state machine

Mount/follow/hover/sprint-style modes and context locks should be modeled as explicit transitions, not scattered booleans. A traversal capability should declare enter, update, exit, interruption, and reset behavior. Boss arenas, uncleared dungeons, cutscenes, and map transitions must be first-class restrictions.

Recommended Melodia split:

- `UMelodiaTraversalComponent` — runtime state and transition authority;
- `BP_MelodiaTraversalGate_Base` — world-facing requirement/check actor;
- `DA_MelodiaTraversalDefinition` — modes, contexts, restrictions, costs, and presentation;
- `BP_MelodiaTraversalFixture` — deterministic test map/route.

### 4. Gate capabilities by progression, not by level-local hacks

Heart-of-Infinity-style progression suggests a general requirement object that can be evaluated by portals, abilities, challenges, and UI. Store the requirement in data, evaluate it through one service, and re-evaluate after load or narrative phase change.

### 5. Keep art-to-runtime handoff explicit

The official art pipeline describes theme/inspiration, design iteration, turnarounds/patterns, 3D production, continued art tuning, VFX, and programming collaboration. The Melodia handoff should therefore require:

`brief -> concept/turnaround -> mesh/AnimBP/VFX -> DataAsset -> integration BP -> authored fixture -> compile/export/path/PIE evidence`

No BP template is “ready” merely because its asset exists.

### 6. Separate constructible definitions from world-state persistence

The Expansion feature is a useful pattern for a future room/build system: definitions/schemes describe what can be built; a placement actor handles instantiation; a world-state anchor records the minimal canonical state. This supports procedural rooms, portals, and challenges without making the room generator a second SaveGame authority.

### 7. Design updates as data packages

Chapter-gated events, permanent features, new regions, and periodic content should enter Melodia through versioned data packages and feature gates. The package should identify requirements, allowed contexts, assets, and test fixtures. Avoid growing one giant EventGraph for every update.

### 8. Make ability modes and presentation availability explicit

The current public Version 2.8 update is a useful systems reference: the Gilded
Dawnchaser ability exposes Follow, Mount, Hover, and Sprint modes; smart mounting and
interaction settings are configurable; Hover is unavailable in uncleared dungeons;
and the ability is blocked in Realm Challenges and boss stages. The same update adds
open-world scene preview, four lighting conditions, effect toggles, and importable
styling schemes with unavailable-piece handling. Melodia should translate this into
data, not copied product logic:

`CapabilityId -> ModeSet -> ContextPolicy -> PresentationVariantSet -> PreviewPolicy -> Fixture`

Every traversal/skill package must therefore declare its enter/update/exit modes,
blocked contexts, fallback presentation, preview/effect toggles, and deterministic
reset behavior. This is the missing bridge between a reusable BP and a future content
drop.

### 9. Research refresh: current public Infinity Nikki signal

The official Version 2.8 notice remains the newest numbered update found in the
official news index during the 2026-08-14 review. It adds the permanent `Golden Dust`
quest, event/challenge content, and the `Gilded Dawnchaser` ability with explicit
Follow, Mount, Hover, and Sprint modes. The notice also makes context restrictions
concrete: the ability is unavailable in Realm Challenges and boss stages, while Hover
is unavailable in uncleared dungeons. Its evolution rewards add presentation state
(idle animation, enhanced effects, alternate piece details) rather than changing the
core authority. See the [official Version 2.8 notice](https://infinitynikki.infoldgames.com/en/news/560).

The Version 2.7 ability preview reinforces the same rule with bounded spawned
objects, lifetime/range limits, and stage restrictions for `Celestial Tide`; see the
[official 2.7 outfit preview](https://infinitynikki.infoldgames.com/en/news/525).
The Unreal Engine interview describes separate branch-based engine transition and
evaluation, direct in-engine cloth authoring, a versatile material system, skeletal
physics plus Chaos Cloth, authored/precomputed clipping rules, and performance-aware
rendering; see [Epic's Infinity Nikki technical interview](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world).

Melodia should adopt only the architecture: versioned ability packages, explicit mode
and context policy, fallback presentation, authored compatibility/clipping profiles,
and offline/fixture validation. It should not copy Nikki's monetization, proprietary
rendering, or live-service economy.

## Updated execution plan

### Phase 0 — closed-editor rebuild and re-entry

1. Let the rebuild owner finish; do not start a second editor session while the rebuild owns the project.
2. Run the C++ target build against the post-rebuild tree with the editor closed; capture exit code and UBT log.
3. If C++ is green, reopen the editor once, verify no modal save loop, and reindex Monolith.
4. Re-query `BP_KawaiiPhysicsPlacementProbe`; verify the hair physics asset's root body, compile, export the graph, and save a fresh evidence envelope.
5. Place the probe only in the intended Melodia integration test map, save the map, re-query the actor list, and run deterministic reset/PIE evidence.
6. Diagnose the D3D12 descriptor failure separately from gameplay work. Avoid another broad material-save batch until the failure is isolated.

**Exit:** post-rebuild build evidence, one clean editor re-entry, probe compile/export/path/PIE evidence, and a recorded disposition for the D3D12 crash.

### Phase 1 — Core P0 Dream slice

1. Re-prove the configured GameMode and WorldSettings route for the integration map and the Opening/KaleidoNave/Dreamstate entry points.
2. Prove input, encounter, and battle startup do not depend on quarantined `AMelodiaGameMode` ownership.
3. Close the First Dream golden route using the task ledger’s current exact gates: package/launch, runtime entry, encounter/battle handoff, persistence/process restart, and return path.
4. Keep the ledger owner-controlled; do not edit `_TASK_QUEUE.md` while another agent is modifying it.

**Exit:** a repeatable P0 route with fresh runtime evidence and no authority collision.

### Phase 2 — Reusable gameplay BP kit

Author one fixture for each template, in the registry-owned order:

1. `Skill` — one data-driven Melodia skill with cooldown/cost/targeting and presentation hooks.
2. `TraversalGate` — one multi-mode traversal state fixture with context restrictions and reset.
3. `Enemy` + `Encounter` — one enemy definition and one encounter director fixture.
4. `Portal` — one portal with capability/narrative requirements and failure feedback.
5. `WorldChallenge` — one repeatable challenge with a result/state anchor; its L1
   contract fixture is present, but live materialization waits on the adapter.
6. `StateAnchor` — one minimal canonical state write/read fixture; its L1 contract
   fixture is present, but live materialization waits on the adapter.

Each template must reach L4 only after compile, graph export, map path, PIE/runtime, and failure-path evidence.

The first live authoring slice remains the Skill definition/presentation path and one
multi-mode TraversalGate, but the Skill cannot be materialized until its definition,
cooldown, and request-id bridge is designed. Enemy, Encounter, Portal, WorldChallenge,
and StateAnchor remain behind the preflight order and fresh T3D/fixture evidence.

### Phase 3 — procedural dungeon, safely staged

1. Live-verify `BP_RoguelikeDungeonGenerator` and the clean five room-builder assets.
2. Author only Start, Standard, and Blessing room data in the sandbox/ZenForestTest route.
3. Wire entrances/exits and prove the player can enter, generate, traverse, and leave.
4. Do not reactivate duplicate persistence. Use the canonical narrative record for future run state.
5. Close the Sir ladder (`NotifyDreamstateCompleted` / `NotifySirRescued`) before considering coordinator reactivation.
6. Treat “Burden” as a new design decision; it is not currently modeled by the existing room data.

### Phase 4 — long-term content scale

Create a small registry/schema layer with:

- `CapabilityId`, `DefinitionVersion`, `UnlockConditions`, `AllowedContexts`;
- `VariantSet`, `EvolutionStage`, `PresentationAsset`;
- `RuntimeAuthority`, `StateWritePolicy`, `FixtureMap`, `EvidenceManifest`.

This registry becomes the integration seam for new skills, enemies, portals, traversal states, events, photo/presentation modes, and future co-op-safe content. Every package should be independently testable and removable.

The JCode/Ollama lane is an authoring assistant, not a runtime authority: it may draft
and validate package JSON outside `Content/`, but it must not mutate `.uasset`, `.umap`,
save state, or `_TASK_QUEUE.md`. The fleet has no shared-checkout lock, so duplicate
launches remain prohibited while the worktree is dirty. See
`Docs/Handoffs/JCODE_OLLAMA_INTEGRATION_AUDIT_2026-08-14.md`.

The native-surface audit confirms the planned Skill, TraversalGate, Enemy, Encounter,
Portal, Narrative, Party, and Travel authorities exist in C++ while the seven canonical
gameplay BP assets are still absent. See
`Docs/Handoffs/BP_NATIVE_SURFACE_AUDIT_2026-08-14.md` before materializing the first two.

The latest Infinity Nikki check remains Version 2.8: the official notice documents the
August 6 Part 2 unlock, Heart of Infinity progression, multi-mode ability restrictions,
scene preview/effect toggles, mount-specific fallback styling, and resource cleanup.
Melodia should adopt these as versioned data/package fields and fixtures, not as copied
economy or proprietary runtime behavior. No official 2.9 announcement was visible in
the checked official news index.

The delegated research refresh adds three requirements to the long-term lane:

- every traversal capability declares explicit state transitions, input/camera/
  collision/energy ownership, temporary-object lifetime cleanup, and interruption;
- every gameplay definition separates core, preview, locked/fallback, and evolution
  presentation states;
- scheduled, recurring, rerun, permanent, and retired content use a versioned release
  manifest with reset, preload, fallback, migration, and reference-safe cleanup rules.
  The offline contract is `specs/content/melodia_content_release_manifest.v1.json`.

The official-source refresh on 2026-08-14 sharpens the next content-preparation
slice: model traversal as an explicit transition graph; bound temporary helpers and
clean them on interruption/range/logout/reset; separate capability availability from
preview, fallback, and evolution presentation; and keep progression snapshots in
the shared gate. Version 2.8's Machine Control, Automaton race, and mount-fallback
examples are reference fixtures for those boundaries, not systems to copy.

The corresponding live BP acceptance checklist is now:

- one mode transition graph with named enter/update/exit/interruption/reset paths;
- one context matrix covering open world, uncleared dungeon, boss/challenge, cutscene,
  menu, travel, and reset;
- bounded helper ownership with instance/lifetime/distance/logout cleanup;
- explicit preview, locked/fallback, runtime, and evolution presentation variants;
- a gate request ID plus evaluation fingerprint in the evidence envelope;
- Kawaii/clipping profile and reduced/no-physics fallback references;
- release-manifest package/version/reset/cleanup references.

The Core P0 owner-run is also captured as
`specs/p0/core_p0_dream_golden_run.v1.json`; it prevents the integration proof map
from being mistaken for the Morning → KaleidoNave player route and records the
fresh-slot/restart/idempotency evidence needed before BP expansion.

All seven canonical BP templates now have L1 contract-only fixtures in the registry:
Skill, TraversalGate, Enemy, Encounter, Portal, WorldChallenge, and StateAnchor.
This closes the offline definition surface; it does not promote any template to
live Blueprint readiness.

## Immediate next actions

1. Obtain the current Claude build-lane result, then restore one explicitly owned editor
   plus one confirmed Monolith endpoint; do not launch a competing build or treat process
   absence as build evidence.
2. After the handoff is clean, run one C++ target build for the post-rebuild reflected
   Wardrobe/capability changes if they are included in the active source state.
3. Reopen one clean editor session and run the player-facing P0 golden route: `L_MelusinaMorning` → `L_KaleidoNave`; use `MelodiaIntegrationMap` only for deterministic persistence checkpoints.
4. Re-run the live T3D safe-wire probe after the golden run with fresh request-derived postcondition evidence.
5. Verify Kawaii physics root-body compatibility, persist the probe in `MelodiaIntegrationMap`, and run PIE reset twice.
6. Reconcile the exact open P0 ledger gates from `_TASK_QUEUE.md` without overwriting its parallel edits.
7. Compile and live-verify the implemented module-neutral Resonant Form capability bridge; then confirm native traversal requests and direct input use the same fail-closed check.
8. Design and build one explicit Skill definition bridge before materializing the Skill BP. Do not auto-project `UMelodiaRhythmSkillDefinition` into `FMelodiaSongSkillRecipe` until note/pattern, instrument, element, material, power, and resource-spend semantics are specified.
9. Run `python Tools/melodia_bp_materialization_preflight.py` after each contract change; it must remain offline-safe and show no planned asset collision.
10. Implement the first data-driven Skill and TraversalGate fixtures before expanding to more enemies or portals.

## Research sources

- [Infinity Nikki Version 2.8 Update Notice](https://infinitynikki.infoldgames.com/en/news/560)
- [Infinity Nikki V2.3 Expansion feature](https://infinitynikki.infoldgames.com/en/news/442)
- [Infinity Nikki Art Design of the Revelry Season](https://infinitynikki.infoldgames.com/en/news/155)
- [Infinity Nikki Version 1.5 optimization preview](https://infinitynikki.infoldgames.com/en/news/156)
- [Infinity Nikki Version 2.2 update](https://infinitynikki.infoldgames.com/en/news/433)
- [Infinity Nikki Version 2.7 ability preview](https://infinitynikki.infoldgames.com/en/news/525)
- [Epic Games: Behind the Scenes of Infinity Nikki](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world)
