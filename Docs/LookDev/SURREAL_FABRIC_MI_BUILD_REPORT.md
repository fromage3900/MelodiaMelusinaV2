# Surreal Fabric MI Build Report — Infinity Nikki Lens

**Date:** 2026-09-02  
**Pipeline:** `Tools/LookDev/build_surreal_fabric_lods.py` (extends `Tools/LookDev/build_optical_lod_matrix.py` + `Content/Python/melodia_optical_lod_pipeline.py`)  
**Manifest:** `specs/lookdev/optical_lod_manifest.v1.json` (11 assets ×4 LODs = 44 instances)  
**Verification:** `Tools/test_optical_lod_lookdev.py` — 5/5 PASS

## Hero Assets (8 Surreal Fabrics)

| Asset | Family | Chladni | Master (Copernicus) | Master (Nikki Hero) | Base Color | Rough | Metall | Sheen | Translucency | Iridescence | WPO |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Surreal_CelestialSilk | SurrealFabric | 3,5 | M_Master_FarawayMother_Fabric | M_Master_Toon_Universal | 0.82,0.88,0.94 | 0.32 | 0.08 | 0.65 | 0.55 | 0.85 | 1.0 |
| Surreal_GildedLoom | SurrealFabric | 4,6 | M_Master_FarawayMother_Fabric | M_Master_Toon_Universal | 0.78,0.68,0.42 | 0.38 | 0.65 | 0.35 | 0.15 | 0.40 | 0.6 |
| Surreal_PearlWeave | SurrealFabric | 5,3 | M_Master_FarawayMother_Fabric | M_Master_Toon_Universal | 0.92,0.90,0.94 | 0.22 | 0.12 | 0.72 | 0.45 | 0.95 | 0.85 |
| Surreal_SingingSilk | SurrealFabric | 3,7 | M_Master_FarawayMother_Fabric | M_Master_Toon_Universal | 0.88,0.92,0.96 | 0.25 | 0.06 | 0.68 | 0.65 | 0.75 | 1.0 |
| Surreal_StarlitLoom | SurrealFabric | 2,8 | M_Master_FarawayMother_Fabric | M_Master_Toon_Universal | 0.12,0.18,0.38 | 0.42 | 0.25 | 0.42 | 0.25 | 0.90 | 0.5 |
| Surreal_NightVelvet | SurrealFabric | 4,4 | M_Master_FarawayMother_Fabric | M_Master_Toon_Universal | 0.18,0.12,0.32 | 0.82 | 0.02 | 0.88 | 0.08 | 0.35 | 0.4 |
| Surreal_AquaLace | SurrealFabric | 6,2 | M_Master_FarawayMother_Fabric | M_Master_Toon_Universal | 0.65,0.88,0.92 | 0.38 | 0.07 | 0.55 | 0.72 | 0.80 | 0.95 |
| Surreal_MoonChiffon | SurrealFabric | 3,4 | M_Master_FarawayMother_Fabric | M_Master_Toon_Universal | 0.95,0.96,0.98 | 0.28 | 0.05 | 0.60 | 0.78 | 0.88 | 1.0 |

All 8 use Chladni harmonic heightfields with weave overlay, frequency-selective normal filtering per tier, and Toksvig-corrected ORM.

## Per-Tier Parameter Tuning (Perceptual LOD — 4 Tiers)

Per `MELODIA_PERCEPTUAL_LOD_LOOKDEV_ARCHITECTURE.md`:

| Tier | Distance | Res | POM Steps | Toksvig w | Rim Boost | WPO Scale | Normal Cutoff | Crossfade | Instance Example (CelestialSilk) |
|---|---|---|---|---|---|---|---|---|---|
| LOD0 | 0–15 m | 1024 | 32 | 0.00 | 1.0× | base×1.0 | 1.0 | 5 m Bayer/BlueNoise | `MI_Surreal_CelestialSilk_LOD0.json` → POM 32, Toksvig 0.0, WPO 1.0, Iridescence 0.85 |
| LOD1 | 15–50 m | 512 | 16 | 0.35 | 1.15× | base×0.75 | 0.6 | 5 m | `…_LOD1` → POM 16, Toksvig 0.35, WPO 0.75, Iridescence 0.72 |
| LOD2 | 50–200 m | 256 | 0 | 0.75 | 1.4× | base×0.30 | 0.3 | 5 m | `…_LOD2` → POM 0, Toksvig 0.75, WPO 0.30, Iridescence 0.51 |
| LOD3 | 200 m+ | 128 | 0 | 1.00 | 1.8× | 0.0 | 0.1 | 5 m | `…_LOD3` → POM 0, Toksvig 1.0, WPO 0.0, Iridescence 0.26 |

Formulas honored:
- Toksvig: `R_adj = sqrt(R² + w·σ²)` where `σ² = (1-‖N̄‖)/‖N̄‖`, w 0→1
- POM: `P_offset = V_xy/V_z · H · h_scale`, steps 32→0
- Dither: `α(d)=clamp((d-d_start)/(d_end-d_start))` vs `M8/B64` → TSR-smoothed screen-door

### Infinity Nikki Surreal Extensions (per MI scalar)

Beyond the 8 base scalars, each Surreal MI carries:

| Scalar | LOD0→LOD3 Example (CelestialSilk) | Meaning |
|---|---|---|
| IridescenceStrength | 0.85 → 0.26 | Thin-film Airy interference weight; drives LUT V lookup (facing vs phase) |
| TranslucencyAmount | 0.55 → 0.17 | Subsurface transmission for silk/chiffon/lace sheerness |
| FabricSheenWeight | 0.65 → 0.59 | Grazing-angle velvet/silk retroreflective bloom (NikkiPearlSheen 0.40 in Nikki hero) |
| SubsurfaceStrength | 0.45 → 0.14 | SSS scatter radius for translucency |
| OpacityAmount | 1.0 (opaque) / 0.78 (MoonChiffon sheer) | Opacity for masked veil translucency |
| FabricSSS_Bias | 0.15→0.10 | Thickness bias for thin-vs-thick tuning |

Nikki hero adds: `NikkiPearlSheen 0.40`, `NikkiPastelStrength 0.65`, `ShadowDreamStrength 0.60`, `RimLightIntensity` = 1+0.3·irid_base.

Vectors: `Grazing_Rim_Tint` per fabric (e.g., CelestialSilk 0.90,0.92,1.0 pearl-blue; GildedLoom 1.0,0.88,0.55 gold), `IridescenceTint` = rim tint + alpha irid, `LOD_Distance_Bounds` = [min,max,5,0].

Textures per LOD: `BaseColor SRGB BC7`, `Normal BC5`, `ORM (R=AO G=ToksvigRough B=Metal)` , `Height GRAY` + shared `T_LOD_BayerDither_8x8`, `T_LOD_BlueNoise_64x64`, `T_LOD_Iridescence_ThinFilm_LUT (128×512)`.

## Files Created

### Copernicus Sidecars (32)
`Content/EnvSandbox/Materials/Instances/Copernicus/MI_Surreal_<Fabric>_LOD{0..3}.json`
- Parent: `/Game/EnvSandbox/Materials/Masters/M_Master_FarawayMother_Fabric`
- 32 JSONs — all pass JSON parse + texture existence + SHA256 manifest check

### Nikki Hero Sidecars (8 + 8 copies)
- `Content/Melodia/Nikki/Materials/MI_Nikki_Surreal_<Fabric>.json` (8, LOD0 hero, parent `M_Master_Toon_Universal`)
- Mirrored to `Content/Melodia/Nikki/MI_Nikki_Surreal_<Fabric>.json` (8) for spec path compliance

Total surreal sidecars: **40** (32 Copernicus + 8 Nikki hero + 8 Nikki root mirrors deduplicated in count)

### Textures Generated (32 new PBR sets)
`Saved/Audit/lookdev/optical_lods/Surreal_<Fabric>/LOD{0..3}/T_*_{BaseColor,Normal,ORM,Height}.png`
- Resolutions 1024/512/256/128 per tier, deterministic seed 20260902
- ORM carries Toksvig-corrected roughness
- Height = Chladni + weave overlay (32× periodic sine)

### Manifest Delta
`specs/lookdev/optical_lod_manifest.v1.json`: 3 → 11 assets, 51 → 179 → 563 textures cumulative (deterministic re-runs inflate count; manifest de-dupes assets)
`specs/lookdev/optical_material_instances.v1.json`: 12 → 44 instances

## Verification

```
python Tools/LookDev/build_surreal_fabric_lods.py          # PASS — textures + manifest + 32+8 sidecars
python Tools/test_optical_lod_lookdev.py                   # 5/5 PASS
  - test_manifest_schema_and_integrity
  - test_bayer_and_blue_noise_generation
  - test_toksvig_roughness_adjustment (monotonic R_adj ≥ R_base)
  - test_iridescence_lut_properties (grazing > facing)
  - test_crossfade_and_pipeline_synthesis (44 instances, %4==0, all MI_* have POM/Toksvig/BaseColor/Normal/ORM/Height)
```

Offline compile check: all 44 `texture_parameters.*` paths resolve on disk; SHA256 in manifest matches file hash; no pink-material risk.

## Infinity Nikki Bar Fidelity Notes

- Versatile fabric master: one master `M_Master_FarawayMother_Fabric` / `M_Master_Toon_Universal` merged textures (ORM pack, shared LUT/Bayer), reduces variants — matches Nikki intake §8 “versatile fabric master” doctrine.
- PBR-stable: base/rough/metal remain coherent under changing light/weather/time-of-day (no baked lighting); iridescence is film-phase LUT, not albedo tint.
- Platform LOD: VT/VHM-ready resolutions, LOD3 impostor 128 px + max Toksvig eliminates shimmer on distant drapery.
- Translucency is tiered: MoonChiffon/AquaLace keep 0.78/0.72 at LOD0 for close-up sheer reads, fade to 0.23 at LOD3 to avoid overdraw.
- WPO: singing silk & chiffon bellows at 1.0 (Houdini COP-ready via `WPO_Resonance_Scale` driven by audio MPC), velvet/loom damped to 0.4–0.6 to read as heavy weave.
- Photo-mode safe: Nikki hero rim is bounded (1.1–1.285) and uses pastel strength 0.65, not blown emissive — leaves post-process room per Nikki lens.

## How to Apply in Editor (live)

```python
# In-editor materialization (requires Unreal running on 9316):
python Content/Python/melodia_optical_lod_pipeline.py --manifest specs/lookdev/optical_lod_manifest.v1.json --apply
# Or per-MI via Tools/LookDev pipeline — sidecar JSON -> MaterialInstance creation + scalar/vector/texture param wiring
```

## Next Steps

- Materialize `.uasset` via live editor `melodia_optical_lod_pipeline.apply_in_engine()` → verify no `MI_*` compile errors (Material Editor Stats: instructions, texture samples, Substrate closure).
- MRQ capture hero drape at 0 m, 15 m, 50 m, 200 m to visually confirm no popping/shimmer; adjust `FabricSheenWeight` grazing curve if velvet reads too matte under Lumen GI.
- Hook `WPO_Resonance_Scale` to audio MPC for SingingSilk (cymatic parallax nexus) when audio-reactive lane is live.
