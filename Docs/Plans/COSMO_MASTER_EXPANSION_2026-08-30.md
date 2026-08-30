# Cosmo Master Expansion — Nikki + Parallax — 2026-08-30

Source: `M_Cosmo_Master` is a 22KB stub (1 MF, 2 params) vs `M_Master_Toon_Cosmic` 559KB template (8 MFs, 80+ params). Expansion grafts Nikki + parallax from Cosmic/Nikki masters.

## Current (stub)

- `/Game/EnvSandbox/Materials/Masters/M_Cosmo_Master` — 22826 bytes
- `MF_MeshBlend_Activator_Index` only
- Params: `Roughness`, `UVScale` only
- Imports: `TP_Default` only

## Target (expanded Cosmo)

### 1) Material Functions to add (7)

From `M_Master_Toon_Cosmic` + `M_Master_Nikki`:

```
MF_SpaceParallax        — Celestial depth (Galaxy/Nebula/Star layers, Parallax)
MF_ParallaxCore         — Height→parallax, steps, shadow
MF_NikkiDreamGrade      — DreamTint, Iridescence, Sparkle
MF_NikkiPearlSheen      — Pearl highlight
MF_NikkiPastelGrade     — Pastel lift, Ramp Low/Mid/High/PosMid
MF_NikkiPetalShadow     — Soft pink petal shadow (pairs with ShadowDream)
MF_NikkiGlitterHalo     — Twinkle halo, scale/speed
```
Plus retain `MF_MeshBlend_Activator_Index` + add `MF_ColorRamp3`, `MF_DF_ContactBlend`, `MF_NormalAdjust` from Cosmic.

### 2) Params to add (organized)

**Celestial (from Cosmic):**
`CelestialGalaxyScale/Strength`, `CelestialNebulaScale/Strength`, `CelestialStarIntensity`, `ConstellationScale/Strength`, `GalaxyStrength/Tint`, `NebulaStrength/Tint`, `FairyDustIntensity/Scale`

**Parallax (from SpaceParallax/ParallaxCore):**
`ParallaxStrength` (0.0-1.0), `ParallaxScale`, `ParallaxHeight`, `ParallaxSteps` (8-32), `ParallaxShadowStrength`, `LayerA/B/C_ParallaxScale`, `LayerA/B/C_NormalStrength`

**Nikki (from M_Master_Nikki):**
`NikkiDreamGrade_Active` (bool), `NikkiPastelGrade_Active`, `NikkiPearlSheen_Active`, `NikkiGlitterHalo_Active`
`NikkiDreamWatercolor`, `NikkiPastelGrade`, `NikkiPastelStrength`, `NikkiPastelLift/PosMid/Ramp*`
`NikkiPearlSheen`, `NikkiPetalShadow` (soft pink #E8A0BF)
`NikkiGlitterHalo_Scale/Intensity/TwinkleSpeed`, `NikkiGlitterHalo_Color` (soft blue #8AA0D6)
`NikkiIrisTint`, `NikkiPastelBloom`

**ShadowDream (already on Universal, add to Cosmo):**
`ShadowDreamStrength` 0.55-0.75, `ShadowDreamTint` #8AA0D6, `ShadowFlowerColor` #E8A0BF, `ShadowFlowerStrength/Scale`

### 3) Wiring — graph order (follow Cosmic template)

```
BaseColor → MF_NikkiDreamGrade (DreamTint) → MF_NikkiPastelGrade → MF_SpaceParallax (celestial overlay) → MF_NikkiPearlSheen → Final
Normal    → MF_ParallaxCore (height→parallax) → MF_NormalAdjust → Final
Roughness → lerp per-layer (LayerA/B/C) with ParallaxSteps
Emissive  → MF_NikkiGlitterHalo (twinkle) + Galaxy/Nebula emit
WPO       → MF_NikkiSquishWPO (optional, low strength)
```

Follow `M_Master_Toon_Cosmic` node positions (export via `monolith blueprint_query get_graph_data` when live) — copy node clusters, don't rebuild from scratch.

### 4) Implementation — steps (editor required)

1. Ensure `M_Master_Toon_Cosmic` is healthy (saved, compiled). Export graph baseline: `bp_regression_checker` fingerprint.
2. Run `Content/Python/expand_cosmo_master.py --dry` — validates all MF assets exist, prints param blocks.
3. Run `expand_cosmo_master.py --inject` — T3D inject via Monolith: creates MF nodes, wires per §3, sets defaults:
   - `ParallaxStrength 0.45`, `ParallaxScale 1.2`, `ParallaxSteps 16`
   - `NikkiDreamGrade_Active true`, `NikkiPastelGrade_Active true`, `NikkiGlitterHalo_Active false` (opt-in)
   - `ShadowDreamTint #8AA0D6`, `ShadowFlowerColor #E8A0BF`
4. Compile (`monolith material list-compile`) — expect 0 errors, Substrate inputs validated.
5. Create verification MI: `MI_Cosmo_NikkiParallax_Verify` at `Instances/Cosmo/` — toggle each Nikki/parallax bool and screenshot.
6. Ledger: `Saved/Audit/cosmo_expansion_2026-08-30.json`

### 5) Verification

- `monolith monolith_discover` — confirm new MFs appear in graph
- `Saved/Audit/cosmo_expansion_2026-08-30.json` has `compiled: true`
- Visual: Nebula scroll + parallax on preview mesh, pastel grade washes blue/pink, no compile errors

### 6) Out of scope tonight (deferred)

- Fabric integration into Cosmo (separate Fabric Deep Focus — uses `M_Universal_Enhanced_Fabric`, not Cosmo)
- Full fabric instance pass (see next task)

---
Ready for `Content/Python/expand_cosmo_master.py` (dry/inj) — stub → 559KB parity.
