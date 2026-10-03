# Studio Ghibli, Musical Intonation, Scrollwork & PBR VFX Library

An expanded suite of **21 high-quality VFX textures & PBR utility maps** designed for **Unreal Engine 5 Substrate Shaders**, **Niagara Emitters**, **Decals**, **Custom Material Panners**, and **Magic Emitters**.

> [!NOTE]
> All textures are stored directly inside your UE project at:
> `C:\EnvironmentPortfolio\BS_GodFile\Content\Alphas_Sparkles\`

---

## 🍃 Studio Ghibli Aesthetic Alphas

- **`T_Alpha_Ghibli_WindSwirl.png`**: Soft logarithmic Ghibli wind swirl / cloud curl with trailing anime starburst glints.
- **`T_Alpha_Ghibli_MeadowSigil.png`**: Magical meadow floral sigil featuring 12-fold petal rings and central anime star dust core.

---

## 🎼 Musical Intonation & Baroque Scrollwork Runes

- **`T_Alpha_Rune_MusicalClefScroll.png`**: Treble Clef concentric magic circle with baroque acanthus scrollwork filigree and musical notes.
- **`T_Alpha_Rune_HarmonicStaff.png`**: 5 concentric musical staff lines with quarter/eighth notes, clefs, and harmonic acoustic sine waves.
- **`T_Alpha_Rune_BaroqueFiligree.png`**: Victorian/Baroque acanthus leaf scrollwork crest for spell casting ground decals.

---

## 🌊 Creative PBR Utility & Motion Maps

### 1. RG Water Vortex Flow Map (`T_FlowMap_WaterVortex_RGA.png`)
- **Red Channel ($V_x$)**: Velocity X vector offset (128 = 0 velocity).
- **Green Channel ($V_y$)**: Velocity Y vector offset (128 = 0 velocity).
- **Alpha Channel**: Radial falloff mask.
- **UE Usage**: Plug into a `CustomExpression` or `FlowMap` panner node in Unreal Engine to animate liquid splashes, magic vortexes, or swirling spell rings seamlessly without heavy geometry!

### 2. Tangent Space Normal Map (`T_Normal_RuneRelief_N.png`)
- **Red ($X$) / Green ($Y$) / Blue ($Z$)**: Tangent space surface normals computed from Sobel height gradients.
- **UE Usage**: Connect to the **Normal** input of your Material to create realistic chiseled stone relief and 3D lighting bevels on flat ground decals or wall runes!

### 3. Packed PBR Texture (`T_Packed_Rune_PBR.png`)
- **Red (R)**: Base Rune Mask (Stencil Opacity).
- **Green (G)**: Soft Inner Glow (Emissive Core).
- **Blue (B)**: Micro-Roughness / Surface Imperfection Noise.
- **Alpha (A)**: Smooth Radial Distance Fade.
- **UE Usage**: Single-texture memory optimization! Drive Opacity, Emissive Glow, and Roughness simultaneously using one single texture sampler.

---

## 📦 Complete UE Asset Inventory (21 Textures)

| Asset Name | Asset Type | UE Path | Shader / VFX Use Case |
| :--- | :--- | :--- | :--- |
| `T_Alpha_Ghibli_WindSwirl.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Ghibli wind gusts, floating petal trails |
| `T_Alpha_Ghibli_MeadowSigil.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Nature spell circles, meadow grass runes |
| `T_Alpha_Rune_MusicalClefScroll.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Musical spell casting rings, bardic magic |
| `T_Alpha_Rune_HarmonicStaff.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Acoustic pulse shockwaves, harmonic barriers |
| `T_Alpha_Rune_BaroqueFiligree.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Baroque ground decals, ornate magic crests |
| `T_FlowMap_WaterVortex_RGA.png` | **RG Flow Map** | `Content/Alphas_Sparkles/` | Animated liquid vortexes, swirling caustics |
| `T_Normal_RuneRelief_N.png` | **Normal Map** | `Content/Alphas_Sparkles/` | Chiseled 3D rune relief & lighting bevels |
| `T_Packed_Rune_PBR.png` | **Packed PBR** | `Content/Alphas_Sparkles/` | Optimized Mask + Emissive Core + Roughness |
| `T_Alpha_water_globule_cluster_alpha.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Viscous liquid droplets, fluid metaballs |
| `T_Alpha_fluid_impact_ripple_alpha.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Water surface ripple shockwaves |
| `T_Alpha_water_splash_burst_alpha.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Dynamic water splash crowns |
| `T_Alpha_water_globule_flipbook.png` | **4x4 Flipbook** | `Content/Alphas_Sparkles/` | Animated liquid droplet splash sequence |
| `T_Alpha_sparkle_pulse_flipbook.png` | **4x4 Flipbook** | `Content/Alphas_Sparkles/` | Animated starburst ignition & twinkling |
| `T_Alpha_sparkle_4point_alpha.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Lens glints, anime eye sparkles |
| `T_Alpha_sparkle_cluster_alpha.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Ambient magic dust, potion bubbles |
| `T_Alpha_diamond_glint_alpha.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Critical hit glints, wish energy |
| `T_Alpha_arcane_rune_alpha.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Spell casting circles, ground decals |
| `T_Alpha_elder_glyph_alpha.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Ancient stone carvings, power runes |
| `T_Alpha_celestial_sigil_alpha.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Solar/Lunar spell circles, celestial rings |
| `T_Alpha_sacred_matrix_alpha.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Crystalline barriers, shield matrices |
| `T_Alpha_elemental_crest_alpha.png` | Alpha Mask | `Content/Alphas_Sparkles/` | Fire/Wind impact rings, hero emblems |

---

## ⚙️ How to Setup Flow Maps in UE Material Editor

> [!TIP]
> **UE Flow Map Shader Math:**
> 1. Sample `T_FlowMap_WaterVortex_RGA.png`.
> 2. Multiply Red and Green channels by `2.0` and subtract `1.0` to decode velocity vector: $\vec{V} = (R \times 2 - 1, G \times 2 - 1)$.
> 3. Multiply $\vec{V}$ by `Time * Speed` and add to UV coordinates: $UV_{\text{flow}} = UV + (\vec{V} \times \text{Time})$.
> 4. Sample your diffuse or noise texture using $UV_{\text{flow}}$ to create continuous swirling liquid motion!
