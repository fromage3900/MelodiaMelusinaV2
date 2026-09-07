# Technical Data Flow — Melodia Melusina

**Last Updated:** 2026-09-02  
**Scope:** stable runtime/state lifecycle for an evergreen single-player game

---

## 1. Core lifecycle

Melodia no longer defines every Chapter by one identical six-phase sequence. The reusable data contract is instead:

```text
AUTHORED INTENT / WORLD ACTION
        ↓
appropriate runtime owner
        ↓
optional rhythm execution
        ↓
Wardrobe / Convergence interpretation
        ↓
world / combat / narrative consequence
        ↓
canonical durable fact
        ↓
save / restart / restore
```

Different content tiers can enter and leave this flow at different points.

---

## 2. Major data owners

### Narrative / progression
`UMelodiaNarrativeSubsystem` + QuillScript own durable narrative facts:

- quest/objective state;
- flags;
- stable intent consumption;
- reward consumption;
- checkpoints;
- authored consequences.

Repeated processing of the same stable intent must remain idempotent.

### TurnBased JRPG / Phoenix
Owns combat/gameplay facts it already controls:

- turn order;
- target selection;
- action resolution;
- party HP/MP/stats;
- inventory;
- terminal battle results;
- stock gameplay save state.

### Rhythm
Melodia rhythm receives an authored/selected action context and returns execution quality/performance data. It may influence result interpretation but does not directly create an independent combat transaction.

### Wardrobe
Wardrobe owns owned/equipped outfit state. Equipped identity can expose traversal capability and feed Convergence interpretation.

### Starskiff
Starskiff owns vehicle/traversal runtime state. Only stable long-term facts should enter canonical persistence; transient transforms/velocities should normally be rebuilt from checkpoints/authoring state.

### Convergence
Convergence reads durable/authoritative inputs and derives relationship state or authored response. Derived values should be recomputable unless there is a specific reason they must become durable facts.

---

## 3. Example: combat Chapter

```text
Quill/world encounter intent
        ↓
Phoenix command selection
        ↓
Melodia rhythm session
        ↓
grade / phrase quality
        ↓
Outfit + Convergence interpret execution
        ↓
Phoenix resolves authoritative action/result
        ↓
Quill receives terminal consequence once
        ↓
reward/checkpoint fact persisted
```

The current simple grade multipliers remain a baseline implementation. Future outfit/Convergence mechanics can change interpretation without bypassing the selected Phoenix action.

---

## 4. Example: non-combat Reverie

```text
Quill start
  ↓
exploration / interaction
  ↓
optional music phrase
  ↓
world-state consequence
  ↓
chapter/reverie checkpoint
  ↓
canonical save
```

No battle subsystem is required simply because the content is called a Chapter.

---

## 5. Example: Monolith Event

```text
durable chapter prerequisites
        ↓
authored world-state director
        ↓
traversal / party / rhythm / outfit signals
        ↓
Convergence interprets existing systems
        ↓
large-scale environmental transition
        ↓
permanent aftermath fact
        ↓
checkpoint / save
```

A Monolith Event does not require conventional enemy HP. Its state owner must still be explicit.

---

## 6. Save/restore contract

The long-term product depends on save records surviving years of new Chapters.

Preferred restore sequence:

```text
read bytes / slot
   ↓
identify version
   ↓
migrate candidate in memory
   ↓
validate intrinsic invariants
   ↓
validate subsystem-owned semantics
   ↓
commit authoritative restore
   ↓
rebuild derived runtime state
   ↓
verify no duplicate side effects
```

Hard rules:

- empty state is valid state;
- an existing save must not be treated as fresh merely because an inventory/outfit slot is empty;
- failed/corrupt candidate loads must not seed defaults over valid history;
- equipped persisted wardrobe IDs must be consistent with ownership before load mutation;
- repeat load must not duplicate rewards, modifiers, quest completion, or derived registrations;
- new schema fields require explicit version/migration behavior.

---

## 7. Durable vs derived state

Persist **facts**, not every runtime detail.

Good durable candidates:

- completed Chapter/Volume IDs;
- quest/checkpoint flags;
- claimed reward/Gift IDs;
- owned/equipped wardrobe IDs;
- major Convergence decisions;
- companion recruitment;
- permanent world-state consequences;
- stable Starskiff upgrades/decorations.

Usually derived/transient:

- active rhythm note instances;
- current timing windows;
- transient UI state;
- temporary VFX/MPC pulses;
- raw Starskiff rigid-body velocity;
- recomputable Convergence presentation values.

---

## 8. Future optional content manifest

Evergreen Gifts/Voyages may later use an optional online manifest, but online availability is not gameplay authority:

```text
optional manifest
   ↓
validate version/policy
   ↓
compare offered content IDs to local canonical history
   ↓
claim/download through existing content/reward paths
   ↓
record durable local fact
```

Network failure must not invalidate owned content or core gameplay.

---

## 9. Chapter package data flow

```text
progression spec
+ optional pillar manifests
+ Quill source
+ assets/maps
       ↓
offline validation
       ↓
runtime integration
       ↓
restart/idempotency proof
       ↓
packaged proof
       ↓
promote into Volume/Voyage
```

This is the scalable unit the project should optimize for.

---

## 10. Governing principle

> **New content extends the vocabulary of durable facts and authored relationships; it does not multiply state authorities.**
