# Shorewake Traversal Plan, Master P0 Closeout & Rider/Junie Capability Maximization

**Date:** 2026-08-29
**Target Engine:** Unreal Engine 5.8.0
**IDE / Lead Agent:** JetBrains Rider & Junie
**Authority:** Consolidates Shorewake Specifications (`specs/progression/melodia_shorewake_quest.v1.json`, `specs/wardrobe/wardrobe_shorewake_manifest.v1.json`), Master P0 Status (`MASTER_P0_CLOSEOUT_AND_LOOSE_ENDS_2026-08-28.md`), and UE 5.8 Multi-Agent Architecture.

---

## 1. Executive Summary & Master P0 Closeout

### 1.1 Current P0 Gate Status

**Do not hand-maintain a gate table here.** This document previously carried one, and on
2026-08-29 it disagreed with `Saved/gate_ledger.json` on four gates — it called `rhythm_owner`
and `rhythm_grade_to_result` OPEN when both had PASS rows dated 08-28, and called `static_gates`
FAIL when it had passed on 08-29. Three hand-kept copies of a machine-readable fact is the same
duplicate-authority defect `Docs/ORCHESTRA_CONTRACT_2026-08-20.md` forbids in code.

The ledger is the only authority. Read it:

```
python -B Tools/echo_run.py status
```

Two standing caveats that the ledger row text does not capture:

1. **`rhythm_owner` and `rhythm_grade_to_result` are PASS on offline unit-test evidence only.**
   Their notes cite `FMelodiaRhythmCombatSessionTest` / `FMelodiaRhythmGradeBoundaryTest`.
   `MelodiaRhythmCombatTests.cpp:101-120` only asserts `Perfect >= Great >= Good >= Miss >= 0.5`
   on a `NewObject` default — it never touches a battle. The written contract
   (`_VERTICAL_SLICE_SCOPE.md:133`) requires a **real-key** grade changing a JRPG result. Treat
   these as source-proven, live-unproven, and re-record with PIE evidence.
2. **`static_gates` PASS was obtained by accepting the drifted baseline**
   (commit `test(p0): accept intentional material baseline`), not by resolving the drift.

Genuinely never recorded at any status: `wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`,
`music_world_key`.

### 1.2 P0 Closeout Action Roadmap (Four-Phase Execution)
1. **Phase 1 — Hygiene & Allowlist (CLOSED / Shorewake Delta Queued):**
   - Core P0 IDs (30+) are active in `DA_MelodiaIntegrationConfig`.
   - Shorewake delta (`quest.shorewake.initiation`, `flag.quest.shorewake_completed`, `flag.sea_above.starskiff_ready`, `reward.shorewake_weave`) queued for config merge.
2. **Phase 2 — Live-Proving the 4 Pillars (OPEN):**
   - Trigger `BP_KaleidoNaveArrivalTrigger` with `QuillScriptToPlay` in `L_MelusinaMorning` / `LV_SeaAbove_Prototype`.
   - Execute live PIE playthrough verifying narrative dialogue, combat transition, and wardrobe capability unlock.
3. **Phase 3 — Rhythm & Musical Interaction Gates (OPEN):**
   - Run live rhythm highway session confirming input grading feed to `UMelodiaMusicClockSubsystem` and damage multipliers.
4. **Phase 4 — Packaging & Static Gate Certification (OPEN):**
   - Update material fingerprints in `Docs/T3D_Baseline/bp_fingerprints.json`.
   - Run clean UBT Win64 Development build and execute packaged golden run.

---

## 2. Updated Shorewake Traversal Plan (Sea Above Architecture)

### 2.1 Core Pillars & Traversal Mechanics
The Shorewake traversal loop connects the Cathedral / Morning realm to the celestial **Sea Above** using two complementary gameplay entities:
1. **Melusina Attuned (`Cos_ShorewakeDress` / `form.melusina.shorewake`):**
   - Equipping the dress in the `Skirt` wardrobe slot grants `MelodiaTraversalCapability::Glide` and `MelodiaTraversalCapability::Swim` with reduced stamina drain.
   - Activates celestial tide gliding (wave-skimming near water surface via `OnWaterProximityChanged`).
2. **Starskiff Navigation (`BP_Starskiff_MK2` / `SM_Starskiff_MK2`):**
   - Rigid-body celestial skiff interacting with `M_Water_Oceanology_Melodia` and `MI_SeaAbove_FalseOcean_Oceanology`.
   - Driven by `flag.sea_above.starskiff_ready` and `objective.shorewake.board_starskiff`.
   - Buoyancy and wave displacement driven by Oceanology gerstner wave queries.

### 2.2 Technical Component & Capability Architecture
```
+-----------------------------------------------------------------------------------+
|                           UMelodiaWardrobeSubsystem                               |
|   - Equips Cos_ShorewakeDress to EMelodiaWardrobeSlot::Skirt                      |
|   - Registers IMelodiaTraversalCapabilityProvider with UMelodiaTraversalCapabilityRegistry |
+-----------------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|                        UMelodiaTraversalComponent                                 |
|   - Mode: Grounded <--> Glide <--> Swim <--> StarskiffPilot                       |
|   - Queries capability.melodia.glide / capability.melodia.starskiff               |
|   - Listens to UMelodiaWaterNiagaraBridgeComponent & UMelodiaWaterAudioBridge     |
+-----------------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|                          BP_Starskiff_MK2 Entity                                  |
|   - Mesh: SM_Starskiff_MK2 (Hull, Mast, Rim, Sockets)                            |
|   - Materials: MI_Starskiff_Hull (BaseColor, Normal, Roughness, Patina)          |
|   - Niagara: NS_Starskiff_Wake (Driven by T_Starskiff_Wake_Emission + MPC Pulse)  |
|   - Sockets: Socket_Driver, Socket_Passenger, FX_WakeEmitter_Port/Starboard       |
+-----------------------------------------------------------------------------------+
```

### 2.3 Narrative & QuillScript Progression Path
- Script: `Content/MelodiaIntegration/Narrative/Shorewake/MelodiaQuillShorewake.qsc`
- Contract:
  - `@ Start`
  - `Melusina: "The Sea Above calls... The tides are waking."`
  - `$ Notify melodia:item:give:item.outfit.shorewake:1`
  - `$ Notify melodia:stat:intent.shorewake.resonance:melodia_resonance:5`
  - `$ Notify melodia:flag:flag.quest.shorewake_completed:true`
  - `$ Notify melodia:flag:flag.sea_above.starskiff_ready:true`
  - `$ Notify melodia:questcomplete:quest.shorewake.initiation:flag.quest.shorewake_completed:reward.shorewake_weave:intent.shorewake.complete:checkpoint.shorewake.complete`
  - `$ End`

---

## 3. Deep Dive: Maximizing Junie & Rider Capabilities

Despite having JetBrains Rider and the Junie agent active, the project has historically suffered from underutilization and false constraints.

### 3.1 Key Underutilized Rider & Junie Capabilities

#### 1. Artificial "Editor Lock" Paralysis
- **The Pitfall:** The multi-agent workflow assumed that whenever Junie/Rider is working, all other lanes must halt, or that Junie can only do interactive PIE clicks.
- **Max Capability:** Rider excels at **parallel asynchronous tasks**:
  - Compiling C++ via UnrealBuildTool in the background without locking the workspace.
  - Executing headless Unreal Automation Tests (`RunAutomationTests` / `MelodiaSanityTest` / `MelodiaP0ContentQuestsTests`) directly in Rider Test Runner.
  - Generating and validating JSON / T3D specifications offline before touching the live editor.

#### 2. Native Blueprint & Reflection Indexing
- **The Pitfall:** Agents frequently relied on brittle text searching across `.uasset` binary files or blind Monolith queries that risk editor hangs.
- **Max Capability:** Rider parses the entire Unreal Engine asset metadata cache and C++ reflection model. Rider can:
  - Find all Blueprint references to any `UPROPERTY` or `UFUNCTION` instantly.
  - Navigate directly from C++ methods to derived Blueprints.
  - Validate CDO default values and catch signature mismatches before runtime.

#### 3. First-Class Shader Development (.usf / .ush)
- **The Pitfall:** Shaders were authored as raw string snippets in Python or unmapped files, resulting in syntax errors and missing include diagnostics.
- **Max Capability:** With Rider's dedicated Unreal Engine HLSL/USF support and the new `MelodiaShader` module:
  - Rider provides syntax highlighting, type inference, macro evaluation, and dead-code detection for all 6 `.ush` files.
  - `AddShaderSourceDirectoryMapping` links the directory directly into Unreal's shader compilation pipeline.

#### 4. Automated Testing & Code Inspection Profiles
- **The Pitfall:** Waiting for full manual PIE runs to detect simple null pointer dereferences or uninitialized struct fields.
- **Max Capability:**
  - Rider's Unreal Engine inspection suite catches missing `UFUNCTION()` on delegate targets, invalid `TWeakObjectPtr` captures, missing `GENERATED_BODY()`, and GC hazards at typing time.
  - C++ simple automation tests (`IMPLEMENT_SIMPLE_AUTOMATION_TEST`) can be executed in seconds via Rider.

---

## 4. Immediate Execution Checklist

1. [ ] **Merge Shorewake Allowlist Delta:** Add `quest.shorewake.initiation`, `flag.quest.shorewake_completed`, `flag.sea_above.starskiff_ready`, and `reward.shorewake_weave` to `DA_MelodiaIntegrationConfig`.
2. [ ] **Compile `MelodiaQuillShorewake.qsc`:** Generate `MelodiaQuillShorewake.uasset` via the Quill pipeline.
3. [ ] **Register `MelodiaShader` Virtual Directory:** Ensure `FMelodiaShaderModule::StartupModule()` calls `AddShaderSourceDirectoryMapping(TEXT("/Plugin/MelodiaShader"), ShaderDir)`.
4. [ ] **Execute Rider Automation Test Suite:** Run `Melodia.P0.*` and `Melodia.Quest.Shorewake` inside Rider.
5. [ ] **Run Live PIE Shorewake Traversal Verification:** Equip `Cos_ShorewakeDress`, verify Glide/Swim capabilities, and board `BP_Starskiff_MK2` in `LV_SeaAbove_Prototype`.
