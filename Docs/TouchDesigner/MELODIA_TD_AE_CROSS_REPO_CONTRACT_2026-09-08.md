# Melodia TouchDesigner / After Effects Cross-Repo Contract

> **MANDATORY CHORAL SHEEP AGENT CONTEXT:** Before changing Sheep visuals, materials, cymatics/Chladni, TouchDesigner, Geometry Nodes, or gameplay presentation, read `Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md`. **Board 06 + the two committed Sheep WebPs are the owner-approved visual lock, and the approved Nikki-derived Cymatics material MUST be used for final Sheep lookdev/P0 proof.** C++ owns gameplay truth; Blueprint/material/Niagara/TD present it. `collab/laptop/longterm` is the intentional parallel laptop Blender/Geometry Nodes lane: preserve it, never wholesale-merge it over current `main`, and promote useful GN work deliberately.


**Date:** 2026-09-08  
**Status:** ACTIVE  
**Game/runtime authority:** `fromage3900/MelodiaMelusinaV2`  
**TouchDesigner implementation:** `fromage3900/MelodiaTouchDesigner` (private), canonical working checkout `C:/MelodiaTouchDesigner/td/grandmaster_melodia/`  
**Historical/frozen TD mirror:** `fromage3900/EnvironmentPortfolio/_TouchDesigner/grandmaster_melodia/`  
**Presentation role:** concert visuals, editorial graphics, compositing, deterministic showcase passes, and live-performance lookdev

## 1. Decision

Keep the Unreal game and the TouchDesigner / After Effects presentation pipeline in **separate Git repositories**.

Do not:
- vendor the full TouchDesigner project into `MelodiaMelusinaV2`;
- convert the TD repo into a submodule;
- fork a second `grandmaster_melodia` inside the game repo;
- let TouchDesigner become gameplay or save-state authority.

The repos remain separate because they have different change rates, binary/externalization needs, tools, and production responsibilities.

The integration is explicit through a **small shared contract**, not repository nesting.

## 2. What each side owns

### MelodiaMelusinaV2 owns truth

Unreal / game repo owns:
- gameplay and companion state;
- pitch-class identity;
- Harmonize state;
- canonical rhythm / beat semantics;
- harmony and world-response truth where runtime implementation exists;
- cymatics / material presentation contracts;
- OSC route definitions;
- deterministic presentation replay schemas;
- capstone shot requirements and implementation claims;
- final UE beauty / utility renders.

TouchDesigner may **read** these meanings. It does not redefine them.

### grandmaster_melodia owns the visual instrument

The canonical TD repository owns:
- TouchDesigner networks and COMPs;
- Embody / TDN externalizations;
- live visual performance systems;
- harmonic-field and cymatic visualization;
- editorialized graphics and pitch glyphs;
- transparent render passes;
- concert-visual scale changes;
- deterministic replay playback;
- TD-specific capture/debug tooling;
- live OSC preview and performance lookdev.

### After Effects owns assembly

AE owns:
- final editorial timing;
- compositing UE + TD passes;
- typography / explanatory graphics;
- breakdown sequencing;
- selective finishing effects;
- delivery masters.

AE may explain the system. It does not invent gameplay or fake implementation proof.

## 3. Working mental model

```text
MelodiaMelusinaV2
  runtime / musical / companion truth
            |
            |  OSC + replay schema + shot contract
            v
grandmaster_melodia
  concert visual / graphic / harmonic-field instrument
            |
            |  transparent / editorial passes
            v
After Effects
  final composite / breakdown / showcase edit
```

Short version:

> **UE is the authored world. TD is the concert-visual instrument. AE assembles the argument.**

## 4. Existing bridge authority

Do not create a second bridge.

Current game-side authorities include:
- `deploy/osc_routing.json`;
- `UMelodiaRhythmReactivitySubsystem`;
- `UMelodiaAudioReactivePresentationSubsystem`;
- `UMelodiaCymaticsSubsystem`;
- `UMelodiaCymaticsWriterSubsystem`;
- `MPC_Melodia_Palette`;
- `MPC_Cymatics_Driver`;
- the existing TD↔UE OSC lane on **UDP 9000**.

The TD Envoy MCP on port **9870** is a tooling/control surface, not a replacement audiovisual signal route.

The current semantic principle remains:

> **one semantic music language, multiple execution contexts.**

## 5. Choral Sheep / Capstone 01

For Chladni Fleece, Gemini should mine `MelodiaMelusinaV2` for current truth, then implement the visual consumer in the canonical TD repo.

First sequence:

```text
one sheep / C
→ Harmonize
→ fleece field appears
→ clean decay

then

C → E → G
→ shared field becomes coherent
→ one world response
```

TouchDesigner should build:
- fleece masks;
- shared harmonic field;
- pitch constellation / glyph layers;
- world mask;
- transparent overlays;
- deterministic replay;
- debug views.

Unreal should remain responsible for:
- the actual sheep;
- fleece material integration;
- character animation;
- environment;
- camera;
- final world consequence;
- MRQ beauty.

## 6. Repository discovery rule

### Canonical working TD checkout

`C:/MelodiaTouchDesigner/td/grandmaster_melodia/`

This path was already documented when the project was moved out of the old EnvironmentPortfolio mirror.

### Frozen GitHub mirror

`fromage3900/EnvironmentPortfolio/_TouchDesigner/grandmaster_melodia/`

That copy is useful for:
- historical inspection;
- network archaeology;
- recovering prior scripts;
- understanding the pre-move project.

It is **not** where agents should implement new TD work unless the owner explicitly reactivates it.

The canonical TD Git remote is now verified as `fromage3900/MelodiaTouchDesigner` (private). The local checkout remains `C:/MelodiaTouchDesigner/td/grandmaster_melodia/`. Use that repo for new TD/AE implementation; do not revive the frozen EnvironmentPortfolio mirror.

## 7. Cross-repo handoff discipline

For a production take, record:

- MelodiaMelusinaV2 commit SHA;
- TD repo commit SHA;
- replay-schema version;
- take id;
- FPS / BPM;
- UE render source;
- TD pass names;
- AE comp/output name.

This gives reproducibility without submodules.

## 8. Gemini lane

Gemini may:
- read broadly from the main game repo;
- use the capstone docs to understand intended meaning;
- implement and polish the concert-visual/compositing pipeline in the canonical TD project;
- prepare AE assembly around real UE/TD inputs;
- create editorialized graphics and showcase passes.

Gemini should **not** spend time designing another orchestration architecture unless the current bridge is demonstrably insufficient.

The desired behavior is exactly what is already happening:

> **gather truth from the main Git, then use TD/AE to turn that truth into authored concert visuals, editorial graphics, composites, and showcase material.**

## 9. No-copy / no-submodule rule

Keep the repositories separate.

If a shared artifact is required:
- schema/contract authority lives in the game repo;
- TD may keep a pinned/generated consumer copy when useful;
- final take metadata records both commit SHAs.

Do not synchronize whole source trees across repos merely to make discovery easier.

## 10. Related current docs

- `Docs/Handoffs/GEMINI_TD_AE_CAPSTONE_HANDOFF_2026-09-08.md`
- `Docs/Semester/CHORAL_SHEEP_CAPSTONE_SHOWCASE_PLAN_2026-09-08.md`
- `Docs/Semester/CHORAL_SHEEP_CHLADNI_FLEECE_EXPERIMENT_2026-09-08.md`
- `Docs/Blender/MELODIA_MUSIC_SIGNAL_BRIDGE_TD_BLENDER_UNREAL_2026-08-30.md`
- `deploy/osc_routing.json`

The purpose of this document is not to add another system.

It exists so every agent knows **where to implement, where to read truth, and where not to duplicate work**.
