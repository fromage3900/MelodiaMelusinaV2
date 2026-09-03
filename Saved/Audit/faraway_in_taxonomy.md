# Faraway Mother — Master Taxonomy Integration Spec

**Date:** 2026-09-01  
**Phase:** grand_review phase_2_faraway_p1 (rec_2)  
**Status:** SPEC — code PRESENT, taxonomy doc STALE  
**Evidence:** `Saved/Audit/faraway_p1_status.json` (verified on-disk)

---

## 1. What exists in code today

| Fact | Evidence |
|------|----------|
| **Category key `mother`** exists in `core.py:CATEGORY_META` | `{"label":"Faraway Mother","icon":"MESH_MONKEY"}` |
| **16 builders registered** under `mother` | `mother.py` 8 + `mother_v3.py` 8, each `register_builder(..., "mother")` |
| **Total registry** | 238 builders across 48 files (vs taxonomy doc claim 199) |
| **Taxonomy doc** | `Docs/Production/GN_TAXONOMY_2026-08-29.md` — 0 hits for `MEL_mother_*`, category `mother` absent, count stale |

**Conclusion:** Mother is PRESENT in the runtime registry but invisible in the taxonomy document. Integration is a doc-sync + surfacing task, not a code task.

---

## 2. Taxonomy placement

### 2.1 Category rank

Insert `mother` as **category 13** (after `set_dressing` 12) in `CATEGORY_META` ordering. It already exists at end of dict; promote by reordering so GN Stack UI groups it with terrain/biome ops rather than buried at bottom.

Proposed `CATEGORY_META` order (12 -> 13):

```
primitives, profiles, math_attrs, structures, effects, ornament, filigree,
music, castle, operations, mesh_tools, set_dressing,
mother (Faraway Mother),          # NEW — fabric-mountain biome
white_current, god_molts          # existing tail
```

If strict numeric ordering matters, assign `mother` sort key 13 and bump `white_current`/`god_molts` to 14/15.

### 2.2 Subgrouping the 16 builders

The 16 builders split into two functional subgroups that should be labeled in the taxonomy table, not left flat:

**A. Horizon/Body (8) — `mother.py` — the torso as terrain:**

| Builder | Role | Taxonomy note |
|---------|------|---------------|
| `MEL_mother_head_silhouette` | `geometry` — horizon card | Pairs with `SM_FM_MotherSilhouette` hero; no parallax per Bible Beat E |
| `MEL_mother_hair_cascade` | `geometry` — ribbon cascade | Fabric-strand instancer; shares ribbon contract with `MEL_ribbon_curve` |
| `MEL_mother_valley_depression` | `deform` — terrain depression | Valleys are negative space; complement to `MEL_mother_fabric_ridge` |
| `MEL_mother_fog_volume` | `volume` — mass implication | Non-mesh; attribute-only output for volumetric fog |
| `MEL_mother_fabric_ridge` | `geometry` — normal-mapped ridge | Skin surface; consumes `T_FM_PleatDetail_N` / `T_FM_FabricWeave_N` |
| `MEL_mother_shoulder_fold` | `geometry` — anatomical fold | Shoulder/chest fold; uses same pleat constants as `cloth_mountains` |
| `MEL_mother_heart_gate` | `factory` — checkpoint collider | Rhythm gate; contract with `MelodiaCymaticsSubsystem` + heart-gate PPV |
| `MEL_mother_moonlight_rig` | `light` — 3-light rig | Key/fill/rim lights for the Monolith key; writes stored light attributes |

**B. Dressing/Foliage (8) — `mother_v3.py` — the hem as biome:**

| Builder | Role | Taxonomy note |
|---------|------|---------------|
| `MEL_mother_walkway_straight` | `geometry` — fabric path | Grid + fold math; sibling to `MEL_mother_walkway_curved` |
| `MEL_mother_walkway_curved` | `curve` — 90° fabric arc | Arc-to-mesh; same Width/Fold Depth contract as straight |
| `MEL_mother_frill_rock` | `geometry` — frozen fabric rock | Rock that is fabric; bridges `structures` ↔ `mother` |
| `MEL_mother_frill_arch` | `geometry` — walk-through arch | Walk-through; pairs with `SeamRoad` tile seam |
| `MEL_mother_lace_tree` | `instance` — foliage-fabric | Lace canopy; consumes `T_FarawayMother_Veil_AquaticLullabyLace` family |
| `MEL_mother_pearl_bush` | `instance` — foliage-jewel | Pearl berries; consumes `T_FarawayMother_Ornament_NacreMusicBoxJewel` |
| `MEL_mother_silk_vine` | `instance` — foliage-fabric | Silk ribbon leaves; consumes `T_FarawayMother_Gown_CelestialSilkJacquard` |
| `MEL_mother_brocade_flower` | `instance` — foliage-fabric | Brocade petals; consumes `T_FarawayMother_Corset_GildedAcanthusBrocade` |

### 2.3 Cross-system contracts

| Mother builder | Consumes | Produces | Owner subsystem |
|----------------|----------|----------|-----------------|
| `head_silhouette` | Hero OBJ `SM_FM_MotherSilhouette` | `Geometry` horizon card | Level (L2/L3 World Partition) |
| `fabric_ridge` / `shoulder_fold` | `T_FM_PleatDetail_N`, `T_FM_SeamMask` | Displaced mesh with `UVMap` + `fabric_mask` attr | `mother` |
| `lace_tree` / `pearl_bush` / etc. | Suite PBR (Veil/Ornament/Gown/Corset) | Instanced foliage with `material_variant` attr | `mother` → `PCG` |
| `heart_gate` | Cymatic beat phase | Collider + `gate_active` bool attr | `mother` ↔ `UMelodiaCymaticsSubsystem` |
| `moonlight_rig` | `MPC_Melodia_Palette` moonlight vector | `key_light` / `fill_light` / `rim_light` stored attrs | `mother` ↔ `AudioReactive` |

---

## 3. Integration into the three taxonomy surfaces

### 3.1 `deploy/surreal_arch/melodia_gn/core.py`

No change required — `mother` already in `CATEGORY_META`. Optional: reorder dict for UI sort.

### 3.2 `deploy/surreal_os/schema/procedural_taxonomy.json`

No change required — this file models the *Zen garden* (`GB_ZEN_*`) ecosystem, not the `MEL_*` GN taxonomy. Mother does not belong here. If a unified schema is desired later, add a `faraway_mother` key under `generators` with the 16 builders — but that is P1 stretch, not gate.

### 3.3 `Docs/Production/GN_TAXONOMY_2026-08-29.md` — REQUIRED

Patch the doc to 238 builders, 13 categories, and insert §13:

```md
### 13. Faraway Mother (16 builders) — category `mother`

| Builder | Label | Description | Presets | Role |
|---------|-------|-------------|---------|------|
| MEL_mother_head_silhouette | Mother Head Silhouette | Sculpted ridge that reads as reclining face | 0 | geometry |
| MEL_mother_hair_cascade | Mother Hair Cascade | Ribbon waterfall as flowing hair | 0 | geometry |
| MEL_mother_valley_depression | Mother Valley Depression | Torso-valley the player walks through | 0 | deform |
| MEL_mother_fog_volume | Mother Fog Volume | Haze implying distant mass (no mesh) | 0 | volume |
| MEL_mother_fabric_ridge | Mother Fabric Ridge | Normal-mapped ridge — skin of the Mother | 0 | geometry |
| MEL_mother_shoulder_fold | Mother Shoulder Fold | Shoulder/chest fold terrain | 0 | geometry |
| MEL_mother_heart_gate | Mother Heart Gate | Rhythm checkpoint at valley heart | 0 | factory |
| MEL_mother_moonlight_rig | Mother Moonlight Rig | Silver-blue directional rig (key/fill/rim) | 0 | light |
| MEL_mother_walkway_straight | Mother Walkway Straight | Straight draped-cloth path | 0 | geometry |
| MEL_mother_walkway_curved | Mother Walkway Curved | 90° curved fabric path | 0 | curve |
| MEL_mother_frill_rock | Mother Frill Rock | Frozen fabric rock formation | 0 | geometry |
| MEL_mother_frill_arch | Mother Frill Arch | Walk-through frill arch | 0 | geometry |
| MEL_mother_lace_tree | Mother Lace Tree | Lace-canopy tree (foliage-fabric) | 0 | instance |
| MEL_mother_pearl_bush | Mother Pearl Bush | Pearl-berry bush (foliage-jewel) | 0 | instance |
| MEL_mother_silk_vine | Mother Silk Vine | Silk-ribbon vine | 0 | instance |
| MEL_mother_brocade_flower | Mother Brocade Flower | Brocade-petal flower | 0 | instance |
```

Also update the stats header: `Builder files 38 → 40` (mother.py + mother_v3.py already counted), `Registered builders 199 → 238`, `Categories 12 → 13` (or 15 if counting `white_current`/`god_molts`).

---

## 4. Material pipeline integration

| Texture set | Builder consumer | Material master |
|-------------|------------------|-----------------|
| `T_FM_PleatDetail_N` / `_2_N` (1024) + `T_FM_SeamMask` (1024) | `fabric_ridge`, `shoulder_fold` | `MI_Master_Nikki_Landscape` (parallax) |
| `T_FarawayMother_Corset_*` (7 maps) | `brocade_flower` petals | `M_Master_Toon_Universal` |
| `T_FarawayMother_Gown_*` (+ Sheen) | `silk_vine` leaves | `M_Master_Nikki` |
| `T_FarawayMother_Veil_*` (+ Alpha/Mask) | `lace_tree` canopy | `M_Master_Toon_Universal_Alpha` |
| `T_FarawayMother_Ornament_*` | `pearl_bush` berries | `M_Master_Toon_Universal` |
| `T_FarawayMother_Mantle_*` | Future: terrain mantle / fog volume tint | `M_Master_Nikki` |

V3 foliage builders reuse existing masters — no new masters per `mother_v3.py` header. The `faraway_p2_2026-08-30.json` proposals map 6 suites → `MI_FarawayMother_*_R045_Tile1_Unique` under `Content/EnvSandbox/Materials/Instances/FarawayMother/P2/` — those MI materializations are the P1 texture→material gate.

---

## 5. Governance

- **Owner:** `mother` category (P1 Faraway Mother subsystem).
- **Do not duplicate:** Any new fabric-mountain geometry must extend `mother` or `mother_v3`, not create a parallel `fabric_terrain` category.
- **Blocked by:** Nothing — code is PRESENT. Doc sync is the only required mutation.
- **Evidence for P1 gate:** `Saved/Audit/faraway_p1_status.json` + this spec.
