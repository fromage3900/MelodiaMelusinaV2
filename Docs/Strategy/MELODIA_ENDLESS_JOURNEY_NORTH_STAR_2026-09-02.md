# Melodia — Endless Journey North Star

**Date:** 2026-09-02  
**Status:** CANONICAL PRODUCT VISION  
**Supersedes as product framing:** the finite ~12h / four-movement assumption in `Docs/FULL_GAME_LOOSE_SCOPE_2026-07-31.md` and the claim that every chapter must execute one identical six-phase loop.  
**Does not supersede:** runtime authority, save ownership, P0 evidence, or validated subsystem boundaries.

---

## 1. Product thesis

Melodia Melusina is an **evergreen single-player Rhythm-JRPG and explorable fantasy place** that can grow for years without requiring the original journey to remain unfinished.

The game is not a treadmill, battle-pass service, MMO, or obligation to publish on a fixed cadence.

The governing promise is:

> **There will sometimes be more journey. There will never need to be more journey.**

Every major Volume must reach an emotionally complete ending. Future Volumes, Voyages, Reveries, gifts, creatures, outfits, and regions may extend the player's history without invalidating that ending.

---

## 2. The permanent game

The permanent runtime should become increasingly boring, stable, and reusable:

- Phoenix / TurnBased JRPG remains the turn, targeting, damage, result, party, inventory, and stock save authority.
- `MelodiaCore` / rhythm presentation remains the execution layer riding on top of authored JRPG actions, not a second combat authority.
- `UMelodiaNarrativeSubsystem` + QuillScript own narrative intents, flags, checkpoints, consequences, and chapter progression.
- `UMelodiaWardrobeSubsystem` owns wardrobe state; outfits are build identity and world relationship, not stat-only cosmetics.
- Convergence is the interpretation layer connecting outfit × music/rhythm × battle × exploration × world response.
- Starskiff is a persistent journey/hub/traversal surface that can accumulate visible history.
- UI remains single-writer per surface.
- Canonical persistence must be forward-compatible and idempotent across years of content additions.

**Do not rebuild these systems every Volume.** New content should primarily recombine, reinterpret, and extend their vocabulary.

---

## 3. The renewable game

The long-term authored surface is intentionally expandable:

- new Chapters and Episodes;
- short Reveries and companion stories;
- outfit stories and Resonant Weaves;
- Starskiff encounters and decorations;
- creatures and ecological relationships;
- Monolith Events;
- new regions / seas / dreams;
- musical world puzzles;
- optional gifts, letters, materials, cosmetics, and archival rewards;
- new Voyages / Volumes using the same stable core.

The beautiful things are not rewards around the game. **They are how the game is played.** Fashion, music, flora, water, ornament, ritual, ecology, and emotional resonance are gameplay substances.

---

## 4. Release structure

### Volume
A major emotionally complete journey. A Volume may contain multiple Movements and many Chapters. Finishing a Volume must feel like finishing a real RPG even if no future update is ever made.

### Movement
A major thematic act that permanently changes the player's understanding of Melodia. Movements contain multiple Chapters and normally culminate in a reality-reinterpreting event.

### Chapter
A named authored unit with a clear question, mechanical focus, character focus, location, visual signature, persistent change, and exit image. Chapters are deliberately variable in size.

### Episode
A compact adventure or problem inside a Chapter/Movement. Usually one strong gameplay proposition and heavy reuse of existing systems.

### Reverie / Interlude
A small intimate unit: character time, Starskiff life, outfit story, creature interaction, sanctuary return, or low-stakes exploration. Often no combat and no new mechanics.

### Monolith Event
A rare culmination, not a routine boss slot. A Monolith Event spends prior Chapters earning one assumption-breaking reinterpretation of reality.

---

## 5. Volume I working arc

Volume I is currently organized around four Movements and a long-form chapter architecture rather than a hard eight-chapter cap.

### Movement I — The First Answer
Intimacy → resonance → first departure.  
Tentpoles: First Dream, Resonant Weave, Choral Sheep, Sea Above, Shorewake, Starskiff departure.

### Movement II — The World Reads Back
Fashion becomes language; landscape begins to interpret the player.  
Tentpoles: Mara Elletra Vell, Seam Map, Hemlands, cymatic fabric geography, Faraway Mother / The Blink.

### Movement III — The Category Error
Matter and space stop obeying familiar categories.  
Tentpoles: Iris Fen, Catalyze, God That Molts, Glasswing / Wayfold, Horizon Eater.

### Movement IV — The Shape We Choose
The threat becomes personal rather than merely larger. Identity, interpretation, and Convergence become the late-game synthesis.  
Tentpoles: House of Measures, Seam Oracle, Refuse the Measure, Last Dress of the Sea, homecoming.

The exact chapter count is intentionally elastic. **50+ mainline named chapters is acceptable** if chapter size stays tiered and the majority reuse existing systems.

---

## 6. Evergreen update model

Melodia can receive optional updates without becoming a manipulative live-service game.

### Gifts
Small account/save-visible parcels: letters, materials, cosmetics, outfit pieces, music, Starskiff decorations. Prefer permanent or archiveable availability over FOMO expiration.

### Reveries
10–30 minute downloadable stories or encounters using existing systems and locations where possible.

### Voyages
Large content additions: new regions, chapter groups, Movements, or full Volumes.

The preferred player experience after returning months or years later is:

> **Something arrived while you were away.**

Not:

> Log in before Tuesday or lose it forever.

---

## 7. Starskiff as accumulated history

The Starskiff should gradually become a physical record of the save's journey:

- gifts and ornaments remain visible;
- companion objects accumulate;
- old chapter trophies become set dressing;
- letters remain readable;
- creatures may revisit;
- later content may recognize durable historical facts without branching the entire plot.

Long-term persistence should favor **stable historical facts** over transient runtime state.

---

## 8. Long-term persistence rule

> **New content may extend the canonical state vocabulary, but must not require rebuilding old Chapters.**

Old content is historical strata. Schema migrations must preserve prior saves; rewards and chapter intents must be idempotent; existing empty/unequipped state is authoritative; a failed load must never seed defaults over valid history.

This makes the current runtime-persistence closure work foundational to the long-term product, not merely P0 cleanup.

---

## 9. Anti-live-service guardrails

Do not make Melodia depend on:

- mandatory daily login loops;
- battle passes;
- ranked/competitive integrity;
- server-authoritative core gameplay;
- aggressive rotating shops;
- frequent reward expiry;
- an update cadence the creator must continuously feed;
- old chapters becoming unusable when a new Voyage ships.

Online infrastructure should be lightweight and optional to the core single-player game.

---

## 10. Definition of success

A new player can complete a satisfying Volume.  
A returning player can discover that the place has grown.  
A five-year player can look around the Starskiff and see a history that belongs to their save.  
The creator can add one tiny gift or an entire new Voyage without rewriting the combat, narrative, wardrobe, or persistence foundations.

**Melodia is not a game that never ends because it withholds an ending. It is a journey that can keep finding new places after an ending.**
