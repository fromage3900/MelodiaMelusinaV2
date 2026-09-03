# Melodia — Evergreen Content & Gift Model

**Date:** 2026-09-02  
**Status:** CANONICAL LONG-TERM UPDATE MODEL  
**Companion:** `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`

---

## 1. Intent

Melodia may receive new content for years, but the base game remains a complete single-player RPG. The update model is designed for a solo/small-team creator who may add content whenever inspiration and production capacity allow.

This is **not** a commitment to continuous live operations.

---

## 2. Three update scales

### Gifts
Tiny additions delivered to an existing save.

Examples:
- outfit pieces / recolors already supported by shipped assets;
- letters;
- crafting/material rewards;
- music tracks or phrases;
- Starskiff ornaments;
- creature keepsakes;
- decorative sanctuary items.

Gifts should use a stable unique `GiftId`, be claimed idempotently, and normally remain available or move into an archive rather than expire.

### Reveries
Small downloadable playable additions, typically 10–30 minutes.

Examples:
- a Mara repair-night story on the Starskiff;
- Iris specimen/dye side story;
- Choral Sheep musical encounter;
- old-location revisit after a world-state change;
- outfit-specific short quest;
- quiet dream / sanctuary scene.

A Reverie should reuse existing systems and may omit combat entirely.

### Voyages
Large additions containing multiple Chapters, a Movement, a region, or a full new Volume.

A Voyage may add new assets and narrow mechanics but should still extend the stable core rather than fork it.

---

## 3. Lightweight online principle

Core gameplay and owned content must remain playable without a continuous server dependency.

Optional online services may expose a signed/versioned manifest describing available gifts or downloadable content. The runtime concept is:

```text
Game start / safe refresh
        ↓
Fetch optional content manifest
        ↓
Validate schema + version + signature/policy
        ↓
Compare offered GiftIds/VoyageIds with canonical claimed/installed IDs
        ↓
Surface parcel / letter / downloadable journey
        ↓
Claim through existing idempotent reward authority
        ↓
Persist canonical durable fact
```

If the service is unavailable, the game continues normally.

---

## 4. Gift contract

A future gift manifest should minimally express:

- stable `gift_id`;
- definition version;
- availability policy;
- reward intent / reward IDs;
- optional message / sender / presentation asset;
- prerequisites if any;
- archive behavior;
- minimum compatible save/schema version;
- content hash / package reference when external payload is required.

The claim path must use the same exactly-once principles as quest rewards. A gift refresh must never duplicate inventory, stats, wardrobe ownership, or persistent flags.

---

## 5. No-FOMO default

Preferred policy:

- gifts are permanent once published, or become archiveable;
- returning players can discover parcels that arrived while they were away;
- seasonal presentation may change without destroying reward eligibility;
- expiry is exceptional and must have a genuine design/legal/operational reason.

The emotional target is **welcome back**, not **you missed it**.

---

## 6. Starskiff mailbox / archive fantasy

The Starskiff is the preferred in-world presentation surface for evergreen updates.

Possible physical manifestations:

- mailbox / parcel shelf;
- chart table listing new Voyages;
- letters pinned in cabin space;
- souvenirs and ornaments appearing after claim;
- companion objects accumulating over time;
- an archive that preserves old messages and event gifts.

This lets update infrastructure reinforce the fiction instead of appearing as an external service menu.

---

## 7. Save-history model

Long-term content should query a bounded set of durable historical facts rather than branch on every past decision.

Examples:
- completed Chapter / Volume IDs;
- encountered/reconciled Monolith states;
- owned/equipped Resonant Weaves;
- recruited companions / creature relationships;
- claimed GiftIds;
- broad Convergence resolution flags;
- major world-state choices.

A future Voyage may acknowledge these facts with dialogue, environment dressing, optional routes, or small modifiers. It should not require combinatorial bespoke versions of every scene.

---

## 8. Compatibility rules

1. Old saves remain first-class.
2. Missing new fields migrate to explicit defaults without overwriting valid old state.
3. Empty state is valid state; do not infer “fresh player” from an empty inventory/wardrobe slot.
4. Failed/corrupt loads do not seed new defaults over an existing save.
5. New content IDs are globally stable once released.
6. Claimed reward/gift intents remain idempotent forever.
7. Old Chapters are not rewritten to require newly released mechanics.
8. Removing published durable IDs requires a migration plan, not a rename-and-forget edit.

---

## 9. Release cadence

There is no required cadence.

Healthy examples:

- one gift when a new outfit is finished;
- three Reveries over a year;
- no update for six months;
- one large Voyage after a long production cycle;
- a surprise letter tied to a real-world date;
- a full new Volume years later.

The architecture serves the creator's pace, not the reverse.

---

## 10. Product language

Prefer Melodia-native terms:

- **Volume** — major complete journey;
- **Movement** — thematic act;
- **Chapter** — named mainline content unit;
- **Reverie** — small intimate playable update;
- **Gift / Parcel** — lightweight reward;
- **Voyage** — substantial new destination/content release;
- **Archive** — persistent record of past gifts/messages.

Avoid positioning the project around “seasons,” “battle passes,” “daily rewards,” or “content drops” unless a specific future product decision intentionally changes this model.

---

## 11. Near-term implementation policy

Do **not** build remote gift infrastructure before runtime persistence closure and Volume I chapter packaging are stable.

Near-term work should only make the future model possible:

- keep stable ID and idempotency discipline;
- version canonical save records;
- distinguish durable facts from derived/transient state;
- keep chapter content package-driven;
- preserve Starskiff as a potential persistent-history surface;
- keep optional online concerns outside core combat/narrative authority.

Evergreen support is a product architecture decision today and a networking/backend implementation task later.
