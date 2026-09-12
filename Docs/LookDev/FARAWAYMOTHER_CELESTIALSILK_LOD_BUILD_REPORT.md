# FarawayMother CelestialSilk — Perceptual LOD Build Report
**Date:** 2026-09-02
**Chladni Mode:** (3, 5) jacquard
**Pipeline:** `Tools/LookDev/build_optical_lod_matrix.py` + `Content/Python/melodia_optical_lod_pipeline.py`

## Build Status: PASS

### Verification Commands (all PASS)
```
python Tools/LookDev/build_optical_lod_matrix.py --verify        # -> Verification PASSED
python Content/Python/melodia_optical_lod_pipeline.py             # -> 12 instances, PASS
python -m unittest Tools.test_optical_lod_lookdev -v              # -> 5/5 OK
```

### Texture Suite (51 maps — 3 assets × 4 tiers × 4 PBR + 3 shared)
Root: `Saved/Audit/lookdev/optical_lods/`

| Asset | LOD0 1024 | LOD1 512 | LOD2 256 | LOD3 128 |
|-------|-----------|----------|----------|----------|
| FarawayMother_CelestialSilk | BaseColor/Normal/ORM/Height | — | — | — |
| Melusina_Shorewake_Gown | BaseColor/Normal/ORM/Height | — | — | — |
| Starskiff_Hull_Celestial | BaseColor/Normal/ORM/Height | — | — | — |

Shared utilities in `Saved/Audit/lookdev/optical_lods/shared/`:
- `T_LOD_BayerDither_8x8.png` (8×8, Bayer ordered dither, 5 m crossfade window)
- `T_LOD_BlueNoise_64x64.png` (64×64, blue-noise stipple, high-pass filtered)
- `T_LOD_Iridescence_ThinFilm_LUT.png` (128×512, Airy thin-film interference, facing vs phase)

### 4-Tier LOD Spec — FarawayMother_CelestialSilk (hero asset)

| Tier | Distance | POM Steps | Toksvig | Rim Boost | WPO Scale | Resolution |
|------|----------|-----------|---------|-----------|-----------|------------|
| LOD0 | 0–15 m   | 32        | 0.00    | 1.0×      | 1.00      | 1024 |
| LOD1 | 15–50 m  | 16        | 0.35    | 1.15×     | 0.75      | 512  |
| LOD2 | 50–200 m | 0         | 0.75    | 1.4×      | 0.30      | 256  |
| LOD3 | 200 m+   | 0         | 1.00    | 1.8×      | 0.00      | 128  |

Crossfade window: 5 m (screen-door dither via Bayer/BlueNoise, TSR-smoothed). LOD2/LOD3 use Toksvig-stabilized specular + grazing rim compensation to hide faceting.

### Material Instances (12 total — 3 assets × 4 tiers)

Source config: `specs/lookdev/optical_material_instances.v1.json` (schema `melodia.optical_lod_pipeline.v1`).
Per-MI JSON sidecars in `Content/EnvSandbox/Materials/Instances/Copernicus/MI_*.json` (12 files) — editor materializes `.uasset` from these via `melodia_optical_lod_pipeline.py::apply_in_engine()` (requires live editor).

FarawayMother_CelestialSilk subset: `specs/lookdev/FarawayMother_CelestialSilk_LookDev.json`

| Instance | Master | Params |
|----------|--------|--------|
| MI_FarawayMother_CelestialSilk_LOD0 | M_Master_FarawayMother_Fabric | POM 32, Toksvig 0.0, Rim 1.0, WPO 1.0 |
| MI_FarawayMother_CelestialSilk_LOD1 | M_Master_FarawayMother_Fabric | POM 16, Toksvig 0.35, Rim 1.15, WPO 0.75 |
| MI_FarawayMother_CelestialSilk_LOD2 | M_Master_FarawayMother_Fabric | POM 0, Toksvig 0.75, Rim 1.4, WPO 0.3 |
| MI_FarawayMother_CelestialSilk_LOD3 | M_Master_FarawayMother_Fabric | POM 0, Toksvig 1.0, Rim 1.8, WPO 0.0 |

Remaining 8 MIs cover Melusina_Shorewake_Gown and Starskiff_Hull_Celestial with identical tier progression.

### Parameter Verification
- **POM:** 32→16→0→0 ✓
- **Toksvig variance:** R_adj = sqrt(R² + w·σ²), w = 0.0/0.35/0.75/1.0 ✓ (unit test `test_toksvig_roughness_adjustment` asserts monotonic increase)
- **Grazing rim:** 1.0→1.15→1.4→1.8 ✓ compensates silhouette faceting
- **Bayer/BlueNoise/IR LUT:** shape and range verified by `test_bayer_and_blue_noise_generation` + `test_iridescence_lut_properties` ✓

### File Paths (absolute)
- Manifest: `C:/EnvironmentPortfolio/BS_GodFile/specs/lookdev/optical_lod_manifest.v1.json`
- MI config: `C:/EnvironmentPortfolio/BS_GodFile/specs/lookdev/optical_material_instances.v1.json`
- FarawayMother subset: `C:/EnvironmentPortfolio/BS_GodFile/specs/lookdev/FarawayMother_CelestialSilk_LookDev.json`
- Copernicus sidecars: `C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Instances/Copernicus/MI_*.json` (×12)
- Textures: `C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/lookdev/optical_lods/**`
- Architecture SSOT: `C:/EnvironmentPortfolio/BS_GodFile/Docs/LookDev/MELODIA_PERCEPTUAL_LOD_LOOKDEV_ARCHITECTURE.md`

### Notes
- `.uasset` materialization requires live UE editor (`apply_in_engine`); offline scaffold is the 12 JSON sidecars + pipeline config, which is the canonical contract.
- All PNGs are tileable (Chladni field uses periodic Sobel) and optimized.
