# Architecture Correction: UI Bridge Subsystem Authority

**Date:** 2026-08-18  
**Session:** Live integration lane, editor verified  
**Replaces:** Any prior assumption that GameMode owns HUD spawning

## The Mistake

Earlier in this session, I incorrectly believed `BP_MelodiaJRPGGameMode` needed HUD widget properties (like `HUDWidgetClass`) to spawn the rhythm battle UI. This led to confusion about how `BP_MelodiaGameMode` (Melodia-native) vs `BP_MelodiaJRPGGameMode` (integration) should relate.

**This was wrong.** The GameMode does NOT spawn the Melodia battle UI.

## The Correct Architecture

### UI Authority: `UMelodiaUIBridgeSubsystem`

The battle UI is auto-created by **`UMelodiaUIBridgeSubsystem`** (a `UGameInstanceSubsystem`), not by any GameMode.

**Key facts:**
- **File:** `Source/BS_GodFile/MelodiaIntegration/MelodiaUIBridgeSubsystem.h/.cpp`
- **Trigger:** Listens to `OnBattleRequested` / `OnJRPGBattleStarted` events
- **Auto-creates:** Calls `CreateBattleUIInternal()` which loads `MelodiaBattleWidgetPath`
- **Default path:** `/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI.BP_MelodiaBattleUI_C` (set in `Initialize()` if path is null)
- **Z-order:** Adds to viewport at Z=100 (above stock JRPG UI)
- **Lifecycle:** Automatically removes on `OnBattleCompleted` / `OnBattleAborted`

### GameMode Responsibilities (DO NOT MIX)

| GameMode | Role | Pawn | Controller | HUD |
|---|---|---|---|---|
| `BP_MelodiaGameMode` | Melodia-native exploration | `bp_melusina` | Default `PlayerController` | **None** (subsystem handles it) |
| `BP_MelodiaJRPGGameMode` | JRPG integration battle | Stock JRPG | `BP_JRPGPlayerController` | **None** (subsystem handles it) |

### Key C++ Subsystems

```
UMelodiaUIBridgeSubsystem          -> Creates/destroys Melodia battle UI overlay
UMelodiaJRPGBattleOverlaySubsystem -> Presentation-only rhythm prompt overlay
UMelodiaExternalJRPGBridgeSubsystem -> Routes encounters to stock battle actor
UMelodiaJRPGPartyBootstrapSubsystem -> Seeds Melusina via AddPlayerUnit
UMelodiaNarrativeSubsystem         -> Bridge between QuillScript and JRPG
UMelodiaRhythmCombatSubsystem      -> Rhythm input, highway, skill registration
```

## What This Means for Agents

1. **Do NOT add `HUDWidgetClass` to either GameMode.** The subsystem handles UI creation.
2. **Do NOT reparent `BP_MelodiaJRPGGameMode` to `MelodiaGameMode`.** `MelodiaGameMode` is `NotBlueprintable`.
3. **If the battle UI doesn't appear:** Check `UMelodiaUIBridgeSubsystem` is initialized and `MelodiaBattleWidgetPath` resolves.
4. **If `BP_MelodiaBattleUI` needs changes:** Modify the widget asset, not the GameMode.
5. **Console command for debugging:** `melodia.BattleUI.LinkController` - forces the stock `battleController` reference write.

## Verified State (2026-08-18)

- `BP_MelodiaGameMode`: `DefaultPawnClass = bp_melusina`, `PlayerControllerClass = default`
- `BP_MelodiaGameMode`: `HUDWidgetClass` and `BattleResultsWidgetClass` were set to `WBP_Battle_Rhythm` / `WBP_Battle_Results` but this is **presentation config**, not spawn logic
- Rhythm skill tested in battle with note highway: **WORKS**
- All 4 Echo completion gates: **PASS** (runtime, save_load, package_launch, repeat_consume)

## Related Files

- `Source/BS_GodFile/MelodiaIntegration/MelodiaUIBridgeSubsystem.cpp` (lines 15-76 for default path, 318-345 for creation logic)
- `Source/BS_GodFile/MelodiaIntegration/MelodiaExternalJRPGBridgeSubsystem.h` (battle start/end delegates)
- `Docs/AGENT_MCP_CHEAT_SHEET.md` (Monolith command reference)
