# Melusina/Melodia Unreal Editor Automation Scripts

## Overview
These Python scripts automate the creation and inspection of assets for the Melusina character and Melodia rhythm system in Unreal Engine 5.8.

## Scripts Created

### 1. `create_tp_melusina_mpc.py`
**Creates:** `MPC_TP_Melusina` Material Parameter Collection
- **DiffuseRamp** (Vector parameter): Default = #352D40 (dark purple)
  - Keys needed: 0.0=#352D40, 0.3=white, 1.0=warm (create Gradient Texture for full ramp)
- **SpecularRamp** (Scalar parameter): Default = 0.9

**Run:**
```cmd
UE_Editor.exe BS_GodFile.uproject -ExecutePythonScript=Content/Python/create_tp_melusina_mpc.py
```

---

### 2. `create_water_mist_niagara.py`
**Creates:** `NS_Uni_WaterMist` Niagara System with `ProximitySpawnRateModule` ModuleScript

**ModuleScript Logic:**
- Input: `PlayerProximity` (float, 0.0=far, 1.0=near)
- Output: `ProximitySpawnRateMultiplier` = `lerp(0.1, 1.0, PlayerProximity)`

**Manual Setup Required in Niagara Editor:**
1. Open `NS_Uni_WaterMist`
2. Select Emitter → EmitterUpdate stage
3. Add Module Script → `ProximitySpawnRateModule`
4. Add SpawnRate module
5. Wire: `ProximitySpawnRateMultiplier` → `SpawnRate.SpawnRateMultiplier`
6. Expose `PlayerProximity` as user parameter for external control

**Run:**
```cmd
UE_Editor.exe BS_GodFile.uproject -ExecutePythonScript=Content/Python/create_water_mist_niagara.py
```

---

### 3. `create_water_bioluminescence_mf.py`
**Creates:** `MF_WaterBioluminescence_v7` Material Function

**Inputs:**
- `CharacterWorldPosition` (Vector3)
- `ProximityRadius` (Scalar, default 500)
- `ProximityFalloff` (Scalar, default 2.0)
- `BaseSparkleDensity` (Scalar)
- `BaseDeepGlowColor` (Vector3)
- `BaseDeepGlowAlpha` (Scalar)
- `BaseFoamIntensity` (Scalar)

**Outputs:**
- `ProximityFactor` (Scalar) = 1 - saturate((distance/Radius)^Falloff)
- `SparkleDensity` = BaseSparkleDensity × ProximityFactor
- `DeepGlowColorRGB` (Vector3, unmodulated)
- `DeepGlowAlpha` = BaseDeepGlowAlpha × ProximityFactor
- `FoamIntensity` = BaseFoamIntensity × ProximityFactor

**Run:**
```cmd
UE_Editor.exe BS_GodFile.uproject -ExecutePythonScript=Content/Python/create_water_bioluminescence_mf.py
```

---

### 4. `inspect_sk_melusina_slots.py`
**Inspects:** SK_Melusina Skeletal Mesh material slots
- Lists all material slots with names and materials
- Highlights slots 24, 26, 28 (target slots)
- Searches for `_SkeletonFixSpike` materials
- Lists clean MI_Melusina_* instances for reassignment

**Run:**
```cmd
UE_Editor.exe BS_GodFile.uproject -ExecutePythonScript=Content/Python/inspect_sk_melusina_slots.py
```

**Manual Fix in Skeletal Mesh Editor:**
1. Open SK_Melusina
2. Go to Materials tab
3. Reassign slots 24, 26, 28 from `_SkeletonFixSpike` to clean MI instances

---

### 5. `review_blueprint_wiring.py`
**Reviews:** Core game mechanics blueprint wiring
- Game Instance / Config / Battle Bridge / GameMode / PlayerController
- Melusina Character Blueprint
- Melodia Skill Blueprints (TrueStrike, PetalCadence, FocusAttack, DoubleHit)
- Animation Blueprints
- MelodiaCore C++ classes via reflection
- T3D system check

**Run:**
```cmd
UE_Editor.exe BS_GodFile.uproject -ExecutePythonScript=Content/Python/review_blueprint_wiring.py
```

---

## Master Runner
**`run_melusina_scripts.bat`** - Interactive menu to run any script

```cmd
cd C:\EnvironmentPortfolio\BS_GodFile
run_melusina_scripts.bat
```

---

## Key Architecture Notes (from project docs)

### Decision 016: Expressive-Only Design Doctrine
- **TurnBasedJRPGTemplate** owns combat authority (rollback history: Decisions 009/011/012/016)
- **MelodiaCore** = presentation only ("expressive, never evaluative")
- Rhythm functions = presentation + one validated `FMelodiaRhythmEffectRequest` → stock resolver
- **DO NOT** make MelodiaCore authoritative

### Critical Validation Rules
1. **DO NOT delete** hardcoded 30-row song-skill fallback until real `DA_*` chart asset exists
2. `SetSongDataAsset` has zero production call sites - deleting fallback would break battle input at BeginPlay
3. MIDI parser (`MelodiaMidiParser`) outputs `FMelodiaSongChart` with `BasicChartNotes` array
4. Latency fix boundary: `GradeInputFromTimingErrorMs(-90)` == `GradeInputFromTimingErrorMs(90)` (symmetric grading)

### Build Info
- UE 5.8 root: `C:\Program Files\Epic Games\UE_5.8`
- Build: `Build.bat BS_GodFileEditor ...`
- UBA link fails while UnrealEditor-Cmd/editor holds MelodiaCore.dll

---

## Next Steps After Running Scripts

1. **Verify MPC_TP_Melusina** - Create Gradient Texture for full DiffuseRamp (0.0, 0.3, 1.0 keys)
2. **Wire Niagara System** - Complete ModuleScript wiring in Niagara Editor
3. **Apply Material Function** - Use MF_WaterBioluminescence_v7 in water materials
4. **Fix SK_Melusina Slots** - Reassign 24/26/28 in Skeletal Mesh Editor
5. **Verify Blueprint Wiring** - Check output of review script for missing connections
6. **Wire MIDI at Runtime** - Add call in GameInstance/MelodiaBattleAdapter to load chart
7. **Run In-Editor Automation** - Melodia.CoreRules.* group (headless hangs)
