# Melodia 3D Folio UI & Evergreen Scaffolding

**Date:** 2026-09-02  
**Status:** prototype architecture / non-authoritative runtime experiment  
**Prototype:** `Prototypes/Web/MelodiaFolio3D/`

---

## 1. Product intent

Melodia's long-term menu language should feel like a **Traveling Folio**: part scorebook, dressmaker pattern book, field journal, chart table, correspondence archive, and physical record of prior Voyages.

The UI should feel cozy and materially present without making ordinary navigation cumbersome.

The central rule is:

> 3D presentation objects may visualize state and emit intents. They never become new gameplay-state authorities.

---

## 2. Why Three.js exists in the pipeline

The Three.js prototype is an interaction/look-development laboratory for:

- tactile Folio page behavior;
- parcel/mail presentation;
- thread-based new-content navigation;
- 3D wardrobe/object inspection;
- repository asset preview;
- future web/spinoff experiments using engine-neutral Melodia contracts.

It is not a replacement for Unreal UI.

The browser implementation should intentionally mirror the eventual Unreal boundary:

```text
canonical durable state
        ↓
UI view model
        ↓
3D presentation surface
        ↓
raycast / pointer input
        ↓
FMelodiaUIIntent-shaped request
        ↓
UMelodiaUIBridgeSubsystem
        ↓
canonical Narrative / Wardrobe / Reward / Chapter authority
```

---

## 3. UI surface families

### A. Traveling Folio

Presentation-stage 3D book containing fast, legible 2D/UMG surfaces.

Suggested pages:

- Chapter Score / journey journal;
- Wardrobe pattern book;
- World chart;
- party/relationship portraits;
- creature field notes;
- music scorebook;
- Convergence tracing-paper overlays;
- Archive / travel stamps;
- correspondence.

### B. Starskiff Post

An in-world mailbox / parcel shelf that consumes the same Post view model as the Folio correspondence page.

The Starskiff becomes physical save-history presentation:

- opened letters persist visually;
- souvenirs/ornaments can appear after durable rewards;
- old Voyage materials can remain aboard;
- archived gifts remain discoverable.

### C. Screen-space critical UI

Keep high-frequency or accessibility-sensitive surfaces conventional:

- rhythm highway;
- combat command selection;
- accessibility settings;
- critical tooltips/status;
- confirmation/error dialogs.

Do not turn every menu action into a 3D navigation puzzle.

---

## 4. Thread navigation language

Replace generic notification clutter with a visual **Thread** system.

Working semantics:

- gold — gifts / relationship correspondence;
- lavender — Reveries / story;
- sakura — wardrobe;
- astral — world discovery / Voyage route.

Thread is presentation only. Every thread destination must also expose conventional accessible navigation and explicit New state.

---

## 5. Post / evergreen UI contract

The browser fixture `mailbox.json` sketches the minimum presentation contract.

A future native struct can follow the same shape:

```text
FMelodiaPostEntry
- EntryId
- EntryType
- DefinitionVersion
- SenderId
- Title
- Body
- PresentationKey
- RewardIds
- PrerequisiteIds
- ArchivePolicy
```

Provider architecture:

```text
             IMelodiaPostProvider
                 /          \
        Local Provider    Remote Provider
             now             later
                 \          /
              normalized entries
                     ↓
          Evergreen Content view model
                     ↓
          UMelodiaUIBridgeSubsystem
                     ↓
        Folio Post / Starskiff Post
```

The first production implementation should be **local-only**. Remote manifests are not required for the UI experiment.

---

## 6. Claim authority

The mailbox must never directly grant a reward.

Correct sequence:

```text
player opens parcel
    ↓
UI emits request with stable GiftId / EntryId
    ↓
canonical reward authority validates eligibility
    ↓
exactly-once IntentId is consumed
    ↓
Wardrobe / inventory / narrative authority mutates durable state
    ↓
save
    ↓
UI renders opened/claimed state from canonical data
```

This preserves the project's idempotency and single-writer rules.

---

## 7. 3D model strategy

Repository audit on 2026-09-02 found:

- no tracked `.glb` / `.gltf` assets in code search;
- 25 tracked `.obj` exports;
- 53 tracked `.fbx` files.

The Three.js prototype therefore supports:

- OBJ as the preferred **existing-repo preview lane**;
- FBX as a compatibility lane, with visible LFS failure reporting;
- GLTF/GLB already wired as the preferred future intentional web-export format.

Current verified seeds are declared in `Prototypes/Web/MelodiaFolio3D/models.json`.

### Future export policy

Do not mass-convert production assets for the web prototype.

Create deliberate GLB exports only when an asset becomes useful as:

- a Folio inspectable object;
- a Starskiff keepsake;
- a wardrobe preview;
- a web/spinoff asset;
- a public portfolio/showcase artifact.

Prefer one curated export manifest over another uncontrolled asset tree.

---

## 8. Model-viewer behavior

Every model entry should be:

- stable-ID addressed;
- source-path traceable;
- format-declared;
- auto-centered;
- auto-normalized to a known inspection volume;
- displayed using neutral fallback material when source material data is unavailable;
- safe to fail without breaking the Folio UI.

Model loading failure is presentation failure, not game-state failure.

---

## 9. Unreal mapping

Recommended native presentation stack:

```text
AMelodiaFolioActor
├─ Folio / page meshes
├─ ribbon / charm / parcel presentation meshes
├─ WidgetComponents for crisp UMG text/details where appropriate
└─ interaction targets
       ↓
UMelodiaUIBridgeSubsystem
       ↓
existing authorities
```

World-space Starskiff objects may use actors / WidgetComponents as presentation surfaces.

The Folio itself should behave like a controlled presentation stage rather than requiring the player to physically walk around an object for routine navigation.

---

## 10. Near-term implementation sequence

### UI-3D-01 — Browser proof — PRESENT

- Three.js Folio shell;
- raycast pages/thread/parcel;
- local mailbox fixture;
- repository OBJ/FBX model manifest;
- auto-fit turntable.

### UI-3D-02 — Intent contract

Author an engine-neutral `melodia.ui_intent.v1` schema and fixtures for:

- `ui.folio.chapter.selected`;
- `ui.wardrobe.inspect_requested`;
- `ui.post.open_requested`;
- `ui.post.claim_requested`;
- `ui.thread.follow_requested`;
- `ui.model.loaded` / `load_failed`.

### UI-3D-03 — Native Folio shell

Prototype one Unreal `AMelodiaFolioActor` and one presentation page routed through the existing UI bridge.

### UI-3D-04 — Post local provider

Create a local-only Post provider that feeds the Folio/Starskiff mailbox from authored data without any network dependency.

### UI-3D-05 — Canonical claim proof

One dev parcel:

```text
available
→ open
→ request claim
→ existing reward authority
→ save
→ process restart
→ remains claimed exactly once
```

Only after this works should remote content delivery be considered.

---

## 11. Non-goals

Do not:

- add a second HUD manager;
- let Three.js become gameplay authority;
- make remote services mandatory for base-game boot;
- build an HTTP/backend service before persistence closure;
- make 3D interaction the only accessibility path;
- mass-convert all FBX assets into web formats;
- let update UI directly mutate Wardrobe, inventory, quests, or save data.

---

## 12. Success condition

The system succeeds when Melodia can present a new letter, outfit, Chapter memory, or Voyage as a **physical-feeling object in the same cozy visual language**, while the underlying runtime remains boring, deterministic, versioned, idempotent, and safely offline-capable.
