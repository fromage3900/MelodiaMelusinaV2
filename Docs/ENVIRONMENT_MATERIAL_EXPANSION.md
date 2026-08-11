# Environment Material Expansion — Complete Roadmap

## Phase A: Gradient Tint Rock (Genshin-Style) — 1 session

**Status: Parameters created, wiring diagram provided**
- 6 params added to landscape master: `GTR_LowColor/MidColor/HighColor`, `GTR_LowAltitude/HighAltitude`, `GTR_Strength`
- Uses existing `MF_ColorRamp3` (3-stop ramp) + `MF_LandscapeDistanceBands`
- Wire: WorldPosition.Z → normalize by altitude → MF_ColorRamp3 blend → lerp(rock_color, gradient, GTR_Strength)

## Phase B: Unified Weathering MF — 1 session

Create `MF_EnvironmentalWeathering` combining:
- Slope mask (snow/moss placement)
- Height mask (snow altitude)
- Curvature (edge wear via `MF_CurvatureOrnament`)
- Noise breakup (world-aligned)
- Output: single blend factor → drives moss/snow/erosion

## Phase C: Detail Normal Wiring — 1 session

- Wire the 28 unwired DetailNormal samplers in universal master
- Use BlendAngleCorrectedNormals for proper detail blending
- Add world-aligned tiling option (reuse triplanar UVs)

## Phase D: Gemstone/Crystal Stack — 2 sessions

| Layer | Technique | Source |
|---|---|---|
| IOR-based F0 | `F0 = ((IOR-1)/(IOR+1))^2` | Schlick approx |
| Chromatic dispersion rim | `float3(r*r,g*g,b*b) = saturate(Rim+Disp)` | DREAM_HLSL_SNIPPETS.md #4 |
| Rainbow sparkle / glint | IQ cosine palette + sparkle system | Already exists |
| Facet parallax (POM) | BlingVol3 height maps → MF_ParallaxCore | Textures exist |
| 12 IOR presets | Diamond 2.42, Sapphire 1.77, Emerald 1.57, etc. | Researched |

**Parameters created:** 19 new params in `06 | Gemstone` group (gated by `bGemstone_Active` static switch)

## Phase E: FabricType System — 2 sessions

| FabricType | Aniso | Roughness | Sheen | Weave |
|---|---|---|---|---|
| 0 Default | 0.0 | 0.70 | 6.0 | None |
| 1 Cotton/Linen | 0.0 | 0.85 | 4.0 | 32 |
| 2 Silk | **0.6** | 0.35 | 8.0 | None |
| 3 Satin | **0.4** | 0.42 | 7.0 | 64 |
| 4 Velvet | **-0.3** | 0.92 | 3.0 | 24 |
| 5 Wool | 0.0 | 0.88 | 2.0 | 48 |
| 6 Chiffon | 0.0 | 0.55 | 5.0 | None |
| 7 Sequins | **0.5** | 0.25 | 9.0 | None |

Uses existing `style_peak()` weighting pattern (like FairyMotifStyle, ElementType). Wires to BSDF Anisotropy + Tangent pins.

## Phase F: Triplanar Single-Calc — 2 sessions

Replace 18 separate WAT/WAN calls with one Custom HLSL computing triplanar UVs. Target: ~80 instructions instead of ~2000. Add `bTriplanar_Active` gate.

## Phase G: Dream Compositor + Face SDF — 2 sessions

- Unify 10 dream toggles into one composited layer
- SDF face shading for character materials

## Total: ~11 sessions, ~30-35 hours

### Immediate Next Steps (In Editor)
1. Open landscape master → wire MF_ColorRamp3 to GTR params
2. Wire the 6 GTR params into the slope/cliff rock lane
3. Test on L_FallenMoon cliffs at different altitudes
