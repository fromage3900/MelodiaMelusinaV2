# Melodia Gaea Four-Setup UE 5.8 Session Plan

**Session objective:** turn four recipe-ready Gaea terrain identities into
isolated, evidence-backed Mesh Terrain test surfaces, then promote only the
first clean vertical slice toward lookdev.

**Current truth:** all four installed Gaea reference graphs parse and validate.
The real Petal Cantata ASTER source mesh exists and is metric. Native Gaea
batch export is not yet proven, so the four JSON files are deterministic setup
contracts, not claims that four native Gaea exports already exist.

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
- Confirm Mesh Terrain plugins and `PCGMeshPartitionInterop` are available.
- Record the source OBJ SHA-256 and the selected setup contract.
- Do not touch `L_WP_SakuraDream`, Headquarters BFG, RenderTests, gameplay
  saves, or the webfront.

### 1. Sakura Terrace — 60 minutes, P0 anchor

- Export or stage the 4097 target from the Directional Erosion contract.
- Import the metric mesh as **Mesh Terrain**, never a classic Landscape.
- Build the partition and attach the landscape height-blend material.
- Run the `waltz_garden` PCG profile against the generated partition.
- Check route width, blossom landmark grounding, and local surface height.
- Run PIE and capture `PIE_SakuraTerrace_1920x1080.png` only if clean.

### 2. Liquid Cathedral — 45 minutes

- Stage the Canyon/River output and build a separate Mesh Terrain partition.
- Keep water as a separate water system; do not bake water into terrain
  collision.
- Verify basin, flow mask, waterline, cathedral dressing, and PCG counts.
- Run PIE and capture only after water and terrain collision agree.

### 3. Cadence Crystal Ridge — 45 minutes

- Stage the stylized ridge output and build the partition.
- Verify the ridge mask, ascent route, and one grounded crystal hero landmark.
- Assign ebony/ivory accent materials only to musical hero assets.
- Capture a clean skyline frame with no debug overlays.

### 4. Fugue Grotto — 45 minutes

- Stage the collapsed-gully output and build the partition.
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
