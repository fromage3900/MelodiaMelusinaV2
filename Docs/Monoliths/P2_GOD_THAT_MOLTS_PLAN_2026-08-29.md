# P2 Monolith Plan — The God That Molts

**Date:** 2026-08-29  
**Status:** preferred P2 direction; concept lock, not implementation lock  
**Core thesis:** **geology may be discarded biology.**

---

## Why this should follow Faraway Mother

The opening Monolith sequence should keep changing the category of nature being reinterpreted:

```text
P0 — Sea Above
water may be anatomy

P1 — Faraway Mother
fabric may be landscape / draped anatomy

P2 — The God That Molts
geology may be discarded biology
```

P2 should feel drier, earthier, more chemical, and more materially investigative than either P0 or P1.

The central realization:

> The valley is not built from the body of a dead god. It is littered with layers that something living has already shed.

This keeps the Monolith frightening without requiring a direct confrontation or a corpse reveal.

---

## Region fantasy

A forested ravine / amber-green basin where the player initially interprets enormous layered forms as:
- bark sheets;
- sedimentary rock;
- old shell deposits;
- translucent mineral strata;
- ruined walls;
- dried resin;
- fungal shelves;
- fossil-like plates.

The forms should be beautiful enough to support ordinary ecology:
- moss grows on them;
- roots pass through cracks;
- insects nest in them;
- water collects in old folds;
- people may have harvested fragments without understanding their origin.

The Monolith-scale horror is retrospective:

> All of this is shed material. The current body is somewhere else.

---

## Preferred character introduction — Iris Fen

**Status:** proposed / soft lock.

Iris should fill a role neither Melusina nor Mara owns.

```text
Melusina asks: What relationship is the world showing me?
Mara asks: What can be measured and stabilized?
Iris asks: What is this made of, and what state can it become?
```

Working role:
- field apothecary;
- ecological/material researcher;
- dye/reagent specialist;
- funerary botanist or residue-reader;
- practical collector of things other people call waste.

Visual direction:
- moss / amber / plum / smoke / oxidized metal;
- stained gloves and working apron or coat;
- translucent specimen pockets or reagent vessels;
- pressed plants / seed / shell / pigment motifs;
- less nautical than Mara;
- less couture-forward than Melusina;
- visibly comfortable handling unpleasant organic material.

Do not finalize her instrument, family history, or exact costume until P1 production scope is clearer.

---

## Proposed gameplay verb — Catalyze

**Catalyze** changes or exposes material state rather than dealing generic elemental damage.

Possible uses:
- accelerate a dormant reaction;
- reveal residue that would otherwise remain invisible;
- soften a hardened membrane;
- crystallize an unstable secretion into temporary footing;
- interrupt self-sealing material;
- expose pigment / mineral / tissue boundaries;
- create temporary traversal opportunities from byproducts;
- alter dyes/coatings/threads used by wardrobe systems.

This is a strong bridge between exploration, materials, and fashion without turning Iris into a generic alchemist class.

---

# Experience structure

## Beat 0 — A normal forest with strange strata

Begin with beauty and material specificity.

The player sees:
- broad bark-like sheets forming walls;
- translucent amber plates catching light;
- deep moss and fungal growth;
- old trails cut through “stone” layers;
- local people or field notes treating the material as a known regional resource.

Nothing needs to move.

---

## Beat 1 — Material inconsistencies

Small clues:
- “rock” curls when warmed;
- “bark” contains repeating layered fibers that do not match local trees;
- mineral-looking sheets retain flexible memory;
- fractures reveal pearl-like lamination instead of stone grain;
- old pieces react to moisture or rhythm.

Mara can measure them.
Melusina can sense relationships.
Neither necessarily knows what they are.

---

## Beat 2 — Iris demonstrates state change

Introduce Iris through competence.

She is already testing a fragment and can show that two apparently different regional materials are the same substance in different states.

Example:
- brittle chalk-like plate + reagent / heat / resonance → flexible translucent membrane;
- amber “resin” → reveals layered pigment cells;
- dry sheet → contracts slightly when rehydrated.

The player learns that the environment's categories are chemically unstable.

---

## Beat 3 — The layers repeat at impossible scale

The same micro-pattern found in a hand-sized fragment appears:
- in a cliff band;
- across a ravine wall;
- in a distant ridge;
- beneath a forest floor.

The scale relationship should be inferred, not announced.

A tiny specimen becomes the key to reading kilometers of terrain.

---

## Beat 4 — Ecological reuse

The region should not treat the shed material as evil.

Show ordinary life using it:
- fungi digesting outer layers;
- birds nesting in cavities;
- roots exploiting seam gaps;
- insects carrying flakes;
- human craft using safe fragments for dye, shell, insulation, or tools.

This matters to Melodia's worldview: Monolith horror and ecological beauty can coexist.

---

## Beat 5 — First undeniable biological proof

A supposedly dead layer responds to a condition:
- humidity;
- pressure;
- rhythm;
- Iris's reagent;
- nearby Monolith resonance.

The response should be small:
- contraction;
- opening pore;
- pigment migration;
- tiny fluid release;
- self-sealing edge.

The question becomes:

> If shed material still behaves like this, what did it come from?

---

## Beat 6 — Molt-field reveal

From a strong composition, the player realizes several “geological” formations correspond to nested discarded layers.

Possible visual logic:
- concentric old skins;
- repeated seam geometry;
- enormous split/opening where one layer was exited;
- younger material nested beneath older weathered strata;
- directionality that implies the absent body moved away.

Do not show the current creature.

The absence is the horror.

---

## Beat 7 — Current-body evidence

End with one clue that the organism is not extinct:
- a distant fresh layer not yet weathered;
- a warm pulse through the ground;
- newly shed translucent sheet somewhere impossible;
- migration trail;
- residue that is hours old rather than centuries old.

The player should understand:

> We are exploring what it outgrew.

---

# Rhythm integration

Rhythm should reveal material state and reaction timing.

Low accuracy:
- basic Catalyze interaction succeeds;
- clues remain broad.

Good accuracy:
- cleaner reaction;
- longer stable material state;
- optional traversal route;
- clearer residue pattern.

Perfect accuracy:
- temporary visibility of the repeated layer pattern across a much larger part of the environment;
- hidden pigment / pore / growth map;
- evidence of the most recent molt direction.

Principle remains:

> Better musical performance reveals more truth about the world.

---

# Material / shader direction

Core material family should feel distinct from water and cloth.

Useful layers:
- weathered outer crust;
- fibrous biological laminate;
- pearlescent inner membrane;
- amber/resinous secretion;
- fungal/ecological overgrowth;
- fresh wet edge only at selected hero reveals.

Working local parameters:

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

Avoid:
- red gore as the main read;
- generic zombie flesh;
- everything pulsing all the time;
- photoreal medical tissue;
- making every cliff visibly organic from the first shot.

The reveal only works if the material first succeeds as geology/bark/ruin.

---

# Technical architecture

P2 is too early to lock a large framework.

Preferred approach:
- local encounter/material director;
- authored material-state transitions;
- local MIDs;
- existing rhythm subsystem;
- simple interaction interfaces;
- decals/mesh swaps/parameter blends before runtime deformation systems.

Working local actor name:

```text
BP_GodThatMolts_EncounterDirector
```

Do not create:
- a project-wide chemistry simulation;
- procedural tissue-growth framework;
- new global MPC solely for P2;
- massive skeletal Monolith rig;
- generalized crafting system just to support one chapter proof.

---

# Production scope

Must-have P2 prototype:
- one forest/ravine material biome;
- Iris introduction beat;
- one hand-scale material test;
- one Catalyze interaction;
- one repeated micro-to-geographic pattern clue;
- one living-material confirmation;
- one molt-field reveal;
- one current-body evidence beat.

Nice-to-have:
- dye/coating reward for wardrobe;
- optional ecology side path;
- harvestable safe molt fragment;
- additional Mara/Iris scientific disagreement;
- hidden perfect-rhythm residue trail.

Cut first:
- combat;
- crafting framework;
- giant current-body reveal;
- gore escalation;
- procedural reaction simulation;
- multiple biomes;
- extra party character.

---

# Acceptance criteria

P2 succeeds if a player can summarize it as:

> “I thought the cliffs were old bark and mineral layers, then I realized the whole region was something's discarded skin — and it had molted recently.”

And if it proves:
- a third non-water Monolith category;
- Iris as a material-state specialist distinct from Mara and Melusina;
- ecology thriving on Monolith byproducts;
- horror through absence and scale rather than direct monster reveal;
- a meaningful bridge between materials and wardrobe progression.
