# Melodia Integration Architecture Handoff — 2026-08-18

## Status: THREE competing systems need consolidation

The integration map currently has **three competing GameMode + Pawn pairs** that were built in parallel. The user directive is to **merge them into one canonical system today** so the rest of the summer is content creation only (skills, quests, enemies), not new systems.

---

## The Three Competing Systems

### 1. Melodia Native (`BP_MelodiaGameMode` + `bp_melusina`)
| | |
|---|---|
| **GameMode** | `BP_MelodiaGameMode` — parent `MelodiaGameMode` (C++), has rhythm highway, battle results widgets, `bUseRhythmHighway=true` |
| **Pawn** | `bp_melusina` — parent `MelodiaSmokeCharacter` (C++), has glide/orrery/traversal |
| **Mesh** | `SK_Melusina` (old) |
| **AnimBP** | `ABP_Melusina_Current` — parent `MelodiaLocomotionAnimInstance` |
| **Pros** | Full Melodia exploration mechanics (glide, swim, dive, dash, water hair) |
| **Cons** | Cannot participate in JRPG template battles; uses old mesh; `MelodiaLocomotionAnimInstance` crashes at `NativeUpdateAnimation()` line 37 (stale DLL — source already fixed, needs rebuild) |

### 2. JRPG Template Stock (`BP_JRPGGameMode` + `BP_MageCharacter`)
| | |
|---|---|
| **GameMode** | `BP_JRPGGameMode` — plain `GameModeBase`, empty stub |
| **Pawn** | `BP_MageCharacter` — stock JRPG template character |
| **Pros** | Battles work out of the box |
| **Cons** | Not Melusina; no Melodia mechanics whatsoever |

### 3. Integration Stub (`BP_MelodiaJRPGGameMode` + `BP_MelusinaJRPGCharacter`)
| | |
|---|---|
| **GameMode** | `BP_MelodiaJRPGGameMode` — plain `GameModeBase`, empty stub, currently set to spawn `bp_melusina` (but PIE logs show `BP_MelusinaJRPGCharacter` spawning — override source TBD) |
| **Pawn** | `BP_MelusinaJRPGCharacter` — parent `BP_JRPGCharacterBase`, **24 SCS components** including water hair, traversal, outfit, wardrobe, all VFX |
| **Mesh** | `SK_Melusina_V2_Body` (current) |
| **AnimBP** | `ABP_Melusina_Current` — same as native |
| **Pros** | JRPG battle-compatible; has updated V2 mesh; has ALL Melodia components |
| **Cons** | Anim instance crash affects it too (same `ABP_Melusina_Current`); wardrobe initialization status unknown; never tested in end-to-end battle flow |

---

## The Core Problem

**`bp_melusina` (MelodiaSmokeCharacter) and `BP_MelusinaJRPGCharacter` (JRPG base) are two different pawns.**

- `bp_melusina` gets glide/smoke/orrery from its C++ parent `MelodiaSmokeCharacter`
- `BP_MelusinaJRPGCharacter` gets JRPG battle capability from `BP_JRPGCharacterBase` and has Melodia components added as SCS components

They were never meant to coexist. The integration map's `BP_MelodiaJRPGGameMode` was supposed to unify them but is currently an empty stub.

---

## Recommended Canonical Architecture

```
BP_MelodiaJRPGGameMode (integration authority)
  ├── PlayerControllerClass: BP_MelodiaJRPGController_Config (inherits BP_JRPGPlayerController)
  ├── DefaultPawnClass: BP_MelusinaJRPGCharacter (THE canonical pawn)
  └── GameInstance: BP_MelodiaJRPGGameInstance

BP_MelusinaJRPGCharacter (canonical player pawn)
  ├── Parent: BP_JRPGCharacterBase
  ├── Mesh: SK_Melusina_V2_Body
  ├── AnimClass: ABP_Melusina_Current
  ├── Components:
  │   ├── WaterHairMesh (MelodiaHairComponent)
  │   ├── MelodiaTraversal (UMelodiaTraversalComponent)
  │   ├── Outfit (MelodiaOutfitComponent)
  │   ├── Wardrobe (MelodiaWardrobeComponent)
  │   └── VFX_* (Niagara components)
  └── Has ALL Melodia exploration mechanics + JRPG battle compatibility
```

**Why `BP_MelusinaJRPGCharacter` should be canonical:**
1. It is the **only** pawn that has both JRPG battle base AND Melodia components
2. It uses the updated `SK_Melusina_V2_Body` mesh
3. It has the water hair render pipeline the user wants preserved
4. It is already configured in `BP_MelodiaJRPGGameMode` (or should be)

---

## Immediate Fixes Required (in order)

### 1. C++ Rebuild: `MelodiaLocomotionAnimInstance`
**Status:** Source code already fixed; compiled binary is stale.

`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaLocomotionAnimInstance.cpp:37`:
```cpp
Traversal = TScriptInterface<IMelodiaTraversalStateProvider>(Component);
```

The crash (`EXCEPTION_ACCESS_VIOLATION reading 0x0`) happens because the DLL does not reflect the current source. **Close editor → build `MelodiaCore` → reopen.** Live Coding cannot patch this because the interface resolution happens at compile time.

### 2. GameMode DefaultPawnClass
**Status:** Confusion about which pawn is actually spawning.

`BP_MelodiaJRPGGameMode` CDO currently reads `DefaultPawnClass = bp_melusina.BP_Melusina_C`, but PIE logs show `BP_MelusinaJRPGCharacter_C_0` with water hair binding. There is an override somewhere (possibly the `PlayerStart` actor, level blueprint, or controller).

**Action needed:** Explicitly set `BP_MelodiaJRPGGameMode.DefaultPawnClass = BP_MelusinaJRPGCharacter_C`, remove any override actors, and verify in PIE.

### 3. Wardrobe / Outfit Initialization
**Status:** `BP_MelusinaJRPGCharacter` has `MelodiaOutfitComponent` and `MelodiaWardrobeComponent` but its EventGraph (79KB) needs audit for proper initialization call.

The "naked in combat" report suggests the outfit is not being applied on spawn. Check:
- Does `BeginPlay` call `Wardrobe->ApplyOutfit()` or equivalent?
- Does `UserConstructionScript` set the mesh properly?
- Is there a default outfit configured on the `MelodiaWardrobeComponent`?

### 4. Retarget Pipeline
**Status:** User explicitly flagged as broken. Need audit of `SK_Melusina` → `SK_Melusina_V2_Body` retarget and animation blueprint `ABP_Melusina_Current`.

### 5. `_ThirdParty/BP_BattleController` Compile Errors
**Status:** ✅ **FIXED** — `RhythmHUDRef` changed from `bool` to `UserWidget`, dead `K2Node_DynamicCast_10` removed. Blueprint compiles clean. NOT YET SAVED TO DISK (Monolith edit is in memory).

---

## What NOT To Do

| Don't | Why |
|---|---|
| Change `BP_MelodiaJRPGGameMode` parent away from `GameModeBase` to `MelodiaGameMode` | The user explicitly said "dont stray from" the rhythm combat that already works on this GameMode |
| Use `bp_melusina` as the integration pawn | It cannot JRPG battle; it uses old mesh; it crashes the anim instance |
| Delete any of the three systems without owner sign-off | The user said "owner sign-off before deleting" |
| Run `git clean -fd` or `git checkout -- .` | Per AGENTS.md — these are catastrophic for this project |

---

## Files Touched This Session

| File | Action | Saved? |
|---|---|---|
| `_ThirdParty/TurnBasedJRPGTemplate/Blueprints/Battle/bp_battlecontroller.uasset` | Fixed `RhythmHUDRef` type, removed dead cast node | ❌ In-memory only |
| `BP_MelodiaJRPGGameMode.DefaultPawnClass` | Changed to `BP_MelusinaJRPGCharacter`, then reverted back to `bp_melusina` | ✅ Saved |

---

## Next Step for This Lane

After C++ rebuild and GameMode pawn fix, run the `melodia_system_golden_run_preflight` MCP command to verify the end-to-end battle encounter still triggers with the unified pawn.

---

*Handoff written by main agent, 2026-08-18. Context: user wants ONE unified system locked in today; rhythm combat is the core, JRPG is the template base; `BP_MelusinaJRPGCharacter` is the canonical pawn candidate.*
