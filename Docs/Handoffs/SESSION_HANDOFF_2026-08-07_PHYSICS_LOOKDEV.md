# Session Handoff — Lookdev + Kawaii Physics (2026-08-07 15:14)

Paused for PC restart. Everything below is verified state; re-run gates after boot.

---

## 1. CRASH FIX (completed, critical to know)

**Do NOT call `blueprint_query:compile_blueprint` — it fatally crashes the editor.**
- Root cause: Monolith's `FMonolithBlueprintCompileActions::HandleCompileBlueprint()` does
  `Cast<UAnimBlueprint>` on ANY blueprint → fatal error on a normal Actor BP:
  `Cast of Blueprint ... to AnimBlueprint failed` (Casts.cpp:10), with
  `UnrealEditor_PropertyAccessNode` / `KismetCompiler` in the stack.
- The corrupt asset `BP_PhysicsPlacementSpawner` was **deleted from disk** so the project loads.
- **Safe compile path:** `blueprint_query:build_blueprint_from_spec` with `auto_compile: true`
  (this compiles through a different code path and returns `compile_success: true`).
  To recompile an existing BP safely: call `build_blueprint_from_spec` with
  `nodes:[], connections:[], pin_defaults:[], auto_compile:true` — it recompiles without edits.

## 2. Placement Spawner BP (completed, built via T3D pipeline)

- `/Game/EnvSandbox/Blueprints/BP_PhysicsPlacementSpawner` (Actor)
- Component: `PlacementMesh` (StaticMeshComponent, root, `StaticMesh=/Game/pillow1`, Mobility=Movable)
- EventGraph: `BeginPlay → SetSimulatePhysics(self=PlacementMesh, bSimulate=true)`
- Compiled **UpToDate, 0 errors, 0 warnings**, saved.
- Builder script: `Tools/build_physics_placement_spawner.py` (uses `build_blueprint_from_spec`
  with node types `CallFunction` / `VariableGet`; connections reference existing node ids,
  e.g. `K2Node_Event_0.then`).
- NOTE: re-running the script re-adds a duplicate component (`PlacementMesh1`) — remove it
  (`remove_component`) before compile if re-run.
- Test meshes (all have convex simple collision): `/Game/pillow1`, `/Game/pillow2`,
  `/Game/EnvSandbox/Meshes/SM_SM_melusinas_Mattress`, `SM_SM_Melusinas_BedFrame`.
  Drop test: L_MelusinaMorning bed.

## 3. Task B — MeluColorGrade (completed)

- Canonical grade = `/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade`
  (NOT the Melodia copy). It is **already fully parameterized** — no const-blocked steps.
  Scalars: `NikkiHeroGradeStrength, DreamSaturation, DreamContrast, DreamShadowLift,
  DreamHighlightSoft, DreamSplitToneStrength, DreamSpectralStrength, DreamSpectralCycles,
  VignetteBaseIntensity, VignetteFalloff, VignetteBlurStrength, VignetteBlurRadiusPx,
  VignetteFeather, VignettePigmentBlend, BeatPaletteResponse, EmissiveResponse`.
- Compiles clean (0 errors, 197 PS instr). Recompiled + verified 2026-08-07.
- Doctrine PP numbers (bloom .65 / vignette .22 / grain .06 / CA .35) are **native PPV volume
  settings, not grade scalars** — volume currently runs neutral; intentionally NOT overridden.

## 4. Task C — beat-pulse on storybook outline (completed)

- Target master (user-corrected): `/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate`
- Beat wiring (Group "Melodia Beat"): `MPC_Melodia_Palette.RhythmPulse` (CollectionParameter_0)
  × `BeatPulseStrength` (2.0) → Clamp → × `bEnableBeatPulse` (default 0) → feeds BOTH
  edge emphasis (`Add_0 → Multiply_2 → CustomBlend`) AND warm tint (`Multiply_3 × BeatPulseColor`
  warm R1.0 G0.45 B0.18 → `Add_1 → CustomSceneColor`).
- **2-MPC limit fix:** freed the UltraDynamicSky slot by removing the `Day_to_Night_Color`
  function call (MFC_0). Its `UDSTint` custom input was reconnected to a **local lerp**:
  `lerp(OutlineColorNight → OutlineColor, DayNightFactor)` (new scalar, default 1.0) — preserves
  the day/night tint WITHOUT the UDS MPC. Compiles clean (0 errors, 369 PS instr).
- **Live instances reparented** (both to the Premium master; Premium is a strict param superset
  of the old FoliageSafe parent, so no overrides lost):
  - `Candidates/Profiles/MI_StorybookOutline_GameplayStandard` → Premium, **bEnableBeatPulse=1**
    (set via `set_material_instance_scalar_parameter_value`, saved)
  - `EnvSandbox/Materials/PostProcess/MI_PP_StorybookOutline` → Premium, **bEnableBeatPulse=0**
    (byte-identical baseline)
- Live chain preference (setup_nikki_render_post_process.py BLENDABLES): GameplayStandard →
  MI_PP_StorybookOutline → FoliageSafe.
- Note: edited the ROOT master `/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookOutline`
  earlier too (added bEnableAudioPulse gate etc.) — harmless default-0, but Premium is the
  canonical live one now.

## 5. MF_AudioReactiveBlend (study result)

- `/Game/EnvSandbox/Materials/Functions/MF_AudioReactiveBlend` exists: 41-output palette blender
  (AudioReactivity × BassWeight/MidWeight/TrebleWeight per output). Currently **unreferenced**.
- Audio bus = `MPC_Melodia_Palette` (`/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette`),
  NOT the retired `MPC_Portfolio_Audio`. Both C++ writers (`MelodiaAudioReactivePresentationSubsystem`
  writes 7/frame: GlobalReactivity/Bass/Mid/Treble/BeatPhase/BeatPulse/RhythmPulse;
  `MelodiaRhythmReactivitySubsystem::Publish()` writes 14 event scalars) hit real params — Bug B is gone.

## 6. NEXT WORK (in-progress, resume after restart)

### A. MF wind — build `MF_ClothWindDrape` material function
- Convention: `Content\EnvSandbox\Materials\Functions\MF_<CamelCase>`, registered in
  `Content\Python\setup_material_functions.py` MF_SPECS, callable via `material_lib.py`.
- Needs: Time + wind direction scalar + amplitude → WorldPositionOffset (fold/flap) + optional
  normal offset; inputs like `WindStrength, WindDirection, WindSpeed, FoldingAmount, DrapeMask,
  UV, Time` → outputs `WPO`, `NormalOffset`. Verify compile via material_query.

### B. Melusina hair KawaiiPhysics polish (fluffy collisions)
- Files: `Physics\DA_Melusina_HairCollisionLimits.uasset` (currently sparse: 1 spherical limit),
  `Hair\ABP_Melusina_Hair.uasset` (KawaiiPhysics node; root bone, damping/stiffness, wind).
- Goal: more collision spheres/limits for fluff; tune damping/stiffness; verify wind enabled.
- Kawaii API (v1.21.0): RootBone, LimitsDataAsset (SphericalLimits/CapsuleLimits/PlanarLimits),
  bEnableWind + WindScale + WindDirectionNoiseAngle, ExternalForces.

### C. Melusina skirt KawaiiPhysics polish (fluffy collisions)
- `Physics\DA_Melusina_SkirtCollisionLimits.uasset` current: SphericalLimits
  `c_kilt_master_x` r18, `c_thigh_b_l`/`c_thigh_b_r` r10.5; CapsuleLimits
  `thigh_stretch_l`/`thigh_stretch_r` r13 len38; skeleton SK_Melusina_Skeleton.

### D. Fix irises popping from Melusina's head (skinning bug)
- Known: `Docs\TOMORROW_2026-07-18_ARTIST_DAY_PLAN.md:25` — "bind iris verts 100% to the eye bone".
- Assets: `Meshes\M_Iris_002.uasset`, `M_IRISFRONT_001.uasset`, `M_IRISBACK_001.uasset`,
  materials `Materials\MI_Melusina_IRISFRONT_001`, `MI_Melusina_IRISBACK_001`.
- Postmortem `Docs\MELUSINA_IRIS_POSTMORTEM_2026-07-13.md` = material/UV confusion doc, not the
  pop bug — do NOT touch front/back texture assignment; the pop is skinning/attachment.
- Diagnosis to confirm post-boot: which bone the iris meshes attach to, whether a physics body
  on the iris (SK_Melusina_PhysicsAsset) or attachment to the hair skeleton causes flight;
  fix = bind 100% to the eye bone / re-parent.

## 7. Environment notes
- Monolith MCP: `http://127.0.0.1:9316/mcp` (28 tools). Editor boots via
  `C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe <uproject>`.
- Only ONE editor instance should run. Proxy: `Plugins\Monolith\Binaries\monolith_proxy.exe`.
- material_query has full graph editing (begin_transaction, connect_expressions, set_instance_*).
- Encoding: use `python -X utf8` for console; write MCP JSON to temp files when unicode-heavy.
- Write MCP results to `C:\Users\froma\AppData\Local\Temp\opencode\` when >2KB.
