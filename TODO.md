# Melodia — Master Task Ledger

**Date:** 2026-09-02  
**Product lens:** evergreen single-player Rhythm-JRPG / game-as-a-place  
**Immediate phase:** runtime closure before broad content expansion

Canonical strategy:

- `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`
- `Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md`
- `Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md`

---

## P0 — preserve the proven core

The 2026-09-01 baseline records a green First Dream / Sea Above integration proof across the existing gate/test infrastructure. Keep that evidence intact, but treat it as a **captured baseline**, not as the definition of every future Chapter.

Do not reopen these foundations without a concrete defect:

- [x] TurnBased JRPG / Phoenix remains combat skeleton and gameplay-state authority.
- [x] Melodia rhythm layer rides on JRPG action execution rather than replacing it.
- [x] Narrative intents/rewards/checkpoints use canonical narrative state and exactly-once consumption.
- [x] Wardrobe can carry gameplay/traversal meaning.
- [x] Music can affect world-route state.
- [x] Single-writer UI discipline exists.
- [x] Reusable progression/spec/test infrastructure exists.

---

## P0.5 — runtime persistence closure (NOW)

Goal:

`Outfit → Starskiff/exploration → Phoenix action → rhythm execution → Convergence/world consequence → reward/checkpoint → SAVE → quit → relaunch → load → same state → load again → no duplication`

- [x] Audit existing load-result split; do not duplicate it with a second save framework.
- [x] Reject persisted equipped-cosmetic state that contradicts ownership before stock load mutation.
- [ ] Audit restore paths for partial mutation and duplicate rebuild side effects.
- [ ] Add candidate validation for remaining intrinsic narrative/save invariants.
- [ ] Keep Wardrobe-owned catalog/slot semantic validation in Wardrobe ownership.
- [ ] Add repeat-load/idempotency tests.
- [ ] Trace Starskiff state owner; classify durable facts vs derived/transient state.
- [ ] Trace Convergence state owner; classify durable facts vs derived/transient state.
- [ ] Extend save schema only after durable facts are agreed.
- [ ] Audit save-write sync/async behavior; add stale-write guard only if a real race is proven.
- [ ] Run full process-restart proof.
- [ ] Run packaged-build proof.

Non-goals:

- no Phoenix rewrite;
- no second SaveGame authority;
- no persisted live rhythm session;
- no raw transient Starskiff physics persistence without a design case;
- no Akuma/Embermere framework import.

---

## P1 — reusable Chapter production lane

Once runtime closure is green, prove that a **new Chapter package can be added without touching the core**.

- [ ] Define one canonical chapter-package authoring template from existing progression schema.
- [ ] Make Chapter tier explicit: Reverie / Episode / Chapter / Monolith Event.
- [ ] Require seven metadata fields: Narrative Question, Mechanical Focus, Character Focus, Location, Visual Signature, Persistent Change, Exit Image.
- [ ] Require stable IDs + idempotent intents/rewards + checkpoint/restore policy.
- [ ] Validate offline contract.
- [ ] Validate PIE/runtime behavior where applicable.
- [ ] Validate restart/load for durable state.
- [ ] Validate package/release promotion.

The old six-phase P0 loop becomes **one golden integration pattern**, not mandatory content pacing.

---

## Volume I — working long-term content order

### Movement I — The First Answer
- [ ] First Dream polish / canonical chapter packaging.
- [ ] Resonant Weave / outfit-as-gameplay proof.
- [ ] Choral Sheep / music-creature relationship.
- [ ] Sea Above Monolith Event.
- [ ] Shorewake calling and Starskiff departure.

### Movement II — The World Reads Back
- [ ] Mara Elletra Vell owner canonization pass.
- [ ] Seam Map / garment-semiotics chapter package.
- [ ] Hemlands / Pleated Range / Embroidered Basin production plan.
- [ ] Cymatic fabric-geography integration.
- [ ] Faraway Mother / The Blink Monolith Event.

### Movement III — The Category Error
- [ ] Iris Fen owner canonization pass.
- [ ] `Catalyze` as a narrow material-state/world-interaction verb using existing ownership.
- [ ] God That Molts formal progression package (currently a planning hole).
- [ ] Glasswing / Wayfold prototype and progression package.
- [ ] Horizon Eater progression renumbering and Event integration.

### Movement IV — The Shape We Choose
- [ ] House of Measures chapter family.
- [ ] Seam Oracle prototype: outfit silhouette × rhythm behavior × Convergence interpretation.
- [ ] `Refuse the Measure` constrained late-game outfit reinterpretation.
- [ ] Last Dress of the Sea world-scale synthesis.
- [ ] Homecoming / `The First Time She Is Not Late` epilogue.

The working planning grid supports **50+ named Chapters** across Volume I; exact chapter count/titles remain editable.

---

## Evergreen lane — design now, implement later

Do not build backend infrastructure yet. Preserve the architecture that makes it possible.

- [ ] Reserve globally stable content/reward ID discipline for future Gifts/Reveries/Voyages.
- [ ] Keep save schemas versioned and forward-migratable.
- [ ] Keep claimed rewards/intents idempotent forever.
- [ ] Design Starskiff mailbox/archive presentation only after local persistence is closed.
- [ ] Design optional remote content manifest after packaged single-player runtime is stable.
- [ ] Default future gifts to permanent/archiveable availability rather than FOMO expiry.
- [ ] Never make core combat/narrative dependent on an online service.

---

## Toolchain / R&D priority

Keep experiments subordinate to production:

**ADOPT / active:** Houdini + SpeedTree + UE5.8; Blender 5.2 LTS; existing Wardrobe/Rhythm/Starskiff pipelines.  
**TEST:** Musical World Compiler as offline authoring compiler; Walk on Surface; IlluGen residue; carefully bounded Blender XPBD/Cascadeur tests.  
**WATCH:** RTX neural material lanes, Magpie, GSplat/other niche tech until a concrete Melodia bottleneck exists.

Rule:

> **Does this produce visibly better Melodia per hour without creating a more expensive maintenance system?**

---

## Definition of progress

Prefer these outcomes over “more systems”:

- a restart-safe save;
- a repeat-load-safe reward;
- a Chapter that reuses existing owners;
- a returning location that reflects durable history;
- a Monolith Event that reinterprets existing mechanics;
- a new Voyage that old saves can enter without rebuilding prior content.

**The long-term goal is to spend more time authoring journeys and less time reopening the engine beneath them.**
