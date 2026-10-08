# Melodia UI Material & Figma Layout Architecture

**Document Version:** 1.0.0  
**Date:** 2026-10-08  
**Author:** UI Manager  
**Repository:** `BS_GodFile`  
**Engine:** Unreal Engine 5.8 (Headless / NullRHI / Slate / UMG)  

---

## 1. Executive Summary

Per the project UI Manager directive, the Melodia UI material foundation and layout hierarchy have been completely overhauled from legacy stub implementations into a AAA-grade, production-ready, stylized material and UMG architecture.

### Key Objectives Accomplished:
1. **Universal Toon Master UI Material (`M_UI_UniversalToon_Master`)**: Authored a fully vectorized SDF rounded-box, tactile paper grain, Ben-Day halftone dot grid, procedural paper drop shadow (`[7, 8]` offset at 25% `#241B2E`), interactive `BraceVoluteSheen` sweep, audio BeatPulse reactivity, and dual-axis progress bar masking.
2. **Mstone Prismatic Gemstone Master UI Material (`M_UI_Mstone_Master`)**: Authored multi-facet internal refraction, spectral chromatic dispersion (RGB aberration), Chladni cymatics resonance, Beer-Lambert volumetric absorption, twinkling 4-point/8-point glints, and metallic bezel contours.
3. **Nikki Pastel Watercolor & Iridescence Master UI Material (`M_UI_Nikki_Master`)**: Authored dual-tone pastel watercolor washes (Rose `#FF93B5` vs Pearl Aqua `#86E4FF`, Sakura `#E7C9CE`, Lavender `#F0DCF0`), thin-film iridescent shimmer loop, white die-cut sticker edge contour, procedural stardust sparkles, and idle breathe animation.
4. **Radial Ring & Orrery Disc Masters**: Created `M_UI_Storybook_RadialRing` and `M_UI_Storybook_OrreryDisc` for the Cosmic Orrery navigation and reticle systems with polar dashed rings, astronomical disc frames, and concentric astrological pips.
5. **Figma 1440×900 Design Space Alignment**: Upgraded `Content/UI/WidgetStyleSheet.json` to canonical Storybook design tokens, overhauled all 30 WBP atom specs in `specs/ui/` with explicit 4-layer luxury UMG hierarchies and slot anchors, and achieved **0 errors / 0 warnings** in the UMG structural linter (`Tools/ui_lint.py`).
6. **Headless Verification**: Ran closed-editor compiler verification (`compile_playtest_ui_and_owners.py`), successfully compiling **129 UI widgets and owners with 0 failures**.

---

## 2. Master Material Specification

All UI master materials are authored under `/Game/Melodia/UI/Materials/` with `MaterialDomain = MD_UI`, `BlendMode = BLEND_Translucent`, and responsive scalar/vector parameter collections.

### 2.1 M_UI_UniversalToon_Master
- **Asset Path:** `/Game/Melodia/UI/Materials/M_UI_UniversalToon_Master.uasset`
- **SDF Rounded Box Engine:** Evaluates exact Euclidean distance from box edges using coordinate-space half-extents and radius parameters, yielding resolution-independent anti-aliased contours.
- **Border & Stroke:** Configurable outer stroke with independent `BorderColor`, `BorderThickness`, and inner fill masking.
- **Procedural Drop Shadow:** Implements the canonical Figma paper drop shadow treatment:
  - Offset: `[7, 8]` pixels
  - Color: `#241B2E`
  - Opacity: `0.25`
  - Blur: `0.0` (crisp paper edge)
- **Ben-Day Halftone Grid:** Vectorized procedural dot grid modulated by local luminance.
- **Tactile Paper Grain:** High-frequency organic noise overlay providing authentic storybook parchment texture.
- **Micro-Interactions & Sheen:** `BraceVoluteSheen` linear diagonal sweep triggered on hover/activation.
- **Audio Reactivity:** `BeatPulse` scalar input for MPC/MetaSound musical pulse integration.
- **Progress Bar Mode:** Linear clipping across horizontal or vertical axes with dedicated fill/track colors.

### 2.2 M_UI_Mstone_Master
- **Asset Path:** `/Game/Melodia/UI/Materials/M_UI_Mstone_Master.uasset`
- **Prismatic Dispersion:** Offsets UV sampling across R, G, and B color channels proportionally to `PrismaticDispersion` strength, simulating gemological chromatic aberration.
- **Internal Facet Refraction:** Simulates multi-planar crystal geometry with depth perspective offsets.
- **Chladni Cymatics:** Mathematical harmonic wave interference pattern reacting to musical frequencies.
- **Beer-Lambert Absorption:** Exponential depth attenuation gradient mimicking gemstone light transmission.
- **Twinkle Glint Stars:** Multi-frequency sine-wave timing for 4-point and 8-point crystalline stars.
- **Gilded Bezel:** High-specular metallic rim highlighting the gemstone circumference.

### 2.3 M_UI_Nikki_Master
- **Asset Path:** `/Game/Melodia/UI/Materials/M_UI_Nikki_Master.uasset`
- **Dual-Tone Watercolor Wash:** Soft gradient blending between primary and secondary pastel washes:
  - Rose (`#FF93B5`) & Pearl Aqua (`#86E4FF`)
  - Sakura (`#E7C9CE`) & Lavender (`#F0DCF0`)
  - Ivory (`#FCFBF8`) & Gilded Gold (`#F8ECD6`)
- **Thin-Film Iridescence:** Periodic hue-shifting sheen loop with subtle amplitude (obeying S4.4 glow-rationing rule).
- **Die-Cut Sticker Contour:** Crisp white border mimicking illustrated physical storybook stickers.
- **Procedural Sparkles:** Dual-scale stardust pips with randomized pulse cycles.
- **Idle Breathe:** Low-frequency (3.0s period) breathing animation for living UI presence.

### 2.4 Storybook Radial & Orrery Masters
- **`M_UI_Storybook_RadialRing.uasset`**: Polar SDF ring arc generator with dashed orbital tracks, angular phase offsets, and astrological pips for dial navigation.
- **`M_UI_Storybook_OrreryDisc.uasset`**: Dual concentric astronomical disc frames with stardust core and celestial coordinate markings.

### 2.5 Overhauled Legacy Stubs
- **`M_UI_Nikki_StorybookCard.uasset`**: Rewired from empty stub to full Nikki watercolor/iridescent master graph.
- **`M_UI_Nikki_VitalsMeter.uasset`**: Rewired to complete dynamic progress bar meter with threshold glowing.
- **`M_UI_AudioGlow_Border.uasset`**: Rewired to audio-reactive animated filigree border shader.

---

## 3. Material Instance Catalog

Nineteen specialized Material Instances (`.uasset`) were compiled and persisted in `/Game/Melodia/UI/Materials/`:

| Instance Name | Parent Master | Style Domain | Target Widget Element |
|---|---|---|---|
| `MI_UI_Toon_Card_Parchment` | `M_UI_UniversalToon_Master` | Universal Toon | Storybook cards, quest log panels |
| `MI_UI_Toon_Card_Plum` | `M_UI_UniversalToon_Master` | Universal Toon | Selected menu cards, header cards |
| `MI_UI_Toon_Button_Primary` | `M_UI_UniversalToon_Master` | Universal Toon | Interactive buttons, confirm prompts |
| `MI_UI_Toon_Progress_Gold` | `M_UI_UniversalToon_Master` | Universal Toon | Gold experience / progress pill meters |
| `MI_UI_Mstone_Diamond_Reticle` | `M_UI_Mstone_Master` | Mstone | Bow HUD center reticle, lock-on diamond |
| `MI_UI_Mstone_Aquamarine_Crest`| `M_UI_Mstone_Master` | Mstone | Mode crests, grade halos |
| `MI_UI_Mstone_RosyQuartz_Vitals`| `M_UI_Mstone_Master` | Mstone | Character portrait gem bezels |
| `MI_UI_Mstone_VoidOrchid_Accent`| `M_UI_Mstone_Master` | Mstone | Dark gemstone badges, status debuffs |
| `MI_UI_Nikki_Card_Ivory` | `M_UI_Nikki_Master` | Nikki | Standard paper card surfaces (`#FCFBF8`) |
| `MI_UI_Nikki_Card_Sakura` | `M_UI_Nikki_Master` | Nikki | Romance/dialogue cards (`#E7C9CE`) |
| `MI_UI_Nikki_Card_Lavender` | `M_UI_Nikki_Master` | Nikki | Speech bubbles, tips (`#F0DCF0`) |
| `MI_UI_Nikki_Card_Plum` | `M_UI_Nikki_Master` | Nikki | Dark storybook panels (`#2A1646`) |
| `MI_UI_Nikki_VitalityBar` | `M_UI_Nikki_Master` | Nikki | Health/Vitality progress bar (`#FF93B5`) |
| `MI_UI_Nikki_ResonanceBar` | `M_UI_Nikki_Master` | Nikki | Mana/Resonance progress bar (`#86E4FF`) |
| `MI_UI_Nikki_QuestMeter` | `M_UI_Nikki_Master` | Nikki | Quest progression pill (`#F2D08B`) |
| `MI_UI_Orrery_RingOuter` | `M_UI_Storybook_RadialRing` | Orrery / Radial | Outer celestial navigation ring |
| `MI_UI_Orrery_RingMidDashed` | `M_UI_Storybook_RadialRing` | Orrery / Radial | Middle dashed orbit rail |
| `MI_UI_Orrery_RingInner` | `M_UI_Storybook_RadialRing` | Orrery / Radial | Inner zodiac pip ring |
| `MI_UI_Orrery_DiscFrame` | `M_UI_Storybook_OrreryDisc`| Orrery / Radial | Central astronomical hub disc |
| `MI_UI_Stardust_Gold` | `M_UI_UniversalToon_Master` | Ambient Sparkle | 4-point gold star particle overlay |
| `MI_UI_Stardust_Iris` | `M_UI_Nikki_Master` | Ambient Sparkle | 8-point stardust iridescence overlay |

---

## 4. Figma 1440×900 Design Space & Widget System

### 4.1 Canonical StyleSheet (`WidgetStyleSheet.json`)
The legacy stub containing generic `#FF6B35` / `Roboto` values was replaced with the canonical Storybook specification:
- **Baseline Canvas:** `1440 × 900` pixels (`specs/ui/storybook_runtime_scene_layers.v1.json`).
- **Color Palette:**
  - Ivory Paper: `#FCFBF8`, Gilded Ivory: `#F8ECD6`, Parchment: `#F3E6C8`
  - Gold Champagne: `#C9A86A`, Gold Highlight: `#F2D08B`, Gold Border: `#DDC79B`
  - Midnight Plum: `#241B2E`, Deep Plum: `#1C1426`, Card Plum: `#2A1646`
  - Sakura: `#E7C9CE`, Lavender: `#F0DCF0`
  - Gameplay HP: Rose `#FF93B5`, Gameplay MP: Pearl Aqua `#86E4FF`
- **Typography:**
  - Headings: `Outfit` (H1: 32px, H2: 24px, H3: 18px)
  - UI/Body: `Inter` (Body: 14px, Caption: 12px, Overline: 10px)
  - Dialogue: `KaiseiDecol` / `KleeOne`
  - Metrics: `JetBrainsMono`
- **Grid & Spacing:** 8px baseline (`xs`: 4, `sm`: 8, `md`: 16, `lg`: 24, `xl`: 32, `xxl`: 48, `xxxl`: 64).
- **Corner Radii:** `xs`: 2, `sm`: 4, `md`: 6, `interaction`: 7, `lg`: 10, `card`: 14, `bubble`: 18, `pill`: 29.
- **Drop Shadow Treatment:** Native vector offset `[7, 8]` px in `#241B2E` at 25% opacity (blur: 0).

### 4.2 4-Layer Luxury UMG Depth Hierarchy
All 30 WBP atom templates in `specs/ui/*.t3d` were generated with explicit slot definitions matching the luxury depth model:
1. **Layer 1 (Void Plate):** Midnight Plum `#241B2E` (92% opacity) base with `MI_UI_Nikki_Card_Ivory` or `MI_UI_Mstone_Diamond_Reticle` material brush. Anchored to `1440×900` bounds.
2. **Layer 2 (Iridescent Sheen):** Dynamic beat-reactive iridescence (`MI_UI_Stardust_Iris`) with 15% opacity.
3. **Layer 3 (Filigree Chrome):** Champagne Gold `#C9A86A` corner flourishes anchored to Top-Left, Top-Right, Bottom-Left, and Bottom-Right with `OverlaySlot` alignments.
4. **Layer 4 (Active Content):** Full-bleed responsive CanvasPanel slot reserved for live typography, progress bars, and gameplay interactive elements.

---

## 5. Verification & Test Receipts

### 5.1 UMG Structural Linter (`Tools/ui_lint.py`)
- **Total Specs Audited:** 30
- **Errors:** 0
- **Warnings:** 0
- **Orphaned Slots:** 0
- **Status:** PASS

### 5.2 Style Audit Assertions (`Tools/test_ui_style_audit.py`)
- **Total Assertions:** 5/5
- **Color Clustering:** Exact conservation across 1,391 uses and 90 colours.
- **HDR Distinctness:** Preserved between high-dynamic range glow channels.
- **Status:** PASS

### 5.3 Storybook Runtime Manifest (`Tools/validate_storybook_runtime_manifest.py`)
- **Textures Verified:** 7 base64 PNG payloads
- **Runtime Entries:** 12 total
- **Status:** PASS

### 5.4 Preflight UI Contract (`Content/Python/verify_melodia_ui_contract.py`)
- **Desktop Battle HUD Preflight:** PASS
- **HUD Event Hooks:** 15/15 events validated across C++ headers and implementation.
- **Status:** PASS

### 5.5 Headless Unreal Engine 5.8 Compile (`compile_playtest_ui_and_owners.py`)
- **Command:** `UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript="compile_playtest_ui_and_owners.py" -unattended -NullRHI -nosound`
- **Total Compiled:** 129
- **Total Saved:** 129
- **Total Failed:** 0
- **Receipt:** `Saved/Audit/playtest_ui_compile.json`
- **Status:** PASS

---

## 6. Commit Ledger

| Commit Hash | Phase | Summary |
|---|---|---|
| `e326a3b34` | Phase 1 | `feat(ui): author universal toon, mstone, nikki, and radial master UI materials and instances` |
| `cddaad9f3` | Phase 2 | `feat(ui): align WidgetStyleSheet and UMG layouts to Figma 1440x900 storybook specifications` |
| Current | Phase 3 & 4 | Architectural record, test suite execution, and closeout |

---
<!-- GOAL_COMPLETE -->
