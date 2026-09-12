# ♬ Melusina's House — Geometry Nodes Furniture + Domestic Prop Genome

**Date:** 2026-09-03  
**Discovery tokens:** `melusinashouseplan`, `Melusina furniture`, `house props`, `Geometry Nodes furniture`, `Melusina Loop`, `bed`, `mirror`, `cabinet`, `chandelier`, `wardrobe rotunda`  
**Parent:** [`../../melusinashouseplan.md`](../../melusinashouseplan.md)  
**Phase-2 companions:** [`MELUSINAS_HOUSE_GN_ASSET_FAMILY_IMPLEMENTATION_2026-09-03.md`](MELUSINAS_HOUSE_GN_ASSET_FAMILY_IMPLEMENTATION_2026-09-03.md) and [`MELUSINAS_HOUSE_GN_ROOMS_AND_ACOUSTIC_ARCHITECTURE_2026-09-03.md`](MELUSINAS_HOUSE_GN_ROOMS_AND_ACOUSTIC_ARCHITECTURE_2026-09-03.md)

> **Goal:** make the house feel like Melusina actually lives there while preserving a reusable procedural grammar. Furniture should not look like unrelated fantasy props dragged into a pink room. It should feel as though the same curve-language that grew the architecture also grew the bedframe, mirror, wardrobe rails, shelves, chandelier, hooks, knobs and little domestic fittings. ♪

---

## 𝄞 Production rule

```text
MEL_*      = reusable Melodia Studio builder
GN_MH_*    = Melusina-house scene wrapper / composition
SM_MH_*    = baked/export-ready static-mesh candidate
CRV_MH_*   = house-specific authoring curve / geometric DNA
```

Do **not** add a global Melodia Studio builder because one house needs a fancy bedside table.

Promote a house-specific system to `MEL_*` only when:

1. it has a useful parameter contract;
2. it can make at least three clearly different assets;
3. another Melodia location can plausibly use it;
4. it does not duplicate an existing builder;
5. it can be tested independently of this house scene.

The existing stack already contains useful building blocks including:

- `MEL_nikki_wardrobe_nook` — rods, mirror, pedestal;
- `MEL_circular_array`, `MEL_radial_array`, `MEL_curve_array`, `MEL_instance_on_spline`;
- `MEL_rail`, `MEL_baluster`, `MEL_column`, `MEL_post`;
- `MEL_ornament_vine`, `MEL_decorative_rosette`, `MEL_ornament_scallop_band`;
- `MEL_filigree_spiral`, `MEL_filigree_corner_volute`;
- `MEL_ribbon_curve`, `MEL_closed_ribbon`;
- Melodia music-note / staff / phrase builders.

Use those as **grammar**, not as finished furniture.

---

# ♪ The furniture thesis — one house, one genetic curve

Create one authoritative 2D source curve:

```text
CRV_MH_MelusinaLoop
```

The curve should sit halfway between:

- a wave;
- a treble-clef gesture;
- a ribbon turn;
- a shell curl;
- a question mark.

Do not make it literally any one of those.

Use transformed fragments of the curve to generate:

```text
bed headboard
mirror crown
chair side rail
cabinet crest
shelf bracket
wardrobe hanger hook
chandelier arm
balcony table leg
lamp stem
shell-knob backplate
floor inlay
```

The rule is **recognition without repetition**. The player should unconsciously sense the family resemblance before they consciously notice the motif.

### Variation controls

Every wrapper that consumes the Loop should expose some subset of:

```text
Loop Scale
Loop Stretch X
Loop Stretch Z
Curl Bias
Open Amount
Mirror X
Reverse Direction
Profile Radius
Asymmetry
Ornament Tier
```

Do not duplicate the source curve to make variants. Transform it downstream.

---

# ♫ Asset family 01 — Melusina's bed

## Target

A round, low, plush bed nested beneath the roof rather than a giant royal four-poster.

It should read as:

```text
soft circular mattress
+ scallop / petal base
+ asymmetric Loop headboard
+ optional half-canopy ribbon
+ pearl finials
+ visibly lived-in textile layer
```

### Wrapper

```text
GN_MH_FURN_01_Bed
```

### Procedural branches

**Base**

```text
Circle Curve / ellipse
→ Fill Curve
→ Extrude Mesh
→ Mesh Bevel
```

**Scalloped plinth**

Reuse `MEL_ornament_scallop_band` logic around a radial path or use `MEL_circular_array` with 10–18 low-relief shell/petal blocks.

**Headboard**

```text
CRV_MH_MelusinaLoop
→ transform / crop
→ Curve to Mesh
→ optional mirrored secondary arm
→ pearl / rosette anchors
```

**Canopy**

Use `MEL_ribbon_curve` or a house wrapper consuming a simple Bézier canopy curve.

### Exposed parameters

```text
Width             1.65–2.10 m
Length            1.90–2.30 m
Mattress Height   0.38–0.52 m
Headboard Height  1.10–1.55 m
Scallop Count     10–18
Canopy Amount     0–1
Loop Curl         0.65–1.35
Asymmetry         0–0.25
```

### Hero-authored layer

Do **not** procedurally generate the final blanket folds, pillow dents or every ribbon crease. Those are hero soft-goods passes after the silhouette works.

Geometry Nodes owns the furniture skeleton and repeatable ornament.

---

# ♬ Asset family 02 — oval mirror + dressing mirror variants

### Wrapper

```text
GN_MH_FURN_02_MirrorFamily
```

### Reuse

Start by studying / reusing the mirror logic inside `MEL_nikki_wardrobe_nook` rather than rebuilding the concept from zero.

### Grammar

```text
Ellipse Curve
→ Curve to Mesh (outer moulding)
→ duplicate smaller ellipse for inner bead
→ rosette / shell crest at top
→ Loop fragment on one shoulder only
→ backing plane
```

Variants:

```text
MH_Mirror_Wardrobe_L
MH_Mirror_Bedroom_M
MH_Mirror_Entry_S
MH_Mirror_BlueRoom_Watered
```

The Blue Room variant may use a thicker shell frame and deliberately imperfect glass/water lookdev later.

### Important rule

The mirror object is **presentation geometry only**. Any gameplay reflection, identity-reading, outfit response or Seam-Oracle-like interpretation belongs to Unreal systems later.

---

# 𝄞 Asset family 03 — curved cabinets + shelves

### Wrapper

```text
GN_MH_FURN_03_CabinetShelfFamily
```

The kitchen and bedroom need believable storage, but the cabinetry should follow the round house instead of fighting it.

### Base construction

Create a cabinet section from a path curve:

```text
Cabinet Path
→ Resample Curve
→ Curve to Mesh (rectangular depth profile)
→ shelf point generation by Z spacing
→ shelf instances
→ door-panel generation
→ trim curve
```

### Useful modes

```text
LOW_CABINET
TALL_PANTRY
WALL_SHELF
CURVED_BOOKCASE
WARDROBE_BAY
```

Expose:

```text
Length
Depth
Height
Shelf Count
Door Count
Arc Amount
Toe Kick
Trim Tier
Back Panel toggle
```

### Ornament placement

Keep ornament localized:

- Loop or vine on the crown;
- tiny shell backplate around knobs;
- thin pearl bead along important doors;
- plain frame on utility cabinetry.

**A spice drawer does not need a cathedral.**

---

# ♪ Asset family 04 — shell knobs, hooks + domestic hardware

This small family has huge visual payoff because it can unify the entire interior.

### Wrapper

```text
GN_MH_FURN_04_HardwareKit
```

### Modules

```text
MH_Knob_Pearl
MH_Knob_Shell
MH_Handle_Ribbon
MH_Hook_Loop
MH_Backplate_Rosette
MH_Hinge_Deco
```

Use combinations of:

- low-segment spheres / pearl shapes;
- decorative rosette;
- shell fan source mesh;
- Loop fragment;
- filigree spiral;
- simple brass stems.

### Rule

Hardware should be the **lowest-cost place to repeat identity**.

If the house needs more coherence, repeat the hardware grammar before adding more giant wall ornament.

---

# ♫ Asset family 05 — chair / chaise / little stool

### Wrapper

```text
GN_MH_FURN_05_SeatFamily
```

Use a simple seat volume and derive the frame from curves.

```text
Seat block / cushion
+ front leg curve × 2
+ back leg / backrest curve × 2
+ Loop-derived back crest
+ optional scallop apron
```

Modes:

```text
SALON_CHAIR
BEDROOM_CHAISE
KITCHEN_STOOL
BLUE_ROOM_LOUNGE
```

The geometry system should output the **hard frame**. Upholstery folds and hero cushion sculpt are downstream.

Recommended silhouette rule:

> no chair should have four perfectly vertical identical legs.

A slight splay / curl keeps the object inside the architectural language.

---

# ♬ Asset family 06 — tables + music stand hybrids

### Wrapper

```text
GN_MH_FURN_06_TableFamily
```

Tables can combine simple radial geometry with musical filigree.

Modes:

```text
SALON_ROUND
TEA_TABLE
BED_SIDE
KITCHEN_WORK
MUSIC_STAND_TABLE
```

Use `MEL_circular_array` for legs when useful, but break perfect repetition through:

- one ornament omission;
- one rotated Loop bracket;
- slightly varied collar position;
- asymmetric drawer placement.

The kitchen work table should remain comparatively plain.

---

# 𝄞 Asset family 07 — Resonance Mobile / chandelier

This should become one of the most recognizable props in Melusina's house.

### Wrapper

```text
GN_MH_FURN_07_ResonanceMobile
```

### Shape

```text
central rose / pearl hub
→ 2–4 concentric rings
→ 5–12 hanging arms
→ glass drops / note-heads / shell slivers
→ occasional thin staff fragment
```

Reuse:

- `MEL_circular_array` / `MEL_radial_array`;
- Melodia music-note geometry;
- `MEL_closed_ribbon`;
- rosette / filigree builders;
- simple instanced droplet source collection.

### Parameters

```text
Radius
Ring Count
Drop Count
Drop Length Range
Note Probability
Shell Probability
Asymmetry
Vertical Spread
```

### Authoring metadata

Store local values for lookdev/debug only:

```text
mh_resonance_band
mh_mobile_index
mh_drop_family
```

Do not assume arbitrary GN attributes will become gameplay data after FBX export.

### Motion

For Blender preview, very small procedural rotation / noise is fine.

For final runtime movement, export clean geometry and let Unreal own animation / audio response.

---

# ♪ Asset family 08 — curved wardrobe rails + garment bays

The Wardrobe Rotunda should reuse the existing `MEL_nikki_wardrobe_nook` idea but become a circular room-scale system.

### Wrapper

```text
GN_MH_FURN_08_WardrobeRadialKit
```

Core:

```text
Room center
→ radial / arc guide
→ garment-bay points
→ rods / uprights / shelves
→ mirror anchor
→ pedestal anchor
```

Expose:

```text
Radius
Bay Count
Bay Arc
Rod Height
Shelf Count
Mirror Bay Index
Pedestal Offset
Open Bay Probability
```

Keep actual outfit content separate. The furniture kit creates **places garments may occupy**, not wardrobe gameplay state.

---

# ♫ Asset family 09 — picture frames, score frames + memory shelves

### Wrapper

```text
GN_MH_FURN_09_MemoryDisplayKit
```

Use existing ornament frame / musical notation builders to generate:

- framed score pages;
- shell-backed photographs / illustrations;
- little travel-object shelves;
- Starskiff letters pinned beneath a rail;
- empty frames intentionally waiting for future journey memories.

This is a strong evergreen-content surface later, but Blender only creates the physical display kit.

---

# ♬ Asset family 10 — lamps + lanterns

### Wrapper

```text
GN_MH_FURN_10_LightFixtureKit
```

Variants:

```text
WALL_SCONCE
TABLE_LAMP
GROTTO_LANTERN
STAIR_PEARL_LIGHT
TOWER_CHIME_LAMP
```

Use:

- Loop arm;
- pearl/shell reservoir;
- small glass envelope;
- brass collar;
- optional hanging ribbon.

Do not bake actual light into geometry. Export fixture geometry and place real UE lights deliberately.

---

# ♪ Procedural vs authored split

| Asset part | Geometry Nodes | Hero/manual pass |
|---|:---:|:---:|
| hard frame / proportions | ✓ | optional polish |
| repeated rails / posts | ✓ | — |
| shells / rosettes / loop trims | ✓ | hero crest optional |
| cushions | base only | ✓ |
| blanket / drape folds | guide only | ✓ |
| clutter placement | sparse procedural seed | ✓ final |
| books / dishes / letters | optional instances | ✓ hero selection |
| chipped paint / wear | material pass | art-direct |
| interaction / gameplay | — | Unreal |

The house should be procedurally **coherent**, not procedurally **complete**.

---

# 𝄞 Collection layout

Inside the house WIP:

```text
MH_FURN_SOURCE
├── CURVES
├── HARDWARE
├── SHELLS
├── PEARLS
├── CUSHION_BLOCKOUT
└── CLUTTER_SOURCE

MH_FURN_GN
├── BED
├── MIRRORS
├── CABINETRY
├── SEATING
├── TABLES
├── MOBILE
├── WARDROBE
├── LIGHTS
└── MEMORY_DISPLAY

MH_FURN_HERO
└── manually polished outputs / soft goods
```

Do not destructively apply modifiers in `MH_FURN_GN`.

---

# ♬ Suggested first serious furniture session — ~2.5 hours

## Pass A — DNA curve · 15 min

- finalize `CRV_MH_MelusinaLoop`;
- make three transformed variants from one source;
- test as rail, mirror crest and bed headboard.

**Gate:** the same curve should feel plausible at all three scales.

## Pass B — bed + mirror · 35 min

- block `GN_MH_FURN_01_Bed`;
- build `GN_MH_FURN_02_MirrorFamily`;
- place both in bedroom.

## Pass C — cabinet + hardware · 35 min

- build one curved kitchen cabinet run;
- create pearl/shell knob kit;
- prove hardware repeats across cabinet + wardrobe.

## Pass D — Resonance Mobile · 35 min

- build rings and hanging instances;
- add restrained note/shell probability;
- render once in clay and once in house palette.

## Pass E — seating + table · 20 min

- one salon chair;
- one tea table;
- derive both from the Loop grammar.

## Pass F — screenshots + audit · 10 min

Save evidence under:

```text
Saved/Audit/melusinashouse/furniture/
```

Suggested names:

```text
MH_FURN_loop_dna.png
MH_FURN_bed_mirror.png
MH_FURN_cabinet_hardware.png
MH_FURN_resonance_mobile.png
MH_FURN_room_context.png
```

---

# ♪ Definition of done

A Phase-3 furniture proof is successful when:

- the bedroom contains a readable bed + mirror family;
- the kitchen has one curved cabinet/shelf run;
- wardrobe hardware visually belongs to the same family;
- the Resonance Mobile is recognizable in silhouette;
- at least four assets visibly reuse `CRV_MH_MelusinaLoop` without looking cloned;
- procedural hard-surface parts remain editable;
- soft goods are clearly separated for hero polish;
- no gameplay/runtime authority has leaked into Blender.

---

> **The house should not look furnished by a prop library. It should look as though its furniture learned how to curl from the walls.** ♪
