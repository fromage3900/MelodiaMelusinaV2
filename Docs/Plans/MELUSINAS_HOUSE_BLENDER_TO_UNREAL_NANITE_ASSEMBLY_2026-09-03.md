# 𝄞 Melusina's House — Blender → Unreal Export + Nanite Assembly Plan

**Date:** 2026-09-03  
**Discovery tokens:** `melusinashouseplan`, `Melusina Unreal export`, `Nanite house`, `Blender FBX`, `house assembly`, `SM_MH`, `UE5.8 environment`  
**Parent:** [`../../melusinashouseplan.md`](../../melusinashouseplan.md)

> **Goal:** preserve the editable Blender 5.2 Geometry Nodes house as the authoring source while producing a clean, testable Unreal 5.8 environment assembly. Export should create a deliberate runtime representation — not flatten the master `.blend` into one giant anonymous mesh. ♪

---

## ♪ Authority split

```text
Blender 5.2
= source geometry / procedural authoring / art lookdev

Unreal 5.8
= runtime materials / collision / lighting / streaming / gameplay / interaction
```

The repo already treats Blender as source of truth for environment assets and supports FBX or staged Blender→UE transfer. This plan narrows that rule specifically for Melusina's House.

---

# ♫ Never export directly from the authoring tree

Keep:

```text
MH_GUIDES
MH_SOURCE_KIT
MH_GN_OUTPUT
MH_FURN_GN
MH_FURN_HERO
MH_MATERIALS
MH_LIGHTING
```

editable.

Create a dedicated duplicate/export collection:

```text
MH_EXPORT
```

Only `MH_EXPORT` receives destructive operations required for handoff.

### Export-copy sequence

```text
procedural authoring object
→ duplicate into MH_EXPORT
→ apply required transforms
→ realize instances only where necessary
→ convert curves to mesh where necessary
→ merge/split deliberately
→ assign final material slots
→ generate / verify UVs
→ create collision helper meshes if needed
→ validate names + pivots
→ export
```

Never apply / realize the live GN authoring tree merely because FBX needs a mesh.

---

# ♬ Runtime asset decomposition

Do **not** export the house as:

```text
SM_MelusinasHouse_FINAL_FINAL_REAL.fbx
```

with everything joined.

Use meaningful chunks that preserve material, culling, collision and iteration boundaries.

Suggested first decomposition:

```text
SM_MH_Shell_Main
SM_MH_Roof_Main
SM_MH_Roof_Wing
SM_MH_Porch_Stairs
SM_MH_Tower
SM_MH_Trim_Hero
SM_MH_Railings_Exterior
SM_MH_Windows_Frames
SM_MH_Doors
SM_MH_Glass_Exterior
SM_MH_BlueRoom_Shell
SM_MH_BlueRoom_WaterProxy

SM_MH_Furn_Bedroom_Set
SM_MH_Furn_Salon_Set
SM_MH_Furn_Kitchen_Set
SM_MH_Furn_Wardrobe_Set
SM_MH_Furn_ResonanceMobile
```

This is a starting granularity, not an immutable law.

Split when a boundary matters for:

- material/rendering mode;
- collision;
- transform / pivot;
- streaming / visibility;
- hero iteration;
- animation;
- runtime interaction.

Join when multiple tiny pieces always move/render together and individual identity provides no value.

---

# ♪ Nanite candidate strategy

Use Nanite as a **candidate for dense static opaque geometry**, not as a checkbox applied blindly to every object.

Strong candidates:

```text
main shell
roof masses
baked roof-scale clusters
hero Rocaille / shell trim
stone / grotto shell
static stair + porch masses
ornamental tower shell
```

Conditional candidates:

```text
railings
window frames
furniture hard frames
small shell ornaments
```

Test these for screen-size / tiny-triangle behavior and actual cost.

Keep transparent / special-rendering objects separate from the first Nanite candidate set unless the project's UE5.8 validation proves the chosen material path behaves correctly:

```text
window glass
water surface
special translucent drapes
some VFX-like luminous pieces
```

### Shingle rule

Do **not** export every procedural shingle as a separately named Static Mesh Actor.

Preferred first test:

```text
procedural shingle instances in Blender
→ export-copy realization
→ merge by roof section / material boundary
→ import as dense static roof-scale mesh
→ test Nanite
```

Alternative if repeated-instance performance proves better in the actual project:

```text
small reusable shingle mesh
→ UE instancing / PCG / HISM-style placement
```

Choose from measured runtime evidence, not ideology.

---

# 𝄞 Pivot strategy

Every exported asset needs an intentional pivot.

### Building chunks

Prefer pivots that make reassembly deterministic:

```text
house shell / roof chunks → common house origin
standalone tower          → tower base center if independently placed
stairs                    → lowest central landing
furniture                 → floor contact / logical placement origin
hanging mobile            → suspension point
wall fixtures             → wall attachment point
```

For multi-mesh house assembly, using a **shared house origin** is often worth the larger coordinates because chunks snap back into place without hand reconstruction.

### Rule

Record which assets use:

```text
COMMON_ORIGIN
LOCAL_LOGICAL_PIVOT
```

Do not mix accidentally.

---

# ♫ Scale + transforms

House authoring rule remains:

```text
Blender: Metric
1 Blender Unit = 1 meter
```

Before export-copy handoff:

- validate real-world dimensions with the 1.7 m mannequin;
- apply scale on export duplicates when required by the chosen exporter;
- preserve correct axis conversion through the tested pipeline;
- never compensate for a broken import by arbitrarily scaling actors in Unreal without understanding the source.

### Acceptance check

A 1 m Blender cube must arrive as the expected 100 cm Unreal size through the chosen pipeline.

Prove this once before moving the hero house.

---

# ♬ Naming contract

Follow project / Epic-style prefixes already used in repo planning.

### Static meshes

```text
SM_MH_Shell_Main
SM_MH_Roof_Main
SM_MH_Roof_Wing
SM_MH_Tower
SM_MH_Trim_Hero
SM_MH_Furn_Bed
SM_MH_Furn_Mirror_L
```

### Materials

```text
M_MH_Surface_Master
MI_MH_Plaster_Pink
MI_MH_Roof_BlueLavender
MI_MH_Brass_Warm
```

### Textures

```text
T_MH_Plaster_D
T_MH_Plaster_N
T_MH_Plaster_ORM
```

### Assembly Blueprint

```text
BP_MH_HouseAssembly
```

The assembly Blueprint may own **placement / component composition**.

It must not become a second source of narrative, wardrobe or persistence truth.

---

# ♪ Material slot export contract

Before export, every opaque hero chunk should have a bounded material-slot list.

Example shell:

```text
0 Plaster
1 IvoryTrim
2 Brass
3 Wood
4 Pearl
```

Example roof:

```text
0 RoofScale
1 IvoryTrim
2 Brass
```

Glass should usually be separated into `SM_MH_Glass_*` meshes rather than hidden among opaque sections.

### Important

Do not rely on arbitrary Geometry Nodes named attributes magically becoming useful Unreal metadata through FBX.

Use tested handoff channels:

- material slots;
- mesh naming;
- vertex colors when intentionally tested;
- separate meshes;
- optional generated sidecar metadata later.

---

# ♫ UV + texel strategy

Each export candidate needs explicit UV intent.

### UV0

Use for the primary material / textures.

### Secondary UV requirements

If the final lighting path requires a dedicated lightmap UV, create/validate it according to the actual UE project lighting strategy.

Do not spend tonight hand-authoring lightmap UVs for everything before knowing whether the asset path needs them.

### Hero trim

For curve-derived trim:

- ensure seam placement is predictable;
- avoid extreme stretching around shell curls;
- use trim-sheet / tiling strategies where appropriate instead of giant unique texture sheets.

---

# 𝄞 Collision plan

Collision should match gameplay need, not visible ornament.

### Main shell

Use simplified collision for:

- walls;
- floors;
- stairs;
- porch;
- major columns.

### No collision by default

```text
shingles
small Rocaille trim
pearl beads
window muntins
hanging chandelier drops
most decorative clutter
```

### Furniture

Only create collision if the player / camera / physics can meaningfully interact with it.

Examples:

- bed: simple box / capsule-like hulls if needed;
- cabinets: simple box hull;
- chairs: often no collision unless player traversal requires it;
- Resonance Mobile: no player collision.

Avoid complex-as-simple collision on huge ornate meshes without profiling.

---

# ♬ Export-copy realization rules

Realize instances only when the destination needs final mesh topology.

### Usually realize on export copy

```text
roof shingles when baking roof clusters
rocaille instance sets that become one hero trim mesh
repeated shell / pearl ornaments when exported as one static chunk
```

### Usually keep logically separate until assembly

```text
doors
windows / glass
furniture sets
mobile / chandelier
hero mirror
water
interactive fixtures
```

### Never destructively realize because "it looks done"

The live authoring collection must remain procedural.

---

# ♪ Suggested Unreal folder

```text
/Game/Melodia/Environment/MelusinasHouse/
├── Meshes/
│   ├── Architecture/
│   ├── Furniture/
│   ├── Props/
│   └── Collision/
├── Materials/
│   ├── Masters/
│   └── Instances/
├── Textures/
├── Blueprints/
├── Audio/
├── VFX/
└── Tests/
```

Do not scatter house assets across unrelated content roots.

---

# ♫ `BP_MH_HouseAssembly`

Purpose:

```text
one reproducible placement root
+ architecture components
+ furniture anchors
+ light / VFX anchors
+ optional debug tags
```

It may include child Static Mesh Components or spawn/place asset groups.

It should **not** own:

- narrative flags;
- wardrobe truth;
- save data;
- encounter progression;
- canonical rhythm state.

If gameplay needs a house-aware actor later, interface with canonical Melodia subsystems instead of hiding state in this assembly Blueprint.

---

# 𝄞 Room anchor contract

Export / create stable anchors for:

```text
ANCH_MH_Salon
ANCH_MH_Bedroom
ANCH_MH_Wardrobe
ANCH_MH_Stair
ANCH_MH_Balcony
ANCH_MH_Kitchen
ANCH_MH_BlueRoom
ANCH_MH_Tower
```

Also useful:

```text
ANCH_MH_Entry
ANCH_MH_ResonanceMobile
ANCH_MH_MirrorHero
ANCH_MH_WaterCenter
```

These are spatial anchors, not state owners.

They make later:

- cinematics;
- audio placement;
- interaction spots;
- lighting rigs;
- narrative staging

much easier.

---

# ♪ Lighting handoff

Do not export Blender lights as if they are authoritative final UE lighting.

Instead export geometry and optional named light anchors.

Suggested UE lighting roles:

```text
warm interior practicals
cool sea/window fill
Blue Room reflected cyan
very restrained pearl accent
moonlight / dusk exterior key
```

The house should still read when all magical glow is disabled.

---

# ♫ Acoustic handoff

Phase 2 defines:

```text
GATHER
GUIDE
RELEASE
```

Blender may visualize these roles.

For Unreal, carry only the **spatial intent**:

- room anchors;
- optional named volumes / helper meshes;
- architecture shape;
- placement notes.

Runtime reverb, occlusion, music response and Convergence interpretation belong to Unreal/audio systems.

Do not export fake acoustic simulation as truth.

---

# ♬ House export manifest

Create a lightweight manifest during the first real export pass.

Suggested future path:

```text
Saved/Audit/melusinashouse/export/mh_export_manifest.json
```

Suggested fields:

```json
{
  "asset_id": "SM_MH_Roof_Main",
  "source_object": "MH_EXPORT_Roof_Main",
  "pivot_mode": "COMMON_ORIGIN",
  "nanite_candidate": true,
  "material_slots": ["RoofScale", "IvoryTrim", "Brass"],
  "collision": "NONE",
  "status": "EXPORTED_NOT_RUNTIME_PROVEN"
}
```

Do not commit generated audit output automatically unless the project evidence policy calls for it.

---

# ♪ First handoff test — one vertical slice of the house

Do **not** begin by exporting the entire completed house.

Use one bounded proof:

```text
front center bay
+ one roof section with shingles
+ one window
+ one Rocaille crest
+ porch / stair chunk
+ one furniture prop
```

### Test sequence

1. duplicate into `MH_EXPORT`;
2. validate scale;
3. validate pivot strategy;
4. realize only required instances;
5. verify material slots;
6. export through the project's tested Blender→UE path;
7. import into `/Game/Melodia/Environment/MelusinasHouse/Tests/`;
8. assign UE material instances;
9. test Nanite on opaque dense candidates;
10. create simple collision where needed;
11. inspect from gameplay-like camera distance;
12. re-export one changed parameter and prove iteration is painless.

**Gate:** do not export the rest of the house until the re-export round trip is boring.

---

# 𝄞 Nanite validation checklist

For each Nanite candidate, record:

```text
imports successfully
material path supported
silhouette correct
no obvious tiny-geometry catastrophe
acceptable memory / render behavior
collision remains intentional
reimport does not break material assignments unexpectedly
```

A checkbox in the Static Mesh editor is not proof.

---

# ♪ Laptop / Hermes execution order

```text
1. git pull
2. read melusinashouseplan.md
3. read Phase 2 asset + room plans
4. read Phase 3 furniture + shader plans
5. open dedicated Melusina house WIP .blend
6. create MH_EXPORT collection
7. choose one bounded exterior slice
8. duplicate + prepare export copies
9. export to a temporary handoff directory
10. import into UE test folder
11. capture scale/material/Nanite/collision evidence
12. only then expand the export set
```

Hermes should never save over the protected live portfolio stage just to perform this proof.

---

# ♫ Evidence captures

Save local evidence under:

```text
Saved/Audit/melusinashouse/export/
```

Suggested screenshots:

```text
MH_EXP_blender_export_collection.png
MH_EXP_ue_scale_check.png
MH_EXP_ue_material_slots.png
MH_EXP_ue_nanite_test.png
MH_EXP_ue_collision.png
MH_EXP_reimport_proof.png
```

Useful proof text:

```text
SOURCE EXISTS
BLENDER EXPORT PROVEN
UE IMPORT PROVEN
NANITE CANDIDATE PROVEN
COLLISION PROVEN
REIMPORT PROVEN
```

Do not jump directly from "FBX exists" to "game-ready."

---

# ♬ Definition of done

The Phase-3 Unreal handoff is successful when:

- the `.blend` remains editable and procedural;
- a separate `MH_EXPORT` collection exists;
- one representative house slice imports at correct scale;
- pivots are deliberate;
- material slots map predictably;
- glass/water remain separated from the first opaque Nanite proof;
- collision exists only where gameplay needs it;
- Nanite candidates have been inspected in Unreal rather than assumed;
- one parameter change can be re-exported without rebuilding the scene manually;
- `BP_MH_HouseAssembly` remains an assembly surface rather than a hidden state authority.

---

> **The Blender house is the instrument being built. The Unreal house is the instrument being played. Keep the handoff legible.** 𝄞
