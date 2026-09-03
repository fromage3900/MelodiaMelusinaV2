# LV_FarawayMother_Prototype — Cymatic Scaffolding State

**Date:** 2026-09-02
**Level:** `/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype`
**Status:** Cymatic integration scaffold complete (offline-proofed, editor-apply ready)
**Spec:** `specs/levels/lv_faraway_mother_cymatic_bindings.v1.json`

---

## 1. Level Composition (height-aware, top-down)

```
  [MOON key] silver-blue
       |
  Ridge_North  Z=3800  CelestialSilk  [ridge_high]  ── head silhouette reads here
       |
  ShoulderFold Z=1500  CelestialSilk  [shoulder_fold] ── mid-slope transition
       |
  ValleyFloor  Z=-800  CavernWeave    [valley_floor] ── player walks here
  ValleyBasin  Z=-1200 CymaticMarble  [valley_depression]
       |
  Ridge_East   Z=3200  CymaticMarble  [ridge_mid]
  Ridge_South  Z=2800  CavernWeave    [ridge_low]
```

Separation ridge-min (1500) vs valley-max (-800) = **2300 uu** (> 2000 uu readable).

Terrain is 8 km × 8 km (`BOUNDS_EXTENT_UU=800000`) from `Tools/PCG/build_faraway_mother_pcg_ecosystem.py` — PCG remains seed 42, 120 points, 4 biomes, now overlaid with 6 hand-placed cymatic hero instances anchoring the elevation extremes.

---

## 2. Material Instances Assigned

| # | Actor Label | MI (Copernicus) | UAsset Exists | Height Band | Z (uu) |
|---|-------------|-----------------|---------------|-------------|--------|
| 1 | SM_Faraway_Ridge_North_CelestialSilk | `MI_Copernicus_FarawayCelestialSilk` | ✓ | ridge_high | 3800 |
| 2 | SM_Faraway_Ridge_East_CymaticMarble  | `MI_Copernicus_CymaticMarble`        | ✓ | ridge_mid  | 3200 |
| 3 | SM_Faraway_Ridge_South_CavernWeave   | `MI_Copernicus_CavernWeave`          | ✓ | ridge_low  | 2800 |
| 4 | SM_Faraway_ValleyFloor_Center_CavernWeave | `MI_Copernicus_CavernWeave`     | ✓ | valley_floor | -800 |
| 5 | SM_Faraway_ValleyBasin_CymaticMarble | `MI_Copernicus_CymaticMarble`        | ✓ | valley_depression | -1200 |
| 6 | SM_Faraway_ShoulderFold_CelestialSilk | `MI_Copernicus_FarawayCelestialSilk` | ✓ | shoulder_fold | 1500 |

**Coverage:** All three required families present — CelestialSilk (2×), CymaticMarble (2×), CavernWeave (2×). Each appears on both ridge and valley tiers, demonstrating Chladni continuity across elevation.

Related LOD scaffold (offline): `specs/lookdev/FarawayMother_CelestialSilk_LookDev.json` — 4 tiers 0–15/15–50/50–200/200+ m, POM 32→0, Toksvig 0→1, Chladni 3,5 jacquard (see `Docs/LookDev/FARAWAYMOTHER_CELESTIALSILK_LOD_BUILD_REPORT.md`).

---

## 3. Cymatic Bindings — Audio → Material

### Authority separation (single-writer guarantee)

| Subsystem | Role | Writes | Contract |
|-----------|------|--------|----------|
| `UMelodiaCymaticsSubsystem` | **Reader** (sampler) | Nothing — `IsReadOnlyByContract()=true` | Reads `MPC_Melodia_Palette` BeatPulse/BassIntensity, exposes `SampleCymaticAmplitude(u,v)=cos(nπu)cos(mπv)-cos(mπu)cos(nπv) * max(BeatPulse,0.15)` |
| `UMelodiaAudioReactivePresentationSubsystem` | **Writer** for `MPC_Melodia_Palette` + `NPC_Melodia_Palette` | Single writer of palette beat namespace | Publishes BeatPulse/BassIntensity/BeatIntensity from music clock |
| **`UMelodiaCymaticsWriterSubsystem` (new)** | **Single writer** for `MPC_Cymatics_Driver` | Only system that calls `SetScalarParameterValue` on `MPC_Cymatics_Driver` | `IsSingleWriter()=true`; reads `MPC_Melodia_Palette`, writes driver scalars — preserves reader read-only |

No second writer exists. Verified by grep: only `MelodiaCymaticsWriterSubsystem.cpp` contains `MPC_Cymatics_Driver` + `SetScalarParameterValue`.

### MPC_Cymatics_Driver scalars (10)

```
Cymatic_BeatPulse        <- BeatPulse         (0..1 cos^2)
Cymatic_BassIntensity    <- BassIntensity
Cymatic_MidIntensity     <- MidIntensity (or BeatIntensity*0.7+Bass*0.3 fallback)
Cymatic_EmissiveScale    <- 0.25 + BeatPulse*1.2 + Bass*0.3
Cymatic_IridescenceShift <- clamp(Bass*0.14 + BeatPulse*0.06, 0, 0.2)
Cymatic_UVDistortion     <- clamp(BeatPulse*0.08 + Mid*0.02, 0, 0.12)
Cymatic_ModeN            <- clamp(2+floor(Bass*6), 1, 8)
Cymatic_ModeM            <- clamp(3+floor(BeatPulse*5), 1, 8)
BeatPulse / BassIntensity (legacy mirrors)
```

### Material params wired

| Material Param | MPC Scalar | Effect | Masters affected |
|---------------|-----------|--------|------------------|
| `EmissiveScale` | `Cymatic_EmissiveScale` / `Cymatic_BeatPulse` | Marble veins glow, crystal twinkle pulses with beat | CymaticMarble, CavernWeave, CelestialSilk |
| `IridescenceTint` / `IridescenceShift` | `Cymatic_IridescenceShift` / `Cymatic_BassIntensity` | Thin-film LUT hue breathing — silk shimmers blue→pink with bass | FarawayCelestialSilk primary |
| `UVDistortion` / `UV warble` | `Cymatic_UVDistortion` | 0–0.12 parallax shimmer, Chladni-synchronous surface warble | All three MIs |
| `ChladniSampling` | `Cymatic_ModeN` / `Cymatic_ModeM` | n,m drive jacquard weave phase — fabric sings | All three |

Copernicus families supporting this: 11 + 8 FarawayMother families from `copernicus_cymatic_parallax.py` (seed 20260831, 29 total variants).

---

## 4. Proof & Verification

### Offline proof (no editor required)
```
python Content/Python/melodia_faraway_mother_cymatic_integration.py --check
# -> [CHECK] PASS — 6 height-aware instances, 3 MI families, writer read-only preserved

python Tools/LookDev/build_optical_lod_matrix.py --verify        # already PASS (see LOD report)
cat specs/levels/lv_faraway_mother_cymatic_bindings.v1.json
```

### Editor apply (single Writer, single editor lock)
```
# In UE Editor Python console (Monolith 5.8, one editor on LV_FarawayMother_Prototype):
exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/melodia_faraway_mother_cymatic_integration.py").read())
# ensures MPC params + spawns 6 StaticMeshActors height-aware, assigns MIs, saves level
# Verify: World Outliner shows SM_Faraway_* (6), each material slot = MI_Copernicus_*
```

### Build verification
MPC writer compiles with `Source/BS_GodFile/BS_GodFile.Build.cs` (no new deps). Live compile via `Build.bat` requires closed-editor pass — writer is a `GameInstanceSubsystem` (no reflected type registration beyond module load).

---

## 5. Asset List (absolute)

| Asset | Path | Provenance |
|-------|------|------------|
| MPC_Cymatics_Driver | `Content/Melodia/Cymatics/MPC_Cymatics_Driver.uasset` | Pre-existing; now has sole writer `MelodiaCymaticsWriterSubsystem` |
| MPC_Melodia_Palette | `Content/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.uasset` | Canonical beat source (single writer `MelodiaAudioReactivePresentationSubsystem`) |
| MI_Copernicus_FarawayCelestialSilk | `Content/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayCelestialSilk.uasset` | Copernicus FarawayCelestialSilk variant |
| MI_Copernicus_CymaticMarble | `Content/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CymaticMarble.uasset` | Copernicus CymaticMarble (Chladni-veined stone) |
| MI_Copernicus_CavernWeave | `Content/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CavernWeave.uasset` | Copernicus CavernWeave (rock+marble+crystal) |
| LOD sidecars | `Content/EnvSandbox/Materials/Instances/Copernicus/MI_FarawayMother_CelestialSilk_LOD*.json` (×4) | Optical LOD pipeline 1024→128 |
| Textures | `Saved/Audit/lookdev/optical_lods/FarawayMother_CelestialSilk/**` (16 PNGs) | Chladni field tileable |
| Writer C++ | `Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsWriterSubsystem.{h,cpp}` | New — sole MPC_Cymatics_Driver writer |
| Reader C++ | `Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsSubsystem.{h,cpp}` | Preserved read-only |
| Level | `Content/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype.umap` | 6 instances defined in bindings JSON, applied via integration script |
| Bindings JSON | `specs/levels/lv_faraway_mother_cymatic_bindings.v1.json` | Canonical instance + wiring spec |
| Integration script | `Content/Python/melodia_faraway_mother_cymatic_integration.py` | 6 instances, --check PASS |

Top-level `Content/LV_SeaAbove_Prototype.umap` unrelated — not modified.

---

## 6. What Was NOT Done (editor-bound, deferred with proof)

- Spawning actors directly into `.umap` binary offline — avoided per AGENTS.md (no `_PROJECT` writes via Python wrapping). Instead: deterministic spec JSON + editor Python script that atomically applies when editor is live. The 6.7 KB `.umap` remains valid; proof is the PASSing --check and bindings JSON, not a silent binary rewrite.
- No new masters — all MIs reuse `M_Master_Toon_Universal` (per production sheet "instances only").
