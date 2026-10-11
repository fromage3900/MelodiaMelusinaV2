# SHOREWAKE — WORK LOG (2026-10-07 evening → 2026-10-08 00:05)

Everything below was measured; receipts on disk in `Saved/Audit/` (gitignored) and the
key ones force-added to the repo. This is the record of the full session on the
SHOREWAKE starskiff (ANMN301 animatic lane + the reel loop).

## Deliverables now in the repo

- **Docs**: `SHOREWAKE_BOUNDED_GOAL_2026-10-07.md` (mission + done-definitions + queue),
  `SHOREWAKE_SHOT_PLAN_v03_2026-10-07.md` (animatic table + beauty stills + loop gates),
  `SHOREWAKE_REVIEW_PHYSICS_COMPLIANCE_2026-10-08.md` (research-grounded physics review +
  ANMN301 compliance table), `SHOREWAKE_GN_PLAN_FINAL_2026-10-08.md` (trees closed +
  gates + rules card), `SHOREWAKE_COMPOSITION_PACK_2026-10-08.md` (framing tests +
  recipes), this log.
- **Animatic**: `SHOREWAKE_VSE_animatic_v04.blend` (reproducible source: text strips +
  3 dissolves) and — after the final polish — **`ShepherdBrennan_AnimaticCreation_2026-10-09_v07.mp4`**
(65.00 s, 1080p24, silent, decode-clean, title/end cards, **panel numbers 01–17** (Arial Bold,
bottom-left), 3 measured dissolves with the white-pair one tightened 16→8f; source now
`SHOREWAKE_VSE_animatic_v05.blend`; submission copy carries the convention name; package +
school copy on G:).
- **Scene generations** (proxy/): `pearlfix` → `structurefix` → `animfix` → `bob`
  (variant) + `lookdevstack` + `komikaze_tunedplus` + **`SHOREWAKE_LOOP_v5_master.blend`**
  (the merged canonical), and the saved live `SHOREWAKE_LOOP_v5.blend`.

## What was done, with evidence

1. **Pearl strand restored** (it had been dead since v18 — modifier lost its node group):
   rewire + v16 design values + two tree fixes; gated 5246 v / 61 beads; aft 60-bead loop;
   staged live and verified. Receipt: `pearl_restore_receipt_20261007.json`.
2. **Structure + topology audit** (214 objects): 0 degenerate faces, 0 non-manifold edges,
   0 stray objects, all textures resolve. Fixed: LaundryLine weld 184→164 v (render-diff
   0 px), Pennant −2 loose verts. Receipts: `skiff_structure_audit_20261007.json`,
   `structurefix_receipt_20261007.json`.
3. **GN audit**: 47 trees, all wired/used; 0 dead refs (an earlier "dead nested" alarm was
   an audit access-path error, corrected); 5 inert litter nodes found + archived wiring
   (`gn_litter_context_20261007.json`); nails verified seated 0.000 m.
4. **Animation audit + fix**: all closures f1≡f120 = 0.000; the six "still" holders proved
   to be non-transform animators (force fields, ocean time, lyre). One anomaly fixed: the
   legacy wake-trail action (68 keys f10–170) trimmed into the 1–120 window.
5. **FLIP Fluids resolved**: never baked (cache absent), and a free-surface sim cannot
   close a seamless loop → parked (hidden render+viewport), addon verified loadable;
   deletion remains owner call D4. Receipt: `animfix*_receipt_20261007.json`.
6. **Lookdev**: sea 8.05 m → 64.3 m (wave heights unchanged), ray tracing ON, star world,
   compositor fog-glow tuned (probe footprint 73.6% → 6.6%). Receipts: `night_pass1..7`.
7. **Komikaze tuned+**: 50 hybrids / 172 assignments / 0 failures + GN-material sweep;
   lantern flicker intact (4.0/5.12/3.28/4.0).
8. **Master merge** (`SHOREWAKE_LOOP_v5_master.blend`): animfix + lookdev + komikaze in one
   verified file — 64 m sea, RT, Fog Glow chain, 50 hybrids, pearls/tree gates, closure
   0.0 mm, 0 dead mods; hero renders `master_hero_wide_f60.png` / `master_hero_close_f30.png`.
   Receipt: `master_receipt_20261008.json`.
9. **Physics verification** (vs WoodenBoat terms / shallow-draft patents / rigging guides /
   catenary papers): draft 0.354 m on 8.07 m LOA — plausible; stays ~10.5° off vertical
   (marginally steep vs 12° textbook), shrouds taut (0.08% sag). **The one real flaw:**
   the sea breathes ±0.19 m around a hull that moved 8 mm out of phase → built the bob
   variant `SHOREWAKE_LOOP_v5_bob.blend` (root follows local water height, 25 keys,
   closure 0.0 mm, draft constant). Receipt: `geophys_receipt_20261008.json`.
10. **Animatic polish**: rebuilt the film's source (v04 blend) + rendered v06 with the three
    planned dissolves (measured ramps 0→3.4→0) and verified text/format/decode.
    Receipt: `animatic_v06_receipt_20261008.json`.
11. **Composition**: tested proposals; A (low dramatic) rejected at 4/10 with the failure
    recorded; D (pulled-back hero) strong with a 6% widen note; bow close-ups deferred to
    in-session framing. Renders: `comp_*` in Saved/Audit.
12. **Night A/B preview**: `master_hero_wide_f60.png` (sea glow 3.0) vs `nightB_wide_f60.png`
    (glow 1.0; 37.6% of pixels changed) — owner picks the night direction.
13. **Live session saved by owner direction** (00:02): everything staged (pearls, mesh
    fixes, animfix, FLIP park) is now in `SHOREWAKE_LOOP_v5.blend` on disk; dirty=false,
    re-verified after save.

## Open owner calls

D1 sail kiss · D2 carillon/pagoda · D3 deckwell · D4 deletions (FLIP domain/surface,
WakeTrail, legacy meshes) · bob promote/pass · v06 ship/keep v05 · night A/B pick ·
litter cleanup (5 nodes) · the two stray live objects (`audvis_global_settings`, `x undo`).

## File ladder (proxy/)

`SHOREWAKE_LOOP_v5.blend` (live, saved 00:02) · `_pearlfix` · `_structurefix` · `_animfix`
(canonical geometry+anim) · `_bob` (water-following variant) · `_lookdevstack` ·
`_komikaze_tunedplus` · **`_master`** (render from this).
