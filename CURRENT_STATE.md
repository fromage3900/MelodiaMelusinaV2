# Current State — Melodia Melusina

**Canonical implementation/status document**  
**Last Updated:** 2026-09-02  
**Target Engine:** Unreal Engine 5.8 | Blender 5.2 LTS | C++20 | Python 3.11

> Product vision is now defined separately in `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`. This file answers **what is implemented/proven now**, not what the full game may eventually contain.

---

## 1. Current production phase

Melodia is no longer a blank-slate prototype. It is in **runtime closure + reusable content architecture**:

- turn-based JRPG combat scaffold is working and remains the combat/state skeleton;
- Melodia's C++ rhythm note highway is tied into battle execution;
- narrative intent/checkpoint/reward state is integrated through the canonical narrative record;
- wardrobe ownership/equipped state and traversal hooks exist;
- Starskiff traversal/integration work exists;
- music-as-key/world challenge infrastructure exists;
- P0 / First Dream + Sea Above provides the current end-to-end proof surface;
- current engineering priority is making persistence/restore, repeat-load idempotency, world-state ownership, and packaged closure boringly reliable.

The next phase is **not another combat rewrite**. It is proving that existing systems survive complete journeys, restarts, new Chapters, and future schema growth.

---

## 2. Product paradigm now in force

Melodia is planned as an **evergreen single-player RPG / game-as-a-place**, not a finite ~12h commitment and not a compulsory live-service treadmill.

The long-term content hierarchy is:

`Volume → Movement → Chapter → Episode / Reverie`, with rare **Monolith Events** and optional later **Gifts / Reveries / Voyages**.

A Volume must have a real ending. Future content can extend the journey after that ending.

Canonical strategy:

- `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`
- `Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md`
- `Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md`

---

## 3. Stable authority model

### Combat / gameplay state
The existing TurnBased JRPG / Phoenix scaffold owns turn order, targeting, action resolution, party stats, inventory, combat results, and stock gameplay state.

### Narrative progression
`UMelodiaNarrativeSubsystem` + QuillScript own narrative progression, stable intents, quest/flag/checkpoint state, and exactly-once consumption.

### Rhythm
`MelodiaCore` / `MelodiaRhythmCombatSubsystem` executes timing/performance on top of selected JRPG actions. Rhythm may change action quality/interpretation; it must not become a parallel combat authority.

### Wardrobe
`UMelodiaWardrobeSubsystem` owns wardrobe/equipped state and exposes concrete gameplay relationships/capabilities. The long-term design target is outfit-as-build-identity, not cosmetic stat dressing.

### Convergence
Convergence is the glue between outfit × rhythm/music × battle × exploration × world response. It should interpret existing owner state rather than store duplicate truth.

### Starskiff
Starskiff is an exploration/traversal system under active integration and a long-term candidate for the physical archive of a player's accumulated journey.

### UI
Every surface retains one writer. UI duplication is a defect, not an alternate presentation path.

---

## 4. P0 evidence baseline

The 2026-09-01 closeout documentation records a green P0 automated/gate baseline, including the First Dream / Sea Above integration surface and existing test harnesses. Treat that as **bounded evidence for the captured baseline**, not as a claim that all future content is production-complete.

The important P0 proofs are architectural:

- full real-input gameplay chain exists;
- rhythm can ride on JRPG action execution;
- wardrobe can alter gameplay/traversal;
- narrative/rewards can be consumed idempotently;
- save/load infrastructure exists;
- music can unlock world routes;
- UI ownership can remain single-writer.

The P0 six-phase sequence remains a useful **golden integration test**, but it is no longer mandatory pacing for every future Chapter.

---

## 5. Current runtime-closure priority

The present closure target is:

```text
Outfit / Wardrobe
      ↓
Starskiff / exploration
      ↓
Phoenix command
      ↓
Melodia rhythm execution
      ↓
Convergence / world consequence
      ↓
reward / checkpoint
      ↓
SAVE
      ↓
quit process
      ↓
reload
      ↓
same durable state
      ↓
load again
      ↓
NO DUPLICATION
```

Key work:

1. validate complete save candidates before mutation where possible;
2. preserve intentional empty state;
3. reject inconsistent persisted wardrobe state before load mutation;
4. audit restore paths for partial mutation / duplicate rebuild side effects;
5. classify Starskiff and Convergence data into durable facts vs derived/transient state;
6. add schema fields only after ownership is stable;
7. prove full restart and repeat-load behavior;
8. prove packaged-build behavior.

Do not persist live rhythm sessions or raw transient vehicle physics unless a concrete design case requires it.

---

## 6. Content progression state

### Concrete / integration-ready direction
- First Dream / Sea Above P0 convergence content;
- Shorewake transition and Starskiff departure framing;
- Faraway Mother / fabric geography system preparation;
- reusable Chapter progression/spec validation infrastructure.

### Strong planned direction, still requiring canon/production passes
- Mara Elletra Vell / seam-reading;
- Iris Fen / material-state `Catalyze` lane;
- God That Molts;
- Horizon Eater / Wayfold;
- House of Measures / Seam Oracle;
- Last Dress of the Sea;
- working 50+ Chapter Volume-I grid.

Names and exact chapter placements beyond already owner-canonized material remain editable. The **tiered content architecture** is the important paradigm shift.

---

## 7. Long-term extensibility policy

New content should primarily add:

- authored places;
- chapter packages;
- outfits / interpretations;
- creatures / relationships;
- encounters;
- Quill narrative;
- world-state consequences;
- Monolith Events;
- optional gifts/reveries/voyages.

New content should **not** casually add:

- another combat framework;
- another save authority;
- another wardrobe subsystem;
- another global UI writer;
- another rhythm runtime authority;
- mandatory online dependency.

The goal is to make the permanent game stable enough that content production becomes the dominant work.

---

## 8. Current definition of “next level”

The project advances when it becomes easier to add a new Chapter without touching the core.

A meaningful milestone is not “another system exists.” It is:

> **A new authored Chapter can be packaged, played, saved, quit, restored, and revisited using stable owners and reusable contracts.**

That is the bridge from an impressive technical project into the long-lived Melodia journey.
