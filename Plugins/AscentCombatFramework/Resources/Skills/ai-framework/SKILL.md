---
name: ai-framework
description: Create, configure and wire NPC AI in ACF — behavior-tree controllers, combat behaviour, threat management, patrol/splines, group spawners and wave systems.
globs: []
alwaysApply: false
---

# AI Framework — ACF Ultimate

The **AIFramework** module is the full NPC brain for ACF. Each NPC is an `AACFCharacter` possessed by an `AACFAIController`, which drives an Unreal **Behavior Tree** through a Blackboard and a set of ACF components: `UACFCombatBehaviourComponent` (how it fights), `UACFThreatManagerComponent` (who it hates most), `UACFAIPatrolComponent` (where it walks), and `UACFCommandsManagerComponent` (player/lead orders). Crowds are organized by `UACFGroupAIComponent` on an `AACFAIGroupSpawner`, and arena/horde encounters are driven by `UACFAIWavesMasterComponent` with `FWaveConfig` waves. This skill covers building a new NPC, its combat behaviour, patrols, groups and waves.

Useful reference docs in the repo: `Docs/AIFramework_Wiki.md` and `Docs/ACFThreatManager_Wiki.md`.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Sample NPC character | `AACFCharacter` (BP subclass) | `/Game/FullSample/` | The possessed pawn (mesh, stats, equipment, AI controller class) |
| AI Controller | `AACFAIController` (BP subclass) | `/Game/FullSample/` (assigned on the NPC) | Possesses the NPC, owns the Behavior Tree + AI components |
| Behavior Tree | `UBehaviorTree` | `/AscentCombatFramework/` AI content | Decision tree assigned on the controller's `BehaviorTree` |
| Combat behaviour | `UACFCombatBehaviorDataAsset` / `UACFBaseCombatBehaviorDataAsset` | sample AI folders | DataAsset of conditional combat actions (`ActionByCondition`) |
| Character DataAsset | `UACFCharacterDataAsset` | sample character configs | Stats, starting items, AI config consumed by spawners |
| Group spawner | `AACFAIGroupSpawner` | `/Game/FullSample/` | Pawn that spawns and coordinates a group/team |
| Spline patrol path | `AACFSplinePath` | placed in level | Waypoints for `EFollowSpline` patrols |
| AI routine | `UACFAIRoutineDataAsset` | sample routines | Time-of-day task schedule (`FAIRoutineTask`) |

> **Never edit sample assets.** Duplicate the sample NPC, controller, behaviour DataAsset and behavior tree into your own folder (e.g. `Content/YourGame/AI/`) and customize **your copies**. Editing the originals means your work is lost on the next plugin/sample update.

### Key classes

| Class | Role |
|---|---|
| `AACFAIController` | Possesses the NPC; owns BT + Blackboard, targeting, threat, combat behaviour, commands, patrol |
| `UACFCombatBehaviourComponent` | Picks combat actions/states; resolves ideal distance and melee range; equips weapon on engage |
| `UACFThreatManagerComponent` | Tracks per-actor threat; raises `OnNewMaxThreateningActor` when the top threat changes |
| `UACFAIPatrolComponent` | Patrol loop in `EFollowSpline` or `ERandomPoint` mode |
| `UACFCommandsManagerComponent` | Executes commands like FollowMe / GoThere (companions) |
| `UATSAITargetComponent` | The AI's targeting component (from the Targeting System) |
| `AACFAIGroupSpawner` | Spawns a coordinated group, assigns team via `UACFTeamComponent` |
| `UACFGroupAIComponent` | Group brain: membership, formations, lead |
| `UACFAIWavesMasterComponent` | Wave/horde controller driving `FWaveConfig` waves |
| `AACFSplinePath` | Spline waypoint actor for patrols |
| `UACFAIRoutineComponent` / `UACFAIRoutineDataAsset` | Daily schedule of `UACFTask` entries by `FRoutineTime` |

### Important enums / structs

- `EAICombatState`: `EMeleeCombat`, `EChaseTarget`, `ERangedCombat`, `EStudyTarget`, `EFlee`.
- `EPatrolType`: `EFollowSpline`, `ERandomPoint`.
- AI state tags (string): `AIState.Patrol`, `AIState.Combat`, `AIState.ReturnHome`, `AIState.FollowLead`, `AIState.Wait`, `AIState.Routine`.
- `FWaveConfig`: `GroupSpawner`, `WaveAgentsOverride` (`FAISpawnInfo[]`), `secondsDelayToNextWave`.

---

## 2 — Setup / Configuration

### A. Create your NPC and AI controller

1. **Duplicate** a sample NPC `AACFCharacter` Blueprint and a sample `AACFAIController` Blueprint into `Content/YourGame/AI/`.
2. On your NPC Blueprint, set the **AI Controller Class** to your duplicated controller, and **Auto Possess AI** = `Placed in World or Spawned`.
3. On your controller Blueprint, assign `BehaviorTree` to your duplicated Behavior Tree asset.
4. Set `DefaultState` (e.g. the `AIState.Patrol` tag) and fill `LocomotionStateByAIState` to map each AI state tag to an `ELocomotionState` (Walk/Jog/Run).

### B. Configure perception & combat ranges on the controller

On the duplicated `AACFAIController` defaults:
- `bIsAggressive` — attack enemies as soon as they are perceived.
- `bShouldReactOnHit` — play a hit reaction when damaged.
- `LoseTargetDistance` — distance at which the AI drops its current target.
- **Home**: `bBoundToHome` + `MaxDistanceFromHome` — return home when wandering too far.
- **Teleport** (for companions/large maps): `bTeleportToLead`, `TeleportToLeadTriggerDistance`, `TeleportNearLeadRadius`.

### C. Create the combat behaviour DataAsset

1. **Duplicate** a sample `UACFCombatBehaviorDataAsset` into `Content/YourGame/AI/`.
2. Populate `ActionByCondition` (`FConditions`): each entry pairs a `UACFActionCondition` (e.g. `UACFDistanceActionCondition`) with an action tag and a trigger chance. This is the modern, condition-driven path.
3. Assign it on the NPC's `UACFCombatBehaviourComponent.CombatBehaviour`, and set the default action tags `EquipMeleeAction`, `EquipRangedAction`, `EngagingAction`.

> The `CombatStatesConfig`, `ActionByCombatState` and `DefaultCombatBehaviorType` fields are marked **DEPRECATED** — prefer `ActionByCondition` on the behaviour DataAsset for new content.

### D. Threat tuning

On `UACFThreatManagerComponent`:
- `DefaultThreatMap` — `TMap<TSubclassOf<AActor>, float>` initial threat per actor class perceived.
- `ThreatMultipliersByActor` — per-class multiplier applied to threat added.

### E. Patrol setup

1. Add a `UACFAIPatrolComponent` to the NPC (sample NPCs already have one).
2. Set `PatrolType`:
   - `EFollowSpline` → place an `AACFSplinePath` in the level and assign it to `PathToFollow` (or to `FAISpawnInfo.PatrolPath` in a spawner).
   - `ERandomPoint` → set `RandomPatrolRadius` around the AI's home.
3. Set `WaitTimeAtPoint` (seconds to idle at each waypoint).

---

## 3 — Core Workflow / Runtime API

### Targeting & state (on `AACFAIController`)

```
AICtrl->SetTarget(TargetActor);        // force a target
AActor* T = AICtrl->GetTarget();       // current target
bool bHas = AICtrl->HasTarget();
AICtrl->RequestAnotherTarget();        // ask threat/targeting for a new one
bool bBattle = AICtrl->IsInBattle();

AICtrl->SetCurrentAIState(StateTag);   // e.g. AIState.Combat
AICtrl->ResetToDefaultState();
AICtrl->SetCombatStateBK(EAICombatState::EChaseTarget);
```

### Threat (on `UACFThreatManagerComponent`)

```
Threat->AddThreat(Attacker, 50.f);
Threat->RemoveThreat(Attacker, 20.f);
AActor* Top = Threat->GetActorWithHigherThreat();
Threat->RemoveThreatening(DeadActor);
// React to a new top threat:
Threat->OnNewMaxThreateningActor.AddDynamic(this, &MyClass::HandleNewTopThreat);
```

### Combat behaviour (on `UACFCombatBehaviourComponent`)

```
Behaviour->TryExecuteConditionAction();                 // evaluate ActionByCondition
Behaviour->TryExecuteActionByCombatState(EAICombatState::EMeleeCombat);
bool bMelee = Behaviour->IsTargetInMeleeRange(Target);
float dist  = Behaviour->GetIdealDistanceByCombatState(EAICombatState::ERangedCombat);
Behaviour->SetCombatBehaviour(MyBehaviourDataAsset);    // swap behaviour at runtime
```

### Patrol (on `UACFAIPatrolComponent`)

```
Patrol->SetPatrolType(EPatrolType::EFollowSpline);
Patrol->SetPathToFollow(MySplinePath);
Patrol->StartPatrolLoop(true);   // bind to controller move-completed and start
Patrol->StopPatrolLoop();
```

### Groups (on `AACFAIGroupSpawner` / `UACFGroupAIComponent`)

```
int32 n = Spawner->GetGroupSize();
AACFCharacter* near = Spawner->GetAgentNearestTo(Location);
FAIAgentsInfo agent;
Spawner->GetAgentWithIndex(0, agent);
FGameplayTag team = Spawner->GetCombatTeam();
```

### Waves (on `UACFAIWavesMasterComponent`) — **call server-side**

```
Waves->StartWave();                                  // begin from first wave
Waves->AddAgentToWave(0, EnemyClass, 3);             // server RPC
Waves->ProceedToNextWave();                          // server RPC (auto on wave end)
int32 idx = Waves->GetCurrentWaveIndex();
// Events:
Waves->OnWaveStarted / OnWaveEnded / OnWaveProgressed / OnAllWavesEnded
```

---

## 4 — Wire to Characters / Blueprints

1. **NPC → controller**: NPC Blueprint `AI Controller Class` = your duplicated `AACFAIController`; the controller auto-creates its BT/Blackboard/combat/threat/targeting/commands/patrol components on possess.
2. **Behavior Tree → services**: the BT uses ACF services (`ACFUpdateStateBTService`, `ACFUpdateCombatBTService`, `ACFUpdatePatrolBTService`, `ACFCheckActionsBTService`) and tasks (`ACFPatrolSplinePathTask`, `ACFFollowSplinePathTask`, `ACFRandomPatrolAroundPointTask`). Keep these wired when duplicating — they write/read the Blackboard keys the controller manages.
3. **Hit/death reactions**: bind `AACFAIController.OnDamageReceived` / `OnPawnDeath`, or rely on `bShouldReactOnHit`. The controller internally feeds damage into the threat manager.
4. **Groups**: place an `AACFAIGroupSpawner`, configure its agents and `UACFTeamComponent` team tag, set `bSpawnOnBeginPlay` (or call spawn from BP). Spawned members get a `GroupOwner` and a `GroupIndex` for formations.
5. **Waves**: put a `UACFAIWavesMasterComponent` on a manager actor; fill `Waves` (`FWaveConfig`) referencing your group spawners (or `WaveAgentsOverride`), then call `StartWave()` from the server (e.g. a trigger volume).
6. **Routines (towns/villagers)**: add `UACFAIRoutineComponent`, assign a duplicated `UACFAIRoutineDataAsset` with `FAIRoutineTask` entries (a `FRoutineTime` + a `UACFTask`); the AI switches to the `AIState.Routine` state to run them.

---

## 5 — Verify

**Checklist before testing:**

- [ ] NPC, AI controller, behavior tree and combat-behaviour DataAsset are **duplicates** under `Content/YourGame/AI/`.
- [ ] NPC `AI Controller Class` points to your controller and **Auto Possess AI** is set.
- [ ] Controller `BehaviorTree` is assigned and `DefaultState` is a valid `AIState.*` tag.
- [ ] `LocomotionStateByAIState` has an entry for each state the AI uses.
- [ ] AI Perception is configured (sight/hearing) and `bIsAggressive` matches intent.
- [ ] Combat behaviour `ActionByCondition` has at least one valid condition+action, and `EquipMeleeAction`/`EngagingAction` tags are set.
- [ ] Threat `DefaultThreatMap` lists the player/enemy classes so perception generates threat.
- [ ] Patrol: spline assigned for `EFollowSpline`, or `RandomPatrolRadius > 0` for `ERandomPoint`.
- [ ] Group spawner has a valid team tag and agent list; waves are started **server-side**.

**Common failures:**

| Symptom | Fix |
|---|---|
| NPC spawns but never moves/acts | No `BehaviorTree` assigned, or BT not started — check controller `BehaviorTree` and Auto Possess AI |
| AI sees the player but never attacks | `bIsAggressive = false`, missing AI Perception, or empty `DefaultThreatMap` so no threat is generated |
| AI attacks but stands still / wrong range | Combat behaviour distances misconfigured — verify `GetIdealDistanceByCombatState` / melee range via the behaviour DataAsset |
| Patrol does nothing | `StartPatrolLoop` never called, wrong `PatrolType`, missing `AACFSplinePath`, or `RandomPatrolRadius = 0` |
| AI keeps running back home mid-fight | `MaxDistanceFromHome` too small with `bBoundToHome` — raise it or disable via `DisableReturnHomeCheck()` |
| Waves never start / only host sees enemies | `StartWave()` / `AddAgentToWave` must run on the **server**; verify authority |
| Whole group shares one target oddly | Threat/targeting is group-aware — confirm each member has its own threat component and correct team tag |
