# Houdini Engine for UE5.8 — Smoke Spec — BS_GodFile

**Date:** 2026-08-27  
**Engine:** UE 5.8 — MeshTerrain-only, NO ALandscape  
**Houdini:** 22.0.368 (installed `C:\Program Files\Side Effects Software\Houdini 22.0.368`)  
**Plugin:** HoudiniEngine 22.0.368 for 5.8 → `Plugins/HoudiniEngine` (copied 2026-08-27, Enabled in .uproject)  
**Related:** `Docs/WorldGen/PROCEDURAL_ENVIRONMENT_BUILD_PLAN...md` · `Content/Python/pcg_scale_world_pipeline.py`

---

## 1. Goal

Prove **HDA → cook inside UE → mesh output** without Landscape, keeping determinism out of Blueprint tick (`AGENTS.md` quantum/service boundary).

Houdini authors the rule, UE cooks it. Output is **Nanite meshes/HISM**, not heightmap-on-Landscape. This replaces the need for Gaea heightmap→Landscape and for 60+ `build_pcg_*.py` Python graph builds for simple stairs/chords.

Non-goal: runtime HDA cook every frame. Cook once at design time, bake to meshes/actors.

## 2. Install (Done 2026-08-27)

```text
SideFX Houdini 22.0.368 installed → C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe (Python 3.13.10)
Houdini Engine Unreal plugin → C:\Program Files\Side Effects Software\Houdini Engine\Unreal\22.0.368\5.8\HoudiniEngine
Copied to → C:\EnvironmentPortfolio\BS_GodFile\Plugins\HoudiniEngine (Binaries/Config/Content/Source + .uplugin Version 22000368)
Added to BS_GodFile.uproject → Plugins: { Name: HoudiniEngine, Enabled: true }
hserver: fromage, Uptime 0:14, Server https://www.sidefx.com/license/sesinetd, No licenses in use yet
```

**Still required — license:**

1. Install **Houdini License Server** (you have it) → run `License Administrator` (`hkey` / `sesictrl`)
2. Sign in with SideFX account → **Get Houdini Engine for Unreal FREE license** (10/studio, commercial) or **Houdini Engine Indie FREE** (3, limited commercial) — https://www.sidefx.com/faq/question/what-houdini-engine-license-do-i-need/
3. Apprentice HDAs **do not** work with Engine licenses — need Indie/Core to author HDAs. FREE Engine license only cooks HDAs in UE, no GUI.
4. After login, `hserver -l` should show `Houdini Engine` license, not `None`.

## 3. Pre-flight Checks (editor closed)

Run `Content/Python/smoke_houdini_engine_pcg.py`:

```powershell
py Content/Python/smoke_houdini_engine_pcg.py
```

Checks: `.uproject` has HoudiniEngine enabled, `Plugins/HoudiniEngine/HoudiniEngine.uplugin` exists, `WP_CELL_SIZE_CM=25600` in `pcg_scale_world_pipeline.py`, `hython` exists, expected plugin folder exists.

All green → proceed to editor. Any red → fix license/path before editor.

## 4. HDA Spec — ArpeggioStair (first useful musical proof)

Reuses the `Build ArpeggioStair` idea from `Docs/Production/PCG/MUSICAL_PCG_NOTES.md` but as HDA, not Python PCG graph.

**HDA:** `hda/ArpeggioStair_1.0.hda` (author in Houdini 22.0.368, publish as HDA)

- **Inputs:** none (or optional curve for placement)
- **Parameters (promoted):**
  - `seed` int (default 1337, drives point seed)
  - `stepCount` int 4..32 (default 16)
  - `laneCount` int 1..8 (default 4)
  - `stepSpacing` float cm (default 200)
  - `laneSpacing` float cm (default 150)
  - `baseMidiNote` int 48..72 (default 60 = C4)
  - `scale` enum [major, minor, pentatonic, chromatic]
  - `heightPerDegree` float cm (default 15) — stair height = scale degree * height
  - `meshChoice` enum [box, beveled_key, proc_mesh]
- **Network (inside HDA):** `Create Points Grid (stepCount x laneCount)` → `Attribute Wrangle (seed = seed + @ptnum; midiNote = baseMidiNote + scaleDegree; lane = @ptnum % laneCount; stepIndex = @ptnum / laneCount)` → `Copy to Points (box/beveled mesh)` → `Output` (mesh + point attributes)
- **Outputs:** `Output 0: Mesh` (Unreal Mesh) + point attributes `seed, midiNote, lane, stepIndex` preserved for PCG/Gameplay
- **Unreal role:** HDA Actor in level, cook → bakes to `StaticMesh` actors or HISM. Attributes become `FPCGPoint.Seed` equivalent — `InitializeFromPCGPoint` pattern reused on baked actors if needed.

PCG alternative: HDA can also output **points** and feed a vanilla PCG graph via `PCG Get Houdini Output` — but mesh output is simpler for P0.

## 5. Unreal Wiring — One Chunk Proof

1. Open `BS_GodFile` in UE5.8, allow HoudiniEngine modules to compile (first open compiles `HoudiniEngine`, `HoudiniEngineEditor`, `HoudiniEngineRuntime`).
2. Verify `Edit → Plugins → Houdini Engine` enabled, no `IsBetaVersion` warnings.
3. Drag `ArpeggioStair_1.0.hda` into `/Game/_PROJECT/ResonantWorld/HDA/` (or `/Game/EnvSandbox/PCG/HDA/`).
4. Place **Houdini Asset Actor** in `L_PCG_Hero_ScaleWorldProof` or new `L_HDA_ArpeggioStair_Smoke`:
   - Set `seed = stable_chunk_seed(world_seed, 0,0)` (e.g., world_seed 3900 → seed from `pcg_scale_world_pipeline.py`)
   - `stepCount 16, laneCount 4` → 64 pads (matches `PCGMusicStepSequencer` 16x4)
   - Cook.
5. **Bake:** `Houdini Engine → Bake to Actors` (or keep cooked HDA Actor for iteration, but bake before World Partition build — baked actors participate in `HLOD_Musical_Static` correctly, cooked HDA Actor does not).
6. Data Layer: Assign baked actors to `DL_Musical_HeroGameplay` if interactive (`exclude_from_hlod true`), or `DL_Musical_StaticArchitecture` if static.
7. PCG origin: HDA transform = `chunk_origin_cm(0,0)` = (0,0,0) for proof center; other chunks use same HDA with different seed/transform via `reusable_graph_binding` philosophy (one HDA, many placements).

## 6. Verification — Musical Chain

Reuse existing proof chain from `SCALE_FIRST_MUSICAL_PCG_PLAN_2026-08-10.md` Step 4 PIE:

1. In PIE, `SetPressedForActor` on one baked pad (or `APCGHeroMusicNode` if you route HDA points through PCG node) → `IsPressed True`.
2. Check `Host ScoreState total=64 hit=1 perfect=0 score=50 streak=1` (for 64 pads).
3. Hear `PlayMusicalNote` via `UMelodiaAudioComponent` (same clock `UMelodiaMusicClockSubsystem`).
4. No second clock, no MPC writer — same `MPC_Melodia_Palette`.

This is the **musical-runtime gate** for HDA path.

## 7. Build & Streaming

- Keep `WP_CELL_SIZE_CM=25600` (`DA_PCGHeroBuilderSettings` `IterativeCellSize 25600`).
- HDA-baked meshes must be `Partitioned` actors (World Partition grid) — verify outliner shows `Is Spatially Loaded`.
- Interactive pads: `NoMerging`, `HISM` or `ISM` per `BP_MelodiaPCGControl` culling.
- After bake, run `Build → Build HLOD`, `Build Navigation`, then `write_grid_report(radius=1)` + `validate_grid()` — seam signatures unchanged because HDA transform = chunk origin.

## 8. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| No Houdini Engine license (hserver shows None) | HDA will not cook | Get FREE Engine license via SideFX Login, restart hserver |
| Houdini 22.0.368 very new | UE 5.8 plugin exists (22.0.368/5.8), but community reports thin | Test HDA cook in copy project first; keep Python PCG path as fallback |
| HDA bakes to non-partitioned actors | break WP streaming | Set actor `Is Spatially Loaded` true, Data Layer correct |
| Apprentice HDA | “incompatible HDA” error | Author with Indie/Core ($299 Indie), not Apprentice |

## 9. Next Steps Checklist

- [ ] License: SideFX login → Houdini Engine FREE → `hserver -l` shows license
- [ ] Reopen UE5.8 → verify Houdini Engine compiles (no UBT errors)
- [ ] Run `py Content/Python/smoke_houdini_engine_pcg.py` → all green
- [ ] Author `ArpeggioStair_1.0.hda` in Houdini 22.0.368 (or use SideFX GameDev Toolset starter HDA)
- [ ] Place in `L_HDA_Smoke`, cook, bake, assign Data Layer
- [ ] PIE: press pad → `PlayMusicalNote` → ScoreState → record
- [ ] If green, repeat with `ChordGarden` HDA (next from MUSICAL_PCG_NOTES)
- [ ] No Landscape actor created at any step

---

**Files:** `Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` · `Content/Python/smoke_houdini_engine_pcg.py`  
**Status:** Plugin installed 2026-08-27, license pending, editor reopen + hython smoke next.
