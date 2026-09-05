# 𝄞 Melusina's House — Rooms + Acoustic Architecture in Geometry Nodes

**Date:** 2026-09-03  
**Discovery tokens:** `melusinashouseplan`, `Melusina house rooms`, `Listening Stair`, `Resonant Salon`, `Wardrobe Rotunda`, `Blue Room`, `acoustic architecture`, `music house geometry nodes`  
**Parent:** [`/melusinashouseplan.md`](../../melusinashouseplan.md)  
**Sibling:** [`MELUSINAS_HOUSE_GN_ASSET_FAMILY_IMPLEMENTATION_2026-09-03.md`](MELUSINAS_HOUSE_GN_ASSET_FAMILY_IMPLEMENTATION_2026-09-03.md)

> **Design premise:** the house is not just decorated with music. Its curves describe how sound is gathered, guided, held and released.

This plan turns that premise into an authorable Blender 5.2 system without pretending Geometry Nodes is a full acoustic simulator.

---

## ♪ The house-level acoustic grammar

Use three simple spatial roles:

```text
GATHER  = concave surfaces, lower rooms, shells, upholstered spaces
GUIDE   = stairs, corridors, rails, curved walls, thresholds
RELEASE = tower, balcony, open porch, windows toward sea
```

Store the role as authoring metadata:

```text
mh_acoustic_role
```

Suggested integer convention:

```text
0 neutral
1 gather
2 guide
3 release
```

This metadata can drive visualization, export tagging and later Unreal authoring tools. It is **not** runtime acoustic authority by itself.

---

# ♫ Room constellation

The house should feel like one central oval with rooms budding from it.

```text
                      [Listening Tower]
                              3
                              │
                    [Melusina Bedroom]
                              1
                              │
 [Crescent Balcony] ── [Oval Salon] ── [Music/Reading Bay]
          3                 1/2
                              │
                      [Listening Stair]
                              2
                       ╱              ╲
             [Kitchen]                [Wardrobe Rotunda]
                1                           1
                       ╲              ╱
                        [Blue Room]
                            1
```

The numbers above correspond roughly to `gather / guide / release`, with the Salon intentionally mixing roles.

---

# 1 — Resonant Salon

## Emotional job

The social and musical heart of the house. It should feel special without becoming a ballroom.

### Geometry target

- two-storey oval volume;
- slightly sunken center;
- off-center instrument anchor;
- upper gallery / partial balcony;
- tall arched windows;
- ceiling medallion derived from score lines + Melusina Loop;
- one chandelier/mobile made from glass notes, pearl drops and rods.

### Recommended wrappers

```text
GN_MH_ROOM_01_ResonantSalon
GN_MH_PROP_01_CeilingScore
GN_MH_PROP_02_ResonanceMobile
```

### Existing builders to compose

```text
MEL_music_room_shell
MEL_arch
MEL_rail
MEL_baluster
MEL_circular_array
MEL_ornament_radial
MEL_decorative_rosette
MEL_music_staff
MEL_music_note_head
MEL_music_harmonic
```

### Salon shell logic

```text
oval guide curve
→ wall shell
→ second-storey band
→ window markers from curve parameter
→ arch instances
→ gallery rail curve
→ floor inset ring
```

### Ceiling-score logic

Do not plaster literal sheet music across the ceiling.

```text
CRV_MelusinaLoop
+ 3–5 concentric staff-like rings
+ sparse note/pearl points
+ central rosette
→ curve sweeps / small instances
→ warm gold + pearl material zones
```

The composition should still read as ornamental plasterwork when viewed without knowing the music reference.

### Acoustic visualization test

Create a temporary debug material or viewport overlay:

```text
concave lower wall = pink / gather
circulation edge   = lavender / guide
high windows       = blue / release
```

This is an authoring tool, not final art.

---

# 2 — Melusina's Bedroom

## Emotional job

The room must feel lived in enough to resist the rest of the house's procedural perfection.

### Geometry target

- round/oval dormer shell;
- one low crescent balcony;
- curved bed alcove;
- built-in shelf following wall curvature;
- asymmetrical wardrobe spill / garment stand;
- one big blue dormer window;
- ribbons, sheet music, jars, shoes and clothes breaking the clean system.

### Wrapper

```text
GN_MH_ROOM_02_BedroomShell
```

### Existing builders

```text
MEL_greybox_room_kit
MEL_greybox_openings
MEL_arch
MEL_rail
MEL_baluster
MEL_ornament_vine
MEL_filigree_corner_volute
MEL_weighted_array
```

### Procedural rule

Architecture may be procedural. **Clutter should not be fully procedural.**

Use GN only to generate sensible anchor points:

```text
window sill anchors
shelf anchors
bedside anchors
wall hook anchors
floor clutter zones
```

Then art-direct a small number of actual props.

### Domestic imperfection parameter

Expose:

```text
LivedIn = 0..1
```

But use it only for preview scatter density. Final hero clutter should be owner-directed.

---

# 3 — Wardrobe Rotunda

## Emotional job

A circular fitting room where clothing is treated as identity and ritual, not as inventory UI furniture.

### Geometry target

- round chamber;
- center fitting pedestal;
- radial garment bays;
- curved rails;
- large oval mirror;
- clerestory windows;
- shell/pearl floor medallion.

### Wrapper

```text
GN_MH_ROOM_03_WardrobeRotunda
```

### Existing builders to compose

```text
MEL_nikki_wardrobe_nook
MEL_circular_array
MEL_rail
MEL_arch
MEL_ornament_radial
MEL_decorative_rosette
MEL_closed_ribbon
```

### Radial bay logic

```text
center point
→ circular array of bay anchors
→ alternate open garment rail / closed cabinet bay
→ skip one or two bays for asymmetry
→ clerestory windows between structural ribs
```

Suggested controls:

```text
Bay Count      6–10
Open Bay Ratio 0.5–0.75
Pedestal Dia   1.3–1.8 m
Mirror Width   1.0–1.4 m
```

### Outfit-response idea

Do not build gameplay logic into Blender.

Instead create optional tagged response anchors:

```text
LOC_MH_RESP_TIDE_CURTAIN
LOC_MH_RESP_BELL_GLASS
LOC_MH_RESP_BLOOM_PLANT
LOC_MH_RESP_VOID_MIRROR
LOC_MH_RESP_ANCHOR_FLOOR
```

These become candidate hooks for Unreal later.

---

# 4 — Listening Stair

## Emotional job

A vertical connector that makes the house feel acoustically alive.

### Geometry target

- spiral stair around a hollow shaft;
- tall thin openings into adjacent rooms;
- pearl/brass balusters;
- occasional hanging glass/chime elements;
- top release toward Listening Tower.

### Wrapper

```text
GN_MH_ROOM_04_ListeningStair
```

### Existing builders

```text
MEL_spiral_array
MEL_instance_on_spline
MEL_baluster
MEL_rail
MEL_arch
MEL_music_harmonic
```

### Stair logic

```text
spiral guide
→ sample tread transforms
→ instance tread module
→ outer rail spline
→ inner handrail spline
→ chime anchors every N steps
```

Expose:

```text
Turns           1.25–1.75
Rise            3.0–3.6 m
Tread Count     18–28
Shaft Radius    0.55–0.85 m
Chime Interval  4–8 steps
```

### Acoustic authoring metadata

Mark the stair as `guide` and store a normalized height attribute:

```text
mh_acoustic_role = 2
mh_vertical_u     = 0..1
```

Later visualization can use `mh_vertical_u` to make debug pulses climb the stair.

---

# 5 — Crescent Balcony

## Emotional job

A small open place where the house releases sound toward sea and sky.

### Geometry target

- crescent plan;
- curved rail;
- shell corner posts;
- shallow awning / ribbons;
- planter pockets;
- view axis toward water.

### Wrapper

```text
GN_MH_ROOM_05_CrescentBalcony
```

### Existing builders

```text
MEL_rail
MEL_baluster
MEL_instance_on_spline
MEL_ornament_vine
MEL_ribbon_curve
MEL_weighted_array
```

### Key parameter

```text
SeaVector
```

This is a simple authoring direction, not world-space truth. Use it to bias:

- planter openings;
- ribbon drift preview;
- ornament sparsity;
- camera framing guides.

Set:

```text
mh_acoustic_role = 3
```

---

# 6 — Kitchen

## Emotional job

The house needs one room where beauty serves ordinary life.

### Geometry target

- powder-blue curved cabinetry;
- pink stone counter;
- round stove hood or stove body;
- arched pantry;
- plant-heavy window;
- one hilariously elaborate Baroque frame around a mundane shelf.

### Wrapper

```text
GN_MH_ROOM_06_KitchenShell
```

### Existing builder reuse

```text
MEL_greybox_room_kit
MEL_greybox_openings
MEL_arch
MEL_ornament_frame
MEL_filigree_corner_volute
MEL_weighted_array
```

### What GN should do

- shell / openings;
- curved cabinet run from wall guide;
- shelf repeats;
- counter sweep;
- cabinet-handle placement;
- prop anchor markers.

### What GN should not do

Do not procedurally generate every spoon, cup and pan. Use a small authored prop kit.

---

# 7 — Blue Room / Water Grotto

## Emotional job

The house's oldest secret: architecture gathered around water that was already singing.

### Geometry target

- two or three partly submerged architectural arches;
- shallow tide pool;
- lower steps;
- blue ceramic / pearl plaster transitions;
- rock intrusion;
- shells and plants;
- tiny bell/chime points the tide can visually touch.

### Wrapper

```text
GN_MH_ROOM_07_BlueRoom
```

### Existing builders

```text
MEL_arch
MEL_env_waterfall_pool
MEL_water_ripples
MEL_water_gerstner
MEL_weighted_array
MEL_ornament_scallop_band
MEL_effect_wave
```

### Two-authoring-state model

For Blender proof, make two presets:

```text
LOW_TIDE
HIGH_TIDE
```

`LOW_TIDE`:

- more floor exposed;
- lower step visible;
- shell scatter extends deeper.

`HIGH_TIDE`:

- water rises;
- lower step disappears;
- reflection / glow coverage increases.

Do not build runtime tide ownership here.

### Metadata

```text
mh_acoustic_role  = 1
mh_water_affinity = 1.0
mh_room_id        = "blue_room"
```

---

# 8 — Listening Tower

## Emotional job

The final release point of the house: narrow, vertical, open to distant weather and song.

### Wrapper

```text
GN_MH_ROOM_08_ListeningTower
```

### Existing builders

```text
MEL_gazebo
MEL_circular_array
MEL_column
MEL_rail
MEL_baluster
MEL_star_finial
MEL_arch
MEL_music_harmonic
```

### Composition

```text
shaft
→ window ribs
→ upper lantern
→ balcony ring
→ domed / ribbon cap
→ finial
```

### Acoustic debug visualization

Create a temporary ring pulse:

```text
MEL_music_harmonic or radial-wave style preview
→ scale from 0.2 to 1.0
→ rise toward tower opening
```

This is for concept validation only.

Set:

```text
mh_acoustic_role = 3
```

---

# ♬ The Resonance Mobile / chandelier

This is worth its own GN proof because it can become a strong hero prop.

### Wrapper

```text
GN_MH_PROP_02_ResonanceMobile
```

### Geometry

```text
central ring
→ 3–5 nested arcs
→ hanging wire points
→ glass-note / pearl / droplet instances
→ slight random length
→ one asymmetrical empty sector
```

Reuse:

```text
MEL_circular_array
MEL_closed_ribbon
MEL_music_note_head
MEL_ornament_scallop_band fragments
```

Keep it light enough that it does not read as a giant brass chandelier.

---

# ♪ Acoustic debug system — not simulation

Create one local GN visualization helper:

```text
GN_MH_DEBUG_AcousticFlow
```

Inputs:

```text
Geometry
Role Attribute
Flow Curves
Density
Pulse Scale
ShowGather
ShowGuide
ShowRelease
```

Visualization:

```text
GATHER  → small inward-facing arcs / dots
GUIDE   → particles or lines along authored flow curves
RELEASE → larger outward rings / arrows
```

Use it to answer:

- does the architecture visually support the acoustic story?
- are there too many competing release points?
- does the stair actually connect the central room to the tower?
- does the Blue Room feel like a gathering basin?

Delete or disable this debug geometry for final assets.

---

# 𝄞 Named semantic contract for house authoring

Keep the attribute vocabulary tiny.

```text
mh_room_id
mh_acoustic_role
mh_ornament_tier
mh_material_zone
mh_water_affinity
mh_vertical_u
mh_loop_presence
```

Recommended uses:

| Attribute | Purpose |
|---|---|
| `mh_room_id` | room selection / export grouping |
| `mh_acoustic_role` | gather/guide/release debug + later authoring hints |
| `mh_ornament_tier` | decoration density 0–3 |
| `mh_material_zone` | stable material partition |
| `mh_water_affinity` | wetness / grotto authoring hint |
| `mh_vertical_u` | normalized vertical position in stair/tower |
| `mh_loop_presence` | marks use of Melusina Loop motif |

Do not invent twenty more attributes until a real consumer exists.

---

# ♫ Room implementation order

### Movement I — the house can be walked

1. Oval Salon shell.
2. Listening Stair.
3. Listening Tower.
4. Crescent Balcony.

This proves the central vertical circulation and exterior silhouette.

### Movement II — the house belongs to Melusina

5. Bedroom.
6. Wardrobe Rotunda.
7. Kitchen.

This proves domestic life, clothing identity and intimacy.

### Movement III — the house has a secret

8. Blue Room.
9. Low/high tide presets.
10. Resonance Mobile + ceiling score.
11. Acoustic debug flow pass.

---

# ♬ Tonight-sized implementation slice

If there are only 2–3 hours:

```text
[ ] Block Oval Salon from an oval guide
[ ] Build Listening Stair guide + 12–20 temporary treads
[ ] Compose Listening Tower from existing builders
[ ] Make one balcony rail curve
[ ] Tag gather / guide / release metadata
[ ] Create one acoustic debug screenshot
```

Do **not** start the kitchen clutter or final bedroom dressing before the core circulation reads.

---

# ♪ Definition of done for a room wrapper

A room wrapper is ready for art polish when:

1. it reads correctly in grey material;
2. player scale is believable;
3. door/window connections are plausible;
4. curves remain editable;
5. repeated pieces remain instanced;
6. its major parameters are exposed;
7. `mh_room_id` and relevant semantic attributes are present;
8. it can be hidden/soloed cleanly;
9. it does not require saving over the live v22 stage;
10. a screenshot exists under `Saved/Audit/melusinashouse/`.

---

# 𝄞 Later Unreal handoff

Blender exports geometry and authoring hints only.

Possible future flow:

```text
Blender hero geometry
+ named room/export groups
+ optional semantic sidecar
→ Unreal import
→ static meshes / Nanite / materials
→ audio volumes / Convergence hooks / gameplay authored in Unreal
```

The debug acoustic metadata may help placement, but it must never quietly become a second gameplay-state system.

---

> **The house should feel as though it has learned where to hold a sound, where to carry it, and where to let it go. Geometry Nodes gives us the grammar; art direction decides the sentence.** ♫
