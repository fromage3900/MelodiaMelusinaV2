# GOAL — Port "Massive World" PCG into Melodia for long-term use (2026-09-24)

**Bounded:** vendor PCG logic enters the project once, in its own folder, re-skinned with our assets through data only. Each step ends in a gate. `L_MelusinaMorning` is adopted last and only with owner OK (Morning content is red-tier).
**Source:** `C:/Users/froma/Downloads/Massive World - Procedural world generation with PCG UE5.5.rar` (717 MB, UE 5.5, plugins `PCG` + `PCGBiomeCore`). Listing: `Saved/Audit/morning_pcg_audit_20260924/massive_world_archive_listing.txt`.
**Project fit:** BS_GodFile is UE 5.8 and already enables `PCG`, `PCGBiomeCore`, `PCGExtendedToolkit`, `PCGWaterInterop`, `Water`. No new plugins needed.

## What the pack is (from the archive listing)

| Area | Size | Keep? |
|---|---|---|
| `MassiveShared/PCG` — `PCG_Spawner`, `PCG_SpawnerOverride`, `PCG_SpawnerSimple`, `PCG_PlaceOfInterest`, `PCG_LoadLevelAssembly`, `PCG_SetLevelByTag`, `PCG_GetWorldLevel`, `PCG_useMountainLevel`/`useWaterLevel`, `PCG_VegetationTransform`, `CalculateMaxSlope` | 3.2 MB | **Yes — core logic** |
| `MassiveWorld/PCG` — `PCG_Biome_3_0` (+2_0, 1), `PCG_RuntimeBiome`, `PCG_Cliff2_0`, `PCG_Lake`, `PCG_River`, `PCG_Road_Water`, `PCG_ParticleStreaming`, `Functions/PCG_IsFertile`/`Slope`/`Spread` | 28.8 MB | **Yes** (Biome 3.0 only; drop 1.0/2.0 after G1 proves 3.0) |
| `MassiveWorld/Blueprint` — `BP_MassiveWorld`, `BP_MassiveWorldEditor`, editor tools (`BP_AreaPlaceBiome`, `BP_FillBiome`, `BP_DrawRiver`/`Lake`/`Cliff`/`RoadRVT`, `BP_SplineRemoveBiome`), stamps, `BP_BiomeMask` | 11.7 MB | **Yes — authoring tools** (drop `BP_RiverSplineBCKP`) |
| `MassiveShared/Blueprint` editor spawner tools, `BP_MassiveTags`, `BP_PlaceOfInterest` | 1.8 MB | Yes (skip `Controller/` pawn/gamemode — we have our own) |
| `Data/DataAsset` — `DA_DemoVegetation*`, `DA_DemoCliff/River/Ocean` | 0.5 MB | Yes, as **templates** for our DAs |
| `Material/MaterialFunction` — landscape layer MFs, `MF_FindWorldLevel`, `MF_GetSlopeData`, `MF_Flowmap`, RVT blend | 0.9 MB | Evaluate only; landscape look stays on `M_Master_Nikki_Landscape` |
| `Texture` (558 MB + 52 MB shared), `StylizedEnvironment` meshes (48 MB), `Audio` (50 MB), `Demo/MassiveWorld_Demo.umap` (53 MB), `Splash` | ~760 MB | **No** — stays in the staging project as reference |

## Steps

### G0 — License — CLEARED 2026-09-24
Owner confirmed the pack is paid for; the `.rar` is the owner's local copy. The owner stages the license entry in `Docs/CREDITS.md`.
- **Gate:** `Docs/CREDITS.md` carries the Massive World entry before the G2 commit.

### G1 — Stage and upgrade outside the repo
- Extract to `C:/EnvironmentPortfolio/_staging/MassiveWorld/` (outside BS_GodFile; never inside `Content/`). Prefer the Fab vault copy once G0 lands.
- Open `Massive.uproject` with UE 5.8 → "Open a Copy" (5.5 is not installed). Fix up redirectors; resave.
- **Gate:** `MassiveWorld_Demo` opens; `PCG_Biome_3_0`, `PCG_River`, `PCG_Lake`, `PCG_Cliff2_0`, `PCG_Road_Water` each generate with zero PCG graph errors in the log (5.5→5.8 node deprecations are the expected breakage — fix in the staging copy, note each fix).

### G2 — Slim migrate into BS_GodFile
- Migrate only the "Yes" rows above to `/Game/ThirdParty/MassiveWorld/` (vendor code stays isolated from `/Game/Melodia` and `/Game/EnvSandbox`).
- Before migrating, retarget every mesh/material/texture reference in the kept DAs to our assets, so the texture/mesh folders never come along.
- **Gate:** reference viewer shows no refs into dropped folders; migrated set < 60 MB; project opens clean; `list_errored_blueprints` = 0. Commit (LFS) on owner OK.

### G3 — Re-skin through data only
- New Melodia DAs from the `DA_Demo*` templates: vegetation → `GenericFlower`/`GenericFlowerTall`, rainbow SpeedTree B0–B6, meadow `_Tall` MIs; rocks/cliffs → existing rock set; water → `PCGWaterInterop` + existing water masters.
- Materials: MIs of existing masters only (Nikki / Universal / `M_Master_Nikki_Landscape`). Pack's `M_MasterMaterial` and landscape MFs are not wired in. No new masters.
- **Gate:** a biome generates with only Melodia meshes/MIs (asset audit of generated ISMs shows zero `/ThirdParty/` render assets).

### G4 — Sandbox proof map
- New `L_MassiveWorld_Sandbox` (World Partition landscape). Not Morning, not `MelodiaIntegrationMap`.
- Author with the pack's own tools: paint 2 biomes, draw a river, a lake, a cliff, a road.
- Roads use RVT (`BP_DrawRoadRVT`): needs `r.VirtualTextures=True`, which is not set in the protected `Config/DefaultEngine.ini` → owner decides; without it, skip roads.
- **Gate:** PIE fly-through clip + `stat unit`/instance counts recorded in `Saved/Audit/`; save-and-reload proof.

### G5 — Hook into the World Compiler
- Map `PCG_PlaceOfInterest` / `PCG_LoadLevelAssembly` onto WorldCompiler hero corners; biome choice driven by movement / music key; seed from the `world.json` manifest.
- Keep PCGEx room-shell/hero-corner graphs as they are; Massive supplies terrain-scale biome + water, WorldCompiler supplies authored set pieces.
- **Gate:** one manifest-driven chunk generates end to end in the sandbox.

### G6 — Morning adoption (owner OK required)
- Only after G4. Replace ad-hoc scatter volumes with biome volumes where it clearly improves the shot; fix the audit findings below in the same pass.

## Morning PCG audit — 2026-09-24 (live, read-only)
Data: `Saved/Audit/morning_pcg_audit_20260924/morning_pcg_volumes.json`. 13 PCG components; none partitioned.

| Actor | Graph | Trigger | State |
|---|---|---|---|
| `Meadow_PCG_Canonical` | `Melodia/PCG/Meadow/PCG_Meadow_RainbowBloom` | on load | OK — 225 inst (GenericFlower, GenericFlowerTall) |
| `WC_HeroCorner_WestRim_PCG` | `WorldCompiler/HeroCorners/PCG_HeroCorner_WestRim` | on demand | 160 inst — **all `SM_Greybox_Rock_A/B/C` blockout meshes** |
| `BP_Morning_GoldenSpiral` | `Melodia/PCG/Morning/PCG_Morning_GoldenSpiralTreads` | on load | OK — 51 inst |
| `WC_morning_rainbow_bloom_Field` | `WorldCompiler/PCG_WorldCompiler_PointField` | on demand | 17 inst — **coral + kelp meshes** (`SM_Coral_*`, `SM_Kelp_*`) in a meadow |
| `WC_HeroCorner_WestRim_PCG_Companion` | `EnvSandbox/PCG/Universal/PCG_RockScatter` | on load | 4 inst incl. `SM_Block_Cube_1` (blockout) |
| `WC_HeroCorner_NorthDress_PCG_Companion` | `PCG_Universal_RockScatter` | on load | 2 inst |
| `WC_HeroCorner_NorthDress_PCG` | `PCG_HeroCorner_NorthDress` | on demand | generated flag set, **0 ISM** — verify output or dead |
| `WC_HeroCorner_EastBank_PCG` | `PCG_HeroCorner_EastBank` | on demand | generated, **0 ISM** |
| `WC_HouseRoomShell_SalonA` | `EnvSandbox/PCG/House/PCG_MelusinaRoomShell_PCGex` | on demand | generated, **0 ISM** (may spawn actors — verify) |
| `WC_CorridorPath_PCG` | `PCG_SplinePath` | on load | generated, **0 ISM** |
| `WC_HeroCorner_EastBank_PCG_Companion` | `PCG_PathScatter` | on load | **not generated** |
| `PCG_MelodiaOpening_Morning_Dressing` | `Melodia/PCG/PCG_Morning_MemoryDressing` | on demand | **deactivated, never generated** |
| `PCG_Escher_PenroseShrine_Morning` | `EnvSandbox/PCG/Styles/Escher/PCG_PenroseShrine` | on load | **zero-extent volume, not generated** |

Findings to decide with the owner (Morning is red-tier; nothing changed):
1. Blockout meshes still generating in the art level (WestRim greybox rocks, `SM_Block_Cube_1`).
2. Underwater coral/kelp in the Morning meadow field — intended or a wrong palette on the point field?
3. Five components claim generated output with no instances; three never produce anything (Penrose zero extent, MemoryDressing deactivated, EastBank companion). Keep-or-remove each.
4. Mixed triggers (6 on-demand, 7 on-load) — on-demand ones rely on a saved generation.

## Not in this goal
Pack textures/meshes/audio/demo map; the pack's player controller/game mode; runtime generation (`PCG_RuntimeBiome`) until the editor-time path is proven; any Morning edit without owner OK.
