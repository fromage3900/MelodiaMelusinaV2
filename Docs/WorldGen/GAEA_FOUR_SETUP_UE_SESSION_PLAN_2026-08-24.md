# Melodia Gaea Four-Setup UE 5.8 Session Plan

**Session objective:** turn four recipe-ready Gaea terrain identities into
isolated, evidence-backed Mesh Terrain test surfaces, then promote only the
first clean vertical slice toward lookdev.

**Current truth:** all four installed Gaea reference graphs parse and validate.
The real Petal Cantata ASTER source mesh exists and is metric. Native Gaea
batch export is not yet proven, so the four JSON files are deterministic setup
contracts, not claims that four native Gaea exports already exist.

## Readiness snapshot before the UE session

The four setup contracts and the matching musical handoff packages are ready on
disk. This is the evidence-backed starting point for tonight; it is not a
claim that the four UE partitions have already been built.

| Setup | Gaea graph | Real source / handoff | UE state | Tonight's gate |
|---|---|---|---|---|
| Sakura Terrace | `C:\Program Files\QuadSpinner\Gaea 2\Examples\Directional Erosion.terrain` | ASTER OBJ at `Content/MelodiaIntegration/ResonantWorld/OfflineWorldGen/PetalCantata_3900/TerrainSources/Yoshino_ASTER_12km_129/PetalCantata_Yoshino_ASTER_12km_129.obj`; `Saved/Audit/world_build_20260824/waltz_garden_waltz/ue_handoff/` | source mesh, Substrate MI, and isolated map exist; partition build pending | build partition, run waltz PCG, clean PIE |
| Liquid Cathedral | `C:\Program Files\QuadSpinner\Gaea 2\Examples\Canyon River with Sea.terrain` | `Saved/Audit/world_build_20260824/cathedral_wide_crystalline/ue_handoff/` | recipe and handoff ready; UE assets/map pending | native export or recorded handoff, water-separated partition |
| Cadence Crystal Ridge | `C:\Program Files\QuadSpinner\Gaea 2\Examples\Creative - Stylized Mountain.terrain` | `Saved/Audit/world_build_20260824/toccata_spires_toccata/ue_handoff/` | recipe and handoff ready; UE assets/map pending | ridge partition, grounded crystal landmark |
| Fugue Grotto | `C:\Program Files\QuadSpinner\Gaea 2\Examples\Collapsed Gullies.terrain` | `Saved/Audit/world_build_20260824/fugue_maze_fugue/ue_handoff/` | recipe and handoff ready; UE assets/map pending | gully partition, route exclusion, grounded entrance |

The recorded handoff packages currently measure `65 x 12` pixels, so they are
usable as deterministic import smoke tests, not final AAA terrain. Replace each
with the native Gaea 4097 target (or a documented high-resolution Gaea export)
before visual promotion. The only currently proven metric geometry is the
12 km x 12 km, 129 x 129 ASTER source mesh; its manifest records SHA-256
`8042fe736e349f93399000222a5240de3ebe0e30500382101e30ad73fe0f534b`.

## Four setups

| Order | Setup | Gaea reference | Musical identity | First UE proof |
|---|---|---|---|---|
| 1 | Sakura Terrace | Directional Erosion | `waltz_garden_waltz` | terrain + blossom route + clean capture |
| 2 | Liquid Cathedral | Canyon River with Sea | `cathedral_wide_crystalline` | basin + water separation + PCG |
| 3 | Cadence Crystal Ridge | Creative Stylized Mountain | `toccata_spires_toccata` | skyline ridge + crystal landmark |
| 4 | Fugue Grotto | Collapsed Gullies | `fugue_maze_fugue` | branching route + entrance exclusion |

Contracts:

- `GAEA_SETUP_SAKURA_TERRACE_2026-08-24.json`
- `GAEA_SETUP_LIQUID_CATHEDRAL_2026-08-24.json`
- `GAEA_SETUP_CADENCE_CRYSTAL_RIDGE_2026-08-24.json`
- `GAEA_SETUP_FUGUE_GROTTO_2026-08-24.json`

## Session order

### 0. Preflight — 20 minutes

- Confirm the live UE project and Monolith bridge are healthy.
- Work only under `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/`.
- Confirm the project has `MeshPartition`, `MeshPartitionWater`,
  `PCGMeshPartitionInterop`, and `GeometryScripting` enabled. Do not enable or
  create a classic Landscape path.
- Record the source OBJ SHA-256 and the selected setup contract.
- Run `Content/Python/stage_uds_sky_gaea_levels.py` once from the live editor;
  it creates/loads four isolated World Partition maps and places the installed
  `/Game/UltraDynamicSky/Blueprints/Ultra_Dynamic_Sky` actor in each. Verify the
  generated report at `Saved/Audit/gaea_setups/uds_sky_stage_report.json`.
- Do not touch `L_WP_SakuraDream`, Headquarters BFG, RenderTests, gameplay
  saves, or the webfront.

### 1. Sakura Terrace — 60 minutes, P0 anchor

- In Gaea, open the Directional Erosion reference and export the 4097 target
  using the Sakura contract's `4000 m x 4000 m` output extent. If native export
  is unavailable, use the recorded handoff only for an import smoke test and
  record that substitution.
- Import the metric mesh as **Mesh Terrain**, never a classic Landscape.
- Build the partition and attach the landscape height-blend material.
- Run the `waltz_garden` PCG profile against the generated partition.
- Check route width, blossom landmark grounding, and local surface height.
- Run PIE and capture `PIE_SakuraTerrace_1920x1080.png` only if clean.

### 2. Liquid Cathedral — 45 minutes

- Open the Canyon River with Sea reference and export the `5000 m x 3000 m`
  basin from the Liquid Cathedral contract; stage the recorded handoff only as
  a fallback smoke test.
- Build a separate Mesh Terrain partition.
- Keep water as a separate water system; do not bake water into terrain
  collision.
- Verify basin, flow mask, waterline, cathedral dressing, and PCG counts.
- Run PIE and capture only after water and terrain collision agree.

### 3. Cadence Crystal Ridge — 45 minutes

- Open the Creative - Stylized Mountain reference and export the Cadence
  `4000 m x 4000 m` ridge; stage the recorded handoff only as a fallback smoke
  test.
- Build the partition.
- Verify the ridge mask, ascent route, and one grounded crystal hero landmark.
- Assign ebony/ivory accent materials only to musical hero assets.
- Capture a clean skyline frame with no debug overlays.

### 4. Fugue Grotto — 45 minutes

- Open the Collapsed Gullies reference and export the Fugue `4000 m x 4000 m`
  gully field; stage the recorded handoff only as a fallback smoke test.
- Build the partition.
- Verify five route branches, the route exclusion mask, and a grounded grotto
  entrance.
- Keep dead ends intentional and record the route graph in the evidence JSON.
- Capture only after traversal/collision checks pass.

### 5. Shared validation — 45 minutes

For each setup record:

- source and output SHA-256;
- world extent, resolution, and import scale;
- Mesh Terrain partition build result;
- PCG generated count and tagged musical outputs;
- prop grounding and collision result;
- PIE runtime gate: zero Blueprint Runtime Error, Accessed None, Fatal,
  Ensure, and cached-lighting matches;
- clean standalone PNG path and visual-review status;
- frame-time/performance sample at the intended density.

## Stop and rollback rules

- Any import/build failure stays inside the setup namespace and is recorded;
  do not repair production maps during the session.
- A technical render is not a beauty approval. Reject black/checker frames,
  floating props, broad empty substrate, editor chrome, debug icons, and
  placeholder materials.
- Do not ingest any capture into the webfront until lookdev validates it.
- Do not commit the whole dirty worktree. Isolate only the four contracts,
  handoff manifests, and verified evidence after the session.

## Definition of done for tonight

The minimum successful outcome is Sakura Terrace with a built UE 5.8 Mesh
Terrain partition, musical PCG output, clean PIE evidence, and one approved
standalone capture. The other three setups are successful when their contracts
are staged, their partitions build, and their validation manifests exist; they
do not need webfront promotion tonight.

If the session ends before native Gaea export, the honest checkpoint is still
useful: four validated contracts, four named Gaea references, four deterministic
Mesh Terrain handoff packages, four isolated UDS-ready map targets, and an
explicit list of the remaining partition/export gates. Do not label that
checkpoint AAA-complete until the high-resolution exports, partition builds,
clean PIE evidence, and visual review all pass.
