# Horizon Eater — Horizon Line Eater Design (2026-09-02)

**Spec:** `horizon_eater_spec.v1.json`  
**Faraway twin:** `../faraway_lod_destruction/FARAWAY_LOD_DESTRUCTION_DESIGN.md`  
**Levels:** `LV_SeaAbove_Prototype` (primary) + `LV_FarawayMother_Prototype` (horizon sink)  
**Engine:** UE 5.8, Oceanology SLW, World Partition + Data Layers + HLOD, PCGEx, Copernicus, single MPC writer

---

## 1. Thesis — horizon IS the mouth

> The Horizon Eater does not have a horizon. It **is** the horizon.

Per `P3_HORIZON_EATER_PLAN_2026-08-29.md`: a filter feeder whose feeding field compresses adjacency; mouth spans what the player reads as horizon. Mountains/ridges become jaw margins, filter plates, pleated throat.

We never build a kilometre rig. We build **three horizon kills that together imply one anatomy**:

| Kill | System | What disappears | Why it sells eater |
|------|--------|---------------|------------------|
| A | Oceanology SLW absorption | False ocean band at -50m seen through real water | Brain reads km of attenuation over m of geometry — water becomes membrane |
| B | Height fog + cloud + haze volume | Above-water horizon line & sky | Above/below horizons both die — no world left beyond |
| C | HLOD LOD3 + PCG filter-flow cull | Distant terrain silhouette at horizon | Geometry itself crumbles into filter corridors |

One scalar rules all three: **`HorizonEatAmount 0..1` on `MPC_Melodia_Palette`** (alias `WorldField.Tension` / `WorldField.HorizonEat`). 0 = pristine horizon, 1 = gone + Bell membrane revealed.

---

## 2. Kill A — Oceanology SLW absorption (primary)

### Why SLW, not height fog

`SEA_ABOVE_SECOND_OCEAN_LAYOUT_AND_CAMERA_PLAN` §3 (doc correction): false ocean sits *below* real water, so rays into it integrate SLW absorption/scattering, **not** `ExponentialHeightFog`. Height fog governs above-water horizon.

The primary scale trick is **tuning absorption to extinguish faster than 50m justifies** — perceptual metres become kilometres.

### Assets on disk (verify before tuning)

- Real ocean: `AOceanologyInfiniteOcean` + `M_Water_Oceanology_Melodia_Inst` (DL_Water)
- Volume: `AOceanologyWaterVolume` — **still a 2m cube** (must scale to enclose false plane, else attenuation does not fire)
- False plane: `SeaAbove_FalseOceanPlane_Prototype` Z -5000 cm, `MI_SeaAbove_FalseOcean_Clean` (20 overrides) currently bound
- Alt: `MI_SeaAbove_FalseOcean_Oceanology` (17 overrides, Beaufort 2, `Biolum_Weight` 0.35) — A/B candidate
- Sheet: `MI_SeaAbove_SurfaceOcean_Oceanology` (real ocean shallow/deep scattering, PhaseGLow/High)

### Measure, then place

```
extinction = -ln(0.01) / absorption_rgb_len  // 99% extinct
plane_z = extinction * 0.70 to 0.80
// If extinction < 50m, horizon already eaten at rest — lower absorption
```

False plane Z is not aesthetic; it is **bounded by real ocean extinction**. False plane is Bell crown tangent per §3 of camera plan: `sag = R - sqrt(R² - d²)`; R≈3km, d=1.2km => 251m sag. Crown just under plane.

### HorizonEat binding (MPC -> MI)

Add to `MPC_Melodia_Palette` via `Content/Python/add_horizon_eater_mpc_params.py`:

```
Absorption            *= 1 + HorizonEat*3.0
DeepScatteringColor    lerp toward horizon fog (desaturate)
Biolum_Weight          0.35 * (1 - HorizonEat*0.9)   // still punches, then dies
PhaseGLow/High         + HorizonEat * 0.6            // forward scatter grows
```

Single writer: `UMelodiaAudioReactivePresentationSubsystem`. Readers only (`UMelodiaCymaticsSubsystem`, MIs). No second writer.

### Verify from hero overlook

From `CineCameraActor` (Sea Above hero cam), frame mid-ground Fresnel band:
- HorizonEat 0.0: full false-ocean band, horizon crisp
- 0.6: band narrows, colour bleeds to haze
- 1.0: band gone, membrane pulse (radial Biolum) travels — *plane was membrane*

Gates: "Bell perimeter hidden" (before) + "pulse creates biological realization" (after) must both pass at same camera.

---

## 3. Kill B — Volumetric haze companion

| Actor | At rest | At HorizonEat 1.0 |
|-------|---------|-------------------|
| `FM_MoonHaze_Fog` ExponentialHeightFog | density 0.04, heightFalloff 0.15, tint (0.70,0.75,0.90) | density 0.18, MaxOpacity 1.0, tint (0.55,0.60,0.72) desat |
| `FM_MoonHaze_PPV` PostProcessVolume | bloom 0.15, exposure +0.5 | bloom 0.28, exposure -0.3 (world darkens) |
| `FM_MoonHaze_VolumeBox` StaticMeshActor (40×26×9 at 0,0,450) | FrostBloom MI 0.04 | extinction 3.5, silver gone |
| `VolumetricCloud` | normal | horizon cloud band softens, under-sky mirror collapses |

Tie all to HorizonEat linear lerp. Companion, not primary — but kills the *above-water* horizon that SLW cannot.

---

## 4. Kill C — LOD3 impostor crumble + PCG filter-flow cull

### LOD3 is the destroyed state

Per `specs/lookdev/optical_lod_manifest` LOD3 `VistaImpostor_ZeroShimmer`: 200-5000m, res 128, POM 0, Toksvig 1.0, rim 1.8, WPO 0. Any geo beyond 200m is already impostor. HorizonEat makes impostor **stipple to nothing** via:

- `T_BayerDither_8x8` (screen), `T_BlueNoise_64x64` (world), `TemporalAAJitter` (frame) -> `MF_LODDitheredDestruction`
- `OpacityMaskClip = DitherValue > Tension*DestructionMask*HorizonEatLerp`
- `DestructionMask = VertexColor.R * VDM.A * HeightMask` — ridges (R=0.9) die first, valley floor lasts
- HLOD keeps bounds but impostor alpha → 0

### PCG cull

`PCG_HorizonEater_FilterFlow` (PCGEx-bridged): density `*= (1 - HorizonEat * HorizonMask)` where HorizonMask = distance>1500m & dot(view, horizon). Survivors advected toward `HorizonMouthCorridor` spline (HDA export). Points that survive become the filter-flow debris the player sees bending toward horizon.

### Tension gate

Crumble only where `Tension>0.6` or `dist>1500m`. WeaveRidge (avg T 0.96) dies at Tension 0.35; FrillValley floor persists to 0.85 — eaten last. SeamWay (`|Chladni|<0.12`) **never** fully crumbles — becomes Wayfold path to mouth.

---

## 5. PCGEx + Houdini + Oceanology wiring

- **Oceanology owns** real water attenuation (Plays Ks). Never duplicate.
- **Houdini owns** `HDA_P3_HorizonMouthComposer`: upper/lower horizon proxies, filter plates, mouth depth cards, silhouette mask, HLOD variants, filter-flow curves & wayfold locators. Exports curves/points/CSV for PCGEx. Scaffold `Tools/Houdini/horizon_eater/hda_horizon_mouth_composer.py`.
- **PCGEx owns** runtime scatter cull & advection (offline hypotheses from Houdini, hero placements hand-authored).
- **Unreal owns** World Partition streaming, Data Layers (DL_Water vs DL_Creature), Wayfold `BP_WayfoldPair` (UE logic), save persist.

Shared textures: promote `T_BayerDither_8x8`, `T_BlueNoise_64x64`, `T_Iridescence_LUT` from `Saved/Audit/lookdev/optical_lods/shared/` to `/Game/EnvSandbox/Textures/Copernicus/Shared/` (Magpie seam decision: reuse, don't regen).

---

## 6. Rhythm / fashion integration (P3 wayfold)

- Wayfold (Glasswing Courier outfit) aligns local adjacency — visual west vs measured northwest vs wing tension all valid.
- Better rhythm: longer stability, clearer destination, side route, glimpse of feeding current.
- Mara Anchor: inside radius, 1m stays 1m — stops collapse mid-crossing.
- Iris proves matter crosses fold (alpine+lowland species side-by-side, pollen from other horizon).

Clothing classification: omen / predator / pilgrim / lineage / guide alters HorizonEat response curve (hostile +0.2 bias).

---

## 7. How to run (overnight weave)

```bat
:: 1. Offline hypotheses (no editor)
.venv\Scripts\python.exe Tools/PCG/build_horizon_eater_ecosystem.py --seed 20260829
.venv\Scripts\python.exe Tools/PCG/build_faraway_lod_destruction_ecosystem.py --seed 20260829
:: outputs: specs/horizon_eater/horizon_eater_placements.v1.json + manifest
::          specs/faraway_lod_destruction/faraway_lod_destruction_placements.v1.json + manifest

:: 2. MPC scalar (headless, editor closed)
UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript="Content/Python/add_horizon_eater_mpc_params.py"

:: 3. Apply to level (editor open, verify :9316)
curl http://localhost:9316/health
python Tools/ue_run_python.py --file Content/Python/horizon_eater_prototype_build.py
python Tools/ue_run_python.py --file Content/Python/faraway_lod_destruction_build.py
```

Editor single :9316 lock — never run both horizon+faraway applys concurrently.

---

## 8. Evidence

- Offline: `Saved/Audit/horizon_eater/` manifests + placement JSONs (hashed, seed 20260829)
- In-engine: 4 HDR captures via `UMelodiaCaptureRenderSubsystem` (Shot A pristine, B half-eaten, C eaten+membrane, D filter corridor top-down)
- Ledger: `Saved/gate_ledger.json` row `horizon_eater_prototype` (PIE + captures + hashes)
