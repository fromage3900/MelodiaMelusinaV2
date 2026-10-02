# Melodia Melusina — Audio-Reactive Materials Bridge Specification

**Document Version:** 1.0.0  
**Status:** Canonical / Verified  
**Authority:** Single Source of Truth for Audio Synesthetic Material Parameter Binding  
**Ledger Gate:** `AUDIO_REACTIVE_MATERIALS` (`P1_TASK_LEDGER.json`) — **CLOSED**  

---

## 1. Executive Summary & Objective

In the Melodia Melusina aesthetic pipeline, real-time musical clock data (Harmonix Quartz / OSC 128 BPM) drives visual synesthesia across both environmental and character assets. Prior to this integration, `UMelodiaAudioReactivePresentationSubsystem` pushed 16 audio-reactive scalars to `MPC_Melodia_Palette` every frame, but surface materials remained visually static because no canonical material bridge existed to sample the collection safely.

This specification formalizes the **Audio-Reactive Material Bridge** centered on `MF_Melodia_AudioReactive_Bridge`. The function establishes a uniform, physically bounded, and artifact-free synesthetic response across the four canonical master material systems:
1. `M_Master_Toon_Universal` (Primary architectural & prop surface master)
2. `M_Master_Gemstone` (Refractive crystal, diamond fire & internal facet master)
3. `M_Master_SDF_Toon` (Signed-distance-field procedural anime shader)
4. `M_PP_MeluColorGrade` (Post-process volume blendable grade & vignette)

---

## 2. Architectural Invariants

### 2.1 Single-Writer Authority
- **The Sole Writer:** `UMelodiaAudioReactivePresentationSubsystem` (C++) remains the **exclusive writer** of `MPC_Melodia_Palette`.
- **Read-Only Invariant:** Shaders, Material Functions (`MF_Melodia_AudioReactive_Bridge`), Material Instances, and Blueprints are strictly read-only consumers. No shader node or script shall attempt to mutate `MPC_Melodia_Palette`.

### 2.2 Neutral Bypass (Quiescent Guarantee)
- When musical audio is inactive or `GlobalReactivity = 0.0`, the bridge function mathematically collapses to identity operations:
  $$\text{BaseColorOut} = \text{BaseColorIn} \times 1.0$$
  $$\text{EmissiveOut} = \text{BaseEmissiveIn} \times 1.0 + 0.0$$
  $$\text{RoughnessOut} = \text{RoughnessIn} - 0.0$$
  $$\text{NormalPerturb} = \text{NormalIn}$$
  Baseline artist-authored look is preserved with zero luminance drift or color shifts.

### 2.3 Strict Clamping & Safety Bounds
- To eliminate HDR whiteout blowout, bloom flash-bangs, or NaN/Inf GPU exceptions, all modulated channels are clamped at the shader exit:
  - $\text{EmissiveOut} \in [0.0, 20.0]$
  - $\text{RoughnessOut} \in [0.02, 1.0]$
  - $\text{BaseColorOut} \in [0.0, 1.0]$ (linear RGB)
  - $\text{WPO Displacement} \le 50.0\text{ cm}$

---

## 3. MPC Parameter Registry (16 Audio Scalars)

| Parameter Name | Default | Range | Writer Subsystem | Role in Material & VFX Shaders |
| :--- | :---: | :---: | :--- | :--- |
| `BeatPulse` | `0.0` | `[0.0, 1.0]` | `UMelodiaAudioReactivePresentationSubsystem` | Downbeat musical pulse: $cos^2(\text{BeatPhase} \times \pi)$. Drives emissive breathing & rim respiration. |
| `BeatPhase` | `0.0` | `[0.0, 1.0]` | `UMelodiaAudioReactivePresentationSubsystem` | Measure progression $[0.0, 1.0]$. Used for cyclical phase shifts and temporal pacing. |
| `BeatIntensity` | `0.0` | `[0.0, 1.0]` | `UMelodiaAudioReactivePresentationSubsystem` | Musical beat pulse intensity envelope. |
| `Bass` | `0.0` | `[0.0, 1.0]` | `UMelodiaAudioReactivePresentationSubsystem` | Low-frequency / battle energy (`bBattleActive ? BattleIntensity : 0.0`). Drives water wave amplitude & caustics. |
| `Mid` | `0.0` | `[0.0, 1.0]` | `UMelodiaAudioReactivePresentationSubsystem` | Percussive impact pulse / melody line. Drives dispersion flash & cel-step quantization shifts. |
| `Treble` | `0.0` | `[0.0, 1.0]` | `UMelodiaAudioReactivePresentationSubsystem` | High-frequency shimmer. Drives gemstone facet twinkle, star sparkles, and starlight micro-highlights. |
| `GlobalReactivity` | `0.0` | `[0.0, 1.0]` | `UMelodiaAudioReactivePresentationSubsystem` | Master synesthesia blend scalar ($0.0 = \text{bypass}, 1.0 = \text{full audio modulation}$). |
| `BassIntensity` | `0.0` | `[0.0, 1.0]` | `UMelodiaAudioReactivePresentationSubsystem` | Value-aligned alias of `Bass` consumed by `UMelodiaCymaticsSubsystem`. |
| `MidIntensity` | `0.0` | `[0.0, 1.0]` | `UMelodiaAudioReactivePresentationSubsystem` | Value-aligned alias of `Mid` consumed by impact subsystems. |
| `RhythmPulse` | `0.0` | `[0.0, 1.0]` | `UMelodiaRhythmReactivitySubsystem` | Discrete rating judgment trigger pulse (Perfect/Great rating pop, 0.18s decay). |
| `ComboNormalized` | `0.0` | `[0.0, 1.0]` | `UMelodiaRhythmReactivitySubsystem` | Normalized combat combo progress ($0..100 \rightarrow 0.0..1.0$). |
| `CrescendoNormalized` | `0.0` | `[0.0, 1.0]` | `UMelodiaRhythmReactivitySubsystem` | Track section crescendo progression. |
| `CommandEnergy` | `0.0` | `[0.0, 1.0]` | `UMelodiaRhythmReactivitySubsystem` | Special ability / resonance gauge charge level. |
| `BreakPulse` | `0.0` | `[0.0, 1.0]` | `UMelodiaRhythmReactivitySubsystem` | Enemy posture break / shield shatter trigger pulse. |
| `VictoryPulse` | `0.0` | `[0.0, 1.0]` | `UMelodiaRhythmReactivitySubsystem` | Encounter resolution celebration burst (rainbow flare). |
| `DissonanceAmount` | `0.0` | `[0.0, 1.0]` | `UMelodiaNarrativeSubsystem` | Corruption / sorrow seam tension (hue jitter & edge warping). |

---

## 4. Bridge Material Function: `MF_Melodia_AudioReactive_Bridge`

### 4.1 Interface Specification
- **Asset Path:** `/Game/EnvSandbox/Materials/Functions/MF_Melodia_AudioReactive_Bridge`
- **T3D Source:** `specs/materials/MF_Melodia_AudioReactive_Bridge.t3d`
- **JSON Manifest:** `specs/materials/MF_Melodia_AudioReactive_Bridge.v1.json`

#### Inputs:
1. `BaseColorIn` (Vector3, Default: `1.0, 1.0, 1.0`): Input diffuse/albedo color.
2. `BaseEmissive` (Vector3, Default: `0.0, 0.0, 0.0`): Input authored emissive color.
3. `RoughnessIn` (Scalar, Default: `0.5`): Input surface roughness.
4. `NormalIn` (Vector3, Default: `0.0, 0.0, 1.0`): Tangent space normal vector.
5. `EmissiveGain` (Scalar, Default: `1.0`, Range: `[0.0, 5.0]`): Gain multiplier for beat pulse.
6. `BassResponse` (Scalar, Default: `0.5`, Range: `[0.0, 2.0]`): Low-frequency response scale.
7. `MidResponse` (Scalar, Default: `0.5`, Range: `[0.0, 2.0]`): Mid-frequency response scale.
8. `TrebleTwinkle` (Scalar, Default: `0.75`, Range: `[0.0, 3.0]`): Treble sparkle shimmer gain.
9. `PulseCurveExp` (Scalar, Default: `2.0`, Range: `[1.0, 4.0]`): Exponent shaping beat attack/decay.

#### Outputs:
1. `BaseColorOut` (Vector3): Pastel breathing diffuse color ($0.0 \le C \le 1.0$).
2. `EmissiveOut` (Vector3): Pulsed emissive color ($0.0 \le E \le 20.0$).
3. `RoughnessOut` (Scalar): Specular micro-flash roughness ($0.02 \le R \le 1.0$).
4. `NormalPerturb` (Vector3): Audio micro-ripple normal offset.
5. `AudioPulseScalar` (Scalar): Clean normalized $[0.0, 1.0]$ beat factor.
6. `AudioBassScalar` (Scalar): Clean normalized $[0.0, 1.0]$ bass factor.
7. `AudioTrebleScalar` (Scalar): Clean normalized $[0.0, 1.0]$ treble factor.

---

## 5. Master Material Integration Mapping

### 5.1 `M_Master_Toon_Universal`
- **Group:** `12 | Audio Synesthesia`
- **Parameters:**
  - `bAudioReactive_Active` (Static Switch, default `True`)
  - `AudioEmissiveGain` (Scalar: `1.0`, Range: `[0.0, 5.0]`)
  - `AudioBassResponse` (Scalar: `0.5`, Range: `[0.0, 2.0]`)
  - `AudioTrebleTwinkle` (Scalar: `0.75`, Range: `[0.0, 3.0]`)
  - `AudioRoughnessDip` (Scalar: `0.08`, Range: `[0.0, 0.25]`)

### 5.2 `M_Master_Gemstone`
- **Group:** `11 | Audio Synesthesia`
- **Wiring:** Feeds internal facet twinkle (`AudioTrebleTwinkle = 1.2`) and cymatics standing wave lattice (`AudioBassResponse = 0.8`).

### 5.3 `M_Master_SDF_Toon`
- **Group:** `10 | Audio Synesthesia`
- **Wiring:** Feeds signed distance field step banding dilation and anime rim flare (`AudioEmissiveGain = 1.0`, `AudioMidResponse = 0.5`).

### 5.4 `M_PP_MeluColorGrade`
- **Group:** `PostProcess Audio Drive`
- **Wiring:** Feeds subtle radial vignette respiration on `BeatPulse` and lens chromatic aberration punch on `RhythmPulse`.

---

## 6. Verification & Automated Test Suite

- **Unit Test Suite:** `Content/Python/Tests/test_audio_reactive_materials.py` (7/7 tests passing).
- **Master Clamping Suite:** `Content/Python/Tests/test_master_material_clamping.py` (5/5 tests passing).
- **Unified Ecosystem Validator:** `tools/verify_material_vfx_ecosystem.py` (PASS, 0 issues).
- **Audit Receipt:** `Saved/Audit/audio_reactive_materials_audit.json`.
- **Showcase Soft-Freeze:** `my-site-kit/tools/verify_sendoff_freeze.py` (PASS, 100% compliant).
