---
name: status-effect-system
description: Create and apply status effects (buffs, debuffs, DoT, stuns) using the ACF StatusEffectSystem module — UACFStatusEffectManagerComponent, UACFBaseStatusEffect, and its subclasses.
globs: []
alwaysApply: false
---

# Status Effect System — ACF Ultimate

The **StatusEffectSystem** module provides a lightweight, Blueprint-friendly system for buffs and debuffs: poison, burn, bleed, stun, speed boost, damage reduction, and any custom effect. `UACFStatusEffectManagerComponent` on a character owns the list of active `UACFBaseStatusEffect` instances and handles stacking / retriggering. Effects are Blueprint subclasses of three concrete types: **instant** (one-shot), **for-duration** (timed modifier), or **damage-over-time** (periodic tick). Effects are identified by a `FGameplayTag` and can display an icon in the UI via `UTexture2D`.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Sample poison effect | `UACFDamageOverTimeStatusEffect` | `/AscentCombatFramework/StatusEffects/` | DoT: periodic damage over time |
| Sample burn effect | `UACFForDurationStatusEffect` | `/AscentCombatFramework/StatusEffects/` | Timed attribute modifier (e.g. speed reduction) |
| Sample instant effect | `UACFInstantStatusEffect` | `/AscentCombatFramework/StatusEffects/` | One-shot attribute change (e.g. instant heal) |

> **Never edit sample assets.** Duplicate into `Content/YourGame/StatusEffects/` and customize your copy.

### Key classes

| Class | Role |
|---|---|
| `UACFStatusEffectManagerComponent` | Manages the list of `FStatusEffect`; add/remove/query; fires delegates |
| `UACFBaseStatusEffect` | Abstract base: `StatusEffectTag`, `GameplayCueTag`, `Icon`, `bCanBeRetriggered` |
| `UACFInstantStatusEffect` | Fires `OnTriggerStatusEffect` once immediately and ends |
| `UACFForDurationStatusEffect` | Runs for `Duration` seconds; optionally applies `FAttributesSetModifier` while active |
| `UACFDamageOverTimeStatusEffect` | Extends for-duration; applies periodic damage on a tick interval |
| `FStatusEffect` | Runtime struct: `StatusTag` + `UACFBaseStatusEffect* effectInstance` + `StatusIcon` |

---

## 2 — Setup / Configuration

### A. Add UACFStatusEffectManagerComponent to your character

1. Open your character Blueprint (subclass of `AACFCharacter`).
2. Add component → `UACFStatusEffectManagerComponent`.
3. No additional configuration is required on the component itself — it starts empty and effects are applied at runtime.

> Note: `AACFCharacter` does not include this component by default. You must add it explicitly to any character that should receive status effects.

### B. Create a status effect Blueprint

#### For-Duration effect (buff / debuff with attribute modifier)

1. Right-click → **Blueprint Class** → parent: `UACFForDurationStatusEffect`.
2. Save under `Content/YourGame/StatusEffects/`.
3. Open the Blueprint and set in **Class Defaults**:
   - **`StatusEffectTag`** — unique GameplayTag (e.g. `StatusEffect.Burn`).
   - **`GameplayCueTag`** — optional tag for a looping VFX/SFX Gameplay Cue (e.g. fire particles).
   - **`Icon`** — UI texture shown in the HUD while active.
   - **`Duration`** — seconds the effect lasts (default 5.0).
   - **`bCanBeRetriggered`** — if true, reapplying the same effect resets its timer; if false, the second application is ignored.
   - **`bAddModifierDuringEffect`** — enable to apply an attribute modifier while the effect is running.
   - **`AttributeModifier`** — `FAttributesSetModifier`: set attribute name (e.g. `MoveSpeed`) and modifier value (additive or multiplicative).
4. Override `OnStatusEffectStarts` (BlueprintNativeEvent) for custom logic when the effect begins.
5. Override `OnStatusEffectEnds` for cleanup (remove particles, restore UI state, etc.).
6. Override `OnStatusRetriggered` to handle what happens when the effect is applied again while already active (e.g. refresh stacks, reset timer).

#### Damage-Over-Time effect (poison, bleed)

1. Parent: `UACFDamageOverTimeStatusEffect`.
2. Same setup as above, plus:
   - **`DamagePerTick`** — damage applied each tick.
   - **`TickInterval`** — seconds between ticks.
   - **`DamageType`** — subclass of `UDamageType`.
3. Each tick calls `TakeDamage` on the affected character automatically.

#### Instant effect (one-shot)

1. Parent: `UACFInstantStatusEffect`.
2. Same tag/icon setup.
3. Override `OnTriggerStatusEffect` — this fires once and the effect immediately ends.
4. Use this for things like: a single heal burst, an instant stat reset, a knockback impulse.

---

## 3 — Core Workflow / Usage

### Applying a status effect at runtime

```
// Get the component on the target character:
UACFStatusEffectManagerComponent* StatusComp = Target->FindComponentByClass<UACFStatusEffectManagerComponent>();

// Apply by class (server-side — creates, applies, and manages the instance):
StatusComp->CreateAndApplyStatusEffect(UMyPoisonEffect::StaticClass(), InstigatorActor);

// Apply a pre-created instance:
UMyBurnEffect* BurnInstance = NewObject<UMyBurnEffect>(StatusComp);
StatusComp->AddStatusEffect(BurnInstance, InstigatorActor);
```

### Removing a status effect

```
// Remove by tag (Server RPC):
StatusComp->RemoveStatusEffect(FGameplayTag::RequestGameplayTag("StatusEffect.Burn"));
```

### Querying active effects

```
// Check if a specific effect is active:
bool bIsPoisoned = StatusComp->IsAffectedByStatusEffect(FGameplayTag::RequestGameplayTag("StatusEffect.Poison"));

// Get all active effects (for UI):
TArray<FStatusEffect> ActiveEffects = StatusComp->GetActiveEffects();
for (const FStatusEffect& Effect : ActiveEffects)
{
    FGameplayTag Tag = Effect.StatusTag;
    UTexture2D* Icon = Effect.StatusIcon;
    UACFBaseStatusEffect* Instance = Effect.effectInstance;
}
```

### Key delegates on UACFStatusEffectManagerComponent

| Delegate | Signature | When it fires |
|---|---|---|
| `OnStatusStarted` | `(FGameplayTag)` | An effect is applied |
| `OnStatusRemoved` | `(FGameplayTag)` | An effect is removed (expired or forced) |
| `OnStatusRetriggered` | `(FGameplayTag)` | An already-active effect is reapplied |
| `OnAnyStatusChanged` | `()` | Any add / remove / retrigger |

### Key delegates on UACFBaseStatusEffect

| Delegate | When it fires |
|---|---|
| `OnStatusEffectStarted` | Effect starts on the character |
| `OnStatusEffectEnded` | Effect ends |

---

## 4 — Wire to Characters / Blueprints

### Applying effects from weapons / abilities

The most common pattern is applying a status effect when a weapon hit occurs or an ability fires. In the ability Blueprint:

```
// In OnNotablePointReached (UACFGameplayAbility override):
UACFStatusEffectManagerComponent* StatusComp = HitActor->FindComponentByClass<UACFStatusEffectManagerComponent>();
if (StatusComp)
{
    StatusComp->CreateAndApplyStatusEffect(UMyPoisonEffect::StaticClass(), GetCharacterOwner());
}
```

Or trigger from a Gameplay Effect's execution — create a custom `UGameplayEffectExecutionCalculation` that calls `CreateAndApplyStatusEffect` on the target.

### Applying effects from environmental hazards

1. Add `UACFStatusEffectManagerComponent` to any `AACFCharacter` that can receive effects.
2. In the hazard actor (e.g. lava floor, poison cloud), on `OnActorBeginOverlap` or on damage:
   ```
   OverlappedActor->FindComponentByClass<UACFStatusEffectManagerComponent>()
       ->CreateAndApplyStatusEffect(ULavaStatusEffect::StaticClass(), this);
   ```

### Displaying effects in HUD

1. Bind the `OnAnyStatusChanged` delegate on the `UACFStatusEffectManagerComponent` to a UI update function.
2. In the update function, call `GetActiveEffects()` and refresh the list of status icons.
3. Use `FStatusEffect.StatusIcon` for the icon texture and `FStatusEffect.StatusTag` for the label.

### VFX / SFX via Gameplay Cue

Set `GameplayCueTag` on the effect to a tag registered in the Gameplay Cue Manager. When the effect starts, the system fires the Gameplay Cue (looping). When the effect ends, it removes the cue. This integrates with the ACF `UACMEffectsDispatcherComponent` on the GameState for replicated FX.

### Stacking behavior

| `bCanBeRetriggered` | Behavior on reapply |
|---|---|
| `false` (default) | Second application calls `OnStatusRetriggered` (override for custom logic) but does NOT reset timer or add a second instance |
| `true` | Duration is refreshed; `OnStatusRetriggered` fires |

To implement true stacking (multiple independent instances), call `CreateAndApplyStatusEffect` multiple times with different `StatusEffectTag` variants (e.g. `StatusEffect.Poison.Stack1`, `StatusEffect.Poison.Stack2`), or manage stack counts manually inside `OnStatusRetriggered`.

---

## 5 — Verify

**Checklist before testing:**

- [ ] `UACFStatusEffectManagerComponent` is added to every character that can receive effects.
- [ ] Effect Blueprints are duplicated from sample and saved under `Content/YourGame/StatusEffects/`.
- [ ] Each effect Blueprint has a unique `StatusEffectTag` (under `StatusEffect.*`).
- [ ] `Icon` is assigned on the effect for HUD display.
- [ ] `CreateAndApplyStatusEffect` is called on the server (or via a server-authoritative path).
- [ ] `GameplayCueTag` is set if looping VFX/SFX is desired.
- [ ] `Duration` is set to a non-zero value for timed effects.
- [ ] `AttributeModifier` attribute name matches an attribute registered in the character's attribute set.

**Common failures:**

| Symptom | Fix |
|---|---|
| Effect applied but no visual change | `GameplayCueTag` is null or the Gameplay Cue is not registered in the Cue Manager |
| Effect never ends | `Duration` is 0 or negative on `UACFForDurationStatusEffect`; timer never starts |
| Attribute not modified during effect | `bAddModifierDuringEffect = false` or `AttributeModifier.AttributeName` typo — must match the ARS attribute set attribute name exactly |
| Reapplying effect has no response | `bCanBeRetriggered = false` and `OnStatusRetriggered` is not overridden to handle it |
| Effect not visible on client | `CreateAndApplyStatusEffect` called on client only — always call with server authority; the component replicates `StatusEffects` to clients |
| DoT deals no damage | `DamageType` is null on `UACFDamageOverTimeStatusEffect`, or `TickInterval` is 0 (divide-by-zero guard) |
| Status icon missing in HUD | `Icon` is null in the effect Blueprint; `GetActiveEffects()` returns effects with null `StatusIcon` |
