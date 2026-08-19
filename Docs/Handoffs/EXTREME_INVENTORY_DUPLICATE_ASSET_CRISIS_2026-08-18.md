# EXTREME INVENTORY — Duplicate Asset Crisis 2026-08-18

**Status:** CRITICAL — Two `BP_BattleController` assets with identical generated class names. One is broken and prevents ALL battles.

---

## 1. The Battle Controller Conflict (CRITICAL)

| Asset | Path | Compile Status | Generated Class | Has Rhythm Code |
|---|---|---|---|---|
| **Tracked (WORKS)** | `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController` | `UpToDate` ✅ | `BP_BattleController_C` | ❌ No |
| **_ThirdParty (BROKEN)** | `/Game/_ThirdParty/TurnBasedJRPGTemplate/Blueprints/Battle/bp_battlecontroller` | `Error` ❌ | `BP_BattleController_C` | ✅ Yes |

**Why this breaks everything:** Both assets generate the same class name `BP_BattleController_C`. UE5 loads whichever it finds last. The `_ThirdParty` copy has:
- `RhythmHUDRef` typed as generic `Object` (should be `UserWidget`)
- `Create Widget` node with NO class specified
- Invalid cast target type
- Extra functions: `SetRhythmMultiplier`, `RegisterRhythmHit`, `GetRhythmRating`

**Result:** When the broken copy loads last, ALL battles fail. `enemyUnits` array is empty. `currentTargetUnit` is None. Null access cascades.

---

## 2. GameMode Situation (3 GameModes, 2 Purposes)

| GameMode | Parent Class | Compile Status | Purpose | Integration Map Default? |
|---|---|---|---|---|
| `BP_MelodiaGameMode` | `MelodiaGameMode` (MelodiaCore) | ✅ UpToDate | Melodia-native exploration | ❌ |
| `BP_MelodiaJRPGGameMode` | `GameModeBase` | ✅ UpToDate | **JRPG integration** | ✅ **YES** |
| `BP_JRPGGameMode` | `GameModeBase` | ✅ UpToDate | Stock template | ❌ |

**Integration map (`MelodiaIntegrationMap`) uses `BP_MelodiaJRPGGameMode`.**

---

## 3. Two Competing Content Trees

### Tracked Tree (`Content/TurnBasedJRPGTemplate/`)
- **205 .uasset files** — the authoritative, maintained copy
- Only `BP_BattleController.uasset` is tracked in git
- Has `BP_OffLevelBattle`, `BP_OffLevelBattleController`, `BP_PermanentBattle` (missing from _ThirdParty)
- Has extra enemies (`BP_WeakEnemy`, `BP_AverageEnemy`), weapons (`BP_BroadSword`, `BP_DragonSword`), quests, UI screens

### _ThirdParty Mirror (`Content/_ThirdParty/TurnBasedJRPGTemplate/`)
- **156 .uasset files** — an older, partial copy
- `bp_battlecontroller.uasset` is **BROKEN** (lowercase filename too)
- Missing ~50 assets compared to tracked
- Has rhythm code additions that the tracked copy doesn't have
- **UNTRACKED by git** — changes here are invisible to version control

### Key Missing in _ThirdParty (present in tracked):
- `BP_OffLevelBattle`, `BP_OffLevelBattleController`, `BP_PermanentBattle`
- `BP_QuestLogic`
- `BP_AverageEnemy`, `BP_WeakEnemy`
- `BP_BroadSword`, `BP_DragonSword`, `BP_GreatStaff`, `BP_Rod`
- `BP_Buckler`
- `BP_LeatherArmor`
- `BP_Chest`, `BP_Forge`, `BP_Shrine` (interactables)
- Many UI dialogues and main menu screens
- `A_Land`, `A_ThirdPersonJump_End` (animations)

---

## 4. UI Systems (Two Parallel HUDs)

### Stock JRPG UI (`BP_BattleUI` family)
- `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI` — stock battle HUD
- `/Game/_ThirdParty/.../BP_BattleUI` — _ThirdParty copy (likely older)

### Melodia Integration UI
- `/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI` — Melodia overlay
- `/Game/MelodiaIntegration/UI/BP_MelodiaRhythmPrompt` — rhythm prompt
- `/Game/MelodiaIntegration/UI/BP_MelodiaTurnOrderList` — turn order
- `/Game/MelodiaIntegration/UI/BP_MelodiaActionButton` — action buttons
- `/Game/MelodiaIntegration/UI/BP_MelodiaActionsUI` — actions panel
- `/Game/MelodiaIntegration/UI/WBP_MelodiaInteractionPrompt` — interaction prompt

**The Melodia UI is created by `UMelodiaUIBridgeSubsystem`** (GameInstanceSubsystem), not by GameMode.

---

## 5. Animation / Character Issues

| Asset | Issue | Impact |
|---|---|---|
| `BP_MelusinaJRPGCharacter` | `CharacterMesh0` pin not found | Mesh component reference broken after mesh swap |
| `ABP_Melusina_WaterHair` | `BreakTransform` backward compatibility error | UE 5.8 changed Transform break node |
| `ABP_Melusina_Current` | Modified in last commit | Unknown impact — needs verification |

---

## 6. Root Cause Summary

```
┌─────────────────────────────────────────────────────────────┐
│  _ThirdParty/bp_battlecontroller has compile errors          │
│  ↓                                                           │
│  Same generated class name as tracked BP_BattleController    │
│  ↓                                                           │
│  UE5 loads whichever it finds last (non-deterministic)       │
│  ↓                                                           │
│  When broken copy loads: battle starts, enemyUnits empty     │
│  ↓                                                           │
│  All target selection fails → "Accessed None" cascade        │
│  ↓                                                           │
│  Melusina can't battle. Rhythm HUD may not spawn.            │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Recommended Consolidation Plan

### Option A: Fix _ThirdParty Copy (Fastest, Riskiest Long-Term)
1. Fix `RhythmHUDRef` type from `Object` → `UserWidget`
2. Add widget class to `Create Widget` node
3. Fix invalid cast
4. **Problem:** Still two copies with same class name = ongoing collision risk

### Option B: Move Rhythm Code to Tracked Copy (Cleanest)
1. Copy rhythm functions from _ThirdParty to tracked `BP_BattleController`
2. Delete _ThirdParty copy (or rename)
3. Re-verify all battle flows
4. **Problem:** Requires careful merge, may lose other _ThirdParty changes

### Option C: Delete _ThirdParty Mirror (Cleanest Architecture)
1. Delete entire `Content/_ThirdParty/TurnBasedJRPGTemplate/` folder
2. Move any unique/rhythm code to tracked location or MelodiaIntegration BPs
3. Re-verify everything
4. **Problem:** _ThirdParty is untracked — deleted code is gone forever

### Additional Fixes Needed Regardless of Option:
- Fix `BP_MelusinaJRPGCharacter` `CharacterMesh0` pin
- Fix `ABP_Melusina_WaterHair` `BreakTransform` node
- Verify `BP_MelodiaJRPGGameMode` pawn/controller config
- Verify `ABP_Melusina_Current` after recent changes

---

## 8. Verified Working State (from earlier today)

The user confirmed at 15:23: **"just tested rhythm skill in battle and it worked with note highway!"**

This means the system WAS working. The break likely occurred when:
- The _ThirdParty `bp_battlecontroller` was modified (adding broken rhythm wiring)
- OR the editor reloaded and picked up the _ThirdParty copy instead of tracked
- OR a save operation wrote to the wrong copy

---

*Inventory compiled 2026-08-18. All asset paths and compile statuses verified live via Monolith.*
