# P2 — God That Molts: Exploration Mechanics + UE 5.8 Implementation Research

**Date:** 2026-08-29  
**Status:** mechanics recommendation; implementation-soft-lock  
**Related:** `P2_GOD_THAT_MOLTS_PLAN_2026-08-29.md`, `Docs/Research/UE58_EXPLORATION_WORLD_BUILDING_RESEARCH_2026-08-29.md`

---

## Core playable thesis

P2 should not be a crafting/alchemy chapter.

It should teach the player that apparently different substances are **states of one discarded biological material**.

The main exploration loop is:

```text
Observe -> Compare -> Sample -> Catalyze -> Stabilize -> Traverse / Interpret
```

The fantasy is not “I cast acid on a wall.”

It is:

> “I learned what this landscape used to be, then temporarily returned a piece of it to another state.”

---

# 1. Party roles in the same object

A single hero molt fragment should support several viewpoints.

## Melusina — relationship

She reads relationships between apparently separate material formations.

Example:
- a hand-sized fragment and a cliff seam share a pulse/tide/ornamental rhythm;
- her outfit/hair reacts to a hidden continuity;
- good rhythm makes the repeated pattern easier to perceive.

Action family:
`Explore.Channel.Relationship`

## Mara — measurement

Mara proves repeatability:
- layer thickness;
- heat retention;
- contraction distance;
- pressure response;
- impossible consistency between distant formations.

Action family:
`Explore.Capability.Survey`

Her job is not to identify the organism; it is to prove that the anomaly is measurable.

## Iris — material state

Iris gets the chapter's new active verb:

`Explore.Capability.Catalyze`

She changes a material from one authored state to another.

Examples:
- brittle crust -> flexible membrane;
- opaque resin -> translucent pigmented layer;
- wet unstable secretion -> crystalline foothold;
- sealed seam -> temporarily reactive/open seam.

## Sir Melodious — resonance

He reveals whether apparently inert layers answer a call.

Use sparingly. His response should confirm life before the level says “living.”

## Ebenezer — tactile proof

A conure bite/scratch/weight test can produce a tiny local response:
- curl;
- bead of clear fluid;
- pigment retreat;
- self-seal.

This is a good optional beat, not a new system requirement.

---

# 2. Recommended interaction architecture

Do not create a global chemistry simulator.

Create one reusable exploration contract and let each P2 actor own authored reactions.

Suggested pieces:

```text
BPC_ExplorationInteractor
IExplorationTarget
FExplorationObservation
FExplorationActionRequest
FExplorationActionResult
```

Suggested tags:

```text
Explore.Clue.Material
Explore.Clue.LayerAge
Explore.Clue.Residue
Explore.Clue.BiologicalResponse

Explore.Capability.Survey
Explore.Capability.Catalyze
Explore.Capability.Anchor
Explore.Capability.ResonanceCall
Explore.Capability.TactileTest
```

The target should own:
- its MID references;
- local Niagara components;
- local sound parameters;
- local collision/traversal changes;
- its current authored state.

The global exploration layer should only answer **who can ask which question**.

---

# 3. Hero material-state prototype

Create one actor first:

```text
BP_MoltFragment_Prototype
```

State enum or StateTree:

```text
Dormant
Observed
Sampled
Catalyzing
Reactive
Stabilized
Spent
```

Recommended implementation:
- one static hero mesh;
- 2–3 material slots or material-layer masks;
- local MIDs;
- optional hidden alternate mesh for major silhouette change;
- one decal/overlay for fresh tissue edge;
- one Niagara component;
- one Audio Component / MetaSound source;
- optional traversal collision component activated only in stabilized state.

Do not start with runtime mesh deformation.

---

# 4. Material system

Use the existing Substrate/material pipeline and local parameters.

Core P2 parameters:

```text
Hydration
LayerAge
MoltReveal
PigmentMigration
ReactionProgress
MembraneFlex
PearlSheen
Freshness
CatalystStrength
```

Recommended authored state mapping:

```text
Dormant geology
  Hydration          0.05
  MoltReveal         0.00
  ReactionProgress   0.00
  Freshness          0.00

Catalyzed membrane
  Hydration          0.65
  MoltReveal         0.60
  ReactionProgress   0.75
  MembraneFlex       0.80

Fresh biological proof
  MoltReveal         1.00
  PigmentMigration   0.70
  PearlSheen         0.90
  Freshness          1.00
```

The important production rule is that the dormant state must first read convincingly as bark/mineral/ruin.

---

# 5. Catalyze should be authored, not systemic chemistry

Each target defines a small `CatalyzeProfile`:

```text
Catalyst requirement
Reaction duration
Rhythm sensitivity
Material target values
Traversal result
VFX result
Audio result
Reset / permanence policy
```

This can initially be a struct on the actor rather than a global Data Asset library.

Only create shared Catalyst Data Assets after multiple P2 targets need the exact same profile.

---

# 6. Rhythm integration

Reuse `UMelodiaRhythmReactivitySubsystem`.

Rhythm controls **quality of interpretation**, not whether Iris can perform basic science.

Suggested mapping:

```text
Low accuracy
  reaction succeeds
  short duration
  noisy/ambiguous material read

Good accuracy
  longer stable state
  optional traversal route
  clean pigment/residue pattern

Perfect accuracy
  broad micro-to-geographic pattern reveal
  most-recent molt direction becomes legible
```

Local encounter code reads existing rhythm signals and maps them to P2 presentation values.

Never fake `NotifyBeat` from the Monolith.

---

# 7. PCG for ecology, not reveal logic

UE 5.8 PCG is a strong fit for the region's ecology.

Use editor-time PCG to distribute:
- moss;
- fungus;
- roots;
- leaf litter;
- shed flakes;
- insect habitat proxies;
- harmless fragment resources.

Use surface/material attributes or authored spline/volume masks to avoid hero reveal areas.

The critical micro-pattern, living response, and current-body evidence remain hand-authored.

Do not make runtime PCG a P2 dependency.

---

# 8. Data Layers for one large reveal only

If P2 moves into a World Partition production map, Runtime Data Layers can handle a **large authored molt-state transition**.

Example:

```text
DL_P2_WeatheredStrata
DL_P2_RevealedNestedMolt
```

During the climax:
- preload the reveal layer;
- activate it during the authored event;
- keep local material transitions running on hero foreground meshes.

This is much cheaper and more controllable than deforming an entire ravine.

For a small prototype map, simple actor visibility/state switching is enough.

---

# 9. Geometry Script: use as art tooling

UE 5.8 marks Geometry Script Beta.

Good offline/editor uses:
- generate shell-layer offsets;
- cut repeated seam profiles;
- create fragment variants;
- build masks or sampling helpers;
- convert a hero molt surface into several weathering stages.

Do not ship the core reveal as runtime Geometry Script mesh surgery unless a later prototype proves it necessary.

---

# 10. Niagara and audio

## Niagara

Create or reuse a shared environmental Effect Type.

P2 VFX should communicate state transition with:
- very small spore release;
- condensation/wicking;
- translucent dust/flakes;
- pigment motes;
- one fresh-residue droplet event.

Avoid hundreds of independent ambient systems. Prefer a few regional systems plus local hero components.

## MetaSound / Audio Modulation

P2 needs material audio more than monster audio.

Parameters:

```text
Hydration
ReactionProgress
LayerAge
Freshness
MonolithResonance
```

Sound transformation:
- stone scrape -> fibrous creak;
- dry crack -> damp membrane tension;
- distant “earth tremor” -> slow living pressure pulse.

The current creature should remain mostly absent from the soundscape until the final clue.

---

# 11. Suggested prototype sequence

Build this in one small test ravine before expanding the region:

1. player finds one “rock” fragment;
2. Mara Survey returns repeatable unusual layer data;
3. Melusina alignment points toward a distant cliff with same pattern;
4. Iris Catalyze changes the hand fragment to flexible membrane;
5. local Niagara + MetaSound response sells biological state;
6. reaction creates a 10-second traversal foothold;
7. camera composition reveals the same seam pattern across the cliff;
8. perfect rhythm briefly highlights multiple nested molt layers;
9. a fresh distant fragment proves the organism molted recently.

If this works, P2 works.

---

# 12. Acceptance criteria

The mechanics pass succeeds if:
- Catalyze feels like material science, not elemental magic;
- the same object supports distinct Melusina/Mara/Iris readings;
- no global chemistry simulation is required;
- one authored state change produces traversal as well as narrative information;
- rhythm improves truth/clarity rather than gating completion;
- the landscape-scale reveal is sold with materials, composition, PCG ecology, and optional Data Layer swaps rather than a giant animated creature.
