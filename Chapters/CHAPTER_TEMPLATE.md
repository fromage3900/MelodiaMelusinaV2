# Chapter bible template — copy to Chapters/NN_name/ and fill

World-building authority: `Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`.
Tier / seven fields: `Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md`.
Validation sequence: `Docs/Plans/REUSABLE_CHAPTER_VALIDATION_SYSTEM_2026-08-31.md`.

Rule that keeps authorities safe: a chapter adds DATA only
(qsc, allowlist delta previewed in encounters.json, PPV weight shifts, meshes,
outfits, songs, PCG). If a chapter seems to need code or a new subsystem, stop —
that is a defect signal per the golden-run exit criterion #6.

First Dream's six-phase route is the **integration proof**. It is not a template
every story must obey. Name the loop stages this chapter actually uses.

Required answers in CHAPTER.md (fill before other files):

1. **Tier** — Reverie / Episode / Chapter / Movement / Monolith Event.
2. **Seven metadata fields**
   - Narrative Question
   - Mechanical Focus
   - Character Focus
   - Location
   - Visual Signature
   - Persistent Change
   - Exit Image
3. **Player-loop stages used** — subset of:
   Player Input, Overworld Traversal, Interaction & Triggers, Narrative Layer,
   Capability / Instrument Unlocks, Encounter Decision, Combat Setup,
   Rhythm / Turn Resolution, Post-Combat Resolution, Progression & Checkpoint,
   Return to World.
4. **C++ owners touched** — subset of Narrative/Quill, Phoenix/JRPG, rhythm,
   Wardrobe, Starskiff, Convergence, UI Bridge, canonical save.
5. **Chladni / TouchDesigner** — presentation-only for this chapter unless a
   named runtime owner already drives the semantic (pitch, Harmonize, world
   response). TD must not own save, quest, combat, or traversal truth.

Files per chapter:
- CHAPTER.md       logline, tier, seven fields, loop stages, C++ owners,
                   Chladni/TD boundary, emotional movement, feeling-arc, route
                   table, beats, encounter, assets, score, lookdev tiers, exit
                   criteria
- route.md         maps + travel edges + which trigger actor lives where (names,
                   not labels — manage_sublevel takes names, rule 23)
- quill/*.qsc      scripts; 7 verbs only; no unallowlisted id is ever emitted
- encounters.json  allowlist delta PREVIEW (schema melodia.chapter_allowlist_delta.v1)
- assets.md        outfit rows (catalog contract, no invented slots), VFX kits,
                   flipbook families (see specs/materials/MF_FlipbookScrub.v1.json)
- score.md         theme, BPM band, MIDI path (never hand-build UMidiFile; use
                   MusicClock imported assets, rule 16)
- lookdev.md       PPV recipe + Nikki treatment tiers applied + owner viewport
                   sign-off date (agent captures for record only; eyes = truth)

Completion = a human plays it fresh-slot end-to-end; ledger row recorded;
verify_baseline re-frozen if any frozen asset moved.
