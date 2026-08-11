# Battle → Narrative Binding Design
**Date**: 2026-08-03  
**Author**: opencode (UE 5.8 C++ gameplay systems engineer)  
**Status**: Design / Planning — read-only; no files modified

---

## A. Architecture Decision

**Chosen: Option 1 — Self-binding in `UMelodiaNarrativeSubsystem`**

The binding listener lives inside `UMelodiaNarrativeSubsystem` itself (`Initialize()` / `Deinitialize()`), extending the pattern already used for Quill events. Rationale:

- `UMelodiaBattleSession` (MelodiaCore plugin) is a **GameInstanceSubsystem** — same scope as `UMelodiaNarrativeSubsystem`. No world-scanning, no actor component registration, no BP involvement needed.
- The `UMelodiaBattleSession::OnEncounterEnded` multicast delegate (`FMelodiaOnEncounterEnded`, param `EMelodiaEncounterResult`) fires at the terminal point of every encounter (Victory / Defeat / Fled).
- `UMelodiaNarrativeSubsystem::CompleteBattle(EMelodiaBattleResult Result)` is already implemented, idempotent-safe, and handles: clearing `PendingEncounterId`, setting `melodia_battle_won` flag, writing `melodia_battle_result` Quill variable, broadcasting `OnBattleCompleted`, and calling `ResumeQuillOnce()`.
- Zero changes to the stock JRPG template (`BP_BattleController`). Zero changes to `BP_MelodiaJRPGGameInstance` (its existing `TravelTo` nodes for `ChangeMapForBattle` remain connected to `OnBattleRequested`).

**Rejected options:**

| Option | Why rejected |
|--------|-------------|
| **2: New adapter class** | Adds an unnecessary indirection layer. The subsystem is the natural owner. |
| **3: GameInstance Blueprint** | Ruled out by the user ("C++ binding over Blueprint for long-term robustness"). Also confirmed missing: `BindEvent` to `OnBattleRequested` and `StartBattle`/`CompleteBattle` calls are absent from `BP_MelodiaJRPGGameInstance`. |

---

## B. Implementation Plan

### Files to Modify

| File | Change |
|------|--------|
| `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.h` | Add `UFUNCTION()` handler `HandleEncounterEnded(EMelodiaEncounterResult Result)` in `private:` section |
| `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.cpp` | Bind `OnEncounterEnded` in `Initialize()`, unbind in `Deinitialize()`, implement handler with result mapping |

No other files touched. No schema changes. No Blueprint edits.

### Binding Logic (Pseudocode)

#### `Initialize()` — add after existing Quill bindings (line 65):

```cpp
if (UMelodiaBattleSession* BattleSession = GetGameInstance()->GetSubsystem<UMelodiaBattleSession>())
{
    BattleSession->OnEncounterEnded.AddUniqueDynamic(this, &ThisClass::HandleEncounterEnded);
}
```

#### `Deinitialize()` — add before `Super::Deinitialize()` (line 79):

```cpp
if (UMelodiaBattleSession* BattleSession = GetGameInstance()->GetSubsystem<UMelodiaBattleSession>())
{
    BattleSession->OnEncounterEnded.RemoveDynamic(this, &ThisClass::HandleEncounterEnded);
}
```

#### New handler:

```cpp
void UMelodiaNarrativeSubsystem::HandleEncounterEnded(EMelodiaEncounterResult Result)
{
    if (PendingEncounterId.IsNone())
    {
        // No narrative-driven battle is pending; ignore results from free
        // encounters (e.g. random encounters, training).
        return;
    }

    EMelodiaBattleResult NarrativeResult;
    switch (Result)
    {
    case EMelodiaEncounterResult::Victory: NarrativeResult = EMelodiaBattleResult::Victory; break;
    case EMelodiaEncounterResult::Defeat:  NarrativeResult = EMelodiaBattleResult::Defeat;  break;
    case EMelodiaEncounterResult::Fled:    NarrativeResult = EMelodiaBattleResult::Fled;    break;
    default:                               NarrativeResult = EMelodiaBattleResult::Unavailable; break;
    }

    CompleteBattle(NarrativeResult);
}
```

### CompleteBattle Flow (Existing, Verified)

```
HandleEncounterEnded(Result)
  └─ CompleteBattle(NarrativeResult)
       ├─ Guards: !PendingEncounterId.IsNone() && !bBattleCompletionConsumed
       ├─ Clears PendingEncounterId, sets bBattleCompletionConsumed = true
       ├─ Sets narrative flag melodia_battle_won (Victory=true, else false)
       ├─ Writes melodia_battle_result Quill variable (victory/defeat/fled/unavailable)
       ├─ Broadcasts OnBattleCompleted(EncounterId, Result)
       ├─ Writes MELUSINA_LOOP_BATTLE_COMPLETED log
       └─ ResumeQuillOnce()
            ├─ Interpreter->Restore()  — restores checkpoint
            └─ Interpreter->Next()     — advances to next beat (branches on melodia_battle_result)
```

### Error Handling

| Scenario | Behavior |
|----------|----------|
| **Unknown encounter ID** (StartBattle) | `Reject(Intent, UnknownIdentifier)` via `IsAllowed()` — `Config->EncounterIds` check |
| **Duplicate completion** (CompleteBattle called twice) | `Reject("CompleteBattle", Duplicate)` — `bBattleCompletionConsumed` guard |
| **Race: battle ends without StartBattle** (random encounter) | `HandleEncounterEnded` returns early — `PendingEncounterId.IsNone()` guard |
| **Missing interpreter** at completion time | `Reject("CompleteBattle", MissingRuntime)` — `ActiveInterpreter.IsValid()` check |
| **Aborted battle** (integration failure) | `AbortPendingBattle(Reason)` — clears pending, broadcasts `OnBattleAborted`, resumes Quill with `unavailable` result |

---

## C. Risks and Mitigations

### 1. Does BP_BattleController expose its battle-starting API as BlueprintCallable?

**Not needed.** The battle-starting path (`OnBattleRequested`) is already delegated to Blueprint via `BP_MelodiaJRPGGameInstance`'s `TravelTo` nodes for `ChangeMapForBattle`. The BP_BattleController's `InitBattle` custom event (confirmed via Monolith: `K2Node_CustomEvent_0`) is triggered by the map load sequence, not directly by narrative.

The `UMelodiaBattleSession::BeginEncounter(FMelodiaEncounterDefinition)` is BlueprintCallable and is the correct way to start an authored encounter. However, in this phase, the stock JRPG template owns the encounter trigger (via `BP_BattleBase` → `currentBattle`). The narrative layer only needs to request travel to the battle map; the template handles the rest.

### 2. How does the result matrix connect to CompleteBattle?

**Via `UMelodiaBattleSession::OnEncounterEnded`.**

Monolith-confirmed execution chain in `BP_BattleController::EventGraph`:
```
OnBattleOver (custom event)
  → FadeOut (AudioComponent::FadeOut)
  → HideBattleUI (BP_BattleUI::HideBattleUI)
  → Switch on E_BattleResult
       ├── NewEnumerator0 (Victory) → PlayerWon → UpdatePlayerUnitsData → AddGold → ... → SwitchToExploreMode
       ├── NewEnumerator1 (Defeat)  → EnemyWon → Delay 2s → PlayVictoryAnimation → ... → CreateWidget
       └── NewEnumerator2 (Fled)    → Map_Keys → UpdatePlayerUnitsData → SwitchToExploreMode
```

The `UMelodiaBattleSession` internally calls `EndEncounter(Result)` before the result switch runs, which broadcasts `OnEncounterEnded`. Our handler catches this broadcast, maps `EMelodiaEncounterResult → EMelodiaBattleResult`, and calls `CompleteBattle`.

**Result mapping** (confirmed by reading MelodiaBattleTypes.h):

| `EMelodiaEncounterResult` | `EMelodiaBattleResult` |
|--------------------------|----------------------|
| `None`                   | `Unavailable`        |
| `Victory`                | `Victory`            |
| `Defeat`                 | `Defeat`             |
| `Fled`                   | `Fled`               |

### 3. Thread safety concerns with Quill interpreter resume?

**Minimal.** Everything runs on the game thread in UE 5.8:

- `UMelodiaBattleSession::OnEncounterEnded` fires from `EndEncounter()` which is called from `CheckVictoryOrDefeat()` on the game thread during the battle turn lifecycle.
- `CompleteBattle` calls `ResumeQuillOnce()` which calls `Interpreter->Restore()` and `Interpreter->Next()` — both game-thread operations.
- The `ActiveInterpreter` weak pointer is only written on the game thread (in `HandleQuillScriptPlay`).

The only concern is re-entrancy if `OnEncounterEnded` fires while Quill is still processing. However, `CompleteBattle` has the `bBattleCompletionConsumed` guard that prevents re-entry, and `StartBattle` has the `Busy` guard (`PendingEncounterId.IsNone()`). These are sufficient for the single-threaded game-loop model.

---

## Appendix: Monolith Query Results

### blueprint_query get_graph_summary — BP_BattleController
```
Asset: /Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController
Parent class: Actor
Graphs: EventGraph (678 nodes), UserConstructionScript (1), GetReadyUnitsBasedOnAT (29),
        CalculateDamage (38), IsHit (25), GetLeveledUpUnits (31), MoveToTarget (10),
        GetReadyUnitsBasedOnSpeed (34), DealDamage (16), GetBattleLevelName (17),
        GetBattleLevelTransition (13), GetBattleTransition (12 macro),
        GetNextReadyUnit (5 macro), SwitchToStaticCamera (10 macro),
        UnitHasEnoughMP (8 macro), OnTurnChanged (delegate), OnActionTimeAdded (delegate)

Key components: DefaultSceneRoot, BattleThemeAudio, VictoryThemeAudio, ExploreThemeAudio,
                MelodiaRhythmAudio (MelodiaAudioComponent),
                MelodiaPresentationRhythm (MelodiaJRPGPresentationRhythmComponent)

Key variables: battleResult (byte/E_BattleResult), isBattleOver (bool), isPlayerVictory (bool),
               currentBattle (BP_BattleBase_C), jRPGPlayerController (BP_JRPGPlayerController_C)

Key custom events: InitBattle, SwitchToBattleMode, StartTransition, OnBattleOver,
                   PlayerWon, EnemyWon

Result switch: K2Node_SwitchEnum_0 "Switch on E_BattleResult"
  → NewEnumerator0 (Victory) → PlayerWon → Map_Keys → UpdatePlayerUnitsData → AddGold → ...
  → NewEnumerator1 (Defeat)  → EnemyWon → Delay 2s → PlayVictoryAnimation → ...
  → NewEnumerator2 (Fled)    → Map_Keys → UpdatePlayerUnitsData → SwitchToExploreMode
```

### cppreflect_query get_uclass — UMelodiaBattleSession
```
Class: UMelodiaBattleSession (GameInstanceSubsystem)
Module: MelodiaCore
Source: Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleSession.h:59
Parent chain: empty (no parent)
Key BlueprintCallable functions: BeginEncounter, SubmitBasicCommand, SubmitSkillCommand,
                                 SubmitUltimateCommand, SubmitFleeCommand, ConfirmVictoryReward,
                                 RestorePersistentPartyHealth, RestorePersistentSkillPoints,
                                 RestorePersistentPartyState
Key delegates: OnBattlePhaseChanged (FMelodiaOnBattlePhaseChanged),
               OnEncounterEnded (FMelodiaOnEncounterEnded — param EMelodiaEncounterResult)
Key accessors: GetBattleController(), GetCombatState(), GetLastEncounterResult(),
               GetLastBattleResults(), IsEncounterActive()
```

### project_query get_asset_details — DA_MelodiaIntegrationConfig
```
Asset: /Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig
Class: MelodiaIntegrationConfig
Last modified: 2026-08-01T16:34:02
References: none (no depends_on or referenced_by)
```
*(No EncounterIds populated in the config as of this scan — allowlist must be filled before battle binding can function.)*

---

## Summary of Binding

1. **Start**: `HandleQuillNotification("melodia:battle:<EncounterId>")` → `StartBattle(Id)` → broadcasts `OnBattleRequested` → `BP_MelodiaJRPGGameInstance` (via existing TravelTo) → `ChangeMapForBattle`
2. **Battle**: Stock JRPG template runs the encounter; `UMelodiaBattleSession` manages phase machine
3. **End**: `UMelodiaBattleSession::OnEncounterEnded` fires → new `HandleEncounterEnded` handler maps result → `CompleteBattle()` → `ResumeQuillOnce()` → Quill interpreter branches on `melodia_battle_result`

**Two files changed, zero new classes, zero Blueprint edits, zero template modifications.**
