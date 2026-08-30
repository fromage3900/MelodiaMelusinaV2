# BS_GodFile — Rider & UE5.8 Integration Roadmap

**Date:** 2026-08-28  
**Status:** Quick wins implemented; medium/long-term queued for owner decision

---

## Quick Wins — IMPLEMENTED

### 1. CPU Profiler Traces Added

All critical subsystem paths now have `TRACE_CPUPROFILER_EVENT_SCOPE` instrumentation. View in Unreal Insights (`UnrealInsights.exe`) by opening a `.utrace` capture.

| File | Traced Functions |
|---|---|
| `MelodiaMusicClockSubsystem.cpp` | `TickClock`, `GetMusicTime`, `EnsureBattleControllerMusicClock` |
| `MelodiaWaterGameplaySubsystem.cpp` | `ApplyOperation`, `RecomputeFlow` |
| `MelodiaPCGNarrativeChallengeBridgeComponent.cpp` | `HandleNoteJudged`, `HandlePatternCompleted` |
| `MelodiaPCGWaterGameplayBridgeComponent.cpp` | `HandleNoteJudged`, `HandlePatternCompleted`, `SubmitResonance` |

**How to capture:** Launch UE with `-trace=cpu,frame,loadtime` or use Session Frontend → Profiler → Live Capture.

### 2. Qodana Configuration

**File:** `qodana.yaml` (updated from unconfigured `ide: QDNET` stub)

- IDE mode: `QDJB` (JetBrains, runs locally without container)
- Profile: `qodana.starter`
- Enabled inspections: `CppMemberFunctionMayBeConst`, `CppParameterMayBeConst`, `CppLocalVariableMayBeConst`, `CppUseNullptr`, `CppUseAuto`, `CppUseEnumClass`, `CppUseOverride`, `CppUseDefault`, `CppUseDelete`, `CppUseNoexcept`, `CppUseNodiscard`, `CppUseMaybeUnused`, `CppRedundantInclude`
- Excluded paths: All `Content/`, `Saved/`, `ThirdParty/`, `Plugins/*`, `Tools/`, `deploy/`, `Docs/`
- Quality gate: max 50 any / 10 critical

**Run locally:**
```bash
qodana scan --ide QDJB
```

### 3. Codebase Modernization Status

**Already modernized — no work needed:**
- All `UPROPERTY` UObject pointers use `TObjectPtr<T>` (verified across entire `Source/` tree)
- No raw `AActor*`, `UActorComponent*`, etc. found in UPROPERTY macros
- `TSoftObjectPtr` used correctly for soft references

---

## Medium-Term — QUEUED

### 1. Adopt FGameplayTag for Identifiers

**Current state:** Subsystems use raw `FName` for network IDs, route IDs, puzzle IDs, event channels:
```cpp
bool ApplyResonance(FName NetworkId, FName TargetWaterNodeId, FName ResonanceChannel, 
    float Strength, FName PuzzleId, FName RouteId, AActor* SourceActor);
```

**Target state:** Hierarchical `FGameplayTag`:
```cpp
bool ApplyResonance(FGameplayTag NetworkId, FGameplayTag TargetWaterNodeId, 
    FGameplayTag ResonanceChannel, float Strength, FGameplayTag PuzzleId, 
    FGameplayTag RouteId, AActor* SourceActor);
```

**Suggested tag hierarchy:**
- `Melodia.Water.Network.{Alpha,Beta,Gamma}`
- `Melodia.Water.Node.{Reservoir,Channel,Valve}`
- `Melodia.Puzzle.Resonance.{01,02,03}`
- `Melodia.Battle.Encounter.{KaleidoNaveMelodySlime,CrystalShard,...}`
- `Melodia.Quest.{FirstDream,WardrobeEquip,ChoralSheep,SeaAbove}`
- `Melodia.Reward.{DawnVeil,DreamweaveShawl,SolsticeDrum,...}`

**Benefits:**
- Compile-time validation (typos fail at build, not runtime)
- Hierarchical filtering (`MatchesTag(Melodia.Water.*)`)
- Built-in autocomplete in Rider and UE Editor
- Zero silent string typo risk

**Migration path:**
1. Define tags in `DefaultGameplayTags.ini` or via `UGameplayTagsManager::AddNativeTag()`
2. Add `FGameplayTag` typedef aliases for readability
3. Update subsystem method signatures
4. Update all call sites
5. Remove old `FName` overloads

**Files affected:** `MelodiaWaterGameplaySubsystem.h/.cpp`, `MelodiaNarrativeSubsystem.h/.cpp`, `MelodiaExternalJRPGBridgeSubsystem.h/.cpp`, `MelodiaBattleMapConfig.h`, `MelodiaExplorationActors.h/.cpp`, `MelodiaPCGWaterGameplayBridgeComponent.h/.cpp`, `MelodiaPCGNarrativeChallengeBridgeComponent.h/.cpp`

### 2. World Partition Data Layers

**Current state:** Multiple showcase levels (`L_KaleidoNave`, `L_MelusinaMorning`, `L_FallenMoon`, `ZenForestTest`) managed as separate level assets.

**Target state:** Single World Partition level with Data Layers for non-destructive variant switching:
- `DL_Lighting_ToonDay`
- `DL_Lighting_NightGlow`
- `DL_Props_Cinematic`
- `DL_PCG_Foliage`
- `DL_Encounter_Active`

**Benefits:**
- One level to maintain
- Runtime layer switching for portfolio captures
- Sequencer-friendly (toggle layers per shot)
- No actor duplication

**Migration path:**
1. Choose a base level (e.g., `L_KaleidoNave`)
2. Convert to World Partition if not already
3. Create Data Layers in World Settings
4. Assign actors to layers
5. Create `UDataLayerAsset` assets for each variant
6. Add runtime toggle via `UDataLayerManager::SetDataLayerRuntimeState()`

### 3. RiderLink Plugin Installation

**Current state:** No RiderLink plugin in project. Automation relies on standalone HTTP/JSON-RPC servers.

**Target state:** RiderLink compiled into `Plugins/Developer/RiderLink` for:
- In-editor test execution (IMPLEMENT_SIMPLE_AUTOMATION_TEST suites)
- Interactive Unreal Editor Log in Rider (color-coded, clickable stack traces)
- PIE toolbar controls (pause, step frame, inspect gameplay state)

**Installation:**
1. Clone RiderLink into `Plugins/Developer/RiderLink/` from Epic's UE source
2. Add to `BS_GodFile.uproject` plugins list
3. Rebuild
4. Enable in Rider: Settings → Plugins → Unreal Engine → RiderLink

**Note:** RiderLink is bundled with UE source on GitHub. For binary-only installs, it may need to be built from source.

---

## Long-Term — QUEUED

### 1. StateTree for Quest & Combat State Machines

**Current state:** State managed across custom subsystem maps and Blueprints.

**Target state:** UE 5.8 StateTree architecture for:
- Quest state machines (start → active → completed → rewarded)
- Battle state machines (intro → player_turn → enemy_turn → resolution → outro)
- Dialog flow (line → wait_input → branch → next)

**Benefits:**
- Deterministic, data-driven, hierarchical
- Sub-frame response times
- Visual debugging in UE Editor
- Replaces sprawling Blueprint chains

**Migration path:**
1. Define `UStateTree` assets for each quest/battle type
2. Create `FStateTreeQuestInstanceData` structs
3. Implement `FStateTreeTaskBase` tasks for each state
4. Replace custom quest/battle state maps with StateTree references
5. Add StateTree debugger integration

### 2. Native UEditorValidatorSubsystem for Asset Pre-Flight

**Current state:** Asset integrity verified via Python CLI scripts (`Tools/bp_sweep.py`).

**Target state:** C++ `UEditorValidatorSubsystem` rules that run on save:
- Substrate materials have valid inputs
- Texture compressions match guidelines
- Skeletal meshes have required sockets
- Quill scripts reference allowlisted IDs

**Benefits:**
- Real-time validation on save
- Prevents broken references from being committed
- No external script execution needed

**Migration path:**
1. Create `UMelodiaAssetValidator` : public `UEditorValidator`
2. Implement `CanValidateAsset_Implementation()` and `ValidateLoadedAsset_Implementation()`
3. Register in `MelodiaCore` plugin startup
4. Migrate Python script rules to C++ validators
5. Add custom validation rules for project-specific requirements

### 3. CommonUI Input Routing

**Current state:** Input handling split across Enhanced Input, custom `UMelodiaInputContextSubsystem`, and custom UI widgets.

**Target state:** `UCommonActivativatableWidget` with native Input Routing:
- Automatic focus management (gamepad, keyboard, mouse)
- Automatic key binding legend updates
- Back-button navigation stacks handled natively

**Migration path:**
1. Migrate battle HUD widgets to `UCommonActivatableWidget`
2. Set up `UCommonUIInputSettings` for action routing
3. Replace custom input context subsystem with CommonUI's built-in system
4. Add `UCommonBoundActionBar` for dynamic key legend display

---

## Deferred — Not in Current Scope

- Slime and Cosmic Reaver meshes (asset blockers)
- Choral Sheep skinning (owner-side)
- Quill background-panel render path (separate bug)
- `AnimMontage.h:781` death crash (post-P0)
- Itch tooling (no `butler`, no `.itch.toml`)

---

## File Manifest

```
BS_GodFile/
├── qodana.yaml                                    # Updated: Unreal C++ inspections
├── Source/BS_GodFile/MelodiaIntegration/
│   ├── MelodiaMusicClockSubsystem.cpp             # +3 trace scopes, +Stats.h include
│   ├── MelodiaWaterGameplaySubsystem.cpp          # +2 trace scopes, +Stats.h include
│   ├── MelodiaPCGNarrativeChallengeBridgeComponent.cpp  # +2 trace scopes, +Stats.h include
│   └── MelodiaPCGWaterGameplayBridgeComponent.cpp       # +3 trace scopes, +Stats.h include
└── Docs/
    ├── MELODIA_PERSONALIZATION_INSTALLATION_2026-08-28.md  # Hermes personalization guide
    └── RIDER_UE58_INTEGRATION_ROADMAP_2026-08-28.md        # This file
```

---

## Next Action

**Phase 1, step 5 from P0 Closeout Plan** remains the critical path: extend `DA_MelodiaIntegrationConfig` with the full missing-ID list, fix the two authoring defects, and compile the five `.qsc` files to `.uasset`. Nothing in Phase 2 can start until the allowlist and compiled assets exist.
