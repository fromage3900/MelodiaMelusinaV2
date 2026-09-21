# Brooch audit — where it stands against "breathtaking", 2026-09-17

Scope: the v10 hero (60 mm, 7 genomes) as a PRODUCT judged against the high-jewelry bar.
Method: session-verified state + audit renders (`Saved/Audit/audit_front.png`,
`audit_front_nooutline.png`) + the six luxury axes from `BROOCH_LUXURY_RESEARCH_2026-09-17.md`.
No mercy requested, none given.

## What is genuinely strong (do not touch)

    silhouette      curve-native petals, smooth-by-construction, watertight, sizing exact (0.0%)
    structure       readable anatomy at 64 px; plate/dome/petals/pave/hardware all resolved
    motion skeleton dangles sway live at 0.017 s/frame; petal-motion architecture proven (0.13 s spike)
    materials seam  per-part IDs (petal/dome/body/setting/chain/pearl/pave) ready for texture work
    craft floor     multi-part assembly reads as JEWELRY, not a prop: bezel, claws, hinge/clasp exist

## Scoring against the six axes

    A. THE HAND (surface craft)      D-     nothing is engraved. One gold PBR across every
                                            metal part. Zero polish contrast (polished vs satin
                                            vs recess), zero micro-normal breakup. High jewelry
                                            is "silk, velvet, honeycomb" gold; ours is CG-flat.
    B. THE LIGHT (optics)            D      metal reflects a flat navy void (no environment to
                                            mirror = dead by construction); pearls read as pink
                                            ping-pong balls (no nacre stack, no subsurface
                                            depth); gems = one transmission-ish material, no
                                            dispersion/fire, no caustics spilling on the metal.
    C. THE DEPTH (layering)          C      one petal layer; no under-story, no leave-behind
                                            layers, no mixed materials (horn/titanium/enamel);
                                            openwork light-through is designed but unbuilt.
    D. THE MOTION (the quiver)       C+     dangles = one clean sine. Missing: the two-band
                                            quiver (sway + jewel tremble), per-link lag, petal
                                            flutter (C3 ready), and motion that makes light play.
    E. THE STORY (why this piece)    D      no name, no lore, no narrative-carrying detail. The
                                            art director's test - "does every element carry
                                            feeling?" - currently fails: motifs yes, meaning no.
    F. THE PRESENTATION (the stage)  D      dev-grade renders: coarse framing, no HDRI, no rig
                                            discipline; the toon outline (house game style)
                                            fights the luxury read in stills; no dark-field rig.

## The five that actually move the needle (ranked by impact / effort)

    1. PRESENTATION RIG (F)       1 day    the single biggest instant jump. Dark field + HDRI/reflection
                                           cards + the dual rig (soft for metal, hard points for
                                           stones) + outline OFF in luxury stills. No asset change.
    2. THE HAND (A)               1-2 wk   engraving language: rigato/telato/segriato micro-maps on
                                           the per-part IDs + guilloché FIELD on the plate/steps
                                           (procedural engine-turning = perfect for our math) +
                                           polish contrast between IDs. This is what stops it
                                           reading as CAD.
    3. STONES + PEARLS (B)        1 wk     pearls as a material stack (nacre SSS + sheen); gems get
                                           real dispersion per register - and the phenomenal
                                           register (moonstone adularescence, labradorite
                                           "black rainbow", opal play-of-color) is EXACTLY the
                                           Melodia element language; caustics on.
    4. THE MOTION (D)             3-4 d    C3 petal flutter + two-band dangle quiver + per-link lag
                                           + glint scheduling. Chao's word for the target: the
                                           buds "quiver gently" - not swing.
    5. THE STORY (E)              1 d      name, collection, limitation, ONE narrative detail
                                           (a Chao-style named masterpiece; a Nikki-style detail
                                           that carries the feeling - e.g. the reliquary socket
                                           as "the held memory"). Cheap, changes everything about
                                           how the piece is READ.

## Verdict

Bones A-, soul D. The pipeline, the motion architecture and the material seams are production-grade;
what is missing is exactly the layer that luxury spends its hours on: the hand's marks, the stone's
light, and the reason the piece exists. Nothing on the list requires re-architecting - all five
items ride the systems already in place (IDs, UV pass, motion split, presets).

Evidence files: `Saved/Audit/audit_front.png` (as-is, outline on) · `audit_front_nooutline.png`
(luxury read with the toon shell off - the difference is itself an audit finding: the outline is a
GAME-look device and must be off for the jewelry read).

---

## Addendum 2026-09-17 (evening) — "why is the rim of beads at an angle?" — ROOT-CAUSED + FIXED

Owner question answered with measurements, not reads. The bead rim (MID_Bead_Pave, the 80-site
border ring) measured: radius a clean ring (r 18.3-21.1 mm) but z spread **21.4 mm** with a smooth
single-period wave (plane fit 18.3 deg about X and Y alike - a ~25 deg diagonal tilt).

**Root cause: the seating sampler.** The ring was seated with `SampleNearestSurface` feeding its
`Value` slot a `Position` field ("surface position field"). Empirically (live A/B):
- sampler connected -> z spread 21.4 mm (tilted);
- `Value` field DISCONNECTED -> z spread 2.43 mm (level).
The sampling itself was fine (target cylinders are level); **the Position field in that slot
returned positions from the wrong geometry context** - so the row rode a tilted phantom surface.

**Fix (builder, `Tools/gen_flower_brooch_v10.py`):** seating replaced with a **downward Raycast**
onto `gold_surf` (plate + step), `Hit Position -> Separate XYZ -> Z + lift`. Applied to BOTH the
pave ring and the gem sampler (same pattern, same bug). After rebuild:
- MID_Bead_Pave z extent **21.41 -> 3.13 mm** (3.1 mm = one bead diameter - a level row);
- MID_Metal_Body z extent 20.62 -> 3.34 mm (the seats rode the same wave);
- all 7 genomes still 0.0% sizing; dangles untouched.

**False lead recorded (lesson):** an inspection that printed `inp.links[0]` suggested the
plate link was "missing" from the join. On multi-input sockets `links` holds ALL links and `[0]`
is just the first - the join was fine all along. Read the full link list before concluding.

**Follow-up candidates (not done, by design):**
1. Border jitter: the ring carries the v7 chaos jitter (~2.5 mm radial) - a real jewelry border
   row is machine-regular; consider a jitter dial per row (0 for the border, kept elsewhere).
2. The accent pearls (petal-snapped) read level (z 8.7-9.7) - they seat at petal tips; fine as-is.

### Jitter dial landed (same evening)

`Pave Jitter` socket (0..1, default 0.0, genome key `pave.jitter`) now owns the row's randomness -
the chaos-driven jitter is opt-in per genome. Measured after the dial (hero):
- 79 distinct bead islands (66 before - no more overlap merges),
- z spread **0.70 mm**, plane tilt **0.01 deg** (a genuinely flat, level row),
- angular-gap CV 0.311 with gaps 2.9-7.7 deg - the residual is the phyllotaxis packing law,
  not jitter. If a true single uniform row is wanted the next dial is an even-coil angular law
  (theta = i*2pi/n) or bead count for touching (~48 beads at r 20 mm for 2.6 mm beads).

### Even row law landed (same evening, second pass)

`Pave Even` socket (bool, default ON; off = legacy golden-angle spiral) - theta = i*(2pi/n) with
the radius staggered inner/outer by parity (a classic two-row pave). Final measurements:
- **80/80 distinct beads, zero merges**,
- **angular gaps exactly uniform: mean 4.500 deg, std 0.000, CV 0.000**,
- **plane tilt 0.00 deg**, z spread 0.70 mm,
- pave bbox perfectly symmetric: 44.53 x 44.53 mm (was 43.96 x 44.02).

Note on instruments: vision reads of the same structural state disagreed between passes (it called
the CV 0.311 row "perfect, uniform" and the CV 0.000 row "not uniform"), so the row was judged by
measurement, not by the vision model. The Even law's visual signature is a fine zigzag (the two
staggered rows); if a classic SINGLE-strand border is preferred instead, that is a bead-count
question (about 48 beads at r 20 mm for 2.6 mm beads to just touch) - one dial away, not a defect.

Presentation rig (the ranked move #1) landed the same session: `Tools/brooch_pres_rig.py`
(PRES_RIG: dark field, white/black reflection cards, soft key + hard gem point + rim + kick) and
`Tools/brooch_pres_shot.py` (bbox-framed front / three-quarter / macro stills, outline off for
stills). Evidence: `Saved/Audit/pres_front.png`, `pres_tq.png`, `pres_macro.png`.
