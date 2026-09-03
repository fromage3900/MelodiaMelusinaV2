# The Dream System — M_Master_Toon_Universal magic stack

Living, layerable "Infinity-Nikki dreamy magic" on the universal master. Every
effect is **switch/strength-gated default-OFF**, so all ~105 instances render
identically until an author opts in. All ride the emissive path and are scaled by
`GlobalEmissiveBoost` (MPC) so a whole level can dim the magic at once.

## Shipped effects (in emissive order)

| Group | Effect | Mechanism | Feel | Gate |
|-------|--------|-----------|------|------|
| 10b | Dream Rim | fresnel × IQ thin-film cosine palette | rainbow silhouette edge | `bDreamRim_Active` |
| 10c | Dream Bloom | luminance(base) smoothstep → pastel | soft highlight self-glow | `DreamBloomStrength` |
| 10d | Dream Flow | `dot(WorldPos,dir)·Scale + Time·Speed` → IQ cosine | living aurora drift | `DreamFlowStrength` |
| 10e | Dream Pulse | `×(1 + Amp·sin(Time·Speed))` on final emissive | whole surface breathing | `DreamPulseAmp` |
| 10f | Kaleidoscope Sigil | polar fold `abs(frac(ang/seg)-0.5)` + ring `sin(rad·Rings)` × IQ palette | rotating rainbow mandala rune | `SigilStrength` |
| 10g | Dawn Wash | `lerp(low,high, saturate(WorldZ·Scale+Bias))` | height-graded pastel dawn glow | `DawnStrength` |
| 10h | Dream Mist | flowing pseudo-curl sin-noise, animated | drifting swirling mist | `MistStrength` |
| 10i | Twinkle Glints | hash-placed star cells × per-cell time twinkle | sparkling star glints | `GlintStrength` |
| 10j | Dream Halo | `pow(saturate(dot(N,V)),Power)` × color | soft view-facing inner glow (fake-SSS) | `HaloStrength` |
| — | GlobalEmissiveBoost | MPC scalar multiply (terminal) | level-wide glow dimmer | MPC default 1.0 |

> **Celestial palette cohesion** (`bCelestialUsesDreamPalette`) was attempted but its wiring
> silently failed and the orphans were pruned — NOT currently present. Rebuild carefully
> (verify each connection) and **never run `delete_unused_expressions` after adding gated
> nodes** — it simplifies/strips default-OFF branches. Tints currently on `ConstellationRamp` (fine).

Kaleidoscope Sigil is the **procedural Fairy-Glyph** — a texture-free animated
rune folded from `SigilSides`/`SigilRings`/`SigilSpeed`/`SigilSharp`/`SigilCycles`.
UV-stamped (TextureCoordinate input pin only — Nanite-safe, no view globals).

IQ cosine palette (shared DNA): `0.5 + 0.5*cos(2π*(t*Cycles + float3(0,0.33,0.67)))`.

## Integration review — Fairy Glyph & Magical Transformation

Both pre-date the Dream stack but share its "glowing motif in a palette" DNA.
Recommended folds (not yet wired — each is a deliberate, gated step):

### Fairy Dust (grp 15) — `FairyGlyphMask`, `FairyMotifStyle/Intensity/Scale/Color/HighlightThreshold`, `bFairyDust_Active`
- **Palette unification (safe, high value):** replace the flat `FairyDustColor`
  multiply on the glyph output with the **Dream Flow spectral** (the animated IQ
  cosine), gated by a new `bFairyUsesDreamPalette`. Result: fairy glyphs shimmer
  through the same living rainbow as the rest of the dream stack instead of a
  static tint. Splice at the FairyDust color input; default switch OFF = current
  look. Low risk — FairyDust is already gated.
- **Glyph as Dream Flow mask:** feed `FairyGlyphMask` as a *spatial mask* on
  Dream Flow so the aurora only blooms through the rune shapes — "glowing sigils
  that breathe." One Multiply into DreamFlowStrength's path, gated.

### Magical / Henshin (grp 16) — `MagicalTransform` (0→1 wipe), `MotifMask/Scale/Color`, `TransformGlow`, `WipeSoftness`, `MagicalPalette`
- **DO NOT hard-gate** `MagicalTransform`: it fans to 5 consumers incl. Subtracts
  (zero-state math breaks if switched out) — confirmed prior trace. Feed it, don't
  fence it.
- **Dream Materialize (the headline fold):** drive `TransformGlow`'s edge color
  from the Dream Flow spectral so the henshin wipe edge becomes a *living rainbow
  materialize* — surfaces phase in on a shimmering spectral seam. The wipe already
  computes a soft edge band via `WipeSoftness`; multiply that band by the animated
  palette + `TransformGlow` and add to emissive. Gate `bDreamMaterialize`.
- **Pulse tie-in:** already automatic — `TransformGlow` output sits in emissive,
  so Dream Pulse breathes it for free once an author raises `DreamPulseAmp`.

## Nikki / anime-toon shader research → surreal-math backlog (ranked)

Techniques cross-referenced from Genshin/HSR/Nikki-class toon shading (ramp
lighting, matcap/fake-SSS, SDF face shadow, anisotropic hair glints, parallax
interiors, emission-mask motifs) adapted to environment art. Ranked by
wow ÷ risk, with the actual math so any can be built headlessly:

0. **ALREADY EXISTS — do NOT rebuild: `MF_SpaceParallax`** (grp 14 Celestial,
   `bCelestial_Active`). "Novel toon multi-depth space parallax: stars/galaxy/nebula
   at different depths parallax against each other by view direction; nebula depth
   toon-banded into shells; stars composite last." Uses `CameraVectorWS` +
   `PixelNormalWS` + `Time` + Custom, exposes per-layer Depth/Strength/Tint +
   `ToonSteps`. This IS the "galaxy inside the surface" effect — more advanced than
   a hand-rolled one. **The only work here is integration/use, not building:**
   (a) drive its `SpaceLow/NebulaTint/GalaxyTint/StarTint` from the shared dream
   palette so it shimmers cohesively; (b) tie `bCelestial_Active` ON for the
   crystal/night/pond instances that want it; (c) it already rides emissive → Dream
   Pulse breathes it for free. Verified 2026-07-04; prior "Dream Constellation
   Interior" backlog idea was a DUPLICATE and is deleted.
2. **Kaleidoscope Sigil (procedural mandala glyphs)** — polar fold UVs into radial
   symmetry: `ang = |frac(atan2(p.y,p.x)/seg)*seg - seg/2|`, `seg=2π/Sides`; rotate
   by `Time·Speed`; stamp rings/petals via `sin(rad·Rings)`. Animated glowing
   mandala — the *procedural* answer to Fairy Glyph (no texture). Palette from Dream
   Flow. Predictable-ish; tune Sides/Rings by eye.
3. **Curl-noise Dream Mist** — advect a soft emissive fog by a curl-noise field
   (`curl = ∂ψ/∂y, -∂ψ/∂x` of value-noise ψ) so mist swirls organically over the
   surface. Very dreamy, cheap; density unpredictable headless.
4. **Twinkle Star Glints (view-dependent)** — sharp anisotropic star-kernel
   speculars that catch as the camera moves: hash-placed points, `pow(NoH, huge)`
   shaped by a cross/star kernel, `Time` twinkle. Classic Nikki sparkle magic;
   needs view+editor tuning. Complements existing Sparkle.
5. **Dawn Wash (world-Z pastel gradient)** — cheapest: lerp two pastel tints by
   `saturate(WorldPos.z/Height + Bias)` → everything kissed by dream-dawn light.
   Fully predictable, near-zero cost; good "always-on subtle" default candidate.
6. **Dream Materialize** — henshin fold above (also a backlog item, listed there).

## Rules (same as the master overhaul)
Additive + gated default-OFF; splice at the emissive tail (never mid-BaseColor);
`save_asset(only_if_is_dirty=False)`; per-feature git commit; targeted
`get_expression_connections` only (never bulk `get_inputs` loops). Author verifies
motion/beauty in-editor — headless capture is unreliable for this master.
