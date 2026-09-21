# MK38 Starskiff — Topology Study + Real-Skiff Research (2026-09-17)

School note: Blender 5.2, measured from SHOREWAKE_proxy_v05_boat.blend.
Research sources: Wikipedia "Carvel (boat building)"; Greenhill via
indigenousboats.blogspot.com (shell-built vs skeleton-built typology).

## 1. Measured topology (bmesh census, base meshes)

| Part | V/E/F | Quads | Poles | Watertight | Finish |
|---|---|---|---|---|---|
| Hull_Shell | 532/1068/534 | 100% (0 tri, 0 ngon) | 12x3, 20x5 (ends + bilge turns) | yes (0 boundary, 0 nonman) | WeightedNormal + 6mm Bevel |
| Gunwale_Rim | 576, all quad | 100% | none (clean extruded loop) | yes | WN + 8mm Bevel |
| Gunwale_Glow | 576, all quad | 100% | none | yes | WN (emissive carrier) |
| Keel | 8 (box) | 6 | 8x3 | yes | WN |
| Keel_BrassShoe / Stem_Brass | 8 each | 6 | 8x3 | yes | WN + small bevels |
| Floorboards | 98 | 96 quad | 8x3 | yes | WN + 10mm Bevel |
| Cushion_Stern | 56 | 54 quad | 8x3 | yes | WN + 15mm Bevel |
| Mast | 64 | 32 quad + 60 tri (cap fans) | mixed 3-10 (spar junctions) | yes | WN + 3mm Bevel |
| MastLantern | 42 | 0 quad, 80 tri (geodesic crystal) | 12x5, 30x6 | yes | WN (flat-shade crystal reads) |
| Ribcage (GN eval) | 216 | arcs | n/a (generated) | — | 9 ribs, 7.61 x 0.81 x 1.00 |

Verdicts: the shell is a textbook hero hull — all-quad, watertight, poles only
where a boat needs them (stem/stern posts, bilge turn). UVMap on everything.
Zero vertex groups everywhere (rigid boat, correct — nothing here should bend
except the pennant). Modifier order on the hull is right: form → audio →
weighted-normal → bevel (deform first, polish last).

## 2. How real skiffs are built (research)

Two structural philosophies (Greenhill's typology — more useful than the blunt
carvel-vs-clinker split):

- SKELETON-built ("frame first", carvel family): keel laid, frames/ribs raised,
  planks fastened edge-to-edge ONTO the frames. Planks are not attached to each
  other — the skeleton carries the loads, caulking seals the seams. Shape is
  determined by design (the frames), so fewer master shipwrights needed. Allows
  bigger hulls: edge-to-edge plank contact shares hogging/sagging forces.
- SHELL-built ("plank first", clinker/lapstrake + most indigenous traditions):
  planks edge-JOINED to each other first (laps, staples, stitching, tenons) to
  make a self-supporting shell; frames inserted after as reinforcement. The
  shell carries itself; frames need not even touch each other (Bangladesh
  example: floors don't meet the side frames).

Anatomy shared by both: KEEL (backbone) → RIBS/FRAMES (transverse skeleton,
keel-to-gunwale arcs) → STRAKES (longitudinal planks, one per bay) → GUNWALE
(sheer clamp capping the top strake) → fastenings (nails/rivets/trenails per
plank-to-frame crossing) → stem/stern posts closing the ends.

Modern note: since the 1960s-80s, epoxy edge-gluing largely replaced caulking
and even mechanical fasteners in small craft — light plywood skiffs are often
built with NO nails at all. Glue is stronger than the fastening.

## 3. Reading MK38 against the research

MK38 is honestly skeleton-built, carvel-logic: keel backbone, 9 GN ribs arcing
keel→gunwale with ball-socket collars where they cross the keel, armor riding
proud of the bones. That matches real frame-first construction in the right
order (bones → skin), which is why it reads believable at thumbnail scale.

Stylizations (all defensible for a hero shore-boat):
- ONE smooth shell instead of individual strake planks. Real carvel shows seams;
  ours reads "midnight celestial" — smooth is a style choice, and the
  MEL_skiff_plates builder exists to add strake armor per rib bay when seams
  are wanted (9 bays at 0.95 m spacing — the number is already measured in).
- Nails as GEOMETRY (48 nail meshes + .001 dupes from the v03 append — cleanup
  queued in v05 plan). Real fasteners sit per plank-frame crossing; ours follow
  that rhythm already.
- Brass shoe + stem brass + jewels + glow gunwale: ceremonial brightwork over a
  workboat skeleton — the "star" in starskiff. Correct priority: read comes from
  silhouette (hull + mast + sail), then glow lines, then jewels.
- Mast pole census is messy (3- through 10-poles) — acceptable: spars are
  turned wood, mostly hidden by sail/rigging, and bevel+WN hides the rest.
  Lantern all-tri geodesic is CORRECT for crystal (flat facets catch light).

## 4. Modeling recommendations (from both halves)

1. Keep the shell all-quad; any future hull edit (strake seams, hawse holes)
   goes through the GN form tree or a duplicate — never triangle the hero.
2. Ribs stay INSIDE the shell (bones under armor) — the v05 seat gate enforces it.
3. Add strakes via MEL_skiff_plates (one patch per rib bay) rather than cutting
   the shell — shell stays watertight, seams read through plate edges.
4. Rivet lattice last (MEL_skiff_rivet_lattice) — smallest read, biggest count.
5. Dedupe the .001 nail materials before any beauty pass (v05 plan item 1).
6. Pennant is the only soft part — if it moves, it gets the only armature (or a
   2-bone chain); everything else stays rigid, matching the zero-vgroup census.
