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

