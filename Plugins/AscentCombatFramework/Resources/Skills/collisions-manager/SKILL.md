---
name: collisions-manager
description: Set up trace-based weapon/damage collision detection (swing traces, area damage, impact FX) on characters and weapons using the ACF CollisionsManager module.
globs: []
alwaysApply: false
---

# Collisions Manager — ACF Ultimate

The **CollisionsManager** module provides trace-based hit detection for melee/ranged attacks. **`UACMCollisionManagerComponent`** lives on a character (or weapon) and runs named **traces** (`FTraceInfo`) between socket pairs on a mesh while an attack montage plays. Activation is normally driven by animation via the **`UACMActivateCollisionANS`** notify state, which starts/stops named traces during the swing window. On hit, the component applies damage (point or area) through a GameplayEffect and broadcasts events. A **`UACMCollisionsMasterComponent`** (on the GameState/level) ticks and coordinates all active managers, and **`UACMEffectsDispatcherComponent`** plays material-based impact FX.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Character / weapon BP | actor with `UACMCollisionManagerComponent` | `/AscentCombatFramework/.../Blueprint/` | Owns the trace config + mesh used for collision |
| Attack montage | `UAnimMontage` + `UACMActivateCollisionANS` | `/AscentCombatFramework/Animations/` | Notify state starts/stops named traces during the swing |
| Impacts FX data | `UACMImpactsFXDataAsset` | `/AscentCombatFramework/.../FX/` | Per-physical-material hit sounds/particles |
| Damage GameplayEffect | `UGameplayEffect` (via `FGameplayEffectConfig`) | `/AscentCombatFramework/GAS/` | Applied to victims on hit |

> **Never edit sample assets.** Duplicate character/weapon Blueprints, montages and FX data assets into `Content/YourGame/...` and wire your copies. Sample assets under `/AscentCombatFramework/` are overwritten on every plugin update.

### Key classes & types

| Symbol | Role |
|---|---|
| `UACMCollisionManagerComponent` | Runs named traces on a mesh, detects hits, applies damage, plays trails |
| `UACMCollisionsMasterComponent` | Central coordinator; ticks all active collision managers (register via `AddComponent`) |
| `UACMActivateCollisionANS` | Anim Notify State; `TracesToStart` names started on `NotifyBegin`, stopped on `NotifyEnd` |
| `UACMActivateDamageAbilityTask` | GAS ability task that activates a trace from inside a `UACFGameplayAbility` |
| `UACMEffectsDispatcherComponent` | Spawns impact / action FX by physical material |
| `FTraceInfo` | A named trace: `StartSocket`/`EndSocket`, `Radius`, `DamageTypeClass`, `BaseDamage`, `GameplayEffect`, trail FX, `bCrossframeAccuracy` |
| `FBaseTraceInfo` | Base of `FTraceInfo`; also used for `SwipeTraceInfo` and `AreaDamageTraceInfo` |
| `EDamageType` | `EPoint`, `EArea` |
| `EDebugType` | `EDontShowDebugInfos`, `EShowInfoDuringSwing`, `EAlwaysShowDebug` |

---

## 2 — Setup / Configuration

1. Add a **`UACMCollisionManagerComponent`** to the actor that owns the damage mesh (the character, or a weapon actor).
2. Call **`SetupCollisionManager(MeshComponent, DefaultChannels)`** once (typically on `BeginPlay` or when a weapon is equipped) to bind the mesh whose sockets the traces use.
3. Configure under **ACM**:
   - **`CollisionChannels`** — channels to trace against (e.g. Pawn).
   - **`bAllowMultipleHitsPerSwing`** — false = each actor is hit once per swing.
   - **`bIgnoreOwner`** (default true) and **`IgnoredActors`**.
   - **`bAutoApplyDamage`** (default true) — auto-applies damage on hit, or leave false to handle damage yourself via `OnCollisionDetected`.
4. Under **ACM|Traces**, populate **`DamageTraces`** — a `TMap<FName, FTraceInfo>`. Each entry is a named trace:
   - **`StartSocket`** / **`EndSocket`** — sockets on the damage mesh (defaults `"start"` / `"end"`).
   - **`Radius`**, **`bCrossframeAccuracy`** (interpolate between frames for fast swings).
   - **`DamageTypeClass`**, **`BaseDamage`**, **`DamageType`** (`EPoint`/`EArea`).
   - **`GameplayEffect`** (`FGameplayEffectConfig`) — applied to victims on hit.
   - **`NiagaraTrail`** / `AttackSound` — visual/audio trail.
5. Optionally set **`SwipeTraceInfo`** (for projectile/swipe shots) and **`AreaDamageTraceInfo`** (for AoE).
6. Add a **`UACMCollisionsMasterComponent`** to the GameState (or a level actor) so active managers are ticked centrally.

---

## 3 — Core Workflow / Runtime API

### Animation-driven activation (recommended)

In the attack montage, add a **`UACMActivateCollisionANS`** notify state across the swing window. Set its **`TracesToStart`** to the trace names you defined in `DamageTraces`. The notify calls `StartSingleTrace` on `NotifyBegin` and `StopSingleTrace` on `NotifyEnd` automatically.

### Manual / GAS activation

```
// Start/stop named traces directly
CollisionComp->StartSingleTrace("RightHandSword");
CollisionComp->StopSingleTrace("RightHandSword");
CollisionComp->StartAllTraces();
CollisionComp->StopAllTraces();

// Timed (auto-stops after Duration)
CollisionComp->StartTimedSingleTrace("RightHandSword", 0.4f);
CollisionComp->StartAllTimedTraces(0.4f);

bool bActive = CollisionComp->IsTraceActive("RightHandSword");
```

From inside a `UACFGameplayAbility`, use **`UACMActivateDamageAbilityTask`** to drive a trace for the active duration of the ability.

### Swipe & area damage

```
// Swipe trace (e.g. a thrust or hitscan)
CollisionComp->PerformSwipeTraceShot(Start, End, Radius);          // server
CollisionComp->PerformSwipeTraceShot_Local(Start, End, R, OutHit); // local query

// Area damage
CollisionComp->StartAreaDamage(Center, Radius, Interval, DamageTypeOverride);  // damage-over-time
CollisionComp->StopCurrentAreaDamage();
CollisionComp->PerformAreaDamage_Single(Center, Radius);                       // one burst
CollisionComp->PerformAreaDamageForDuration(Center, Radius, Duration, Interval);
```

### Ignore / owner management

```
CollisionComp->AddActorToIgnore(SomeActor);
CollisionComp->SetActorOwner(OwningCharacter);  // when comp is on a weapon, set the wielder as damage dealer
CollisionComp->AddCollisionChannel(ECC_Pawn);
```

### Runtime trace config

```
CollisionComp->SetTraceConfig("RightHandSword", NewTraceInfo);
FTraceInfo Info;
CollisionComp->TryGetTraceConfig("RightHandSword", Info);
```

### Events

| Delegate | Fires when |
|---|---|
| `OnCollisionDetected(HitResult)` | A trace hits an actor (handle custom damage here if `bAutoApplyDamage` is false) |
| `OnActorDamaged(damageReceiver)` | Damage applied to an actor |
| `OnTrailActivated(TrailName)` / `OnTrailDeactivated(TrailName)` | Trace/trail started or stopped |

---

## 4 — Wire to Characters / Blueprints

1. **Weapon-mounted setup:** put the `UACMCollisionManagerComponent` on the weapon actor. On equip, call `SetupCollisionManager(WeaponMesh, Channels)` and `SetActorOwner(Character)` so damage is attributed to the wielder, not the weapon.
2. **Character-mounted setup (unarmed):** put the component on the character and `SetupCollisionManager` with the character mesh; define traces using fist/foot sockets.
3. **Montage notifies:** in each attack montage, add `UACMActivateCollisionANS` over the impact frames with `TracesToStart` matching your `DamageTraces` keys. This is how the Actions System combat abilities turn collision on/off.
4. **Master coordinator:** ensure a `UACMCollisionsMasterComponent` exists (GameState); managers register themselves so traces are ticked.
5. **Impact FX:** assign a `UACMImpactsFXDataAsset` to the `UACMEffectsDispatcherComponent` to play per-material hit FX. Damage flows through GAS, so victims must have a GAS attributes component to actually take damage.

---

## 5 — Verify

**Checklist before testing:**

- [ ] `UACMCollisionManagerComponent` present on the character or weapon.
- [ ] `SetupCollisionManager(Mesh, Channels)` called with the correct damage mesh.
- [ ] Damage mesh has the sockets named in each trace's `StartSocket`/`EndSocket`.
- [ ] `DamageTraces` populated; each has a `GameplayEffect` / `BaseDamage` and correct `DamageTypeClass`.
- [ ] `CollisionChannels` includes the victims' object channel; victims not in `IgnoredActors`.
- [ ] Attack montages have `UACMActivateCollisionANS` with `TracesToStart` matching trace names.
- [ ] When component is on a weapon, `SetActorOwner(Character)` is called.
- [ ] A `UACMCollisionsMasterComponent` exists (e.g. on GameState).
- [ ] Victims have a GAS attributes component so the GameplayEffect can apply damage.

**Common failures:**

| Symptom | Fix |
|---|---|
| No hits ever detected | `SetupCollisionManager` not called, or trace sockets don't exist on the mesh |
| Trace runs but no damage | `GameplayEffect`/`BaseDamage` not set on the `FTraceInfo`, or victim has no GAS attributes component |
| Self-damage / hits own weapon | `bIgnoreOwner` false, or `SetActorOwner` not called for a weapon-mounted component |
| Multiple hits per swing | `bAllowMultipleHitsPerSwing` is true (set false for single hit per actor) |
| Wrong actor credited with kill | `SetActorOwner` not pointing at the wielder |
| Fast swings pass through targets | Enable `bCrossframeAccuracy` on the trace; increase `Radius` |
| Collision never turns on in combat | Montage missing `UACMActivateCollisionANS`, or `TracesToStart` names don't match `DamageTraces` keys |
| Can't see what's happening | Set `ShowDebugInfo` to `EShowInfoDuringSwing` or `EAlwaysShowDebug` |
| Traces don't tick | No `UACMCollisionsMasterComponent` registered to coordinate managers |
