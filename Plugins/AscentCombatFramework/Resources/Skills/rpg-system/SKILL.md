---
name: rpg-system
description: Configure ACF RPG stats, primary attributes, derived statistics, leveling, XP and perks using the Advanced RPG System (ARS) statistics component.
globs: []
alwaysApply: false
---

# Advanced RPG System (ARS) — ACF Ultimate

The **AdvancedRPGSystem** module is ACF's stats/attributes/leveling layer, built on top of Unreal's **Gameplay Ability System (GAS)**. The central component is `UARSStatisticsComponent` (a `UACFGASAttributesComponent`) which owns a character's `FAttributesSet`: **Primary Attributes** (e.g. Strength), **Statistics** (regenerating pools like Health/Stamina/Mana — `FStatistic`) and **Attributes/Parameters** (derived values like AttackPower — `FAttribute`). Leveling and XP live in `UARSLevelingComponent`, while curves/rules that turn primary attributes and level into final stats live in DataAssets (`UARSLevelingSystemDataAsset`, `UARSGenerationRulesDataAsset`). This skill covers configuring stats, generation, leveling and runtime stat changes.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Leveling-by-curve DataAsset | `UARSLevelingSystemDataAsset` | sample RPG/Configuration folders | Primary attribute value per character level (`FAttributesByLevel` curves) |
| Generation rules DataAsset | `UARSGenerationRulesDataAsset` | sample RPG/Configuration folders | How primary attributes influence statistics & parameters (curves) |
| Statistics config DataTable | DataTable of `FStatisticsConfig` | sample RPG config | Maps GAS attributes ↔ stat `SetByCallerTag` (max/current/regen, UI name/color) |
| Attributes config DataTable | DataTable of `FAttributesConfig` | sample RPG config | Maps GAS attributes ↔ attribute `SetByCallerTag` |
| Difficulty scaling table | DataTable | `/AscentCombatFramework/Configuration/DifficultyConfig` | Difficulty-based stat scaling (reassign in Ascent GAS Settings) |
| Character DataAsset | `UACFCharacterDataAsset` | sample character configs | References the ARS config used to initialize a character |

> **Never edit sample assets.** Duplicate the leveling/generation DataAssets and config tables into your own folder (e.g. `Content/YourGame/RPG/`), reassign them on your character/GAS settings, and customize **your copies**. Editing the originals = lost on update.

### Key classes

| Class | Role |
|---|---|
| `UARSStatisticsComponent` | Per-character stats/attributes hub; modify/refill/consume stats, apply attribute-set modifiers |
| `UARSLevelingComponent` | Level + XP + perks; `AddExp`, `ForceSetLevel`, `OnCharacterLevelUp` |
| `UARSLevelingSystemDataAsset` | Curves giving each primary attribute's value at a given level |
| `UARSGenerationRulesDataAsset` | Rules/curves converting primary attributes into statistics & parameters |
| `UARSFunctionLibrary` | Blueprint helpers for ARS values/tags |

### Important enums / structs

- `EStatsLoadMethod`: `EUseDefaultsWithoutGeneration`, `EGenerateFromDefaultsPrimary`, `ELoadByLevel`.
- `EStatisticsType`: `EStatistic`, `EPrimaryAttribute`, `ESecondaryAttribute`.
- `EModifierType`: `EAdditive`, `EPercentage`.
- `FStatistic` — `StatType` tag, `MaxValue`, `CurrentValue`, `HasRegeneration`, `RegenValue`, `RegenDelay`, `bStartFromZero`.
- `FAttribute` — `AttributeType` tag + `Value`.
- `FAttributesSet` — `Attributes` (primary), `Statistics`, `Parameters`.
- `FAttributesSetModifier` — bundle of `PrimaryAttributesMod` / `StatisticsMod` / `AttributesMod` (or a custom `GameplayEffectModifier`).
- `FStatisticValue` — `Statistic` tag + `Value` (used for costs).
- Stat/attribute tags live under `RPG.Statistics`, `RPG.PrimaryAttributes`, `RPG.Attributes`.

---

## 2 — Setup / Configuration

### A. Choose how stats are generated

The component initializes its `FAttributesSet` using an `EStatsLoadMethod`:
- `EUseDefaultsWithoutGeneration` — use the authored default set as-is (good for unique bosses).
- `EGenerateFromDefaultsPrimary` — author only primary attributes; statistics/parameters are generated from the **generation rules**.
- `ELoadByLevel` — primary attributes are read from the **leveling curves** for the current `CharacterLevel`, then generation rules derive the rest. Use this for level-scaling characters.

### B. Create your generation rules DataAsset

1. **Duplicate** a sample `UARSGenerationRulesDataAsset` into `Content/YourGame/RPG/`.
2. For each `FGenerationRule` set `PrimaryAttributesTag` and fill:
   - `InfluencedStatistics` (`FStatInfluence`): `TargetStat` + `CurveMaxValue` + `CurveRegenValue`.
   - `InfluencedParameters` (`FAttributeInfluence`): `TargetParameter` + `CurveValue`.
3. Each curve's **X = primary attribute value**, **Y = resulting stat/parameter value**.

### C. Create your leveling curves DataAsset (for `ELoadByLevel`)

1. **Duplicate** a sample `UARSLevelingSystemDataAsset` into `Content/YourGame/RPG/`.
2. Add `FAttributesByLevel` entries: one per primary attribute, each with a `ValueByLevelCurve` (**X = level**, **Y = attribute value**).

### D. Configure leveling & XP (`UARSLevelingComponent`)

- `LevelingType` — `ECantLevelUp`, `EGenerateNewStatsFromCurves`, or `EAssignPerksManually`.
- `ExpForNextLevelCurve` — **X = level**, **Y = XP required** for the next level.
- `ExpToGiveOnDeathByCurrentLevel` — XP this enemy grants its killer (for leveling enemies); or `ExpToGiveOnDeath` for non-leveling enemies.
- `PerksObtainedOnLevelUp` — perk points granted per level when using `EAssignPerksManually`.

### E. Map GAS attributes to ACF tags

In the statistics/attributes config tables (duplicated), each row (`FStatisticsConfig` / `FAttributesConfig`) binds a `SetByCallerTag` to the GAS `FGameplayAttribute`(s) — max/current/regen for statistics. Reassign these tables in **Ascent GAS Settings**.

---

## 3 — Core Workflow / Runtime API

### Reading stats & attributes (`UARSStatisticsComponent`)

```
float hp     = Stats->GetCurrentValueForStatitstic(HealthTag);
float hpMax  = Stats->GetMaxValueForStatitstic(HealthTag);
float hpNorm = Stats->GetNormalizedValueForStatitstic(HealthTag);   // 0..1, great for UI bars
float str    = Stats->GetCurrentPrimaryAttributeValue(StrengthTag);
float atk    = Stats->GetCurrentAttributeValue(AttackPowerTag);
```

### Modifying / refilling / consuming stats

```
Stats->ModifyStatistic(HealthTag, -25.f);     // apply damage to a pool (server)
Stats->RefillStat(StaminaTag);                // set current = max

// Costs (e.g. an ability that costs 20 stamina):
TArray<FStatisticValue> Costs = { FStatisticValue(StaminaTag, 20.f) };
if (Stats->CheckCosts(Costs)) { Stats->ConsumeStatistics(Costs); }
```

### Buffs / debuffs via attribute-set modifiers

```
FAttributesSetModifier Mod;
Mod.AttributesMod.Add(FAttributeModifier(AttackPowerTag, EModifierType::EAdditive, 10.f));
FActiveGameplayEffectHandle Handle = Stats->AddAttributeSetModifier(Mod);  // server / authority
// later:
Stats->RemoveAttributeSetModifier(Handle);
// timed buff:
Stats->AddTimedAttributeSetModifier(Mod, 8.f);
```

### Leveling & XP (`UARSLevelingComponent`)

```
Leveling->AddExp(150);                       // server; auto level-up when threshold reached
int32 lvl   = Leveling->GetCurrentLevel();
int32 cur   = Leveling->GetCurrentExp();
int32 need  = Leveling->GetTotaleExpToNextLevel();
int32 perks = Leveling->GetAvailablePerks();
Leveling->ConsumePerks(1);
Leveling->ForceSetLevel(5);                  // jump to a level (also reinitializes stats)

// React to changes:
Leveling->OnCharacterLevelUp.AddDynamic(this, &MyClass::HandleLevelUp);
Leveling->OnCurrentExpValueChanged.AddDynamic(this, &MyClass::HandleExpChanged);
```

### Re-initialize after a manual level change

```
Stats->SetNewLevelAndReinitialize(NewLevel);  // server; regenerates the attribute set
```

### Useful delegates

| Delegate | When it fires |
|---|---|
| `UARSStatisticsComponent::OnAttributeSetModified` | Any time the attribute set changes (recompute UI) |
| `UARSStatisticsComponent::OnHealthReachesZero` | Health pool hits zero (hook death) |
| `UARSLevelingComponent::OnCharacterLevelUp` | Character gains a level |
| `UARSLevelingComponent::OnCurrentExpValueChanged` | XP changes (update XP bar) |

---

## 4 — Wire to Characters / Blueprints

1. **Add the components**: sample `AACFCharacter` already has a `UARSStatisticsComponent` (and leveling). For a fresh actor, add `UARSStatisticsComponent`; leveling is available through the GAS runtime (`UARSLevelingComponent`).
2. **Assign DataAssets**: on the character (or its `UACFCharacterDataAsset`), set the generation rules / leveling curves to **your duplicates** and pick the `EStatsLoadMethod`.
3. **Project settings**: reassign the statistics/attributes config tables and the `DifficultyConfig` table to your duplicates in **Ascent GAS Settings**.
4. **Damage hookup**: ACF's damage handler routes incoming damage into `ModifyStatistic` on the health stat; bind `OnHealthReachesZero` to trigger the death flow.
5. **UI**: drive health/stamina/mana bars from `GetNormalizedValueForStatitstic`, and refresh on `OnAttributeSetModified`. Show level/XP from the leveling component and refresh on its delegates.
6. **Persistence**: stats, level, XP and perks are marked `SaveGame`, so they round-trip through the ACF Save System automatically.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Generation rules and leveling-curve DataAssets are **duplicates** under `Content/YourGame/RPG/`.
- [ ] The chosen `EStatsLoadMethod` matches your intent (defaults vs generated vs by-level).
- [ ] If `ELoadByLevel`: every primary attribute has a `ValueByLevelCurve`.
- [ ] If generating stats: each `FGenerationRule` has curves for the statistics/parameters you expect.
- [ ] Statistics config rows map every gameplay stat tag to its max/current/regen GAS attributes.
- [ ] Leveling `LevelingType` is set, with `ExpForNextLevelCurve` (for leveling characters).
- [ ] Stat modifications (`ModifyStatistic`, `AddAttributeSetModifier`, `AddExp`) are called on the **server/authority**.
- [ ] Config tables and `DifficultyConfig` reassigned to your duplicates in Ascent GAS Settings.

**Common failures:**

| Symptom | Fix |
|---|---|
| All stats are 0 / default | Wrong `EStatsLoadMethod`, or generation rules/leveling curves not assigned |
| Health/Stamina bar empty or static | Stat not in the config table, or UI not reading `GetNormalizedValueForStatitstic` / not bound to `OnAttributeSetModified` |
| Stats don't scale with level | Using `EUseDefaultsWithoutGeneration` instead of `ELoadByLevel`, or missing `ValueByLevelCurve` |
| XP added but no level-up | `LevelingType = ECantLevelUp`, or `ExpForNextLevelCurve` missing/zero |
| Modifiers do nothing or don't replicate | `AddAttributeSetModifier`/`AddTimedAttributeSetModifier` called on client — must be authority |
| Killing enemies grants no XP | Enemy `ExpToGiveOnDeath` / `ExpToGiveOnDeathByCurrentLevel` not set |
| Perks never accumulate | `LevelingType` not `EAssignPerksManually`, or `PerksObtainedOnLevelUp = 0` |
