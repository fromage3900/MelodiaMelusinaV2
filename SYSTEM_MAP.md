# System Architecture Map — Melodia Melusina

**Last Updated:** 2026-09-02  
**Target:** Unreal Engine 5.8 | Blender 5.2 LTS | C++20

---

## 1. Architecture principle

Melodia's long-term growth depends on **stable runtime ownership beneath renewable authored content**.

```text
                         RENEWABLE CONTENT
   Gifts / Reveries / Episodes / Chapters / Movements / Voyages / Volumes
                                      │
                                      ▼
                           CHAPTER PACKAGE LAYER
        stable IDs • progression specs • Quill • content manifests • tests
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           STABLE GAMEPLAY CORE                               │
│                                                                              │
│  Phoenix / TurnBased JRPG        Melodia rhythm execution                    │
│  turns • targets • results       timing • phrase quality • presentation     │
│               │                         │                                    │
│               └────────────┬────────────┘                                    │
│                            ▼                                                 │
│                  Wardrobe + Convergence                                      │
│           build identity • interpretation • world response                   │
│                            │                                                 │
│            ┌───────────────┼────────────────┐                                │
│            ▼               ▼                ▼                                │
│       Starskiff        World / Music       UI Bridge                         │
│       traversal        challenges          one writer/surface                │
│            └───────────────┬────────────────┘                                │
│                            ▼                                                 │
│           Narrative / canonical durable state                                │
│  Quill intents • flags • checkpoints • rewards • forward-compatible save    │
└──────────────────────────────────────────────────────────────────────────────┘
```

The core should become more stable as content grows. A new Voyage is normally a **content integration problem**, not an excuse to reopen combat/save/UI ownership.

---

## 2. System ownership

### TurnBased JRPG / Phoenix
Owns combat skeleton and stock gameplay state:

- turn order;
- targeting;
- action resolution;
- HP/MP/stats;
- party/inventory;
- terminal battle result;
- stock gameplay save state it already owns.

**Do not rebuild this in MelodiaCore.**

### Melodia rhythm
Owns rhythm/performance execution and presentation around an already selected action.

Current simple grade-to-damage behavior is a proven baseline, not the ceiling. Future Chapters may interpret rhythm through outfit/Convergence differently, but the selected JRPG action remains authoritative.

### Narrative / Quill
`UMelodiaNarrativeSubsystem` + QuillScript own:

- stable narrative intents;
- quest/objective flags;
- consequences;
- checkpoints;
- exactly-once reward consumption;
- content progression history.

### Wardrobe
`UMelodiaWardrobeSubsystem` owns owned/equipped wardrobe state and exposes mechanical capability/identity.

Outfits can affect:

- traversal;
- rhythm interpretation;
- battle affordances;
- creature/world relationships;
- Convergence response.

### Convergence
Convergence is an **interpretation layer**. It reads owner state and produces authored relationships. It must not become a duplicate inventory, quest log, battle manager, or second save authority.

### Starskiff
Starskiff owns vehicle/traversal behavior. Long-term, it may also be the fiction-facing presentation surface for accumulated journey history (parcels, souvenirs, companion objects), while durable ownership remains in canonical save state.

### UI Bridge
One writer per surface. New Chapters/Voyages may add screens but not parallel UI ownership.

---

## 3. Chapter package boundary

A future Chapter should arrive as data/content around the stable core:

```text
specs/progression/<chapter>.v1.json
+ optional wardrobe/world/encounter/audio manifests
+ Quill source if needed
+ stable IDs
+ authored maps/assets
+ offline tests
+ runtime/restart/package evidence
```

A Chapter may use only the systems it needs.

Examples:

- Reverie: Quill + exploration + save;
- creature Episode: rhythm + world interaction + consequence;
- combat Chapter: Phoenix + rhythm + Wardrobe/Convergence;
- Starskiff Chapter: traversal + party dialogue + world state;
- Monolith Event: authored world transitions + traversal, no conventional boss HP required.

The old six-phase P0 chain is a **full-stack integration pattern**, not a mandatory chapter script.

---

## 4. Long-term update boundary

Optional future online support belongs **outside** the stable gameplay core.

```text
optional remote manifest
        ↓
validated Gift/Voyage availability
        ↓
existing idempotent reward/content ownership path
        ↓
canonical local save history
```

If the network is unavailable, core game and owned content continue to work.

Do not put turn resolution, wardrobe ownership, narrative progression, or normal save/load behind a service dependency.

---

## 5. Production hierarchy

### Permanent systems
Phoenix, rhythm execution, Narrative, Wardrobe, Convergence seams, Starskiff traversal, UI ownership, persistence, chapter loader/validation.

### Renewable authored content
Chapters, Reveries, creatures, outfits, regions, Monolith Events, world puzzles, dialogue, Voyages, gifts.

When deciding whether to add code, ask:

> Can this be expressed as content using the stable owners we already have?

If yes, prefer that.

---

## 6. Current closure target

```text
Wardrobe
   ↓
Starskiff / exploration
   ↓
Phoenix action
   ↓
Rhythm execution
   ↓
Convergence / consequence
   ↓
checkpoint / reward
   ↓
canonical save
   ↓
full process restart
   ↓
restore exact durable state
   ↓
repeat load with no duplication
```

Closing this loop is more important than adding another global subsystem.

---

## 7. Strategy references

- `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`
- `Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md`
- `Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md`
- `CURRENT_STATE.md`
- `TODO.md`

**Architecture goal:** years from now, most new Melodia work should look like authoring a journey, not repairing the engine underneath it.
