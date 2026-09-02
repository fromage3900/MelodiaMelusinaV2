# Mara Ellettra Vell — Houdini Instrument + Cymatics Execution Plan

**Date:** 2026-08-31  
**Status:** EXECUTION PLAN — TONIGHT  
**Primary target:** `cyma_spear` hero instrument  
**Secondary goal:** establish a reusable procedural instrument family for Mara without expanding tonight into five finished weapons.  
**Engine/runtime authority:** existing Melodia musical-time + reactivity systems; no new rhythm authority is introduced here.

---

## 0. Tonight's win condition

By the end of the session, the project should have **one convincing, parameterized Mara instrument** that:

1. reads as a designed object in silhouette before material detail;
2. is built as a reusable Houdini HDA rather than a one-off mesh;
3. exposes the existing `cyma_spear` variant and preserves the current Copernicus calibration controls;
4. derives engraving/emissive masks from a stable cymatic field in UV/rest space;
5. exports clean render geometry, collision, FX guide points, and named sockets;
6. preserves physically readable warm copper with cymatics layered on top rather than replacing the material;
7. can react at runtime to the existing `MPC_Melodia_Palette` channels with **no Houdini recook during play**;
8. survives the existing Copernicus batch/headless/GUI smoke path;
9. produces evidence screenshots, but **does not claim canonical AAA PASS** unless the existing evaluator gate is actually satisfied.

### Hard scope cut

Do **not** try to finish every concept-sheet instrument tonight. Build the shared architecture and finish `cyma_spear` first. The Bell Staff, Wave Harp, Harmonic Lute, Monolith Conductor, and Phase Drum become variants after the hero pipeline is proven.

---

# 1. Existing project contracts to preserve

## 1.1 Current Copernicus hero calibration

The live calibration already uses:

- `instrument_variant = cyma_spear`
- `comp_a_driver = COMP_A_F`
- `metal_finish = Warm Copper`
- `metallic = 1.0`
- `roughness = 0.18`
- `fresnel = 0.92`
- `microdetail = 0.36`
- `engraving_depth = 0.02`
- `engraving_density = 1.85`
- `glow_strength = 4.25`
- `damage = 0.08`
- `flow_anisotropy = 0.48`
- `rot_speed = 0.17`
- `cymatic_blend = 0.90`

**Rule:** the new instrument HDA should consume or mirror these names rather than inventing a parallel tuning surface.

The current artifact is still visually blocked because the compute result reads as a bright scalar field rather than credible copper. Therefore the cymatic work below is explicitly designed as a **mask/detail layer**, not the base material.

## 1.2 Current Houdini/Copernicus workflow

Project policy is already:

- Houdini `21.0.552`, Python `3.13`;
- edit scripts externally;
- prefer `hython` for construction and validation;
- use visible Houdini UI for viewer/IPR/evidence;
- current Copernicus viewer path must remain visible in `Composite View`;
- HDA existence is not proof of render quality.

Existing useful Copernicus presets:

- `golden_path`
- `warm_gradient`
- `uv_transform`
- `emboss_stack`

For this task, `emboss_stack` is the most important production primitive because the cymatic ridge field can drive engraving height/normal generation.

## 1.3 Existing runtime audio authority

Do not create a second beat clock.

`UMelodiaAudioReactivePresentationSubsystem` is already the owner of the continuous beat namespace on `MPC_Melodia_Palette`, including:

- `BeatPhase`
- `BeatPulse`
- `BeatIntensity`
- `Treble`
- `GlobalReactivity`
- `Bass`
- `Mid`

`UMelodiaRhythmReactivitySubsystem` owns command/gameplay-presentation values including:

- `RhythmPulse` = command energy
- `GlobalSparkleIntensity`
- `PaletteShift`
- `GlobalEmissiveBoost`
- `ProximityGlow`
- `TemporalJitter`
- `DreadPresence`
- `DissonanceAmount`
- `WarmthGlow`
- `DreamRipple`
- `EmberDance`
- `CozyBloom`

The reactivity signal also already exposes `BeatPulse`, `BeatPhase`, `BPM`, `ComboNormalized`, `CrescendoNormalized`, `CommandEnergy`, rhythm grade, rhythm element, command/break/victory pulses, tension, and dissonance for C++/Blueprint consumers.

**Architecture rule:** Houdini authors the instrument and static cymatic basis. Unreal animates that basis with these existing values. Runtime cymatics must not require Houdini Engine recooks.

---

# 2. HDA architecture

Create the production asset under the existing Mara production convention:

```text
/obj/MaraProduction
  /PROP
    /PROP_MARA_CymaticInstrument
```

Inside the HDA, keep semantic stages obvious:

```text
IN_GUIDES
  |
GUIDES
  |
PRIMARY_MASS
  |
FRAME_RINGS -----------+
  |                     |
RESONATOR_CORE          |
  |                     |
PRONGS_GUARDS           |
  |                     |
ORNAMENT                 |
  +---------- MERGE_BODY+
                         |
CYMATICS_UV_REST --------+
  |
CYMATICS_MASKS
  |
UV_MAT_GROUPS
  |
LODS_COLLISION
  |
SOCKETS_FX_GUIDES
  |
EXPORT
  |
VALIDATE
```

### Required outputs

```text
OUT_RENDER
OUT_COLLISION
OUT_EFX_GUIDES
OUT_DEBUG_CYMATICS
```

### Naming

Use stable production names:

```text
PROP_MARA_CYMA_SPEAR_RENDER
PROP_MARA_CYMA_SPEAR_COLLISION
SOCKET_MARA_PROP_R
SOCKET_MARA_RES_CORE
SOCKET_MARA_FX_TIP
SOCKET_MARA_FX_RING
CACHE_MARA_CYMA_SPEAR_*
```

The `SOCKET_MARA_RES_CORE` point should sit at the visual resonance crystal/core. `SOCKET_MARA_FX_TIP` should be a stable transform for Niagara beams/ripples. `SOCKET_MARA_FX_RING` should be centered on the principal resonator ring.

---

# 3. Instrument parameter interface

## 3.1 Preserve the existing calibration controls

Expose:

```text
instrument_variant
comp_a_driver
metal_finish
metallic
roughness
fresnel
microdetail
engraving_depth
engraving_density
glow_strength
damage
flow_anisotropy
rot_speed
cymatic_blend
```

## 3.2 Add geometry controls

Keep the first pass small and meaningful:

```text
body_length
body_radius
shaft_taper
ring_radius
ring_thickness
ring_count
core_radius
prong_length
prong_spread
guard_arc
ornament_scale
asymmetry
```

Do not expose 50 low-level modeling parameters. Promote only controls that visibly change design language.

## 3.3 Add cymatic authoring controls

```text
cyma_mode             // chladni | radial | interference
cyma_m                // angular / first mode count
cyma_n                // second mode count
cyma_frequency
cyma_phase
cyma_threshold
cyma_width
cyma_warp
cyma_seed
cyma_macro_depth
cyma_micro_strength
```

Recommended defaults for the first readable pattern:

```text
cyma_mode = chladni
cyma_m = 3
cyma_n = 5
cyma_phase = 0
cyma_threshold = 0.08
cyma_width = 0.04
cyma_macro_depth = 0.012–0.02
```

Keep `cymatic_blend` as the art-directable master mix.

---

# 4. Geometry build — exact order

## Pass A — silhouette first

### A1. Main spine

Create one resampled central curve from grip to tip. This is the design skeleton. Give it a normalized `curveu` attribute and never destroy that reference until export.

The silhouette should read as:

- narrow grip;
- widening resonator body around ~60–72% of length;
- one large circular/elliptical visual event;
- a thin forward prong/tip;
- controlled asymmetry from one secondary arc or hanging element.

If the grayscale silhouette does not look like Mara's instrument, do not add engraving yet.

### A2. Shaft/body

Use Sweep around the spine. Drive radius with a ramp using `curveu` so the hand zone is clean and the resonator zone expands deliberately.

Keep cross-section moderate. Do not subdivide for microdetail.

### A3. Resonator ring family

Generate ring centers from `curveu`, then instance/copy ring modules. Make the largest ring a separate named packed piece so later variants can replace it without rebuilding the shaft.

Each ring gets:

- stable local frame;
- `name` attribute;
- `variant_region = resonator`;
- `material_region = metal`.

### A4. Resonance core

Build the core as a separate mesh. Start with a faceted gem/lens/crystal form rather than a sphere. The core should be visible through the ring and create a focal contrast.

Group as `RES_CORE` and keep it replaceable.

### A5. Prongs / guard / harmonic arcs

Author these as curves and Sweep them. Curves are much faster to art-direct tonight than destructive polygon modeling.

Use one deliberate S-curve or crescent arc to pull the design toward the musical/cymatic concept art. Avoid generic fantasy spear symmetry.

### A6. Ornament

Only after silhouette works:

- 2–4 hanging calibration tags;
- one small charm chain;
- engraved ring plates;
- optional cloth tassel as separate geometry.

Do **not** proceduralize every chain link tonight. Instances are sufficient.

---

# 5. Cymatic field construction

The cymatic field must live in stable UV/rest coordinates so the design does not swim when the instrument is transformed or animated.

## 5.1 Chladni-inspired field

On a UV-flattened/rest-space representation, create an Attribute Wrangle equivalent to:

```c
vector2 uv = set(v@uv.x, v@uv.y);
float x = fit(uv.x, 0.0, 1.0, -1.0, 1.0);
float y = fit(uv.y, 0.0, 1.0, -1.0, 1.0);

float m = chf("m");
float n = chf("n");
float phase = chf("phase");

float a = sin(m * M_PI * x + phase) * sin(n * M_PI * y);
float b = sin(n * M_PI * x) * sin(m * M_PI * y + phase);
float field = a - b;

float threshold = chf("threshold");
float width = chf("width");
float ridge = 1.0 - smooth(threshold, threshold + width, abs(field));

f@cyma_value = field;
f@cyma_ridge = clamp(ridge, 0.0, 1.0);
f@cyma_phase = phase;
```

Use the field to make **nodal lines** rather than embossing the entire scalar gradient.

## 5.2 Radial variant

For rings/core faces, radial cymatics will read better:

```c
float x = fit(v@uv.x, 0.0, 1.0, -1.0, 1.0);
float y = fit(v@uv.y, 0.0, 1.0, -1.0, 1.0);
float r = length(set(x, y));
float theta = atan2(y, x);
float phase = chf("phase");

float field = cos(chf("lobes") * theta + phase)
            * cos(chf("radial_freq") * r * M_PI - phase);
```

Use this on the large resonator disk/ring and the Chladni field on long enamel/metal panels.

## 5.3 Store a small reusable data contract

At minimum:

```text
f@cyma_value
f@cyma_ridge
f@cyma_phase
v@cyma_dir
s@cyma_region
```

This is the bridge between geometry, Copernicus, export validation, and later tooling.

---

# 6. Split cymatics by physical scale

This is the most important rendering rule tonight.

### Macro — real geometry or height

Use only large, readable grooves/ridges. Keep actual displacement shallow enough to preserve the machined metal silhouette.

Suggested range:

```text
0.5–2 mm equivalent visual depth
```

### Meso — normal/bump

Use Copernicus `emboss_stack` to turn the cymatic ridge into engraved normal/height detail.

### Micro — shader only

Micro scratches, brushed anisotropy, tiny surface frequency should remain shader detail. Do not send them through geometry.

### Emissive — accent only

Emission should reveal/trace selected nodal lines. It must never flatten the object into a glowing card.

### Roughness — subtle modulation

Use cymatic lines to slightly tighten or loosen roughness. Do not modulate metallic aggressively. Copper must still look metallic with all cymatic emission disabled.

---

# 7. Copernicus texture stack

Create four production outputs from the same cymatic basis:

```text
CYMA_MASK
CYMA_HEIGHT
CYMA_EMISSIVE
CYMA_ROUGHNESS
```

Optional fifth output later:

```text
CYMA_VARIANT_ATLAS
```

## Suggested graph logic

```text
stable UV cymatic source
   |
uv_transform
   |
threshold / edge shaping
   +------> CYMA_MASK
   |
emboss_stack
   +------> CYMA_HEIGHT
   |
blur / remap / selective bloom
   +------> CYMA_EMISSIVE
   |
invert + low-amplitude remap
   +------> CYMA_ROUGHNESS
```

Use `warm_gradient` **only as a debug visualization** while proving values. It is not the final copper surface.

### Proposed production output path

```text
Content/Houdini/GeneratedData/Textures/Mara/CymaSpear/
```

### Proposed production HDA path

```text
Content/Houdini/GeneratedData/HDAs/Mara/
```

Keep the existing Copernicus test output path separate from production assets.

---

# 8. Unreal runtime cymatics — no recook design

The HDA bakes the pattern basis. Runtime merely animates material parameters and FX.

## 8.1 Material inputs

Create the instrument material instance so the metal path remains valid independently of music:

```text
BASE COPPER
  BaseColor
  Metallic = ~1
  Roughness = authored base + subtle CYMA_ROUGHNESS
  Normal = base normal + CYMA_HEIGHT

CYMATIC OVERLAY
  mask = CYMA_MASK
  emissive = CYMA_EMISSIVE * runtime intensity
  phase motion = UV/analytic offset or atlas blend
```

### Test zero state first

Set every runtime signal to zero. The instrument must still read as premium warm copper. If it does not, fix the material before reactivity.

## 8.2 Runtime parameter mapping

Use the existing project authority rather than inventing another channel set:

| Existing channel | Instrument use |
|---|---|
| `BeatPhase` | continuous traveling phase / ring rotation; subtle |
| `BeatPulse` / `BeatIntensity` | short nodal-line luminosity lift |
| `RhythmPulse` | command-energy amplitude / cymatic activation |
| `GlobalEmissiveBoost` | crescendo-scale brightness ceiling |
| `PaletteShift` | select/blend authored pattern palette or mode |
| `GlobalSparkleIntensity` | crystal/core sparkle |
| `ProximityGlow` | break/reveal flash from core outward |
| `TemporalJitter` | unstable phase distortion; keep small |
| `DreadPresence` | cool/dampen outer copper response |
| `DissonanceAmount` | controlled perturbation of pattern regularity |
| `WarmthGlow` | exploration idle warmth |
| `DreamRipple` | slow core ripple outside combat |

### Recommended runtime formulas

Keep these art-directed, not physically literal:

```text
CymaIntensity = saturate(RhythmPulse * 0.65 + BeatPulse * 0.35)
CymaEmission  = CYMA_EMISSIVE * CymaIntensity * GlobalEmissiveBoost
CymaPhase     = frac(BeatPhase + TemporalJitter * 0.03)
CoreSparkle   = GlobalSparkleIntensity * 0.6 + BeatPulse * 0.2
Distortion    = DissonanceAmount * 0.025
```

Do not rotate the entire texture aggressively every beat. The player should perceive a resonant instrument, not a UV effect demo.

## 8.3 Pattern-state strategy

For the first runtime version, bake **4–8 cymatic patterns** and blend/index them. Do not solve a full PDE on the GPU tonight.

Example modes:

```text
0 Rest / survey
1 Beat response
2 Command / attack
3 Crescendo
4 Break
5 Victory
6 Dread
7 Rupture
```

A later shader can analytically synthesize radial modes, but the atlas approach gets the art direction locked first.

---

# 9. Variant system after the hero works

One HDA should share modules while allowing large silhouette swaps.

```text
cyma_spear              // tonight; hero proof
resonant_bell_staff     // ring -> hanging bell architecture
wave_harp               // shaft -> curved string frame
harmonic_lute           // compact circular body + strings
monolith_conductor      // elongated ring/crystal conductor
phase_drum              // radial disk / handheld resonator
```

Shared modules:

- grip;
- resonator core;
- ring grammar;
- calibration tags;
- cymatic field contract;
- material groups;
- socket naming;
- export/validation.

Variant-specific modules should switch **before** ornament, not after, so silhouette changes are real rather than cosmetic.

---

# 10. Export contract

The production HDA should export only approved surfaces and stable helper data.

## Render

- consolidated render mesh or intentional modular pieces;
- material slots: `METAL`, `CORE`, `ENAMEL`, optional `CLOTH`;
- clean UV0;
- optional UV1 only if needed by runtime material/lighting;
- vertex color channel reserved for useful masks, not random debug color.

## Collision

One or a few primitive/convex collision shapes. Do not auto-convex every ornament.

## FX guides

Export points/transforms for:

```text
SOCKET_MARA_RES_CORE
SOCKET_MARA_FX_TIP
SOCKET_MARA_FX_RING
```

## Character attachment

Export a stable right-hand grip transform:

```text
SOCKET_MARA_PROP_R
```

Do not bake Mara's hand pose into the prop geometry. Keep attachment authority at the character/weapon layer.

---

# 11. Validator checklist

Create/extend a validator before calling the asset done.

### Geometry

- non-empty `OUT_RENDER`;
- no NaN positions/normals;
- no unexpected open boundaries on rigid metal;
- sane bounding box;
- named material groups exist;
- `cyma_ridge` stays in `[0,1]`;
- UVs exist on all cymatic regions;
- sockets exist exactly once.

### Design

- readable in black silhouette;
- hero ring/core visible at game camera distance;
- grip area is not obstructed by ornaments;
- no tassel/chain intersects primary grip;
- asymmetry does not destroy balance/readability.

### Material

- copper is identifiable with emissive = 0;
- highlights move over the surface in lit view;
- engraving reads without becoming black line art;
- emissive occupies a minority of the visible surface;
- core is a focal accent, not a white clipping disk.

### Runtime

- BeatPhase animates continuously only when musical time exists;
- no second beat clock is created;
- `RhythmPulse` reacts to command energy;
- zero-signal state is stable;
- no gameplay result depends on this presentation layer.

---

# 12. Tonight's execution schedule

## 00:00–00:20 — baseline and safety

1. Pull current branch/repo state.
2. Open the current Copernicus AAA calibration and screenshot the current blocked look.
3. Record the current `cyma_spear` parameter values above.
4. Make sure you can run the existing smoke command before touching production work.

From `Tools/Houdini`:

```bat
python run_hython.py copernicus_smoke.py
```

If the baseline smoke fails, stop and fix baseline first.

## 00:20–01:10 — hero silhouette

Build:

- main spine;
- swept shaft;
- hero resonator ring;
- core;
- one prong/arc family;
- provisional grip.

**Gate:** viewport black silhouette must already look intentional.

## 01:10–01:50 — reusable HDA structure

- wrap modules into semantic subnets;
- promote only the geometry controls listed above;
- establish output nodes;
- add material region groups;
- add four named socket/FX points.

**Gate:** changing `ring_radius`, `body_length`, and `prong_spread` must not break the graph.

## 01:50–02:35 — cymatic basis

- create stable UV/rest-space basis;
- implement Chladni field;
- implement radial field for ring/core;
- write `cyma_value`, `cyma_ridge`, `cyma_phase`, `cyma_region`;
- test threshold/width controls.

**Gate:** transform the object and verify the cymatic pattern does not swim.

## 02:35–03:15 — Copernicus maps

- route pattern through `uv_transform`;
- use `emboss_stack` for engraving height;
- generate `CYMA_MASK`, `CYMA_HEIGHT`, `CYMA_EMISSIVE`, `CYMA_ROUGHNESS`;
- keep warm-gradient debug separate from final material.

**Gate:** maps are individually legible in `Composite View`.

## 03:15–03:55 — copper material repair + cymatic layering

Start with emission OFF.

1. Make warm copper believable.
2. Confirm metallic response and roughness highlight.
3. Add engraving normal/height.
4. Add subtle roughness modulation.
5. Finally enable cymatic emission.

**Gate:** toggling `cymatic_blend` to zero leaves a convincing instrument rather than exposing a broken base shader.

## 03:55–04:25 — export + UE-ready contract

- generate render output;
- generate cheap collision;
- verify material groups;
- verify sockets;
- save HDA under proposed Mara production output path;
- prepare textures under `GeneratedData/Textures/Mara/CymaSpear`.

Do not spend this block on decorative chains.

## 04:25–04:50 — validation

Run the existing Houdini/Copernicus checks, including the documented batch/headless path. Then open Houdini visibly and verify the expected viewer result in `Composite View`.

Run at minimum:

```bat
python run_hython.py copernicus_smoke.py
python run_hython.py copernicus_headless_smoke.py
```

Then run the documented GUI smoke/evidence flow using `copernicus_gui_smoke.py` in Houdini.

## 04:50–05:10 — evidence and notes

Capture:

1. silhouette/unlit view;
2. lit copper, cymatics off;
3. lit copper, cymatics on;
4. cymatic debug mask;
5. HDA parameter pane;
6. socket/FX guide visualization;
7. Copernicus `Composite View` output.

Record what passed and what remained blocked. Do not convert a visually weak artifact into a PASS merely because the network cooked.

---

# 13. Three-hour emergency cutoff

If energy/time runs out, stop after this minimum:

1. hero `cyma_spear` silhouette;
2. reusable HDA structure;
3. stable UV/rest cymatic ridge field;
4. four map outputs;
5. copper reads correctly with emission OFF;
6. one successful HDA save/export;
7. existing smoke test still passes.

Defer:

- five extra instrument variants;
- chains/tassel simulation;
- damage system polish;
- atlas of 8 runtime modes;
- full Niagara treatment;
- final UE weapon animation/hand posing;
- canonical AAA evaluator pass.

That cutoff still leaves a valuable production primitive rather than another half-finished visual experiment.

---

# 14. First UE integration after Houdini proof

When the Houdini/Copernicus asset is visually proven, integration should be intentionally thin:

1. Import/cook the instrument asset.
2. Attach via `SOCKET_MARA_PROP_R`.
3. Use an instrument material instance that samples `MPC_Melodia_Palette`.
4. Map `BeatPhase`, `BeatPulse`, `RhythmPulse`, `GlobalEmissiveBoost`, and `PaletteShift` first.
5. Add core/tip Niagara only after material reactivity works.
6. Use `SOCKET_MARA_RES_CORE`, `SOCKET_MARA_FX_RING`, and `SOCKET_MARA_FX_TIP` as effect origins.
7. If a mesh-specific dynamic-material path is needed, use the existing `UMelodiaRhythmReactivitySubsystem::RegisterReactiveMeshComponent` instead of inventing a new global writer.

### First playable behavior

At rest:
- warm copper;
- faint core light;
- very slow `DreamRipple` breathing.

On beat:
- nodal lines briefly brighten;
- core pulse remains restrained.

On command:
- `RhythmPulse` expands the active cymatic region from core toward tip.

On crescendo:
- `GlobalEmissiveBoost` lifts energy but keeps metal visible.

On break:
- `ProximityGlow` sends one reveal sweep through the engraved channels.

On dissonance:
- `DissonanceAmount` perturbs phase slightly rather than turning the whole object noisy.

This gives Mara an instrument that visibly *measures and answers resonance* rather than simply glowing to music.

---

# 15. Future instrument-family expansion

Once `cyma_spear` passes the visual/material gate, duplicate **only the silhouette module**, not the entire graph.

Recommended order:

1. `resonant_bell_staff` — easiest reuse of shaft + ring grammar;
2. `monolith_conductor` — easy reuse of ring/core, stronger crystal emphasis;
3. `wave_harp` — proves strings/curved-frame architecture;
4. `harmonic_lute` — compact handheld topology;
5. `phase_drum` — proves radial cymatics and impact presentation.

Each variant should retain the same export/socket/cymatic/material contract so Unreal does not care how the instrument was constructed.

---

# 16. Definition of done for this experiment

Tonight's experiment is successful when all of these are true:

- [ ] `cyma_spear` is a recognizable designed silhouette.
- [ ] HDA modules and promoted controls are clean.
- [ ] existing calibration parameters remain compatible.
- [ ] cymatics are generated from stable coordinates.
- [ ] macro/meso/micro detail are separated.
- [ ] copper reads correctly with all glow disabled.
- [ ] glow traces cymatics without replacing material response.
- [ ] render/collision/FX/socket outputs exist.
- [ ] `COMP_A_F` remains the existing driver contract.
- [ ] no duplicate rhythm clock or beat writer is added.
- [ ] Copernicus smoke tests still pass.
- [ ] visible Houdini evidence exists.
- [ ] current AAA gate is only marked PASS if its evaluator requirements are actually met.

---

## Source-of-truth files consulted

- `Tools/Houdini/copernicus/README.md`
- `Docs/Plans/COPERNICUS_AAA_LIVE_REPORT_2026-08-31.md`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.cpp`
- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmReactivitySubsystem.h`
- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmReactivitySubsystem.cpp`
- historical Mara P0–P3 Houdini execution plan on `docs/2026-08-29-character-p1-p2-canon-audit`

**Decision:** make the cymatic pattern a reusable authored field and runtime presentation surface, not a new simulation authority. The instrument must be beautiful when silent; music then reveals its hidden geometry.