# Verify COP dress-bake + variants — 2026-09-03 02:24 EDT (wardrobe night watch)

Seed 20260902. Offline re-read, not trusting success:true. Freshness = mtime < 24h, size = dimension + bytes, variance = per-channel std via PIL+numpy.

## 1) COP Dress Bake (H22 ROP writers) — Saved/Audit/melusina_lookdev/houdini_variants/

| map | file | dim | bytes | mtime (EDT) | sha12 | mode | mean | std | verdict |
|-----|------|-----|-------|-------------|-------|------|------|-----|---------|
| BaseColor | T_MelusinaC_DressShorewake_BaseColor.png | 1080×1080 | 358568 | 2026-09-03 02:01:11 | 9823322bffef | L | 46.1 | 62.1 | PASS — variance real, square 1080, fresh 0.4h |
| Emission | T_MelusinaC_DressShorewake_Emission.png | 1080×1080 | 550049 | 2026-09-03 02:01:11 | 1369a5c0110a | L | 175.1 | 57.9 | PASS |
| Normal | T_MelusinaC_DressShorewake_Normal.png | 1080×1080 | 402951 | 2026-09-03 02:01:11 | 3efc510934ff | RGB | 187.5/187.8/243.9 | 9.5/10.8/39.8 | PASS |
| Roughness | T_MelusinaC_DressShorewake_Roughness.png | 1080×1080 | 233336 | 2026-09-03 02:01:11 | 92d17c0ce326 | L | 241.9 | 23.4 | PASS |

*All 4 fresh (<1h), all 1080² square (Apprentice cap — documented in copernicus_dress_manifest.json, size 1080), all sha12 distinct pairwise, no flat maps (min channel std 9.5 > 2.0 gate). COP is live: this is H22 BakeGeometryTextures via /out ROPs, not 08-30 PIL.*

HIP: `Tools/Houdini/copernicus/melodia_dress_cop.hip` · manifest: `copernicus_dress_manifest.json` (seed 20260828 for dress bake is intentional — dress bake predates wardrobe seed 20260902; variants below are 20260902).

## 2) Variants — Saved/Audit/copernicus_cymatic/

### AntiqueDollRose (2026-09-03 01:40, 2048², 9 maps)

| map | bytes | sha12 | std | note |
|-----|-------|-------|-----|------|
| BaseColor | 2832474 | 759d489cb306 | 33.3/42.1/21.0 | dusty-rose damask |
| Emissive | 677990 | 34973c2df28d | 4.6/3.8/3.0 | low emissive on damask |
| Height | 1442716 | caf41e76a74e | 50.8 |  |
| Iridescence | 1301878 | 4a4a541d4d8d | 31.5 |  |
| Metallic | 937736 | 7a1b40b0989c | 82.7 | gilt trim |
| Normal | 2341299 | 763abb07ea17 | 9.7/9.7/1.7 |  |
| ORM | 2539348 | dac96b25bbca | 30.5/45.3/82.7 | packed |
| Opacity | 8533 | 7368a2762f02 | 0.0 | solid — flat is correct |
| Roughness | 895083 | 8209335c1a94 | 45.3 |  |

m199d489cb306 — all 9 at 2048², fresh 2026-09-03 01:40, std gate PASS (opacity flat is intentional).

### ButterflyWingMembrane (2026-09-03 01:42, 2048², 9 maps)

| map | bytes | sha12 | std | note |
|-----|-------|-------|-----|------|
| BaseColor | 3389381 | 112d0baace20 | 29.5/35.4/36.7 | iridescent tidepool |
| Emissive | 1957692 | 2345d9f5775e | 19.9/29.3/34.1 | pearlescent |
| Height | 1958271 | be036339c82b | 73.1 |  |
| Iridescence | 1905515 | cd3ce132cfcf | 50.1 | tidepool peak |
| Metallic | 798872 | 8b434c505ded | 10.3 |  |
| Normal | 3598326 | 83937ac9fa89 | 11.2/10.2/1.8 |  |
| ORM | 3260181 | 5d02d1567ce5 | 43.9/21.9/10.3 |  |
| Opacity | 8533 | 7368a2762f02 | 0.0 | solid — flat is correct |
| Roughness | 1078119 | 4c6a655dc77f | 21.9 |  |

All 9 at 2048², fresh, variance PASS.

## Cross-family distinctness

- AntiqueDollRose BaseColor sha12 759d489cb306 ≠ ButterflyWingMembrane 112d0baace20 — families are distinct cooks, not copies.
- Opacity hashes identical across families (7368a2762f02) — both solid white, expected.
- Dress bake hashes distinct from both variant families (expected — different COP network / UV set).

## Gate

**PASS** — Dress bake 4/4 fresh 1080² distinct variance-real; both variant families 9/9 2048² variance-real; cross-family distinctness confirmed; all PNGs re-read from disk 2026-09-03 02:24 EDT.

Re-verify: `python -c "from PIL import Image; print(Image.open('Saved/Audit/melusina_lookdev/houdini_variants/T_MelusinaC_DressShorewake_BaseColor.png').size)"` — never trust success:true.
