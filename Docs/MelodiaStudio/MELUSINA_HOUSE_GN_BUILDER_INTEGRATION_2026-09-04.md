# ♬ Melusina House — Melodia Studio GN Builder Integration

**Date:** 2026-09-04  
**Canonical agent entrypoint:** `/MELUSINA_HOUSE_GN_START_HERE.md`  
**Canonical next-work roadmap:** `/Docs/MelodiaStudio/MELUSINA_HOUSE_GN_FOUNDATION_TO_SHELL_ROADMAP_2026-09-04.md`  
**Discovery tokens:** `Melusina House GN`, `MH foundation`, `MEL_mh_`, `Melodia Studio house builders`

## Why agents kept getting lost

Three different layers were being described as if they were one thing:

1. **concept art / modeling breakdowns**;
2. **scene-local proposed names** such as `GN_MH_03_RoofRibbon`;
3. **actual registered Melodia Studio IDs** beginning with `MEL_`.

Meanwhile, real house code landed in `melodia_house.py`, `melusina_house.py`, and `house_dress.py`, but the older plans continued to read like future work. The live builders were also split across generic GN Stack categories.

This packet makes the integration chain explicit and gives the house a dedicated catalog surface.

---

# 𝄞 Melodia Studio registration chain

Every house builder must complete this chain:

```text
builder function
→ register_builder(...)
→ GROUP_BUILDERS / GROUP_METADATA
→ __init__.py imports the module
→ _rebuild_derived_data()
→ TREE_TYPES / TREE_CATEGORIES
→ GN Stack "Melusina House" section
→ optional BUILDERS_PRESETS entry
→ Blender 5.2 construction smoke
```

A file existing on disk is not enough.

## Dedicated category

`core.py` owns:

```python
"melusina_house": {"label": "Melusina House", "icon": "HOME"}
```

House-only builders should register to this category. Shared primitives such as `MEL_baluster`, `MEL_arch`, or `MEL_curve_array` stay in their generic families.

This prevents two bad outcomes:

- duplicating reusable builders just to make them easy to find;
- scattering house-specific wrappers through four generic sections.

---

# ♪ Foundation builders

The foundation layer is intentionally simpler than the visual concepts.

## `MEL_mh_foundation_pod`

**Purpose:** atomic oval floor mass.

Inputs:
- Width
- Depth
- Foundation Height
- Bevel

Graph:

```text
Cylinder
→ nonuniform XY scale
→ lift half height
→ Mesh Bevel
→ output
```

Use it for one room pod, tower footing, Blue Room base, or isolated proportion tests.

## `MEL_mh_foundation_cluster`

**Purpose:** first useful lower-house footprint.

```text
center salon pod
+ left pod
+ right pod
+ rear pod
→ Join Geometry
```

Key controls:
- Center Width / Depth
- Side Width / Depth
- Side Spread
- Rear Width / Depth
- Rear Offset
- Foundation Height
- Bevel

This is where agents should solve the **rounder house silhouette** before touching decoration.

## `MEL_mh_foundation_porch`

**Purpose:** independent front entry / terrace mass.

It deliberately does not own stairs, rails, shell crests, or drapes. Those remain later modules so the porch proportions can be changed without rebuilding decoration.

## `MEL_mh_foundation_master`

**Purpose:** one-click concept-board blockout.

Contains:
- center/side/rear foundation pods;
- front porch;
- Listening Tower circular pad.

This is the recommended **first builder for Hermes/agents**.

---

# ♫ Existing live structural layer

## `MEL_mh6_room_shell`

Already implemented in `melodia_house.py`.

Owns a procedural room/wall shell with:
- Width / Depth / Height;
- Curve;
- Base Bevel;
- optional SDF wall/opening work;
- cornice controls;
- opening grid controls.

Do not replace this with another generic curved-wall builder unless a concrete limitation is proven.

## `MEL_melusina_house_round_interior`

Already implemented in `melusina_house.py`.

Composes:
- circular center room;
- music/prayer nook;
- kitchen;
- rear hall;
- curved stair proof;
- base/cornice trim.

It is a composition builder, not the foundation SSOT.

---

# ♬ Existing detail layer

`melodia_house.py` also owns:

```text
MEL_mh_aaa_cornice
MEL_mh_aaa_dentil
MEL_mh_aaa_scallop_uv
MEL_mh_aaa_lissajous_pearl
```

Treat these as **house-specific detail builders**.

Do not start a house session with them.

---

# ♪ Existing dressing layer

`house_dress.py` owns:

```text
MEL_mh_piano_walk
MEL_mh_sheet_rail
MEL_mh_staff_rows
MEL_mh_xylo_fountain
MEL_mh_stepping_stones
MEL_mh_lantern_row
MEL_mh_tree_line
```

These are post-silhouette modules.

---

# 𝄞 What is still genuinely missing

After foundation integration, the next builder work should be:

| Priority | Builder / wrapper | Why |
|---|---|---|
| P1 | `MEL_mh_roof_ribbon` | silhouette-defining; first new builder after foundation smoke |
| P1 | `MEL_mh_opening_family` | reusable visible frame + cutter pair |
| P1 | `MEL_mh_porch_stair` | connect foundation porch to existing stair/rail vocabulary |
| P2 | `MEL_mh_listening_tower` | vertical counterweight above the new tower pad |
| P2 | `MEL_mh_shingle_distributor` | turn `MEL_mh_aaa_scallop_uv` into controlled roof-wide distribution |
| P2 | `MEL_mh_melusina_loop` | stable curve DNA for ornament/furniture |
| P2 | Blue Room grotto shell | water-affinity architecture |
| P3 | furniture wrappers | only after rooms are stable |

Do **not** create all of these simultaneously. The canonical batch order and acceptance gates are maintained in `MELUSINA_HOUSE_GN_FOUNDATION_TO_SHELL_ROADMAP_2026-09-04.md`.

---

# ♫ Foundation-to-house build score

### Pass A — 20 minutes

`MEL_mh_foundation_master`

Tune only:
- Side Spread
- Rear Offset
- Porch Offset
- Tower X/Y
- overall pod dimensions.

Capture top/front/three-quarter clay screenshots.

### Pass B — 30 minutes

Layer:
- `MEL_mh6_room_shell`;
- `MEL_melusina_house_round_interior`.

Prove circulation and room proportions.

### Pass C — 45 minutes

Only then begin roof/opening builders.

### Pass D

AAA trim and dressing.

---

# ♪ Preset expectations

Foundation builders should have simple composition presets, not aesthetic overload.

Recommended:
- COMPACT_DOLLHOUSE
- ROUND_BAROQUE_DEFAULT
- WIDE_SALON
- CRESCENT_ENTRY
- SEA_TERRACE

Preset socket names must exactly match the node-group interface. `Tools/verify_melusina_house_gn_catalog.py` checks the source-level contract before Blender smoke.

---

# ♬ Agent execution contract

When asked to work on Melusina's House:

1. Read `MELUSINA_HOUSE_GN_START_HERE.md`.
2. Run the catalog verifier.
3. Read only the module relevant to the requested builder.
4. Use a disposable Blender 5.2 file or isolated house WIP.
5. Search GN Stack for `MH Foundation`.
6. Build one thing.
7. Capture evidence.
8. Update the manifest if a builder ID/status changes.
9. Never infer current builder state from a month-old handoff.

## Forbidden assumptions

- `GN_MH_*` means a registered builder. **False.**
- a concept sheet is exact geometry. **False.**
- a builder file being present means the module is imported. **False.**
- an imported module means GN Stack discovery works. **Not necessarily.**
- old exact builder-count assertions are current health truth. **False.**

---

# 𝄞 Blender smoke

In a safe Blender 5.2 session:

```text
Melodia Studio
→ GN Stack
→ category: Melusina House
→ search: MH Foundation
→ add MH Foundation Master
```

Manipulate three parameters. If the geometry responds, capture:

```text
Saved/Audit/melusina_house/
  foundation_top.png
  foundation_front.png
  foundation_three_quarter.png
```

Then test `MEL_mh6_room_shell`.

Do not call the builder visually verified until this has happened.

---

> **The house pipeline now begins with a registered foundation, not with an agent trying to reverse-engineer a painting.** ♫
