# Batch B — Sheep Reparent + Chladni_C + Flipbook Fix — 2026-09-12

## Done

1. **Reparent `MI_ChoralSheep_Body` → `M_Master_Toon_Character`** (owner lock).
   Toon_Character was designed for this (ChladniPatternTexture, ChladniIntensity/
   EmissiveStrength/SheenStrength, HarmonizeActive params). Carried over: 4 tex
   (Albedo→CharacterAlbedo, Normal, ORM→RoughnessMap, ChladniPatternTexture),
   7 scalars (BeatAccent 1.31, Chladni E/I/S 2.5/2.0/0.5, Harmonize ~1.0,
   CharacterRoughness 1.0, UV tiling), 2 vectors (LilacHalo, PearlSilk).
   Dropped (no counterpart, documented): Height/Displacement, RoseVelvet
   DetailNormal, TextureWeight, RoughnessBias, FabricAniso, Iridescence,
   DetailStrength, RefractionDepthBias. Verified live via redump.
2. **Created `MI_ChoralSheep_Body_Chladni_C`** (child of Body): ROOT bound,
   Intensity 2.5, Emissive 3.5, Harmonize 1.0 — pitch-C accent layer.
3. **BeatStar flipbook fixed:** renderer `SubImageSize` was (1,1) on the 8-frame
   `T_Spark_Twinkle8` atlas — set (4,2); added missing SubUVAnimation module,
   Number Of Frames=8, recompiled. WoolMote verified 1×1-correct (single-frame),
   left alone. Coats untouched (live Hermes-adjacent work).

## Proof

- Redumps: Body parent + params, child chain, renderer props.
- PIE smoke IntegrationMap: 47 samples, 0 errors. 0 dirty, 0 errored BPs.

## Incidents/notes

- Read-only flags RE-APPEARED on both edited files after the repo-wide sweep
  (09-09 stamps) — something re-applies them; cleared again, saved True.
  The re-flagging source is unidentified: watch item for the freeze.
- Photo keeper (CS-06/CS-10 pitch-C visual) is owner-lane: needs the live sheep
  + pitch event framing, beyond a smoke harness.

**Evidence level:** live-proven (redumps + compile + smoke).
