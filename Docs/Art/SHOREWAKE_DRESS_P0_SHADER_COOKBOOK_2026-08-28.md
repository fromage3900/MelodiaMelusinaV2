# Shorewake Dress — P0 Shader Cookbook

**Date:** 2026-08-28  
**Audience:** Brennan + Claude/editor agents  
**Engine:** Unreal Engine 5.8  
**Status:** executable look-dev specification  
**Scope:** Sea Above P0 / Shorelistener + Wakebound material family

> **Naming note:** “Shorewake” is the shader/look-dev family in this document. It does **not** force a canon outfit rename. The first unlockable can remain **Shorelistener**, while **Wakebound Survey Set** remains the traversal field variant.

---

# 1. Art target

The dress should feel like **hand-painted cloth that has learned one impossible fact about water**.

It is not a wet dress shader, not holographic sci-fi fabric, not a generic anime iridescent material, and not a miniature copy of the ocean shader.

The read order must be:

1. **recognizable Melusina silhouette** — puff sleeves, fitted ornamental bodice, skirt/apron language, small star hat;
2. **quiet painterly textile** — lavender / pearl / blush / cyan, broad brush value design;
3. **one impossible hem** — translucent asymmetric Shorelistener Hem behaving slightly against gravity;
4. **Second Horizon clasp / tide line** — one concentrated jewel/detail anchor;
5. **diegetic attunement** — material response grows as Melusina nears a Tide Seam;
6. **rhythm accent** — felt more than noticed.

For the first outfit, reduce decorative geometry roughly **35–45%** relative to later legendary looks. Let the material and motion carry the wonder.

---

# 2. Do-not-touch list

Before changing anything, inspect existing assets and names in the project.

**Do not:**

- duplicate the production water master onto clothing;
- modify `/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Substrate`;
- use SceneDepth in an opaque Single Layer Water path;
- turn the false Sea Above presentation plane into gameplay water;
- create new C++ for this look-dev pass;
- put every animation value in a global Material Parameter Collection;
- make the entire dress translucent;
- use expensive real-time refraction as the core “magic” read;
- let rhythm pulses flash the costume like a music visualizer;
- build a generic fashion shader framework before the hero outfit works.

Existing project seams to respect:

```text
Rhythm subsystem:
    UMelodiaRhythmReactivitySubsystem

Canonical shared rhythm/material bus:
    MPC_Melodia_Palette

Production water master:
    /Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade
```

The garment should **reference the same world**, not share the same master material.

---

# 3. Recommended asset family

Create a small, explicit family:

```text
/Game/Melodia/Characters/Melusina/Materials/Shorewake/
│
├─ M_Shorewake_Fabric_Master
├─ M_Shorewake_TranslucentHem_Master
├─ M_Shorewake_SeaGlass_Master
│
├─ MF_Shorewake_TideGradient
├─ MF_Shorewake_PainterlyBreakup
├─ MF_Shorewake_TideSeamAttunement
├─ MF_Shorewake_RhythmAccent
├─ MF_Shorewake_HemWPO
└─ MF_Shorewake_SeaGlass

Instances/
├─ MI_Shorewake_Bodice
├─ MI_Shorewake_Sleeves
├─ MI_Shorewake_Skirt
├─ MI_Shorewake_Apron
├─ MI_Shorewake_Hem
└─ MI_Shorewake_SecondHorizonClasp
```

If the existing character material folders use another convention, follow the repository convention rather than creating a competing hierarchy.

---

# 4. Mesh preparation — fastest route to a beautiful shader

The shader will only read if the mesh gives it stable masks.

## Required vertex color contract

Use vertex colors where possible so Claude/editor agents do not need a new mask texture for every experiment.

```text
VertexColor.R = Hem influence / WPO amplitude
VertexColor.G = Tide embroidery / magic reveal mask
VertexColor.B = Edge / painted highlight support
VertexColor.A = Material-specific spare mask
```

Suggested values:

```text
Bodice:         R 0.00–0.08
Sleeve edge:    R 0.10–0.20
Upper skirt:    R 0.05–0.15
Lower skirt:    R 0.25–0.60
Magic hem:      R 0.70–1.00
```

The bodice must remain stable. The lower hem gets the motion.

## UV expectation

- **UV0:** normal authored garment textures / painted trim
- **UV1 optional:** relaxed gradient-friendly layout
- World/object position may be used for broad gradients, but do not rely on world-space detail for the fine textile weave — it will look like projection mapping.

## Separate material section

The translucent asymmetric hem should be a **separate mesh section/material slot**. This single decision prevents the entire dress from paying translucency cost and preserves silhouette readability.

---

# 5. Master A — `M_Shorewake_Fabric_Master`

## Surface strategy

Use an **Opaque** or **Masked** garment material. Prefer the project's stable Substrate workflow if character materials already use it; otherwise use the existing character shading model rather than migrating the character during P0.

The target is soft cloth with painted value control, not physically perfect textile simulation.

### Parameter groups

#### Color

```text
DeepLavender      = (approx) #5F5184
FoamPearl         = (approx) #E9E3EE
HorizonCyan       = (approx) #8FD9DF
BlushPink         = (approx) #D9A0BF
SeaGlassTint      = (approx) #A9E7E4
ShadowTint        = cooler desaturated lavender
```

Treat these only as starting swatches. Match the actual character under the Sea Above lighting before locking values.

#### Painterly

```text
BrushScale                0.5–8
BrushStrength             0–1
FiberScale                1–30
FiberStrength             0–0.25
ValuePosterizeStrength    0–1
EdgeHighlightStrength     0–1
CavityTintStrength        0–1
RoughnessBreakup          0–0.3
```

#### Tide

```text
TideDirectionWS           Vector3
TideScale                 0.0005–0.02 depending world units
TidePhase                 0–1
TideBandWidth             0.02–0.5
TideBandSoftness          0.01–0.5
TideColorAmount           0–1
TideGlow                  0–5
SeamProximity             0–1  // local MID preferred
SeamDirectionWS           Vector3
```

#### Motion

```text
HemFloatStrength          0–5 cm visual starting range
HemCurlStrength           0–1
HemNoiseScale             0.001–0.1
HemNoiseSpeed             0–2
UpwardBias                0–1
PulseDisplacement         0–2 cm
WindInfluence             0–1
```

#### Rhythm

```text
BeatInfluence             0–0.15
CrescendoInfluence        0–0.10
DreamRippleInfluence      0–0.20
WarmthInfluence           0–0.10
```

Keep all defaults subtle.

---

# 6. Material Function — `MF_Shorewake_TideGradient`

This is the broad “the dress remembers the horizon” color structure.

## Goal

A slow, wide color transition should run across the garment as though a waterline exists in a coordinate system slightly misaligned with gravity.

## Node math

Use **Absolute World Position**, but transform or stabilize it relative to the character if swimming/teleporting causes visible swimming. For a first pass:

```text
P = AbsoluteWorldPosition
D = normalize(TideDirectionWS)
Projected = dot(P, D)
Phase = Projected * TideScale + TidePhase
```

For a single broad wave:

```text
Wave01 = sin(Phase * 2π) * 0.5 + 0.5
BroadBand = SmoothStep(Low, High, Wave01)
```

For a crisp central horizon stripe:

```text
Centered = abs(frac(Phase) - 0.5)
HorizonLine = 1 - smoothstep(TideBandWidth,
                             TideBandWidth + TideBandSoftness,
                             Centered)
```

If `frac` creates ugly discontinuities across the dress, do not force repetition. Use a non-repeating linear projected band:

```text
DistanceFromLine = abs(Projected - TideLinePosition)
HorizonLine = 1 - smoothstep(Width, Width + Softness, DistanceFromLine)
```

This non-repeating version is often more elegant for a hero costume.

## Output

Return:

```text
BroadGradient
HorizonLine
ProjectedCoordinate
```

Use **BroadGradient** to blend `DeepLavender → FoamPearl/HorizonCyan`. Use **HorizonLine** as a narrow emission/embroidered response, but multiply it by the authored garment mask (`VertexColor.G` or texture mask) so the stripe does not magically draw across every surface.

---

# 7. Material Function — `MF_Shorewake_PainterlyBreakup`

## Goal

Break the clean CG smoothness without turning cloth into noisy grunge.

Use **large shapes first, tiny fiber second**.

### Layer A — broad brush-value breakup

Inputs:

```text
ObjectPosition or local-position projection
Low-frequency noise / existing painterly texture
BrushScale
BrushStrength
```

Pseudo-math:

```text
BrushNoise = SamplePainterlyNoise(LocalUV * BrushScale)
BrushValue = lerp(1.0, remap(BrushNoise, 0.85, 1.15), BrushStrength)
BaseColor *= BrushValue
```

Keep contrast tiny. You want hand-painted variation, not camouflage.

### Layer B — directional fiber

Use a small tiled textile normal or procedural directional pattern in tangent UV space.

```text
Fiber = Texture(UV0 * FiberScale)
Roughness += (Fiber - 0.5) * FiberStrength
Normal = BlendAngleCorrectedNormals(BaseNormal, FiberNormal * FiberNormalStrength)
```

Do not make the fiber visibly repeat at gameplay camera distance.

### Layer C — authored edge accent

Use `VertexColor.B`, curvature/cavity texture if already baked, or a simple mask authored from Substance.

```text
PaintedEdge = VertexColor.B * EdgeHighlightStrength
BaseColor = lerp(BaseColor, FoamPearl, PaintedEdge * 0.15)
Roughness = lerp(Roughness, Roughness * 0.9, PaintedEdge)
```

The highlight should look painted into the style, not like a procedural worn metal edge.

---

# 8. Material Function — `MF_Shorewake_TideSeamAttunement`

This is the outfit's actual gameplay storytelling function.

## Runtime contract

`SeamProximity` should be supplied **locally** through the dress's Dynamic Material Instance unless many systems genuinely need the same value.

Suggested semantic range:

```text
0.00  no seam nearby
0.20  far — barely perceptible
0.45  near enough for horizon embroidery alignment
0.70  strong directional float / shimmer
0.90  upward droplet behavior
1.00  directly at active Tide Seam
```

Also pass `SeamDirectionWS` as a vector when the seam has a meaningful current/up direction.

## Curves

Do not use raw proximity directly for every effect.

```text
FarResponse    = smoothstep(0.15, 0.40, SeamProximity)
NearResponse   = smoothstep(0.40, 0.72, SeamProximity)
CloseResponse  = smoothstep(0.70, 0.92, SeamProximity)
SeamResponse   = smoothstep(0.90, 1.00, SeamProximity)
```

Return all four masks. They stage the reveal.

---

# 9. The five-stage diegetic response

The costume should teach the mechanic without UI text.

## Stage 1 — far: hem contradicts gravity

At `FarResponse > 0`:

- asymmetric hem raises by only a few millimeters to centimeters;
- motion direction biases toward `SeamDirectionWS`;
- no bright emission yet.

The player should wonder whether they imagined it.

## Stage 2 — nearer: tide embroidery aligns

At `NearResponse`:

- narrow `HorizonLine` becomes more coherent;
- painterly cyan/pearl color shift increases;
- emission remains around the threshold of visibility.

```text
HorizonEmission = HorizonLine
                * VertexColor.G
                * NearResponse
                * TideGlow
```

## Stage 3 — near: hair and fabric agree

The garment shader increases directional WPO and the character hair system should receive the same seam direction/proximity via its own MID or existing character response system.

Do not force hair behavior into this master material. The important storytelling beat is **two different materials agreeing on the impossible direction**.

## Stage 4 — very near: droplets crawl upward

At `CloseResponse`:

- use a masked/transparent animated droplet pattern on the **separate translucent hem**;
- scroll it opposite gravity / along seam direction;
- keep droplets sparse and elongated.

The droplets should feel like the dress is remembering rain in reverse.

## Stage 5 — seam: second reflection / pearlescent displacement

At `SeamResponse`:

- reveal a subtle second highlight band offset from the real specular response;
- increase thin Fresnel pearl/cyan response;
- add a tiny pulse to the horizon line.

Avoid literal screen-space mirror reflection unless the existing character rendering already supports it cheaply. A painted “false reflection” is more controllable and more in style.

---

# 10. Material Function — `MF_Shorewake_HemWPO`

## Principle

**Physics owns silhouette motion. Shader WPO owns impossible micro-motion.**

If cloth simulation exists, do not compete with it.

### Inputs

```text
WorldPosition
ObjectPosition
VertexNormalWS
VertexColor.R   // HemMask
Time
SeamProximity
SeamDirectionWS
HemFloatStrength
HemCurlStrength
HemNoiseScale
HemNoiseSpeed
UpwardBias
Pulse
```

### Base micro-wave

```text
LocalP = WorldPosition - ObjectPosition
PhaseA = dot(LocalP, float3(0.73, 0.31, 0.19)) * HemNoiseScale + Time * HemNoiseSpeed
PhaseB = dot(LocalP, float3(-0.21, 0.91, 0.37)) * HemNoiseScale * 0.73 - Time * HemNoiseSpeed * 0.61
Noise = sin(PhaseA) * 0.65 + sin(PhaseB) * 0.35
```

### Normal flutter

```text
NormalOffset = VertexNormalWS
             * Noise
             * HemFloatStrength
             * HemMask
```

### Impossible upward / seam pull

```text
SeamDir = normalize(SeamDirectionWS)
DirectionalOffset = SeamDir
                  * HemFloatStrength
                  * UpwardBias
                  * FarResponse
                  * HemMask
```

If the seam direction is unavailable, use a designer-controlled world direction rather than assuming `+Z` is always the narrative “up.”

### Curl near edge

Use hem mask power to focus motion on the very edge:

```text
EdgeMask = pow(saturate(HemMask), 3)
CurlOffset = VertexNormalWS
           * sin(PhaseA * 0.5 + Time)
           * HemCurlStrength
           * EdgeMask
           * NearResponse
```

### Rhythm pulse

```text
PulseOffset = VertexNormalWS
            * Pulse
            * PulseDisplacement
            * EdgeMask
```

### Final

```text
WorldPositionOffset = NormalOffset
                    + DirectionalOffset
                    + CurlOffset
                    + PulseOffset
```

Clamp the final magnitude. Start tiny. The magical read should come from coordinated cues, not a skirt exploding through the character.

---

# 11. Master B — `M_Shorewake_TranslucentHem_Master`

## Scope

Only the asymmetric Shorelistener hem / chiffon-water-glass panel uses this material.

### Blend mode

Test in this order:

1. **Translucent / Thin Translucent** if stable with the current character pipeline;
2. fallback to **Masked + dithered transparency** if sorting/performance becomes ugly;
3. avoid converting the whole costume to translucency.

### Base opacity

Target readability before realism:

```text
BaseOpacity ~ 0.30–0.65
Opacity = BaseOpacity
        * HemTextureMask
        * ViewSupport
```

Do not let it disappear over bright ocean highlights.

### Fresnel

```text
F = Fresnel(Exponent ~ 3–6)
Rim = smoothstep(RimLow, RimHigh, F)
```

Color the rim `FoamPearl → HorizonCyan` and modulate by painterly noise.

### Fake internal depth

Instead of costly refraction:

```text
LayerA = noise(UV + Time * slowVector)
LayerB = noise(UV * 1.7 - Time * slowerVector)
Internal = saturate(LayerA * 0.6 + LayerB * 0.4)
BaseColor += Internal * SeaGlassTint * 0.05–0.15
```

### Upward droplet mask

Use a sparse grayscale droplet/vein texture or procedural Voronoi-like pattern if one already exists.

```text
ScrollUV.y = UV.y + Time * DropletSpeed * -1
Droplets = Texture(DropletMask, ScrollUV)
Droplets = smoothstep(0.75, 0.95, Droplets)
Droplets *= CloseResponse
```

Then:

```text
Emissive += Droplets * HorizonCyan * 0.2–0.8
Opacity   += Droplets * 0.1
```

Make the upward direction configurable. A seam may pull sideways or “up” toward the Sea Above.

### Depth Fade

Depth Fade is acceptable **only** on this translucent section if it improves intersections and is stable. Do not use it as a gimmick. Keep the distance short.

---

# 12. Master C — `M_Shorewake_SeaGlass_Master`

Use for the **Second Horizon clasp**, small beads, or one hero ornament.

The clasp is the highest-frequency detail on the simple first outfit.

## Look

- pearl ceramic / sea glass / watery crystal;
- cyan-lavender internal color;
- a thin horizontal “second horizon” trapped inside;
- mostly opaque silhouette with luminous depth, not invisible glass.

### Node recipe

```text
Fresnel = Fresnel(4–7)
InternalNoise = low-frequency animated noise
Horizon = MF_Shorewake_TideGradient(...).HorizonLine

BaseColor = lerp(DeepLavender, SeaGlassTint, InternalNoise * 0.35)
BaseColor += FoamPearl * Fresnel * 0.2
Emissive = Horizon * HorizonCyan * ClaspGlow * Attunement
Roughness = 0.18–0.35 with subtle breakup
```

If using translucency, keep it limited to the clasp and avoid high refraction. An opaque material with Fresnel + emissive depth usually reads better at gameplay size.

---

# 13. Rhythm — `MF_Shorewake_RhythmAccent`

The outfit is an instrument for perceiving the world, not an equalizer.

Read from the project's actual shared rhythm path (`MPC_Melodia_Palette` and/or values pushed from `UMelodiaRhythmReactivitySubsystem`). Inspect names before connecting.

A safe look-dev composition:

```text
Accent = BeatPulse            * 0.10
       + CommandPulse         * 0.08
       + CrescendoNormalized  * 0.06
       + TensionSustain       * 0.05
```

For the dress itself, simplify further if possible:

```text
ClothPulse = BeatPulse * BeatInfluence
           + CrescendoNormalized * CrescendoInfluence
           + DreamRipple * DreamRippleInfluence
```

Use the result for:

- **2–6%** color-value lift in the tide embroidery;
- sub-centimeter hem pulse;
- a tiny clasp glow bloom;
- slight pearl shift during `DreamRipple`.

Do **not** drive base opacity, full dress emission, or large WPO from raw beats.

### Saturation / clamp

```text
Accent = saturate(Accent)
SoftAccent = Accent * Accent * (3 - 2 * Accent) // smoothstep curve
```

This keeps the response graceful.

---

# 14. Painterly lighting cheat — use with restraint

If the existing character master supports artist-controlled shadow/highlight ramps, stay inside that system.

If not, a light-touch facing response can reinforce painted planes:

```text
Facing = saturate(dot(PixelNormalWS, CameraVectorWS))
Edge = 1 - Facing
PaintedLift = pow(Edge, 3) * 0.03–0.08
```

Multiply by an authored mask so only selected folds/edges receive it.

Do **not** build a full fake toon lighting model tonight. Sea Above should still integrate Melusina into Lumen/world lighting.

---

# 15. Runtime Blueprint handoff

Create or reuse one small outfit presentation component/Blueprint responsible for MIDs.

Pseudo-contract:

```text
On Outfit Equipped:
    Create/cache MIDs for fabric, hem, clasp

On Tide Seam state change:
    SetScalarParameterValue("SeamProximity", value)
    SetVectorParameterValue("SeamDirectionWS", direction)

On rhythm signal update / tick at reasonable cadence:
    set only required local accent values if not sourced from MPC
```

Do not call `CreateDynamicMaterialInstance` every frame.

### Smoothing

Gameplay proximity may jump. Material response must not.

```text
SmoothedSeam = FInterpTo(SmoothedSeam,
                         TargetSeam,
                         DeltaSeconds,
                         2.5–5.0)
```

Direction can use vector interpolation / normalized lerp.

### Event priority

```text
Outfit equipped
→ cache MIDs
→ subscribe to nearest authored Tide Seam / exploration state
→ update proximity/direction
→ optional rhythm accents
```

Do not scan the world for all seams every frame from the material controller. Let the exploration system tell the outfit what matters.

---

# 16. P0 “beauty first” defaults

These are starting values, not canon numbers.

```text
Fabric Roughness             0.62
Fabric Specular              modest
BrushStrength                0.16
FiberStrength                0.06
EdgeHighlightStrength        0.20

TideColorAmount              0.32
TideGlow                     0.15 normal / 0.45 near seam

Hem BaseOpacity              0.46
Hem Fresnel Exponent         4.5
HemFloatStrength             1.5 cm-equivalent visual target
UpwardBias                   0.25 far / 0.70 very near
PulseDisplacement            0.25–0.6 cm

Clasp Roughness              0.24
ClaspGlow                    0.20 normal / 0.75 active seam

BeatInfluence                0.06
CrescendoInfluence           0.04
DreamRippleInfluence         0.08
```

If any effect looks impressive while standing still in the material editor, it is probably too strong. Judge it in the Sea Above level, at gameplay camera distance, in motion.

---

# 17. P0 hero-shot tuning

The shader needs to support the Sea Above reveal, not compete with it.

## Shot A — shoreline serenity

- dress reads mostly matte and painterly;
- hem transparency visible against dark rocks, not glowing;
- clasp is a tiny cool highlight;
- no obvious “quest item” pulsing.

## Shot B — first second-horizon glimpse

- the actual world horizon and dress tide line accidentally align for a second;
- hem drifts in the wrong direction by a small amount;
- hair tips can echo the direction;
- player notices coherence before they understand it.

## Shot C — Tide Seam proximity

- horizon embroidery gains coherence;
- thin pearlescent rim appears on hem;
- sparse droplets crawl upward;
- no UI required to say “you are close.”

## Shot D — Bell pulse

- Bell remains the largest visual event;
- dress responds one beat **after or with** the world pulse, at low intensity;
- clasp catches a second tiny horizon;
- do not turn Melusina into a lantern.

## Shot E — aftermath

- most glow falls away;
- one residual droplet continues upward after the world appears calm;
- this is a cheap, beautiful lingering proof that the impossible rule persists.

---

# 18. Sea Above visual coordination

P0 emotional structure:

```text
serenity
→ anomaly
→ impossible space
→ biological realization
→ short aftermath
```

The dress should mirror that structure:

```text
cloth
→ odd hem motion
→ aligned second-horizon line
→ liquid/biological response
→ quiet residue
```

This is stronger than giving the outfit five constant magic effects.

### P0 world layer reminder

```text
sky / atmosphere
→ real ocean (gameplay water)
→ fog / depth gap
→ false ocean presentation plane
→ Bell membrane
→ optional under-sky cards
```

The false ocean remains presentation-only. The dress should react to authored Tide Seam / Sea Above state, **not** by registering the false ocean as a Water Body.

---

# 19. Shader compile / performance checklist

For each master:

- [ ] compile with no warnings relevant to the chosen blend/shading path
- [ ] record shader instruction count before/after major feature additions
- [ ] record sampler count
- [ ] test skeletal animation extremes
- [ ] test cloth simulation if enabled
- [ ] test Lumen daylight and night/blue hour
- [ ] test over bright Oceanology highlights
- [ ] test against fog
- [ ] test at 3 camera distances
- [ ] verify WPO does not pull vertices through legs/body
- [ ] verify translucent section sorting with hair
- [ ] verify no per-frame MID creation
- [ ] verify rhythm signals are smoothed/clamped
- [ ] verify seam response still reads with rhythm disabled

## Lite switch

Add static or scalar switches so a fallback material instance can disable:

```text
AnimatedDroplets
SecondaryHemNoise
ClaspInternalAnimation
ExtraEmission
```

The outfit must retain its color hierarchy and horizon motif even in the Lite state.

---

# 20. Claude execution plan — build in tiny batches

## Batch 1 — cloth identity

**Goal:** beautiful still frame before magic.

1. inspect existing Melusina material setup;
2. create `M_Shorewake_Fabric_Master` or derive from the existing stable character master if that is clearly safer;
3. expose palette + roughness + painterly breakup;
4. wire vertex-color masks;
5. create bodice/skirt/sleeve instances;
6. compile and screenshot in Sea Above lighting.

**Stop condition:** fabric looks authored and painterly without any emission/WPO.

## Batch 2 — Second Horizon

1. create `MF_Shorewake_TideGradient`;
2. create broad gradient and single hero horizon band;
3. multiply hero band by embroidery mask;
4. add `SeamProximity` local scalar;
5. expose direction/position parameters;
6. test alignment with the actual Sea Above horizon from a hero camera.

**Stop condition:** horizon motif is visible but elegant at gameplay distance.

## Batch 3 — translucent hem

1. split/verify material section;
2. create `M_Shorewake_TranslucentHem_Master`;
3. establish stable opacity + Fresnel first;
4. add painterly internal depth;
5. test hair/translucency sorting;
6. only then add sparse upward droplets.

**Stop condition:** hem reads against sky, rock and water without artifacting.

## Batch 4 — impossible motion

1. create `MF_Shorewake_HemWPO`;
2. wire `VertexColor.R` mask;
3. add small normal flutter;
4. add seam directional pull;
5. clamp displacement;
6. test animations and cloth.

**Stop condition:** player can notice wrong-gravity behavior, but silhouette remains controlled.

## Batch 5 — clasp + rhythm

1. create sea-glass clasp material;
2. trap horizon line inside the clasp;
3. hook only existing confirmed rhythm signals;
4. default weights under 0.1;
5. add one Bell-pulse coordination test.

**Stop condition:** rhythm feels like the world and outfit are breathing together, not flashing together.

## Batch 6 — polish / validation

1. make Lite instances;
2. profile shader cost;
3. remove any effect that duplicates another effect's job;
4. capture before/after hero frames;
5. commit each stable material batch separately.

---

# 21. Agent prompt — paste directly to Claude

```text
You are implementing the Shorewake material family for Melodia Melusina in UE5.8.

Read Docs/Art/SHOREWAKE_DRESS_P0_SHADER_COOKBOOK_2026-08-28.md first.
Inspect the live project before modifying assets. Preserve existing character material conventions where possible.

Non-negotiables:
- The outfit must look painterly before any magic is enabled.
- Keep the first outfit visually simpler than later legendary outfits.
- Use a separate translucent material section only for the asymmetric hem.
- Implement Tide Seam response as staged diegetic feedback, not UI-like pulsing.
- Use local MIDs for SeamProximity and SeamDirectionWS unless a confirmed project-wide bus is already intended for them.
- Rhythm is subtle; use existing UMelodiaRhythmReactivitySubsystem / MPC_Melodia_Palette paths only after inspecting their actual parameters.
- Do not modify M_Water_Master_Grand_v10_Substrate.
- Do not turn the dress into a water material.
- Do not add new C++ tonight.
- Do not invent Oceanology or Melodia API names.
- Compile and validate after each material function/master batch.
- Record instruction/sampler changes.
- Keep commits narrow and reversible.

Build order:
1. stable painterly opaque fabric
2. Second Horizon gradient / embroidery
3. translucent asymmetric hem
4. hem WPO / seam-direction response
5. sea-glass clasp
6. subtle rhythm accents
7. Lite switches + performance validation

The P0 visual hierarchy is:
Sea Above / Bell > Melusina silhouette > Shorewake tide response > microdetail.
If a dress effect competes with the Bell reveal, reduce or remove it.
```

---

# 22. Final art-direction rule

> **The Shorewake dress should not announce that it is magical. It should behave like ordinary handmade clothing that has quietly decided the ocean is somewhere else.**

That is the P0 look.
