# The White Current — Production Sheet

**Date:** 2026-08-29  
**Concept:** P2-01 — White seam that standardizes water  
**Source:** `Docs/Art/MONOLITH_CONCEPT_ART_BACKLOG_2026-08-26.md`  
**Status:** Build-ready — instances only, no new materials

---

## Core Phenomenon

All water systems develop a too-still, too-clear white seam that standardizes water. The production rule: the seam is the visible trace of something vast moving beneath connected water networks. The player sees the effect (white seam) but never the full cause (eel/oarfish).

---

## Body Map — Model vs. Implied

| Body Part | Approach | Asset | Instance |
|-----------|----------|-------|----------|
| White seam (visible trace) | Modeled (shader + spline) | Existing water material + white seam shader | `BP_WhiteSeam_Spline` instance |
| Eel/oarfish silhouette | Modeled (hero mesh) | Existing toon master + translucent material | `BP_Eel_Silhouette` instance |
| Water network | Implied (spline system) | Existing water splines | Spline instances |
| Moonlit surf | Modeled (water plane) | Existing water material | `BP_Moonlit_Surf` instance |
| Distant mass | Implied (fog + haze) | Existing fog material | Fog volume instance |

---

## GN Builders

### 1. MEL_white_seam_spline
White seam that follows a water spline. Inputs: Width, Flow Speed, Seam Intensity, Turbulence. Uses existing water material with white seam overlay.

### 2. MEL_eel_silhouette
Pale eel/oarfish silhouette that moves beneath the surface. Inputs: Length, Body Width, Fin Count, Glow Intensity, Translucency. Uses existing toon master.

### 3. MEL_water_network
Connected water network spline system. Inputs: Node Count, Connection Density, Flow Direction, White Level. Uses existing water splines.

### 4. MEL_moonlit_surf
Moonlit water surface with white seam reflection. Inputs: Surface Size, Wave Height, Moon Reflection, Seam Visibility. Uses existing water material.

### 5. MEL_white_haze_volume
Volumetric haze that implies the eel's distant mass. Inputs: Density, Height, Tint, Falloff. Uses existing fog material.

### 6. MEL_current_marker
Flow-direction arrow instances that trace the eel's path. Inputs: Count, Spacing, Arrow Size, Glow. Uses existing toon master.

---

## Material Instances (no new masters)

| Instance | Base Master | Key Params |
|----------|-------------|------------|
| `MI_WhiteSeam_Trace` | `MI_Master_Toon_Universal_Alpha` | White (0.95, 0.95, 1.0), emission 1.5, translucent |
| `MI_Eel_Silhouette` | `MI_Master_Toon_Universal_Alpha` | Pale blue-white (0.85, 0.90, 1.0), translucency 0.7, glow 2.0 |
| `MI_WaterNetwork_White` | `MI_Master_Nikki_Landscape` | White seam overlay, cool tint (0.80, 0.85, 0.95) |
| `MI_MoonlitSurf_White` | `MI_Master_Nikki_Landscape` | Moon reflection, white seam visibility 0.8 |
| `MI_WhiteHaze_Distant` | Existing fog material | White-blue (0.85, 0.88, 0.95), density 0.03 |

---

## Level Layout — LV_WhiteCurrent_Prototype

```
Composition (top-down, not to scale):

  [MOON] — high, cold white key
    |
  [WHITE SEAM SPLINE] — follows river/lake network
    |                    Visible trace of the eel
  [EEL SILHOUETTE] — pale shape beneath surface
    |                    Hero mesh, translucent
  [WATER NETWORK] — connected splines
    |                    Player walks along banks
  [MOONLIT SURF] — water plane with seam reflection
    |
  [WHITE HAZE] — implies distant mass
    |
  [CURRENT MARKERS] — arrows tracing the eel's path
    |
  [CHECKPOINT] — rhythm gate at the "head" of the seam
```

---

## Rhythm + Fashion Integration

| System | Hook |
|--------|------|
| White seam visibility | Beat-synchronized intensity (pulses with rhythm) |
| Eel movement | Rhythm accuracy controls eel speed (faster when in sync) |
| Water network flow | Highway notes travel along the white seam |
| Fashion | Reflective/white clothing lets the entity perceive/track the player |
| Checkpoint | Rhythm gate at the "head" — align the seam to proceed |

---

## Evidence Standard

1. PIE session with labeled overlay (matches this sheet)
2. Assertion report JSON next to captures
3. `Saved/gate_ledger.json` row for `white_current_prototype`
4. SHA-256 hashes of new assets/instances

---

## Build Order

1. Production sheet (this doc) — DONE
2. GN builders (6 new, instances only) — ~2 hrs
3. PIE layout + capture — ~30 min
4. Evidence + ledger — ~15 min
