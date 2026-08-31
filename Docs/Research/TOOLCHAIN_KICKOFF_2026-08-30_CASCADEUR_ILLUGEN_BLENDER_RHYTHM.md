# 2026-08-30 — Toolchain Kickoff: Cascadeur + IlluGen + Blender Rhythm Proceduralism

**Project:** Melodia Melusina / Unreal Engine 5.8  
**Status:** same-day execution plan  
**Branch:** `docs/2026-08-29-character-p1-p2-canon-audit`  
**Parent research:**
- `Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`
- `Docs/Research/TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md`
- `Docs/Research/EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_03_2026-08-30.md`

---

# Goal

Start the emerging-toolchain R&D **today**, not tomorrow, with the three tools most likely to produce an immediate visible result:

1. **Cascadeur 2026.1** — physically assisted hero-character animation;
2. **JangaFX IlluGen** — rapid VFX texture / flow-map / animated mask generation;
3. **Blender 5.2 LTS Geometry Nodes rhythm proceduralism** — both native audio-frequency sampling and a separate MIDI-event ingestion path.

The day is successful if it produces **three small Melodia-shaped proofs**, not if every tool is fully integrated.

> **One tool, one real project bottleneck, one measurable result.**

---

# Critical terminology: Blender audio is not MIDI

Blender 5.2's newly relevant native feature is **Sample Sound Frequencies** in Geometry Nodes. That reads frequency content from audio and makes it available to node-based procedural systems.

That is different from MIDI.

For Melodia we should deliberately test both lanes:

```text
A. MIDI lane
MIDI file / note events
    -> Python or small importer/parser
    -> note / velocity / channel / time attributes
    -> Geometry Nodes curves / points / instances / fields
    -> baked authored geometry / animation data

B. AUDIO lane
music / stem / rendered phrase
    -> Blender 5.2 Sample Sound Frequencies
    -> frequency bands / energy
    -> Geometry Nodes deformation / growth / scattering
    -> baked authored geometry / animation data
```

The **MIDI lane provides semantic musical events**. The **audio lane provides continuous spectral energy**.

Neither becomes Melodia's runtime rhythm authority. Unreal's existing rhythm systems remain authoritative at runtime. Blender is an **offline authoring / ideation / bake layer**.

---

# Working rules for today

- Work in disposable or duplicated test scenes/maps where possible.
- Do not enable experimental runtime plugins in the only production project copy.
- Record exact software version/build used.
- Record setup time separately from creative time.
- Save one screenshot/video per benchmark if useful.
- Prefer exports that become ordinary UE assets.
- Do not commit vendor binaries, example packs, proprietary sample content, or license-restricted source assets.
- Stop a test early if its claimed advantage is obviously not materializing.
- End each spike with **ADOPT / PARK / REJECT / WATCH**.

---

# Test 1 — Cascadeur 2026.1

## Question

Can Cascadeur substantially shorten the time required to make **grounded, expressive, physically convincing authored hero motion** for Melodia while preserving the UE skeleton/retarget pipeline?

## Primary benchmark: Mara Anchor Brace

Create a 3–5 second full-body animation in which Mara:

1. recognizes an incoming spatial/environmental force;
2. plants the Sounding Staff;
3. drops her center of mass;
4. braces through the rear leg and shoulder;
5. absorbs an impact/pulse;
6. settles while maintaining the Anchor.

This is a useful benchmark because it tests:
- weight;
- balance;
- planted contacts;
- staff interaction;
- anticipation;
- secondary recovery;
- a physically readable gameplay pose.

## Input

Use the closest available production-compatible humanoid skeleton/proxy. Do **not** remodel Mara for this spike.

Preferred iteration path:

```text
UE / production-compatible skeleton
        -> Cascadeur
        -> animation blockout + physical polish
        -> Live Link preview if stable
        -> FBX / normal UE animation import
        -> IK Retarget / Control Rig cleanup only as needed
```

## What to test

- AutoPosing / assisted posing usefulness;
- center-of-mass and trajectory tools;
- contact stability;
- penetration cleanup;
- root-motion control;
- staff hand/contact consistency;
- UE Live Link setup time and reliability;
- round-trip skeleton/bone naming behavior;
- how much UE cleanup remains after export.

## Optional second benchmark

If the Mara test finishes quickly, make one **Melusina traversal landing / balance-recovery** motion.

## Timebox

- Setup/import: 20–30 min
- Animation: 45–60 min
- UE round-trip: 20–30 min
- Decision notes: 10 min

## Pass condition

**ADOPT / integrate further** if:
- the physically convincing result is clearly faster than the existing Blender/UE loop;
- skeleton and root motion round-trip cleanly;
- contact cleanup is meaningfully easier;
- Cascadeur remains an authoring-only dependency.

## Park/reject triggers

- constant skeleton conversion friction;
- Live Link instability outweighs animation speed;
- result still needs essentially complete re-animation in UE/Blender;
- staff/contact workflows are more cumbersome than existing tools.

## Evidence naming

```text
cascadeur_mara_anchor_before_2026-08-30.*
cascadeur_mara_anchor_after_2026-08-30.*
cascadeur_mara_anchor_ue_roundtrip_2026-08-30.*
```

---

# Test 2 — JangaFX IlluGen

## Question

Can IlluGen make **production-useful animated VFX texture families** faster than the current Houdini/Copernicus/Substance route while exporting clean UE-friendly data?

## Primary benchmark: P3 Horizon Eater Filter Flow

Create a small texture family that communicates an impossible atmospheric current before the creature reveal.

Target outputs:
- directional flow map;
- low-frequency distortion map;
- high-frequency particulate breakup;
- streak/residue mask;
- optional animated flipbook or image sequence;
- optional normal/height-like supporting output if it improves the effect.

## Visual rule

It should look like **ordinary wind data that becomes biologically suspicious**, not a portal/glitch effect.

Candidate UE use:

```text
IlluGen flow/distortion data
        -> UE material function
        -> Niagara pollen / dust / seed advection
        -> subtle landscape/grass atmospheric response
        -> BP_HorizonEater_EncounterDirector parameters
```

Houdini remains authoritative for large-scale procedural fields where needed; IlluGen is being tested as the **fast beauty / VFX texture layer**.

## Secondary benchmark: Sea Above

If time remains, make one:
- upward water-flow texture;
- caustic/interference pattern;
- Bell pearl breakup mask.

## Timebox

- Install/orientation: 15–20 min
- P3 family: 35–45 min
- UE import/material test: 20–30 min
- Decision notes: 10 min

## Pass condition

**ADOPT / integrate further** if a reusable animated texture family reaches UE substantially faster than recreating the same idea in Houdini/COPs/Substance, without forcing an opaque runtime dependency.

## Reject triggers

- poor export control;
- awkward color-space/packing behavior;
- animated data is difficult to reproduce/version;
- little or no speed gain over existing tools;
- workflow encourages one-off vendor-format assets rather than ordinary UE textures.

## Evidence naming

```text
illugen_p3_filterflow_graph_2026-08-30.*
illugen_p3_filterflow_exports_2026-08-30.*
illugen_p3_filterflow_ue_2026-08-30.*
```

---

# Test 3 — Blender 5.2 LTS: MIDI + Sample Sound Frequencies

## Question

Can Blender become a **fast rhythm-to-procedural-geometry sketchpad** that complements the existing Houdini/Unreal rhythm pipeline rather than duplicating it?

## Benchmark A — MIDI semantic geometry

Use a short MIDI phrase and convert musical events into geometry attributes.

Minimum event schema:

```text
note
velocity
channel / track
start_time
end_time / duration
normalized_beat
```

Suggested mapping:

```text
X              = musical time / beat
Y              = pitch
radius          = velocity
curve length    = duration
material/ID     = channel or instrument
rotation/phase  = normalized beat or note class
```

Then build one useful Melodia visual from those attributes.

### Preferred first concept: Rhythm Garden / Runtime-Geometry Reference

Generate a compact procedural structure where:
- notes become stems / ribbons / coral-like filaments;
- chords become clusters;
- velocity controls bloom or thickness;
- duration controls extension;
- phrase structure creates macro silhouette.

The point is **not** to ship this node graph directly. The point is to determine whether MIDI can serve as an authoring language for environment forms that later become normal UE assets.

Other valid outputs:
- Tide Seam ribbons;
- P3 filter filaments;
- prayer-strip rhythms for P1;
- coral / shell growth families;
- runtime-geometry reference for the existing MIDI-driven ideas.

## Implementation boundary

Do not assume Blender has a new native MIDI Geometry Nodes reader.

If no existing project importer is available, create the smallest possible bridge:

```text
MIDI
 -> Python parse
 -> Geometry Nodes-readable points / curves / attributes
```

Do not spend the day building a general-purpose DAW inside Blender.

## Benchmark B — native audio-frequency geometry

Use Blender 5.2's **Sample Sound Frequencies** on the same phrase or its rendered audio.

Split into a few meaningful bands, for example:

```text
low      -> macro displacement / breathing
low-mid  -> width / structural response
mid      -> branching / instance density
high     -> shimmer / fine detail
```

Generate a second version of the same scene or asset using spectral energy rather than MIDI notes.

## The comparison we actually want

At the end, answer:

**What does MIDI do better?**
- exact note/chord structure;
- discrete gameplay-like rhythm events;
- repeatable authorial mapping.

**What does audio do better?**
- timbre;
- texture;
- continuous musical energy;
- expressive frequency-domain motion.

The likely long-term answer is a hybrid authoring workflow, not choosing one forever.

## UE handoff test

Bake/export one result as conventional data:
- static mesh;
- curve/spline source;
- vertex animation/cache if justified;
- point/attribute data convertible through Houdini;
- texture/field representation.

Then verify it can enter UE without Blender at runtime.

## Runtime authority guardrail

```text
Blender / MIDI / audio = offline authored source
Houdini                 = optional refinement / conversion
Unreal rhythm subsystem = runtime truth
```

Never create a second runtime beat clock or gameplay timing source from Blender output.

## Timebox

- MIDI ingest proof: 20–30 min
- Geometry Nodes mapping: 35–45 min
- Sample Sound Frequencies version: 30–40 min
- bake/export check: 15–20 min
- comparison notes: 10 min

## Pass condition

**ADOPT as a niche authoring accelerator** if:
- one phrase generates compelling editable geometry in under ~90 minutes;
- musical intent remains legible in the node graph;
- outputs bake/export cleanly;
- the workflow is substantially faster/more playful than constructing the same study in Houdini from scratch.

## Park/reject triggers

- MIDI bridge dominates the work;
- node graph becomes less readable than Houdini;
- exported data loses the useful semantics;
- audio-frequency response looks like generic equalizer art rather than authored worldbuilding.

## Evidence naming

```text
blender52_midi_geometry_2026-08-30.*
blender52_audiofreq_geometry_2026-08-30.*
blender52_midi_vs_audio_2026-08-30.*
```

---

# Recommended order for today

## Phase 0 — 15 minutes

- confirm clean project/research branch state;
- make local R&D folders;
- note exact installed versions;
- choose one short Melodia music/MIDI phrase;
- identify the humanoid skeleton/proxy for Cascadeur.

## Phase 1 — Cascadeur — ~90 minutes

Highest risk is skeleton/round-trip friction, so test it first while energy is high.

Deliverable:
**Mara Anchor Brace v0**.

## Phase 2 — IlluGen — ~60–75 minutes

Deliverable:
**P3 Filter Flow texture family v0**.

## Phase 3 — Blender rhythm proceduralism — ~90–120 minutes

Deliverables:
- MIDI-event procedural geometry v0;
- Sample Sound Frequencies procedural geometry v0;
- quick side-by-side comparison.

## Phase 4 — 30 minutes

For each tool record:

```text
Version/build:
Setup time:
Hands-on creation time:
Comparator workflow:
Best result:
Worst friction:
UE handoff:
Runtime dependency:
License/export concern:
Decision: ADOPT / PARK / REJECT / WATCH
Next action:
```

---

# Suggested local test asset organization

Do not commit empty folders; this is the intended structure once evidence exists.

```text
Docs/Research/Evidence/2026-08-30/
    Cascadeur/
    IlluGen/
    BlenderRhythm/

/Tools/RnD/Cascadeur/
/Tools/RnD/IlluGen/
/Tools/RnD/BlenderRhythm/
```

Only commit Melodia-owned evidence/source files that are appropriate for the repository.

---

# Integration decisions to make by end of day

## Cascadeur

Choose one:
- **ADOPT** as a normal humanoid motion authoring lane;
- **PARK** for only difficult physical shots;
- **REJECT** if round-trip friction overwhelms gains.

## IlluGen

Choose one:
- **ADOPT** for rapid VFX textures/flowmaps;
- **PARK** as occasional sketch software;
- **REJECT** if COPs/Substance already wins.

## Blender rhythm proceduralism

Choose separately:
- MIDI geometry: **ADOPT / PARK / REJECT**;
- Sample Sound Frequencies: **ADOPT / PARK / REJECT**.

Do not collapse these into one verdict.

---

# What comes next after these three

If today's first wave succeeds, the next highest-value spikes remain:
- Copernicus P2 matched material-state family;
- Unreal MCP controlled editor automation;
- UE5.8 Mesh Terrain + PCG impossible-terrain patch;
- MetaTailor wardrobe-fit test;
- FluidNinja P3 local field comparison;
- RealityScan -> Houdini -> stylized UE loop.

But those do **not** block today's work.

---

# Final doctrine

> **Cascadeur proves motion. IlluGen proves field appearance. Blender proves music can author form. Unreal remains the game.**
