# L5 Evidence Gates — ZenLantern Hero

Date: 2026-09-24

## Gate board
| Gate | Meaning | Status |
|---|---|---|
| G1 | V2 mesh + uv_report.json density/overlap | **PASS** (L1L2_receipt — density_delta ~0%, overlap_new_vs_authored 0) |
| G2 | Morph FBX re-import proof (shape keys present + deltas) | **PASS (Blender reimport)** — UE editor reimport still owner |
| G3 | vcol refresh on V2 (A fire box, G eaves+ribs) | **PASS** on charmfix blend (`vcol_refresh_report.json` 2026-09-23) |
| G4 | UE lookdev capture pulse ON vs OFF | **PENDING** (needs editor + L4 wire + Ctrl+S) |

## G2 Blender proof (2026-09-24)
Reimported `ZenLantern_V2_L3_morphs.fbx` in Blender 5.2 factory scene:

| Shape key | Max delta (m) |
|---|---|
| SK_FlameBreath | 0.14017 |
| SK_RoofLift | 0.19000 |
| SK_CharmSway_L | 0.46197 |
| SK_CharmSway_R | 0.46175 |
| SK_DawnDusk | 0.02619 |

Object: `zenlantern_V2_L3` · 15670 verts · 15572 faces · keys Basis + 5 morphs.

## Still open for owner
1. UE import morph FBX → confirm 5 morph targets on static mesh
2. L4 MI + Niagara + MPC wire → G4 screenshot pair
3. Ctrl+S dirty Melodia packages (no Monolith save_packages)
4. Painter SMS → real `.spsm` into live exports
