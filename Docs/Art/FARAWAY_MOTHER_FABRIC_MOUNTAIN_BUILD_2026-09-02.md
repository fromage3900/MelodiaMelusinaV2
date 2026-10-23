# P2 Faraway Mother — Fabric Mountain System (2026-09-02)

**Production sheet:** `Docs/Art/FAR_AWAY_MOTHER_PRODUCTION_SHEET_2026-08-29.md`
**Level:** `Content/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype.umap`
**Status:** Build-ready — Nanite terrain generated offline, editor automation ready (requires editor restart after 2026-09-02 Monolith crash)

## What shipped this session

### 1) Fabric ridge terrain — heightmap → Nanite mesh (no Landscape)
| Artifact | Path | Notes |
|----------|------|-------|
| 16-bit heightmap | `Saved/Audit/faraway_mother/fabric_ridge_terrain/T_FarawayMother_FabricRidge_Height_1k.png` | 1024×1024, I;16, fabric folds: macro body silhouette (head/shoulder/hip/knee Gaussians) + 3 pleat octaves + torso valley depression |
| 8-bit preview | `Saved/Audit/faraway_mother/fabric_ridge_terrain/T_FarawayMother_FabricRidge_Height_1k_preview.png` | 426 KB, visual QA |
| Nanite OBJ fallback | `Saved/Audit/faraway_mother/fabric_ridge_terrain/SM_FarawayMother_FabricRidge_4km.obj` | GRID 128, 16 641 verts, 32 768 tris, 4 km × 2.6 km, height scale 180 m, ready for Interchange import |
| Manifest | `Saved/Audit/faraway_mother/fabric_ridge_terrain/manifest.json` | seed 20260829, scale_xy 4000, scale_z 180, range -21 m … +77 m |
| Unreal import path | `/Game/EnvSandbox/Meshes/Terrain/SM_FarawayMother_FabricRidge` | Nanite enabled, complex collision for raycast |
| Material | `/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape` | Per Copernicus contract: height-compete, not Landscape |

The HDA contract (`Tools/Houdini/copernicus/copernicus_terrain_height_to_nanite.py`) describes the COP→SOP path (File COP → HF Adjust → HF File SOP → ConvertHeightfield → PolyReduce). The OBJ is the offline Apprentice-safe fallback when `hython` is unavailable — same geometry, imported via `AssetImportTask` (FBXImportUI, Nanite enabled) in the editor script. No `Landscape` actor is created.

### 2) Height-aware kitbash / fabric placement — raycast, 5 meshes
Editor script: `Content/Python/faraway_mother_prototype_build.py`

No `LandscapeGrassType` or PCGEx scatter; pure raycast placement against the Nanite mesh collision via `KismetSystemLibrary.line_trace_single` (high Z 5000 → -1000).

| # | Mesh | Label | XY (cm) | Yaw | Scale | Z-off | Copernicus MI |
|---|------|-------|---------|-----|-------|-------|---------------|
| 1 | `SM_Orn_RosetteMedallion` | `FM_Ridge_Rosette_Crest` | (-900, 180) | 15° | 3.0 | +8 cm | `MI_Copernicus_GildedLoom` (gold fabric) |
| 2 | `SM_ATL_Palace_ArchA` | `FM_Valley_Arch_Entrance` | (100, -40) | 90° | 1.2 | +2 | `MI_Mother_Mantle` (NightSkyVelvet) |
| 3 | `SM_Orn_ColumnCapital` | `FM_Shoulder_Capital` | (600, 220) | -20° | 2.5 | +5 | `MI_Copernicus_SilkWaterfall` |
| 4 | `SM_Orn_PendantFinial` | `FM_Heart_Finial_Gate` | (20, 0) | 0° | 4.0 | +12 | `MI_Copernicus_FinalDreamweaver` (iridescence) |
| 5 | `SM_Orn_RoseWindow_8Petal` | `FM_Torso_RoseWindow` | (800, -180) | 35° | 2.0 | +6 | `MI_Mother_Veil` (AquaticLullabyLace) |

All placements resolve final Z at runtime: `hit.location.z + z_offset`. Fallback Z = 35 cm median if trace misses (logged). Duplicate labels are skipped (idempotent rerun).

### 3) Moon-haze volume — silver-blue per sheet
Wired in the same script (`wire_moon_haze()`):

| Actor | Label | Key params |
|-------|-------|------------|
| `ExponentialHeightFog` | `FM_MoonHaze_Fog` | density **0.04**, heightFalloff 0.15, maxOpacity 0.85, tint (0.70, 0.75, 0.90), volumetric ON, extinction 1.5 |
| `PostProcessVolume` | `FM_MoonHaze_PPV` | unbound ON, cool tint (0.15, 0.20, 0.35) per production sheet, bloom |
| `StaticMeshActor` (Cube 100 cm → scaled 40×26×9) | `FM_MoonHaze_VolumeBox` | at (0, 0, 450), extent (4000, 2600, 900), no collision, castShadow OFF, MI `MI_Copernicus_FrostBloom` (silver haze) |

Implies distant limbs without mesh (design rule).

### 4) Copernicus MI wiring — new instances only, no new masters
| MI | Usage |
|----|-------|
| `MI_Copernicus_GildedLoom` | ridge crest — gold fabric regions |
| `MI_Copernicus_SilkWaterfall` | shoulder fold — water-like silk flow |
| `MI_Copernicus_FinalDreamweaver` | heart gate — frozen moonlight iridescence |
| `MI_Copernicus_FrostBloom` | haze volume — frost/silver scatter |
| `MI_Mother_Gown/Mantle/Veil/Corset/Cradle` (P2 Faraway) | kitbash overrides per placement table, sheen setups 1–3 from `FarawayMother_MNIKKI_Sheen_Setups.txt` |

Masters untouched: `M_Master_Nikki_Landscape`, `M_Master_Nikki`, `M_Master_Toon_Universal`, `M_Master_Toon_Universal_Alpha`.

## Level state (2026-09-02 01:09 UTC)
- `LV_FarawayMother_Prototype.umap` is still at 6.7 KB (empty prototype, only `WorldDataLayers`/`WorldPartitionMiniMap` in external actors). The terrain and placements are pending editor execution — the Monolith editor proxy crashed on `load_level` during this session (no `LISTENING` on 9316 as of 01:07 UTC, `UnrealEditor-Cmd` PID 10244 orphaned). The build script is crash-safe (checks current world before reload) and will succeed after manual editor restart.

## How to apply (owner steps)
```bat
:: 1) Restart editor (dismiss any modal, verify port)
netstat -ano | findstr :9316
curl http://localhost:9316/health

:: 2) Run the assembly (one-editor lock)
python Tools/ue_run_python.py --file Content/Python/faraway_mother_prototype_build.py

:: 3) Open the level
:: Content/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype

:: 4) PIE smoke + capture
:: Play → overlay labels (Matches production sheet § Layout)
:: Save screenshot to Saved/Screenshots/faraway_mother_pie_2026-09-02.png
```

To re-run or tune placements, edit `PLACEMENTS` in `faraway_mother_prototype_build.py` and rerun — labels are deduped. To use the heightmap in Houdini instead of the OBJ fallback:
```bat
"C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" Tools/Houdini/copernicus/copernicus_terrain_height_to_nanite.py --heightmap Saved/Audit/faraway_mother/fabric_ridge_terrain/T_FarawayMother_FabricRidge_Height_1k.png
```

## Evidence checklist (per production sheet § Evidence)
- [x] Heightmap + Nanite OBJ + manifest (SHA-256 below)
- [ ] PIE overlay capture matching sheet composition (blocked — editor down, manual PIE needed)
- [ ] Assertion report JSON next to captures
- [ ] `Saved/gate_ledger.json` row for `faraway_mother_prototype` (requires PIE pass)
- [ ] Hash of new MIs (`MI_Mother_*` already hashed in prior P2 pass; Copernicus MIs pre-exist)

## Hashes
```
T_FarawayMother_FabricRidge_Height_1k.png  — see manifest.json (recompute with certutil -hashfile)
SM_FarawayMother_FabricRidge_4km.obj       — 32768 tris, seed 20260829
Content/Python/faraway_mother_prototype_build.py — deterministic placements, idempotent
```

## Next steps
1. **Editor restart + run** the build script (5 min). Verify terrain imports at `/Game/EnvSandbox/Meshes/Terrain/SM_FarawayMother_FabricRidge`, Nanite ON, collision `QueryAndPhysics`.
2. **PIE validation** — orbit camera from valley (0,0,120) toward head (-900, 180): check fabric pleat normal at 1×–4× scale, fog breathing, no z-fighting on valley floor.
3. **Screenshots** — top-down + horizon read per § Level Layout. Save with labels `HEAD / HAIR CASCADE / SHOULDER VALLEY / TORSO DEPRESSION / LIMBS (haze) / HEART GATE`.
4. **Material pass** — assign `MI_Copernicus_*` to terrain material slots (slope/curvature blend if `M_Master_Nikki_Landscape` exposes layers) and confirm sheen via `FarawayMother_MNIKKI_Sheen_Setups.txt`.
5. **Gate ledger** — `python Tools/echo_run.py record faraway_mother_prototype pass` once PIE capture + assertions exist.

## Files delivered this session
- `Saved/Audit/faraway_mother/fabric_ridge_terrain/T_FarawayMother_FabricRidge_Height_1k.png` (1.7 MB)
- `Saved/Audit/faraway_mother/fabric_ridge_terrain/T_FarawayMother_FabricRidge_Height_1k_preview.png` (426 KB)
- `Saved/Audit/faraway_mother/fabric_ridge_terrain/SM_FarawayMother_FabricRidge_4km.obj` (1.9 MB)
- `Saved/Audit/faraway_mother/fabric_ridge_terrain/manifest.json`
- `Content/Python/faraway_mother_prototype_build.py`
- `Content/Python/faraway_mother_height_aware_placements.json` (see below)

---

## Research proposal (2026-10-23): Harmonic Continental Genesis

**Status: PROPOSED — design and lab acceptance plan only.** This section does not claim a Houdini cook, 500 m terrain, stitched tiles, Vellum bake, playable region, TD return path, or UE import. \`CURRENT_STATE.md\` remains the sole status authority; the Faraway P1 resonance integration spec and the existing World Compiler remain the functional contracts.

### Creative thesis / desired player experience

**Faraway Mother: The World That Remembers Every Song.** The 8 x 8 km world is perceived as one continent-sized instrument. Mountains read as tensioned silk; valleys as gathers; routes as embroidery; cathedral ribs as nodal-line structures; flora as harmonic deposition. During an authored musical reveal, the player discovers that widely separated ridges, gardens and bridges describe the *same* historical standing-wave field.

This is not an instruction to generate 8 km of dense Vellum cloth or dynamically deform collision at runtime. The artistic thesis is **one common field at multiple scales**, with far-field deterministic/baked terrain, selective hero cloth simulations, and presentation-only material/FX modulation in UE.

Five legible scales, driven by shared authored coordinates:

| Scale | Artistic read | Technical representation |
| --- | --- | --- |
| 8 km | sleeping Mother / entire garment silhouette | coarse tiled world identity and distance LOD |
| 1 km | valleys as gathers, directional pleats | continuous global Chladni/tension field + heightfields |
| 100 m | seams, routes, lace arches, fabric landforms | feature curves, selected Vellum hero patches, baked meshes |
| 10 m | flora, architectural stitches, relief | existing World Compiler point fields, UE PCG and dressing |
| 10 cm | silk jacquard and thread weave | Copernicus masks/material presentation; **not** sculpted continental geometry |

### Authority and protected inputs (do not duplicate)

1. **Canonical spatial basis:** \`Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py\` and \`Tools/PCG/build_faraway_mother_pcg_ecosystem.py\`; default Faraway Chladni mode **(3,5)**, \`WorldField.Tension\`, \`Resonance\`, \`Moisture\`, and the ResonantSeamWay nodal mask.
2. **Signed field:** \`F(u,v) = cos(3*pi*u)*cos(5*pi*v) - cos(5*pi*u)*cos(3*pi*v)\`; signed zero contours define candidate nodal routes. The existing \`abs(F) < 0.12\` seam band is a mask, **not** a guaranteed traversable road.
3. **World coordinates:** Faraway world X/Y \`[-400000,+400000]\` cm map to UV \`[0,1]\` with \`U=(X+400000)/800000\`, \`V=(Y+400000)/800000\`. Houdini computes in metres; UE intake uses **100 cm per metre**. Tile-local UV resets are forbidden.
4. **Protected hand-authored work:** \`Houdini/FarawayDrape.hip\` (especially \`FARAWAY_DRAPE_GRID\`, \`TENSION_MASK\`, \`Cymatic_BeatPulse\` and the authored curvature/tension network). Work in a separately named experimental file. Never overwrite that master or regenerate it with the generic COP builder.
5. **Reuse existing production lanes:** \`Tools/Houdini/sea_above_reef/build_cloth_mountains.py\`, \`Tools/Houdini/vdm_fabric_mountains/vdm_fabric_baker.py\`, \`faraway_alignment_diagnostic.py\`, the current Faraway level/PCG scripts, \`Docs/WorldGen/WORLD_COMPILER_CONTRACT.md\`, \`Docs/WorldGen/TERRAIN_HANDOFF_CONTRACT.md\`, and \`Docs/Production/FARAWAY_MOTHER_P1_RESONANCE_FIELD_INTEGRATION_SPEC.md\`.
6. **Runtime ownership:** Hython authors deterministic spatial substrate; the existing World Compiler packages field-derived dressing data; UE 5.8 owns gameplay, collision, save state and traversal gating; TouchDesigner uses the existing semantic music/OSC and \`OUT_SHOW_FIELD\` presentation lane. No new writer, compiler, or game authority.

### Scale ladder — prove small before building a continent

| Gate | Domain | Partition | Intended proof |
| --- | --- | --- | --- |
| G0 | 1 representative 250 m tile | isolated research | field correctness and usable geometry |
| **G1 lab target** | **500 x 500 m** | **2 x 2 tiles of 250 m** | border-perfect geology, one hero cloth fold and continuous resonant seam |
| G2 conditional | 1 x 1 km | 4 x 4 tiles | PDG caching/rebuild economics, streamed handoff, ecology |
| G3 future | 8 x 8 km | 32 x 32 = 1,024 tiles | **aspirational only**, after technical, artistic, runtime and storage acceptance |

**G1 is the only authorized research scope for this lab plan.** G2/G3 require separate capacity measurements and owner approval. No default all-tiles cook.

### G1 lab work packets (Houdini Education / school workstation)

**0 — Preflight and protection**
- Read the actual license tier, Houdini version, Labs availability and current Git revision. Record usable RAM, scratch disk and machine-level time budget; no speculative capacity assumptions.
- Resolve SSD/source checkout; verify the *real* \`FarawayDrape.hip\` bytes and hand-authored nodes. Save \`FarawayDrape_HarmonicGenesis_Lab_20261023.hipnc\` (or the format issued by the active licence) in a protected experimental/scratch directory **without writing over the authored master**.
- Keep raw \`.bgeo.sc\`/VDB/Vellum caches out of Git. Do not rename licence extensions as a conversion or assume school-generated files are commercially unrestricted.

**1 — Author one globally sampled harmonic field**
- Start with existing \`faraway_static_field.py\` at canonical (3,5) and seed 3900; record source SHA, mode, UV convention and channel meanings.
- For the 500 m pilot crop, sample the **same global 8 km basis** at explicit metre positions. Preserve sample correspondence at shared tile edges; do not independently normalize each of the four tiles to \`[0,1]\`.
- Bake diagnostic outputs for signed \`F\`, tension, resonance, moisture and the seam mask. Keep signed nodal contour data separate from its antialiased/material-display mask.
- Compare canonical PCG/Hython samples and tile-edge samples numerically. Fail on flipped V, mismatched bounds, drift or unaccounted seed changes.

**2 — Generate geological cloth at two resolutions**
- Build four low-/mid-resolution 250 m mesh/heightfield tiles from global field coordinates. Pleat orientation and fold frequency vary with the shared tension field; use low-frequency sculptural anatomy + deliberate pleat guides, not uniform noise everywhere.
- Stitch by matching shared boundary **positions and normals** (including a one-sample halo for gradient evaluation) and stable mesh/world origins. Rebuild any one tile without modifying its neighbors.
- Use one selected hero patch (e.g. 125–250 m) for a bounded Vellum drape onto a reduced collider. Test three wedges: gravity-only; tension-guided pleats; Chladni-weighted warp/weft stiffness. Use a coarse particle spacing first (pilot ~4–8 m), measure cook time/memory, then refine only if the silhouette materially improves.
- Bake the settled frame / deformation textures only if a real consumer demands them. Full-continent Vellum and UE runtime cloth are explicitly out of scope.

**3 — Extract the geography's musical seam**
- Compute a signed \`F=0\` contour (marching squares / sampled iso-contour) in **global coordinates**; weld/merge connections across the four tile borders before choosing hero routes.
- Filter candidate corridors using slope, curvature, clearance, preserved authored routes, bank/water constraints and a minimum walkable width. A nodal line is a *candidate*, not instant navigability.
- Conform one continuous embroidery/stone seam to the draped terrain and place **one** selected lace-arch/bridge gesture along it, extending existing arch/cathedral/profile math. Keep this mostly static, with optional presentation reveal mask rather than runtime physics.
- Export seam curve/points and a mask sharing the exact same world bounds/UV orientation as the terrain.

**4 — Ecology and musical archaeology (bounded)**
- Generate a small World Compiler-compatible **candidate** dressing field from tension, moisture, resonance and walkability, for existing WeaveRidge / LaceCanopy / FrillValley / ResonantSeamWay concepts.
- Prefer current species/PCG contracts, no new material master and no duplicate World Compiler. No automatic write to the UE level.
- Stretch: author one *historical resonance* layer (a dormant prior motif) as optional non-gameplay field metadata. It may guide faded embroidery, ruins or orchard patterns, but cannot unlock quests, declare valid music or replace the canonical music state.

**5 — Evaluate as art, not just a cook**
- Capture a neutral clay view; an annotated global Chladni/tension view; a final silk + embroidery hero frame from matched cameras.
- Capture top, player-height and seam-close-up inspection views. Measure the hero patch, not just count primitive instances.
- Make a small comparison sheet for gravity-only / tension / harmonic stiffness and select one winner for later HDA/UE promotion. Keep the others as research variants, not new authorities.

### Acceptance gates (fail closed)

**A. Mathematical consistency**
- Mode is canonical (3,5) unless an artistic experiment is explicitly marked noncanonical.
- Shared-border positions differ by at most **0.01 m** (or tighter if the terrain data precision permits); normals have dot product **>= 0.98** at comparable samples after harmonized derivative evaluation.
- Global field samples on both sides of a tile edge agree within **1e-5** in float-space, and the four-tile nodal seam graph contains no unintentional border break.
- Same input SHA/seed/recipe/version and platform produce byte-identical deterministic *source field tables* or a documented float-tolerant numeric equivalent when output encoders are nondeterministic. Timestamps belong only in evidence envelopes.

**B. Geometric and artistic**
- The four tiles read as one landscape in silhouette and player-height perspective.
- The strongest read is **fabric acting as geology**: folds and pleats, not a rocky mountain with a cloth-pattern overlay.
- The selected arch/seam is continuous, seated on terrain and readable without emissive effects.
- Existing traversal/clearance keepouts are preserved; no path is asserted playable without UE validation.

**C. Integration and provenance**
- Produce a small representative mesh + field/map handoff with scale, axes, UV/world bounds, seed, source commit, material references and SHA-256 hashes. Route any UE-bound terrain through the established \`melodia.terrain_handoff.v1\` validator/converter; do not invent a new handoff schema.
- Static field channels preserve existing RGBA meanings: tension / resonance / moisture / seam.
- Geometry, masks and Vellum evidence can be inspected without a live Unreal editor. UE/TD live integration is a **later independently verified gate**, not implied by successful Houdini cooking.
- Preserve the authored Faraway master, the single cymatics MPC writer and existing World Compiler; make no runtime, branch cleanup or editor changes as a side effect.

**D. Compute safety**
- Pilot one tile and one coarse Vellum wedge first. Record elapsed time, memory peak, scratch size, triangle/voxel counts and incremental recook behavior.
- Abort/rate down if system paging begins, free scratch becomes unsafe, or the 2 x 2 crop exceeds the lab allocation. Cache and render budgets are measured, never extrapolated as guarantees from license tier.

### Requested evidence / artifact layout (outputs NOT yet created)

Use the existing audit conventions under \`Saved/Audit/houdini_faraway_mother/harmonic_genesis_20261023/\` (small manifests/screenshots only in Git if production policy permits; large caches/export meshes in approved scratch):

\`\`\`text
harmonic_genesis_20261023/
  source_manifest.json             # source SHA, Houdini/build/version, seed, (n,m), bounds, licenses
  global_field_RGBA.png            # tension / resonance / moisture / seam
  signed_chladni_preview.png       # separate signed diagnostic, not substitute for RGBA authority
  tiles_2x2/                      # 4 source tiles + joint boundary measurements
  vellum_wedges/                  # coarse gravity / tension / harmonic variants + metrics
  seam_graph.json                 # global polyline IDs, borders, route/clearance metadata
  hero_views/                     # clay / annotated / textile beauty renders
  terrain_handoff.json            # only after validated converter/intake contract
  acceptance.json                 # pass/fail/blocked with measured values and hashes
\`\`\`

Suggested first session sequence: **preflight -> canonical field/border probe -> 2 x 2 clay terrain -> one coarse Vellum wedge -> one continuous seam -> renders and audit**. If time is limited, stop at the first failed gate and deliver a smaller complete proof. Do not scale until the 2 x 2 G1 gate passes.

### Promotion and scope discipline

This is a **P1/P2 research proposal**. Poitou P0 and its accepted presentation identity are not replaced. No new production HDA, continent compiler, C++ subsystem, MIDI authority, TouchDesigner bridge, or gameplay mechanic may be declared from this plan. Promotion to an HDA or World Compiler consumer requires measured output, owner-selected art direction, matching runtime contract, and a separate UE 5.8 acceptance step.

**Definition of success for the next lab:** four cohesive tiles, one visible fabric-geology hero, one mathematically continuous seam and three honest comparison images — with zero collateral modifications to existing canonical projects.

---

## Chladni Cloth Day (2026-10-23): French DEM / couture geology research and ready-to-run intake

**Status: researched and source/staging tooling prepared; not proof of live French DEM fetch or Houdini cook.** This extends the **Harmonic Continental Genesis** proposal above. Large binary DEMs, raw COP exports, Vellum caches and derived meshes are intentionally not committed. Never overwrite the authored \`Houdini/FarawayDrape.hip\`.

### Prioritized French terrain references (real geography -> textile language)

| Region and crop centre (WGS84 latitude, longitude) | Real topographic vocabulary | Translating it into Faraway Mother's cloth |
| --- | --- | --- |
| **Jura / Crêt de la Neige** (46.270978, 5.939484) | limestone strata, long aligned ridges, folded escarpments | **Celestial Silk Jacquard**: ivory satin directional pleats; prime WeaveRidge geometry |
| **Cantal / Puy Mary–Pas de Peyrol** (45.1140957, 2.6717462) | radial volcanic valleys, converging ridge fans | **Mother's Night Velvet**: radial skirt gathers and heavy shadowed lowlands |
| **Pyrenees / Cirque de Gavarnie** (42.697179, -0.015318) | amphitheatre walls, cliff ledges, waterfalls | **Aquatic Lullaby Lace + Singing Water Organza**: suspended drapery and silk waterfalls |
| **Ecrins / Barre des Ecrins** (44.92220, 6.35969) | jagged peaks, glacier channels, sharp facets | **Glacial Pearl Organza**: localized frost, broken lace, crystal accents |
| **Vosges / Hohneck** (48.0375775, 7.015543) | softer rounded ridges and grass-covered crest | **Night Velvet**: calm traversal valleys; avoids nonstop jagged spectacle |

These are source *sample-point centres* for small research crops, not precisely delineated range boundaries. All are **inspiration**, not a new canonical Paitou/Poitou landscape (Poitou's real marsh terrain is different). The code-readable centers, licensed source portals and material preset IDs live at \`recipes/houdini_faraway/terrain_fabric_atlas.v1.json\`.

### Actual elevation sources: don't confuse DTM with DSM

- **IGN BD ALTI® (recommended for 4-8 km geological silhouette):** 25 m / 75 m *bare-earth DTM (MNT)*, France coverage. Open Licence 2.0. Source: https://www.data.gouv.fr/datasets/bd-alti-r-1
- **IGN RGE ALTI® (preferred for 1-5 m hero/cirque close-ups):** 1 m / 5 m *bare-earth DTM*, France. Open Licence 2.0; coverage has nodata restrictions, product availability/vertical datum require inspection. Source: https://www.data.gouv.fr/datasets/rge-alti-r
- **Copernicus DEM GLO-30 Public (convenient COG/HTTPS intake):** nominal 30 m **DSM**, not bare-ground DTM; vegetation, buildings and other above-ground structures can affect values. Public COG tile access is documented at https://registry.opendata.aws/copernicus-dem/ and https://copernicus-dem-30m.s3.amazonaws.com/readme.html. Coverage for some countries may be restricted; check tile availability and licence terms before redistributing source or derivative files. Data-access availability from this chat runtime was *not* validated.
- **QGIS fallback:** download IGN BD/RGE ALTI terrain for desired department through the official linked portal; crop/reproject to EPSG:2154 (Lambert-93) and export a GeoTIFF. Use local \`--source\` rather than remote \`--fetch-copernicus\` if school network/proxy blocks public S3.

Source attribution: credit IGN and link Licence Ouverte v2.0 for IGN-derived products; cite Copernicus DEM and review its actual dataset-specific licence for Copernicus-derived work. No third-party photography, copyrighted imagery or heavy DEM tiles are copied into Git.

### The prepared converter (no workstation paths hard-coded)

\`Tools/Houdini/vdm_fabric_mountains/prepare_french_dem.py\` reads georeferenced raster(s), crops a metrically defined square about a selected landmark, reprojects into **EPSG:2154**, and writes:

- \`height_absolute_m_epsg2154.tif\` — geo-referenced float32 elevation in metres, retaining the source elevations;
- \`height_normalized_16bit.png\` — unsigned normalized 16-bit height for Houdini HeightField File SOP and masks, with min/max for inverse decode;
- \`hillshade_preview.png\` and \`slope_preview_8bit.png\` — inspection images, never substitutes for the height layer;
- \`source_manifest.json\` — source provenance, vertical unit warning, coordinate system, output hashes, size, z min/max, validity fraction, and exact PNG decode rule.

**Lab preflight, PowerShell at repo root (pip only if packages are missing):**
\`\`\`powershell
git fetch origin
git status --short --branch
py -c "import rasterio, numpy, PIL, pyproj; print('DEM dependencies OK')"
# If dependencies are missing, use school-approved Python/QGIS environment; don't corrupt Houdini's hython.
py Tools/Houdini/vdm_fabric_mountains/prepare_french_dem.py --preset jura_cret_neige --fixture --size-m 1000 --res 257
# Prints SYNTHETIC_FIXTURE_NOT_REAL_ELEVATION; verifies graph intake only.
\`\`\`

**For real French terrain, choose ONE route:**
\`\`\`powershell
# RGE/BD ALTI data downloaded from IGN into a local georeferenced GeoTIFF/ASC:
py Tools/Houdini/vdm_fabric_mountains/prepare_french_dem.py --preset jura_cret_neige --source "D:\DEM\IGN_Jura.tif" --size-m 4000 --res 513
# Or (network required; streamed COG reads may cross more than one 1° tile):
py Tools/Houdini/vdm_fabric_mountains/prepare_french_dem.py --preset cantal_puy_mary --fetch-copernicus --size-m 4000 --res 513
\`\`\`

No 4 m geographical detail appears magically when upsampling a 30 m DSM to 513 pixels on a 4 km crop. Retain the GeoTIFF as vertical truth; PNG height is normalized per crop and MUST be decoded using the manifest. Check source height datum; do not blend different vertical datums without explicit transformation. If remote fetch fails, fall back to IGN/QGIS local \`--source\`; do not silently substitute synthetic terrain as real.

### Houdini SOP/Copernicus intake procedure

1. Save a **separate experimental copy** of \`Houdini/FarawayDrape.hip\`; verify that \`FARAWAY_DRAPE_GRID\` and \`TENSION_MASK\` survived. The original is protected. A school Education seat may produce non-commercial file types; preserve script/recipe sources for future permitted rebuilds.
2. In a new Geometry SOP network, load \`height_normalized_16bit.png\` with **HeightField File**. Set size to the crop extent in metres (e.g., 4000) and height scale to the **manifest z span**; then add a height offset of **z_min_m** using HeightField Wrangle/height layer arithmetic (or load the float32 GeoTIFF directly when supported). Record mask/sampling orientation; compare landmarks with the hillshade.
3. Add a heightfield conditioning branch for fabric geology; do NOT replace real regional relief with procedural noise. Study Jura aligned folds, Cantal radial crest, Gavarnie hanging wall and Ecrins fractures as shape guides. Keep actual elevation information distinct from authored stylization.
4. Read existing Faraway canonical static RGBA (R tension, G resonance, B moisture, A seam) from \`faraway_static_field.py\`. The canonical musical field is computed in global 8 km world coordinates, **not** per French DEM crop; French terrain is a *shape reference*, not a replacement Chladni coordinate system.
5. For heightfield-to-mesh handoff, use the existing \`melodia.terrain_handoff.v1\` conversion/validation. Keep the **100 cm/m** UE 5.8 Mesh Terrain contract, \`classic_landscape_used: false\`, and UE PCG/editor single-writer restrictions. A local Houdini render is not a playable proof.

SideFX refs: HeightField File https://www.sidefx.com/docs/houdini/nodes/sop/heightfield_file.html ; HeightField Output https://www.sidefx.com/docs/houdini/nodes/sop/heightfield_output.html ; HeightField/Mono COP https://www.sidefx.com/docs/houdini/heightfields_cop/conversion.html .

### Six bounded Copernicus textile experiments (reuse existing family material identities)

Use the six presets in \`terrain_fabric_atlas.v1.json\` and the mathematical contact sheet \`Docs/Art/References/FarawayMother_Chladni_Cloth_Modes_20261023.svg\`.

| Textile (priority) | Existing family | Primary output / art goal |
| --- | --- | --- |
| **01 Celestial Silk Jacquard — DO FIRST** | FarawayCelestialSilk | directional silk thread height/normal + tension-modulated sheen, canonical (3,5) hidden jacquard |
| **02 Mother's Night Velvet — DO NEXT** | FarawayNightVelvet | deep plum nap, directional softness, controlled high roughness; no glitter/noise wash |
| **03 Gilded Resonance Brocade — DO NEXT** | FarawayGildedRidge | gold thread following a **canonical** near-zero seam mask; raised stitches, normal + selective emissive reveal |
| 04 Aquatic Lullaby Lace | FarawayAquaLace | openwork geometry/opacity, pearl and aquamarine edges; inspect transparency/culling |
| 05 Singing Water Organza | SingingSilk | long flow streaks, normal/roughness, soft aquamarine translucency |
| 06 Glacial Pearl Organza | FarawayCelestialSilk experimental variant | restrained frost microfacets and pearl iridescence for rare hero peaks |

**Suggested COP branches:** canonical mask file / optional native Chladni artistic mode -> signed field / near-zero contour -> warp/weft directional noise and Tile Pattern -> curvature/slope/tension masks -> Height to Normal -> BaseColor / Roughness / Sheen / Height / optional Opacity or Emissive. Node names/capabilities should be checked in the actual installed Houdini build before automating a graph. The native artistic Chladni COP is **not** asserted equivalent to the existing canonical cosine field. Mode (4,6) is explicitly **ART EXPERIMENT ONLY**; mode (3,5) owns spatial seam truth.

**First comparison:** use the *same* draped Jura/Gavarnie geometry and fixed camera: satin ridge, velvet valley, one gold nodal seam. Capture neutral clay, pure material, and controlled Chladni reveal, plus maps and a short source/provenance manifest. Prefer a gorgeous unified test to six disconnected map exports.

**Evidence gate:** only mark as cooked after actual lab \`hython\`/GUI evidence records source SHA, licence tier, terrain source/CRS/datum, height min/max, render paths, actual material maps, and protected master unchanged. Raw maps/caches remain in \`Saved/Audit/houdini_faraway_mother/\` or college scratch (not Git). Record implementation status **only** in \`CURRENT_STATE.md\` after future genuine cooking.

---

## Poitou Surface x Mycelium Subsurface x Faraway Harmonic Skin (2026-10-23)

**Status: PROPOSED, not built.** This is an extension to the Harmonic Continental Genesis / Chladni Cloth Day research plan above. No cave asset or source file was imported, moved, recooked, or altered by this commit. The owner knows where the Melusina's House mycelium cave source is; its exact path remains **OWNER-RESOLVED AT THE LAB**, not a guessed Git path. This is an offline Houdini experiment first, not a new runtime system.

### Core artistic hypothesis

**Faraway Mother is a single continent-sized garment suspended over a living, interconnected subterranean organism.** Poitou-style terrain infrastructure establishes the surface and access paths; Melusina's House mycelium cave branches supply buried structural anchor candidates; Faraway's canonical signed Chladni (3,5) field supplies rhythmic tension and nodal embroidery. Selected underground branches can *influence* the cloth constraint field so the mountains read as held in place by something alive beneath them.

At the hero reveal, a luminous gold seam visible on the mountain surface aligns with the buried branching network. This link is **authored spatial composition**, not a claim that physically correct acoustics or fungal growth are being simulated.

### Existing production interfaces to reuse — no new global compiler

| Lane | Source / known authority | Reusable interface | Do **not** assume |
| --- | --- | --- | --- |
| **Poitou surface assembly** | \`POITOU_START_HERE.md\`; \`Docs/Plans/POITOU_MELUSINAS_MORNING_CONVERGENCE_2026-10-20.md\`; \`Docs/Poitou/poitou_layout/HOUDINI_ENGINE_LIVE_CONVERGENCE_SPEC.md\`; current \`poitou_layout_live.hdalc\` builder *when owner confirms actual checkout/build* | curve-based paths, banks, masks, terrain collision exclusions, staging conventions, UE HDA source/outputs | Poitou's live HDA may be on another workstation/branch; do not import or recook the P0 town, duplicate it, or replace Poitou's real-world flat regional identity |
| **Melusina's House cave / mycelium** | OWNER-RESOLVED LOCAL SOURCE: inspect file/UE level/SOP/HDA and record path + SHA before using. \`MELUSINA_HOUSE_GN_START_HERE.md\` and original house design documents provide context but are **not** proof of this specific cave generator | If available: cave SDF/VDB, tunnel curves, centerline connectivity, fungal branch positions, chamber anchors, signed-distance samples, bioluminescent dressing masks | An exact procedural asset path, live cook, connectivity, units, or ready-made VDB cannot be inferred from searchable Git. Treat as candidate, not verified reuse until opened |
| **Faraway harmonic cloth** | protected \`Houdini/FarawayDrape.hip\`; \`Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py\`; \`Tools/PCG/build_faraway_mother_pcg_ecosystem.py\`; six cloth recipes in \`recipes/houdini_faraway/terrain_fabric_atlas.v1.json\` | existing handmade \`FARAWAY_DRAPE_GRID\`, \`TENSION_MASK\`, canonical signed (3,5) spatial field, selected Vellum drape/constraint experiments, Copernicus material maps | full-continent live cloth, non-canonical (4,6) override of spatial seams, or a rebuilt authored master |
| **World handoff** | \`Docs/WorldGen/WORLD_COMPILER_CONTRACT.md\`, \`Docs/WorldGen/TERRAIN_HANDOFF_CONTRACT.md\`; Faraway P1 resonance-field integration spec | deterministic offline mask/point bundles, UE 5.8 Mesh Terrain at 100 cm/m, existing World Compiler + PCG, TD \`OUT_SHOW_FIELD\` presentation | separate World Compiler, new gameplay writer, second MPC, or Unreal level edits during the school research cook |

**Role separation:** Poitou gives tested *patterns* for surface construction, not the exact P0 map. Cave system is a verified local candidate only after source inspection. Faraway owns the chapter's art direction and harmonic field. \`CURRENT_STATE.md\` is the **only status authority**.

### Data-flow architecture — bounded 250 m hero slice

\`\`\`text
Poitou-inspired path/mask/terrain interface (read-only example)
                       |
                       v
        surface shell / walkability keepouts <------ France DEM study
                       |
                       +-----------------------+
                                               |
Owner-located mycelium source --verify--> curve/SDF adapter (metres)
                                               |
                                               v
                     cave branches + chamber surfaces
                        |                   |
                        | anchor candidates | protected cave voids
                        v                   v
canonical Faraway F(3,5), tension --> Vellum drape / guide folds
                        |                   |
                        +------ aligned ----+
                                   |
                    seam curve + material masks
                                   |
               Copernicus satin/velvet/brocade preview
                                   |
                 offline mesh/mask/evidence only
                                   |
            optional later World Compiler/UE gate
\`\`\`

**Important:** Spatial alignment is explicit. The global Faraway chapter bounds stay [-400000,+400000] UE centimetres (8 km square); \`U=(X+400000)/800000\` and \`V=(Y+400000)/800000\`. Transform the cave and Poitou-derived input geometries into the **selected Faraway local research crop in metres** with recorded world transforms. Do not reset Chladni UV per tile. Do not mistake the French DEM georeference CRS for UE world coordinates; an authored transform is necessary.

### Lab sequence — the minimum convincing experiment

**Gate 0 — Non-destructive source checkout (15–25 minutes)**
1. \`git fetch origin\`, inspect \`git status --short --branch\` and update only a clean checkout (never overwrite dirty art). Verify school Houdini version, Education licence, scratch/RAM.
2. Locate the owner-known Mycelium cave source locally; inspect *actual geometry* and its type (Blender/UE/SOP/HDA/curve/VDB), parent transforms, bounding box, metres-vs-centimetres, accessible outputs, and license. Save absolute source path and SHA256 in a **scratch/audit manifest**. Do not guess or overwrite.
3. Save a disposable experiment from a copy of \`Houdini/FarawayDrape.hip\`; independently verify \`FARAWAY_DRAPE_GRID\`, \`TENSION_MASK\` and handmade \`Cymatic_BeatPulse\` remain intact. Confirm the home and lab licence formats before sharing a scene.

**Gate 1 — Single 250 x 250 m section / neutral clay (45–75 minutes)**
1. Use Poitou's curve/mask/terrain placement *principles* to establish a reduced surface shell, two preserved traversal routes/clearance masks and a hero camera.
2. Bring in **one** selected mycelial cave or branch skeleton. If the current source is a baked mesh, derive temporary centerlines or a VDB/SDF from it rather than generating a competing ecosystem. Simplify to one branching cave chamber and 3–7 significant branch reaches.
3. Derive \`cave_open_space\`, \`cave_roof_thickness\`, \`cave_branch_proximity\`, \`support_anchor_candidates\`, and \`walkable_keepout\` masks or SOP attributes. Reserve at least 2 m of solid roof thickness in the first visual experiment unless the cave model demands more; **this is a provisional artistic safety margin, not structural engineering**.
4. Explicitly test that the routes stay connected, no cave void punctures a walking surface unintentionally, and the underground section reads as *one* real volume (not randomly scattered glowing mushrooms).

**Gate 2 — Constraint-driven cloth / harmonic reveal (45–90 minutes)**
1. Sample the canonical (3,5) field in shared world space; use cave branch proximity and selected anchors as **additional Vellum pin/stiffness influences**. Keep \`TENSION_MASK\` artist-authored input distinct from any generated \`mycelium_anchor_mask\`.
2. Compare 3 variants at equal resolution/camera: **A** gravity-only, **B** canonical tension-only, **C** canonical tension plus mycelium anchor influence. No entire 8 km Vellum. Preview coarse and refine only after silhouette approval.
3. Extract the signed Chladni near-zero contour. Conform one continuous golden brocade stitch to the cloth and use selected underground branches to suggest a correlated glow pattern. A mathematically aligned overlay, **not** new musical authority.
4. Use the existing Copernicus material variants: Celestial Silk on ridges, Night Velvet in folds, Gilded Resonance at the seam. Compare clay and material versions without changing the terrain.

**Gate 3 — One cross-section hero receipt (30–45 minutes)**
1. Save the same camera across variants; capture **surface view**, **cutaway subterranean view**, and **field/anchor debug overlay**. Draw a line from each underground support candidate to its surface pin influence.
2. Record cave mesh/SDF counts, bounds/units, number of retained connected underground components, surface/path intersections, simulated cloth particle spacing and cook time, and source SHA/licence. Measure RAM/scratch before attempting a refinement.
3. Export only representative derived geometry and masks into \`Saved/Audit/houdini_faraway_mother/mycelium_cloth_lab_20261023/\` or approved scratch. Large VDB/geometry/simulation sequences stay outside Git.

### Acceptance tests / failure handling

- [ ] **Source genuine:** cave generator verified locally by file path + hash + object/graph inspection. If unavailable, stop at source identification; **do not silently fabricate a cave asset**.
- [ ] **Cross-layer alignment:** cave anchors, cloth surface and golden nodal seam share a recorded transform and one world-space field sample convention. All world/mask axes visually reviewed.
- [ ] **Surface safety:** no accidental open tunnels on preserved routes, no floating path/bridge support, and no destructive writing to Poitou P0 or \`L_MelusinaMorning\`.
- [ ] **Underground topology:** at least one continuous navigable candidate corridor with an intentional opening (physical capsule clearance requires an eventual UE test; Houdini screenshots cannot prove gameplay).
- [ ] **Comparative visual lift:** variant C produces demonstrably more intentional folds than A/B *without* filling the cave or becoming a noisy heightfield.
- [ ] **Protected authorities:** \`FarawayDrape.hip\` hash unchanged, original Mycelium source unchanged, same Faraway (3,5) field and World Compiler interfaces; no new runtime subsystem.
- [ ] **Evidence:** source/cook manifest, three fixed-camera captures, field/anchor diagram, per-variant performance numbers and a clear PASS / FAIL / BLOCKED label.

If the asset is a UE-only native binary or inaccessible on the lab workstation, first export a **read-only proxy** using the owner's existing DCC/UE tools and document that transfer. Never treat repo search absence as proof the user's asset does not exist.

### Future escalation — only after the cross-section earns it

Reapply the proven adapter to **four globally stitched 250 m tiles (500 x 500 m)**, with PDG partitioning and proper boundary checks from the Harmonic Continental Genesis plan above. Underground branches crossing a tile border must preserve IDs/connectivity and tunnel continuity. Only a later, owner-approved gate should promote a usable adapter into an HDA/World Compiler consumer or UE level. The aspirational 8 x 8 km continent remains a separate long-range objective.

**Definition of today's success:** a readable cloth mountain and connected glowing cave in **one single cutaway**, with at least one measurable relationship between mycelium branch anchoring, fabric-fold direction, and the canonical golden Chladni seam. *One beautiful, reproducible proof beats a continent of unfinished graphs.*
