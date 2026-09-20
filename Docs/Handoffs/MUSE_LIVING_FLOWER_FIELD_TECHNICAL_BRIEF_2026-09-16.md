# Muse Technical Brief — Melodia Living Flower Field

**Date:** 2026-09-16  
**Status:** Approved implementation brief for artist + agent co-production  
**Primary owner split:** Brennan owns composition/lookdev; Muse owns technical infrastructure.

## Goal

Build a serene, AAA-quality flower field for Melusina where existing SpeedTree plants move naturally with wind while a restrained chromatic response travels through the meadow in the same direction. Houdini provides deterministic ecology points and metadata; Unreal PCG/PCGEx instantiates the existing SpeedTree assets; UE materials, the canonical Melodia MPC pair, Niagara, and OSC provide the live runtime response.

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
- The canonical Melodia material buses are:
  - `MPC_Melodia_Palette` — source/audio-reactivity bus.
  - `MPC_Cymatics_Driver` — derived cymatic/material driver.
- Current code and docs treat `UMelodiaCymaticsWriterSubsystem` as the **sole writer** to `MPC_Cymatics_Driver`; new flower-field wind values must preserve that authority instead of having unrelated systems write the driver directly.
- Current asset paths found in repo code are:
  - `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette`
  - `/Game/Melodia/Cymatics/MPC_Cymatics_Driver`
- A separate migration plan exists for eventually moving the palette asset. Do **not** move it as part of this task; current writer paths must remain valid.
- Existing routing docs and runtime code disagree on some port ownership (`9000` vs `8000`), so Muse must audit live directionality before changing ports.

## Hallucination-check corrections

1. **Do not assume Houdini→PCG metadata is a perfect 1:1 transfer.** Validate every attribute required by the downstream graph. Use the actual Houdini-PCG output contract rather than assuming arbitrary attributes automatically survive.

2. **Do not add a third Material Parameter Collection to the flower material.** Keep the feature inside the canonical pair `MPC_Melodia_Palette` + `MPC_Cymatics_Driver`.

3. **Do not use `MPC_SakuraDream` as flower-field authority.** It may remain valid for older Sakura/EnvSandbox effects, but it is not the canonical Melodia world-field bus for this system.

4. **Do not violate the Cymatics driver sole-writer contract.** OSC/game input should enter an upstream/source lane, then the existing Cymatics writer should derive/publish the corresponding `Cymatic_*` values into `MPC_Cymatics_Driver`.

5. **Do not blindly change every OSC route to port 9000.** `deploy/osc_routing.json` treats 9000 as canonical TD↔UE routing while `Content/Python/osc_server.py` currently listens on 8000. Determine whether these are separate inbound/outbound duties or stale documentation before normalizing anything.

6. **Keep the SpeedTree material wind chain intact.** Add the Melodia response around the imported SpeedTree material/function structure; do not replace the SpeedTree expression or break its wind/LOD inputs.

7. **No runtime Houdini dependency.** Houdini cooks author ecology; runtime wind/color/music behavior stays in Unreal.

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
        +----------------------------+
        |                            |
        v                            v
SpeedTree Wind               Flower Material Layer
                                     |
                            directional hue reveal
                                     |
                     MPC_Cymatics_Driver
                                     ^
                                     |
                    UMelodiaCymaticsWriterSubsystem
                                     ^
                                     |
                      MPC_Melodia_Palette
                                     ^
                                     |
                          OSC / TD / game input
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
- verify `MPC_Melodia_Palette` and `MPC_Cymatics_Driver` parameter contracts and current asset paths
- verify the Cymatics writer remains the sole writer to `MPC_Cymatics_Driver`

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

1. **`LV_Category-Staging.umap`** — highest-value reference for this task. Study `PCGEx_Staging_Distribution`, `PCGEx_Staging_ClosestMatch`, `PCGEx_Staging_RandomPerCategory`, and Asset Collections for curated flower-family selection and weighted variants.

2. **`LV_Category-Sampling.umap`** — use for transferring hero masks, nearest-spline/surface information, density metadata, and artist-authored response weights into flower points.

3. **`LV_Category-Paths.umap`** — use for authored path/exclusion boundaries, cleaned curve data, cluster edges, and controlled transitions near gameplay paths.

4. **`LV_Category-Tensors.umap`** — use selectively for secondary directional structures, not the base meadow scatter. Tensor/custom-guide patterns are useful when the art needs coherent flow lines or a hero gust corridor; they are overkill for ordinary flower distribution.

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

The material should consume derived world-field values from `MPC_Cymatics_Driver` and source/audio values from `MPC_Melodia_Palette` only where necessary. Stay within the two-collection budget.

---

## P4 — canonical wind contract

Audit and then expose a complete wind vector instead of reducing the effect to `abs(X)`.

Desired semantic source contract:

```text
WindDirX
WindDirY
WindStrength
```

Prefer storing normalized XY direction plus magnitude rather than a redundant XYZ vector for this meadow.

### Authority rule

Do **not** write wind directly from the OSC Python bridge into `MPC_Cymatics_Driver` if that breaks the sole-writer contract.

Preferred data flow:

```text
OSC / game wind
    -> MPC_Melodia_Palette source lanes
    -> UMelodiaCymaticsWriterSubsystem
    -> MPC_Cymatics_Driver derived lanes
    -> flower material / Niagara
```

Candidate names, to be created only after checking for collisions:

```text
MPC_Melodia_Palette
  WindDirX
  WindDirY
  WindStrength

MPC_Cymatics_Driver
  Cymatic_WindDirX
  Cymatic_WindDirY
  Cymatic_WindStrength
```

The existing Cymatics driver contract is currently scalar-oriented, so three scalars are safer than inventing an unverified vector parameter convention.

Feed the same semantic wind into:
- SpeedTree / `WindDirectionalSource` behavior where appropriate
- `MPC_Cymatics_Driver` flower/material response
- Niagara petals/motes
- hue-reveal direction

Do not assume an MPC update itself changes SpeedTree physical wind; those systems must be coordinated explicitly.

---

## P5 — musical layer

Reuse existing Melodia audio signals. Do not create another audio bus.

The repo already defines the pipeline conceptually as:

```text
MPC_Melodia_Palette
    -> UMelodiaCymaticsWriterSubsystem
    -> MPC_Cymatics_Driver
```

Use existing driver fields such as the current `Cymatic_BeatPulse`, `Cymatic_BassIntensity`, `Cymatic_MidIntensity`, `Cymatic_EmissiveScale`, and `Cymatic_IridescenceShift` where they match the desired art response instead of duplicating them.

Suggested mapping:

```text
Cymatic_MidIntensity      -> subtle hue excursion / tiny stem modulation
Cymatic_BassIntensity     -> restrained petal breathing
Cymatic_IridescenceShift  -> grazing color response
Cymatic_EmissiveScale     -> sparkle ceiling
Cymatic_BeatPulse         -> tiny transient rim/color event
```

Wind remains the directional conductor. Music decorates the ecology.

---

## P6 — Niagara punctuation

Reuse the same canonical wind values for occasional petals, pollen/motes, and restrained sparkle.

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

### MPC authority
- OSC/game writes source wind values only to the chosen source contract
- Cymatics writer is still the only writer to `MPC_Cymatics_Driver`
- derived driver values match source direction/strength

### OSC
Prove actual route and port ownership before changing canonical docs/code.

### Audio
Prove each existing cymatic lane independently and confirm the field still reads beautifully with all audio reactivity at zero.

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
Treble / Iridescence Amount
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
P0  bridge + port + metadata + MPC-authority canary
P1  HDA points + deterministic metadata
P2  PCGEx staging -> existing SpeedTree instances
P3  directional hue-reveal material
P4  canonical wind source -> Cymatics driver flow
P5  per-species/per-instance response
P6  Niagara punctuation
P7  existing cymatic/music modulation
P8  profiling, reopen proof, docs
```

At each stage, leave the project in a valid working state.

## Acceptance criteria

The feature is complete when the artist can compose/lookdev without touching technical plumbing; Houdini outputs deterministic ecology points; Unreal efficiently instances the existing SpeedTree assets; wind motion and chromatic travel agree; species respond differently without unique material instances; the canonical `MPC_Melodia_Palette -> UMelodiaCymaticsWriterSubsystem -> MPC_Cymatics_Driver` authority remains intact; existing OSC/audio systems enhance rather than define the scene; no runtime Houdini cook is required; reopen is deterministic; and the finished meadow still looks beautiful with all reactive inputs disabled.
