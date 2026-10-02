---
name: turn-combat
description: Build turn-based JRPG combat (scheduler, turn phases, battle zones, encounters, combat config) using the ACF AscentTurnCombat module.
globs: []
alwaysApply: false
---

# Turn Combat — ACF Ultimate

The **AscentTurnCombat** module is a data-driven turn-based (JRPG) battle layer. `UACFBattleManagerComponent` (lives on the **GameState**) drives the whole flow: it loads a `UACFCombatConfigDataAsset`, spawns a `UACFTurnScheduler` to decide *who goes when*, and runs an ordered list of `UACFTurnPhase` objects to decide *what happens each turn*. Battles are triggered by a `UACFBattleZoneStarterComponent` overlap, which positions the party and spawns enemies (from a `UACFEncounterDataAsset`) inside a `UACFBattleZoneComponent`. Combatants act through `UACFTurnAbility` (a `UACFGameplayAbility` subclass) driven by `UACFTurnAbilitySystemComponent`.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Combat Config | `UACFCombatConfigDataAsset` | `/AscentCombatFramework/TurnCombat/Configuration/` | Scheduler + phase pipeline + cameras + end-battle UI; the single asset that defines battle rules |
| Turn Phase | `UACFTurnPhase` (Blueprint) | `/AscentCombatFramework/TurnCombat/` | One step of a turn (menu, AI decision, execute, cleanup) |
| Encounter | `UACFEncounterDataAsset` | `/AscentCombatFramework/TurnCombat/` | Which enemies spawn, battle music, rewards, intro/outro sequences |
| Turn Ability | `UACFTurnAbility` | `/AscentCombatFramework/TurnCombat/` | A combat action (attack/buff/spell) with approach/return movement and damage |

> **Never edit sample assets.** Duplicate the Combat Config, phases, encounters and abilities into `Content/YourGame/TurnCombat/` and reassign your copies. Sample assets under `/AscentCombatFramework/` are overwritten on every plugin update. See `Docs/ACFTurnCombat_CombatConfig_Wiki.md`.

### Key classes

| Class | Role |
|---|---|
| `UACFBattleManagerComponent` | On GameState; owns battle lifecycle, turn order, phase loop. Replicated, server-authoritative |
| `UACFCombatConfigDataAsset` | `UPrimaryDataAsset` holding `TurnInitiativeAttribute`, `SchedulerPolicyClass`, `PlayerPhases`/`EnemyPhases`, `InitCombatPhase`/`EndCombatPhase`, camera tags, end-battle widgets |
| `UACFTurnScheduler` | Abstract instanced policy; computes `TArray<FCombatTurn>` from candidates + initiative attribute |
| `UACFTurnScheduler_Default` | Plain initiative / alternating teams / proportional extra-slots scheduler |
| `UACFTurnScheduler_ATB` | Active-Time-Battle gauge-fill scheduler |
| `UACFTurnPhase` | Instanced/Blueprintable `UObject`; override `OnPhaseStart`/`OnPhaseEnd`, call `CompletePhase()` when done |
| `UACFBattleZoneComponent` | Defines hero/enemy spawn slot transforms; positions party, spawns enemies |
| `UACFBattleZoneStarterComponent` | Trigger that fires `StartCombatFromBattleZone` on player overlap |
| `UACFEncounterDataAsset` | `FACFEnemyGroup` list (`FBaseUnit` + count), music, `FEncounterReward`, level sequences |
| `UACFPartyComponent` | On PlayerController; active/reserve party members, presets, save/load |
| `UACFTurnAbility` | Turn action: targets, approach/return movement, `ApplyAbilityDamage()` |
| `UACFTurnAbilitySystemComponent` | ASC variant used by turn combatants |

---

## 2 — Setup / Configuration

1. **Use `AACFGameState`** (or a subclass) as your GameMode's GameState — it carries `UACFBattleManagerComponent`.
2. **Duplicate the sample Combat Config** from `/AscentCombatFramework/TurnCombat/Configuration/` into `Content/YourGame/TurnCombat/` (e.g. `DA_CombatConfig`).
3. Open your **GameState Blueprint** → select `ACFBattleManagerComponent` → set **`CombatConfigData`** (soft pointer) to **your duplicated asset**.
4. Tune **`InitialSlotsToGenerate`** (default `60`) — number of turn slots the scheduler pre-builds. Higher for ATB-style long queues.
5. In your Combat Config copy, configure:
   - **`TurnInitiativeAttribute`** — the GAS float attribute used to sort turns (default `UACFTurnAttributeSet::Initiative`).
   - **`SchedulerPolicyClass`** — an **instanced sub-object** (not a class dropdown). Set its type to `UACFTurnScheduler_Default`, `UACFTurnScheduler_ATB`, or a custom subclass.
   - **`InitCombatPhase`** / **`EndCombatPhase`** — one-shot phases.
   - **`PlayerPhases`** / **`EnemyPhases`** — ordered per-turn pipelines.
   - **`TurnAbilitiesMovesetTag`** — moveset applied to all combatants at battle start.
   - **`DefaultCharacterCameraTag`** / **`DefaultBattleZoneCameraTag`** — camera blend tags.
   - **`VictoryEndBattleWidget`** / **`DefeatEndBattleWidget`** — end-of-battle UI.

---

## 3 — Core Workflow / Runtime API

### Scheduler — who goes when

`SchedulerPolicyClass` is an instanced object inside the Combat Config.

- **`UACFTurnScheduler_Default`** — set its **Order Mode**: *Plain Initiative* (classic), *Alternating Teams* (interleaves party/enemy), *Proportional* (faster actors get extra slots; tune Max Slots Per Actor, Max Same Team Run).
- **`UACFTurnScheduler_ATB`** — gauge-fill model: tune *Turn Gauge Required*, *Initial Gauge Randomness*, *Enforce Team Alternation*.
- **Custom** — subclass `UACFTurnScheduler` (BP or C++), override `BuildInitialTurnOrder`.

Team-aware modes need labels — call **`TagCombatSides(PartyActors, EnemyActors)`** from your Init phase, or team modes fall back to plain initiative.

### Turn phases — what happens each turn

Each phase is a `UACFTurnPhase` Blueprint. Lifecycle:

```
Battle starts
  → Init Combat Phase  → ... → BattleManager->FinalizeBattleStart()
Turn loop:
  → AdvanceToNextTurn (scheduler picks next actor)
  → Player Phases[] OR Enemy Phases[] (based on turn owner)
       → Phase OnPhaseStart → CompletePhase() → next phase
       → last phase CompletePhase() → auto AdvanceToNextTurn
Victory → End Combat Phase → ApplyReward() → FinalizeBattleEnd(true)
Defeat  → defeat widget directly
```

Inside a phase Blueprint:
- **`Get Turn Owner`** — pawn whose turn it is.
- **`Get Battle Manager`** — the manager component.
- **`Get Turn Owner Ability Comp`** — the pawn's `UACFTurnAbilitySystemComponent`.
- Always call **`CompletePhase()`** when the step finishes, or the battle freezes.
- Set **`PhaseName`** for UI.

### Battle Manager API (server-authoritative)

```
// Lifecycle
BattleManager->InitializeBattleManager();
BattleManager->StartCombatFromBattleZone(Party, Enemies, Zone, EncounterSettings, StartingPC);
BattleManager->FinalizeBattleStart();
BattleManager->EndBattle(bPlayerVictory);
BattleManager->ApplyReward();

// Turn order
BattleManager->BuildInitialTurnOrder(Candidates);
BattleManager->RebuildTurnOrder(Candidates);
BattleManager->AdvanceToNextTurn();
BattleManager->AddCombatantToBattle(Pawn);
BattleManager->RemoveCombatantFromBattle(Pawn);

// Phases
BattleManager->StartCurrentPhase();
BattleManager->AdvanceToNextPhase();
BattleManager->ReturnToPreviousPhase();        // e.g. cancel action → back to menu
BattleManager->AdvanceToSpecificPhase(Phase);

// Queries
bool bInBattle = BattleManager->IsInBattle();
APawn* Active  = BattleManager->GetActiveTurnActor();
APawn* Next    = BattleManager->GetNextTurnActor();
BattleManager->GetTurnPreview(Count, bIncludeActive, OutActors);   // for UI turn order bar
```

### Key delegates

| Delegate | Fires when |
|---|---|
| `OnBattleStarted` | Battle begins |
| `OnBattleEnded(bPlayerVictory)` | Battle ends |
| `OnPhaseChanged(NewPhaseIndex)` | Phase changes |
| `OnActiveTurnChanged(Manager, ActiveActor)` | A new combatant's turn starts |
| `OnTurnBegin(Pawn)` / `OnTurnEnd(Pawn)` | Turn boundaries |
| `OnTurnAbilityStarted/Ended(ability)` | A turn ability runs |
| `OnTurnOrderReady` / `OnRebuildTurnsOrder` | Turn queue (re)built |

### Turn abilities

Subclass `UACFTurnAbility` (BP or C++). Configure `TurnConfig` (`FTurnAbilityConfig`) and `AbilityDamage` (`FAbilityDamage`). The ability auto-handles approach movement to the target and return to origin; override `OnApproachFinished`/`OnReturnFinished`, and call **`ApplyAbilityDamage()`** at the hit moment. Read targets with `GetTargets(OutTargets)`.

---

## 4 — Wire to Characters / Blueprints

### Triggering a battle (battle zone)

1. Place an **`AACFBattleZone`** in the level. On its `UACFBattleZoneComponent`, lay out **`HeroesPositions`** and **`EnemyPositions`** (edit-widget transforms) — these are the spawn slots.
2. Add a **`UACFBattleZoneStarterComponent`** to a trigger actor (or the encounter trigger). Set:
   - **`BattleZone`** → soft ref to the placed battle zone.
   - **`Encounter`** → your duplicated `UACFEncounterDataAsset`.
   - **`bStartOnOverlap = true`**, **`bAutoCreateTrigger`** + **`TriggerRadius`** (or assign **`ExternalTrigger`**).
   - **`bDestroyOwnerOnStart`** / **`DestroyOwnerDelay`** to remove the overworld enemy after combat starts.
3. On player overlap the starter builds enemy specs, positions the party, and calls `StartCombatFromBattleZone`.

### Party

Attach **`UACFPartyComponent`** to your **PlayerController**. Set **`MaxParty`** and **`DefaultPartyConfig`** (array of `FBaseUnit`). Enable `bApplyPresetOnBeginPlay` to spawn the preset. Use `MoveToParty`/`MoveToReserve`, `GetActiveParty`, `CycleThroughPartyMembers` for party management UI.

### Combatants

Every combatant pawn needs a **`UACFTurnAbilitySystemComponent`** and the moveset matching **`TurnAbilitiesMovesetTag`**. Enemies come from the encounter's `FBaseUnit` (soft character class + level + ACF data); the battle zone applies their `UACFCharacterDataAsset` at spawn.

---

## 5 — Verify

**Checklist before testing:**

- [ ] GameState is `AACFGameState` (or carries `UACFBattleManagerComponent`).
- [ ] Combat Config **duplicated** into `Content/YourGame/TurnCombat/` and assigned as `CombatConfigData` on the Battle Manager (not the sample).
- [ ] `SchedulerPolicyClass` instanced object is set (type chosen, not left null).
- [ ] `InitCombatPhase` calls `FinalizeBattleStart()`; `EndCombatPhase` calls `ApplyReward()` + `FinalizeBattleEnd()`.
- [ ] Every phase Blueprint calls `CompletePhase()` on completion.
- [ ] `PlayerPhases` and `EnemyPhases` populated (and different where intended).
- [ ] `TurnInitiativeAttribute` points to a real GAS attribute.
- [ ] `TurnAbilitiesMovesetTag` set; combatants have `UACFTurnAbilitySystemComponent`.
- [ ] Battle Zone has hero + enemy slot transforms; Starter references the zone + your encounter.
- [ ] For team-aware schedulers, `TagCombatSides` is called from the Init phase.
- [ ] `UACFPartyComponent` on PlayerController with `DefaultPartyConfig` set.

**Common failures:**

| Symptom | Fix |
|---|---|
| Battle never starts / no phases run | `CombatConfigData` not assigned on the GameState Battle Manager |
| Scheduler changes have no effect | GameState still points to the sample asset — assign **your duplicate** |
| Phase stuck / battle frozen | A phase never called `CompletePhase()` |
| Init phase runs but turns never begin | Init phase didn't call `FinalizeBattleStart()` |
| Victory but no rewards/UI | End Combat Phase missing `ApplyReward()` + `FinalizeBattleEnd()` |
| Wrong turn order | Wrong scheduler Order Mode; for team modes verify `TagCombatSides` was called |
| Player and enemies run the same steps | Check `PlayerPhases` vs `EnemyPhases` — they're separate arrays |
| Abilities unavailable in battle | `TurnAbilitiesMovesetTag` unset or combatant missing `UACFTurnAbilitySystemComponent` |
| Battle zone spawns nothing | Encounter has no `FACFEnemyGroup`, or zone has no enemy slot transforms |
