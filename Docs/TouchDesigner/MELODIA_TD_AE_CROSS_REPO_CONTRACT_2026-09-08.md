# Melodia TouchDesigner / After Effects Cross-Repo Contract

**Status:** CANONICAL DURABLE INTEGRATION CONTRACT  
**Game/runtime authority:** `fromage3900/MelodiaMelusinaV2`  
**TouchDesigner implementation:** `fromage3900/MelodiaTouchDesigner`  
**Historical TD mirror:** `fromage3900/EnvironmentPortfolio/_TouchDesigner/grandmaster_melodia/`

**For current TD/AE tasks, blockers, proof state, or capstone priority, read `CURRENT_STATE.md`.** This file defines boundaries and handoff rules only.

## 1. Decision

Keep the Unreal game and TouchDesigner / After Effects presentation pipeline in **separate Git repositories**.

Do not vendor the full TD project into `MelodiaMelusinaV2`, create a second `grandmaster_melodia`, or let TouchDesigner become gameplay/save authority.

The repos integrate through small explicit signal/replay contracts, not repository nesting.

## 2. Ownership

### MelodiaMelusinaV2 owns truth

The game repo owns:

- gameplay and companion state;
- pitch-class identity and Harmonize state;
- canonical rhythm / beat semantics;
- harmony/world-response truth where runtime implementation exists;
- cymatics/material presentation contracts;
- OSC route definitions;
- deterministic replay schemas;
- capstone implementation evidence;
- final UE beauty / utility renders.

TouchDesigner may read these meanings. It does not redefine them.

### MelodiaTouchDesigner owns the visual instrument

The TD repo owns:

- TouchDesigner networks and COMPs;
- live visual performance systems;
- harmonic-field / cymatic visualization;
- editorial graphics and pitch glyphs;
- transparent render passes;
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

AE may explain the system. It must not invent gameplay or fake implementation proof.

## 3. Mental model

```text
MelodiaMelusinaV2
  runtime / musical / companion truth
            |
            |  OSC + replay schema + shot contract
            v
MelodiaTouchDesigner
  concert visual / graphic / harmonic-field instrument
            |
            |  transparent / editorial passes
            v
After Effects
  final composite / breakdown / showcase edit
```

> **UE is the authored world. TD is the visual instrument. AE assembles the argument.**

## 4. Existing bridge authority

Do not create a second bridge.

Game-side authorities include:

- `deploy/osc_routing.json`;
- `UMelodiaRhythmReactivitySubsystem`;
- `UMelodiaAudioReactivePresentationSubsystem`;
- `UMelodiaCymaticsSubsystem`;
- `UMelodiaCymaticsWriterSubsystem`;
- `MPC_Melodia_Palette`;
- `MPC_Cymatics_Driver`;
- the existing game <-> TD semantic OSC lane on UDP `:9000`.

The TD Envoy/MCP control surface is tooling, not a replacement audiovisual signal route.

Durable principle:

> **one semantic music language, multiple execution contexts.**

## 5. Choral Sheep usage

Choral Sheep / Chladni Fleece is a consumer of the existing architecture, not a new bridge.

Durable Sheep context: `Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md`.

Unreal owns the actual Sheep, approved Nikki-derived material integration, animation, environment, camera, and gameplay/world consequence. TD may visualize pitch/harmony/cymatics and produce deterministic or transparent presentation passes.

The capstone presentation spine remains:

```text
Creature -> Motif -> Harmony -> World
```

Current milestone order belongs in `CURRENT_STATE.md`, not here.

## 6. Repository discovery

Canonical TD working checkout:

```text
C:/MelodiaTouchDesigner/td/grandmaster_melodia/
```

Canonical remote:

```text
fromage3900/MelodiaTouchDesigner
```

Frozen historical mirror:

```text
fromage3900/EnvironmentPortfolio/_TouchDesigner/grandmaster_melodia/
```

The mirror is useful for archaeology/recovery only. Do not implement new work there unless explicitly reactivated by the owner.

## 7. Cross-repo handoff discipline

For a production take, record:

- MelodiaMelusinaV2 commit SHA;
- TD repo commit SHA;
- replay-schema version;
- take id;
- FPS / BPM where relevant;
- UE render source;
- TD pass names;
- AE comp/output name.

This gives reproducibility without submodules.

## 8. Agent rules

An agent working in TD/AE should:

- read `CURRENT_STATE.md` for present priorities;
- gather semantic truth from the game repo;
- implement presentation in the canonical TD repo;
- prepare AE assembly around real UE/TD inputs;
- reuse existing OSC/music semantics;
- report session findings in the task/PR/commit context rather than creating new handoff/status docs.

It should not design another orchestration architecture unless the existing bridge is demonstrably insufficient.

## 9. Shared-artifact rule

If a shared artifact is required:

- schema/contract authority lives in the game repo;
- TD may keep a pinned/generated consumer copy when useful;
- final take metadata records both commit SHAs.

Do not synchronize whole source trees across repos merely to make discovery easier.
