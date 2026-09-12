# 029a GameMode Authority and Retirement Inventory

Date: 2026-08-14  
Status: static inventory complete; live Blueprint/WorldSettings proof still required  
Prerequisite: T3D safety repair `c6ef5f6c`, pure suite 42/42

## Decision

The project should keep one gameplay GameMode authority: the configured
`/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode` candidate. The
legacy native `AMelodiaGameMode`, mobile `AMelodiaMobileGameMode`, and dead
`/Game/Melodia/_PROJECT/BP_MelodiaGameMode` lane must receive no new gameplay
ownership while their live references are being verified.

This is a retirement/quarantine decision, not a deletion instruction. Existing
asset parents and reflected classes must remain loadable until a live
referencer/compile pass proves they can be removed.

## Static evidence

| Evidence | Finding | Confidence |
|---|---|---|
| `Config/DefaultEngine.ini:16` | `GlobalDefaultGameMode=/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode.BP_MelodiaJRPGGameMode_C` | Configured intent only |
| `MelodiaGameMode.h/.cpp` | Native mode bootstraps HUD, battle input, battle-session delegates, loop phases, and results UI | Source fact |
| `MelodiaMobileGameMode.h/.cpp` | Native mobile mode supplies mobile HUD class, landscape, and touch defaults behind mobile platform guards | Source fact |
| `Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md:83-84` | `UMelodiaBattleInputComponent` is created by `AMelodiaGameMode`, while the configured mode is `BP_MelodiaJRPGGameMode` | Documented risk; requires live proof |
| `Content/Melodia/_PROJECT/BP_MelodiaGameMode.uasset` | Legacy Blueprint exists and is documented as having zero referencers | Stale/indirect until live query |
| `Content/Melodia/UI/WBP_Battle_Mobile.uasset` | Mobile widget asset exists; native parent is documented as `UMelodiaMobileHUD` | Asset fact; live referencer unverified |
| `Content/MelodiaIntegration/Tests/BP_T3DSafeWireProbe.uasset` | Disposable T3D fixture exists | Asset fact |

Fresh static audit evidence (rerun 2026-08-14): `python Tools/battle_path_static_audit.py` confirms the
configured global mode remains
`/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode`, the configured GameInstance
and cook map set resolve on disk, and `monolith_reachable: false`. Live map overrides,
actor counts, and referencers were therefore skipped as designed. Report:
`Saved/Audit/battle_static_1786744243.json`.

## What the quarantined desktop GameMode actually owns

`AMelodiaGameMode` is not an empty class. Its current implementation performs
these responsibilities:

1. Sets `AMelodiaSmokeCharacter` as the default pawn in its constructor.
2. Delays bootstrap by 0.5 seconds during `BeginPlay`.
3. Spawns a `UMelodiaRhythmHUDWidget` and adds it to the viewport.
4. Finds or dynamically creates `UMelodiaBattleInputComponent` on the player
   pawn and enables automatic input binding.
5. Binds `UMelodiaBattleSession::OnBattlePhaseChanged` and
   `OnEncounterEnded` delegates.
6. Tracks `Bootstrapping`, `Exploration`, `Battle`, and `VictoryReward` loop
   phases.
7. Updates HUD prompts and phase banners as battle phases change.
8. Spawns `UMelodiaBattleResultsWidget` after victory or defeat.
9. Returns HUD presentation to exploration after an encounter ends.

These responsibilities explain why blindly deleting the native class would be
unsafe. They do not justify restoring it as a second live authority.

## What the mobile GameMode owns

`AMelodiaMobileGameMode` is narrower:

- `MobileHUDClass` is a `UMelodiaMobileHUD` subclass slot.
- `bForceLandscape` defaults to true.
- `bUseTouchInput` defaults to true.
- On iOS/Android only, it applies viewport orientation and player-controller
  touch/cursor settings.

It does not implement the desktop battle-session bootstrap. Its existence is
compatible with a future mobile route, but it must not be used as the desktop
authority or receive desktop combat wiring.

## Migration matrix

| Legacy responsibility | Intended owner after 029a | Current status | Required proof |
|---|---|---|---|
| Default pawn selection | `BP_MelodiaJRPGGameMode` / configured player route | Unverified | Live CDO and effective WorldSettings query |
| Battle input creation | Existing player-controller/character integration contract | Risk: native legacy mode creates it; configured mode may not | Live component inventory plus PIE input smoke test |
| Battle-session binding | Stock battle/session authority and integration bridge | Do not duplicate in a BP until path is proven | Live referencer and delegate-path audit |
| Rhythm HUD spawn | Active stock/integration presentation authority | Legacy native method only | Live UI referencer and viewport proof |
| Battle results presentation | Stock results contract | Legacy native method only | Live battle completion fixture |
| Loop-phase enum/state | Canonical gameplay state contract | Legacy native enum remains quarantined | Identify one state authority before adding traversal states |
| Mobile orientation/touch | Mobile platform route | Separate and currently unverified | Platform-specific route test; no desktop edits |
| Dead legacy widget references | None unless owner reactivates the lane | `BP_MelodiaGameMode` is not configured | Live zero-referencer report before cleanup |

## Required live audit

When the existing Unreal Editor becomes reachable, perform these read-only
queries before any migration edit:

1. Query `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode` parent,
   CDO, interfaces, components, graphs, and compile state.
2. Query WorldSettings for:
   - `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`;
   - `/Game/Melodia/Levels/Opening/L_MelusinaMorning`;
   - `/Game/EnvSandbox/Environments/L_KaleidoNave`;
   - the Dreamstate map if it remains in the active P0 slice.
3. Prove the effective GameMode on each map; global config alone is not enough.
4. Find live references to:
   - `AMelodiaGameMode`;
   - `AMelodiaMobileGameMode`;
   - `/Game/Melodia/_PROJECT/BP_MelodiaGameMode`;
   - `WBP_Battle_Mobile`;
   - the configured battle bridge and player controller.
5. Inspect whether the configured route creates or receives
   `UMelodiaBattleInputComponent` without relying on the quarantined mode.
6. Compile the configured mode and all directly affected Blueprints.

Do not infer any of these results from stale `Docs/T3D_Baseline` exports or
`Saved/Audit` JSON.

## Safe retirement sequence

### Gate A — prove the live route

The configured GameMode and map overrides must be known from the running editor.
If the active route is ambiguous, stop and resolve authority before authoring
new skills, enemies, portals, or traversal gates.

### Gate B — preserve required behavior

If the live route lacks the old input bootstrap, move the smallest required
behavior into the existing player-controller/character integration contract or
another owner-approved runtime seam. Do not reactivate `AMelodiaGameMode` just
to obtain one component.

### Gate C — prove mobile separation

Keep `WBP_Battle_Mobile` and `UMelodiaMobileHUD` available for a future mobile
route. Confirm their active parent/referencer before changing the native mobile
class. Mobile work must not introduce desktop GameMode coupling.

### Gate D — quarantine legacy assets

After live zero-referencer proof and owner review, mark the legacy GameMode and
its widget-only references as retired. Do not delete them in the same change as
the gameplay authority migration.

## Relationship to the BP expansion kit

The reusable BP kit remains valid, but every template must call into the
resolved authority rather than reproducing legacy GameMode behavior:

- skills request stock battle execution;
- enemies and encounters request stock battle/session flow;
- portals and traversal gates request the travel/traversal subsystems;
- world challenges and state anchors use the canonical save/event contract;
- Kawaii presentation remains an AnimBP/fixture concern, not GameMode logic.

The first Kawaii fixture is still missing. `ABP_Melusina_WaterHair` is the
runtime reference; `BP_PhysicsPlacementSpawner` is only a generic rigid-body
fixture and cannot satisfy this gate.

## Completion evidence for 029a

029a is complete only when the repository contains:

- a fresh live GameMode/WorldSettings report;
- a live referencer report for both native modes and the legacy BP;
- a compile result for the configured route;
- an input/battle smoke result on the effective route;
- an owner-approved retirement/quarantine decision;
- no new BP content wired to the quarantined authorities.

Current state: static inventory complete; live evidence and owner decision remain
open. The Monolith endpoint is currently unavailable, so no retirement mutation
has been attempted.
