# Melodia Outfit Creation Hub — Blueprint

**Date:** 2026-08-29
**Status:** VALIDATED — every stage of this hub has run successfully at least once on the
Shorewake dress (2026-08-28/29). This document generalizes that proven arc into a repeatable
factory for new Melusina outfits.

**Authority:** the hub is a CONTENT pipeline. Wardrobe authority stays with
`MelodiaWardrobeSubsystem` + the `Cos_*` convention; outfits are content, never new systems.

---

## The proven pipeline (all stages ran on the Shorewake dress)

```
SOURCE            any of: USDZ garment / FBX / Blender project
  │
  ├─ A. PANEL PASS (Blender headless, dress_48_materials.py pattern)
  │     import → one LABELED material slot per panel (SW_<Outfit>_P01..N)
  │     → 48MAT .blend + Substance-ready FBX + slot/panel manifest
  │     verified: slot count, zero empty slots, per-slot poly sums = total
  │
  ├─ B. MAGIC PASS (Houdini headless, build_dress_magical.py pattern)
  │     posed-space geometry in → boundary-loop detection → hem fluff ridges,
  │     bodice scale plates (Cd hue bands), flip/inflate variants
  │     → OBJs + plates/loops/inflate JSONs + manifest
  │
  ├─ C. MERGE PASS (Blender, shorewake_pass_c.py pattern)
  │     owner FBX + magical OBJs → skin-weight transfer (POLYINTERP_NEAREST)
  │     → join → MORPH AUTHORING (Bloom/Swirl/ShimmerWave/ScaleFlip/FluffInflate)
  │     → 48+ slots → SK_<Outfit>_Magical.fbx (armature preserved)
  │     → QA renders (neutral + transformation pose)
  │
  ├─ D. SHINE KIT (numpy/PIL, dress_shine_kit.py pattern)
  │     iridescent scale-shimmer overlay + coverage mask, loop-verified
  │
  └─ E. UE IMPORT (editor holder, IMPORT_QUEUE recipe)
        MI binding (overlay lerp by mask, fresnel→Iridescence LUT, glints,
        pulse-coupled emission) + wardrobe slot via MelodiaWardrobeSubsystem
        + transformation BP (the sequence table)
```

## What a NEW outfit needs (inputs)

1. A garment source file (USDZ/FBX/blend) — panels may be merged; the hub re-splits
   only if the source has separate panels, otherwise slots come from material/UV regions.
2. An outfit id (`Cos_<Name>`) + slot decision (replace skirt / full-body swap).
3. Optional: palette/theme (the chromatic 12-PC system and spectral LUTs are shared).

Everything else — ridges, scales, shimmer LUTs, morphs, staging, QA — is generated.

## Hard rules (carried from the lane)

- Owner file NEVER modified: hub works on copies.
- Deterministic seeds; manifests are outputs; ingest verifies (three-category wrap).
- Blender **4.5** for headless renders (5.2 background color pipeline broken on this box).
- `-b --factory-startup -noaudio` always; clear USD stray objects; rebuild imported
  material graphs (no "Principled BSDF" name lookups).
- One MPC writer (SeaAbovePulse) per reactive outfit; wardrobe authority untouched.
- P0 gates close only through PIE + ledger — outfits are content, certified separately.

## Proven reference implementations

| Stage | Reference script (Shorewake) |
|---|---|
| A | `Tools/Houdini/sea_above_reef/dress_48_materials.py` |
| B | `build_dress_magical.py` |
| C | `shorewake_pass_c.py` |
| D | `dress_shine_kit.py`, `jelly_surreal_lut.py` |
| QA | `render_qa_blender.py` + `assemble_contact_sheets.py` (use **4.5**) |
| E | `Reef/IMPORT_QUEUE.md` recipes + `MelodiaWardrobeSubsystem` |

## Current outfit status

- **Shorewake**: stages A–D complete (48 slots, magical layer merged, 5 morphs,
  `SK_ShorewakeDress_Magical.fbx` staged); stage E = owner's live session.
- **Next outfits**: pick a source garment → hub stages A–D in one session each.
