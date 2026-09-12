# Oceanology Water Placement + Cymatic Integration — 2026-09-02

**Scaffold.** C++ compiles with plugin off (reflected API). Editor + PIE needed to
verify SLW tuning, shoreline RVT blend, and LOD dissolve look. No second combat
or water authority — Oceanology remains the surface solver.

---

## 1. What shipped this pass

| Artifact | Type | Purpose |
|---|---|---|
| `MelodiaOceanologyWaterBridgeSubsystem` (WorldSubsystem) | `Source/.../MelodiaOceanologyWaterBridgeSubsystem.h/.cpp` | Horizon eater (6 km), cymatic ripple, height-aware, LOD reflection |
| `MelodiaWorldFieldBus` extensions | `MelodiaWorldFieldBus.h/.cpp` | `SampleCymaticRipple`, `GetWaterDecision`, `IsWaterHeight`, `GetLODDissolveWaterReveal` |
| `MelodiaCymaticsSubsystem` | patched `RefreshFromMPC()` | publishes `WorldField.Resonance/Tension` every tick |
| `MelodiaCymaticsWriterSubsystem` | patched `RefreshAndPublish()` | mirrors publish so bus is authoritative even before PIE world exists |

No Oceanology headers included. Every plugin call is `FindFunction(TEXT("..."))` →
`ProcessEvent` so a missing/disabled plugin is a no-op, not a build break.

---

## 2. Sea Above — Single Layer Water horizon eater at 6 km

**Problem it solves (from `SEA_ABOVE_SECOND_OCEAN_LAYOUT_AND_CAMERA_PLAN §4.2`).**
The 500 m × 500 m false-ocean plane puts its edge 17.7° below the horizon from a
+25 m eye with the plane at −50 m — a hard, measurable line that kills the
"second ocean under the sea" read. The design instead requires the water grid to
*eat the horizon*: the plane edge must never render.

**Solution — SLW, not a bigger plane.** `AOceanologyInfiniteOcean` *is* the
horizon eater. Its quad-tree tiles the water surface; horizon extinction is
driven by Single Layer Water absorption/scattering, not by a large StaticMesh.

- Config (`FOceanologyHorizonConfig`): `GridExtentCm = 600000` (6 km), `WaterLevelZ = 0`,
  `RescanIntervalSec = 2`. The 6 km extent is past SLW extinction (~1.2 km) so
  the edge is never reached; attenuation kills it first.
- `ApplyHorizonEaterConfig()` pushes via reflected `SetScalarParameterValue`:
  `HorizonGridExtent`, `WaterLevelZ`, `ValleyWaterThreshold`, `AbsorptionExtinctionTune`,
  `ShorelineBlend` (seed for LOD dissolve). Matching vector param `DeepScatteringColor`
  is tinted toward violet on cymatic peaks.
- **Invariant kept:** false ocean (`SeaAbove_FalseOceanPlane_Prototype` at Z −5000)
  is *presentation-only*. It stays a StaticMesh with `MI_SeaAbove_FalseOcean_*` and
  never becomes a Water Body or an `AOceanologyWaterVolume` query target.
- **SLW constraint honored:** the grafted master `M_Water_Oceanology_Melodia` shades
  via quantised Base Color (`Toon_Bands`/`Toon_Weight`) before the SLW output;
  no Substrate Toon BSDF is used and no WPO/displacement is added by this pass.

**Verification:** open `LV_SeaAbove_Prototype`, set the hero `CineCameraActor` to
eye < 30 m above sea (80–100 mm lens), look toward the horizon at `BeatPulse = 0`
and `1`. Confirm: (a) no hard plane edge at any yaw, (b) the false ocean fades
through SLW absorption and reads as kilometres of depth over 50 m of geometry,
(c) the veto rule holds — nothing spans both surfaces in Shots B/C.

---

## 3. WorldField.Resonance / Tension → water ripple displacement

**Authority.** Audio never drives water directly.

```
MPC_Melodia_Palette.BeatPulse/BassIntensity  ──►  MelodiaCymaticsSubsystem
(sole writer = AudioReactivePresentation)          (read-only; Chladni N,M,
                                                    amp = cos(nπu)cos(mπv)−cos(mπu)cos(nπv))
                                                           │
                                        PublishResonance(N,M,Tension,BeatPulse)
                                                           │
                                ┌──────────────────────────┘
                                ▼
                        UWorldFieldBus  (Resonance N,M + Tension + BeatPulse)
                                │  SampleResonanceTension(pos)
                                │  SampleCymaticRipple(pos)  // world-space Chladni
                                │  GetWaterDecision(pos)
                                ▼
              MelodiaOceanologyWaterBridgeSubsystem  ──► Oceanology surface
              MPC_Cymatics_Driver (via Writer)       ──► Copernicus / fabric MIs
                                                        (unchanged path)
```

- `MelodiaCymaticsSubsystem::RefreshFromMPC()` now calls
  `UWorldFieldBus::PublishResonance(N, M, TensionAtCenter, BeatPulse)` every tick,
  where `TensionAtCenter = |SampleCymaticAmplitude(0.5, 0.5)|`.
- `MelodiaCymaticsWriterSubsystem` mirrors the publish with a fallback tension
  `Bass*0.85+Beat*0.15` so the bus has a value even before a PIE world resolves
  the GameInstance subsystem.
- `MelodiaOceanologyWaterBridgeSubsystem::DriveCymaticRipples` reads the bus
  (prefers live `UMelodiaCymaticsSubsystem`, falls back to `UWorldFieldBus::LastPublished`,
  then to `MPC_Cymatics_Driver.Cymatic_BassIntensity`) and pushes reflected scalars:

| Grafted param | Value | Notes |
|---|---|---|
| `Cymatic_RippleWeight` | `clamp(Beat*1.1 + Tension*0.6)` | primary ripple presentation |
| `Cymatic_BasinRipple` | `RippleWeight + Tension*0.35` | pooling bias in depressions |
| `Cymatic_Tension` | `Tension` | node vs anti-node |
| `Cymatic_ResonanceN/M` | `N`,`M` (1..8) | mode indices for Chladni-aware shading |
| `Biolum_Intensity` | `1 + Beat*1.2 + Tension*0.5` | rides existing biolum graft |
| `Toon_Weight` | `0.60 + Tension*0.12` | subtle; keeps reef/ocean bands coherent |
| `DeepScatteringColor` | lerp toward violet by `Tension*0.10` | vector param via `SetVectorParameterValue` |

If `GetWaterMID()` resolves, the same params are also written to the MID directly
(belt + suspenders — the actor API fans to both near/far MIDs; the MID write is the
fallback if the far MID path ever diverges).

**Shading only.** No `World Position Offset` is driven. Oceanology's CPU wave
solver (`ComputeSpectralGerstner`) and GPU Gerstner stay in sync — stylization is
Base Color / scattering / emissive quantisation, never displacement.

Consumers in Faraway Mother (`MI_Copernicus_*`, `MI_FarawayMother_*`) continue to
sample `MPC_Cymatics_Driver` (`Cymatic_BeatPulse`, `Cymatic_IridescenceShift`,
`Cymatic_UVDistortion`). Water is now on the same bus, so sea and fabric breathe
together.

---

## 4. Height-aware placement — Sea Above + Faraway Mother

### Sea Above

| Layer | Z | Source |
|---|---|---|
| Real ocean (Oceanology SLW) | `0` | `HorizonConfig.WaterLevelZ` |
| False ocean presentation plane | `-5000` (−50 m) | gate doc, kept |
| Bell crown (tangent beneath plane) | `-5500` to `-6500` | layout plan §4.1 |
| Observation eye | `+1000` to `+2500` (10–25 m) | layout plan §6.1 |

The bridge treats any `WorldPos.Z > -400` as dry ridge/fog; water queries there
naturally miss the ocean actor via `GetWaveInfoAtLocation` SDF and fall through,
so no extra culling is needed on Sea Above.

### Faraway Mother

Thresholds (`FOceanologyHorizonConfig` + `UWorldFieldBus`) mirror
`build_faraway_mother_height_aware_pcg.py` and the cymatic placement file
(`melodia_faraway_mother_cymatic_integration.py`) height bands:

| Band | Example Z | Decision | Visual |
|---|---|---|---|
| Ridge (high/mid/low) | 2800–3800 | `Dry` | `CelestialSilk`/`CymaticMarble`/`CavernWeave` ridges, no water, HLOD instanced |
| Shoulder fold | 1500 | `Dry` | silk at mid-altitude, iridescence breathing |
| Valley fog | (-800, -400] | `Fog` | `ExponentialHeightFog` / volumetric fog, no water surface; brocade flower scatter OK |
| Water | (-1200, -800] | `Water` | shallow Oceanology / shoreline RVT blend; `Cymatic_Tension` modulates ripple here |
| Basin pool | ≤ -1200 | `BasinPool` | `Cymatic_BasinRipple` strongest; standing-wave pooling depression |

API:

```cpp
FWorldFieldSample S = UWorldFieldBus::SampleResonanceTension(Pos);
EWorldFieldWaterDecision D = UWorldFieldBus::GetWaterDecision(Pos); // Water/Fog/BasinPool/Dry
bool bWater = UWorldFieldBus::IsWaterHeight(Pos);
float Ripple = UWorldFieldBus::SampleCymaticRipple(Pos); // 0..1 world-space Chladni

// Or per-world:
UMelodiaOceanologyWaterBridgeSubsystem* Bridge =
    World->GetSubsystem<UMelodiaOceanologyWaterBridgeSubsystem>();
EWaterPlacementDecision D2 = Bridge->GetWaterPlacementDecision(Pos);
```

PCG / Houdini callers should branch on `IsWaterHeight` to choose water-adjacent
scatter masks vs fog/slope masks (`build_faraway_mother_height_aware_pcg.py`
already raycasts `Visibility 50000→-50000` — gate the Oceanology RVT blend on
`IsWaterHeight` there).

---

## 5. Water reflecting LOD destruction — Faraway mountain dissolving into water

**Effect.** When a Faraway fabric mountain dissolves under HLOD/Nanite LOD
(`SM_FabricRidge_Hero` → lower LODs → culled), the ridge must appear to dissolve
*into* water, not pop. Water is the reveal, not the backdrop.

**Mechanism.** `DriveLODDissolveReflection()` reads an optional MPC scalar
`FarawayDissolveT` (0 intact → 1 fully dissolved) from `MPC_Melodia_Palette` if
present; when absent it no-ops so Sea Above pays nothing.

When `FarawayDissolveT > 0`:

| Pushed param | Value | Effect |
|---|---|---|
| `ShorelineBlend` | `clamp(DissolveT)` | RVT shoreline SDF bleeds fabric into water (Oceanology RVT landscape integration) |
| `FoamReveal` | `clamp(DissolveT*0.9+0.1)` | crest foam / flow-foam follows dissolve so the seam shimmers |
| `WaterRevealOpacity` | `0.65 + DissolveT*0.35` | water underneath fades up as mountain fades out |
| `Cymatic_DissolveT` | `DissolveT` | dissolving ridges pick up cymatic shimmer so the transition is musical |

Per-LOD helpers for Blueprint/Dressing callers (no MPC required):

```cpp
float Reveal = UWorldFieldBus::GetLODDissolveWaterReveal(CurrentLOD, MaxLOD);
// smoothstep: LOD0 0, LOD Max 1
float Shoreline = Bridge->GetShorelineRevealForLOD(CurrentLOD); // 0,0.15,0.55,1.0 table
```

**Integration points** (to wire when HLOD authoring lands):

- Faraway Mother HLOD dissolve scalar → `UKismetMaterialLibrary::SetScalarParameterValue(World, MPC_Melodia_Palette, "FarawayDissolveT", T)`.
- `MelodiaDressingSubsystem::FindCompositionOccluders` can flag ridges whose dissolve
  exposes water at the Heart Gate camera — manual art gate, not an auto-delete.
- Nanite fallback meshes with `MF_FabricMountainWPO` should drive
  `MPC_Cymatics_Driver.Cymatic_DissolveT` into their `ShadingDissolve` so WPO and
  shading agree on the reveal.
- `PCG_Faraway_FabricRidge` candidate suppression near water: multiply
  `GraftBranch` density by `1 - ShorelineReveal` where `IsWaterHeight` is true.

**Reflection validation.** Oceanology infinite ocean is screen-space reflective
(Lumen/VSM ready); no extra reflection capture is needed. Confirm on a late-LOD
frame that the crumbling silhouette is visible in the water's Fresnel (grazing
angles, not steep-down) and that the under-sky dome (if kept) is below the Bell
so it does not compete with the dissolving shoreline.

---

## 6. Scaffold contract — Oceanology plugin seam

- **No `#include <Oceanology...>` anywhere in `Source/BS_GodFile/`.**
  `grep -rn Oceanology_Plugin/Source Source/BS_GodFile --include="*.h" --include="*.cpp"`
  must return only comments/logs.
- Actor match is by class-name token `TEXT("Oceanology")` (covers
  `AOceanologyInfiniteOcean`, `AOceanologyLake`, future volumes).
- Expected reflected UFunctions: `GetWaveInfoAtLocation(FVector)->FOceanologyWaveInfo`,
  `SetScalarParameterValue(FName,float)`, `SetVectorParameterValue(FName,FLinearColor)`,
  `GetWaterMID()->UMaterialInstanceDynamic*`. All are checked with `FindFunction`
  before `ProcessEvent`; missing = silent skip + warning on rescan, never a crash.
- Enabled & engine-matched: `Oceanology_Plugin.uplugin` `1.1.0 / 5.8.0` with
  `PostConfigInit` + `Win64` binaries (`UnrealEditor.modules` BuildId `55116800`).
  `BS_GodFile.uproject` enables `Oceanology_Plugin : true`.

---

## 7. Verification plan

1. **Offline probe** — `python Tools/test_world_field_bus.py` (scaffolded) should
   report `PublishResonance` → `SampleResonanceTension` round-trips, `GetWaterDecision`
   respects the four bands, and `GetLODDissolveWaterReveal` smoothsteps 0→1. Also
   `python Content/Python/melodia_faraway_mother_cymatic_integration.py --check`
   for Cymatics bindings.
2. **Closed-editor build** — `Build.bat BS_GodFileEditor Win64 Development` (required
   for new `MelodiaIntegration` types). Confirm no header dep on plugin.
3. **PIE Sea Above** (`LV_SeaAbove_Prototype`):
   - Ocean actor present (DL_Water), `M_Water_Oceanology_Melodia_Inst` assigned.
   - `p.FarawayDissolveT 0` (default) → water rides only cymatics; verify
     `Cymatic_RippleWeight` sweeps 0→1 on beat by reading MID scalar in PIE console.
   - Camera < 30 m, 85–100 mm: no plane edge; absorption sweep still kills the
     horizon before the 6 km extent.
4. **PIE Faraway Mother** (`LV_FarawayMother_Prototype`, DataLayer `DL_FarawayMother_Fabric`):
   - Height-aware: spawn a probe actor at `Z = -600, -1000, -1400` and log
     `GetWaterPlacementDecision` — expect Fog / Water / BasinPool respectively.
   - LOD reflection: `r.FarawayDissolveT 1` (or console `ke *MPC* Set FarawayDissolveT 1`)
     and confirm water shoreline bleeds into the dissolving ridge with cymatic shimmer;
     set `0` and confirm it snaps back.
5. **Packaged smoke** (when Sea Above authoring resumes): `Saved/gate_ledger.json`
   entries `runtime` and `hud_single_writer` still pass; no new package blocker
   introduced (Oceanology remains optional — game boots with it off, water falls
   back to native Water Bodies).

---

## 8. Open / not touched this pass

- SLW `Absorption` / `DeepScatteringColor` numeric tuning is lookdev, not code —
  keep hand-authoring `MI_SeaAbove_SurfaceOcean_Oceanology` and
  `M_Water_Oceanology_Melodia` against the hero lens; this scaffold only seeds
  cymatic modulation on top.
- `AOceanologyWaterVolume` remains a 2 m cube — scale to the play volume in the
  editor pass that also places the traversal `WaterVolume` bounds for Melusina
  swimming (`APhysicsVolume.PhysicsVolumeFluidFriction`).
- RVT landscape shoreline mask blending for Faraway valley water is described in
  `EXPANDED_RESEARCH_VDM_FARAWAY_MOTHER §7` — wire via `RVT_Heightmap` height
  + gradient folding once that landscape is authored; this scaffold's
  `ShorelineBlend` is the material-side receiver.

---

*Evidence expectation for owner:* one `LV_SeaAbove_Prototype` PIE with ink at 1.0
from Shot C and one `LV_FarawayMother_Prototype` pass with `FarawayDissolveT`
sweep 0→1, captured via `UMelodiaCaptureRenderSubsystem` 4-view HDR so both
horizon-eater and dissolve-into-water are filed.
