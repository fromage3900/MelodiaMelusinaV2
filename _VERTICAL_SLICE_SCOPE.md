# Active Vertical Slice Scope — First Dream / Sea Above Proof

**Last Updated:** 2026-09-02  
**Classification:** P0 runtime/integration proof, not full-game product scope

---

## 1. What this slice proves

The active slice exists to prove that Melodia's stable owners can complete a real player journey:

- Quill/narrative progression;
- exploration/world interaction;
- TurnBased JRPG/Phoenix combat;
- Melodia rhythm execution;
- Wardrobe gameplay/traversal consequence;
- reward/checkpoint state;
- canonical save/load;
- restart and idempotency closure.

The slice is the **first integration laboratory** for the long-term game.

It is not a rule that every future Chapter must contain exactly the same activities in exactly the same order.

---

## 2. Product scope lives elsewhere

Current product vision:

- `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`
- `Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md`
- `Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md`

Those documents define Volumes, Movements, Chapters, Episodes, Reveries, Monolith Events, Gifts, and Voyages.

This document defines **what P0 must prove before that broader production model is trusted**.

---

## 3. Current proof route

Canonical/current proof content is centered on:

- `L_MelusinaMorning` — sanctuary / narrative opening;
- First Dream / Kaleido Nave encounter path;
- Sea Above traversal/world interaction;
- Wardrobe/Resonant Weave gameplay proof;
- Choral Sheep/music relationship where included in the current convergence package;
- Starskiff integration surface;
- canonical checkpoint/save state.

Exact map packaging remains governed by the active build/golden-run specification, not by this prose summary.

---

## 4. Stable authority constraints

### Do not replace

- Phoenix / TurnBased JRPG combat-state ownership;
- canonical narrative/save ownership;
- Melodia rhythm execution seam;
- Wardrobe ownership;
- single-writer UI.

### Do not add for P0

- second combat framework;
- second SaveGame authority;
- mandatory online service;
- generalized live-service backend;
- broad new economy;
- another global rhythm/wardrobe/UI path.

---

## 5. P0 golden integration pattern

The current full-stack route can still be tested as:

```text
narrative initiation
      ↓
exploration / music-as-key
      ↓
turn-based encounter
      ↓
rhythm execution
      ↓
result / idempotent consequence
      ↓
wardrobe/world progression
      ↓
checkpoint / save
      ↓
restart / restore
```

This sequence is a **high-value golden test**, not a mandatory content template.

Future examples:

- a Reverie may use only narrative + exploration + save;
- a creature Chapter may use music/rhythm + world response without combat;
- a Monolith Event may use traversal + world-state transitions without enemy HP;
- a Starskiff Episode may use traversal + party state + checkpoint only.

---

## 6. Current closure acceptance

P0 is meaningfully closed when the player can complete the integrated route and the durable result survives:

1. save;
2. full process quit;
3. relaunch;
4. load;
5. exact durable-state restoration;
6. repeat load with no duplicated reward/modifier/quest/world effect;
7. packaged execution.

Source presence and offline tests alone are not enough for this final claim.

---

## 7. What happens after P0

The project graduates from proving systems to **authoring journeys with those systems**.

The next production milestone is not “invent Chapter 2's bespoke replacement architecture.” It is:

> **Author and ship another Chapter package using the same stable owners, restart-safe persistence, and validation contracts.**

That is the foundation required for a 50+ Chapter Volume and future Voyages.
