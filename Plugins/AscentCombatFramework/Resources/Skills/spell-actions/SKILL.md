---
name: spell-actions
description: Build magic and spell abilities (projectile spells, summons, heals, buffs) on top of the GAS-based ACF Actions System using the SpellActions module.
globs: []
alwaysApply: false
---

# Spell Actions — ACF Ultimate

The **SpellActions** module ships ready-made `UACFActionAbility` / `UACFComboAction` subclasses that turn the generic Actions System into spellcasting. Every spell is just an ability granted through a `UACFAbilitySet` and triggered by a `FGameplayTag`, so casting respects the same priority, buffering, montage and cost pipeline as melee actions. Cost/mana is paid via `ActionConfig.ActionCost` (an array of `FStatisticValue`), and the spell payload (projectile, summon, heal, buff) fires from `OnNotablePointReached` — an `AnimNotify` placed on the cast montage.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Projectile spell | `UACFSpellProjectileAction` | `/AscentCombatFramework/Actions/Spells/` | Spawns a `UACFProjectile` from a socket on a notable point (combo-aware) |
| Summon spell | `UACFSummonAction` | `/AscentCombatFramework/Actions/Spells/` | Spawns up to `MaxCompanionNumb` `AACFCharacter` companions around the caster |
| Cure / heal spell | `UACFCureAction` | `/AscentCombatFramework/Actions/Spells/` | Applies a `FStatisticValue` to a statistic (e.g. +Health, +Mana) |
| Buff spell | `UACFBuffAction` | `/AscentCombatFramework/Actions/Spells/` | Applies a `FTimedAttributeSetModifier` (timed stat buff) |
| Spell ability set | `UACFAbilitySet` | `/AscentCombatFramework/Actions/AbilitySets/` | Groups the spells granted to a caster |

> **Never edit sample assets.** Duplicate the sample spells/ability sets into `Content/YourGame/Spells/` and customize **your copy**.

### Key classes

| Class | Parent | Role |
|---|---|---|
| `UACFSpellProjectileAction` | `UACFComboAction` | `ProjectileClass`, `ShootDirection` (`EShootDirection`), `LaunchSocketNames[]`, `GetDesiredSocketName()` |
| `UACFSummonAction` | `UACFActionAbility` | `CompanionToSummonClass`, `MaxCompanionNumb`, `SpawnRadius`, `bAutoKillAfterSeconds`, `AutoKillTime` |
| `UACFCureAction` | `UACFActionAbility` | `StatModifier` (`FStatisticValue`) applied on notable point |
| `UACFBuffAction` | `UACFActionAbility` | `BuffToApply` (`FTimedAttributeSetModifier`) |

All four override `OnNotablePointReached_Implementation()` — that is where the spell effect is applied. `UACFSummonAction` also overrides `CanExecuteAction_Implementation()` to block casting when the companion cap is reached.

---

## 2 — Setup / Configuration

### A. Create a spell ability Blueprint

1. In the Content Browser, right-click → **Blueprint Class**.
2. Pick the matching parent for the spell type:
   - **Projectile spell** → `UACFSpellProjectileAction`
   - **Summon** → `UACFSummonAction`
   - **Heal** → `UACFCureAction`
   - **Buff** → `UACFBuffAction`
3. Save under `Content/YourGame/Spells/`.
4. Open the Blueprint → **Class Defaults** and fill the shared ability fields:
   - **`animMontage`** — the cast animation. Add an **AnimNotify** at the moment the spell should fire (this drives `OnNotablePointReached`).
   - **`TriggeringTag`** — the `FGameplayTag` used to cast (e.g. `Actions.Spell.Fireball`).
   - **`ActionConfig.ActionCost`** — array of `FStatisticValue` (e.g. Mana cost). This is your mana gate.
   - **`ActionConfig.Cooldown`** — cooldown GameplayEffect (optional).

### B. Fill the spell-specific fields

- **Projectile (`UACFSpellProjectileAction`):**
  - `ProjectileClass` → your `UACFProjectile` subclass.
  - `ShootDirection` → `EShootDirection` value (camera/forward/etc.).
  - `LaunchSocketNames` → array of socket names; the index used is the current combo counter, so a 3-hit cast can fire from 3 different sockets.
- **Summon (`UACFSummonAction`):**
  - `CompanionToSummonClass` → `AACFCharacter` BP to spawn.
  - `MaxCompanionNumb`, `SpawnRadius`, `bAutoKillAfterSeconds`, `AutoKillTime`.
- **Cure (`UACFCureAction`):** `StatModifier` → statistic tag + value (e.g. `RPG.Statistic.Health`, +50).
- **Buff (`UACFBuffAction`):** `BuffToApply` → `FTimedAttributeSetModifier` (attribute modifiers + duration).

### C. Add spells to an AbilitySet

1. Duplicate the sample `UACFAbilitySet` into `Content/YourGame/Spells/`.
2. Add one entry per spell: set `AbilityTag` = the spell's `TriggeringTag`, `AbilityClass` = your spell BP, and `bGrantOnStart` as needed.
3. Assign this set as the caster's `DefaultAbilitySet` on the `UACFCharacterDataAsset`, or as a moveset set (e.g. `Moveset.Staff`).

---

## 3 — Core Workflow / Runtime API

### Casting a spell

Spells trigger exactly like any other action through the `UACFAbilitySystemComponent`:

```
// Cast (respects priority + mana cost in ActionConfig.ActionCost):
ActionsComp->TriggerAction(FGameplayTag::RequestGameplayTag("Actions.Spell.Fireball"), EActionPriority::ELow, true);
```

If `ActionConfig.ActionCost` cannot be paid, the ability fails to activate — no extra mana plumbing required.

### Where the effect happens

| Spell | What `OnNotablePointReached` does |
|---|---|
| `UACFSpellProjectileAction` | Spawns `ProjectileClass` from `GetDesiredSocketName()` in `ShootDirection` |
| `UACFSummonAction` | Spawns companions (cap = `MaxCompanionNumb`); optionally auto-kills after `AutoKillTime` |
| `UACFCureAction` | Applies `StatModifier` to the caster's statistic |
| `UACFBuffAction` | Applies `BuffToApply` timed modifier to the caster |

To change *when* the spell fires, move the AnimNotify on the cast montage — do not hardcode timings.

### Summon companion lifecycle

`UACFSummonAction` tracks spawned `Companions`, blocks new casts via `CanExecuteAction_Implementation` once `MaxCompanionNumb` is reached, and frees a slot on companion death. Use `bAutoKillAfterSeconds` + `AutoKillTime` for temporary summons.

---

## 4 — Wire to Characters / Blueprints

1. On your caster's `UACFCharacterDataAsset`, set `DefaultAbilitySet` (or a moveset entry) to your duplicated spell `UACFAbilitySet`.
2. Make sure the caster has a **Mana** (or equivalent) statistic in its `ARS` attribute set so `ActionConfig.ActionCost` has something to deduct.
3. **Player input:** in `SetupPlayerInputComponentBP`, bind a cast input and call `GetActionsComponent()->TriggerAction(SpellTag, EActionPriority::ELow, true)`.
4. **AI casters:** trigger the same tag from a behavior-tree task — `Character->TriggerAction(SpellTag, EActionPriority::ELow, false)`. No input binding needed.
5. For projectile spells, ensure the caster mesh actually has the sockets named in `LaunchSocketNames`.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Spell Blueprints duplicated from sample into `Content/YourGame/Spells/`.
- [ ] Each spell has `animMontage` with an **AnimNotify** at the cast moment.
- [ ] Each spell has a unique `TriggeringTag` and matching `AbilityTag` in the set.
- [ ] `ActionConfig.ActionCost` references a real statistic (mana) on the caster.
- [ ] Spell-specific fields filled (`ProjectileClass`, `CompanionToSummonClass`, `StatModifier`, or `BuffToApply`).
- [ ] Caster mesh has the sockets listed in `LaunchSocketNames` (projectile spells).
- [ ] Spell `UACFAbilitySet` assigned on the caster's `UACFCharacterDataAsset`.

**Common failures:**

| Symptom | Fix |
|---|---|
| Cast plays but nothing spawns/heals | Missing AnimNotify on the montage — `OnNotablePointReached` never fires |
| Projectile spawns at wrong place | `LaunchSocketNames` socket doesn't exist on the mesh, or wrong combo index |
| Spell never activates | Caster can't pay `ActionConfig.ActionCost` (not enough mana), or `TriggeringTag` mismatch |
| Summon does nothing after first cast | `MaxCompanionNumb` reached — `CanExecuteAction` blocks until a companion dies / is auto-killed |
| Buff/heal applies to wrong target | `StatModifier` / `BuffToApply` always targets the caster; use a projectile/effect for targeted spells |
| Companions never despawn | `bAutoKillAfterSeconds` is false — enable it and set `AutoKillTime` |
