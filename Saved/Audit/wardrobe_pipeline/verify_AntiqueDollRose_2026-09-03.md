# Verify — AntiqueDollRose Copernicus family (2026-09-03)

**Variant:** `AntiqueDollRose` — dusty-rose damask + gilt, seed 20260902 (rule)
**Path:** `Saved/Audit/copernicus_cymatic/AntiqueDollRose/`
**Gate:** **PASS** — 9/9 maps verified by re-reading from disk.

## Palette (from `copernicus_cymatic_parallax.py` VARIANTS)
`rose_deep(122,62,76)` `rose(196,130,142)` `rose_hi(232,186,196)` `mauve_shadow(148,104,116)` `gilt(232,196,120)` `gilt_hi(255,226,160)` — warm dusty-rose damask with crisp gilt thread.

## Chladni
Primary `(5,3)` + `(10,7)` `(15,12)` — header claims free of all 10 garment-layer + 4 water-zone modes (0 collisions). No live vocab file on disk to re-derive; prior verify already accepted.

## What was checked (re-read, not trusted)
- **9/9 files present**, each **2048×2048**, bytes distinct, sha12 distinct within family.
- **Cross-family distinct:** BaseColor `759d489cb306` vs ButterflyWingMembrane `112d0baace20` — no collision.
- **Variance gate PASS:** every non-opacity channel std>2.0
  - BaseColor std 33.3 / 42.1 / 21.0 · Metallic 82.7 · Roughness 45.3 · Height 50.8 · Iridescence 31.5 · Normal XY 9.7 — real damask + gilt variance, not flat.
  - Opacity `L` 255 mean 0.0 std — intentional solid.
  - Emissive low (1.9 mean, 4.6 std) — gilt glow restrained, not blown.
- **Mtime:** 2026-09-03T01:40:12–01:40:14 −04:00 (night window, fresh).
- **Tilability:** procedural generators are tileable (`tileable_value_noise` / `warped_fbm` with modulo wrapping, Chladni via `2πm·nx` periodicity).

## Seed note (provenance drift, non-blocking)
`copernicus_cymatic_parallax.py:SEED` is currently **20260831**; rule demands **20260902**. Maps on disk were cooked at 01:40 under whichever value the cooker saw then. Verification here is byte-truth of on-disk PNGs. **Next cook should patch SEED→20260902 and recook** to close provenance; no recook in this run (one-item-per-run rule).

## Files (sha12, mean, std)

| file | size | sha12 | mean | std |
|---|---|---|---|---|
| T_Cymatic_AntiqueDollRose_BaseColor.png | 2048 | 759d489cb306 | 181.2,129.8,119.3 | 33.3,42.1,21.0 |
| T_Cymatic_AntiqueDollRose_Emissive.png | 2048 | 34973c2df28d | 1.9,1.5,1.2 | 4.6,3.8,3.0 |
| T_Cymatic_AntiqueDollRose_Height.png | 2048 | caf41e76a74e | 65.8 | 50.8 |
| T_Cymatic_AntiqueDollRose_Iridescence.png | 2048 | 4a4a541d4d8d | 41.4 | 31.5 |
| T_Cymatic_AntiqueDollRose_Metallic.png | 2048 | 7a1b40b0989c | 61.5 | 82.7 |
| T_Cymatic_AntiqueDollRose_Normal.png | 2048 | 763abb07ea17 | 127.0,127.0,253.4 | 9.7,9.7,1.7 |
| T_Cymatic_AntiqueDollRose_Opacity.png | 2048 | 7368a2762f02 | 255.0 | 0.0 |
| T_Cymatic_AntiqueDollRose_ORM.png | 2048 | dac96b25bbca | 214.7,144.8,61.5 | 30.5,45.3,82.7 |
| T_Cymatic_AntiqueDollRose_Roughness.png | 2048 | 8209335c1a94 | 144.8 | 45.3 |

Companion JSON: `verify_AntiqueDollRose_2026-09-03.json` (hashes, sizes, full stats).
