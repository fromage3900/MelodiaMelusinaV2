# ♬ Melusina's House — Geometry Nodes Asset-Family Implementation

**Date:** 2026-09-03  
**Discovery tokens:** `melusinashouseplan`, `Melusina house GN`, `house asset families`, `round baroque`, `pink blue architecture`, `rocaille`, `scallop shingles`, `Listening Tower`, `Blue Room`  
**Parent plan:** [`/melusinashouseplan.md`](../../melusinashouseplan.md)  
**GN taxonomy:** [`Docs/Production/GN_TAXONOMY_2026-08-29.md`](../Production/GN_TAXONOMY_2026-08-29.md)  
**Target:** Blender 5.2 / Melodia Studio / `deploy/surreal_arch/`

> **Goal:** turn the concept-sheet architecture into a modular production kit without exploding the global Geometry Nodes registry.

---

## 𝄞 The rule that keeps this sane

There are two levels of node groups:

```text
MEL_*     = reusable Melodia Studio builder
GN_MH_*   = Melusina-house-specific scene wrapper / composition
```

Use existing `MEL_*` builders inside `GN_MH_*` wrappers whenever possible.

Only promote a house-specific idea into `deploy/surreal_arch/melodia_gn/` when all three are true:

1. it is useful outside Melusina's House;
2. its inputs/outputs are stable enough to document;
3. it survives a headless builder smoke and one live Blender visual review.

This prevents one hero environment from turning the shared GN stack into hundreds of one-off operators.

---

# ♪ Existing builders we should deliberately reuse

Current taxonomy already gives us most of the structural language we need.

### Primitives / placement

- `MEL_instance_on_spline`
- `MEL_curve_array`
- `MEL_circular_array`
- `MEL_spiral_array`
- `MEL_weighted_array`
- `MEL_bounding_box`

### Profiles

- `MEL_column`
- `MEL_baluster`
- `MEL_baluster_collar`
- `MEL_post`
- `MEL_rail`
- `MEL_star_finial`
- `MEL_egg_dart_rail`

### Structures

- `MEL_arch`
- `MEL_gazebo`
- `MEL_greybox_room_kit`
- `MEL_greybox_openings`
- `MEL_music_room_shell`
- `MEL_nikki_wardrobe_nook`
- `MEL_pergola_walkway`

### Ornament / filigree

- `MEL_ornament_vine`
- `MEL_ornament_radial`
- `MEL_ornament_scallop_band`
- `MEL_decorative_rosette`
- `MEL_ornament_rosette_sixpetal`
- `MEL_ornament_keyhole_frame`
- `MEL_filigree_spiral`
- `MEL_filigree_corner_volute`
- `MEL_filigree_wreath_ring`

### Effects / water / ribbon

- `MEL_ribbon_curve`
- `MEL_closed_ribbon`
- `MEL_water_gerstner`
- `MEL_water_ripples`
- `MEL_env_waterfall_pool`
- `MEL_effect_wave`
- `MEL_radial_wave`

### Music geometry

Use the existing music family sparingly:

- `MEL_music_staff`
- `MEL_music_note_head`
- `MEL_music_treble_clef`
- `MEL_music_sheet_rail`
- `MEL_music_harmonic`
- `MEL_music_phrase`

Musical notation should be rare and meaningful, not wallpaper.

---

# ♫ Asset-family map

| Family | Scene wrapper | Existing builders to compose | New shared builder? | First proof |
|---|---|---|---|---|
| curved foundation / shell | `GN_MH_01_FoundationPorch`, `GN_MH_02_CurvedWallShell` | greybox room/openings, arch, curve utilities | no | three-bay concave/convex façade |
| flowing roof ribbons | `GN_MH_03_RoofRibbon` | ribbon curve, curve array, mesh tools | **maybe later** | one clean S-curve roof wing |
| scallop / fish-scale shingles | `GN_MH_04_ScallopShingles` | instance-on-spline, curve array, scallop band | **yes candidate** | 2×2 m curved roof patch |
| windows / doors | `GN_MH_05_WindowDoorKit` | arch, keyhole frame, radial ornament, rosette | no | 3 window variants + hero door |
| Listening Tower | `GN_MH_06_TowerChimney` | gazebo, circular array, column, star finial | no | tower silhouette + balcony ring |
| rocaille / Melusina Loop trim | `GN_MH_07_RocailleTrim` | ornament vine, filigree spiral/volute, ribbon curve | **yes candidate: loop only** | one reusable signature curve |
| railings / stairs | `GN_MH_08_RailingBalusters` | baluster, rail, instance-on-spline, spiral array | no | porch + Listening Stair proof |
| awnings / drapes | `GN_MH_09_AwningsDrapes` | ribbon curve, effect wave, tapestry concepts | maybe later | lavender awning + curtain valance |
| flowers / edge growth | `GN_MH_10_FoliageScatter` | weighted array, instance-on-spline | no | porch edge + tower planter scatter |
| interior shell | `GN_MH_11_InteriorShell` | music room shell, wardrobe nook, greybox openings | no | Salon + Rotunda blockout |
| musical ornament / response | `GN_MH_12_MusicalOrnamentPass` | music staff, note head, harmonic, phrase | no | one ceiling-score medallion |
| Blue Room / grotto | `GN_MH_13_BlueRoomGrotto` | water pool, ripples, arches, weighted scatter | maybe later | flooded arch + tide pool |

---

# 𝄞 Family A — flowing roof ribbon

## Design target

The roof must carry most of the silhouette. It should read as **one large flowing gesture** interrupted by a smaller wing and the Listening Tower, not a pile of conventional gables.

### `GN_MH_03_RoofRibbon`

Inputs:

```text
Roof Guide Curve
Half Width
Rise
Edge Curl
Thickness
Eave Drop
Sampling Density
Material Index
```

Recommended logic:

```text
Guide Curve
→ Resample Curve
→ Capture tangent / normal frame
→ generate left + right edge offsets
→ Set Position with vertical rise profile
→ bridge edges into roof strip
→ Solidify / Extrude
→ Mesh Bevel on exposed lip only
→ store mh_roof_u / mh_roof_v attributes
```

Use a smooth bell or sine profile for roof rise rather than manually moving dozens of vertices.

### Gate

Before shingles, the bare roof must already make the house recognizable in silhouette.

If the roof only becomes attractive after ornament, fix the roof first.

---

# ♪ Family B — scallop shingles

This is the strongest candidate for a reusable shared builder because the technique can serve cottages, pavilions, Sea Above structures, wardrobe roofs, and other soft architecture.

### Scene wrapper

`GN_MH_04_ScallopShingles`

### Candidate reusable builder

`MEL_surface_scallop_shingles`

Do **not** add it to Melodia Studio until the scene wrapper proves the method.

### 5.2 node strategy

```text
roof surface
→ preserve / generate UV-like coordinates
→ point grid in parameter space
→ offset every second row by 0.5 tile width
→ Sample UV Surface / equivalent surface sampling
→ sample Position + Normal + tangent direction
→ align one scallop tile instance to tangent frame
→ random scale ±3–5%
→ random hue/material slot within blue/lavender family
→ Instance on Points
```

Important controls:

```text
Tile Width          0.26–0.31 m
Tile Height         0.32–0.39 m
Row Overlap         35–45%
Row Stagger         0.5
Normal Offset       0.015–0.03 m
Variation Seed      integer
Edge Trim Distance  0.05–0.10 m
```

### Tile source geometry

Create one low-poly scallop tile with:

- rounded lower edge;
- shallow crown;
- tiny thickness;
- UV/material coordinate;
- optional pearl lip variant.

Keep instances unrealized in authoring.

### Proof ladder

1. flat 2×2 m test patch;
2. single curved roof ribbon;
3. roof seam between two ribbons;
4. hero three-quarter view;
5. export-copy test with realized instances only if required.

---

# ♫ Family C — windows, doors, shell frames

`GN_MH_05_WindowDoorKit`

We need only a small family:

```text
WIN_MH_01_TallArch
WIN_MH_02_RoundRose
WIN_MH_03_OvalDormer
WIN_MH_04_TinyTower
DOOR_MH_01_HeroEntry
```

### Build logic

```text
opening dimensions
→ MEL_arch / base frame
→ optional MEL_ornament_keyhole_frame
→ rosette / radial ornament branch
→ curve-based gold trim
→ glass inset plane
→ optional shell crest
```

Use one normalized local coordinate system so width/height/depth can vary without rebuilding each frame.

### Hero-door rule

The front door gets one stronger shell/rocaille crest and the Melusina Loop in the glass.

Other doors remain quieter.

---

# ♬ Family D — Rocaille + the Melusina Loop

The generic Rococo layer should come from existing builders.

### `GN_MH_07_RocailleTrim`

Compose:

```text
MEL_ornament_vine
+ MEL_filigree_spiral
+ MEL_filigree_corner_volute
+ MEL_decorative_rosette
+ MEL_ribbon_curve
```

The house-specific addition is a canonical curve:

```text
CRV_MelusinaLoop
```

Shape language:

```text
wave + ribbon bow + question-mark tension + treble-clef memory
```

It must **not** literally be a treble clef.

Use the same source curve for:

- front-door glass;
- one railing panel;
- bedframe;
- mirror crown;
- floor inlay;
- balcony bracket;
- ceiling-score medallion;
- garden border.

### Candidate reusable builder

Only after the motif stabilizes:

```text
MEL_melusina_loop
```

If it remains character-specific, keep it house-local and do not pollute the global registry.

---

# 𝄞 Family E — railings, stair, balcony

`GN_MH_08_RailingBalusters`

### Straight / curved balcony rail

```text
rail guide curve
→ MEL_instance_on_spline
   source = MEL_baluster / collar variant
→ MEL_rail for top rail
→ optional lower rail
→ every Nth baluster becomes a shell post / pearl post
```

Inputs:

```text
Baluster Spacing   0.30–0.34 m
Rail Height        0.90–1.05 m
Post Interval      4–7 balusters
Curve Follow       on
Loop Insert Chance 0–0.20
```

### Listening Stair

The Listening Stair wraps a hollow acoustic shaft.

```text
spiral guide
→ stair tread instances
→ outer baluster spline
→ inner handrail spline
→ occasional hanging chime points
```

Use `MEL_spiral_array` only where it genuinely simplifies the step transforms; keep the stair's visible outer rail curve artist-editable.

---

# ♪ Family F — Listening Tower

`GN_MH_06_TowerChimney`

Build it as a composition, not a new global tower generator.

```text
cylinder / rounded shaft
+ MEL_circular_array of columns or window ribs
+ MEL_gazebo logic for upper lantern
+ MEL_rail / balusters for balcony
+ MEL_star_finial or custom note finial
+ curved roof cap
```

Target proportions:

```text
Diameter         1.6–2.0 m
Visible shaft    5.8–6.6 m
Lantern height   1.5–2.0 m
Balcony radius   +0.35–0.50 m beyond shaft
Finial           0.6–1.0 m
```

### Visual job

The tower is the **release** element of the acoustic façade. It should feel narrower, lighter and more vertical than the swollen salon mass.

---

# ♫ Family G — Blue Room / grotto

`GN_MH_13_BlueRoomGrotto`

The grotto should not be generated as random cave noise. Start with architectural arches and let rock/water partially reclaim them.

### Base assembly

```text
2–3 MEL_arch openings
→ offset / scale / rotate slightly
→ stone / shell cladding branch
→ lower floor basin
→ MEL_env_waterfall_pool or custom shallow water plane
→ MEL_water_ripples
→ weighted shell / rock / plant scatter
```

Named authoring controls:

```text
TideLevel
WaterExtent
ArchSubmerge
GlowDensity
ShellScatter
RockIntrusion
```

### Story geometry

At low tide, expose another 1–2 m of floor and a lower step.
At high tide, visually erase that floor edge.

For the first asset pass this can be two authored presets, not runtime simulation.

---

# ♬ Family H — drapes, awnings, ribbons

`GN_MH_09_AwningsDrapes`

Start cheap:

```text
edge curve
→ hanging points / catenary approximation
→ Curve to Mesh ribbon
→ MEL_effect_wave subtle offset
→ lavender material
```

Only move to cloth simulation if the simple procedural shape cannot produce the visual target.

Possible later Blender 5.2 proof:

- generate procedural cloth strip;
- pin its upper edge;
- run one short relaxation simulation;
- apply result to a source mesh;
- instance/bend that baked drape shape procedurally.

Do not put a heavy simulation inside every house modifier evaluation.

---

# ♪ Family I — floral / domestic scatter

`GN_MH_10_FoliageScatter`

Use two masks:

```text
architectural edge mask
+ human-touch mask
```

Architectural edge mask places:

- ivy near grotto and porch foundation;
- small flowers at railing bases;
- moss at water-facing stone.

Human-touch mask places:

- potted flowers;
- ribbon bundles;
- shell charms;
- small domestic clutter anchors.

Keep the second mask sparse and art-directable. Melusina lives here; perfect procedural randomness is less believable than a few repeated habits.

---

# 𝄞 Family J — shell / pearl emblems

Do not make a new shell generator immediately.

First prove a house crest by composing:

```text
MEL_decorative_rosette
+ MEL_ornament_scallop_band fragment
+ pearl spheres / radial points
+ filigree corner volutes
```

Use 3 crest tiers:

```text
Tier 1 — tiny window shell
Tier 2 — balcony / dormer shell
Tier 3 — hero front-door crest
```

Only Tier 3 gets the full pearl + loop + gold treatment.

---

# ♫ Material slots / attributes

Every house wrapper should preserve simple material-zone attributes before realization/export:

```text
mh_material_zone
mh_ornament_tier
mh_room_id
mh_water_affinity
mh_acoustic_role
```

Suggested `mh_material_zone` values:

```text
0 pink_plaster
1 pearl_trim
2 powder_blue
3 roof_blue
4 lavender
5 warm_gold
6 wood
7 glass_aqua
8 water
9 stone_grotto
10 foliage
```

Use `MEL_store_named_attr` where useful, or equivalent native Store Named Attribute nodes inside the local wrapper.

---

# ♬ Build order — first serious asset session

## Pass 1 — silhouette kit · 60–90 min

1. curved wall shell;
2. main roof ribbon;
3. wing roof ribbon;
4. Listening Tower blockout;
5. porch / crescent balcony.

**Gate:** screenshot without materials must already read as Melusina's House.

## Pass 2 — repetition systems · 60 min

1. scallop shingle patch;
2. railing system;
3. three-window family;
4. one shell crest;
5. one Rocaille trim strip.

## Pass 3 — signature DNA · 45 min

1. draw `CRV_MelusinaLoop`;
2. use it in door glass;
3. use it in one railing panel;
4. use it in one floor/ceiling test;
5. reject any version that looks like a copied treble clef.

## Pass 4 — water + domestic life · 60 min

1. Blue Room arch/basin;
2. lavender drape proof;
3. planter/flower scatter;
4. warm interior window cards;
5. one domestic prop cluster.

---

# 𝄞 Promotion backlog — what may become real Melodia Studio builders

Do not implement these all at once.

### P1 candidate

```text
MEL_surface_scallop_shingles
```

Reason: broadly reusable surface-instancing pattern.

### P2 candidate

```text
MEL_curve_roof_ribbon
```

Only promote if it proves useful for more than this house.

### P3 candidate

```text
MEL_melusina_loop
```

Probably **do not** promote unless the motif becomes a wider Melodia architectural signature.

### Keep local by default

```text
GN_MH_06_TowerChimney
GN_MH_13_BlueRoomGrotto
GN_MH_05_WindowDoorKit
GN_MH_11_InteriorShell
```

They are hero-environment compositions, not necessarily reusable primitives.

---

# ♪ Evidence / validation

For each family, capture:

```text
Saved/Audit/melusinashouse/
  <family>_wire.png
  <family>_material.png
  <family>_params.txt
```

Minimum proof per GN family:

1. modifier evaluates in Blender 5.2;
2. no obvious flipped normals / exploding instances;
3. main controls exposed and named;
4. low-count debug mode exists where density is high;
5. instances remain unrealized until export requires otherwise;
6. no save over live v22 stage from agent automation.

For any promoted `MEL_*` builder additionally require:

- registered in Melodia Studio;
- headless builder smoke;
- GN Stack UI entry;
- one curated preset;
- taxonomy update;
- live visual review.

---

> **Build the house from a small vocabulary that repeats with intention. The procedural system should make the architecture feel related to itself, not merely detailed.** ♪
