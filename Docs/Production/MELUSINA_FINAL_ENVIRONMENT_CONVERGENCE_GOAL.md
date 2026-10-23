# Melusina Environment Convergence & Architectural Standardization Specification
**Target Milestone**: Tonight's Final Convergence Deployment (`/goal`)  
**Domain**: Procedural World Building, Modular Architectural Taxonomy, Unreal Engine 5.8 & Houdini Engine Integration  
**Authority**: Jev System Decision Audit (`jev-1.13.0`), Monolith Engine Live Runtime, World Compiler v2  
**Active Project**: [EnvironmentPortfolio](file:///c:/EnvironmentPortfolio), [BS_GodFile](file:///c:/EnvironmentPortfolio/BS_GodFile)  

---

## Executive Summary & Engineering Objective

This specification establishes the definitive architectural, procedural, and collision convergence pipeline for the Melusina environment suite, drawing directly from the modular world-building methodologies developed by Infold Games (*Infinity Nikki*). 

The primary objectives achieved tonight are:
1. **Infold/Nikki Architectural Deconstruction**: Establishing a metric-standardized, socket-driven bay taxonomy for Parisian/Haussmannian and Poitou Romanesque architectural variants that seamlessly scales from individual village cottages to monumental cathedral ruins.
2. **Procedural World Compiler & Heatmap Convergence**: Fully integrating the Chladni acoustic resonance fields into dual-tier spatial representations—compiled sparse vector point bundles and 1009×1009 16-bit raster heatmaps for clearance, walkability, vegetation density, and audio submix crossfading.
3. **Zero-Proxy, 100% Nanite Complex Collision Standard**: Eliminating all approximate simplified collision hulls, floating bounding boxes, and proxy meshes. Enforcing `ECollisionTraceFlag::CTF_UseComplexAsSimple` per-poly raytracing against high-density Nanite geometry with ground-probe line-trace verification.
4. **Live Houdini Engine & PCG Iteration Loop**: Authoring and registering `HDA_Poitou_AbbeyBuilder_1.0.hda` for live SessionSync in Unreal Engine 5.8, enabling interactive parametric decay, bay rhythm tuning, and structural scaling.
5. **Canonical Level Staging**: Staging the 4 canonical Melusina environments (`L_Poitou_v2`, `L_MelusinaMorning`, `L_KaleidoNave`, `L_ZenForestTest`) with verified daylight PBR lighting, grounded landscape geometry, and zero-slop lookbook plate curation.

---

## 1. Architectural System Breakdown: Infold (*Infinity Nikki*) Modular Methodology

### 1.1 The Infold Philosophy: High-Density Stylized Realism
Infold Games (*Infinity Nikki*) achieves its world-building aesthetic by refusing the traditional compromise between stylized fairy-tale whimsy and authentic structural logic. Rather than cartoonishly warping architecture or pasting disembodied musical symbols across buildings, their pipeline adheres to rigorous real-world classical architectural treatises (Vignola, Durand, Haussmann) while exaggerating silhouette readability, micro-detail crispness, and light-catching surface relief.

The core rule: **The architectural rhythm IS the music.**

> **Governing meter (single source of truth — supersedes any earlier statement of this rule
> anywhere in the repo, including the two-line version this section used to carry).**
>
> | Unit | Value | Musical meaning |
> |---|---|---|
> | Grid | **0.6 m** | 1 beat @ 128 BPM, 4/4 — `wall_thickness` 1.8 m = 3 grid units |
> | Bar / bay | **2.4 m** | 1 bar of 4/4 @ 128 BPM (4 beats) — `bay_length` = 2.4, `wall_height` 14.4 m = 6 bays |
> | Long module | 3.6 m | 6 beats = 1.5 bars of 4/4 = 2 bars of 3/4 (same beat length) |
> | Tempo | **128 BPM, 4/4** | 1 beat = 0.469 s, 1 bar = 1.875 s, walk = 1.28 m/s |
>
> The earlier "2.4 m = allegro 3/4 / 3.6 m = andante 4/4" phrasing was internally inconsistent
> (2.4 : 3.6 = 2 : 3, which is 4 beats : 6 beats, not 3 : 4) and contradicted the Poitou build
> grid, which fixes one tempo and one speed. **One tempo, one grid, one bar — 0.6 m / 2.4 m /
> 128 BPM 4/4.** This is the meter `Recipes/melodia_poitou_parisian_v2.json` (`bpm: 128`),
> `Docs/Poitou/current_state.md` ("Grid 0.6 m, bar = 2.4 m, 128 BPM"), the AE animation layer
> (`Tools/Poitou/ae_first_day_animation_layer.md`, "1 bar = 1.875 s", `A_MEL_Walk_PianoStep_128`)
> and the AbbeyBuilder HDA (`bay_length` 2.4 m) already assume.
>
> **OPEN — owner decision (one number).** The Maillezais canon dimensions do not tile on the
> bar: `abbey_len` 105 m / 2.4 = **43.75 bays**, `abbey_wid` 32 m / 2.4 = **13.33 bays**.
> Either the dimension wins (105 → 105.6 m = 44 bays, 32 → 33.6 m = 14 bays) or the bar wins
> (43 × 2.4 = 103.2 m, 13 × 2.4 = 31.2 m). "Zero slop" (§3) forbids a fractional bay count,
> so this cannot stay open while geometry is generated.

- Balcony ironwork incorporates wave-harmonic frequency curves into classical French rocaille and art-nouveau foliate tracery.
- Limestone cornices mirror acoustic harmonic node profiles derived from physical Chladni sound-figure experiments.

```
       ┌────────────────────────────────────────────────────────┐
       │   ATTIC & MANSARD (Combles) - Zinc/Slate + Lucarnes    │  3.0m
       ├────────────────────────────────────────────────────────┤
       │   TIER 4 (Quatrième Étage) - Standard Bay Windows      │  3.2m
       ├────────────────────────────────────────────────────────┤
       │   TIER 3 (Troisième Étage) - Juliette Balconies        │  3.2m
       ├────────────────────────────────────────────────────────┤
       │   PIANO NOBILE (Deuxième Étage) - Balcon Filant 0.8m    │  3.6m
       ├────────────────────────────────────────────────────────┤
       │   BASE & ENTRESOL - Rusticated Limestone + Portals     │  4.8m
       └────────────────────────────────────────────────────────┘
       ▲                      ▲                       ▲
       │◀────── 2.4m ────────▶│◀────── 3.6m ─────────▶│ (Bay Rhythm)
```

### 1.2 The 4-Tier Vertical Hierarchy (Haussmannian & Romanesque Sockets)

> **Status: TARGET socket contract, not implemented.** The AbbeyBuilder HDA exposes no
> per-tier datum controls. Its real vertical controls are `wall_height` (14.4 m = 6 bays) and
> `wall_thickness` (1.8 m = 3 grid units) — a single mass, not four stacked tiers. The tier
> datums below are the design intent the socket system must eventually express; nothing in
> the current HDA realises them, and no tier should be described as built until it is.

Every architectural structure in the Melusina universe—from urban Parisian residential blocks to rural Poitou monastic outbuildings—is assembled using a strict 4-tier vertical socket contract:

#### Tier 1: Ground Base & Entresol (4.8m Datum)
- **Clearance**: 3.2m ground floor + 1.6m mezzanine / entresol.
- **Materiality**: Rusticated ashlar limestone (`pierre de taille` from Saint-Maximin or Poitou Chauvigny quarries) with deep horizontal rustication grooves (`refends`).
- **Variants**:
  - `Base_01_ArchedBoutique`: Semicircular ashlar archway with recessed timber and brass storefronts.
  - `Base_02_CarriagePortail`: Monumental segmental arch (`porte-cochère`) flanked by twin stone guard-stones (`chasse-roues`).
  - `Base_03_BlindArcade_Poitou`: Romanesque blind arcade with paired limestone colonnettes, carved animalier capitals, and water-weathered plinths.
- **Socket Contract**:
  - Bottom: `Socket_Foundation_Snap` (Ground-probe line-trace offset).
  - Top: `Socket_Base_To_Piano` (Horizontal drip molding datum at +480 cm).

#### Tier 2: Piano Nobile (3.6m Datum)
- **Clearance**: 3.6m ceiling height.
- **Distinction**: The ceremonial grand floor. Features the highest ceilings, most ornate window entablatures (triangular pediments, segmental pediments, or carved acanthus brackets), and a continuous running balcony.
- **Balcon Filant**: Continuous cast-iron or wrought-iron railing with ornate scrollwork, projecting 80 cm from the masonry line on carved stone corbels.
- **Acoustic Integration**: Balustrade ironwork profiles are generated directly from standing acoustic wave frequencies, forming harmonic crests and nodes across each 2.4m bay.
- **Socket Contract**:
  - Bottom: `Socket_Base_To_Piano` (Snaps to Tier 1 datum).
  - Top: `Socket_Piano_To_Mid` (Stringcourse molding datum at +840 cm).

#### Tier 3: Intermediate Floors (Étages Courants) (3.2m Datum per Story)
- **Clearance**: 3.2m per floor (typically 1 to 3 stacked stories).
- **Distinction**: Decreasing ornamental density and shallower window reveals as height increases. Replaces continuous balconies with individual Juliette balconies (`garde-corps`).
- **Variants**:
  - `Mid_01_SingleBay_Window`: Clean dressed stone jambs with molded architrave.
  - `Mid_02_DoubleBay_Pilaster`: Paired window bay partitioned by a Corinthian or composite pilaster.
  - `Mid_03_Ruin_PorousStone`: Weathered abbey wall variant with partially collapsed masonry revealing core rubble work (`opus caementicium`).
- **Socket Contract**:
  - Self-stackable: `Socket_Mid_In` to `Socket_Mid_Out` at +320 cm intervals.

#### Tier 4: Attic & Mansard Roof (Combles & Lucarnes) (3.0m - 4.5m Datum)
- **Clearance**: 3.0m internal ceiling height within a 60° to 75° pitched roof profile.
- **Materiality**: Prefabricated standing-seam Parisian zinc plates (`zinc laminé`) or dark grey Angers slate tiles.
- **Variants**:
  - `Roof_01_Mansard_Straight`: Classic François Mansart double-pitched roof.
  - `Roof_02_Mansard_ZincLucarne`: Features stamped zinc dormers with pediment caps and floral acroteria.
  - `Roof_03_Poitou_Tower_Spire`: Conical or octagonal limestone shingle spires characteristic of Poitou Romanesque lantern towers (e.g., Saint-Pierre de Chauvigny).
- **Acoustic Utility**: Chimney stacks are hollow, tuned acoustic resonators (`tuyaux d'orgue`) with tuned reed vents that produce low-frequency harmonic hums during high-altitude wind events.

---

## 2. World Compiler & Spatial Heatmap Integration

The World Compiler (`Tools/world_compiler.py`) serves as the Single Source of Truth for spatial generation across all Melusina levels. For `melusina_poitou_parisian_v2`, the compiler generates both sparse vector point tables and dense 16-bit 1009×1009 raster heatmaps.

```
       ┌────────────────────────────────────────────────────────┐
       │   World Compiler Recipe (recipes/melusina_poitou_...)  │
       │   - Identity: liquid_cathedral | Mode: dorian | BPM: 128│
       └───────────────────────────┬────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
       ┌────────────────────────┐    ┌────────────────────────┐
       │ Dense Spatial Heatmaps │    │ Compiled Point Bundles │
       │ (1009x1009 16-bit PNG) │    │ (SQLite / JSON Tables) │
       ├────────────────────────┤    ├────────────────────────┤
       │ 1. Walkability Map     │    │ - 2,793 Ecology Points │
       │ 2. Keepout Clearance   │    │ - 5 Movement Bands     │
       │ 3. Flora Density       │    │ - Musical Bay Anchors  │
       │ 4. Audio Crossfade     │    │ - Structural Grid Data │
       └────────────┬───────────┘    └────────────┬───────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │       Unreal Engine 5.8 Runtime / PCG Graph            │
       │  - Nanite Complex Collision Geometry (No Proxies)      │
       │  - Ground-Probe Line-Trace Actor Snapping              │
       │  - Dynamic Audio Submix Volume Driving                 │
       └────────────────────────────────────────────────────────┘
```

### 2.1 Baked Heatmap Specifications (Saved/WorldCompiler/melusina_poitou_parisian_v2_3900/heatmaps/)

1. **Walkability Heatmap (`heatmap_walkability.png`)**:
   - **Resolution**: 1009 × 1009 pixels (16-bit grayscale, normalized 0..65535).
   - **Spatial Scale**: 200m × 200m total world footprint centered on `(X=87834, Y=14200)`.
   - **Data Semantic**: 
     - `1.0 (65535)`: Dedicated primary thoroughfares, nave center aisles, paved stone quays, and flagstone courtyard plazas.
     - `0.6 (39321)`: Secondary beaten-earth trails, lawn margins, and ruined side ambulatories.
     - `0.0 (0)`: Steep water embankments, deep marsh trenches, and structural stone footings.
   - **Gameplay Function**: PCG uses this map to restrict player character pathing, AI companion following vectors, and interactive quest item placement.

2. **Clearance / Hard Keepout Heatmap (`heatmap_clearance.png`)**:
   - **Data Semantic**:
     - `0.0 (0)`: Strict exclusion zone. Enforces zero foliage, zero clutter debris, and zero dynamic prop spawning within 15 meters of the High Altar sanctuary, ancient wellheads, lock gate pivots, and primary portal thresholds.
     - `1.0 (65535)`: Free scattering zone for procedural debris, weeds, and wild grass.

3. **Flora Density Harmonic Field (`heatmap_flora_density.png`)**:
   - **Mathematical Basis**: 2D Chladni standing-wave nodal equation evaluated at 128 BPM Dorian mode harmonics:
     $$\Psi(x, y) = a \cos\left(\frac{n \pi x}{L}\right) \cos\left(\frac{m \pi y}{L}\right) - b \cos\left(\frac{m \pi x}{L}\right) \cos\left(\frac{n \pi y}{L}\right)$$
     with radial Gaussian falloff along the Grand Viaduct axis.
   - **Species Distribution**:
     - High nodal intensity ($>0.7$): Pollarded Ash (*Fraxinus excelsior* / Têtards), European Gorse (*Ulex europaeus*).
     - Mid nodal intensity ($0.3 - 0.7$): Sea Thrift (*Armeria maritima*), wild hydrangeas, maritime bent grass (*Calamagrostis*).
     - Low nodal intensity ($<0.3$): Fine river moss (*Bryophyta*) adhering to wet limestone foundations.

4. **Audio Crossfade Attenuation Map (`heatmap_audio_crossfade.png`)**:
   - **Data Semantic**: Multichannel submix weighting.
     - Inner Abbey Sanctuary ($R=255$): 100% Cathedral Organ Resonance Submix, 4.2-second liturgical reverb impulse response.
     - Marsh Canal Transition ($G=255$): Water lap, reeds rustling, wind through pollard branches.
     - Village Square / Quay ($B=255$): Warm acoustic bells, distant barque ripples, dry stone ambient reflection.

---

## 3. Real Walkable Levels: The Zero-Proxy, 100% Nanite Collision Standard

### 3.1 The Failure Mode of Simplified Colliders
In classical AAA production, artists frequently build low-poly collision boxes, capsules, or 12-sided convex hulls to optimize CPU physics. For intricate Romanesque ruins, spiral stairs, Gothic tracery, and collapsed masonry, this creates catastrophic visual-physical desynchronization:
- Nikki's feet float 15–25 cm in mid-air over recessed stone carvings.
- Dresses and hair physics clip through thin tracery cusps or collide invisibly against empty air between open arches.
- Ruined archways that visually appear 3.5 meters high block the player at 2.0 meters due to coarse bounding box corners.

### 3.2 The Nanite Complex Collision Solution
In Unreal Engine 5.8 with Nanite-enabled static meshes, the engine can evaluate raycasts and rigid-body sweeps directly against the Nanite streaming geometry or high-density render triangle meshes:

1. **Complex Collision Flag Enforcement**:
   Every architectural mesh (`SM_Maillezais_*`, `SM_Abbey_*`, `SM_Parisian_*`) must declare:
   ```cpp
   // Unreal Engine C++ / Core Reflection
   BodyInstance.SetCollisionComplexity(ECollisionTraceFlag::CTF_UseComplexAsSimple);
   ```
   *Verified in Live Monolith MCP Audit*:
   - `SM_Maillezais_BrokenArch`: `collision_complexity: "UseComplexAsSimple"`, `has_per_poly_collision: true`.
   - `SM_Maillezais_ButtressStub`: `collision_complexity: "UseComplexAsSimple"`, `has_per_poly_collision: true`.
   - `SM_Maillezais_CrumbledWall`: `collision_complexity: "UseComplexAsSimple"`, `has_per_poly_collision: true`.

2. **Ground-Probe Snapping Protocol**:
   All procedurally generated actors must never be placed using bounding box centers or fixed horizontal planes. They are anchored via dynamic vertical line-tracing:
   - Line trace cast from `(X, Y, Z + 10000)` downward to `(X, Y, Z - 10000)`.
   - Channel: `ECC_WorldStatic` (filtering explicitly for Landscape and complex foundation geometry).
   - Trace Hit Result extracts exact landscape elevation (e.g. Z=2011 at nave entrance descending to Z=1755 at the marsh canal).
   - Actor root is snapped directly to `Hit.ImpactPoint.Z`, with normal alignment to landscape slope for natural settled bedding.

3. **Stale Collision Geometry Purge**:
   - Stale procedural collision boxes and historical HDA bounding shells (such as the legacy `HoudiniAssetActor_16` shelf at Z=4750) are systematically detected and purged from the level hierarchy, preventing ghost collisions.

---

## 4. Live Houdini Engine & HDA Convergence Architecture

> **There are two HDAs in this pipeline and they do different jobs.** This section previously
> described one asset ("the AbbeyBuilder") as though it generated the abbey *and* the terrain.
> It does not. Read this before changing any HDA parameter.

| | `poitou_layout_live` | `HDA_Poitou_AbbeyBuilder_1.0` |
|---|---|---|
| Job | **Layout.** Terrain, canals, ditches, islands, lanes, rise, horizon bands, water, mist, and the abbey's *placement* | **Shell.** The abbey ruin mass itself |
| Asset | `hda/` + `Saved/Audit/PoitouConvergence_20261020/poitou_layout_live_before_ign_20261020_224959.hdalc` | `hda/HDA_Poitou_AbbeyBuilder_1.0.hda` (16,754 B) + `Content/HDA/` mirror |
| Builder | `Tools/Poitou/build_poitou_hda.py` | not built by any repo tool (added by `ada95ab74`) |
| Key abbey controls | `abbey_len` 105, `abbey_wid` 32, `abbey_rot` 20 (metres / degrees) | `bay_count` 8, `bay_length` 2.4 → an **8-bay, 19.2 m** shell module |

**Do not author against the parameter table this section used to carry.** The names
`nave_length`, `nave_width`, `bay_spacing`, `decay_amount`, `broken_arch_seed`,
`buttress_count`, `limestone_erosion`, `tracery_style` and `export_unreal_nanite` **do not
exist** in the asset. Two of the numbers were real but attached to the wrong names (`0.45`
is `decay_intensity`, not `decay_amount`; `8` is `bay_count`, not `buttress_count`), and the
`decay_seed` default is 1337, not 42.

### 4.1 `HDA_Poitou_AbbeyBuilder_1.0` — real parameter contract

Read from the asset itself with Houdini 22.0.368 `hython` on 2026-10-21
(`hou.hda.definitionsInFile` → `parmTemplateGroup`), not from documentation:

| Parameter | Type | Label | Default | Note |
|---|---|---|---|---|
| `preview_mode` | Toggle | Preview Mode (<50ms) | 0 | fast cook variant |
| `bay_count` | Int | Bay Count | 8 | × `bay_length` = 19.2 m nave |
| `bay_length` | Float | Bay Length (m) | **2.4** | = 1 bar of 4/4 @ 128 BPM (§1.1) |
| `wall_height` | Float | Wall Height (m) | **14.4** | = 6 bays |
| `wall_thickness` | Float | Wall Thickness (m) | 1.8 | = 3 grid units (0.6 m) |
| `window_style` | Menu | Window Style | 1 | menu, not an int range |
| `buttress_tiers` | Int | Buttress Tiers | 3 | |
| `decay_intensity` | Float | Decay Intensity | 0.45 | procedural ruin slider |
| `decay_seed` | Int | Decay Seed | 1337 | |

The node type is `HDA_Poitou_AbbeyBuilder`, description *"Poitou Maillezais Abbey Ruin
Builder (BS_GodFile UE5.8)"*. The asset's own documented stat (512 points / 336 polygons) is
consistent with an 8-bay shell module, not with a 105 m cathedral — the 105 m / 32 m
Maillezais dimensions are the *layout* HDA's `abbey_len` / `abbey_wid`, and the two must be
told apart.

### 4.1a `poitou_layout_live` — real parameter contract

Read live from the running Houdini Engine session, not from the recipe
(`Saved/Audit/PoitouConvergence_20261020/live_parameters_before.txt`,
`live_requested_parameters.json`, 2026-10-20). 61 exposed parameters. The ones that matter
for the canon: `abbey_len` 105.0 / `abbey_wid` 32.0 / `abbey_rot` 20.0, `bank_drop` 0.5,
`ditch_spacing` 17.5 / `ditch_warp` 12.0 / `ditch_halfw` 1.2 / `ditch_ymax` 420.0 /
`ditch_depth` 0.8, `ue_canal_width` 6.0 / `ue_canal_depth` 1.2, `lane_spacing` 12.0,
`shell_cluster_radius` 21.0, `rise_centerx` 830 / `rise_centery` 860 / `rise_radius` 140 /
`rise_height` 20 / `rise_plateau` 50, `iles_count` 4 / `iles_seed` 3 / `iles_radius` 70 /
`iles_hmin` 4 / `iles_hmax` 12, `band0_dist` 1300 / `band1_dist` 1900 / `band2_dist` 2600 /
`band_spacing` 9 / `band_gap` 0.45, `spire_dist` 2300 / `spire_angle` 35 / `spire_height` 40 /
`spire_count` 2, `mist_strength` 1.0, `water_res` 2.0, `water_drop` 0.25, `skirt_extent` 6000,
`swell_amp` 10 / `swell_ramp` 1500 / `swell_freq` 0.0012, `seed` 1. Toggles: `full_res`,
`nikki_layers`, `ign_calib`, `instance_preview`, `use_ue_input0/1`, `real_meshes`,
`snap_canals`, `horizon_on`. Strings: `landscape_material`, `layerinfo_dir`,
`water_material`, `skirt_material`. Ints: `iles_count`, `radial_lanes` 5, `spire_count`.

> **Tempo is a separate axis.** The layout's `bpm` is 128 (`Recipes/melodia_poitou_parisian_v2.json`);
> every other world recipe is 96. `UMelodiaMusicClockSubsystem` is documented as *global tempo,
> per-zone key* — confirm the clock's tempo authority before authoring any 128 BPM-locked clip
> (`A_MEL_Walk_PianoStep_128`), because a clip authored against the wrong tempo is a rewrite.

### 4.2 Authoring and launching

- **Houdini Engine (in-editor):** `Houdini Engine > Restart Session` if the session is dead.
  `Content/HDA/MelodiaRoomShell_1.0.hda` is the other live in-editor HDA and is a *different*
  asset from the Poitou pair above.
- **HDA authoring source of record:** `C:\Users\froma\agent-tools\poitou_houdini\`
  (outside the repo) plus the in-repo `Tools/Poitou/build_poitou_hda.py`. **These two carry
  different parameter sets** — the in-repo builder uses `abbey_len`/`abbey_wid`/`bank_drop`/
  `ditch_*`/`band*`/`spire_*`; treat the repo copy as the source of truth and the external
  folder as a scratch workspace until they are reconciled.
- **Hython compiler:** SideFX Houdini 22.0.368 (`hython.exe`).

---

## 5. Canonical Multi-Level Staging & Lookbook Verification

> **Corrected 2026-10-21. This section previously claimed all 4 canonical environments were
> "staged, verified in live Unreal Engine 5.8, lighting-tuned, and registered into the public
> lookbook portfolio" with zero-slop plates. That claim was false and is replaced below by
> what is actually true. Evidence: `Saved/Audit/PoitouConvergence_20261020/plate_audit.json`
> (the repo's own `Tools/audit_showcase_plates.py`, run against the published plates).

**Live level set (2026-10-21, commit `46669de7b`):** `L_MelusinaMorning.umap` is now a
**37 KB shell**. The live level is `/Game/EnvSandbox/Poitou/L_Poitou_v2` (36 MB, 169 actors:
114 `BP_Door2_0_C`, 22 static mesh actors, 13 Houdini asset actors, 3 landscapes, PCG world,
Oceanology lake, PlayerStart, 2 cine cameras). `EditorStartupMap` / `GameDefaultMap` remain
`L_MelodiaMainMenu`.

**Lookbook plate audit — 6 of 7 published plates FAIL the project's own gate:**

| Plate | Verdict |
|---|---|
| `hero-poitou-abbey-1920x1080` | **FAIL** `FLAT_WEBP(32KB<40KB)` — an unlit black silhouette on a flat white ground plane; no `Poitou_Sun`, no marsh, no water |
| `hero-zen-forest-1920x1080` | **FAIL** `FLAT_WEBP(3KB)`, `NEAR_BLACK`, `FLAT_IMAGE` — `mean_luma = 0.0`, `unique_colors = 1`: a solid black rectangle |
| `hero-kaleido-nave-1920x1080` | **FAIL** `NEAR_BLACK` (mean luma 10.2) — magenta default-material geometry in a void |
| `hero-sea-above-1920x1080` | **FAIL** `FLAT_WEBP(10KB)` — a flat blue gradient, sky only, zero geometry |
| `hero-melusina-morning-fairy-dust` | **FAIL** `MISSING_MATERIAL_MAGENTA(37%)` — the UE default-material tell |
| `hero-sakura-dream-petal-cantata` | **FAIL** `FLAT_WEBP(28KB)`, `NEAR_BLACK` |
| `hero-melusina-morning-1920x1080` | ok by the luma gate — **but its caption and alt text do not describe the image** (caption says "dawn-kissed flower islands … pastel light"; the plate is an orange sky over classical columns and a black mass). Caption correction is owed. |

**Consequence:** `my-site-kit/content/site-plates.json` marked all five showcase slots
`"status": "reviewed_environment_study"`. That status is wrong for the plates above and has
been corrected. **No plate may be published as reviewed until `Tools/audit_showcase_plates.py`
exits 0.** The tool exits 1 on any flag and is the deploy gate for the portfolio.

The 4 canonical Melusina environments and their actual state:

### Level 1: Poitou Abbey — Sunlit Maillezais Sanctuary (`L_Poitou_v2`)
- **Map Path**: `/Game/EnvSandbox/Poitou/L_Poitou_v2` — **the live level**
- **Identity & Anchor**: Poitou-Charentes Romanesque Cathedral ruins on coastal marshland.
- **Lighting Tuning**:
  - `Poitou_Sun`: Directional Light set to 45.0 lux, warm golden daylight (`#FFE8C8`, 5500K color temperature), cast shadows enabled.
  - `Poitou_SkyLight`: Real-time capture with lilac ambient bounce (`#8A93C8` at 2.8 lux).
  - `Poitou_HeightFog`: Soft morning mist with exponential decay at 0.005.
- **Physical Verification**: 18 abbey static mesh actors grounded on landscape surface (Z=2011 to Z=1755); Universal PBR material `MI_Poitou_RuinStone` assigned.
- **Lookbook Plate**: `hero-poitou-abbey-1920x1080.webp` / `hero-poitou-abbey-1920x1080.png` — **FAILS the plate audit; re-render owed.** The published plate does not show the lighting described above.

### Level 2: Melusina Morning — Meadow Cantata (`L_MelusinaMorning`)
- **Map Path**: `/Game/Melodia/Levels/Opening/L_MelusinaMorning` — **now a 37 KB shell, not the live level.** The level was replaced by Poitou on 2026-10-21 (`46669de7b`); this entry is retained as the identity of the overture/movement, not as a staged level.
- **Identity & Anchor**: Breton Coastal Romanesque pastoral meadow, dry-stone dikes, maritime pine canopy.
- **Atmosphere**: Early dawn mist settling across undulating wildflower meadows and crystal pavilions.
- **Lookbook Plate**: `hero-melusina-morning-1920x1080.webp` / `hero-melusina-morning-1920x1080.png` — passes the luma gate, but the caption/alt text do not match the image and need rewriting.

### Level 3: Kaleido Nave — Starlight Cathedral (`L_KaleidoNave`)
- **Map Path**: `/Game/EnvSandbox/Environments/L_KaleidoNave`
- **Identity & Anchor**: Monumental crystalline interior sanctuary, Rayonnant Gothic tracery, refractive caustics.
- **Atmosphere**: Vaulted crystal ceilings casting radiant chromatic caustics across mirrored marble sanctuary floors.
- **Lookbook Plate**: `hero-kaleido-nave-1920x1080.webp` / `hero-kaleido-nave-1920x1080.png` — **FAILS the plate audit (`NEAR_BLACK`, luma 10.2); re-render owed.**

### Level 4: Zen Forest — Tranquil Shaded Canopy (`L_ZenForestTest`)
- **Map Path**: `/Game/ZenForestTest`
- **Identity & Anchor**: High-fidelity Japanese cedar forest pathway, mossy stone lanterns, and drifting sakura petals.
- **Atmosphere**: Peaceful forest sanctum where soft ambient breezes guide drifting cherry petals through ancient cedar groves.
- **Lookbook Plate**: `hero-zen-forest-1920x1080.webp` / `hero-zen-forest-1920x1080.png` — **FAILS the plate audit (solid black, luma 0.0); re-render owed.**
- **⚑ STATUS: NOT CORE CANON — pending owner decision.** `Docs/MELODIA_MELUSINA_WORLD_IDENTITY_CANON_2026-10-20.md` §5 lists this land as *"Japanese cedar — NOT French"* and §8 open question 2 calls it *"the biggest lever on 'full french'"*, and its §6 forbids importing non-French pastiche into the core lands. This section previously filed it as canonical Level 4 with no flag. **It is not core canon until the owner decides** (keep as a labelled "beyond" tier / translate to French / retire). Until then it is neither promoted nor deleted — it simply must not be described as one of the canonical French lands.

---

## 6. Official Jev Decision Audit Receipts

The operational decisions governing this deployment were formally audited and certified by the Jev autonomous decision engine (`jev-1.13.0` via `TypeSafeClient`):

- **Audit Receipt File**: [BS_GodFile/Saved/Audit/jev_world_compiler_parisian_audit.json](file:///c:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/jev_world_compiler_parisian_audit.json)
- **Certifications**:
  1. `architectural_modular_breakdown`: `HIERARCHICAL_SOCKET_BAY_TAXONOMY` (Confidence: 1.000)  
     *Rationale*: Enforces invariant vertical datum levels (Base 4.8m, Piano Nobile 3.6m, Mid 3.2m, Mansard 3.0m) and horizontal bay spacing (2.4m/3.6m) to ensure total asset interchangeability between urban Haussmannian and rural Poitou Romanesque variants.
  2. `collision_and_walkability_policy`: `NANITE_COMPLEX_RAYTRACE_WITH_GROUND_PROBE` (Confidence: 1.000)  
     *Rationale*: Zero-proxy mesh mandate. Uses high-fidelity Nanite per-poly raytracing for character collision, paired with downward vertical line-traces to guarantee ground settlement without foot-hovering.
  3. `world_compiler_heatmap_strategy`: `UNIFIED_RASTER_POINT_BUNDLE` (Confidence: 0.980)  
     *Rationale*: Combines compiled sparse point arrays with 1009×1009 16-bit spatial rasters for walkability, clearance, Chladni flora density, and audio crossfading.
  4. `tonight_staging_pipeline`: `FOUR_LEVEL_CANON_WORLD_COMPILATION` (Confidence: 0.920)  
     *Rationale*: Synchronizes live multi-camera captures, PBR lighting corrections, WebP/PNG responsive publishing, and zero-slop lookbook copy across the 4 canonical levels.

---

## 7. Actionable Workflow Guide for Rapid Team Iteration

1. **Parametric Abbey & Building Prototyping (Houdini Engine)**:
   - Launch Houdini: `python tools/launch_houdini_engine_sessionsync.py`.
   - In Unreal Engine 5.8: the live layout HDA is `poitou_layout_live` (already in `L_Poitou_v2`); `Content/HDA/HDA_Poitou_AbbeyBuilder_1.0` is the separate 8-bay shell module and is **not** yet placed in the level.
   - Adjust `decay_intensity`, `bay_count`/`bay_length`, and `wall_height` in the Details Panel - those are the real control names (section 4.1). Changes cook interactively in real time.
2. **Re-compiling Spatial Heatmaps & Point Bundles**:
   - Edit recipe: `BS_GodFile/recipes/melusina_poitou_parisian_v2.json`.
   - Execute: `python Tools/world_compiler.py compile BS_GodFile/recipes/melusina_poitou_parisian_v2.json`.
   - Regenerate 16-bit rasters: `python tools/generate_world_compiler_heatmaps.py`.
3. **Deploying Multi-Camera Renders to Webfront**:
   - Execute: `python tools/stage_nikki_canon_renders.py`.
   - Review updated lookbook plates in `my-site-kit/content/site-plates.json`.
   - **Gate before publish:** `python Tools/audit_showcase_plates.py` must exit 0. It flags black, flat-gradient and missing-material plates (6 of the 7 currently published fail). A plate is not "reviewed" because it was written to the manifest.
   - Note: `site-plates.json` `slots.*.path` pointed at `../generated/assets/unreal/hero-<name>-1920x1080.webp`, which does not exist - the files are named without the size suffix, and the resolving field is `plates[].asset_path` (`/melodia/vfx-showcase-2026-09-28/...`). The `path` values have been corrected to the on-disk names.

---

## 8. Poitou Sanctuary Pack AAA CAD Refinement & Contact Sheet Receipts

All 13 assets comprising the Poitou Sanctuary Pack have been rebuilt according to the AAA CAD hard-surface discipline using Blender 5.2.1 LTS and the Higgsas Geometry Nodes Library v1.3:

- **Official Studio Contact Sheet**: [Saved/Audit/Screens/poitou_sanctuary_contact_sheet.png](file:///c:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/Screens/poitou_sanctuary_contact_sheet.png) (2560×1440, 2.33 MB).
- **Asset Manifest Receipt**: [Content/Melodia/Meshes/Poitou/poitou_sculpt_pack_manifest.json](file:///c:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Meshes/Poitou/poitou_sculpt_pack_manifest.json).
- **CAD Shading Standard**: 18mm 2-segment chamfers (profile 0.70) + face-area weighted normals (`Keep Sharp = True`).
- **Melusina Paint Pipeline**: 4-channel `vcol_melodia` baked onto every vertex (R: Cavity Wear, G: Decoration Curvature, B: Audio Elevation, A: Chladni Resonant Node).
- **Unreal Engine 5.8 Collision**: 100% per-poly raytracing verified (`ECollisionTraceFlag::CTF_UseComplexAsSimple`).

## 9. Curation Gate: Curated-Hybrid Acceptance (Poitou)

The Poitou level is a **curated hybrid**: the sanctuary pack and hero assets are hand-sculpted (Blender 5.2.1 + Higgsas GN, Â§8), while the core level, room shell and layout are generated live through Houdini Engine (Â§4, Â§7.1). Curated means a human chooses what ships; it does **not** mean the generated side inherits the sculpted side's guarantees. Three clauses make the hybrid shippable, and one tool proves them.

### 9.1 Collision ownership follows the authoring side
Â§3.2's zero-proxy standard is verified on the **sculpted** pack (`SM_Maillezais_BrokenArch`, `SM_Maillezais_ButtressStub`, `SM_Maillezais_CrumbledWall` -> `UseComplexAsSimple`, `has_per_poly_collision: true`). The **generated** side must meet the same standard, because it is the surface the pawn actually stands on.

Baseline measured on `L_Poitou_v2` (2026-10-21): 604 static/landscape components â€” **442 `QUERY_AND_PHYSICS`, 161 `NO_COLLISION`**.
- Most of the 161 are correct by design: her cosmetics (brows, lashes, iris, regalia, FX rings, wand, violin), decoration (grass, ground cover), the lake's debug cube, the bubble-preview sphere.
- **One is not:** the room shell's `SM_hero_house` (`/Game/Melodia/Kit/MorningPlaza/SM_hero_house/StaticMeshes/SM_hero_house`) carries **no collision data at all** (`simple_collision_count = -1`, `CTF_USE_DEFAULT`, component `NO_COLLISION`). She can walk through the house.

**Requirement:** every HDA / Houdini Engine output the pawn can touch generates complex-as-simple collision in the same cook, or ships a baked collision proxy authored in Houdini. No exemption for "it is only decoration".

**Gate status: OPEN.** The requirement is stated; the baseline measured one paragraph above **violates it** (`SM_hero_house`, no collision data, pawn walks through the house). The fix belongs in the room-shell HDA output, not in a runtime pass — and per the standing rule recorded in `CURRENT_STATE.md` (2026-10-20), **collision is an art/rig decision and must not be authored by a demo or automation pass**.

### 9.2 The shipping path bakes; the live cook is authoring only
Â§7.1's interactive cook is an authoring loop and must not be the shipping path.
- Live-cooked Houdini Engine actors cannot be cooked for a build, and their geometry can arrive **after** the pawn has landed â€” the floor is not there in the first frames.
- Baseline: **28 HAPI cook events** in one editor session, with the room shell cooking during PIE.

**Requirement:** for any shippable level, Houdini Engine actors are baked to static meshes (or the level ships pre-cooked outputs), and the spawn is gated so the pawn cannot land before its supporting surface exists.

### 9.3 One live generation
A curated hybrid keeps working generations; they must be parked, not live.
- Baseline on `L_Poitou_v2`: `Poitou_Layout_v6` **and** `Poitou_Layout_v6_Recovery` are both live, alongside two landscape generations (`poitou_layout_live_v6_357_422`, `Poitou_Layout_RoomShell_Candidate_601_71`).
- **Requirement:** exactly one layout and one landscape generation are live (cooking, colliding, visible). The rest are parked outside the level or disabled. A parked generation costs nothing; a live one doubles the cooks and makes "which is canonical" a question every reader has to re-ask.
- **Gate status: OPEN.** The baseline above still has two live layout generations. Note also that `Poitou_Layout_v6_Recovery` carries the ISM tree instances (`tree-high` 596x, `tree_fat` 184x); those were repointed to `SM_MossyTree_01` in the map, but they are **cook output** - a recook restores the Kenney proxies. Confirmed live on 2026-10-21: the editor log shows `Failed to find object '.../tree-high.tree-high'` and `LogHoudiniEngineEditor: Warning: Null Object found for instance` during a Poitou cook. The durable fix is the HDA's instance-asset assignment, not the map.

### 9.4 Mechanical acceptance: the grounding proof
`Tools/Editor/check_pawn_grounding.py` runs automatically once per PIE session and writes a receipt to `Saved/Audit/GroundingProof/`. It is the gate for 9.1 and 9.2:
- **PASS** requires all three: the pawn settles (no descent across the sample window) **and** the character movement reports a blocking floor **and** that surface's component has collision enabled (and, for a mesh surface, its asset carries collision data).
- It names the surface she stands on, so "she fell through" becomes a named asset instead of a screenshot.
- **INCONCLUSIVE** is a real outcome: if the editor game thread is blocked (a modal dialog freezes PIE, or an asset editor window has no docked tabs), the proof says so instead of guessing.

Baseline reference reading (2026-10-21, clean session): she stands on the room shell at `floor_dist = 2.15 cm`, with the landscape surface 108 cm below her.

---

## 10. In-theme procedural architecture programme (headless) — 2026-10-21

**Intent.** Every element of Poitou is created in theme, procedurally, in the v6 layout HDA, with a
masonry system that is actually French-Romanesque. Not "more instances of better meshes": real
generated geometry.

**Authority.** This section is the build contract for the programme. The world identity is
`Docs/MELODIA_MELUSINA_WORLD_IDENTITY_CANON_2026-10-20.md`; the style contract is
`Docs/Poitou/poitou_layout/style_contract.md`; the asset graveyard retirement is
`Docs/Production/KENNEY_GRAVEYARD_RETIREMENT_2026-10-21.md`.

### 10.1 The measured baseline — what the level is today

`Tools/Poitou/poitou_intheme_gate.py` (headless, hython) cooks the live v6 HDA and asserts that
every generated instance is in-theme, exists, and is the size its scale divisor assumes. It fails
today, and the failure is the programme's backlog:

```
output output_landscape     points=9        prims=9
output output_points        points=12572    prims=9
output output_route_curve   points=261      prims=1
output output_skirt_mesh    points=0        prims=0      (expected: horizon_on is off)
output output_water         points=12247    prims=9781
point types: poplar 628 · ash_tetard 196 · reed_bank 1554 · meadow_grass_clump 4414 ·
             reed_marsh 5669 · barque 6 · building 105

FAIL: 9 problems
  - poplar          628  -> tree-high           RETIRED-PACK
  - ash_tetard      196  -> tree_fat             RETIRED-PACK
  - reed_bank      1554  -> grass_leafsLarge     RETIRED-PACK
  - meadow_grass_clump 4414 -> grass_leafsLarge  RETIRED-PACK
  - reed_marsh     5669  -> grass_leafsLarge     RETIRED-PACK
  - barque            6  -> canoe               RETIRED-PACK
  - no 'poplar_band' points
  - no 'abbey_maillezais_footprint' points
```

**12,547 of the layout's 12,572 instance points — 99.8% — point at the retired Kenney pack.**
The only in-theme instance is `building` × 105 → `SM_hero_house`, which is the *Morning* house
mesh (not a Poitou house) and carries no collision (§9.1).

**The abbey is not generated at all.** v6's `inst.vex` ends with
`if(real && (t=="rubble" || t=="abbey_maillezais_footprint")) removepoint(0,@ptnum);` — with real
meshes on, the abbey footprint cube and every rubble cube are *deleted*. The layout HDA therefore
produces a heightfield, a water plane, a horizon skirt, a route curve and a field of instance
points, and **not one piece of architecture**.

**The scale divisors are wrong** (`Tools/Editor/poitou_intheme_assets.py`, Unreal side):

| mesh | divisor in `inst.vex` | measured | verdict |
|---|---|---|---|
| `tree-high` (poplar) | 1.02 / 2.97 / 1.02 m | **does not load** | MISSING |
| `tree_fat` (ash) | 0.76 / 1.15 / 0.65 m | 1356.0 × 1631.0 × 1594.3 cm | **SIZE-ERROR, ~18×** |
| `grass_leafsLarge` (reeds) | absolute `set(3,12,3)` | 47.6 × 48.7 × 14.3 cm | **SIZE-ERROR** |
| `canoe` (barque) | 0.30 / 0.18 / 1.15 m | 30.0 × 115.0 × 18.3 cm | AXIS-ORDER (size right, axis mapping ambiguous) |
| `SM_hero_house` | 5.57 / 3.27 / 4.01 m | 557.2 × 401.5 × 326.7 cm | AXIS-ORDER (size right, axis mapping ambiguous) |

`inst.vex` divides Y by the mesh's Z and Z by the mesh's Y, because the source meshes are
authored Z-up and Houdini is Y-up. For the house that is a 23% error; for the ash, 18×.

> **This is why the level read as a graveyard: the props were the wrong SIZE, not just the wrong
> art.** A retarget that swaps the mesh without re-deriving the divisor reproduces the same
> failure, so the divisor is part of the asset contract from now on.

### 10.2 The two things that block everything else

**(a) The repo's builder is the wrong version.** `Tools/Poitou/build_poitou_hda.py` is the **v5**
builder; the live **v6** builder is `C:\Users\froma\agent-tools\poitou_houdini\build_poitou_hda.py`
(29,308 B vs 26,393 B). Building from the repo copy silently regresses: 13 landscape layers
instead of 20, no IGN calibration, `horizon_on=True` instead of False, and the wrong landscape
material. `patch_nikki.py` (4,350 B) is the exact v5→v6 source diff. **The repo copy must become
the v6 source of truth** — the build spec already says to treat the repo copy as the source of
truth and the external folder as scratch, but the repo copy is currently the *older* one.

**(b) The materials do not exist.** The generator vocabulary names ~30 material instances and
**six exist**:

- Present: `MI_Poitou_LimeWash` (#E6DFCC / 0.88), `MI_Poitou_Tile` (#C07A57 / 0.80),
  `MI_Poitou_Slate` (#4E555C / 0.55), `MI_Poitou_Oak` (#A58A66 / 0.80), `MI_Poitou_Tar`
  (#26221E / 0.65), `MI_Poitou_RuinStone` (#9A9384 / 0.85).
- **Missing and needed first:** `M_Poitou_Stone_Plinth` — the **third slot on every Poitou stone
  mesh** in the sculpt manifest, and it does not exist in the project. The `Foundations` receipt
  admits it: *"RuinStone is reused pending limestone material review."*
- Missing and needed by the generators: `MI_Poitou_Quoin_Limestone`, `MI_Poitou_Church_Ashlar`,
  `MI_Poitou_Wall_LimeRender` (+`_Coastal`), `MI_Poitou_Wall_BarnRubble`, `MI_Poitou_Church_Carved`,
  `MI_Poitou_Church_SpireSlate`, `MI_Poitou_Church_Louvres`, `MI_Poitou_Ruin_Limestone`,
  `MI_Poitou_Ruin_BrokenEdge`, `MI_Poitou_Ruin_GothicTracery`, `MI_Poitou_Wall_Quereux`,
  `MI_Poitou_Plinth_DampStone`, `MI_Poitou_Trim_Wood`, `MI_Poitou_Cladding_Poplar`,
  `MI_Poitou_Roof_Slate_Logis`, `MI_Poitou_Roof_TigeDeBotte`, `MI_Poitou_Shutter_*` (4),
  `MI_Poitou_Walk_OakDeck`, `MI_Poitou_Walk_TarredKey`, `MI_Poitou_Walk_Rail`, `MI_Poitou_Walk_Pile`,
  `MI_Poitou_Bridge_StoneBief`, `MI_Poitou_Duckweed`.

**No new master** (the 2026-10-20 v2 decision): every one is an MI of
`/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`, using the 8-layer master spec
(L0–L7 + toon) and the vertex-paint convention **R = lime-wash, G = extra damp, B = moss,
A = reserved (ivy on ruin / peel override)**.

### 10.3 The research the generators build on

**Maillezais — the canon anchor, and the real building.**
- 7-bay nave; everything except the 7th bay is 11th-century Romanesque.
- **Westwork (massif d'entrée) with narthex, c. 1080**, two towers.
- **Galleries in the side aisles of the first four bays**, carried on vaults and supported
  **yoke-by-yoke by belt arches** — the generator needs a *bel/force* arch, not a plain wall.
- **Five massive buttresses on the north wall, added in the 13th century, "at their bases,
  slope-like bevels were attached to the outside to enlarge the contact area"** — that is the
  foundation typology: a **splayed buttress base**, not a flat plinth.
- Gothic pointed-arch windows added in bays 5–7, c. 1300 — so a *semicircular-arches-only* rule
  is right for the Romanesque core and the Gothic phase is a later overlay.
- Ruined, and **used as a stone quarry** after the Revolution.
- **The abbey was an island until the monks dug the canals in the 13th century.** The canal and
  the abbey are **one project**, not two — the layout must read that way.
- The outdoor area west of the abbey presents medieval construction as "adventure archaeology":
  a giant mason's head, hands and feet scattered as workshops.

**Tuffeau.** A local limestone of the Loire Valley: *"chalky or sandy, fine-grained limestone, white
to yellowish-cream"*. The repo's `M_Tufa_Stone_Blocks` and `M_Chauvigny_Stone` (Saint-Savin) are the
right names.

**The masonry system — `appareil`.** This is the "proper brick generation", and it is a real
technical vocabulary, not a texture:
- **Grand appareil** — dressed ashlar in horizontal courses, **dry joints** ("joints vifs"), no
  mortar. The upper tier and the openings.
- **Appareil à moellons quadrangulaires** — squared rubble in horizontal courses with
  *"une volonté évidente de faire alterner les joints"*: stone laid in a brick bond.
- **Opus mixtum à bandes** — alternating courses of rubble and courses of brick.
- **Chaînage d'angle / arases** — *"l'emploi de briques disposées en chaînages (ou arases) de deux
  ou trois rangées, à intervalles réguliers dans une maçonnerie"* answers *"favoriser la dilatation de
  la construction, assurer la régularité de la construction et son homogénéité, les rangées de
  briques occupant toute l'épaisseur du mur"*. **This is the single best rule for the generator:
  a brick band every 2–3 courses, through the full wall thickness.**
- **Appareil en épis** — herringbone, for revetments and insets.
- **Bonds** — English / Flemish / American; **"dog's tooth"** (alternating headers and stretchers
  forming a zig-zag) for door and window jambs.
- **Refends** — the deep vertical grooves of a rusticated base course, already named in the world
  identity canon.
- **Soubassement** (footing), **arase** (levelling course), **chaînage d'angle** (corner bonding).
- **Rendered rubble**: *"moellons équarris sur une seule face en parement et non assisés"*, with
  the opening frame standing **2–3 cm proud** of the render. Lime mortars only — *"Proscrire
  l'utilisation du ciment, et utiliser un mortier de chaux (chaux aérienne, ou chaux hydraulique
  naturelle NHL)"*.
- **Faux appareil** — painted false joints. Provins: *"faux appareil jaune à joints rouges et
  blancs"*; Maulnes: *"faux-joints gravés très fins imitant un appareil régulier de pierre de
  taille"*. This is the cheap, high-yield path: a Poitou facade can carry a *painted* ashlar
  pattern instead of modelled coursing.

**The canal.** Canal du Midi: 360 km, 328 works, 1667–1694, Riquet. The section is the generator
spec: *"780 m long at the top and 140 m at the base, made up of 153,000 m³ of mixed stone and earth
between **two masonry retaining walls and a central impermeable stone barrier**."* The works that
line it: *"écluses, ponts, épanchoirs mais également moulins, lavoirs, maisons d'éclusiers, ports et
auberges."* The **maison éclusière** typology was fixed c. 1750 with *"variations locales très
limitées"*; at the end of the 17th century they were single-storey, **11–12 m long and 7–8 m deep**.
UNESCO: the canal is remarkable *"for both great aesthetic concern in terms of architecture and in
terms of man-made landscapes"* — **the canal's engineering and its buildings are one work.**

### 10.4 The programme, in order

**Phase 0 — Recover and reconcile (blocks everything).**
1. Reconcile the v6 builder and v6 `snip/*.vex` into the repo, using `patch_nikki.py` as the diff, and
   make the repo copy the single source of truth. After this, `Tools/Poitou/build_poitou_hda.py`
   builds v6 and the external folder is scratch.
2. Recover the **missing builder scripts** for the 2026-10-21 HDAs. Their `.hdalc` binaries and
   `receipt.json` survive under `Saved/Audit/PoitouConvergence_20261020/`; the builders do not.
   Only `extend_roomshell_full_town.py` (43,918 B) survives.
3. One build path, one hash, one receipt.

**Phase 1 — The material gap (blocks the masonry).**
1. Author `M_Poitou_Stone_Plinth` — it is the third slot on every Poitou stone mesh.
2. Author the masonry MIs listed in §10.2, as MIs of `M_Master_Toon_Universal`, no new master.
3. Port the technique of `Tools/Houdini/surreal_brick_aaa.py` (SDF rounded-box bricks, per-brick
   inset/shift/colour variation, mortar gaps, bevel + crest highlight) to a Poitou trim set at the
   2.4 m bay tile scale, targeting `M_Tufa_Stone_Blocks` + `M_Limestone_Rubble_Core` +
   `M_Mortar_Joints` — the three that already exist — so the wall is legible before the new MIs land.

**Phase 2 — The masonry system.**
Base: `Tools/Houdini/cathedral/build_poitou_abbey_hda.py` already implements a working version of
the bay/buttress/decay grammar (2.4 m bays, 0.6 m tufa, stepped buttresses, `preview_mode`) and is
**not wired into the v6 layout**. Extend it with the `appareil` rules:

| Element | Rule |
|---|---|
| module | 0.6 m tufa module, 0.6 m course height, 0.45 m ashlar facing leaves, 0.9 m rubble core, **1.8 m double-leaf wall** |
| bay | 2.4 m; **wall run 14.4 m = 6 bays exactly** |
| courses | grand appareil (dry-jointed ashlar) in the upper tier and around openings; appareil à moellons quadrangulaires below; **opus mixtum à bandes with a brick band every 2–3 courses through the full thickness** |
| openings | **semicircular arches only** in the Romanesque core; the Gothic phase is a later overlay |
| base | refends rustication at the base tier; **splayed buttress base** (the 13th-c. Maillezais bevel) |
| render | rendered rubble with the opening frame 2–3 cm proud; lime mortars, never cement |
| cheap path | faux appareil — painted false joints (Provins, Maulnes) |

The generator's module envelope must match `SM_Maillezais_CrumbledWall` (12.02 × 2.26 × 10.505 m
blockout / 13.729 × 2.32 × 9.485 m converged): a ~12–14 m long, 2.3 m thick, ~10 m tall
double-leaf wall module. **14.4 m = 6 × 2.4 m exactly** resolves the fractional-bay problem the
build spec flags as an open owner decision, and the 105 m × 32 m canon footprint should snap to a
whole number of 14.4 m runs.

**Phase 3 — The element generators.** Each becomes a new output node in the v6 HDA, authored
headlessly. Foundations, lane ribbons, crossing bridges and roofs **already exist as HDAs** — the
gap is not generating them but upgrading flat primitives into in-theme masonry.

| Element | Base | In-theme target | Today |
|---|---|---|---|
| Foundations / soubassement | `Poitou_GroundedFoundations` (104 lots, 624 plinth polys, max relief 1.496 m) | `M_Poitou_Stone_Plinth` + `M_Tufa_Stone_Blocks` | flat, `RuinStone` reused, not imported |
| Wall runs / ashlar | new, from the abbey HDA grammar | `M_Tufa_Stone_Blocks` + `M_Limestone_Rubble_Core` + `M_Mortar_Joints` | absent |
| Railings / balustrade | `deploy/surreal_architecture_gen.py::build_railing` (line 3696) | `M_Wrought_Iron` + `M_Wrought_Iron_Hinges` (**both exist**) | absent |
| Canal stonework | extend `Poitou_LocalBanks`; two retaining walls + a central impermeable barrier | `MI_Poitou_Bridge_StoneBief` + tufa | absent |
| Paved pathways | `Poitou_ConnectingLanes` (104 lots, 71 connected, 1753 m, 2.4 m, 907 polys) | `MI_Poitou_Walk_OakDeck` / `_TarredKey` / `_Rail` / `_Pile` | flat ribbons, no kerbs, no collision, intersections unverified |
| Crossing bridges | `Poitou_LaneCrossings` (**`crossings: []` — none met the criteria**) | `MI_Poitou_Bridge_StoneBief` | none |
| Roofs | `Poitou_SolidRoofs` (104, 10,192 polys, 0 non-manifold) + `Poitou_StudioRoofs` (114 curved) | `MI_Poitou_Roof_Slate_Logis`, `_TigeDeBotte` | not live-imported |
| Lock gate / abbey | `SM_Poitou_LockGate_Pair`, `SM_Maillezais_*` | `M_Wrought_Iron`, `M_Tarred_Oak` | abbey not generated at all |
| Poplar / ash rows | `inst.vex` repoint | `SM_MossyTree_01`, `SM_AshTetard_*` | 628 + 196 instances on the retired pack |
| Barque | `inst.vex` repoint | `SM_Marais_Barque_4m6_Sculpted` (4.50 m, the 4m6 slot) | 6 on the retired pack |
| Door / fence / reeds | — | — | **no in-theme equivalent exists — must be authored** |

**Phase 4 — The gates, all headless.**
1. `Tools/Poitou/poitou_intheme_gate.py` (hython): no retired-pack instance, no `/Engine/BasicShapes`
   blockout, every named instance in-theme, every output cooks, the required vocabulary complete,
   **and the scale divisors match the measured meshes**. Writes
   `Saved/Audit/PoitouConvergence_20261021/intheme_gate.json`; exits non-zero on any failure.
2. `Tools/Editor/poitou_intheme_assets.py` (Unreal commandlet): measures every instanced mesh and
   every replacement candidate, classifies each as MISSING / SIZE-ERROR / AXIS-ORDER, and writes
   `inst_scale_cache.json` for the gate to compare.
3. `Tools/Poitou/run_intheme_gate.ps1`: the **wedge-proof** runner. A bare `hython --version` in a
   shared console hung >60 s and wedged the shell on 2026-08-28, so every hython call goes through
   `Start-Process` + a hard timeout + a forced kill — the pattern already used by
   `Tools/Houdini/sea_above_reef/probe_hython_license.ps1`.
4. The per-lot audit shape is already proven by `ScaleAudit/hda_scale_foundation_audit.json`:
   floor centre, shell dimensions, roof footprint error, per-corner ground sample, foundation
   exposure, terrain intrusion.

**Phase 5 — Acceptance.** The programme is done when the gate passes on the v6 source, the
foundations/lanes/crossings/roofs receipts report real masonry rather than flat ribbons, and one
continuous walkthrough shows the abbey, the canal stonework and the paths in theme at 1:1.

### 10.5 Open owner decisions

1. **The bay.** 14.4 m = 6 × 2.4 m exactly. Does the 105 m canon footprint snap to a whole number
   of 14.4 m runs, and does the 32 m width snap to 2.4 m bays? (This is the same fractional-bay
   question the build spec already carries.)
2. **The poplar.** `SM_MossyTree_01` is the Megascan the owner already used for the far bands, so
   near and far would read as one species — but it is a Megascan, not a Poitou poplar.
3. **The door, the fence and the reeds** have no in-theme equivalent. Author, or accept a
   substitute.
4. **Faux appareil** — is painted false-joint coursing acceptable in place of modelled masonry
   where the camera never gets close?


### 10.6 Landed 2026-10-21 — the gate is green, the masonry is generated

The in-theme gate (`Tools/Poitou/poitou_intheme_gate.py`, headless hython) **passes**. The baseline
recorded in 10.1 is closed on every line it names:

| baseline failure (10.1) | now |
|---|---|
| 12,547 of 12,572 instances named the retired Kenney pack | **0** — every instance names an in-theme asset that resolves |
| `output_skirt_mesh` cooked empty | **14,000 prims** — `horizon_on` now defaults True |
| no `poplar_band` points | **1,911** far poplar bands + 2 far spires |
| the abbey was deleted outright | **32 pieces of real Maillezais tufa ruin** (2 arches, 16 nave wall runs, 14 buttresses) |
| the scale divisors were wrong | **0 of 10 mismatched** — the audit parses `inst.vex` and enforces the `(srcX, srcZ, srcY)` axis rule |
| `M_Poitou_Stone_Plinth` never authored | authored, plus 7 more MIs; **18 meshes re-bound** off `WorldGridMaterial` |

**The masonry generator is the new thing.** `Tools/Poitou/snip/revet.vex` generates the canal-du-Midi
section in Houdini rather than placing meshes: two retaining walls and the central impermeable
barrier, 0.6 m module / 0.6 m course, joints staggered half a module, a chaine-arase brick band
every 3 courses through the full thickness, a 0.45 m ashlar leaf over a 0.9 m rubble core, a
refend base, 2 cm dry joints, vertex paint R=lime-wash G=damp B=moss A=ivy — **329,439 prims** in
three project materials. It ships as `output_masonry` (output index 5).

**The build path is now the repo.** `Tools/Poitou/build_poitou_hda.py` + `snip/` + `layout_v0.json`
are the source of truth; `Tools/Poitou/run_intheme_gate.ps1 -Build -Measure` reproduces the HDA,
the audit and the gate. The external v6 folder is no longer a build input.

**Still open (owner).** A Poitou poplar mesh (the hornbeam is a real European tree, not a columnar
Lombardy poplar). Whether faux appareil is acceptable for distant walls. The six lost element
builders (foundations / lanes / crossings / roofs), which survive only as receipts. And the UE-side
HDA asset needs a sixth output slot for `output_masonry`, which needs the editor.
## 11. The offline HDA programme - the lens, and what we build next

> This section is the execution plan for the whole Poitou programme. It lives here, in the build
> contract, because a plan document is not a second authority - AGENTS.md is explicit that there
> is one status document (`CURRENT_STATE.md`) and one build contract (this file). Everything below
> is executed HEADLESS: no editor, no GPU, no human in the loop until the gate is green.

### 11.0 The lens - the rule every generator is judged by

**Geometry is the silhouette. Paint is the finish. One kit, many assemblies.**

This is the Infinity Nikki lesson applied to Poitou, and it is the reason the programme is a
programme and not a shopping list of assets:

* **The silhouette is BUILT.** Coursing, arches, buttress steps, roof pitch, the columnar crown of
  a poplar, the step of a quay - all geometry, all on the governing meter (0.6 m beat, 2.4 m bay),
  all generated in the HDA.
* **The finish is PAINTED.** Lime-wash, the damp band, moss, ivy, the per-course tile hue - all
  vertex paint read by the ONE toon master. A surface can carry four zones without four textures.
* **False joints are PAINT, never geometry.** Faux appareil belongs in the master, on the paint
  layer, wherever the silhouette does not need it. That is the single biggest cost saving in the
  programme and it is free.
* **One kit, many assemblies.** Every generator includes `snip/kit.vex`. The canal revetment, the
  abbey, the houses, the quay and the poplars are ONE building system with different parameters -
  not seven styles that happen to coexist in a level.
* **The gate is the discipline.** A generator is done when it compiles, cooks non-empty, emits the
  element groups the gate names, and uses project materials only. A generator that silently stops
  emitting is a FAILURE, not a smaller level. The gate is what makes expanding the geometry safe:
  every generator added since 2026-10-21 was caught by it, twice, before it shipped.

### 11.1 Where the programme stands (measured 2026-10-21)

`Tools/Poitou/snip/kit.vex` is the shared grammar: `kit_box`, `kit_wall_stone`, `kit_wall`,
`kit_arch`, `kit_buttress`, `kit_slope`, `kit_gable`, `kit_ribbon`, `kit_taper`, `kit_faux_mask`.
It fixes the constants the canon fixes: 0.6 m module and course, 2.4 m bay, 14.4 m = 6 bays,
0.45 m ashlar leaf over a 0.9 m rubble core, a chaine/arase band every 3 courses through the full
thickness, a rusticated refend base, 2 cm dry joints, semicircular arches only, and the vertex paint
convention R=lime-wash G=damp B=moss A=ivy.

Seven generators ship, all off that kit, all gated:

| generator | element | measured output |
|---|---|---|
| `revet.vex` | the canal-du-Midi section: two retaining walls + the central barrier | **329,439 prims** |
| `abbey.vex` | Maillezais: 7-bay nave, 1080 westwork, narthex, gallery on belt arches, splayed buttresses, apse, gable roof | 13,860 nave + 13,266 westwork + 5,580 apse + 504 arcade + 504 lancets + 288 buttresses + 36 portal + 144 roof + 54 apse roof |
| `found.vex` | the soubassement under every village house | **150,984 prims** |
| `lane.vex` | the village lane ribbons with kerbs, dodging the houses | **13,536 prims** |
| `cross.vex` | the lane crossings - deck, parapet, piers | 30 + 60 + 60 prims |
| `roof.vex` | the village roofs, low-pitch canal tile, per-course hue jitter | **13,080 prims** |
| `poplar_gen.vex` | the canal-bank poplar, generated: tapering trunk + columnar crown | 33,858 + 18,810 prims |

**596,382 generated prims in total**, and the gate asserts every one of the 18 element groups is
present by name. The near poplar rows are no longer instanced at all: the poplar is generated,
because the in-theme tree meshes are broad-crowned European trees and a stretched hornbeam is not
a poplar. The far horizon bands stay instanced - at 1.3-2.6 km a columnar poplar is a smudge and
a real tree reads as a tree.

### 11.2 The backlog, in priority order

Priority is by what a still of the P0 walk must contain. P0 is the walk (bedroom -> house ->
village -> canal -> departure), so the village and the canal outrank everything else.

| # | generator | what it must emit | the gate assertion | why it is worth it |
|---|---|---|---|---|
| **P0.1** | `house.vex` | the village house shell: walls in courses, a round-arched tufa door surround, an oak door, shutters, a chimney, the soubassement under it | `house_wall`, `house_door_surround`, `house_door_leaf`, `house_shutter`, `house_chimney` | the 105 village houses are ONE instanced mesh with no generated detail, and the village is beat 3 of the walk |
| **P0.2** | `church.vex` | the village church: nave, porch, bell tower, slate spire | `church_nave`, `church_tower`, `church_spire` | the church is the heart of the village; the route passes it |
| **P0.3** | `door.vex` | the door and the fence - the last two elements with NO in-theme equivalent (owner decision 3). Both become masonry: a tufa-framed round-arched opening, and a low rubble wall with an iron rail | `door_surround`, `door_leaf`, `fence_wall`, `fence_rail` | closes the last substitution gap in the programme |
| **P1.1** | `quay.vex` | the maison eclusiere (11-12 x 7-8 m) and the quay walls | `lock_house`, `quay_wall` | the canal-du-Midi section is beat 4, and the lock house is the building the whole canal system exists for |
| **P1.2** | `jetty.vex` | the tarred-oak pilings and the plank walkway (the palette's "black keys") | `jetty_piling`, `jetty_deck` | the water's edge is where the eye goes, and the barques need somewhere to lie |
| **P1.3** | `bank.vex` | the steps down to the water, the mooring rings, the towpath edging | `bank_step`, `mooring_ring` | the bank is where the level is read from eye height |
| **P2.1** | `reed.vex` | the reed beds as generated geometry along the canal | `reed_clump` | today the reeds are an instanced grass card; the marsh is a whole beat of the mood |
| **P2.2** | `ivy.vex` | the ivy on the ruin (vertex channel A) and the moss breakup | `ivy_mat` | the canon's A channel is unused; ivy is what makes a ruin romantic |
| **P2.3** | `quoin.vex` | the dressed quoins and the tufa string courses on the house corners | `quoin`, `string_course` | cheap, and it is what makes a rendered-rubble wall read as built |
| **P3.1** | `clos.vex` | the walled garden (clos) with the fig trees and the vine rows | `clos_wall`, `fig_tree`, `vine_row` | the clos is the Poitou house garden and it is what makes a house a home |
| **P3.2** | `boat.vex` | the barque hull, generated: tarred oak, iron hardware | `boat_hull`, `boat_iron` | six barques are placed; they should be built, not instanced |
| **P3.3** | `bird.vex` | the flock, against the existing AE layer (`Tools/Poitou/ae_poitou_flockloop.py`) | `bird` | the marsh is alive; the AE layer already exists |
| **P4** | `appareil.vex` | the faux-appareil mask writer for distant walls | the `faux_joint` attribute is present on the masonry | a PAINT feature, not geometry - the cheap path to distant walls |

### 11.3 How we execute it - headless, one command, gated

```
Tools\Poitou\run_intheme_gate.ps1 -Build -Measure
```

1. **BUILD** - `hython Tools/Poitou/build_poitou_hda.py` cooks the v6 HDA from the repo sources and
   writes `Tools/Poitou/hda/poitou_layout_live.hdalc` + the test hip. Every node error is printed.
2. **MEASURE** - `UnrealEditor-Cmd -run=pythonscript Tools/Editor/poitou_intheme_assets.py` parses
   `snip/inst.vex`, measures every instanced mesh in Unreal and checks the axis contract.
3. **GATE** - `hython Tools/Poitou/poitou_intheme_gate.py` cooks the HDA and asserts: every output
   cooks non-empty; every instance is in-theme; the vocabulary is complete; every scale divisor
   matches its measured mesh; every generated element group named in 11.2 is present; every
   material a generator assigns is a project material. The receipt lands in
   `Saved/Audit/PoitouConvergence_20261020/intheme_gate.json`.

**A generator is done when the gate is green.** Not when it "looks right" - a screenshot is the
editor's job, and the editor is the owner's.

### 11.4 The UE-side wiring (needs the editor, and only the editor)

The HDA now has two generated outputs: `output_masonry` (the revetment) and `output_generated` (the
element set). The UE-side Houdini Engine asset `poitou_layout_live_v6.uasset` needs **two** output
slots added and wired, and the two generated outputs need `unreal_material` mapping to material
slots. That is the one piece of this programme that cannot be done headlessly, because the editor
is the owner's live session.

### 11.5 The paint layer (the part that makes the geometry cheap)

The toon master already carries the layer stack - lime-wash, the damp band, moss, weathering - and
the generators write R/G/B/A per stone. Two things are still owed there, and both need a material
edit (ask-first, `Content/Materials/` is on the never-touch list):

* the **A channel** is not read by the master yet, so the generated ivy is invisible until it is;
* **faux appareil** needs a joint-mask input in the master, fed by the `faux_joint` vertex
  attribute the kit writes.

### 11.6 Open owner decisions (unchanged, still owed)

1. **The poplar** - the tree is now generated, which settles the art gap, but a Poitou poplar
   deserves a real trunk profile rather than a stack of drums.
2. **Faux appareil** - acceptable for distant walls? (P4 above assumes yes.)
3. **`p4 submit -c 292`** - the Kenney retirement is still an unsubmitted Perforce changelist.
4. The two stale remote branches, and the primary checkout's reconciliation with `origin/main`.
## 12. BRIEFING FOR THE NEXT AGENT (2026-10-21) - the traps, the measurements, the rules

Read this before writing a single generator. Everything here was paid for in an outage.

### 12.1 The rule that matters

**ADDITIVE ONLY. New files and new HDA outputs. Never mutate an asset a live level depends on.**
On 2026-10-21 a session rebound the material slots of 18 existing Poitou mesh packages while
`L_Poitou_v2` was live. The level's `Poitou_Layout_v6` Houdini cook then finished "with errors",
the actor produced nothing, and the owner's working game level stopped. The pre-session state was
measured (18:34) and is in `Saved/Audit/PoitouConvergence_20261020/poitou_mesh_slots.json`;
`Tools/Editor/poitou_restore_mesh_bindings.py` restores it exactly. Jev's ruling
(`JevPoitouLevelAudit_20261021.json`) is `NEW_ASSETS_ONLY_NO_EXISTING_MUTATION`.

Corollaries that cost me time:
* **Never remove content before its replacement is live.** I removed the near poplar rows'
  instance (627 trees) because a generated poplar existed - but the generated poplar was not wired
  to the UE output slots, so the trees simply vanished.
* **The 8 MIs stay unbound.** Authoring a material is additive; binding it to a live mesh is a
  separate, owner-approved step.
* **`p4 revert` on the Poitou meshes would DELETE them** - they are open for ADD. Check
  `p4 opened` before touching anything in `Content/`.

### 12.2 The axis trap (the one that cost the most)

The retired Kenney pack is **Y-up**; the Poitou authored pack and every in-theme mesh is **Z-up**
with its pivot at the base. Houdini is Y-up and the Houdini Engine maps
`UE X -> Houdini X`, `UE Z -> Houdini Y (up)`, `UE Y -> Houdini Z`. So the divisor triple written
into `set(scale.x, scale.y, scale.z)` is

    (srcX, srcZ, srcY)

and **the .y (up) divisor must equal the mesh's measured Z size**. A .y divisor that matches some
other axis is an axis-order error: right in one direction, grossly wrong in the others. That is
what the 18x-wrong pollard ash was. `Tools/Editor/poitou_intheme_assets.py` PARSES `inst.vex` and
enforces this; do not hand-maintain a divisor table.

Measured sizes (metres, 2026-10-21, after the restore) - divide by these, never by eye:

| key | asset | srcX | srcY | srcZ (height) |
|---|---|---|---|---|
| POP | SM_EuropeanHornbeam_04 | 4.1249 | 2.7299 | 6.7970 |
| ASH | SM_AshTetard_Canal_03_Sculpted | 2.2012 | 2.1764 | 2.2930 |
| GRS | SM_KikuyuGrass_01 | 0.7528 | 0.7960 | 0.4623 |
| CANOE | SM_Marais_Barque_4m6_Sculpted | 4.5024 | 1.4416 | 0.3028 |
| HOUSE | SM_Melusina_ClayHouse_v07 | 12.6613 | 9.4577 | 6.9265 |
| SPIRE | SM_Poitou_Cymatic_Spire_Sculpted | 3.6553 | 3.6545 | 15.2443 |
| RUBBLE | SM_Maillezais_CrumbledWall_Sculpted | 11.9784 | 1.5333 | 6.7375 |
| ARCH | SM_Maillezais_BrokenArch_Sculpted | 8.4525 | 1.8155 | 13.2064 |
| BUTTRESS | SM_Maillezais_ButtressStub_Sculpted | 1.6173 | 2.2697 | 9.8036 |
| GROUND | SM_GrassGroundPatch_01 | 3.3966 | 4.9005 | 0.1893 |

**A save can move a mesh's bounds** (re-saving these meshes moved the crumbled wall's thickness
126.5 -> 153.3 cm). Re-measure after any save, and let the audit re-derive.

### 12.3 VEX in this Houdini build (22.0.368) - the landmines

* **A UTF-8 BOM in a .vex file is a fatal parse error** ("Unknown token"). PowerShell
  `Set-Content -Encoding UTF8` writes one. Write the file with
  `[System.IO.File]::WriteAllText($p, $t, (New-Object System.Text.UTF8Encoding($false)))`.
* No 2-D array literals: `int f[6][4] = {{0,1,3,2},...}` is a syntax error. Use a flat array and
  index `f[k*4+j]`.
* `fmod` does not exist; `mod` is integer-only. Use `c % 3` / `float(c % 2)`.
* `addvertex(geohandle, point, prim)` - the third argument is the PRIM index, not a position. You
  must `addpoint()` first, then `addvertex(0, pt, -1)`.
* Prefer `setpointattrib` over `setvertexattrib`: the vertex overloads are a minefield, and each
  generated box owns its own points anyway.
* Brace literals inside expressions can fail to parse (`{0,1,0}`) - use `set(0,1,0)`.
* `push()` is ambiguous - assign to a typed local first, then push.
* `pr.attribValue("group")` THROWS on a prim with no group. Write your own prim string attribute
  (`element`) and read that; the gate reads `element`.
* Report every node error immediately after the cook. A single failed wrangle silently empties
  every downstream output, and the HDA still "cooks".

### 12.4 Houdini Engine for Unreal - the boundaries

* **A commandlet does NOT cook.** `-run=pythonscript` loads the map and the actors are there, but
  the plugin's cook never runs (no editor tick). A headless check can only READ the editor's log.
* **UE rotates `Saved/Logs/BS_GodFile.log`** every time a second Unreal process starts, so the
  editor's live log may be `BS_GodFile_2.log`. A log-reading tool must scan every log in
  `Saved/Logs/` and keep the NEWEST cook line per actor.
* **A check that finds no evidence must FAIL.** Mine reported "all OK" when it had found zero cook
  lines. That false green is the worst possible outcome; make "no evidence" a hard failure.
* **`Tools/Editor/poitou_he_cook_check.py`** is that check: it reports each Houdini actor's cook
  result (`FinishedCooking.` vs `... with errors`). Run it AFTER the owner cooks.
* **One new HDA output = one new output slot on the UE-side Houdini Engine asset**, which is an
  editor operation. So the generated elements ship as ONE merged output (`output_generated`),
  tagged by prim group and material - not one output per element.
* The Houdini Engine asset exposes **no editable properties to Python** (every candidate fails
  with "Failed to find property"), and there is no Python-callable reimport. You cannot re-embed
  an HDA headlessly.
* `unreal.SystemLibrary.delay()` needs latent info and does not work in a commandlet - use
  `time.sleep`.
* Copying a `static_materials` element ALIASES it: mutating the "copy" mutates slot 0. Build new
  slots with `unreal.StaticMaterial()`.
* `unreal.load_asset` on a missing path returns None; `pr.attribValue` on a missing attribute
  raises. Guard both.

### 12.5 The kit, and what is already built

`Tools/Poitou/snip/kit.vex` is the shared grammar and every generator includes it:
`kit_box`, `kit_wall_stone`, `kit_wall`, `kit_arch`, `kit_buttress`, `kit_slope`, `kit_gable`,
`kit_ribbon`, `kit_taper`, `kit_faux_mask`. It fixes the canon's constants: 0.6 m module and
course (1 beat), 2.4 m bay (1 bar), 14.4 m = 6 bays, 0.45 m ashlar leaf over 0.9 m rubble core, a
chaine/arase band every 3 courses through the full thickness, a rusticated refend base, 2 cm dry
joints, semicircular arches only, and the vertex paint convention R=lime-wash G=damp B=moss A=ivy.

Shipped generators, all gated by name (18 element groups): `revet.vex` (canal-du-Midi section,
329,439 prims), `abbey.vex` (Maillezais: 7-bay nave, 1080 westwork, narthex, gallery on belt
arches, splayed buttresses, apse, gable roof), `found.vex` (soubassement under every house),
`lane.vex` (2.4 m ribbons with kerbs that dodge the houses), `cross.vex` (deck, parapet, piers -
the old receipt had none), `roof.vex` (low-pitch canal tile), `poplar_gen.vex` (tapering trunk +
columnar crown). **596,382 generated prims.** The near poplar rows still instance the hornbeam
until the generated poplar is wired to the level.

### 12.6 What the gate does NOT check yet - the real gap

The gate asserts **emission**: outputs cook, instances are in-theme, divisors match measured
meshes, every named element group is present, every material is a project material. It does NOT
assert **placement or appearance**. A generator can emit the right number of prims in the wrong
place and the gate stays green. That is exactly how tonight's work was allowed to look finished.

**The next gate must assert placement**, headlessly:
* the revetment's minimum distance to the canal centreline curve, and its height band against
  `ign_water`;
* the abbey's footprint against the canon centre (830, 870) and its rotation against `abbey_rot`;
* the crossing count within a band, and that each crossing's deck actually spans a canal;
* the roof pitch in degrees per house, against the canal-tile pitch;
* the lane width (2.4 m) and the lane's clearance from every house footprint;
* the poplar's crown aspect ratio (columnar, not broad) and its height band 25-35 m;
* and, once the owner has the editor open, **one screenshot from the P0 route's approach** -
  the abbey silhouette over the canal. Numbers prove the maths; the picture proves the world.

### 12.7 The UE-side work that needs the editor (and only the editor)

1. **Cook the level's Houdini actors** (the plugin's `Temp/` scratch was cleared and the failing
   cook must re-run), then `poitou_he_cook_check.py` must report `Poitou_Layout_v6: OK`.
2. **Add two output slots** to `poitou_layout_live_v6.uasset`: `output_masonry` (the revetment) and
   `output_generated` (the element set).
3. **Bind the 8 new MIs** to the meshes, as an owner-approved step (Jev: new assets only until
   then).
4. The toon master does not read the vertex **A** channel yet, and has no faux-appareil input -
   a material edit, which is ask-first (`Content/Materials/` is on the never-touch list).

### 12.8 The backlog, in priority order

P0.1 `house.vex` (wall, round-arched tufa door surround, oak door, shutters, chimney) - the 105
village houses are one instanced mesh with no generated detail. P0.2 `church.vex` (nave, porch,
bell tower, slate spire). P0.3 `door.vex` (the door and the fence - the last elements with no
in-theme equivalent; both become masonry). P1.1 `quay.vex` (the maison eclusiere, 11-12 x 7-8 m,
and the quay walls). P1.2 `jetty.vex` (tarred-oak pilings, the "black keys"). P1.3 `bank.vex`
(steps to the water, mooring rings). P2.1 `reed.vex`. P2.2 `ivy.vex` (the A channel). P2.3
`quoin.vex`. P3.1 `clos.vex` (the walled garden, fig trees, vine rows). P3.2 `boat.vex`. P3.3
`bird.vex` (the AE layer already exists). P4 the faux-appareil mask writer.
Each one must earn a named group in the gate. Full table in section 11.2.
## 13. THE UPDATED PLAN - what the frontier model does next (2026-10-21)

Jev audited the programme against its original goal and this contract's own reference docs
(receipt `Saved/Audit/PoitouConvergence_20261020/JevPoitouProgrammeAudit_20261021.json`, packet
`Tools/Poitou/jev_poitou_programme_audit_20261021.py`). Its rulings are the order below.

| Jev question | ruling |
|---|---|
| canals | `PARTIAL_NEEDS_LOCKHOUSE_JETTY_AND_STEPS` |
| house foundations | `SHALLOW_NEEDS_REAL_FOUNDATION_TYPES` |
| brick generation | `NEED_BOND_AND_RUBBLE_CORE_PATTERN` |
| priority order | `WIRE_AND_PROVE_FIRST_THEN_SPEC_FEATURES` |
| reuse vs bespoke | `REUSE_EXISTING_SYSTEMS_FIRST` |
| poplar + toon-master conflict | `CHECK_THE_MASTER_SHADING_MODEL_FIRST_THEN_DECIDE` |
| palette authority | `STYLE_CONTRACT_IS_AUTHORITY_REWRITE_THE_MIS` |

### Stage 0 - the owner, in the editor (~10 min). Nothing else is visible until this happens.

Cook the level's Houdini actors (the plugin's scratch was cleared and the failing cook must
re-run), add two output slots to `poitou_layout_live_v6.uasset` (`output_masonry`,
`output_generated`), and cook. `Tools/Editor/poitou_he_cook_check.py` then prints
`Poitou_Layout_v6: OK` or it does not. **That is the proof, and it is one line.**

### Stage 1 - wire, prove, and make the gate assert PLACEMENT (Jev: WIRE_AND_PROVE_FIRST)

1. **Emit the spec'd attributes on every generated prim.** The HE convergence spec gives the
   exact VEX and the generators emit none of it:
   `s@unreal_material` (done), `i@unreal_nanite_enabled = 1`,
   `i@unreal_collision_mode = 0` (complex collision), `s@unreal_output_name = "SM_..."`. Without
   them, 596,382 prims arrive without Nanite and without collision. This is a few lines in
   `kit_box` and it is the single cheapest quality-per-hour item in the programme.
2. **Extend the gate from emission to placement.** Deterministic assertions, each a test not a
   question: the revetment's minimum distance to the canal centreline and its height band against
   `ign_water`; the abbey footprint against the canon centre (830, 870) and `abbey_rot`; each
   crossing's deck actually spanning a canal; the roof pitch in degrees per house; the lane width
   (2.4 m) and its clearance from every house; the poplar's crown aspect and 25-35 m band; and the
   Nikkie rules that are cheap to assert - albedo 0.08-0.85 linear (rule 3), a secondary landmark
   within 200 m (rule 8), vignettes <=6 m separated by >=12 m quiet (rules 5, 10), >=2 layered
   historical styles per zone (rule 18), ornament scale 1.3-1.5x (rule 13), the abbey readable
   from >=70% of the walkable area (rule 7 - the HDA's own sightline check already reads 93.9%).
3. **One screenshot from the P0 route's approach** (the abbey silhouette over the canal, and the
   canal leg with its revetment). Numbers prove the maths; the picture proves the world. This is
   the step the last session skipped, and it is why 596,382 prims have never been judged.

### Stage 2 - the three original goals, done properly

4. **BRICK: a real bond, not a band** (Jev). The kit gains `kit_bond_course` - header/stretcher
   alternation, per-brick length and value jitter, a proper half-lap return - and `kit_rubble_core`
   replaces the plain core box with a rubble pattern (voronoi or jittered cells at the leaf/core
   interface). The chaine/arase band becomes one instance of the same bond system, not a special
   case. **This is the "brick generation" the original goal asked for.**
5. **FOUNDATIONS: real types, not one ring** (Jev). The style contract names them: the balais barn
   plinth with its half-timber wall (W 4.8-9.6, H 3.0-5.0, step drop 0.6-1.2 toward the water); the
   damp baseboard at **0.4-0.8 m** (the generator currently lays 1.2 m); the quereux variants; the
   bank steps down to the water. And the house walls get their openings - see Stage 3.
6. **CANALS: the rest of the canal-du-Midi section** (Jev). The maison eclusiere (11-12 x 7-8 m);
   the quay at **0.6-1.5 m above the water** (the generator currently runs 0.9-2.4 m); the
   tarred-oak jetty and pilings (the palette's "black keys"); the mooring rings; the duckweed
   surface on the conches.

### Stage 3 - REUSE the systems the project already owns (Jev: REUSE_EXISTING_SYSTEMS_FIRST)

7. **The lane crossings become the existing piano-walkway system**, not a bespoke generator:
   `DA_PianoWalkway_Poitou` (a variant of the existing `DA_PianoWalkway_MorningMeadow`),
   `MI_PianoKey_Poitou_Oak` / `_Tarred`, and `PCG_PianoKeyRun_2Oct` for the short footbridges. The
   style contract says this explicitly; `cross.vex` invented a parallel system and should be
   replaced, not extended.
8. **The house walls use the MEL_* builders**: `MEL_wall_straight/_corner/_with_door/_with_window/
   _multi_window/_t_join` for the quereux walls, enclos and gable fills, round arches only, never
   an ogive; `MEL_half_timber_wall` for the balais barns and the jetty sheds; `MEL_retaining_wall`
   for the quays and levees; and the `GN_PARIS_WallDetail` trim pass with the baseboard on.
9. **The village church comes from `MEL_math_gothic_cathedral` (lowered) and the `SM_Cathedral_*`
   kit**, not from a new church generator.
10. **The abbey becomes the spec'd `HDA_Poitou_AbbeyBuilder`**: an Unreal spline input 0 and a
    volume brush input 1 that crumbles the ruin where the brush is, `preview_mode` for a <45 ms
    proxy cook, `bay_count` 7-8, `wall_thickness` 1.8, `window_style` as a menu (Romanesque round /
    Early Gothic lancet / Rayonnant rose), `buttress_tiers` 3, `decay_intensity` 0.45. The
    generator as built is fixed geometry at a hardcoded centre with no brush and no decay.

### Stage 4 - the identity layer: the cheapest AAA win, and it is the "musical but French" contract

11. **The musical motif bands (style contract section 4) are entirely unimplemented and they are
    cheap**, because they ride the silhouette the kit already builds: the bay rhythm as the
    far-band metre; poplar spacing 6-7 m as the metre; bell-tower louvres reading as dark stripes;
    rail posts at bar spacing; archivolt "chords"; octave dark boards on the bridges; organ-pipe
    louvre gradation; and in the near band, carved capitals, corbel musicians, ironwork shutter
    hinges as clef scrolls, and door knockers. **This is half the art direction and it is the
    cheapest thing left.**
12. **Nikkie rule 13, ornament scale 1.3-1.5x** on buttress finials, lamps and flowers; **rule 8**,
    a secondary landmark within 200 m of any point; **rule 10**, vignettes within 6 m separated by
    >=12 m of quiet; **rule 18**, >=2 layered historical styles per zone (the Romanesque/Gothic
    stone ruin with the later timber and marsh houses).

### Stage 5 - materials, in Jev's order

13. **Check `M_Master_Toon_Universal`'s shading model FIRST** (Jev). Nikkie rule 2 forbids unlit
    toon on environment, and the whole material programme is MIs of that master. If it is unlit,
    every Poitou surface is wrong and the 8 MIs need a different parent - that decision changes
    the material work, so it comes first.
14. **Rewrite the 8 MIs to the STYLE CONTRACT palette** (Jev: the contract is the authority). The
    contract and the MA proposal differ by 2-4% per slot: lime wash #E9E3D3 (not #E6DFCC),
    limestone quoin #D8CBAE, roof tile #B56A4A, shutter green #8FAE9B, tar #2A2622, moss #5E6B3A,
    oak #A88D6A. The MIs stay UNBOUND until the owner approves the binding.
15. **The master must read the vertex A channel (ivy) and a faux-appareil joint mask.** That is a
    material edit - ask-first, `Content/Materials/` is on the never-touch list. Until then the
    kit's `kit_faux_mask` writes attributes nothing reads.
16. **Decide the poplar** after 13: if the master is lit, keep the generated poplar as the hero
    (rule 9 says foliage is PCG-only, so the far bands should go back to PCG and the near row
    becomes the hero).

### Stage 6 - the spec'd HDA suite and the lookbook

17. **Dual-stage cooking**: `preview_mode` for a <45 ms proxy and a production Nanite bake
    (800-1200 ms). Without it the editor cannot iterate the level, which is the whole point of
    the live convergence spec.
18. **PDG/TOPs offload** for heavy variation (20 crumbled-buttress variations, randomised stone
    piles) so the viewport never blocks.
19. **The lookbook is unfinished**: 6 of the 7 `poitou_board` plates fail the repo's own lookbook
    gate, and Nikkie rule 16 wants a weekly benchmark against 3 locked reference frames. Fixing
    the plates is what lets the next agent judge its own output.

### 13.1 What a frontier model can do with this that the last session could not

* **Hold the whole system at once**: the kit, the seven generators, the gate, the style contract
  and the Nikkie rules, and see that a new element is a small delta on a tested kernel rather than
  a new art pipeline.
* **Do the placement maths and the visual judgement**: the last session could prove that 596,382
  prims exist and could not say whether they look like a Poitou canal. That is the gap the
  placement assertions and the one screenshot close.
* **Say what is wrong with a picture**: the lookbook plates and the reference board are the
  benchmark, and a model that can read them against a frame is the difference between "gated" and
  "finished".
* **Keep the discipline**: additive only, no content mutation, no removal before the replacement
  is live, a check that fails on no evidence, and the owner's editor never touched.
## 14. THE LIVE-UE / Houdini research, and the staging pipeline that lets a frontier model burn its whole quota on CONTENT (2026-10-21)

Researched against SideFX docs and the 22.0 changelog on 2026-10-21. This section is what makes
section 13 executable without an editor: the point is that a frontier model can author a dozen
generators, gate them, and stage them, and the owner does ONE cook at the end.

### 14.1 The environment: what our Houdini build already has, and what an upgrade would buy

**CORRECTION (2026-10-21, later the same day): an earlier draft of this section claimed our build
"predates UE 5.8 support by two patches". That was wrong, and it is corrected here because the
next agent would otherwise act on it.** The workstation runs **Houdini 22.0.368**. SideFX added
Unreal 5.8 support in **22.0.355** (2026-06-18), and 22.0.368 is **thirteen patches newer**, so
**we are already past the UE 5.8 support line** and past the 22.0.359 fix for the UE 5.8
collision-preset crash. The installed plugin is **HEU 3.0 built for H22.0.368**
(`Plugins/HoudiniEngine/HoudiniEngine.uplugin`: `VersionName: 3.0 - H22.0.368`) - paired and
correct. **No upgrade is needed to make UE 5.8 work.**

What we genuinely lack is everything dated AFTER our build:

| build | date | what it fixes for us |
|---|---|---|
| 22.0.355 | 2026-06-18 | **UE 5.8 support at all** |
| 22.0.359 | 2026-06-22 | crash when the UE 5.8 plugin shows collision presets |
| 22.0.371 | 2026-07 | the plugin stopped loading `.hdalc`/`.hdanc`/`.otl` files - **we build `.hdalc`** |
| 22.0.401 | 2026-08 | nanite meshes get incorrect data when the same mesh is used in two HDAs with different Nanite settings; cooks are cancelled if a parameter is edited mid-cook |
| 22.0.470 | 2026-10-11 | **landscape spline assertion in Unreal 5.8**; a UI stall with Session Sync; PCG outputs not re-used between cooks; **a LOCK feature for Houdini Asset Components** |
| 22.0.471 | 2026-10-12 | `unreal_pdg_asset` to skip the PDG scan on large HDAs; a toggle to stop automatic cooks when an HDA is modified inside Session Sync |

The plugin releases track the Houdini build exactly: **HEU 4.0.3 = Houdini 22.0.566, HEU 4.0.2 =
22.0.459, HEU 4.0.1 = 22.0.429** - all shipping UE5.8 binaries, all on **HAPI 9.0**.

**Recommendation, in proportion to what it buys:** **do not upgrade tonight.** An upgrade means
reinstalling Houdini, bumping the plugin, and re-validating a working pipeline on a machine with a
live editor, and it buys OPTIONAL things only:

| what | build | worth it? |
|---|---|---|
| the **Houdini Asset Component lock** (including lock-on-load) | 22.0.470 | **yes** - a locked component cannot be modified or cooked by accident, and that is exactly the failure this session caused |
| the UE 5.8 **landscape spline assertion** fix and the SessionSync UI-stall fix | 22.0.470 | yes, if/when we drive landscape splines and Session Sync |
| PCG outputs correctly re-used between cooks | 22.0.470 | yes if we lean on PCG |
| nanite mesh data correct when one mesh is used by two HDAs with different settings | 22.0.401 | low - we use each in-theme mesh in one HDA |
| **SideFX Labs** (needs >= 22.0.382) | see 15.2 | only if it earns its place against our own implementation |

**If and when the owner does it:** the Launcher has **Houdini 22.0.466 already staged locally**,
22.0.466 is an exact Labs tag, and the matching plugin releases are **HEU 4.0.2 (Houdini 22.0.459)**
or **4.0.3 (Houdini 22.0.566)** - take the one whose HAPI matches the Houdini build, and install
Labs from the public GitHub tarball for that exact tag. Do it in a planned window with the editor
closed, not mid-session.

### 14.2 Session Sync is the live workflow - and it is what makes CAD-like work possible

`Houdini Engine > Open Houdini Session Sync` (or connect to a running Houdini) gives a **live
session with a Houdini GUI**: HDAs, inputs, curves and outputs synchronise **both ways**, so a
change in Houdini appears in Unreal and vice versa. The documented use case is precisely ours:
*"you kitbash a building in Unreal, you can then bring them into Houdini to build interiors, add
building parts, re-UV it... the ivy tool case - the iterations to the tool would require constant
back and forth; instead send the assets from Unreal into Houdini to iterate the tool while
retaining the context of the assets."*

Two settings matter: **Sync With Houdini Cook** (keep the assets synced with cook changes) and
**Cook Using Houdini Time** (otherwise the viewport goes out of sync with the cook).

**This is the workflow the P0 walk wants:** the canon curves (canal, route, lanes) are **Unreal
splines**; the HDA consumes them as input; the designer moves a spline point in the viewport and
the masonry re-courses in place, in seconds, with the Houdini window open beside Unreal.

### 14.3 The attribute set the kit must emit (from the official attribute table)

The generators currently emit `unreal_material` only. The spec'd set, all of it cheap:

| attribute | type | why it matters here |
|---|---|---|
| `unreal_nanite_enabled` | int | without it 596,382 prims arrive with NO Nanite |
| `unreal_nanite_position_precision` | int | 0.6 m masonry wants coarse precision, not the UE default |
| `unreal_nanite_percent_triangles` | int | and the trim/fallback relative error pair below |
| `unreal_nanite_trim_relative_error` / `unreal_nanite_fallback_relative_error` | float | the 2 cm dry joints are below Nanite's default error - they will be eaten unless the error is tightened |
| `unreal_output_name` | string | names the generated mesh, so a bake lands as a named asset |
| `unreal_collision_mode` | int | 0 = complex collision; the revetment and the abbey need it |
| `unreal_uproperty_*` | any | **the generic UProperty channel**: the HDA can set ANY property on the generated component, and on the Houdini Asset Component itself (e.g. `i@unreal_uproperty_bUseOutputNodes = 1`) |
| `unreal_output_curve` (+`_linear`, `_closed`) | int | a curve prim with this set outputs as a **SplineComponent** - the CAD-like return path: the HDA can hand a wall run back to Unreal as an editable spline |
| `unreal_output_dynamic_mesh` | int | 22.0.470 experimental: output as a **Dynamic Mesh** instead of a static mesh - a live-editable generated mesh in the editor |
| `unreal_level_path` | string | bake outputs to a named level (supports string tokens) - **the staging lever** |
| `unreal_bake_folder`, `unreal_bake_actor`, `unreal_bake_actor_class`, `unreal_bake_outliner_folder` | string | where a bake lands and under what actor/class - **the staging pipeline** |
| `unreal_landscape_output_mode` | int | 0 generate, 1 modify an edit layer on the existing landscape |
| `unreal_landscape_layer_info` | string | point a heightfield mask at an existing LayerInfo - the landscape layers the Poitou masks already have |
| `unreal_landscape_section_size` + `unreal_landscape_sections_per_component` | int | the landscape's tile budget |
| `unreal_landscape_partition_grid_size` | int | **world partition** - the level has an HLOD/near-150-mid-800-far>800 band plan (Nikkie rules 5, 6) and this is the attribute that drives it |
| `unreal_pdg_params` | - | makes the HDA output PCG data instead of Unreal objects; the PCG HDA node syncs parameters, inputs and outputs |

**PDG**: the HDA PCG node merges all outputs into one stream, each internally tagged `output_0`,
`output_1`; downstream PCG nodes isolate them with **Filter Data By Tag**. If an HDA modifies an
existing landscape, enable **Ignore Landscape Tracking** on the PCG Component or UE will build a
dependency loop.

### 14.4 The CAD-like architectural systems SideFX already ships - adopt, do not re-author

* **SideFX Labs "Building Generator 4.0"** (`labs--building_generator-4.0`): *"converts simple
  blockout geometry into detailed, modular buildings... slices them into floors, identifies
  structural regions such as walls, corners, and ledges, and replaces those regions with
  high-resolution modules sourced from a user-defined module library."* Floor Overrides, full floor
  height, wall-face modules, concave/convex corner modules, top and bottom ledges, sideslop
  modules. **This is the CAD-like loop the project wants: a blockout becomes a building.** The
  module library can be the style contract's `MEL_wall_*` set, and our `house.vex` becomes a
  configuration of it rather than a new generator.
* **"Procedural building from modules"** (SideFX tutorial, 2025-04-08): dynamic instantiation sized
  for Unreal, point-cloud transfer, corner and roof adjustment, door modules.
* **Project Titan / Titan Evo** (2022, and the 2026-10-08 tutorials): the production reference for
  exactly our elements - the **bridge** tutorial (main arch, supporting structure, deck,
  railings, platforms, chains, gears; each part a flexible system; then trim sheets and tileable
  materials for UE5) is the canal crossing and the parapet; plus Building, Fence, Platform,
  Scaffold, Stacking, Cables, Pipes, Foliage, Lamps.
* **"City Building with OSM Data"**: OSM in, buildings/roads/props out, points carrying attributes
  for UE instancing. **The Poitou canal and lane network could be driven from real data** the way
  the IGN RGE ALTI DEM already is.
* **Copernicus Baker / Pre Process Baker** (2026-10-08): bake high-resolution detail into texture
  maps and drive a layered procedural material - the route from our 2 cm dry joints and vertex
  paint to a real trim-sheet material.
* **Project Vitruvius** (SideFX, upcoming): architecture and urban environments. **Project Dryad**:
  procedural environments. Watch both; do not wait for them.

### 14.5 The staging pipeline - why a frontier model needs no editor at all

**The insight that makes the whole quota usable: every generator writes into the EXISTING merged
outputs.** `output_generated` already exists in the HDA and already carries 18 named element
groups. A new generator adds a new group, not a new HDA output - so **SOL never needs an editor
slot, never touches the UE asset, and never touches the level.** The owner does one cook at the
end and the whole set appears.

The pipeline, in order, per generator:

1. **Author** `Tools/Poitou/snip/<name>.vex`, including `snip/kit.vex` in its snippet. Git only.
2. **Wire** it into `Tools/Poitou/build_poitou_hda.py` as one more wrangle into the existing
   `merge_generated_elements` node. Git only. **No new output index.**
3. **Name its group** and add that group to `REQUIRED_GENERATED_GROUPS` in
   `Tools/Poitou/poitou_intheme_gate.py`. Git only.
4. **Build + gate** headlessly: `Tools/Poitou/run_intheme_gate.ps1 -Build -Measure`. The gate
   fails if the group is missing, if a material is not a project material, or if an instance's
   divisor does not match its measured mesh.
5. **Stage**: the generator's output name and bake folder are set by the attributes in 14.3, so the
   owner's single cook produces named, bake-ready assets under
   `Content/HoudiniEngine/Bake/<HDA>/<group>/`, ready to `p4 add` as a batch. **Baking is what
   turns a generator into staged content, and it is the only step that needs the editor.**
6. **Perforce**: the bake folder and the new material assets are added in one changelist; the
   generator sources are git. The 8 MIs are still unbound until the owner approves the binding.

**The generator contract card.** Each generator gets a card so that no context has to be re-derived
(the card is the whole point of this section - the next model reads the card, not the canon):

```
NAME            : <file>.vex            KIT FUNCTIONS : kit_wall_stone, kit_arch, ...
GROUPS          : <group names the gate must see>
OUTPUT          : merged into output_generated (never a new output index)
MATERIALS       : <existing project material paths only>
PARMS           : <the parms it reads, and their defaults>
ACCEPTANCE      : the gate line it must satisfy, and the placement assertion it must pass
DO NOT TOUCH    : existing Content assets, the level, the UE-side HDA asset, the owner's editor
TRAPS           : the axis rule, the VEX landmines (section 12.3), the attribute set (14.3)
```

**And the standing safety rail that this session lacked:** once the owner is happy, **lock the
level's Houdini Asset Components** (22.0.470 added the lock, including lock-on-load). A locked
component cannot be modified or cooked by accident, which is exactly the failure this session
caused.

### 14.6 What a frontier model should be given, and what it should not be asked to rediscover

**Given, read-only, in this order:** contract section 12 (traps + the measured size table) ->
section 13 (the ordered plan) -> this section -> the one card for the generator it is building.
**Not to be asked to rediscover:** the axis rule, the VEX landmines, the palette authority (the
style contract wins), the additive-only rule, the fact that the level's cook is a separate fact
from the Houdini-side gate, and the fact that the previous session's 18-mesh mutation was the
outage.

**Where the frontier model's advantage actually is, and it is not in writing VEX:** the placement
maths (is the abbey where the walk sees it, is the revetment on the canal, does the lane dodge
the houses), the visual judgement against the lookbook plates, and holding the style contract, the
Nikkie rules and the kit in mind at once. The VEX is the cheap part; the last session proved that.
## 15. VITRUVIUS, DRYAD, AND SIDEFX LABS - what is real, what is not, and what we can do tonight (2026-10-21)

### 15.1 Correction first: Vitruvius and Dryad are NOT tools

I named them last section as if they were usable. They are not, and the honest position is:

* **PROJECT VITRUVIUS** - *"an **upcoming toolset** designed to enhance procedural workflows for
  creating architecture and urban environments in Houdini. It provides tools for generating and
  customizing buildings, cities, and other architectural structures."* It is a **SideFX Labs
  research initiative**, not a shipped tool. A SideFX intern at Pixar (2023-2024) "researched,
  planned, and prototyped architecture generation tools for Project Vitruvius"; a 2024 EPC workshop
  covered "Road Networks" and "project VITRUVIUS from SideFX Labs". **There is no release, no
  package, and no ETA. It cannot be used tonight and should not be planned against.**
* **PROJECT DRYAD** - *"an **experimental initiative** focused on advancing procedural workflows for
  creating natural environments... detailed landscapes, forests, and terrains."* Same status:
  **an initiative, not a tool.** Also not plannable.

**Do not put either in a plan.** If a frontier model sees "Project Vitruvius" in a brief and
assumes it is an installable tool, it will burn quota chasing a thing that does not exist. The
realisable version of the same idea is **SideFX Labs' shipped toolset**, which already contains
the building/city/road workflow.

### 15.2 What IS real: SideFX Labs, and why it cannot be installed on our Houdini tonight

`sideeffects/SideFXLabs` is **public** (1,251 stars, default branch `Development`, **1.53 GB** of
source, last pushed 2026-10-21) and is released **per Houdini build**, e.g.
`https://github.com/sideeffects/SideFXLabs/tarball/refs/tags/22.0.466`. **No SideFX account is
needed for the GitHub route** (the account is only needed for the Launcher's package install).

**The blocker is version-locking, not access.** The oldest 22.0.x tag is **22.0.382**; there is no
22.0.368 tag (our build), and **Houdini refuses to load an HDA saved by a newer Houdini**. So
Labs cannot load on 22.0.368 - it would need 22.0.382+.

**And the good news is that the same upgrade we already want fixes this.** The Launcher's product
folder shows **Houdini 22.0.466 already staged locally** (with `houdini_installer.exe` and
`hserver.iso`), and 22.0.466 is:
* **past the UE 5.8 support line** (22.0.355, 2026-06-18) - and
* **an exact Labs tag** (22.0.466), and
* matched by a plugin release (**HEU 4.0.2 = 22.0.459, 4.0.3 = 22.0.566**; take the one whose
  HAPI matches).

**One owner action unlocks three things:** install Houdini 22.0.466+ (or 22.0.471+ for the UE 5.8
landscape-spline fix and the Asset-Component lock), the matching Houdini Engine plugin, and
SideFX Labs for that exact build from the public GitHub tarball. It is a machine-level change
with the owner's editor live, so it is the owner's call and needs a quiet machine - not something
an agent should do unasked.

### 15.3 The CAD-like pattern we can implement in OUR kit tonight, with no install

The point of Labs is not the code, it is the **pattern**, and the pattern is free to copy:

> **Building Generator 4.0:** *"converts simple blockout geometry into detailed, modular
> buildings. The node analyzes incoming building volumes, slices them into floors, identifies
> structural regions such as walls, corners, and ledges, and replaces those regions with
> high-resolution modules sourced from a user-defined module library."*
> Its parms: full floor height, seed, simple ledges, **facade module pattern**, **concave/convex
> corner modules**, **top ledge**, **bottom ledge**, **sideslop module**, and **floor overrides**.

**Our module library already exists**: the style contract's `MEL_wall_straight / _corner /
_with_door / _with_window / _multi_window / _t_join`, `MEL_half_timber_wall`,
`MEL_retaining_wall`. So the kit can grow the same shape - a **module pattern per wall type**,
corner resolution, ledges, and floor overrides - and the generator becomes *configuration* rather
than invention. That is the CAD-like loop: a blockout (a house footprint) becomes a building.

**This is the version we can build tonight, with zero installs and zero version risk**, and it is
the same decision Jev already made (`REUSE_EXISTING_SYSTEMS_FIRST`). When Houdini is upgraded,
the Labs Building Generator can be dropped in behind the same interface if it earns its place.

### 15.4 The same for the other two references

* **"City Building with OSM Data"** (SideFX): OSM in, buildings/roads/props out, points carrying
  attributes for UE instancing. **The Poitou canal and lane network could come from real data** the
  way the IGN RGE ALTI DEM already does - and OSM needs no account and no install.
* **"Procedural building from modules"** (2025-04-08): dynamic instantiation sized for Unreal, a
  point cloud for the transfer, corner and roof adjustment, door modules.
* **Project Titan / Titan Evo** and the **2026-10-08 bridge tutorial** (main arch, supporting
  structure, deck, railings, platforms, chains, gears; each part a flexible system; then trim
  sheets and tileable materials for UE5): that is the **canal crossing and the parapet** -
  Titan's **Fence** and **Platform/Fence** tools are the same shape as our missing `fence`/`door`
  elements.
* **Copernicus Baker / Pre Process Baker**: bake the high-resolution detail into texture maps and
  drive a layered procedural material - the route from our 2 cm dry joints and vertex paint to a
  real trim-sheet material.

### 15.5 The honest "tonight" list, in order

1. **The owner cooks the level and adds the two output slots** - nothing else is visible until
   that happens, and it is the only step that needs the editor.
2. **CARD 1: the brick bond + the rubble core** (`Tools/Poitou/GENERATOR_CARDS.md`) - the first
   real gap in the original goal, and it makes every wall in the level better at once.
3. **The attribute set** (section 14.3) - Nanite plus the trim relative error, or the joints get
   eaten; `unreal_output_name`; collision mode; and the bake attributes so the output stages.
4. **The module-library pattern in the kit** (15.3) - the CAD-like loop, ours, no install.
5. **The placement assertions and one screenshot** - so the work is judged, not just counted.
6. **Then** the Houdini + plugin + Labs upgrade, as an owner action on a quiet machine, and only
   if Labs then earns its place against our own implementation.

## 16. Salon HDA convergence and floral water sigils — owner direction 2026-10-22

**Execution order: Hython first.** This expands the existing plan using the original house boards, Soubise Salon references, current RoomShell and native bake pipeline. Implementation proof and exact continuation live in CURRENT_STATE.md, not this design section. The 21:50 House transfer recorded there supersedes earlier scene census dates in this dated review.

Review and implementation plan · October 22, 2026 · America/Toronto

The strongest path to P0 is to **extend the surviving room-shell HDA, preserve the assembled house, and converge the actual bedroom-to-canal journey around stable architectural interfaces**. Begin in Hython, where the canonical asset already cooks cleanly, and reconcile its source with the newer saved level before any replacement bake. The present generator supplies the shell, ornament, a medallion, and existing socket/gate metadata; it needs reliable openings, geometry identities, verified UV/trim policy, material bindings, and assembly contracts before broader architectural variation. The design should develop an oval, partly two-storey salon with curved boiserie, a partial gallery and framed stair, an off-centre instrument, and a terrace-to-canal view, without requiring every future room to close P0. Floral magic, water sigils, pearl, wet glaze and selective gold should replace neutral Chladni grids as the art recommendation. Optional Labs/Titan tools earn their place through small native trials; they do not become dependencies for the playable house. **Hython success, a saved map, and an incremental Editor build are separate evidence tiers: P0 remains open until the route survives real input, reload, and a current package.** ([Native findings](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json), [landscape, level and build review](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json))

### Preserve the house and reconcile three conflicting records

The operative house is `/Game/Melodia/Levels/Opening/L_MelusinaHouse_P0`, with the latest measured project evidence on C: and a complete, dirty portable twin on G:. Neither checkout is disposable. The house map was saved on **October 22 at 21:05 EDT**, after the available scene packets; current Perforce readback finds house revision 4/head change 305 open in default and Poitou revision 2/head change 288 open in change 303. No Unreal Editor process was running during this review, so the current house cannot be described as freshly inspected in-editor. The existing level is the artistic authority, while creation manifests document how things were made. Regeneration must preserve owner placements, transforms and material overrides. `CURRENT_STATE.md` remains the sole status authority; this section is the requested implementation plan; current proof and queue remain in CURRENT_STATE.md. ([State evidence and ownership](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json), [house state authority](<C:/EnvironmentPortfolio/BS_GodFile/Docs/Production/HOUSE_P0_STATE_2026-10-22.md>))

The key reconciliation is dimensional. The clean Hython fixture is **15.36 × 11.52 × 7.20 m**, the older SceneContext records a Salon shell AABB of **15.90 × 12.06 × 7.60 m**, and a conflicting dressing creation record describes a **13.58 × 18.35 × 5.63 m** Salon output. These values represent different bounds, records and configurations; none authorizes replacing the saved map. The creation record was generated before the scene packets, although its file was modified later. Start by reading the latest actor parameters, actor matrix, baked mesh identities and world bounds, then identify the intended enclosure and author its reference fit from that state. ([Native fixture](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json), [record chronology and dimensions](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json))

| Existing system | Keep and extend | Required convergence gate |
|---|---|---|
| `melodia::room_shell` | Surviving canonical shell, ornament, medallion, `sockets_json`, `gate_json`; one public output | Reconcile the actual Salon instance; explicit openings, verified planar UVs/trim policy, material roles and collision |
| House assembly and author placements | Existing bedroom, landing, Salon, interactables, dressing and newer saved scene | Create-only additions; reviewable transform/output diff before replacement |
| HouseGardenVista landscape | Local exterior stage, measured about 79.69 m square in saved evidence | Fresh door/terrace/ground/water contacts and one usable overview |
| Poitou outputs | Existing Hython landscape, route, water, masonry and architecture | Current UE cook, capsule traversal, map-travel seam and persistence |
| World Compiler, fill and runtime owners | Existing assembly, PCGEx fill, musical consumers, travel and interaction infrastructure | Pass richer data into these systems; introduce no duplicate compiler, scatterer or harmonic driver |

The landscape scales also require explicit treatment. The house’s saved garden terrain covers roughly **79.69 × 79.69 m**, while Poitou’s saved packet contains two **1 km square** tiles with a 200 m AABB gap between them. That gap is a measurement, not an established traversal fault. Treat house and regional terrain as separate stages until the travel/streaming owner, target spawn and route coverage are read back. Establish floor datums, terrain contact heights, waterline and facing at bedroom–landing, landing–Salon, Salon–terrace, terrace–garden, and the house–Poitou seam. Retain the **0.6 m beat / 2.4 m bar / 128 BPM** grammar for architectural rhythm; it does not justify globally rescaling the owner’s house. ([Landscape measurements and Golden Walk scope](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json))

### Stable interfaces let richer architecture remain playable

The first Hython change should make connected architecture reliable. The inspected definition exposes one randomly selected door, and a controlled width change from **15.36 to 16.80 m** moved its centre from **5.76 to 9.60 m** along an unchanged wall direction. Both cooks passed their embedded gates. A wider room can therefore strand a corridor without producing a generator error. Promote route-critical apertures to explicit, persistent records, while keeping legacy scalar parameters compatible for existing actors. An opening’s metadata must identify the hole actually cut; a socket hovering against solid wall is a failed output. ([Measured doorway jump and gate limits](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json))

| Contract | Concrete extension of existing data | Acceptance evidence |
|---|---|---|
| Room and part identity | Stable `room_id`, `part_id`, semantic role, source hash and output version | IDs survive seed, width and decoration changes; unrelated owner objects stay untouched |
| Openings and seams | Extend `sockets_json` with `opening_id`, wall/curve segment, centre/frame, width/headroom, floor datum, mate and route role; support multiple exits | Cut geometry and socket agree; connected endpoints remain paired through a dimension wedge |
| Coordinates | Stamp metres, source/export basis and actor-to-world matrix; preserve current `(x,z,-y)` wrapper convention | Same fixture has upward floors, correct normals and matched dimensions in Hython and UE; no double transform |
| Visual geometry and collision | Stable shell/trim/roof/walkable identities plus simplified collision and dressing exclusions | No blocked thresholds, collision on decoration, inverted faces or terrain penetrations on the walk |
| UVs and materials | Verify existing vertex planar UVs from `_uv_planar_mapping` (0.5 scale); develop shared density, trim and curved-wall seam policy; no exposed UV controls currently; resolve `material_role` to existing Unreal MIs | Checker and glancing-light review; no stretched panels or unresolved Houdini-only material paths |
| Music and motif provenance | Basis/domain/boundary, mode or authored parameters, seed, field and texture hashes, role and musical mapping | Physical plate Hz, room acoustics and artistic note identity remain separate fields |

Keep the current public output ordering intact. Stable part attributes and the existing JSON detail fields can carry this richer contract first; a multi-output HDA is a later, explicitly versioned option if the existing importer benefits from it. The current `shop_materialpath` values name Houdini materials and do not prove an Unreal binding. Likewise, aggregate positive volume and `door_clear` are useful source checks, but do not establish per-component watertightness, collision or capsule clearance. Recover an editable loose source from the surviving embedded module as a deliberate, hash-tracked source promotion before changing the canonical definition. Root-relative dependencies should replace the absolute streamer-library default through the existing project resolver. ([Native output and dependency audit](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json))

The reference-fit grammar starts with the **round pink/ivory house, three swept blue/lavender roof gestures, convex entrance, retreating shoulders and slender right tower** visible on REF_01. Reuse the owner’s existing roof ribbons and compatible hero parts. REF_02 supports separate shell, opening, roof, rail, ornament and vegetation families. REF_03 is damaged and too small to recover exact labels or a floor plan; use its broad cutaway relationship together with the recovered text. The historical master and room packet were recovered as design memory, not proof that their old builder aliases still exist. ([Reference review](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json), [original master](https://github.com/fromage3900/MelodiaMelusinaV2/blob/main/Docs/References/MelusinasHouse/OriginalDesign/melusinashouseplan_2026-09-02.md))

Inside, develop the two-storey oval Salon through **curved pale boiserie, alternating arched light bays and quieter panels, a continuous ceiling cove, an off-centre instrument and a delicate pearl/glass mobile**. The inspected Soubise photographs support that wall rhythm and open centre; Petit Trianon supports music-room intimacy and a garden terrace. Borrow their spatial principles at domestic scale. Preserve a clear lower through-route, make the partial gallery a beautiful framed vista, and show one stair without requiring a new upstairs mechanic. A bedroom-exit view should reveal the instrument or medallion, then lead toward front-door light. The slightly sunken centre is a candidate only if the measured route and accessible perimeter remain continuous. ([Official Soubise precedent](https://www.archives-nationales.culture.gouv.fr/lhotel-de-soubise), [official Petit Trianon precedent](https://www.chateauversailles.fr/decouvrir/domaine/domaine-trianon/petit-trianon), [room/acoustic packet](https://github.com/fromage3900/MelodiaMelusinaV2/blob/main/Docs/References/MelusinasHouse/OriginalDesign/MELUSINAS_HOUSE_GN_ROOMS_AND_ACOUSTIC_ARCHITECTURE_2026-09-03.md))

Expand through **gather, guide and release** templates: Salon, Bedroom, Wardrobe Rotunda, Kitchen and Blue Room gather; Listening Stair, landing and thresholds guide; Crescent Balcony, Listening Tower, windows and porch release. Include the Music/Reading Bay from the constellation as the ninth program node; the packet numbers eight wrappers, so reconcile that bay’s wrapper/ID explicitly. These templates reuse shell/opening/cove, roof/tower, rail/stair, support-surface and ornament families, with `mh_room_id`, material zones and authoring hints passed into existing assembly. The saved census’s **13 HDA actors are not nine rooms**. For P0, the lower route is mandatory; gallery, tower and unopened rooms can enrich the visible house while retaining expansion interfaces. ([Recovered room constellation and attributes](https://github.com/fromage3900/MelodiaMelusinaV2/blob/main/Docs/References/MelusinasHouse/OriginalDesign/MELUSINAS_HOUSE_GN_ROOMS_AND_ACOUSTIC_ARCHITECTURE_2026-09-03.md), [saved census](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json))

At the exterior, let the extravagant house meet a quieter wetland: limestone base, soft grassy banks, low bridges, pollarded ash, duckweed, calm conches and a legible canal landing. Fit porch supports, terrace deck and the dry route to measured terrain/water datums; retain existing canal/route/heightfield masks. Inspect a native cross-section through each contact before adding surface detail. Future PCGEx fill consumes support/exclusion surfaces and texture sampling into in-graph `$Density`; grayscale maps use the appropriate RGB/R channel. Do not copy the stale `PCGDensityData` reference. ([Landscape boards, reference fit and density correction](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json))

### Floral sigils turn shared fields into authored materials

**WaterLily should lead the Salon floor, TidalRose answer it overhead, and TwinCurrent carry the house’s water language through the threshold toward the canal.** Pearl droplets, blooming petals, shell fans and little currents provide delight at several scales: one clear hero motif, finer lace on a rail or reveal, and a release motif at water. Keep each recognisable with emission disabled; magic then blooms from an already convincing material. The new six-family native batch is an art-directed derivative of the existing analytical carrier, rather than a simulation of an oval room’s eigenmodes. ([Floral v2 manifest](../../RawArt/MelusinasHouse/Chladni/SalonFloralSigils_20261022/floral_sigil_manifest.json))

The revised batch delivers **five material maps per family—BaseColor, ORM, DirectX Normal, 16-bit Height and EmissiveMask—plus Beauty/Magic previews**, all at 1024². Six families yield 42 family PNGs plus three contact sheets: **45 PNGs total**. Readback validates file sets, dimensions and hashes, reports six distinct BaseColor hashes, all six emissive masks nonempty, and `all_pass=true`. Direct contact-sheet review confirms six different silhouettes. These are offline analytical previews of delivered textures; a real Copernicus high/low bake and UE material response remain separate gates. Height is artistic relief, not calibrated displacement. ([Texture readback](../../RawArt/MelusinasHouse/Chladni/SalonFloralSigils_20261022/texture_readback_validation.json))

![Six floral and water-sigil variants under neutral offline lighting](../../RawArt/MelusinasHouse/Chladni/SalonFloralSigils_20261022/Beauty_Contact.png)

![The same variants with their delivered emissive masks in an offline magic preview](../../RawArt/MelusinasHouse/Chladni/SalonFloralSigils_20261022/Magic_Contact.png)

| Family | Proposed role and composition | Creative surface response |
|---|---|---|
| WaterLily | Floor hero: open petal rosette, lagoon heart, pearl droplets and fine gold veins | Satin pearl petals, polished water pockets, shallow carved recesses; gold confined to veins/pollen |
| TidalRose | Ceiling counterpart: layered rose/tide curls around quiet space for the mobile | Dry ivory plaster and blue/lavender glazed channels, with small warm metal tips |
| IrisPearlLace | Gallery rail, window or threshold accent; a delicate bloom in fine lace | Pearl contacts and underlaps, glossy beads against quieter plaster/textile, rare gold closures |
| TwinCurrent | Door/terrace seal and canal link; interlaced currents with clear negative space | Wet polished channels, dry surrounding stone, narrow brass edges and separate magic mask |
| MoonTideScallop | Secondary night/porch/water-facing ornament; lunar shell rhythm | Scalloped pearl relief, lagoon recesses, selective gilded crests and a separate moon glint |
| BellflowerRipple | Intimate reading/bedroom accent or cascading ripple detail | Small blush/lavender blooms, water glints and sparse gold; simplify at distance |

Pack **ORM as R=AO, G=roughness, B=metallic**. AO supports shallow recesses and overlaps; roughness creates the expressive contrast between wet channels, satin pearl, chalky plaster and gold; metallic selects actual gold/brass areas. Water, pearl, cloth and plaster remain nonmetal. Import data textures in linear space with sRGB off, apply normal-map compression/convention, and use existing approved material controls. Emissive, iridescence and opacity remain separate from ORM. The present candidate family provides a subset of the established nine-map contract; deliver missing maps or explicitly validate the chosen material’s subset before integration. It is not a full nine-map pass. ([Map contract and sole-writer constraints](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json))

Record field basis, boundary/domain, carrier mode, authored transformations, metric domain size, UV method, role, resolution, colour space and hashes. The original square simply-supported wedge remains calibration: **three spatial topologies × two physical materials**, not six unique designs. RoomShell’s cos-difference medallion and heuristic frequency label are separate again. Actual plate frequency, room axial note and artistic musical identity must keep separate fields. The existing harmonic/cymatic consumers and sole MPC writer receive content; these textures add no beat clock or runtime authority. ([Native field distinctions](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json), [existing semantic owners](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json))

### Hython packages converge before the level changes

The native path is already available: **Hython 22.0.368, Indie**, with the historical Salon fixture cooking **40,380 points / 10,143 primitives, zero errors and warnings**. Labs Building Generator 4.0/Utility 2.0 were absent from that process’s node registry. Their official capabilities fit repetitive boiserie/window/corner/cove bays, provided explicit hero portals and oval curvature stay authoritative. Trial a three-bay solid/window/portal sector and concave/convex corners, compare UVs and transforms, and retain a native SOP fallback behind the same interface. No upgrade is required merely to plan this work. ([Native probe](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json), [Building Generator 4.0](https://www.sidefx.com/docs/houdini/nodes/sop/labs--building_generator-4.0.html), [Utility 2.0](https://www.sidefx.com/docs/houdini/nodes/sop/labs--building_generator_utility-2.0.html))

Use Titan EVO’s **bridge/platform decomposition and trim UV method** for gallery rails, crescent porch edges and one Poitou landing/crossing; use its scaffold module-table discipline for deterministic repeated pieces and artist overrides. Adopt a bounded Copernicus/Pre Process Baker canary for one real high/low plaster or shell relief before hero bakes. These are researched methods, not locally proven tools: exact definitions, representative cook and any asset-package terms must be checked first. Vitruvius remains upcoming and Dryad experimental; neither belongs on P0’s critical path. OSM city generation stays deferred while the authored route already exists. ([Titan bridge](https://www.sidefx.com/tutorials/titan-evo-bridge-modeling/), [scaffold](https://www.sidefx.com/tutorials/titan-evo-scaffold-tool/), [asset baking](https://www.sidefx.com/tutorials/project-titan-evo-asset-texturing/), [Labs availability](https://www.sidefx.com/products/sidefx-labs/))

| Ordered package | Dependency | Concrete output | Acceptance gate |
|---|---|---|---|
| A — Freeze the as-built interfaces | Existing saved house and owner source | Latest read-only room/actor/door/roof/terrain packet, source/asset hashes, protected-placement list | Resolve the three dimensional records; usable overhead, eye-height and roof views; identify travel owner |
| B — Recover and extend the canonical source | A; embedded module survives | Editable source in existing source lane; isolated candidate HDA; explicit openings, IDs, existing socket/gate schema extended | Repeatable cook and reopen; width/seed/multiple-exit wedges preserve route cuts and mate frames |
| C — Build the reference-fit kit | B | Curved boiserie/light/cove sector, UV/material zones, partial gallery/rail, framed stair, preserved roof/tower assembly | Three clay hero views and cutaway match boards; people-scale route clear; native fallback passes |
| D — Select and finish the floral family | B; new native batch | Floor/ceiling/threshold candidates, complete declared map subset, provenance and preview sheets | Distinct motifs; emission-off legibility; correct ORM/normal/UV response; chosen material contract validated |
| E — Fit exterior and expansion sockets | A–C | Supported porch/terrace/canal contacts; terrain/route/exclusion masks; nine-program template interfaces | Native sections show dry continuous route and water relationship; no global rescale or owner-prop movement |
| F — Stage one serialized UE integration | B–E; owner opens intended map | Reviewable procedural-only bake/import diff, existing-MI bindings, collision and contact readback | Matched neutral/dawn/magic-off captures opened; source hashes/bounds agree; owner layout preserved |
| G — Walk and persist the experience | F | Real-input house leg, travel seam, complete Golden Walk, interaction receipts and continuous capture | Named boundaries reached, no stuck thresholds, correct spawn/facing, exactly-once interactions, saved reload |
| H — Certify the current package | G; final assets included | Latest packaged route, collision/material/performance evidence and rows in existing ledger | Same route works from package; current output/maps cook; remaining blockers explicit in CURRENT_STATE |

Packages B–E can produce isolated Hython candidates before the editor opens; package A’s current scene reflection remains a prerequisite for replacing placed geometry. Optional tool trials support C rather than delaying B or D. Freeze accepted interfaces before broader decoration, and review one bounded visual change at a time.

### P0 closes through an actual journey and persistence

P0’s mandatory sequence is **bedroom → curved landing → lower Salon → front/terrace exit → Poitou street/crossing → conversation → canal landing/departure**. The existing Golden Walk contract targets ten minutes within **8–12 minutes**, three naive route-only testers, three transition runs, three hero stills and an uninterrupted capture. Preserve its M00–M09 interaction gates and keep the independent integration proof separate. CURRENT_STATE now records the 21:50 saved transfer of Morning triggers into House: House replaces Morning as the opening; Sir intro plus RequestTravel owns departure, the travel box is a stub, and owner-placed volumes/House travel ID remain unresolved. Preserve that newer work rather than restoring the old boot map. Read the actual house-to-Poitou travel owner and spawn/facing; a pleasing terrace sightline alone does not establish the seam. ([Golden Walk and proof scope](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json), [Golden Walk design authority](https://github.com/fromage3900/MelodiaMelusinaV2/blob/main/Docs/Plans/POITOU_P0_GOLDEN_WALK_2026-10-21.md))

The previous bedroom-to-Salon sampler recorded **221 identical positions: zero centimetres travelled**. A replacement receipt must show possessed real-input movement, meaningful path progress, arrival across named boundaries and no collision/focus trap. A proposed automated stuck flag is less than 0.1 m progress over two seconds of sustained movement input outside intentional stops; this is a candidate QA threshold to ratify, not existing canon. Pair it with capsule/contact checks at every threshold and a watched continuous run. Reopen the saved map, restart and repeat the seam, then walk the current packaged output; these are separate receipts. Compare before/after route frame time and collision cost on the target hardware, and use the project’s actual budget rather than inventing one here. ([Failed walk receipt and remaining gates](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json))

The latest observed **incremental Editor build succeeded at 21:29 EDT on October 22**, and subsequent native tests exited zero. That supports source readiness, not a full clean build, latest package or house walk. Saved house assembly evidence, fresh Hython Poitou outputs and collision candidates remain useful at their stated tiers. Useful proof now requires matched captures showing the oval room, roof silhouette and landscape contact; the old house overview was visually unusable despite successful metadata. Record measured results in the existing ledger and update CURRENT_STATE at implementation time. No new status document is required. ([Build logs, scene captures and proof limits](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json))

### Delivery boundary and next slice

The house can expand without expanding its obligations indefinitely: stable room/portal/material interfaces support all nine program nodes, while a composed lower route delivers P0’s actual experience. The next implementation slice is source recovery plus explicit apertures and one curved Salon bay, followed by the selected WaterLily/TidalRose/TwinCurrent material trio and the exterior contact pass.

The reference review and isolated native execution have now produced project-local floral bakes and the first explicit-portal candidate; recovered native and bake sources, recipes and evidence are committed. CURRENT_STATE records the exact commits, passing Hython gates and continuation commands. Current-map integration, UE material acceptance, real traversal, reload and packaging remain separate implementation gates. The revised house should earn its magic through playful material detail and a continuous journey that survives being played.

**Evidence index.** [1 — Reference and official-tool review](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json) contains inspected boards, recovered design provenance and primary URLs. [2 — Native Hython findings](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json) and [3 — actual cook report](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json) establish the current native contract. [4 — Landscape, level and build evidence](../../Saved/Audit/SalonConvergence_20261022/review_evidence.json) indexes saved scene, P4 and build receipts. [5 — Floral manifest](../../RawArt/MelusinasHouse/Chladni/SalonFloralSigils_20261022/floral_sigil_manifest.json), [6 — texture validation](../../RawArt/MelusinasHouse/Chladni/SalonFloralSigils_20261022/texture_readback_validation.json) and [7 — ORM channel sheet](../../RawArt/MelusinasHouse/Chladni/SalonFloralSigils_20261022/ORM_Channel_Contact.png) support the new bake claims.
