---
name: teams
description: Configure team/faction gameplay tags, attitudes (hostile/friendly/neutral), friendly fire, and battle types using the ACF AscentTeams module.
globs: []
alwaysApply: false
---

# Teams — ACF Ultimate

The **AscentTeams** module manages factions and relationships. Each actor carries a **`UACFTeamComponent`** with a team **GameplayTag**. A single **`UACFTeamManagerComponent`** (on the GameState) holds the **`UACFTeamsConfigDataAsset`** that defines every team and its **attitude** (`ETeamAttitude`: Hostile / Friendly / Neutral) toward other teams, plus the global **friendly fire** flag and **battle type** (team-based vs everyone-against-everyone). A **`UACFTeamManagerSubsystem`** (WorldSubsystem) is the convenient read-only entry point used at hit-time to answer "can A damage B?" — it integrates with Unreal's `GenericTeamAgentInterface` so AI perception sees the same attitudes.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Teams Config | `UACFTeamsConfigDataAsset` | `/AscentCombatFramework/.../Teams/` | All teams, display names, attitude relationships, damage collision channels |
| GameState | actor with `UACFTeamManagerComponent` | `AACFGameState` | Holds the config + runtime battle type / friendly fire |
| Character | actor with `UACFTeamComponent` | `/AscentCombatFramework/.../Blueprint/` | Per-actor team membership |

> **Never edit sample assets.** Duplicate the Teams Config into `Content/YourGame/Teams/` and reassign your copy on the Team Manager. Sample assets under `/AscentCombatFramework/` are overwritten on every plugin update.

### Key classes & types

| Symbol | Role |
|---|---|
| `UACFTeamComponent` | Per-actor team tag; queries attitude/hostility; implements `GetGenericTeamId` |
| `UACFTeamManagerComponent` | On GameState; owns the config asset, friendly-fire flag, battle type (server-authoritative) |
| `UACFTeamManagerSubsystem` | WorldSubsystem; read-only attitude/damage queries between actors and teams |
| `UACFTeamsConfigDataAsset` | `TMap<FGenericTeamId, FTeamConfig>` — defines all teams |
| `FTeamConfig` | `TeamTag`, `DisplayName`, `Relationship` (`TMap<Tag, ETeamAttitude>`), `DamageCollisionsChannel` |
| `EBattleType` | `ETeamBased`, `EEveryoneAgainstEveryone` |
| `ETeamAttitude` (engine) | `Hostile`, `Friendly`, `Neutral` |

---

## 2 — Setup / Configuration

1. **Use `AACFGameState`** (or add `UACFTeamManagerComponent` to your GameState).
2. **Duplicate the sample Teams Config** into `Content/YourGame/Teams/` and open your copy.
3. Define teams in **`TeamsConfig`** (`TMap<FGenericTeamId, FTeamConfig>`). For each entry set:
   - **`TeamTag`** — gameplay tag under `Teams.*` (e.g. `Teams.Player`, `Teams.Enemy`).
   - **`DisplayName`** — UI label.
   - **`Relationship`** — map of other `TeamTag` → `ETeamAttitude` (Hostile/Friendly/Neutral). Unlisted teams fall back to the manager's **`DefaultAttitude`**.
   - **`DamageCollisionsChannel`** — collision channels used for hostile damage traces.
4. On the GameState's `UACFTeamManagerComponent`, set:
   - **`TeamConfigDataAsset`** → **your duplicated asset**.
   - **`DefaultAttitude`** (default `Neutral`) — attitude when no explicit relationship exists.
   - **`CurrentBattleType`** (default `ETeamBased`).
   - **`bFriendlyFireEnabled`** (default false).
5. Add a **`UACFTeamComponent`** to each character/pawn and set its **`CurrentTeam`** tag (matching a `TeamTag` in the config).

---

## 3 — Core Workflow / Runtime API

### Per-actor team (`UACFTeamComponent`)

```
// Server-only set
TeamComp->SetTeam(FGameplayTag::RequestGameplayTag("Teams.Enemy"));
TeamComp->ServerRequestTeamChange(NewTeamTag);   // client → server request
FGameplayTag Team = TeamComp->GetTeam();

// Attitude queries
ETeamAttitude::Type A = TeamComp->GetAttitudeTowards(OtherTeamTag);
ETeamAttitude::Type B = TeamComp->GetAttitudeTowardsActor(OtherActor);
bool bHostile  = TeamComp->IsHostileTowards(OtherTeamTag);
bool bFriendly = TeamComp->IsFriendlyWith(OtherTeamTag);
bool bCanDamage = TeamComp->CanDamageTeam(OtherTeamTag);
```

Delegate: **`OnTeamChanged(NewTeam)`** fires when the actor's team changes.

### Global queries (`UACFTeamManagerSubsystem`)

The subsystem is the easiest place to ask relationship questions from anywhere (gameplay code, damage logic, AI):

```
UACFTeamManagerSubsystem* Teams = World->GetSubsystem<UACFTeamManagerSubsystem>();

FGameplayTag Team = Teams->GetActorTeam(Actor);
ETeamAttitude::Type Att = Teams->GetAttitudeBetweenActors(ActorA, ActorB);
bool bHostile = Teams->AreActorsHostile(Attacker, Victim);
bool bCanDamage = Teams->CanActorDamageActor(Attacker, Victim);   // respects friendly fire + battle type

// Team-tag level
bool bH = Teams->AreTeamsHostile(TeamA, TeamB);
bool bD = Teams->CanTeamDamageTeam(AttackerTeam, VictimTeam);

// Tag <-> GenericTeamId
FGenericTeamId Id = Teams->FromTagToTeamId(TeamTag);
FGameplayTag   Tag = Teams->FromTeamIdToTag(Id);

// Collision channels (for damage traces)
TArray<TEnumAsByte<ECollisionChannel>> Chans = Teams->GetHostileCollisionChannels(Team);
```

### Battle type & friendly fire (`UACFTeamManagerComponent`, server only)

```
Manager->SetBattleType(EBattleType::EEveryoneAgainstEveryone);  // free-for-all (everyone hostile)
Manager->SetFriendlyFireEnabled(true);                          // allow same-team damage
bool bFF = Manager->IsFriendlyFireEnabled();
```

`EEveryoneAgainstEveryone` makes every actor hostile to every other regardless of team tags. `IsFriendlyFireEnabled()` returns true automatically in that mode.

### Manager / subsystem events

| Delegate | Fires when |
|---|---|
| `OnTeamChanged(Actor, NewTeam)` | Any actor's team changes (subsystem forwards) |
| `OnFriendlyFireChanged(bEnabled)` | Friendly fire toggled |
| `OnBattleTypeChanged(NewBattleType)` | Battle type changed |

---

## 4 — Wire to Characters / Blueprints

1. **GameState:** ensure the `UACFTeamManagerComponent` has your duplicated `TeamConfigDataAsset` assigned. This is the single source of truth.
2. **Characters:** add `UACFTeamComponent` and set `CurrentTeam` per pawn (player → `Teams.Player`, enemies → `Teams.Enemy`, etc.). Set it server-side via `SetTeam`.
3. **AI perception:** because `UACFTeamComponent` implements `GetGenericTeamId`, Unreal's AI Perception automatically treats actors as hostile/friendly per your config — no extra wiring.
4. **Damage gating:** before applying damage (or when building damage traces in the Collisions Manager), call `UACFTeamManagerSubsystem::CanActorDamageActor(Attacker, Victim)` so friendly fire and battle type are respected. Use `GetHostileCollisionChannels` to limit weapon traces to valid targets.
5. **Runtime changes:** call `SetBattleType` / `SetFriendlyFireEnabled` on the server (e.g. for arena modes); clients react via the replicated state and events.

---

## 5 — Verify

**Checklist before testing:**

- [ ] GameState is `AACFGameState` (or has `UACFTeamManagerComponent`).
- [ ] Teams Config **duplicated** to `Content/YourGame/Teams/` and assigned as `TeamConfigDataAsset`.
- [ ] Every team that fights has a `FTeamConfig` entry with a `TeamTag` and `Relationship` map.
- [ ] Each pawn has a `UACFTeamComponent` with a `CurrentTeam` matching a config `TeamTag`.
- [ ] `DefaultAttitude` set intentionally (Neutral by default — unlisted pairs won't fight).
- [ ] Team changes are made on the server (`SetTeam` / `ServerRequestTeamChange`).
- [ ] Damage logic / traces consult `CanActorDamageActor` and hostile collision channels.

**Common failures:**

| Symptom | Fix |
|---|---|
| Everyone is neutral / nobody fights | Teams not listed in each other's `Relationship`, and `DefaultAttitude` is Neutral |
| Allies damage each other | `bFriendlyFireEnabled` true, or battle type set to `EEveryoneAgainstEveryone` |
| Enemies ignore the player | Player pawn's `UACFTeamComponent` team tag doesn't match a hostile relationship entry |
| AI perception sees wrong attitude | Team tag/`GetGenericTeamId` mismatch; verify `FromTagToTeamId` mapping in the config |
| Team change has no effect on clients | Called on a client without authority — use `SetTeam` (server) or `ServerRequestTeamChange` |
| Damage traces hit nothing | Wrong `DamageCollisionsChannel` for the team; check `GetHostileCollisionChannels` |
| Config edits lost after update | You edited the sample asset — use your duplicate and reassign on the manager |
