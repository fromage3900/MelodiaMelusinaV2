# Melodia Bestiary — creature-design authority

**Status:** AUTHORING REFERENCE (not a runtime feature)  
**Updated:** 2026-10-26  
**Repository:** `fromage3900/MelodiaMelusinaV2`

## Purpose

One curated design index for Melodia Melusina's ecological and musical creatures: their identity, visual grammar, region, player relationship, encounter behavior, status, production boundaries, and source evidence. This bestiary is **not** permission to add enemies, companions, new gameplay verbs, or content scope.

**Design authority is not implementation proof.** An approved concept may lack an asset. A finished local asset may lack a verified versioned/runtime receipt.

## Canon and evidence vocabulary

| Label | Meaning |
|---|---|
| **CANON — APPROVED DESIGN** | Owner explicitly approved the creature's stated identity. Not evidence of a complete 3D asset or runtime encounter. |
| **VISUAL CANDIDATE** | A promising look, anatomy, ornament, or transformation idea requiring explicit final owner sign-off. |
| **RESEARCH CANDIDATE** | Brainstormed creature / ecological niche. Not a roster commitment. |
| **USER-REPORTED EXISTING** | Owner says an asset/build exists, but this pass did not locate a verified versioned proof. Preserve and audit; do not rebuild. |
| **SOURCE VERIFIED / LIVE PROVEN** | Narrow proof supported by a linked repo source or specific runtime evidence. Use the most precise proof available; never infer live gameplay from a script/spec. |
| **DEFERRED** | Interesting work deliberately not in the current production envelope. |
| **REJECTED / NON-CANON** | Not allowed to re-enter through generated art or an agent's assumption. |

An entry may carry separate **design status** and **implementation status**. New art does not silently change canon. If a generated sheet introduces anatomy, names, accessories, text, or gameplay, mark those details *visual candidate* until owner approval. No image-generation output is authoritative by itself.

## Region index

| Region / route | Creature | Design status | Implementation evidence | Entry |
|---|---|---|---|---|
| Faraway Mother (P1) | **Les Emmaillotés — The Swaddled** | **CANON — APPROVED DESIGN** (core); bear-form is a **VISUAL CANDIDATE** | Not verified as a cooked UE encounter | [Dedicated creature sheet](Creatures/LES_EMMAILLOTES.md) |
| Faraway Mother (P1) | Lace Wings; Méduses du Silence; Seam Eels; Bobbin Choir; Voilettes | RESEARCH CANDIDATES / selectively deferred | Not audited | [Regional ecology](Regions/FARAWAY_MOTHER.md) |
| Poitou / Melusina's Morning (P0) | Doily Moth | USER-REPORTED EXISTING; preserve | Local completion reported, no Git-verified output found in this pass | [Regional roster](Regions/POITOU.md) |
| Poitou / Melusina's Morning (P0) | Ganipote, Feux Follets, Frêne-Têtard, Beliche, eel, marsh bird | RESEARCH CANDIDATES | No new implementations authorized | [Regional roster](Regions/POITOU.md) |
| Existing cross-project motif creature | Choral Sheep | Established project creature | [Integration runbook](../CHORAL_SHEEP_INTEGRATION_RUNBOOK.md); **does not certify this session's PIE** | Future dedicated entry only if useful |

These are **index entries**, not a quota, spawn list, release promise, or evidence that all region designs have been committed.

## Canonical editorial entry contract

Use [CREATURE_ENTRY_TEMPLATE.md](CREATURE_ENTRY_TEMPLATE.md). Each record separates:

1. **Stable identity:** working ID, display name, region, pronouns/collective name, categorical relationship to the world.
2. **Approval ledger:** exactly what was approved; what is provisional; what is rejected; whose explicit decision can promote a candidate.
3. **Art-direction lock:** near/mid/far silhouette, values, materials, animation states and primary emotion; original reference versus generated depiction.
4. **Musical identity:** observable inputs / response / feedback using already-owned Melodia rhythm systems.
5. **Narrative ecology:** why the creature belongs in this specific region, and how the player responds.
6. **Build surface:** existing field/terrain/material/rig/PCG/UE owners to reuse; no invented system authority.
7. **Proof / QA:** asset existence, in-engine smoke, encounter behavior, screenshots, save/restart if relevant.
8. **Research provenance:** distinguish true regional folklore, sourced historical design inspiration, and original fiction.

## Relationship to the in-game Compendium

[Melodia Compendium Bible](../References/Narrative/MELODIA_COMPENDIUM_BIBLE.md) already defines the player-facing category **Motif Creature** and the runtime `FMelodiaCompendiumEntry` schema: `EntryId`, `Category`, `DisplayName`, `Subtitle`, `Summary`, `MusicalIdentity`, `FieldNote`, `Artwork`, `VoiceNote`, `UnlockFlagId`, `RelatedEntryIds`, and `Tags`.

This **Bestiary is an editorial/design reference**, not a second `SaveGame`, discoverability ledger, UI database, spawn registry, quest tracker, companion definition, or gameplay truth. When a creature earns an in-game entry, author **one** Motif Creature instance in the existing Persona/Compendium content authority. Let existing narrative flags govern discovery. Do not build a Bestiary screen for P0; the old first-slice UI plan explicitly deferred it.

## Chapter and scope guardrails

- **P0 Poitou:** Keep the authored Morning → House → Village → Canal golden walk bounded; no mandatory new combat or creature mechanic. See [Poitou golden walk](../Plans/POITOU_P0_GOLDEN_WALK_2026-10-21.md).
- **P1 Faraway Mother:** Fabric is geography; creatures reflect draped anatomy and a wounded musical field. Prefer nonviolent lull/retune responses. See [Faraway resonance integration spec](../Production/FARAWAY_MOTHER_P1_RESONANCE_FIELD_INTEGRATION_SPEC.md).
- **Character/reference boards:** Source materials are for art education, not evidence of historical monsters. Avoid literal infant anatomy and anthropomorphic doll replacements in the Faraway ecology.
- **Systems:** Reuse the existing PhraseBus, PCG spatial field, UE gameplay authority, Houdini/Hython offline forge, TD presentation lane, and existing material family. A bestiary entry adds no runtime framework.

## Next bounded editorial review

Owner approves or rejects **the bear-shaped visual candidate** for Les Emmaillotés, then chooses **one** proportion study and **one** three-state visual sheet (rest / partial unravel / comfort). Further creatures remain parked until their scene/story purpose is demonstrated.
