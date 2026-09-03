# Glacier Audio-Reactive Landscape Pipeline — Staging Record — 2026-09-02

Status: **STAGED + VERIFIED ON-DISK** (live PIE capture pending, editor lock contention 2026-09-02 evening).
Committed: `a62a2deb feat(landscape)` on `feature/p0-closeout-2026-09-02`.

Authority: `GAEA_LANDSCAPE_IMPORT_RECIPE_2026-09-02.md` (canonical import loop) → this doc
(audio-reactive extension of the landscape master). Related: `GAEA_TERRAIN_PIPELINE_2026-09-01.md` §0/§8.

## 1. Landscape master extension (VERIFIED via T3D export, 130 unique params, was 122)

`M_Master_Toon_Landscape_HeightBlend` — additive nodes only, gated so existing substrate MIs are unchanged:

- `bUseGaeaLayers` (StaticSwitchParameter, default **false**) — `True` = painted Gaea layers, `False` = substrate path (bit-identical to pre-change)
- `LandscapeLayerCoords → Multiply(PaintedLayer_Tiling, default 4.0) → 4× TextureSampleParameter2D (PaintedLayer_Base/Snow/Water/Rock) → LandscapeLayerBlend(Base/Snow/Water/Rock)`
- Switch True input ← LayerBlend, False input ← `LinearInterpolate_13` (original BaseColor chain), output → `SubstrateToonBSDF_0.BaseColor` (single edge change)
- `LandscapeLayerSample(Water) × MoistureWetnessBoost` (0.35) — World Field Bus v1 `WorldField.Moisture` landscape-native read
- `CollectionParameter(MPC_Melodia_Palette:BeatPulse) × AudioEmissiveStrength (scalar, default 0.0) → Add → SubstrateToonBSDF_0.EmissiveColor` — audio-reactive emissive (single MPC writer contract intact: `UMelodiaAudioReactivePresentationSubsystem` is sole writer; material is a reader)

Evidence: `Saved/Audit/master_before_wiring_2026-09-02.json` (122) vs live `130 unique ParameterName` in
`Docs/T3D_Baseline/materials/M_Master_Toon_Landscape_HeightBlend.t3d` (exported 2026-09-02 18:44).

## 2. MI_Glacier_Landscape_Layered (verified on-disk)

`/Game/Gaea/Glacier/Materials/MI_Glacier_Landscape_Layered` (14,231 B, 2026-09-02 17:33) — parent = HeightBlend master,
`bUseGaeaLayers=true` (override present in binary; live reflection confirmation pending PIE),
4 texture bindings: `T_Glacier_SatMap / T_Glacier_GroundTexture / T_Glacier_Combine / T_Glacier_ColorErosion`,
scalars: `PaintedLayer_Tiling 4.0, MoistureWetnessBoost 0.35, AudioEmissiveStrength 0.0, Wetness 0.10, ShoreWetnessBoost 0.46, PastelLift 0.24, DreamSaturation 0.22, DreamContrast 0.04` (house grammar from `apply_gaea_substrate_materials.py`).
Layer info objects minted: `/Game/Gaea/Glacier/Layers/Base|Rock|Snow|Water` (1.5 KB each).

Assigned as `landscape_material` on the 256-component Glacier landscape in
`LV_SeaAbove_Prototype` (EnvSandbox copy, live map; external actor `TO7CUZC3W04JZOUSFXP8FT` 12.4 MB preserved 14:04:47).

## 3. Audio-reactive lane behavior

- `AudioEmissiveStrength=0.0` default → no visual change until a consumer MI raises it (0.25–0.60 for visible beat shimmer on snow/ice).
- Beat source: `MPC_Melodia_Palette.BeatPulse` [0,1] — written only by `UMelodiaAudioReactivePresentationSubsystem`
  (path `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette`, confirmed in `MelodiaAudioReactivePresentationSubsystem.cpp` `AudioMpcPath`).
- Cymatics contract: `UMelodiaCymaticsSubsystem` is a read-only consumer (`IsReadOnlyByContract()=true`);
  `ModeN/ModeM → WorldField.Resonance`, `SampleCymaticAmplitude → WorldField.Tension` (master index §5b-i).
  HorizonEater ecosystems publish `HorizonEatAmount/DestructionAmount/HorizonTension/WorldHorizonEat` on the same MPC
  (51 scalars total, added via `add_horizon_eater_mpc_params.py`).

## 4. Live staging state (on-disk verified)

| Item | State |
|---|---|
| Glacier landscape | 256 comps, 5 km, raycast-verified 0.0–0.7 m vs r16, 307 external actors |
| Foliage | 15 instances (IvyForTrees_01 + BigBush), height-aware via r16 `z_at()`, highlands y≈2000±120 m, Z 40–586 m |
| PCG | ResonanceCathedral 86 ISM (delta-seated, floors −146.5 m = terrain), Colonnade 48 ISM (volume-relative, −156.7 m) |
| HorizonEater | 24 debug markers + FarawayLOD 20 markers, height-aware raycast placement |
| Staging files | `Saved/GaeaStaging/Glacier/` 10/10 (r16, definition.json, 4 color PNGs, 3 weightmaps 1009², contract.json) |
| Manifest | `Saved/Audit/gaea_texture_manifest_glacier.json` 7 entries, round-trip 0.00196 |

## 5. Pending (owner-approved execution order)

1. **Live PIE capture** — screenshots + JSON assertion reports (landscape, foliage, beat-pulse emissive) — requires editor lock (contention with swarm session on 2026-09-02 evening; retry when calm).
2. **Cook** — `MapsToCook` now includes `LV_SeaAbove_Prototype` (re-applied on main); run closed-editor `RunUAT BuildCookRun … -archive -archivedirectory=G:\StagedBuilds\P0_20260902`.
3. **RVT writer v2** — `WorldField.Moisture/Contact` → RVT for PCG/Niagara sampling (v1 is in-master read, documented above).
4. **Blender GN live run** — spec at `Saved/Audit/blender_gn_dressing_spec_2026-09-02.json`.
5. **VegetationGrowthSubsystem build** — SCAFFOLDED C++ needs closed-editor build for audio-reactive SpeedTree growth.
