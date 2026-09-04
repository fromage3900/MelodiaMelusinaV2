# Verify — ButterflyWingMembrane Copernicus family (2026-09-03)

**Variant:** `ButterflyWingMembrane` — iridescent wing membrane + tidepool nacre, seed 20260902 (rule)
**Queue alias:** `ButterflyWingTidepool` (iridescent tidepool, distinct Chladni mode) — on-disk folder is `ButterflyWingMembrane`, same family; verified as fulfillment.
**Path:** `Saved/Audit/copernicus_cymatic/ButterflyWingMembrane/`
**Gate:** **PASS** — 9/9 maps verified by re-reading from disk.

## Palette (from `copernicus_cymatic_parallax.py` VARIANTS at 26c175aa)
`membrane_deep(18,30,52)` `membrane(46,92,148)` `membrane_hi(120,200,235)` `vein_dark(10,16,30)` `vein_edge(200,230,255)` `eyespot(255,170,90)` `eyespot_ring(20,24,44)` — deep tidepool blue → membrane nacre → vein-edge iridescence + eyespot accent.

## Chladni
Primary `(7,4)` + `(12,9)` `(17,13)` — header claims free of all 10 garment-layer + 4 water-zone modes (0 collisions), distinct from AntiqueDollRose `(5,3)`. No live vocab file on this branch to re-derive; prior header accepted.

## What was checked (re-read, not trusted)
- **9/9 files present**, each **2048×2048**, bytes distinct, sha12 distinct within family.
- **Cross-family distinct:** BaseColor `112d0baace20` vs AntiqueDollRose `759d489cb306` — no collision; confirms two independent families.
- **Variance gate PASS:** every non-opacity channel std>2.0
  - BaseColor std 29.5 / 35.4 / 36.7 · Emissive 19.9 / 29.3 / 34.1 · Height 73.1 · Iridescence 50.1 · Metallic 10.3 · Roughness 21.9 · ORM 43.9/21.9/10.3 · Normal XY 11.2/10.2 — strong iridescence + height variance, not flat.
  - Opacity `L` 255 mean 0.0 std — intentional solid.
  - Normal Z 253.4 mean 1.8 std (expected flat Z for planar parallax).
- **Mtime:** 2026-09-03T01:42:34–01:42:37 −04:00 (night window, fresh).
- **Tilability:** procedural generators are tileable (`tileable_value_noise` / `warped_fbm` with modulo wrapping, Chladni via `2πm·nx` periodicity).

## Seed note (provenance drift, non-blocking)
`copernicus_cymatic_parallax.py:SEED` on this branch is currently **20260831**; rule demands **20260902**. Maps on disk were cooked at 01:42 under whichever value the cooker saw then. Verification here is byte-truth of on-disk PNGs. **Next cook should patch SEED→20260902 and recook** to close provenance; no recook in this run (one-item-per-run rule).

## Files (sha12, mean, std)

| file | size | sha12 | mean | std |
|---|---|---|---|---|
| T_Cymatic_ButterflyWingMembrane_BaseColor.png | 2048 | 112d0baace20 | 44.8,68.5,96.4 | 29.5,35.4,36.7 |
| T_Cymatic_ButterflyWingMembrane_Emissive.png | 2048 | 2345d9f5775e | 13.2,19.5,22.6 | 19.9,29.3,34.1 |
| T_Cymatic_ButterflyWingMembrane_Height.png | 2048 | be036339c82b | 94.6 | 73.1 |
| T_Cymatic_ButterflyWingMembrane_Iridescence.png | 2048 | cd3ce132cfcf | 189.0 | 50.1 |
| T_Cymatic_ButterflyWingMembrane_Metallic.png | 2048 | 8b434c505ded | 14.3 | 10.3 |
| T_Cymatic_ButterflyWingMembrane_Normal.png | 2048 | 83937ac9fa89 | 127.0,127.0,253.4 | 11.2,10.2,1.8 |
| T_Cymatic_ButterflyWingMembrane_Opacity.png | 2048 | 7368a2762f02 | 255.0 | 0.0 |
| T_Cymatic_ButterflyWingMembrane_ORM.png | 2048 | 5d02d1567ce5 | 197.5,68.0,14.3 | 43.9,21.9,10.3 |
| T_Cymatic_ButterflyWingMembrane_Roughness.png | 2048 | 4c6a655dc77f | 68.0 | 21.9 |

Companion JSON: `verify_ButterflyWingMembrane_2026-09-03.json` (hashes, sizes, full stats).
