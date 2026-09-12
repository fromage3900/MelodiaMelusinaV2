# Blueprint Authority and Readiness Audit

Date: 2026-08-14  
Scope: Melodia integration, long-term gameplay Blueprint expansion, T3D handoff, and Kawaii Physics placement  
Status: static audit complete; live graph verification is pending editor/Monolith availability

## Executive verdict

The project has enough named assets to begin a durable gameplay-content layer, but it does not yet have proof that every Blueprint is ready for production use. The correct long-term move is an authority registry with explicit readiness gates, not bulk creation or broad rewiring.

The highest-risk issue is authority mismatch:

- `Config/DefaultEngine.ini` points the global default GameMode at `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode`.
- `AMelodiaGameMode` still owns older HUD/input bootstrap behavior, including dynamic creation of `UMelodiaBattleInputComponent`.
- The wiring contract records that the configured `BP_MelodiaJRPGGameMode` does not inherit that native bootstrap path, so the component may never be created on the live route.
- `AMelodiaGameMode` and `AMelodiaMobileGameMode` are already documented as quarantined lanes. They must not receive new gameplay ownership while the configured route is unresolved.

The Kawaii Physics audit found a working runtime AnimBP and a disposable placement
probe on disk, but not a reusable production Kawaii base. The existing generic
`BP_PhysicsPlacementSpawner` is a rigid-body placement fixture and is not a
Kawaii/AnimBP placement contract.

## Evidence boundary

This audit separates facts from hypotheses:

- Asset paths and source declarations were inspected from the repository.
- `Config/DefaultEngine.ini` is evidence of configured intent, not proof of the effective GameMode for every map; WorldSettings may override it.
- Existing exports and saved audit JSON are supporting evidence only. They are not substitutes for a fresh live graph export.
- The Monolith MCP/editor graph endpoint was unavailable during this pass while an Unreal Editor process was already running. No second editor was started.
- Therefore all graph, component, compile, and reachability states below that say `UNVERIFIED` require one live editor pass.

## Authority map

| Concern | Current documented/configured authority | Readiness concern | Decision |
|---|---|---|---|
| Front-end/menu | Native `AOrreryMainMenuGameMode` | Separate from gameplay GameMode; must remain the menu owner | Keep as front-end authority |
| Gameplay GameMode | `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode` | Live parent, CDO, components, and graphs not queryable in this pass | Treat as the only candidate gameplay GameMode; verify before extending |
| Legacy desktop mode | `AMelodiaGameMode` | Quarantined; contains older HUD/input bootstrap | No new placements; reconcile or retire after live-path proof |
| Mobile mode | `AMelodiaMobileGameMode` | Separate mobile HUD/touch lane; not the configured desktop route | No desktop gameplay ownership |
| Battle execution | Stock battle controller/session path plus the integration bridge | Avoid a second battle executor or UI authority | Extend through the bridge and stock contract only |
| Battle presentation | Stock battle UI plus integration UI assets | Existing docs identify duplicate/empty UI risks | Prove the active widget path before adding widgets |
| Save/load | Stock save contract and the configured JRPG save path | Historical audits identify competing save authorities | Keep one runtime owner; quarantine duplicates |
| Narrative | `UMelodiaNarrativeSubsystem` / Quill contract | Must remain event-driven and independent of content BPs | BPs emit events; subsystem owns progression |
| Travel | `UMelodiaTravelSubsystem` with travel presentation BPs | Travel volumes/triggers must not become second map routers | BPs request travel; subsystem owns routing |
| Traversal | `UMelodiaTraversalComponent` and traversal state contract | New abilities need a stable state interface | Add content adapters, not per-BP traversal authorities |
| Kawaii hair runtime | `/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair` | One Kawaii node was found; live compile and presentation coverage are stale/unverified | Preserve as runtime reference; create a disposable placement probe |
| Generic physics placement | `Content/EnvSandbox/Blueprints/BP_PhysicsPlacementSpawner.uasset` | Ignored/untracked and rigid-body oriented | Keep as local fixture only; do not treat as production integration |

## Readiness levels

Every reusable Blueprint should move through these levels independently:

- **L0 — Inventory:** asset exists, owner and intended route are recorded.
- **L1 — Contract:** parent class, interfaces, exposed variables, events, and authority boundaries are documented.
- **L2 — Graph:** live graph has been inspected; required nodes and references are present; no forbidden ownership is present.
- **L3 — Fixture:** a disposable test map or automated probe exercises the asset on its real path.
- **L4 — Ship:** compile succeeds, live-path reachability is proven, fixture evidence is fresh, and the asset is registered in the task ledger.

No asset is considered production-ready solely because a `.uasset` exists on disk.

## Current Blueprint readiness matrix

| Blueprint or class | Intended role | Current state | Next proof/action |
|---|---|---|---|
| `BP_MelodiaJRPGGameMode` | Configured gameplay authority | L0; L1–L4 unverified | Query parent/CDO/components/graphs; compile; prove effective WorldSettings route |
| `BP_MelodiaJRPGGameInstance` | Session/bootstrap state | L0; live graph unverified | Verify it owns session setup without duplicating save/travel authority |
| `BP_MelodiaJRPGPlayerController` | Player input/presentation adapter | L0; live graph unverified | Verify possession, input mapping, and battle handoff |
| `BP_MelodiaBattleBridge` | Integration adapter into stock battle | L0; live graph unverified | Prove it forwards events without becoming a second battle executor |
| `BP_MelodiaBattleUI` | Integration presentation surface | L0; possible duplicate/empty risk | Find live referencer and compile; retain only if on active presentation path |
| `BP_MelodiaTravelVolume` | World travel request/presentation | L0 | Verify it calls the travel contract, not direct `OpenLevel` ownership |
| `BP_KaleidoNaveArrivalTrigger` | Arrival presentation trigger | L0 | Verify one-shot behavior, idempotency, and event emission |
| `BP_MelusinaJRPGCharacter` | JRPG player avatar adapter | L0 | Verify traversal component, wardrobe hooks, and battle possession boundaries |
| `BP_SirMelodiousMorningIntro` | Opening narrative fixture | L0 | Verify it emits narrative/travel events and does not own progression |
| `BP_SirMelodiousPlayerUnit` | Party-unit content | L0 | Verify party/skill data contract and battle bridge compatibility |
| `BP_MelusinaTrueStrike`, `BP_MelusinaPetalCadence`, `BP_MelusinaFocusAttack`, `BP_MelusinaDoubleHit` | Existing skill content | L0 | Validate one shared skill contract, target rules, costs, cooldowns, and stock execution |
| `BP_Resonance`, `BP_SirSkyboundRefrain` | Existing party skill/buff content | L0 | Validate effect data and event routing; no direct save/narrative mutation |
| `BP_MelodiaPortal_Base` | Long-term portal content template | Planned; missing tracked canonical asset | Define request/lock/arrival contract before making variants |
| `BP_MelodiaTraversalGate_Base` | Traversal-state gate template | Planned; missing tracked canonical asset | Bind to `UMelodiaTraversalComponent` state queries and fail-safe presentation |
| `BP_MelodiaEnemy_Base` / `BP_MelodiaEncounter_Base` | Enemy and encounter content templates | Planned; missing tracked canonical assets | Make stock battle/session handoff the only execution path |
| `BP_MelodiaWorldChallenge_Base` | Exploration challenge template | Planned; missing tracked canonical asset | Define reward/event contract and reset semantics |
| `BP_MelodiaStateAnchor_Base` | Idempotent world-state anchor | Planned; missing tracked canonical asset | Define save-key and replay behavior through the canonical save owner |
| `ABP_Melusina_WaterHair` | Kawaii hair presentation | Runtime reference exists; live proof stale | Verify Kawaii node, root, physics asset, limits, compile, and active character use |
| `BP_KawaiiPhysicsPlacementProbe` | Disposable Kawaii placement/presentation fixture | Exists on disk; compile/export and a live spawn were observed, but map persistence, root-body compatibility, and PIE reset remain unverified | Complete clean-session map save, reset/debug graph, compile, reachability, and deterministic PIE evidence |
| `BP_PhysicsPlacementSpawner` | Generic rigid-body placement test | Exists on ignored/untracked path | Keep local and clearly non-production; do not use as Kawaii evidence |

## Retirement and quarantine decisions

These are retirement candidates, not deletion instructions:

1. `AMelodiaGameMode` and `AMelodiaMobileGameMode` remain quarantined until the configured gameplay route is proven. No new gameplay ownership should be added to either class.
2. `BP_MelodiaGameMode` is documented as having zero referencers and should not be wired into the live route without an owner-approved decision.
3. Historical duplicate save, quest, battle, roguelike, and outfit authorities in MelodiaCore remain out of the expansion lane until a live referencer audit identifies a real consumer.
4. `BP_PhysicsPlacementSpawner` remains a disposable rigid-body fixture. Its ignored status means it cannot satisfy a tracked production readiness gate.

Quarantine means “do not extend or silently delete.” Removal requires a fresh live referencer report and a ledger decision.

## Long-term Blueprint kit

The following templates are the minimum reusable vocabulary for future skills, enemies, portals, traversal, and world content:

| Template | Required contract |
|---|---|
| `BP_MelodiaSkill_Base` | Identity, target rules, cost, cooldown, execution request, result/event output, cancel/failure result |
| `BP_MelodiaEnemy_Base` | Encounter identity, threat profile, stock battle unit data, defeat event, reward hook |
| `BP_MelodiaEncounter_Base` | Spawn/activation rules, encounter lock, battle request, completion/reset behavior |
| `BP_MelodiaPortal_Base` | Discovery, unlock condition, traversal request, destination key, arrival event, safe failure |
| `BP_MelodiaTraversalGate_Base` | Required traversal state, blocked/available presentation, deterministic re-check after load |
| `BP_MelodiaWorldChallenge_Base` | Challenge state, attempt/reset semantics, reward event, save key |
| `BP_MelodiaStateAnchor_Base` | Stable identity, idempotent event application, persistence key, replay-safe presentation |
| `BP_KawaiiPhysicsPlacementProbe` | Skeletal mesh, AnimBP assignment, Kawaii node/root, physics/collision asset, camera/reset fixture, compile evidence |

Variants should contain data and presentation only. Runtime ownership belongs to the existing subsystem/component/stock execution contract.

## Immediate execution sequence

### P0 — Resolve authority before expanding content

When the existing editor becomes queryable, perform one read-only live pass:

1. Query `BP_MelodiaJRPGGameMode` parent class, CDO, interfaces, components, graphs, and compile status.
2. Query map WorldSettings for `MelodiaIntegrationMap`, the opening map, and the Kaleido Nave route.
3. Run `Tools/bp_live_path.py` for the configured GameMode, battle bridge, travel volume, and battle UI.
4. Compare live results with the static authority map and record only fresh evidence.
5. Decide whether the battle input bootstrap must be migrated into the configured route, provided that decision is made by the owning gameplay authority rather than by reactivating the quarantined GameMode.

### P0 — Finish the T3D safety repair

The other agent is repairing `Tools/t3d_safe_wire.py`. Do not edit that file concurrently. After the repair lands:

- rerun `python Tools/test_t3d_safe_wire.py`;
- re-run the live `inject` and `blueprint_compile` evidence against a disposable fixture;
- update the ledger only with fresh postcondition evidence;
- treat the current 42/42 pure-suite result as transport/unit confidence, not live-editor proof.

### P1 — Build the Kawaii placement probe

Create the probe on `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` only after the live graph tool is available. It should:

- use the Melusina skeletal mesh and `ABP_Melusina_WaterHair` as the reference presentation;
- expose a reset button and a visible camera framing the simulated hair/cloth;
- make the Kawaii root, physics asset, collision limits, and any required anim instance settings inspectable;
- compile in isolation and then be reached from the integration map;
- remain a test fixture, not a hidden production dependency.

### P1 — Register the content template kit

For each template, create a contract row and a disposable fixture before producing many variants. The first content slice should be one of each: one skill, one enemy, one encounter, one portal, one traversal gate, one world challenge, and one state anchor.

### P2 — Scale content only after the gates pass

Once the first fixture set is green, generate variants through data assets and small presentation BPs. Every new skill, enemy, portal, or traversal state must link back to its template, authority owner, test fixture, and save/event contract.

## Acceptance checklist

An asset may be marked L4 only when all of the following are present:

- live parent/CDO/interfaces/components evidence;
- live graph export with required nodes and no forbidden direct ownership;
- compile success from the current editor;
- proof that the configured map/route can reach the asset;
- a disposable fixture or runtime probe with deterministic reset;
- a ledger row naming the owner, authority, evidence date, and retirement path;
- no dependence on ignored files or stale `Saved/Audit` JSON.

## Current blocker and next step

The work is not blocked on design. It is blocked on live verification: the current Unreal Editor process is already running, but Monolith is not reachable. Starting a second editor would create a worse authority collision. The next safe action is therefore to let the in-flight T3D repair finish, then use the existing editor for one read-only Blueprint/GameMode query pass and create the Kawaii probe from fresh live evidence.

## Fresh live evidence — 2026-08-14

The Monolith bridge became reachable briefly during the current editor session.
The configured gameplay asset was queried read-only:

- `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode` is `UpToDate` and
  data-only.
- Its native parent is `GameModeBase`, not `AMelodiaGameMode`.
- It has no Blueprint variables, no Blueprint interfaces, no SCS-added gameplay
  components, and two graph entries (`EventGraph` and
  `UserConstructionScript`).
- The graph inventory reported two EventGraph nodes and one construction-script
  node; the asset is not inheriting the legacy native HUD/input bootstrap.

This converts the former GameMode mismatch from a documentation risk into live
verified evidence. Any input/HUD migration must therefore target the configured
integration route or an owner-approved subsystem/controller seam; reactivating
`AMelodiaGameMode` would create a second authority.

The missing Kawaii fixture was then created additively at
`/Game/MelodiaIntegration/Tests/BP_KawaiiPhysicsPlacementProbe` and saved. The
live mutation responses confirmed:

- `PreviewMesh` (`SkeletalMeshComponent`);
- `PreviewCamera` (`CameraComponent`);
- `ResetAnchor` (`SceneComponent`);
- `PreviewMesh.SkeletalMesh` set to `SK_Melusina`;
- `PreviewMesh.AnimClass` set to `ABP_Melusina_WaterHair`;
- `InitialTransform` (`Transform`) and `bKawaiiDebug` (`bool`) variables;
- `ResetSimulation` custom event.

The editor then entered a long material-save batch that repeatedly opened a
modal `Message Log` window. Monolith became unresponsive before the remaining
debug event, compile, graph export, and integration-map reachability checks
could run. The probe asset is persisted, but it is not yet L3/L4-ready; the
next live pass must inspect the saved graph, finish the reset/debug wiring,
compile, and produce fresh evidence.
