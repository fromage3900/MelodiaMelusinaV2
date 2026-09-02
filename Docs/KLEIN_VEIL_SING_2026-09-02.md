# Klein Veil — Make It Sing (Audio-Reactive Hero Asset)

**Date:** 2026-09-02 · **Seed:** 20260829 · **Choice:** Klein Veil (3D Chladni Klein bottle-veil) — chosen over Gyroid Heart
**Status:** Offline proof complete (PBR + VDM + LOD + MPC wiring + height-aware placement). In-editor import is idempotent via `Content/Python/klein_veil_import.py`.

## Why Klein Veil

- Klein bottle already ships as SDF `M_SDF_Klein_Bottle` in 61-material math-art lineage — veil extends it to Faraway Mother nacre fabric.
- Non-orientable topology = perfect metaphor for Faraway Mother seam (inside/outside fold).
- Gyroid Heart would duplicate `LaceCanopy` heart_grace; Klein Veil owns the nodal `ResonantSeamWay` corridor.

## What Was Built (entire pipeline)

| Layer | Artifact | Path |
|-------|----------|------|
| **VDM** | Vector displacement (RGB=XYZ lateral+lift, A=mask) 32f proxy | `Saved/Audit/vdm_fabric/T_FarawayMother_Fabric_VDM_KleinVeil.png` + `.npy` (32f) → UE `{UE_VDM_PATH}` |
| **Cymatic** | Chladni standing wave `Z=cos(nπu)cos(mπv)-cos(mπu)cos(nπv)` modes (4,6)/(8,12)/(14,18)/(24,18) modulates pleat freq & emissive | Baked into PBR Height/Iridescence/Emissive; runtime `UMelodiaCymaticsSubsystem.SampleCymaticAmplitude(U,V)` read-only |
| **Brass** | Filigree spiral wrap on Klein seam + bracing hoop + aged patina bloom | Seam mask in BaseColor/Metallic/Emissive, roughness 0.25 |
| **Surreal fabric** | Nacre veil (240,245,255) + CelestialSilk constellation + AquaticLullabyLace micro-weave + thin-film iridescence LUT | PBR 9-map `Saved/Audit/klein_veil/T_KleinVeil_*` |
| **LOD** | Optical LOD 0-3: POM 32→0, Toksvig 0→1.0, WPO 1.0→0.0, rim 1.0→0.15, Bayer dither | `specs/klein_veil/klein_veil_manifest.v1.json` `lod` block |
| **Audio→visual MPC** | Single writer `UMelodiaAudioReactivePresentationSubsystem` → `MPC_Melodia_Palette` (BeatPulse/Bass/Mid/Treble) + twin `NPC_Melodia_Palette`; consumer is read-only `UMelodiaCymaticsSubsystem` | See Wiring below |
| **Placement** | Height-aware, instances only, Faraway Mother valley | FrillValley (-900,6200) primary + ResonantSeamWay echo (1200,5500), raycast 25000→-10000 Visibility, +35uu hover |

## MPC Wiring (single writer preserved)

- **Sole writer:** `UMelodiaAudioReactivePresentationSubsystem` — writes `BeatPulse` (`cos²(BeatPhase·π)`), `BeatPhase`, `BeatIntensity`, `Bass`/`Mid`/`Treble` to `MPC_Melodia_Palette` and twin `NPC_Melodia_Palette` each tick. *Never add a second writer.*
- **Reader:** `UMelodiaCymaticsSubsystem` (`IsReadOnlyByContract()=true`) — `SampleCymaticAmplitude(U,V)`, `GetCymaticMode()`, `GetBeatPulse()`, `GetBassIntensity()` read MPC via `GetParameterCollectionInstance`.
- **Klein Veil bindings (MI `{UE_MI_PATH}`):**
  - `MPC.BeatPulse 0..1` → `EmissiveMapIntensity` + `IridescenceIntensity` + `WPO_Resonance_Scale` pulse (`1.0 + BeatPulse*0.6`), `BeatPulse` scalar on MI
  - `MPC.Bass` → `foldFreq = baseFreq + Bass*2.0` + VDM B lift (`WPO scale.z`)
  - `MPC.Mid` → `DreamFlowSpeed` seam panning (`+Mid*0.4`)
  - `NPC.BeatPulse` → `NS_KleinVeil_Sparkle` Niagara spawn
  - Oceanology already grafted: valley haze `Biolum_Intensity 1+BeatPulse*1.5` shares beat

Master material must expose: `EmissiveMapIntensity`, `IridescenceIntensity`, `WPO_Resonance_Scale`, `DreamFlowSpeed`, `POM_StepCount`, `Toksvig_AntiAliasing_Weight` (all present on `M_Master_Toon_Universal` per `Brass_Structure_Framework.md`).

## Height-Aware Valley Placement

Level: `/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype` (8 km × 8 km, WorldField Tension 0..1)
- **Primary:** `KleinVeil_ValleyHeart` at (-900, 6200) — FrillValley (T=0.32) low basin, fog + brocade understory, seam faces Heart Gate.
- **Echo:** `KleinVeil_RidgeEcho` at (1200, 5500) — ResonantSeamWay nodal corridor (|Chladni|<0.12), sparse, rhythm checkpoint adjacency.
- Raycast: `LineTraceSingle(Visibility, (x,y,25000)->(x,y,-10000), complex=true)` → `ImpactPoint.z`; offline synthetic fallback `landscape_z_synthetic` +35uu hover so veil never clips. **Instances only** (ISM/PCG `PCG_Faraway_FabricRidge`), no unique `StaticMeshActor` breaking batching.

## UE Import (when editor is up)

```python
# One editor, unattended:false, then save
exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/klein_veil_import.py", encoding="utf-8").read())
# Verifies: MI exists, textures imported to /Game/EnvSandbox/Textures/Copernicus/KleinVeil, actors spawned height-aware, tagged WPO/biome
```

## Proof (offline, no editor)

```
  C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\klein_veil\T_KleinVeil_BaseColor.png
  C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\klein_veil\T_KleinVeil_Normal.png
  C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\klein_veil\T_KleinVeil_Roughness.png
  C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\klein_veil\T_KleinVeil_Metallic.png
  C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\klein_veil\T_KleinVeil_Height.png
  C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\klein_veil\T_KleinVeil_ORM.png
  C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\klein_veil\T_KleinVeil_Emissive.png
  C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\klein_veil\T_KleinVeil_Iridescence.png
  C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\klein_veil\T_KleinVeil_Opacity.png
  C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\vdm_fabric\T_FarawayMother_Fabric_VDM_KleinVeil.png
  C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\vdm_fabric\T_FarawayMother_Fabric_VDM_KleinVeil.npy
  Manifest: specs/klein_veil/klein_veil_manifest.v1.json hash=5ac9d7750c2c1900
  Importer: Content/Python/klein_veil_import.py
  Placement: Saved/Audit/vdm_fabric/klein_veil_placements.json
```

PNGs are tileable (wrapped noise, 2π Chladni), 8-bit proxy for review; real cook is 32f EXR VDM + BC7/BC5/BC4 import via `verify_tex_contract.py`. Change seed → new manifest + QA renders.

## Files Created This Run

- `Saved/Audit/klein_veil/T_KleinVeil_*.png` (9 PBR maps, 2048x2048)
- `Saved/Audit/vdm_fabric/T_FarawayMother_Fabric_VDM_KleinVeil.png` + `.npy`
- `specs/klein_veil/klein_veil_manifest.v1.json`
- `Saved/Audit/vdm_fabric/klein_veil_placements.json`
- `Content/Python/klein_veil_import.py`
- `Docs/KLEIN_VEIL_SING_2026-09-02.md` (this file)

## Next (owner)

1. `hython Tools/Houdini/vdm_fabric_mountains/vdm_fabric_baker.py --variant KleinVeil --res 4096` for true EXR (optional — PNG proxy is review-safe)
2. Editor: run `klein_veil_import.py`, verify PIE: BeatPulse lifts emissive + WPO, Bass deepens pleats, Mid pans seam, LOD0 crevice → LOD3 flat no pop (Bayer dither)
3. `Tools/mcp_tool_surface.py --live` capture 4-view HDR + `IsPPVStackCanonical` gate before chapter map migration
