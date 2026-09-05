# ♪ Melodia — what we are actually doing next

**Date:** 2026-09-02  
**Phase:** close the runtime → make Chapters cheap to add → grow the journey

> This is the production score, not the dream board. If something is beautiful but makes the core less reliable, it waits.

Canonical long-term direction:

- `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`
- `Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md`
- `Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md`

---

## 𝄞 NOW — close the song

Golden proof:

```text
Outfit
→ Starskiff / exploration
→ Phoenix action
→ rhythm execution
→ Convergence / world consequence
→ reward / checkpoint
→ SAVE
→ quit process
→ relaunch
→ same durable state
→ load again
→ no duplication / no drift
```

### Persistence / restore

- [x] Keep the existing load-result split; do not invent another save framework.
- [x] Reject equipped cosmetic state that contradicts owned cosmetic state before stock load mutation.
- [ ] Re-cut / transplant runtime-persistence work from stale PR #54 onto a fresh branch from current `main`.
- [ ] Audit `RestoreNarrativeRecord` / `RestoreNarrativeRecordFromSave` for partial mutation and duplicate rebuild side effects.
- [ ] Add remaining intrinsic candidate validation before canonical mutation where possible.
- [ ] Keep Wardrobe catalog / slot / authored semantic checks inside Wardrobe ownership.
- [ ] Add repeat-load equality + idempotency tests.
- [ ] Trace Starskiff ownership and write down **durable facts vs derived/transient state**.
- [ ] Trace Convergence ownership the same way.
- [ ] Extend the save schema only after those durable facts are locked.
- [ ] Audit sync/async save writes; add stale-write protection only if a real race is proven.
- [ ] Run full process restart proof.
- [ ] Run packaged-build proof.

### Hard no's while this is open

- no Phoenix rewrite;
- no second SaveGame authority;
- no persisted live rhythm session;
- no raw Starskiff physics snapshot unless design actually needs it;
- no imported Akuma / Embermere framework;
- no remote Gifts backend before local persistence is boringly reliable.

---

## ♫ NEXT — make a new Chapter boring to author

The project wins when a new Chapter mostly means **content**, not surgery on the engine.

- [ ] Lock one canonical Chapter-package template from the existing progression schema.
- [ ] Give each package a tier: Reverie / Episode / Chapter / Monolith Event.
- [ ] Require the seven useful authoring questions:
  - Narrative Question
  - Mechanical Focus
  - Character Focus
  - Location
  - Visual Signature
  - Persistent Change
  - Exit Image
- [ ] Require stable IDs + idempotent intents/rewards + checkpoint/restore policy.
- [ ] Validate the package offline.
- [ ] Validate runtime/PIE behavior where it matters.
- [ ] Validate restart/load for durable state.
- [ ] Validate package/release promotion.

The old P0 six-phase route stays as one great **integration song**. It is not a template every story has to obey.

---

## ♬ Volume I — the journey we can keep arranging

### Movement I — The First Answer

- [ ] First Dream polish + canonical package.
- [ ] Resonant Weave / outfit-as-gameplay proof.
- [ ] Choral Sheep / music-creature relationship.
- [ ] Sea Above Monolith Event.
- [ ] Shorewake calling + Starskiff departure.

### Movement II — The World Reads Back

- [ ] Mara Elletra Vell owner canonization pass.
- [ ] Seam Map / clothing-as-language package.
- [ ] Hemlands / Pleated Range / Embroidered Basin production plan.
- [ ] Cymatic fabric-geography integration.
- [ ] Faraway Mother / The Blink Monolith Event.

### Movement III — The Category Error

- [ ] Iris Fen owner canonization pass.
- [ ] Keep `Catalyze` narrow: material-state/world interaction, not another giant system.
- [ ] Create the missing **God That Molts** progression package.
- [ ] Reconcile Horizon Eater ordering after God That Molts.
- [ ] Prototype Glasswing / Wayfold with authored spatial tricks before generalized non-Euclidean tech.
- [ ] Horizon Eater Event integration.

### Movement IV — The Shape We Choose

- [ ] House of Measures chapter family.
- [ ] Seam Oracle: silhouette × rhythm behavior × Convergence interpretation.
- [ ] `Refuse the Measure` as constrained outfit reinterpretation, not free-form skill-editor sprawl.
- [ ] Last Dress of the Sea world-scale systems synthesis.
- [ ] Homecoming / `The First Time She Is Not Late`.

The 50+ Chapter grid is a **score we can rearrange**, not a legal contract with ourselves.

---

## ♪ Browser / UI / authoring playground

These are fast experiments. They are allowed to be weird because they are not allowed to become runtime authority.

- [x] Traveling Folio Three.js lab.
- [x] Mara-style Folio presentation variant.
- [x] MusicKey3D world-interaction sandbox.
- [x] **Cymatic Sanctuary** — 12-instrument Music-as-Key tool at `Docs/Tools/puzzle-sandbox/index.html`.
- [ ] Compare Cymatic Sanctuary against the native UE music-as-key contract and keep only useful schema ideas.
- [ ] Export one curated Melusina / Mara / Starskiff GLB for browser presentation instead of converting the whole asset library.
- [ ] Let Folio 3D widgets emit typed UI intents that map cleanly back to `UMelodiaUIBridgeSubsystem`.
- [ ] Keep future mailbox/Gift UI local-fixture-first until persistence closure passes.

---

## ♫ Git health — keep the repo from becoming archaeology again

- [ ] Refresh persistence closure from current `main`; do not merge stale PR #54 wholesale.
- [ ] Review PR #61 as a **large Wix/site snapshot**, not a tiny Three.js patch.
- [ ] Reconcile PR #61's shared Three.js r128 layer with the newer 0.185-era Folio/MusicKey prototypes before making it a common dependency.
- [ ] Treat giant old research PRs (#28 / #37 and similar) as extraction sources unless specifically refreshed.
- [ ] Keep human-owned maps/art isolated from automated mass merges.
- [ ] Keep new work in small fresh branches with one clear reason to exist.

---

## 𝄞 Evergreen lane — design the door now, build the server later

- [ ] Keep content / reward IDs globally stable.
- [ ] Keep save schemas versioned and migratable.
- [ ] Keep claimed intents / rewards exactly-once forever.
- [ ] Let the Starskiff mailbox/archive exist first as a local presentation contract.
- [ ] Design a remote manifest only after packaged single-player closure.
- [ ] Default future Gifts to permanent/archiveable instead of FOMO expiry.
- [ ] Never make combat or narrative depend on a network service.

---

## ♬ Toolchain rule

Active core: Unreal 5.8 · Houdini · Blender 5.2 LTS · SpeedTree · existing Wardrobe/Rhythm/Starskiff pipelines.

Test things when they have a Melodia-shaped problem to solve. Watch them when they do not.

> **Does this make visibly better Melodia per hour without creating a more expensive maintenance problem?**

That question outranks novelty.

---

## ♪ Definition of progress

I would rather leave a session with:

- one restart-safe save;
- one repeat-load-safe reward;
- one Chapter that reuses existing owners;
- one old location that remembers what happened there;
- one Monolith Event that reinterprets mechanics we already own;
- one new Voyage an old save can enter cleanly;

…than five more global systems with beautiful diagrams.

> **The goal is to spend more time making journeys and less time reopening the engine underneath them.** ♫
