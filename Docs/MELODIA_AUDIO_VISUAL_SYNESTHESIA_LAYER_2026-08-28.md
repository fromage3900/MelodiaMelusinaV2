# Melodia — Audio-Visual Synesthesia & Beat-Reactivity Architecture

**Date:** 2026-08-28
**Scope:** C++ Music Clock $\rightarrow$ MPC Palette $\rightarrow$ MetaSounds $\rightarrow$ PPV $\rightarrow$ Niagara Petal Loop FX
**Core Goal:** Transform musical rhythm into breathing, tactile game-world visual feedback.

---

## 1. The 5-Tier Synesthesia Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Tier 1: C++ Quartz / Harmonix Master Clock (UMelodiaMusicClockSubsystem)     │
│   • Single authoritative musical time source (128 BPM / 4/4 time signature) │
│   • Sub-frame beat phase tracking: BeatPhase = (t % SecondsPerBeat) / SpB   │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────────────┐
│ Tier 2: Continuous Envelopes & Beat-Hit Detectors                           │
│   • BeatPulse = exp(-8.0 * BeatPhase) [exponential per-beat decay]          │
│   • BassIntensity = RMS energy of low-pass audio stems (< 120Hz)            │
│   • RhythmPulse = 1.0 on Perfect/Great note judgment (0.18s decay)          │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────────────┐
│ Tier 3: Central Dispatch via MPC_Melodia_Palette                            │
│   • Scalar Parameters: BeatPulse, BassIntensity, MidIntensity, RhythmPulse  │
│   • Vector Parameters: MelusinaAccentGold, MelusinaTrimLavender, BiolumGreen│
└──────────────────┬────────────────────┬────────────────────┬────────────────┘
                   │                    │                    │
┌──────────────────▼──────┐  ┌──────────▼─────────┐  ┌───────▼────────────────┐
│ Tier 4A: MetaSounds     │  │ Tier 4B: PPV Lens  │  │ Tier 4C: Niagara FX    │
│ • MS_HarmonicSynth      │  │ • Bloom Intensity  │  │ • NS_Melodia_PetalLoop │
│ • Stem Dynamic Shimmer  │  │ • Chromatic Fringe │  │ • Backdrop Pulse Ring  │
│ • Adaptive Harmony Mix  │  │ • Color Saturation │  │ • Lane Hit Spark Burst │
└─────────────────────────┘  └────────────────────┘  └────────────────────────┘
```

---

## 2. Dispatch Rules & Reactive Math

| Parameter | Source Event / Engine | Formula / Envelope | Target Consumers |
| :--- | :--- | :--- | :--- |
| `BeatPulse` | Clock downbeat / upbeat | $\text{BeatPulse} = \exp(-8.0 \cdot \text{BeatPhase})$ | • PPV Bloom (`0.8 + 0.6 \cdot \text{BeatPulse}`)<br>• `M_Melodia_AudioReactive_Petal` emissive rim<br>• UMG filigree border 1px respiration |
| `BassIntensity` | MetaSound sub/kick stem | $\text{RMS}(\text{Sub} + \text{Kick})$ | • Water Gerstner WPO displacement amplitude<br>• `NS_Melodia_PetalLoop` vortex curl noise strength (`120 \rightarrow 200`)<br>• Micro camera-shake on heavy impacts |
| `RhythmPulse` | `SubmitRatedInput` | $1.0 \text{ on Perfect, decaying in } 0.18\text{s}$ | • PPV Chromatic Aberration (`0.0 \rightarrow 0.45`)<br>• `NS_Melodia_LaneHit` particle burst<br>• `WBP_GradePop` judgment ring expansion |
| `WaterWavePhase` | Global simulation time | $\phi = 2\pi \cdot (\text{Bar} + \text{BeatPhase}/4)$ | • Gerstner wave continuous phase sync<br>• Dynamic caustics light function pan |

---

## 3. Ambient Celestial Petal Loop FX (`NS_Melodia_PetalLoop`)

- **Design Philosophy**: Ambient celestial cherry blossom petals and starlight motes that gently swirl in the breeze and expand radially on rhythmic downbeats.
- **Emitter Structure**:
  1. **`Emitter_CelestialPetals`**:
     - Material: `M_Melodia_AudioReactive_Petal` (2-sided masked subsurface with Champagne Gold / Dusty Sakura gradient).
     - Particle Count: 35 active particles, 4.0-7.5s lifetime.
     - Audio Reactivity:
       - Radial spawn velocity expands by $+35\%$ on `BeatPulse`.
       - Curl noise turbulence scales with `BassIntensity` ($120 \rightarrow 200$ strength).
       - Subsurface rim glow flares up to $3.5\times$ on kick hits.
  2. **`Emitter_StarlightSparks`**:
     - Particle Count: 50 micro-sparks with $25\times$ emissive intensity.
     - Orbiting particle center with high-frequency shimmer.

---

## 4. Material & Post-Process Specifications

1. **`M_Melodia_AudioReactive_Petal`**:
   - Two-Sided Subsurface shading model (`MSM_Subsurface`).
   - Reads `MPC_Melodia_Palette.BeatPulse` to modulate emissive subsurface transmission.
   - Spec file: `specs/materials/M_Melodia_AudioReactive_Petal.t3d`.
2. **`PP_Melodia_AudioReactive_Lens`**:
   - Post-Process Material Domain (`MD_PostProcess`).
   - Reads `MPC_Melodia_Palette.RhythmPulse` to apply a localized lens chromatic aberration punch on Perfect note hits.
   - Spec file: `specs/materials/PP_Melodia_AudioReactive_Lens.t3d`.

---

## 5. Verification & Audit

- Simulation verified across 32 time-series samples over a 4-beat bar @ 128 BPM.
- Audit report exported to `Saved/Audit/melodia_audio_visual_synesthesia_audit.json`.
- All contracts passing cleanly under `run_tests.ps1`.
