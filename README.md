# ♪ Melodia Melusina — an Evergreen Single-Player Rhythm-JRPG

![Melodia Banner](Docs/melodia-banner.svg)

![Unreal Engine 5.8](https://img.shields.io/badge/Unreal_Engine-5.8_%2B_C%2B%2B-informational?logo=unrealengine&logoColor=white&color=0a1929)
![Blender 5.2](https://img.shields.io/badge/Blender-5.2_LTS-critical?logo=blender&logoColor=white&color=e87d0d)

> **Product North Star:** Melodia is an emotionally complete single-player RPG that can keep growing into new Volumes, Voyages, Chapters, Reveries, outfits, creatures, gifts, and impossible places for years. It is not designed around a battle pass, mandatory daily engagement, or a fixed live-service cadence.

> **Core design thesis:** **the beautiful things are not rewards around the game — they are how the game is played.** Fashion, music, water, flora, ornament, ecology, and emotional resonance are gameplay substances.

## What Melodia is becoming

Melodia Melusina is a single-author / small-team **turn-based Rhythm-JRPG and explorable fantasy place** built in Unreal Engine 5.8.

Its stable gameplay skeleton is:

```text
Turn-based strategy      = the skeleton
Rhythm execution         = how actions are performed
Outfits / Wardrobe       = build identity + world relationship
Convergence              = the glue between systems
Starskiff                = traversal + persistent journey surface
QuillScript              = narrative progression authority
```

The current game already has a working Phoenix/TurnBased JRPG combat scaffold, a C++ rhythm layer with a battle-integrated note highway, wardrobe/traversal state, narrative progression, save/load infrastructure, Starskiff traversal work, music-as-key world interaction, and a reusable validation pipeline.

The long-term goal is **Game as a Place**: a finished journey that can later receive more journey without making its existing ending incomplete.

## Canonical strategy docs

Read these before proposing new global systems or restructuring Chapters:

1. [`Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`](Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md) — product vision, permanent vs renewable game, Volumes/Voyages, long-term save philosophy.
2. [`Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md`](Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md) — tiered Chapters, Episodes, Reveries, Movements, Monolith Events, and the working 50+ chapter Volume-I grid.
3. [`Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md`](Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md) — optional Gifts, Reveries, Voyages, no-FOMO default, Starskiff archive fantasy, future compatibility rules.
4. [`CURRENT_STATE.md`](CURRENT_STATE.md) — what is actually implemented/proven now.
5. [`TODO.md`](TODO.md) — current production priorities; strategy is not permission to skip runtime closure.

---

## Stable runtime architecture

Melodia's long-term extensibility depends on **not rewriting the working core every time a new Chapter arrives**.

### State and authority boundaries

- **TurnBased JRPG / Phoenix scaffold** owns turn order, targeting, action resolution, party stats, inventory, combat results, and the stock save/gameplay state it already controls.
- **`UMelodiaNarrativeSubsystem` + QuillScript** own narrative intents, flags, quest/checkpoint progression, consequences, and exactly-once narrative/reward consumption.
- **Melodia rhythm (`MelodiaCore` / `MelodiaRhythmCombatSubsystem`)** rides on top of selected JRPG actions. Rhythm performance modifies execution/result interpretation; it must not become a second combat authority.
- **`UMelodiaWardrobeSubsystem`** owns wardrobe/equipped state and exposes gameplay capabilities/identity.
- **Convergence** interprets relationships between outfit × rhythm/music × battle × traversal × world state. It should connect authorities, not duplicate them.
- **`UMelodiaUIBridgeSubsystem`** preserves single-writer UI ownership.
- **Starskiff** is both a traversal vehicle and a long-term candidate for physically accumulating the player's journey history.

### Runtime loop — flexible, not mandatory per Chapter

The P0 slice proves a useful full-stack chain:

```text
Quill / world intent
        ↓
Phoenix command / world action
        ↓
Melodia rhythm execution when appropriate
        ↓
Wardrobe + Convergence interpret result
        ↓
world / narrative consequence
        ↓
canonical durable state
        ↓
restart-safe restore
```

**Not every future Chapter must contain every box.** A Reverie may have no combat. A creature Episode may use rhythm without Phoenix. A Monolith Event may culminate in traversal and world-state intervention rather than enemy HP.

The reusable contract is **state ownership + chapter packaging + persistence + validation**, not identical pacing.

---

## Tiered content architecture

Melodia is now planned as a long-lived hierarchy rather than a finite sequence of equal-sized mega-chapters.

| Unit | Typical role |
|---|---|
| **Reverie / Interlude** | intimate 10–30 minute character, creature, outfit, Starskiff, or sanctuary story; heavy reuse |
| **Episode** | focused adventure with one strong gameplay proposition |
| **Chapter** | substantial authored unit with a persistent change; at most one major mechanical extension |
| **Movement** | thematic act that recombines existing systems into a new grammar |
| **Monolith Event** | rare assumption-breaking culmination earned by prior Chapters; not a routine boss slot |
| **Volume** | emotionally complete game-scale journey that can stand alone forever |

The working Volume-I grid allows **50+ named mainline Chapters**, but chapter size is intentionally variable. The goal is many memorable authored units, not 50 new subsystems.

### Working Movement arc

```text
Movement I  — The First Answer
Movement II — The World Reads Back
Movement III — The Category Error
Movement IV — The Shape We Choose
```

Current major tentpoles include First Dream / Sea Above, Shorewake, Mara and the Faraway Mother, God That Molts / Iris, Horizon Eater / Wayfold, the House of Measures / Seam Oracle, and the Last Dress of the Sea. Draft names beyond already canonized content remain owner-editable.

---

## Evergreen growth without the live-service treadmill

Future updates can be different sizes:

- **Gifts / Parcels** — letters, outfit pieces, music, materials, Starskiff ornaments, creature keepsakes.
- **Reveries** — small playable stories using existing systems.
- **Voyages** — larger new destinations, chapter groups, Movements, or full Volumes.

The default philosophy is **welcome back, not fear of missing out**. Gifts should normally remain claimable or move into an Archive. Core gameplay must not require a continuous server connection.

The ideal returning-player experience is:

> *A parcel arrived on the Starskiff while you were away.*

Long term, an old save should visibly accumulate history rather than merely accumulate a percentage-complete menu.

---

## Current production reality

The long-term vision does **not** change the immediate production rule: close and stabilize the core before widening content.

The 2026-09-01 P0 evidence baseline records a green core proof across the existing test/gate infrastructure. Treat those rows as bounded evidence for that captured baseline, not as permission to assume every future Chapter is shipping-ready.

Current high-value engineering work remains:

1. persistence/restore invariants and restart/idempotency proof;
2. clean ownership across Wardrobe → Convergence → Starskiff/world state;
3. a complete packaged golden path;
4. reusable Chapter package validation;
5. only then broad content production.

**Do not rewrite Phoenix, introduce a second save object, persist live rhythm sessions, or build remote-gift infrastructure before the local runtime is boringly reliable.**

---

## Toolchain philosophy

Core content production remains Unreal Engine 5.8 + Houdini + Blender 5.2 LTS + SpeedTree / Substance / supporting tools as appropriate.

Experimental pipelines are judged by one question:

> **Does this produce visibly better Melodia per hour without creating a more expensive maintenance system?**

The Musical World Compiler is an **offline authoring compiler**: music may author world anatomy, but Unreal/MelodiaCore remains runtime gameplay authority.

---

## Repository map

| Directory | Scope |
|---|---|
| `Source/BS_GodFile/` | native gameplay/integration systems |
| `Plugins/MelodiaCore/` | Melodia rhythm/gameplay presentation foundations |
| `Plugins/MelodiaWardrobe/` | wardrobe implementation |
| `Content/Melodia/` | characters, levels, UI, authored game content |
| `Content/EnvSandbox/` | environments, Monoliths, materials, procedural lookdev |
| `specs/` | progression, validation, content contracts, stable IDs |
| `Tools/` | build/test/audit/content-pipeline automation |
| `Docs/Strategy/` | canonical product/content strategy |
| `Docs/` | research, plans, handoffs, production evidence |

Bulk binary art remains intentionally governed by Git/LFS/Perforce policies documented elsewhere; code/specs/docs remain Git-authoritative.

---

## Quick start

See [`QUICKSTART.md`](QUICKSTART.md) for setup and validation commands.

The shortest contributor reading order is:

`README → Endless Journey North Star → CURRENT_STATE → TODO → SYSTEM_MAP → relevant chapter/spec`.

---

## License & provenance

Original repository source, tools, and configurations are MIT licensed; third-party assets retain their own licenses and provenance requirements.

- [`LICENSE`](LICENSE)
- [`Docs/CREDITS.md`](Docs/CREDITS.md)
- [`Docs/SOURCES_MATRIX.md`](Docs/SOURCES_MATRIX.md)

---

**Melodia is not a game that never ends because it withholds an ending. It is a journey that can keep finding new places after an ending.**
