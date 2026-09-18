# SKIFF GN MASTER PLAN v10 — structural overhaul + tiers, drapery, jewels, lissajous
2026-09-17 late · Blender 5.2 · school animatic lane · supersedes structure/deco
sections of v09 where they differ; the v09 schedule and laws still stand.

## 0. What this is

A complete Geometry-Nodes overhaul of the starskiff's architecture, built from
everything we have learned (topology study, hull cure, rib orientation law,
cross-section proof, guide-socket discovery, parent-inverse law, waterline law)
and from the full 584-builder kit inventory. Every piece below names the exact
kit builder it rides on — no invented nodes, no bespoke scripts where a builder
exists.

## 1. Research digest — the kit pieces this plan uses (verified present)

Structure:   MEL_starskiff_hull_form, MEL_starskiff_hull_audio, MEL_skiff_ribcage,
             MEL_skiff_balljoints, MEL_skiff_plates, MEL_skiff_rivet_lattice,
             MEL_skiff_chladni_plates
Tiers:       MEL_cn_tiered_pagoda, MEL_chime_carillon_tier, MEL_balcony
Drapery:     MEL_mother_draped_curtain, MEL_curtain_wall, MEL_garment_audio_drape,
             MEL_garment_xpbd_drape, MEL_heraldic_banner
Jewels:      MEL_nikki_bead_string, MEL_nikki_bead, MEL_nikki_wall_beads,
             MEL_nikki_star_pendant, MEL_filigree_wreath_ring, MEL_heart_chain,
             MEL_mother_hair_cascade
Lissajous:   MEL_lissajous, MEL_lissajous_ribbon, MEL_mh_aaa_lissajous_pearl,
             MEL_music_lissajous_harp
Arches:      MEL_arch family (cusped, ogee, gothic, dreamy gothic, broken, way)

Laws carried in from research (non-negotiable):
- Fresh trees only: filed groups carry stale defaults (the 11.4 m bloat cure).
- GN dials can't be driven from Python; fresh-tree INTERFACE DEFAULTS can,
  including object sockets (the Guide recipe) — plan every exposure that way.
- Ribs are ∪ (tips at gunwales); builders that emit ∩/one-sided get the
  180°-about-X fix + re-seat, proven by cross-section, never by bbox alone.
- Absolute-coordinate meshes: matrix_parent_inverse must cancel the anchor.
- Zero-vert hosts (passthrough junk) and unparented guides (RELATIVE reads).
- Visible hardware lives z 0.68 and z 0.855; transom band z 0.62..0.84;
  waterline truth z 0.62.

## 2. Canonical GN stack for the boat (the overhaul)

One stack order, every generation built from it:

    Hull_Shell:  hull_form  ->  hull_audio  ->  WeightedNormal  ->  Bevel
    Ribcage:     host(0-vert) + MEL_skiff_ribcage (flip-fixed seat, z 0.62 dip)
    Joints:      host + MEL_skiff_balljoints (same transform as ribcage)
    Plates:      host + MEL_skiff_plates (armor over bones; one per rib bay)
    Rivets:      host + MEL_skiff_rivet_lattice (last, smallest read)
    Chladni:     host + MEL_skiff_chladni_plates (accent plates, optional)
    Tiers:       tier hosts parented to mast/anchor (section 3)
    Drapery:     drape hosts on measured guide objects (section 4)
    Jewels:      strand hosts on measured guides (section 5)
    Lissajous:   curve hosts between measured anchor points (section 6)

Order of application = bones -> armor -> rivets -> ornament -> soft. The
current v09 file already carries ribs/joints; this plan rebuilds the whole
structure fresh from this stack so every element shares one provenance.

## 3. SECOND TIERS — "a taller, whimsical starskiff"

Intent: two readable tiers above the deck — a lookout tier (the CrowsNest we
have, made canonical) and a decorative tier crown.

3a. Tier 1 — lookout (exists in v09; rebuilt in the overhaul to stack spec):
    platform r 0.34, 8 posts, brass caps, scallop fringe, rope ladder.
3b. Tier 2 — carillon/pagoda crown: MEL_chime_carillon_tier (a small tiered
    bell-house) mounted ABOVE the nest on the mast at z ~2.75, scaled to
    ~0.35 via object scale; MEL_cn_tiered_pagoda as the alternate silhouette
    for a flared-eave roof. Both are objects, one chosen, one kept hidden
    (design A/B in the file, owner picks).
3c. MEL_balcony — a tiny side balcony off the nest rim (port side), scaled
    ~0.3, its railing echoing the nest posts.
Gate: each tier reads in the nest-cam render; nothing intersects the boom
(z 2.33) or the pennant (z 2.68).

## 4. DRAPERY — soft architecture

4a. Awning drape: MEL_mother_draped_curtain over the stern deck (guide =
    measured boom-to-stern line), scaled 0.5, scalloped hem reads as the
    canopy; material = M_Sail_Pearl_Damask.
4b. Banner: MEL_heraldic_banner on the mast at z ~2.9 (above pennant),
    scaled 0.35 — the one heraldic note, brass-and-pearl.
4c. Audio-drape study: MEL_garment_audio_drape as an OFFLINE study only —
    wave-driven cloth on the boom (authoring/bake lane; no runtime audio
    writer anywhere; this is the project's music law).
4d. Live cloth stays ours too: Pennant_Sim (cloth modifier) is the only
    simmed drape shipped; drapery 4a/4b are static or gently keyed.

## 5. DANGLING JEWELS — falls, strands, and charms

5a. Bead strings: MEL_nikki_bead_string along the nest rim (guide = octagon
    around the platform), scaled 0.5 — a bead swag under the lookout.
5b. Star pendants: MEL_nikki_star_pendant (already proven) — add one inner
    strand inside the nest rail, and one under the boom mid-span.
5c. Heart chain: MEL_heart_chain as a short charm fall at the stern plate,
    scaled 0.6 — hangs beside the medallion.
5d. Wreath ring: MEL_filigree_wreath_ring around the mast at the tier-2
    base (z ~2.62), scaled 0.4 — a gilt collar.
5e. Hair cascade: MEL_mother_hair_cascade as the grand jewel fall from the
    nest rim to the waterline on the seaward side (scaled 0.5) — the
    signature piece; if it reads heavy, halve the scale.
Gates: nothing hangs below z 0.70 toward the water (0.62 is the sea); every
strand's attach point measures onto a real surface.

## 6. LISSAJOUS — the rigging becomes music

6a. MEL_lissajous_ribbon between measured anchors: bow prow (3.82, 0, 0.95)
    to masthead collar (0.333, 0, 2.9), and stern plate top (-3.66, 0, 0.84)
    to the same collar — two decorative stays that ARE the rigging.
6b. MEL_lissajous as a smaller in-fill arch above the nest, tied sparrow-
    style between the mast and tier-2 base.
6c. MEL_mh_aaa_lissajous_pearl as the optional pearl-strand variant for the
    seaward stay (A/B against 6a).
Gate: ribbon curves stay clear of the sail furl (x -0.37..1.03, z 2.31..2.46)
and of the promoted-shot camera frustums (01/03/13/15/16).

## 7. The five stream items (folded in, order fixed)

1. Water tier 1: Ocean modifier (res 6-7) + ripple keys + wake trail; staged
   AFTER the structure overhaul so the wides are final geometry first.
2. Pennant cloth bake: bake Pennant_Sim to keys, remove the sim modifier.
3. Promoted shots 01/07/08/13/15: rendered only after 1 & 2 land.
4. Workspace kit: raycast_place() + seat_by_iteration() helpers, and the
   reusable GN wrapper for "host + builder + fresh-tree defaults" — so the
   next ornament is 5 lines, not 100.
5. Hygiene: .001 sweep, FLIP Domain removal, hidden-object census, one
   final generation named v10_final for panels.

## 8. Build sequence (each step gated + committed)

  v10a  structure stack rebuild (2) -> cross-section proof renders
  v10b  tiers (3) -> nest-cam render gate
  v10c  drapery (4) -> drape-cam render gate
  v10d  jewels (5) -> strand attach-point printout + render
  v10e  lissajous rigging (6) -> clearance check vs furled sail + cams
  v10f  stream items (7) -> water, bake, promoted shots, cut rebuild

## 9. Owner decisions

1. Tier 2 silhouette: carillon bell-house or flared pagoda? (plan builds both,
   owner hides one — recommendation: carillon reads more "starskiff")
2. Jewel heaviness: full cascade (5e at 0.5) or restrained (0.25)?
   (recommendation: start 0.35, owner's eye)
3. Lissajous stays: ribbon (6a) or pearl (6c) for the seaward line?
   (recommendation: ribbon port, pearl starboard — asymmetry is whimsy)
4. Awning over stern: yes/no (recommendation: yes — it makes shot 03's
   mid-ship closeup read as inhabited).
