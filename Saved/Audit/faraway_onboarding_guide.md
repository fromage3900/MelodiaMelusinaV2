# Faraway Mother — New Team Member Onboarding Guide

**Date:** 2026-09-01 | **Phase:** P1 first-class (`grand_review` phase_2)  
**Bible:** `MONOLITH_LEVEL_DESIGN_BIBLE_2026-08-26.md` #10 — The Monolith (Faraway Mother)  
**Status doc:** `Saved/Audit/faraway_p1_status.json` (verified on-disk, no fabrication)  
**Taxonomy spec:** `Saved/Audit/faraway_in_taxonomy.md`

---

## 1. What the Faraway Mother is (30 seconds)

A reclining maternal figure whose body *is* the terrain. The player walks through the valley of her torso, toward her shoulder ridge, under a horizon silhouette that never shows full anatomy — only suggestion. Fabric physics are the geology: pleats are strata, seams are canyons, embroidery paths are roads. Four of the six wardrobe suites drape her slopes as foliage.

Not a character rig. A **landscape sculpture + fabric biome**.

---

## 2. Where everything lives

```
deploy/surreal_arch/melodia_gn/
  mother.py        — 8 horizon/body builders (816 lines)
  mother_v3.py     — 8 dressing/foliage builders (647 lines)
  core.py          — CATEGORY_META["mother"] = Faraway Mother (MESH_MONKEY)

Saved/Audit/faraway_mother/
  heroes/          — 3 hero OBJs + 6 QA renders (Blender 4.5.4 LTS)
    SM_FM_MotherSilhouette.obj  3.3 MB  66k pts  65k faces  (horizon card, 6-9 km out)
    SM_FM_EyeLandmark.obj       1.9 MB  35k pts  34k faces  (Beat H eye-hill)
    SM_FM_Lantern.obj            6 KB   132 pts   264 faces (foreground prop)
  terrain/         — 5 biome tiles + 10 renders + 5 .r16 heightmaps
    SM_FM_Hemlands.obj / HM_FM_Hemlands.r16
    SM_FM_PleatedRange.obj / HM_FM_PleatedRange.r16
    SM_FM_EmbroideredBasin.obj / HM_FM_EmbroideredBasin.r16
    SM_FM_VeiledMountains.obj / HM_FM_VeiledMountains.r16
    SM_FM_SeamRoad.obj / HM_FM_SeamRoad.r16
  textures/        — 6 fabric-material kit PNGs (textures_manifest.json)
    T_FM_PleatDetail_N.png    1024  data (pleat normal)
    T_FM_PleatDetail_2_N.png  1024  data (second pleat variant)
    T_FM_SeamMask.png         1024  data (valley mask)
    T_FM_Embroidery_A/B.png  1024  sRGB (stitch atlases)
    T_FM_FabricWeave_N.png    512  data (weave normal)
  SM_ClothMountains_v0.obj    8.8 MB grid 384 (hero cloth-mountain tile)
  renders/         — cloth-mountain QA (Aerial + North)

Content/Textures/FarawayMother_Suites/  — 47 PNG + 47 .uasset (6 suites)
  Corset_GildedAcanthusBrocade   7 maps  (AO BC H M N ORM R)
  Cradle_CarvedAlabasterWood     7 maps
  Gown_CelestialSilkJacquard     8 maps  (+ Sheen)
  Mantle_NightSkyVelvet           8 maps  (+ Sheen)
  Ornament_NacreMusicBoxJewel    8 maps  (+ Sheen)
  Veil_AquaticLullabyLace        9 maps  (+ Alpha, Mask)

Docs/Production/GN_TAXONOMY_2026-08-29.md  — STALE (199 builders; missing mother)
Saved/Audit/faraway_p1_status.json        — verified counts (238 actual)
Saved/Audit/faraway_in_taxonomy.md        — integration spec
Saved/Audit/FarawayMother_ContactSheet.png — 2.2 MB contact sheet (6 original suites)
```

---

## 3. The 16 GN builders (what to reach for)

**Horizon/Body — `mother.py`:**

1. `MEL_mother_head_silhouette` — moonlit face profile on the horizon. Place at 6–9 km, no parallax.
2. `MEL_mother_hair_cascade` — ribbon waterfall as hair. Ribbon contract; pairs with fog.
3. `MEL_mother_valley_depression` — torso valley the player walks through. Negative space.
4. `MEL_mother_fog_volume` — volumetric haze implying mass. No mesh, attribute-only.
5. `MEL_mother_fabric_ridge` — skin surface with pleat normals. Textured with `T_FM_PleatDetail_N`.
6. `MEL_mother_shoulder_fold` — anatomical fold terrain. Same pleat constants as cloth-mountains.
7. `MEL_mother_heart_gate` — rhythm checkpoint at valley heart. Connect to cymatics gate.
8. `MEL_mother_moonlight_rig` — 3-light rig (key/fill/rim) for the silver-blue key light.

**Dressing/Foliage — `mother_v3.py`:**

9. `MEL_mother_walkway_straight` — straight draped-cloth path (Length/Width/Fold Depth/Frequency/Tension).
10. `MEL_mother_walkway_curved` — 90° fabric arc (Radius/Angle/Width/Fold Depth/Frequency).
11. `MEL_mother_frill_rock` — rock that is frozen fabric (Height/Frill Count/Frill Depth/Base Radius/Sharpness).
12. `MEL_mother_frill_arch` — walk-through frill arch.
13. `MEL_mother_lace_tree` — lace-canopy tree → `Veil_AquaticLullabyLace` suite.
14. `MEL_mother_pearl_bush` — pearl-berry bush → `Ornament_NacreMusicBoxJewel` suite.
15. `MEL_mother_silk_vine` — silk-ribbon vine → `Gown_CelestialSilkJacquard` suite.
16. `MEL_mother_brocade_flower` — brocade-petal flower → `Corset_GildedAcanthusBrocade` suite.

All 16 reuse existing masters (`MI_Master_Nikki_Landscape`, `MI_Master_Toon_Universal_Alpha`) — no new masters.

---

## 4. Your first hour (hands-on)

### Step 0 — Verify the registry (no Houdini needed)

```bash
python -c "from deploy.surreal_arch.melodia_gn.core import GROUP_BUILDERS, GROUP_METADATA; \
  print([k for k in GROUP_BUILDERS if 'mother' in k])"
# Expect 16 MEL_mother_* entries
```

### Step 1 — Inspect a hero mesh (Blender or Meshlab)

Open `Saved/Audit/faraway_mother/heroes/SM_FM_MotherSilhouette.obj`. Check silhouette from low camera — head profile should read as ridge, not anatomy.

### Step 2 — Spawn a builder in Blender (Hython)

```python
import bpy
from deploy.surreal_arch.melodia_gn.mother import build_mother_fabric_ridge
tree = build_mother_fabric_ridge()  # creates Geometry Nodes group MEL_mother_fabric_ridge
# Add Geometry Nodes modifier to a plane, assign the group, tweak Fold Depth
```

### Step 3 — Place a foliage builder

```python
from deploy.surreal_arch.melodia_gn.mother_v3 import build_mother_lace_tree
tree = build_mother_lace_tree()
# Instance on terrain points; assign MI_FarawayMother_Veil_* to canopy instances
```

### Step 4 — Check the QA renders

Open `Saved/Audit/faraway_mother/heroes/renders/` and `terrain/renders/` — 18 PNGs (Aerial + North per mesh), Blender 4.5.4 LTS clay renders. If any mesh looks wrong, re-bake via `Tools/Houdini/` copernicus dress-bake.

---

## 5. Common pitfalls

| Mistake | Why it hurts | Do instead |
|---------|--------------|------------|
| Modeling more anatomy on the silhouette | Breaks Bible Beat E — Mother is suggestion, not model | Keep `head_silhouette` as ridge; fog + moonlight do the work |
| Using hero OBJ as Landscape heightmap | Hero is mesh sculpture, not heightfield | Use `terrain/HM_*.r16` for Landscape; heroes are `StaticMesh` |
| Creating new fabric masters | `mother_v3.py` header: "No new materials. Pure GN geometry." | Reuse `M_Master_Nikki*` / `M_Master_Toon_Universal*` |
| Importing at 1.0 scale | OBJs are in meters; UE is cm | Import at 100x (manifest `ue_import.scale`), Nanite ON |
| Editing `GN_TAXONOMY_2026-08-29.md` to add mother and stopping | Taxonomy stale is a symptom, not the gate | Also verify registry = 238, not 199; see `faraway_in_taxonomy.md` |

---

## 6. What is still open (P1 stretch)

- **V3 PBR gaps:** `mother_v3` foliage builders have GN geometry but no dedicated `T_FM_Walkway_*` / `T_FM_Frill_*` texture sets yet. They reuse the 6 suite PBRs. Dedicated sets are tracked in `faraway_mother_v3_asset_import_gap_spec_2026-09-01.json` (queued).
- **MI materialization:** `faraway_p2_2026-08-30.json` proposes 6 `MI_FarawayMother_*_R045_Tile1_Unique` instances under `Content/EnvSandbox/Materials/Instances/FarawayMother/P2/` — PNG+uasset pairs exist, MI assets not yet materialized (editor gate).
- **Taxonomy doc sync:** `Docs/Production/GN_TAXONOMY_2026-08-29.md` needs bumping to 238 / 13 categories. Spec in `faraway_in_taxonomy.md`.
- **P1 ledger:** `P1_TASK_LEDGER.json` not yet materialized; `faraway_p1_status.json` is the evidence to cite when it is.

---

## 7. Contacts & references

- **Bible:** `MONOLITH_LEVEL_DESIGN_BIBLE_2026-08-26.md` #10
- **Coinsheet:** `Saved/Audit/ue_level_building_coinsheet_2026-09-01.json` (p2_status, hython_build_session)
- **Plan:** `Saved/Audit/grand_review_expansion_plan_2026-09-01.json` phase_2
- **Master Index:** `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` (§1 PRESENT list)
- **Blend showcases:** `Saved/Audit/faraway_mother_full_showcase.blend`, `faraway_mother_grandmaster.blend`
