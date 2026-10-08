# SHOREWAKE — PHYSICS, COMPLIANCE + POLISH REVIEW (2026-10-08)

Measured, not guessed. Receipts: `Saved/Audit/geophys_receipt_20261008.json`,
`bob_receipt_20261008.json`, `scene_full_audit_20261007.json`, `animfix*_receipt_20261007.json`.
References consulted: WoodenBoat yacht-design terminology (draft/DWL/CB), shallow-draft
hull patent US6325009 (draft:length ~1:12 for shoal cruisers), rigging practice guides
(staying angle >= 12 deg minimum; stays taut, not singing), catenary mooring papers
(working lines nearly straight; a rigidly benign sag only for slack lines).

## 1. Real-boat physics verification

- **Draft / waterline: PASS (plausible).** Hull floats at 0.354 m draft on 8.07 m LOA
  (1:22.8). Keel stays submerged even at the wave trough (5.6 cm margin); at swell
  crests ~0.6 m of hull is immersed. Reads as a light, shallow skiff. Mast rake 0.36
  deg from vertical (real practice 1-3 deg aft; visually fine).
- **Standing rigging: PASS (marginal).** Stays and shrouds run ~10.5-10.7 deg off
  vertical vs the textbook 12 deg minimum - marginally steep, plausible for a short
  mast. Shrouds are straight (0.08% longer than their chord = taut, matching real
  rigging practice).
- **Seating integrity: PASS.** Every nail head and fitting measured against the full
  boat surface (79k-face BVH): all touch their mounts at 0.000 m. The earlier
  "floating dots" read = hanging jewelry and pearls by design, not defects.
- **THE ONE REAL PHYSICS DEFECT - boom found and repaired as a variant.** The sea
  breathes +-0.19 m around the hull while the boat translated only 8 mm and OUT OF
  PHASE (`bob_A` evidence) - i.e. the waterline slid up and down the hull instead of
  the hull riding the swell. That is the actual "floaty" tell. Fix built:
  `SHOREWAKE_LOOP_v5_bob.blend` - the root now follows the local water height at 25
  linear keys (two gentle heaves per loop, draft preserved, closure 0.0 mm).
  A/B stills: `bob_A_old_f31.png` vs `bob_B_new_f31.png` (and _f61 pair).
  **Owner: eyeball the pair; if liked, it folds into the master.**
- Marginal notes: no external mooring-line geometry (beat board "tethered" is
  narrative only); `LG_LightObj_0` hangs 18 m below the hull (inert - verify/hide);
  ocean wind is a scalar 4.0 (fixed direction; pennant sway is keyed, not derived).

## 2. ANMN301 compliance (brief + submission standards)

| requirement | status |
|---|---|
| MP4, 1920x1080, 24 fps | PASS (single video stream, 65.00 s, clean full decode) |
| Audio only if requested | PASS (silent) |
| Filename `lastFirst_assignmentName_dueDate` | note: current file carries `_v05` suffix; rename a copy at submission |
| Panels labeled + numbered | PASS (numbers 01-17 burned in; labels = numbers) |
| Order, no gaps | PASS (contiguous 73 -> 1489) |
| Pacing guide (acting 3-6 / action 1-2 / establishing 3-5 / reaction 2-4) | within class except action shots 13 (3.0 s) and 14 (4.0 s) - reference guideline, optional trim |
| Up to 3 transitions (clarity only) | 0 of 3 used - all hard cuts; compliant as-is. The 3 planned fades (at 457 / 985 / 1393) were never implemented - optional add |
| Title card + end card | PASS (text verified from frames) |
| Plays with no broken frames | PASS (error-free decode) |

**Submission readiness: v05 is submittable today.** The optional upgrades are: the
3 dissolves (the disk VSE v03 lacks text strips - v05 came from an unsaved working
state - so a v06 rebuild = v03 + recovered text + fades, scriptable), pacing trim of
13/14, and the bob variant. None are required.

## 3. Polish list (ranked)

1. Eyeball the bob A/B (the one physics repair; promotes into the master).
2. Decide on the 3 dissolves (v06 rebuild path above) - or ship v05 as-is.
3. LB: hide/remove `LG_LightObj_0` (inert light, z=-18).
4. From the standing queue: master merge (goal doc), night-value A/B, litter nodes,
   live-session junk objects, datablock-name hygiene.
5. Note: `panels_v3/title.png` + `end.png` are still blank placeholders (unused by
   the working source - ignore or delete).

## 4. What was NOT touched (deliberately)

- D1 sail kiss (owner A/B), D2 carillon/pagoda, D3 deckwell - all still open owner calls.
- The canonical animfix file and the live session: the bob exists ONLY as a separate
  variant file until approved.
