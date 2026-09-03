# The Faraway Mother — Production Sheet

**Date:** 2026-08-29  
**Concept:** Monolith — fabric-mountain/body-landscape  
**Source:** `Docs/Art/MONOLITH_CONCEPT_ART_BACKLOG_2026-08-26.md`  
**Status:** Build-ready — instances only, no new materials

---

## Core Phenomenon

A distant maternal silhouette visible on the moonlit horizon. The "body" is a mountain range shaped like a reclining figure — fabric ridges suggest skin/folds, waterfalls suggest hair. The player walks through the "torso valley" without ever seeing full anatomy. Rhythm stabilizes the local moon phase; fashion silhouettes with celestial/marine motifs affect whether membrane paths open.

---

## Body Map — Model vs. Implied

| Body Part | Approach | Asset | Instance |
|-----------|----------|-------|----------|
| Face/head silhouette | Modeled (hero mesh) | Existing landscape + sculpted ridge | `BP_MotherHead_Silhouette` instance |
| Hair/waterfall cascade | Modeled (Niagara ribbon) | `M_Oceanology_NikkiHero` or toon waterfall | `BP_HairCascade` instance |
| Shoulder/chest folds | Implied (terrain + normal) | `MI_Master_Nikki_Landscape` fabric normal | Terrain instance |
| Torso valley | Implied (terrain depression) | Existing landscape + fog | Terrain instance |
| Distant limbs | Implied (silhouette + haze) | No mesh — moon haze only | Fog volume instance |
| Hands/feet | Implied (rock formations) | Existing rock assets | Scattered props |

---

## GN Builders

### 1. MEL_terrain_fabric_ridge
Fabric normal-mapped terrain ridge. Inputs: Width, Height, Fold Depth, Fold Count. Uses existing `MI_Master_Nikki_Landscape` as material override.

### 2. MEL_cascade_hair_ribbon
Ribbon waterfall cascade. Inputs: Length, Width, Flow Speed, Strand Count. Translucent moonlit material.

### 3. MEL_moon_haze_volume
Volumetric fog box that implies distant mass. Inputs: Density, Height, Tint, Falloff. Silver-blue moonlit tint.

### 4. MEL_valley_depression
Terrain depression with fog fill. Inputs: Radius, Depth, Fog Level, Floor Material.

### 5. MEL_mother_head_silhouette
Sculpted ridge silhouette — the readable "face". Inputs: Profile Scale, Ridge Count, Fold Depth. Uses existing toon master.

---

## Material Instances (no new masters)

| Instance | Base Master | Key Params |
|----------|-------------|------------|
| `MI_Mother_FabricRidge` | `MI_Master_Nikki_Landscape` | Fabric normal intensity 2.0, cool moonlit tint (0.15, 0.20, 0.35) |
| `MI_Mother_HairCascade` | `MI_Master_Toon_Universal_Alpha` | Translucency 0.8, moon reflection, slow flow |
| `MI_Mother_MoonHaze` | Existing fog material | Silver-blue (0.70, 0.75, 0.90), density 0.04 |
| `MI_Mother_ValleyFloor` | `MI_Master_Nikki_Landscape` | Dark cool grey, wet specular, ripple normal |

---

## Level Layout — LV_FarawayMother_Prototype

```
Composition (top-down, not to scale):

  [MOON] — low horizon, silver-blue key
    |
  [HEAD SILHOUETTE] — sculpted ridge (hero mesh)
    |                    Face profile reads left
  [HAIR CASCADE] — Niagara ribbon from head down
    |
  [SHOULDER VALLEY] — terrain depression, fog-filled
    |                    Player walks here (gameplay lane)
  [TORSO DEPRESSION] — deeper valley, denser fog
    |
  [DISTANT LIMBS] — implied by moon haze (no mesh)
    |
  [CHECKPOINT GATE] — rhythm gate at "heart"
```

---

## Rhythm + Fashion Integration

| System | Hook |
|--------|------|
| Moon phase | Beat-synchronized intensity (breathing — she's alive) |
| Fog density | Rhythm accuracy controls fog clarity (see more when in sync) |
| Highway | Notes travel along hair cascade ribbon |
| Fashion | Celestial/marine silhouettes open membrane paths in the valley |
| Checkpoint | Rhythm gate at "heart" — stabilize the moon to proceed |

---

## Evidence Standard

1. PIE session with labeled overlay (matches this sheet)
2. Assertion report JSON next to captures
3. `Saved/gate_ledger.json` row for `faraway_mother_prototype`
4. SHA-256 hashes of new assets/instances

---

## Build Order

1. Production sheet (this doc) — DONE
2. GN builders (5 new, instances only) — ~2 hrs
3. PIE layout + capture — ~30 min
4. Evidence + ledger — ~15 min
