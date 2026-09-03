# melusinashouseplan

> **HERMES_DISCOVERY_KEY:** `melusinashouseplan`  
> **Search aliases:** `Melusina house` · `Melusina's House` · `geometry nodes house` · `Blender 5.2` · `round baroque` · `pink blue architecture` · `rococo shell house` · `seaside sanctuary`  
> **Canonical entrypoint:** `/melusinashouseplan.md`  
> **Reference folder:** `/Docs/References/MelusinasHouse/`  
> **Owning lane:** Blender 5.2 offline environment authoring  
> **Runtime authority:** Unreal remains the game/runtime authority. This packet creates art assets, not a second gameplay system. ♪

**Updated:** 2026-09-02  
**Primary operator:** owner / Hermes agent on the laptop  
**Target:** an editable, modular, Geometry-Nodes-first hero house matching the latest pink/blue round-Baroque concept direction.

---

## 𝄞 Read these first

1. `melusinashouseplan.md` — this file; canonical house build score.
2. `Docs/References/MelusinasHouse/` — the three attached modeling boards.
3. `Docs/BLENDER_MELODIA_COCKPIT.md` — current Blender 5.2 / MCP safety and startup truth.
4. `deploy/surreal_arch/README.md` — Melodia Studio procedural-architecture SSOT. Reuse existing builders before adding duplicates.

**Hermes rule:** do not begin by searching every historical handoff. Start here, then inspect the existing Melodia Studio builder catalog for reusable arches, ornaments, rails, musical motifs, scatter, and export utilities.

---

# ♪ Tonight's result

Tonight is **not** a final Nanite-ready house and it is not an excuse to spend six hours on one shell carving. The goal is a beautiful, editable hero shell that proves the architectural grammar.

By the end of the session, have:

- a round, asymmetrical, immediately readable silhouette;
- foundation + porch + main curved wall shell;
- three overlapping curved roof/ribbon masses;
- a working procedural shingle patch expanded to the hero roofs;
- arched + round window family and front door;
- the right-side tower/chimney counterweight;
- one coherent rocaille / pearl / shell trim system;
- railings, lavender awning proof, and restrained flower scatter;
- front, three-quarter, and side screenshots under `Saved/Audit/melusinashouse/`;
- all important shape parameters exposed in named GN groups.

Do **not** destructively realize every instance in the authoring tree. Realize only on isolated branches where booleans or export actually require it.

---

# ♫ Design thesis — round Baroque, not a generic cottage

The latest concepts improve the original house because the architecture itself now behaves like Melodia: it **swells, answers, curls and repeats motifs** instead of stacking normal rectangles under fantasy decoration.

Use two historical grammars as ingredients, not as a literal reconstruction:

### Borromini / San Carlo — movement in the building mass

Francesco Borromini's San Carlo alle Quattro Fontane is useful because its architecture is generated through interacting curved geometry rather than a static flat front. Its plan uses oval / interlocking geometric logic, while the façade alternates concave and convex zones. For Melusina's house, translate that into a domestic three-bay rhythm:

```text
concave shoulder → convex welcoming entry → concave shoulder
```

The result should make the front wall feel gently inhaled/exhaled. The center bay is wider and pushes toward the visitor; side bays curl back. Do not copy the church's orders or proportions.

### Rococo — marine curve grammar

Rococo's `rocaille` vocabulary is exceptionally useful for Melodia: broken-shell/rock forms, marine motifs, acanthus, and energetic **S / C curves**, often arranged asymmetrically. Translate that grammar into:

- shell-cap cresting;
- pearled curve trim;
- S-curve porch brackets;
- C-curve window surrounds;
- lyre / treble-clef infill;
- hanging chimes and droplet ornaments;
- deliberately incomplete secondary symmetry.

The important lesson is **controlled asymmetry**, not random clutter.

### Melodia owns the palette

Historical precedent supplies geometry only. The house remains unmistakably Melodia:

- pearl blush / pink plaster;
- iridescent blue → lavender → rose shingles;
- warm gold/brass edging;
- pearl white carved shells;
- aqua / opalescent glass;
- lavender fabric and flowers;
- warm honey light inside.

---

# ♬ Working scale

These are production assumptions for tonight, not claims about historical architecture.

| Parameter | Start value | Useful range |
|---|---:|---:|
| overall width | 13.2 m | 12.5–14.0 m |
| overall depth | 9.8 m | 9.0–11.0 m |
| main wall height | 3.42 m | 3.35–3.50 m |
| loft spring | 2.9 m | 2.8–3.0 m |
| main ridge | 8.4 m | 8.0–8.8 m |
| tower top | 10.5 m | 10.0–11.0 m |
| porch depth | 1.8 m | 1.7–1.9 m |
| front door | 1.15 × 2.35 m | ±10% |
| wall thickness | 0.30 m | 0.28–0.32 m |
| façade wave amplitude | 0.65 m | 0.55–0.75 m |
| eave overhang | 0.58 m | 0.50–0.65 m |
| main roof rise | 2.55 m | 2.3–2.8 m |
| shingle module | 0.28 × 0.36 m | ±10% |
| shingle overlap | 40% | 35–45% |
| trim profile radius | 0.05 m | 0.03–0.08 m |
| baluster spacing | 0.32 m | 0.30–0.34 m |
| tower diameter | 1.8 m | 1.6–2.0 m |
| secondary ornament omit | 20% | 15–25% |

Set Blender to **Metric, 1 Blender Unit = 1 m**. Keep a 1.7 m mannequin visible in `MH_GUIDES` until the final silhouette pass.

---

# 𝄞 File + collection organization

Create a **new clean `.blend`**. Do not author this directly in the live portfolio stage.

Suggested local WIP:

```text
Saved/Blender/MelusinasHouse/MelusinasHouse_GN_v001.blend
```

Do not commit `.blend` files unless the owner explicitly asks. When ready for Unreal, export from a duplicate `EXPORT` collection rather than flattening the authoring collection.

Collections:

```text
MH_GUIDES
MH_SOURCE_KIT
MH_GN_OUTPUT
MH_MATERIALS
MH_LIGHTING
EXPORT              # only when approved
```

Guide objects:

```text
CRV_MH_Footprint
CRV_MH_FrontFacade
CRV_MH_Porch
CRV_MH_RoofMain
CRV_MH_RoofWing
CRV_MH_RoofPorch
CRV_MH_Rocaille
LOC_MH_Tower
CUT_MH_DoorsWindows
```

Create or reuse these exact node-group names so Hermes and later audits can find them:

```text
GN_MH_00_MasterAssembly
GN_MH_01_FoundationPorch
GN_MH_02_CurvedWallShell
GN_MH_03_RoofRibbon
GN_MH_04_ScallopShingles
GN_MH_05_WindowDoorKit
GN_MH_06_TowerChimney
GN_MH_07_RocailleTrim
GN_MH_08_RailingBalusters
GN_MH_09_AwningsDrapes
GN_MH_10_FoliageScatter
GN_MH_11_InteriorShell
GN_MH_12_MusicalOrnamentPass     # optional tonight
```

Before writing a new builder, check Melodia Studio / `deploy/surreal_arch/` for an existing equivalent. **Reuse + wrap beats duplicate + drift.**

---

# ♪ Step-by-step Blender 5.2 Geometry Nodes build

## 0 — Protect the real project first · 5 minutes

1. Pull current Git.
2. Read `Docs/BLENDER_MELODIA_COCKPIT.md`.
3. Open a new Blender 5.2 file or a dedicated house WIP — **not** `Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend` for agent saving.
4. If Hermes uses BlenderMCP, connect after Blender starts and ping:

```powershell
python Tools/blender_mcp_client.py get_scene_info
```

5. Do not run BlenderMCP and Melodia Studio LiveLink on the same port simultaneously.
6. Do not save the live v22 portfolio stage from an agent unless `MELODIA_ALLOW_STAGE_SAVE=1` is deliberately set by the owner.

---

## 1 — Draw the house as curves before making walls · 15 minutes

This is the most important modeling decision of the night.

In top view, create `CRV_MH_Footprint` from **three overlapping rounded room pods**, not a rectangle. Use 8–16 deliberate Bézier points, Auto/Aligned handles, and a 1 m grid.

Create `CRV_MH_FrontFacade` as three connected curved bays:

- left concave shoulder;
- broad center convex entry bay;
- right concave shoulder flowing toward tower.

Make the center bay about 30–40% wider than either shoulder. Adjust until the front reads clearly even as a single line.

**Gate:** if the curve already looks like a normal cottage footprint, stop and fix it now. Ornament will not rescue the silhouette later.

---

## 2 — `GN_MH_01_FoundationPorch` · 25 minutes

### Foundation

```text
Footprint Curve
→ Fill Curve
→ Extrude Mesh (0.35–0.50 m)
→ Mesh Bevel (0.05–0.08 m, 2–3 segments)
→ Set Material
```

Blender 5.2's Geometry Nodes **Mesh Bevel** is ideal here: use it procedurally instead of stacking destructive bevel modifiers throughout the kit.

### Porch deck

```text
CRV_MH_Porch
→ Curve to Mesh (deck / edge profile)
→ Extrude / join support slab
→ Mesh Bevel
```

For steps, use either:

```text
Mesh Line → Instance on Points (tread module)
```

or a small **Repeat Zone** if you want variable rise/run. Keep tread instances unrealized until a boolean or export copy needs them.

Shape the stair cheeks as two C-curves that rise into shell-finial posts; this is one of the fastest ways to get the new round-Baroque character into the silhouette.

---

## 3 — `GN_MH_02_CurvedWallShell` · 35 minutes

Use a wall-center guide curve rather than trying to bend a finished rectangular wall afterward.

```text
CRV_MH_FrontFacade / wall guides
→ Resample Curve only where needed
→ Curve to Mesh (rectangular wall profile: thickness × height)
→ window/door boolean branch
→ Mesh Bevel
→ Material
```

Expose:

- `Wall Height`
- `Wall Thickness`
- `Facade Wave`
- `Base Bevel`
- `Story Offset`

For openings, keep cutters in `CUT_MH_DoorsWindows` as named instances. On the **boolean branch only**:

```text
Cutter instances → Realize Instances
Wall mesh + cutters → Mesh Boolean / Difference
```

Do not realize the entire house to make the boolean convenient.

**Shape target:** the façade should still read concave → convex → concave in clay view with all trim disabled.

---

## 4 — `GN_MH_05_WindowDoorKit` · 45 minutes

Build one reusable family before placing twenty bespoke holes.

### Tall arched frame

Use a curve-built frame:

```text
straight left jamb
+ quadratic / Bézier arch
+ straight right jamb
→ Join Geometry (curves)
→ Curve to Mesh (moulding profile)
```

Create paired outputs:

1. visible frame;
2. simple hidden cutter volume.

Variants:

- `MH_Window_Arch_L`
- `MH_Window_Round_M`
- `MH_Window_Turret_S`
- `MH_Door_Entry`

For the round rose window, instance radial mullions around a circle and keep the center medallion large enough to read at game camera distance.

For the front door, keep the door itself mostly authored and readable: arched plank mass + brass inset + treble-clef / lyre ornament. Reuse the existing Melodia musical ornament kit where possible.

---

## 5 — `GN_MH_03_RoofRibbon` · 55 minutes

The roof is the visual thesis. Think **three overlapping ribbons / whale backs / shell sweeps**, not three ordinary gables.

Create ridge/path curves:

```text
CRV_MH_RoofMain
CRV_MH_RoofWing
CRV_MH_RoofPorch
```

Core group:

```text
Ridge / guide curve
→ Set Curve Radius or sampled width controls
→ Curve to Mesh (custom roof cross-section profile)
→ Extrude Mesh / thickness branch
→ Mesh Bevel (0.025–0.04 m)
→ Material
```

Use one group with different parameters instead of three separate roof systems. Expose:

- `Roof Width`
- `Roof Rise`
- `Eave Curl`
- `End Lift`
- `Thickness`
- `Asymmetry`

The roof edge should dip and rise like a phrase. Keep the center roof largest, wing roof offset, porch roof lower and more sheltering.

---

## 6 — `GN_MH_04_ScallopShingles` · 50 minutes

This is the Blender 5.2-specific robust method.

First give each finished roof surface a clean, **non-overlapping UV map**. Then generate shingles in UV space and project them back to the roof with `Sample UV Surface`.

```text
0–1 UV point grid
→ row/column Index math
→ offset every second row by 0.5 shingle width
→ Sample UV Surface (roof Position + Normal)
→ Set Position
→ align rotation to sampled Normal + roof tangent
→ Pick Instance / Geometry to Instance (3–5 shingle variants)
→ Instance on Points
→ random scale 0.95–1.05
→ material variation
```

Why this route: `Sample UV Surface` gives a stable two-dimensional parameterization of a curved roof, which is much easier to art-direct than trying to infer perfect rows from world-space normals.

Use `Geometry to Instance` / instance workflows for repeated shingles; Blender's instancing is far lighter than physically joining tens of thousands of pieces. Keep shingles unrealized in the authoring asset.

Start dimensions:

```text
width:   0.28 m
height:  0.36 m
overlap: 40%
```

Create 3–5 simple shell/scallop variants and vary hue subtly across blue, lavender, aqua and occasional blush. Do not make every tile a different saturated color.

**Gate:** first prove a 2×2 m roof patch. Only distribute across the full house after rows, tangent orientation, spacing and overlap are correct.

---

## 7 — `GN_MH_06_TowerChimney` · 25 minutes

Place `LOC_MH_Tower` right of center to act as the vertical counterweight to the broad roof ribbons.

Build as a modular stack:

```text
stone/plaster base
→ slightly tapered shaft
→ lantern / lookout ring
→ small domed or shell cap
→ crest
```

A profile curve spun/revolved for the cap is preferable to a generic cone. Add a side bell/chime arm and 2–4 hanging charms. The tower should be elegant and slender, not a second castle keep.

Expose diameter, height, taper and cap scale.

---

## 8 — `GN_MH_07_RocailleTrim` · 40 minutes

Create a source mini-library of 6–10 curves:

- 2–3 C-curves;
- 2–3 S-curves;
- one shell fan outline;
- one pearl string path;
- one treble-clef / lyre-adjacent musical curve.

Core flow:

```text
source curve
→ optional Resample Curve
→ Curve to Mesh (0.03–0.08 m profile)
→ endpoint / planned-peak instances
→ shell / pearl / floral / musical crest collection
```

For pearl strings:

```text
curve
→ Resample Curve by Length
→ Curve to Points
→ Instance on Points (pearl)
```

Use seeded variation, but make **composition decisions first**. A simple procedural asymmetry control can omit 15–25% of secondary instances while always preserving hero crests.

Rules:

- entrance gets the richest shell/pearl statement;
- windows get a smaller C-curve vocabulary;
- roof crests are thin and sparse;
- never cover every available edge;
- asymmetry should look composed, not damaged.

---

## 9 — `GN_MH_08_RailingBalusters` · 20 minutes

```text
rail guide curve
→ Curve to Mesh (top + bottom rails)
→ Resample Curve by Length (≈0.32 m)
→ Curve to Points
→ Instance on Points (turned baluster collection)
```

Use `Index → Modulo` or `Pick Instance` so every 4th/5th post may become a shell/pearl accent. Hero corner posts get authored shell finials.

Do not randomize baluster scale enough to make the porch structurally chaotic.

---

## 10 — `GN_MH_09_AwningsDrapes` · 25 minutes

For tonight, use deterministic GN cloth-like geometry first. Simulation is optional.

Start with a grid around 18×8 or 24×10 subdivisions. Let normalized horizontal coordinate be `u`.

Approximate the hanging sag with:

```text
sag = -SagAmount * sin(pi * u)^2
```

In nodes: Map Range / math → Sine → Multiply → Set Position. Add a second sine along the vertical coordinate for a gentle forward belly.

Keep top corners/socket points fixed in your construction. Add separate tassel curves and pearl/drop instances.

Blender 5.2 has experimental Geometry Nodes dynamics/cloth work; use that **only as an optional relax pass** after the deterministic drape works. Do not make tonight's success depend on experimental simulation.

---

## 11 — `GN_MH_10_FoliageScatter` · 20 minutes

Scatter belongs on explicit beds and planters, not indiscriminately across the house.

```text
planter / flower-bed target mesh
→ Distribute Points on Faces
→ density / painted or procedural mask
→ Pick Instance from flower collection
→ Instance on Points
```

Cluster lavender, blue, blush and pearl-white flowers heavily near:

- porch edges;
- tower base;
- window boxes;
- one side of the stair.

Leave enough negative space to read the stone/plaster and curved wall profile.

---

## 12 — `GN_MH_11_InteriorShell` · 20–30 minute blockout

The interior should inherit the round plan instead of secretly becoming a rectangular sitcom house.

Suggested layout from the cutaway reference:

```text
MAIN LEVEL
center      entry + sitting / circular rug
left        music / prayer nook
right       kitchen + pantry
rear/right  curved stair
porch       social / sea-facing extension

UPPER
left/center sleeping loft
center/right writing desk / field-journal worktable
right tower lookout niche
```

Use the exterior wall guides to derive an interior shell and partitions, but keep furniture hero props authored manually. Geometry Nodes should solve repetition and architectural grammar — not turn every chair into a procedural research project.

---

## 13 — `GN_MH_12_MusicalOrnamentPass` · optional

Reuse existing Melodia Studio musical ornaments first:

- treble-clef front door;
- harp / lyre railing inset;
- bell / chime tower hardware;
- note or clef roof crest;
- tiny instrument motifs in brackets.

If you want a one-minute audio-reactive lookdev test, Blender 5.2's `Sample Sound Frequencies` can drive a subtle lantern intensity proxy, ornament scale pulse, or display-only resonance curve. This remains an **offline authoring/lookdev lane**. Unreal / MelodiaCore remains runtime rhythm authority.

---

# ♫ `GN_MH_00_MasterAssembly`

Do not build the whole house inside one unreadable mega-tree. The master group should be boring:

```text
FoundationPorch
+ CurvedWallShell
+ RoofRibbon × 3
+ ScallopShingles
+ WindowDoorKit instances
+ TowerChimney
+ RocailleTrim
+ RailingBalusters
+ AwningsDrapes
+ FoliageScatter
+ InteriorShell toggle
→ Join Geometry
→ material / visibility switches
→ output
```

Blender 5.2 geometry bundles/lists can help package related geometry/data when that genuinely simplifies the graph, but don't adopt a new abstraction simply because it is new. The asset should remain understandable to you at 2 a.m.

Expose these master controls:

```text
Facade Wave
Wall Height
Wall Thickness
Roof Main Rise
Roof Curl
Eave Overhang
Tower Height
Tower Diameter
Shingle Density / Scale
Trim Density
Ornament Asymmetry
Flower Density
Random Seed
Show Interior
Show Set Dressing
LOD / Preview Density
```

---

# ♬ Materials — get the read without over-shading

Create a small reusable material set:

| Material | Direction |
|---|---|
| `M_MH_PearlPlaster_Pink` | warm blush/off-white plaster; gentle roughness breakup; faint pearl response |
| `M_MH_Roof_IridescentBlue` | blue/lavender/rose color shift; scallop tiles stay readable |
| `M_MH_GoldBrass` | aged warm gold; polished edges, darker recesses |
| `M_MH_WoodWarm` | honey/walnut structural wood; modest wear |
| `M_MH_LavenderFabric` | soft lavender/mauve; slightly translucent edge response if useful |
| `M_MH_AquaGlass` | warm interior emission behind aqua/opalescent glass |

Palette anchor suggestions:

```text
blush plaster    #F7D6E7
pearl            #F6F0E8
powder blue      #9CC6E6
roof blue        #6E8AAF
lavender         #A8A0DD
rose accent      #E7A5C9
warm brass       #C6A15A
```

Avoid mirror-shiny metals and candy-plastic plaster. The concept's softness comes from broad color relationships + rounded geometry + warm light, not maximum specular everywhere.

---

# ♪ Tonight — recommended 5½ hour score

| Time | Work | Gate |
|---|---|---|
| 0:00–0:20 | setup, references, metric scale, curves | silhouette reads in top/front guides |
| 0:20–1:00 | foundation, porch, curved walls | concave→convex→concave survives clay view |
| 1:00–1:45 | window/door family + cutters | one reusable kit, no bespoke-hole spiral |
| 1:45–2:45 | roof ribbon system | three roofs read as one family |
| 2:45–3:25 | shingle proof → full roofs | rows stable; instances not exploded |
| 3:25–4:10 | tower, rails, rocaille | silhouette now unmistakably Melodia |
| 4:10–4:45 | drapes, flowers, base materials | color balance matches refs without clutter |
| 4:45–5:30 | polish, screenshots, parameter audit | front / 3q / side all agree |
| 5:30–6:00 | optional export duplicate | only if authoring asset is already safe |

If time collapses, cut **foliage, drape simulation and interior dressing first**. Do not cut the curved façade, roof grammar, tower counterweight or shingle proof.

---

# 𝄞 Definition of done

A successful first house pass satisfies all of these:

- front, three-quarter and side views clearly belong to one house;
- the silhouette is rounded, layered, asymmetrical and pink/blue — not a normal triangular cottage with decorations pasted on;
- central façade reads convex, shoulders read concave;
- three roof ribbons create depth without becoming unreadable spaghetti;
- tower is a deliberate right-side vertical counterweight;
- shingles are procedural instances and follow the roof reliably;
- major GN groups have named exposed parameters;
- rocaille uses C/S/shell grammar with controlled asymmetry;
- no unnecessary permanent `Realize Instances` across the authoring graph;
- no agent save over the live v22 stage;
- screenshots land under `Saved/Audit/melusinashouse/`;
- any UE export comes from an isolated duplicate `EXPORT` collection.

---

# ♬ Hermes execution contract

When Hermes receives “build Melusina's house,” do this exact sequence:

1. Open `/melusinashouseplan.md`.
2. Inspect `/Docs/References/MelusinasHouse/`.
3. Read `Docs/BLENDER_MELODIA_COCKPIT.md` for the current Blender/MCP safety state.
4. Read `deploy/surreal_arch/README.md` and search existing builders before creating anything new.
5. Work in a new/dedicated `.blend`; do **not** rewrite Melodia Studio or save the live portfolio stage.
6. If using BlenderMCP, connect on the documented lane and verify scene info before mutation.
7. Create/reuse the node groups using the exact `GN_MH_*` names in this packet.
8. Stop for visual evidence at three milestones: **wall silhouette**, **roof + shingle proof**, **detail/color pass**.
9. If a Blender 5.2 node/socket/API differs from this document, consult the current 5.2 docs and record the correction. Never invent a node name to make the plan look complete.
10. Prefer existing Melodia builders/operators where they already solve arches, ornaments, musical motifs, scatter or export.
11. This is offline environment authoring. Do not create a new native Unreal “house system.”

Useful existing agent lane:

```text
deploy/blender_5.2_mcp.py
└─ run_gn_builder → build/apply a Geometry Nodes tree to an object
```

Treat that as an execution door, not a reason to bypass visual review.

---

# ♪ Attached concept references

All working references are deliberately colocated here:

```text
Docs/References/MelusinasHouse/
├── REF_01_EXTERIOR_ROUND_BAROQUE_PINK_BLUE.jpg
├── REF_02_GEOMETRY_NODES_BUILD_SHEET.jpg
├── REF_03_CUTAWAY_INTERIOR_FLOW.jpg
└── README.md
```

Interpretation order:

1. **REF_01** — silhouette, color hierarchy, massing, tower offset, porch mood.
2. **REF_02** — modular / Geometry Nodes decomposition and reusable asset families.
3. **REF_03** — cutaway, rounded room flow, upper/lower relationship, interior priorities.

The images are concept direction, **not measured blueprints**. When an image detail conflicts with this plan's structural rules, keep the structural rule and use the image for visual intent.

---

# ♫ Research sources

Current Blender 5.2 / Geometry Nodes references:

- Blender 5.2 LTS release: https://www.blender.org/download/releases/5-2/
- Blender 5.2 Geometry Nodes release notes: https://developer.blender.org/docs/release_notes/5.2/geometry_nodes/
- Sample UV Surface: https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/mesh/sample/sample_uv_surface.html
- Mesh Bevel: https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/mesh/operations/mesh_bevel.html
- Geometry to Instance: https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/geometry/geometry_to_instance.html

Architectural grammar:

- Borromini, San Carlo alle Quattro Fontane — Smarthistory: https://smarthistory.org/borromini-san-carlo-alle-quattro-fontane/
- Rococo / rocaille introduction — Victoria and Albert Museum: https://www.vam.ac.uk/articles/the-rococo-style-an-introduction
- San Carlino façade reference: https://sancarlino.ch/espacios/the-facade/

Use the research to understand **why curves and asymmetry work**. The pink/blue shell-house design itself is a Melodia fantasy interpretation, not a historical reconstruction.

---

> **House rule:** make the architecture sing before decorating it with notes. ♪
