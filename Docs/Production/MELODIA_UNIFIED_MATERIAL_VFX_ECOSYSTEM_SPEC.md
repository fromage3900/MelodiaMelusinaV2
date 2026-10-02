# Melodia Melusina — Unified Material & VFX Ecosystem Specification

**Status:** Approved & Implemented (SSOT Standard)  
**Authority:** Jev SystemOne Consensus (`UNIFIED_MATERIAL_AND_VFX_ECOSYSTEM` @ 1.00 probability / 0.99 confidence)  
**Automated Validator:** `tools/verify_material_vfx_ecosystem.py` (Pass 100% Green)  

---

## 1. Scope & Architectural Mandate

To ensure the long-term visual fidelity, performance, and stability of Melodia Melusina, all material and particle systems must adhere strictly to the **Unified Material & VFX Ecosystem** standard. This architecture eliminates:
1. **Unbounded Shader Math:** Specular blooming, NaN subsurface scattering, and runaway displacement.
2. **Niagara Billboard Clipping:** Square particle artifacts caused by unweighted alpha or streaming mip drops.
3. **SubUV Coordinate Desynchronization:** Stretched or jittering animated flipbook frames.
4. **Post-Process Visual Conflict:** Competing full-screen blendables causing oversaturation or crushed shadows.

---

## 2. Core SSOT Standards

### 2.1 Master Material Clamping Specification

All material instances deriving from Melodia master materials must respect safe numerical boundaries. Clamping is enforced mathematically at the master graph level and audited via `master_material_clamping_engine.py`:

| Subsystem | Master Graph | Parameter | Safe Clamp Range | Purpose |
|---|---|---|---|---|
| **Gemstone & Cymatics** | `M_Master_Gemstone` | `RefractionDepth` | `[0.01, 10.0]` | Prevents internal raymarch infinite loop / VRAM spikes |
| | | `DispersionStrength` | `[0.0, 2.5]` | Calibrates chromatic aberration along facet normals |
| | | `InternalCausticsIntensity` | `[0.0, 5.0]` | Prevents caustics overexposure in direct sunlight |
| **Procedural SDF** | `M_Master_SDF_Toon` | `SDF_Steps` | `[8, 64]` | Maintains 60 FPS raymarch budget on consumer GPUs |
| | | `SDF_Thickness` | `[0.001, 0.5]` | Prevents inverted volume geometry |
| | | `SDF_BandingFrequency` | `[1.0, 32.0]` | Controls toon stepped contour frequency |
| **Oceanology / Water** | `M_Water_Oceanology_Melodia` | `WaterExtinctionDistance` | `[10.0, 2000.0]` | Depth-attenuated light transmission |
| | | `GerstnerWaveSpeed` | `[0.1, 5.0]` | Harmonizes surface wave chop with flower wind |
| | | `CausticsSpeed` | `[0.1, 4.0]` | Synchronizes caustics flow with underwater current |
| **Post-Process Volumes** | `M_PP_StorybookOutline_Frozen` | `OutlineThickness` | `[0.5, 3.5]` | Single-pixel sharp storybook inking |
| | | `OutlineDepthThreshold` | `[0.01, 1.0]` | Depth discontinuity sensitivity |
| | | `OutlineNormalThreshold` | `[0.1, 0.9]` | Surface curvature discontinuity sensitivity |
| **SubUV Flipbooks** | `MI_Niagara_Kawaii_SparklePulse_Flipbook` | `GridCols` / `GridRows` | `[1, 16]` | Power-of-two texture coordinate slicing |
| | | `AnimationSpeed` | `[0.0, 10.0]` | Frame stepping rate |
| | | `SubUV_Index` | `[0, 255]` | Array index clamp |

---

### 2.2 Niagara Particle Texture Hardening & DXT1 Opacity Rule

Square billboard defects on particle emitters (`NS_Morning_GlitterGlint`, `NS_Melusina_StarSparkle`, `NS_ChoralSheep_BeatStar`) are strictly prevented via two invariant rules:

1. **DXT1 Safe Opacity Math:**
   $$\text{Opacity} = \text{Texture.R} \times \text{ParticleColor.A}$$
   Never sample from `Texture.A` on DXT1/BC1 textures, as the alpha channel is quantized to 1-bit or discarded, producing harsh square geometry.

2. **Effects Streaming Policy:**
   All particle sprite textures are flagged:
   - `never_stream = True` (Texture never drops to low-res mips under VRAM pressure).
   - `lod_group = TEXTUREGROUP_Effects` (Preserves sharp glint cores and smooth radial tapers).

---

### 2.3 Post-Process Volume Blendable Weighting

The global camera and regional volumes in `L_MelusinaMorning` operate under an explicit weighted hierarchy:
- `MI_StorybookOutline_Frozen`: **Weight 1.0** (Continuous silhouette definition).
- `MI_MeluColorGrade_Frozen`: **Weight 0.85** (Pastoral morning grading with soft peach halation).
- `MI_PP_EdgeDesat_Morning`: **Weight 1.0 (Regional)** (Edge vignetting desaturation).
- `M_PP_StorybookVines_Inst`: **Weight 0.35 (Conditional)** (Framing vine overlays).

---

## 3. Automated Continuous Verification

Run the ecosystem validator from workspace root:
```powershell
python tools/verify_material_vfx_ecosystem.py
```

The validator verifies:
1. Presence and integrity of master clamping definitions (25 parameter types).
2. Niagara texture hardening status (17 textures, 12 systems).
3. Exact alignment between on-disk video loops (25 files) and `material_loops_manifest.json`.
4. Existence and readability of all 10 contact sheets (5 PNG + 5 WebP).
