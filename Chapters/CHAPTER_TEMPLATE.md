# Chapter bible template — copy to Chapters/NN_name/ and fill
Rule that keeps authorities safe: a chapter adds DATA only
(qsc, allowlist delta previewed in encounters.json, PPV weight shifts, meshes,
outfits, songs, PCG). If a chapter seems to need code or a new subsystem, stop —
that is a defect signal per the golden-run exit criterion #6.

Files per chapter:
- CHAPTER.md       logline, emotional movement, feeling-arc, route table,
                   beats, encounter, assets, score, lookdev tiers, exit criteria
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
