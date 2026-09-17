# Muse Technical Brief — Melodia Living Flower Field

**Date:** 2026-09-16  
**Status:** Approved implementation brief for artist + agent co-production  
**Primary owner split:** Brennan owns composition/lookdev; Muse owns technical infrastructure.

## Goal

Build a serene, AAA-quality flower field for Melusina where existing SpeedTree plants move naturally with wind while a restrained chromatic response travels through the meadow in the same direction. Houdini provides deterministic ecology points and metadata; Unreal PCG/PCGEx instantiates the existing SpeedTree assets; UE materials, MPCs, Niagara, and OSC provide the live runtime response.

The field must still look finished with OSC/audio disabled.

## Artist / Muse ownership

### Artist owns
- final flower species and SpeedTree asset choices
- composition, hero clusters, density balance, and negative space
- camera, lighting, fog, palette, and final beauty judgment
- final wind strength, hue strength, sparkle level, and Niagara restraint

### Muse owns
- Houdini HDA architecture
- Houdini→PCG data contract and validation
- PCG/PCGEx staging and instancing
- deterministic seeds and metadata
- wind/MPC/OSC plumbing
- reusable material function(s)
- Niagara wind follow-through
- performance, debug views, restart/reopen validation, and documentation

Do not let architecture churn block the artist’s scene-composition loop.

---

## Verified project state

- Project targets **Unreal Engine 5.8**.
- `PCG`, `PCGExtendedToolkit`, `HoudiniEngine`, and `SpeedTreeImporter` are enabled in `BS_GodFile.uproject`.
- Vendored PCGEx is **0.76** and declares `EngineVersion: 5.8.0`.
- Existing project OSC infrastructure already routes material/audio data into MPCs.
- Existing routing docs and runtime code disagree on some port ownership (`9000` vs `8000`), so Muse must audit live directionality before changing ports.

## Hallucination-check corrections

1. **Do not assume Houdini→PCG metadata is a perfect 1:1 transfer.** SideFX explicitly notes that PCG data can change during transfer. Validate every attribute required by the downstream graph. For native PCG output use the Houdini PCG workflow (`Force PCG Outputs` and/or the documented `unreal_pcg_params` mechanism) rather than assuming arbitrary point attrs automatically survive.

2. **Do not add a third Material Parameter Collection to one flower material.** UE 5.8 materials can reference at most two MPCs. The flower material plan should therefore remain within the existing `MPC_SakuraDream` + `MPC_Melodia_Palette` pair, or consolidate parameters rather than introducing a third collection.

3. **Do not blindly change every OSC route to port 9000.** `deploy/osc_routing.json` treats 9000 as canonical TD↔UE routing while `Content/Python/osc_server.py` currently listens on 8000. First determine whether these represent separate inbound/outbound duties or stale documentation. Preserve working routes and normalize only after a live send/receive test.

4. **Keep the SpeedTree material wind chain intact.** Add the Melodia response around the imported SpeedTree material/function structure; do not replace the SpeedTree expression or break its wind/LOD inputs.

5. **No runtime Houdini dependency.** Houdini cooks author ecology; runtime wind/color/music behavior stays in Unreal.

---

## Core architecture

```text
ARTIST BEAUTY TARGET
        |
        v
HOUDINI 22
HDA_MelodiaFlowerField
        |
        | points + tested metadata only
        v
UNREAL PCG / PCGEx
        |
        v
EXISTING SPEEDTREE ASSETS
        |
        +---------------------------+
        |                           |
        v                           v
SpeedTree Wind              Flower Material Layer
                                    |
                           directional hue reveal
                                    |
                    MPC_SakuraDream + MPC_Melodia_Palette
                                    ^
                                    |
                              OSC / TD / game
```

Do not pass duplicated SpeedTree geometry through Houdini. Houdini outputs transforms, masks, IDs, weights, and metadata; Unreal owns the asset references and instances.

---

## P0 — audit and prove the bridge

Before making production changes:

- verify Houdini 22 PCG plug-in is the PCG-capable Houdini Engine build
- verify the HDA node can round-trip scalar/vector/string-or-ID metadata required by the field
- verify repeated cook with identical seed/input is deterministic
- verify editor reopen retains the PCG/HDA relationship
- verify the existing OSC listener’s actual inbound port and the TD sender’s outbound port
- verify existing `MPC_SakuraDream` and `MPC_Melodia_Palette` parameter budgets

Do this in a disposable test graph/map, not the production scene.

---

## P1 — HDA_MelodiaFlowerField

Inputs:
- terrain / landscape or mesh terrain
- optional artist density mask
- optional exclusion geometry
- optional paths/splines
- optional hero-zone masks

Output points only.

Required metadata contract, subject to actual Houdini-PCG round-trip verification:

```text
species_id
variant_id
scale
yaw
cluster_id
hue_seed
wind_phase
wind_response
sparkle_response
hero_weight
height_class
density_class
```

Use deterministic seeds. Same inputs + same seed must reproduce the same layout.

The HDA should support authored ecological masses rather than uniform noise:
- hero bloom cluster
- dense meadow
- low transition field
- tall accent patch
- sparse breathing zone

---

## P2 — PCG / PCGEx staging

Map `species_id` / category metadata to artist-curated SpeedTree collections. Prefer instanced spawning rather than unique Actors.

Preserve:
- SpeedTree LOD behavior
- SpeedTree wind
- culling
- material slots
- existing imported SpeedTree functionality

Avoid per-flower ticking and per-flower dynamic material instances.

### PCGEx example maps worth studying / borrowing patterns from

Do **not** merge the example project maps wholesale into production. Use them as reference sources and rebuild only the needed subgraphs against the vendored PCGEx 0.76 API.

1. **`LV_Category-Staging.umap`** — highest-value reference for this task. Study the staging/collection examples such as `PCGEx_Staging_Distribution`, `PCGEx_Staging_ClosestMatch`, `PCGEx_Staging_RandomPerCategory`, and Asset Collections. Use these patterns for curated flower-family selection and weighted variants.

2. **`LV_Category-Sampling.umap`** — use for transferring hero masks, nearest-spline/surface information, density metadata, and artist-authored response weights into flower points.

3. **`LV_Category-Paths.umap`** — use for authored path/exclusion boundaries, cleaned curve data, cluster edges, and controlled transitions near gameplay paths.

4. **`LV_Category-Tensors.umap`** — use selectively for secondary directional structures, not the base meadow scatter. Relevant examples include tensor transform/extrusion/custom-guide patterns. Tensors are useful when the art needs coherent flow lines or a hero gust corridor; they are overkill for ordinary flower distribution.

5. **`Categories-All.umap`** — discovery/index map only. Do not make it a production dependency.

Existing Melodia doctrine still applies: PCGEx is valuable when it adds structure/meaning, not when it simply randomizes more scatter.

---

## P3 — wind-driven material response

Create a reusable function such as `MF_MelodiaWindHueReveal`.

Base flower appearance must remain correct at response amount 0.

Conceptual field math:

```text
D = normalize(WindDirection.xy)
phase = dot(AbsoluteWorldPosition.xy, D) * SpatialFrequency
phase += Time * WindStrength * TravelSpeed
phase += PerInstanceHueSeed
Wave = sin(phase) * 0.5 + 0.5
```

Guard against a near-zero wind vector before normalization.

Use the wave to blend toward an artist-authored palette response, not to run an aggressive full-spectrum rainbow cycle.

Target stack:

```text
natural SpeedTree albedo
+ restrained directional tint
+ optional grazing iridescence
+ optional dream rim
```

Different flower families should receive different response strengths from instance metadata/custom data without unique MIs.

---

## P4 — wind contract

Audit and then expose a complete wind vector instead of reducing the effect to `abs(X)`.

Desired semantic contract:

```text
WindDirection = normalized XY direction
WindStrength  = XY magnitude
```

Feed the same semantic wind into:
- SpeedTree / WindDirectionalSource behavior where appropriate
- `MPC_SakuraDream` wind parameters
- Niagara petals/motes
- hue-reveal direction

Do not assume a material MPC update itself changes SpeedTree physical wind; those systems must be coordinated explicitly.

---

## P5 — musical layer

Reuse existing Melodia audio signals. Do not create another audio bus.

Suggested mapping:

```text
Mid       -> subtle hue excursion / tiny stem modulation
Bass      -> restrained petal breathing
Treble    -> sparkle / grazing iridescence
BeatPulse -> tiny transient rim/color event
```

Wind remains the directional conductor. Music decorates the ecology.

---

## P6 — Niagara punctuation

Reuse the same wind vector for occasional petals, pollen/motes, and restrained sparkle.

Expose artist controls for:
- PetalSpawnMultiplier
- MoteSpawnMultiplier
- SparkleIntensity
- HeroZoneWeight

Avoid constant particle noise.

---

## Performance rules

Prefer:

```text
one/few global MPC updates
+ many cheap material consumers
+ instanced vegetation
```

Avoid:
- runtime Houdini cooks
- per-frame PCG regeneration
- per-flower Blueprint Tick
- hundreds of dynamic material instances
- unnecessary masked overdraw and Niagara density

Profile before/after:
- instance count
- draw calls
- GPU timing
- material cost
- Niagara counts
- LOD/cull behavior

---

## Validation slice

Use a safe 30–50 m test meadow with three flower species.

Validate:

### Static
- natural material appearance
- SpeedTree LOD/wind still works
- deterministic HDA output
- no broken instance materials

### Direction
Test `+X`, `-X`, `+Y`, `-Y`, then diagonals. Physical bend, hue travel, and Niagara drift should read as the same wind event.

### Zero wind
No NaNs, flicker, or direction snapping.

### OSC
Prove actual route and port ownership before changing canonical docs/code.

### Audio
Prove each band independently and confirm the field still reads beautifully with all audio reactivity at zero.

### Reopen
Close/reopen editor and verify the HDA/PCG relationship, material references, and control values remain sane.

---

## Artist-facing controls

Keep the beauty surface compact:

```text
FLOWER FIELD
Density
Cluster Size
Species Mix
Hero Weight

WIND MAGIC
Hue Reveal Amount
Hue Travel Speed
Hue Spatial Scale
Wind Response
Color Settle

MUSIC
Mid Hue Amount
Bass Bloom Amount
Treble Sparkle Amount
Beat Response

FX
Petal Density
Mote Density
Sparkle Strength
```

Engineering/debug settings stay elsewhere.

---

## Execution order

```text
P0  bridge + port + metadata canary
P1  HDA points + deterministic metadata
P2  PCGEx staging -> existing SpeedTree instances
P3  directional hue-reveal material
P4  complete wind vector coordination
P5  per-species/per-instance response
P6  Niagara punctuation
P7  music modulation
P8  profiling, reopen proof, docs
```

At each stage, leave the project in a valid working state.

## Acceptance criteria

The feature is complete when the artist can compose/lookdev without touching technical plumbing; Houdini outputs deterministic ecology points; Unreal efficiently instances the existing SpeedTree assets; wind motion and chromatic travel agree; species respond differently without unique material instances; existing OSC/audio systems enhance rather than define the scene; no runtime Houdini cook is required; reopen is deterministic; and the finished meadow still looks beautiful with all reactive inputs disabled.
