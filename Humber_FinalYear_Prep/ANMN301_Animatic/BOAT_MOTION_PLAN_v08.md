# Shorewake Motion Systems Plan v08 — cloth, boat rock, water, wind
Written under the Infinity Nikki developer lens · 2026-09-17 · Blender 5.2 only, school ANMN301

## 0. Where this sits

Boat truth today: `SHOREWAKE_proxy_v07_decor.blend` (fresh GN hull trees, 9 ribs +
balljoints seated, star finial crown, star-pendant garlands both rails).
Owner's live session currently holds `v05_boat.blend`, DIRTY — their Melusina
pass. MCP is the working probe; every mutation in this plan stages headless onto
a NEW generation (v08+), never into the open session.

Melusina's own cloth and hair are HER lane (wardrobe/garment motion skill).
This plan owns the BOAT's motion: sail, pennant, garlands, hull, water, wind.

## 1. The Nikki lens — five laws this plan obeys

1. **Cloth never dies.** In Nikki-grade work something is always moving, even at
   rest: a pennant breathing, a sail shivering, water never frozen. A still is a
   chosen frame of a living system, not a dead pose.
2. **One field, everything rides.** Their wind system is a single authored force
   that cloth, hair, foliage and water all read. Analogue of this project's
   one-writer-per-surface law: ONE wind field object, ONE water surface, ONE rock
   driver. No second wind, no second wave system.
3. **Water is authored, never accidental.** Nikki water reads because it is
   art-directed (shoreline foam, sparkling crests), not because a solver was
   turned on. Physical sim is reserved for one hero moment at most.
4. **Motion must read at thumbnail scale.** If the rock/pennant/ripple doesn't
   read in a 3-second glance, it is budget spent for nothing — cut it.
5. **Budget is part of the design.** Every system declares its vertex caps, cache
   caps and frame budget before it ships; determinism (fixed seeds/frames) is
   how a render stays reproducible for submission.

## 2. System 1 — Wind (the single field)

- One Empty force field: Wind (strength/direction) + Turbulence (scale 0.5-1.5,
  low strength) — the only wind writer in the stage.
- Story states, keyed with the beat board, not simulated: asleep ~0.02 (shiver),
  playing ~0.06, wake ~0.35 (13, the snap), crossing ~0.15 steady.
- Consumers: pennant (primary), sail cloth (12-16), garland cords (visual shiver
  only — gems stay rigid), water ripple emission phase (procedural, section 4).
- Nikki check: pennant reads as a wind direction, not noise — one dominant
  direction every shot.

## 3. System 2 — Cloth (sail + pennant)

Inventory: `Pennant` mesh (M_Pennant) ✓ sim-ready candidate; `Sail_MK33` ✓ but
needs a sim grid first; `FX_SailCloth` empty (the authored attachment point —
use it); Cushion_Stern stays rigid (velvet is a material read, not motion).

Prerequisite (modeling, one pass): re-grid Sail_MK33 and Pennant to quad grids
(sail ≤ 32x24, pennant ≤ 12x8) — pin edge boundaries to boom/mast; keep the
authored mesh as the render shell if sim topology reads badly in beauty shots.

Sim route (both proven-ish, pick per surface):
- **Simply Cloth Studio** (enabled) — fastest authored route: preset + pin
  groups + one-click bake. Default for pennant.
- **cloth_next** (installed, NOT enabled — enable on use) — alternative solver
  presets; only if Simply Cloth fights the pinning.
- **Built-in 5.2 node cloth (XPBD)** — research-lane per garment-motion skill:
  single shells only, no self-collision; use only if the addons stall.

Discipline (from the garment-motion skill, applied to boat cloth):
- Sim → BAKE to keys → remove the sim modifier. Shipped stills/frames are baked
  states, never live sim (a live sim in the save file is a defect).
- No self-collision exists — the sail must not be authored to fold onto itself.
- Headless bakes need timeline evaluation; bake on a scratch copy first, then
  copy keys into the stage generation.
- Caps: pennant 400 verts, sail 5k verts, one sim object at a time.

## 4. System 2b — Water (authored tiers, not solver-first)

- **Tier 0 (current):** shaded plane + emissive states. What every panel uses.
- **Tier 1 (this plan, the animatic):** Ocean modifier, resolution 6-7, small
  chop (spatial size ~1.2, waves 1.5, choppiness 0.6) + toon material; plus
  PROCEDURAL RIPPLE RINGS for 07/08 — animated emission circles expanding from
  the bow, keyed to the story beat (the water "answers"), deterministic.
  Wake trail for 13/15: a tapered foam gradient (material, not particles).
- **Tier 2 (one hero moment, optional):** flip_fluids (enabled, HOLD verdict
  stands) — ONLY if the owner wants one real splash close-up; bake GBs on a
  scratch file, cap cache, single shot. Never in the two-way crossing shots.
- Nikki check: at a glance, water reads sea-cyan with pearl foam crests, no
  rainbow, no noise-mush; the ripple answer at 07/08 is legible as a beat.

## 5. System 3 — Boat rock (the parent motion everything rides)

Driver: the `Starskiff_MK38` anchor — the single rock writer. Everything parented
(garlands, star, jewels, pennant, mast) rides for free; Melusina stays seated by
her own lane's seat hold.

- Stills: bake a rock POSE per shot (heave z, roll y, pitch x, small; the board's
  wake lift at 13 already keys z +0.3).
- Moving shots: procedural keys — heave = sin(t) amplitude A, roll = sin(t+φ),
  pitch lagging roll by ~0.3 rad. Amplitudes by story state: asleep 0.04 heave /
  1.5°, playing 0.06 / 2°, wake impulse 0.12 / 5° for 12 frames then settle,
  crossing 0.10 / 3.5° at 0.35 Hz.
- The rule of lag: pennant and cloth respond AFTER the hull (wind fields and sim
  give this for free; for keyed shots add 2-3 frame offsets so nothing moves in
  unison — unison motion is the tell of fake boats).

## 6. Shot promotion table (panels that become moving shots)

| Shot | Duration | Motion | Systems |
|---|---|---|---|
| 01 wide asleep | 2s loop (48f) | gentle rock only, mist drift | rock, wind (shiver) |
| 07 first phrase | 2s (48f) | ripple ring leaves bow | water ripples, rock |
| 08 water answers | 2s (48f) | ripple returns wider + bells reflection | water, rock |
| 13 skiff wakes | 3s (72f) | hull lifts, pennant snaps, wake trail blooms | rock impulse + wind + water trail + cloth |
| 15 crossing | 5s (120f) | steady rock, trailing wake, sail filling | rock + cloth + water |

All other shots stay stills. Cost: ~336 frames of moving render ≈ 6 min EEVEE at
1s/frame plus bakes — comfortably inside a school week.

## 7. Evidence + budget discipline (what "done" means per system)

- Each system gate: wind (field exists, one, keyed states reproduced), cloth
  (bake exists, sim modifier gone, frame-march contact sheet), rock (anchor
  keys sampled at 4 story frames, amplitudes logged), water (still A/B of tiers,
  ripple ring read at 07/08).
- Frame-march: render every 8th frame of each promoted shot to a contact sheet
  in Saved/Audit; the owner's eye is the pass/fail on beauty, the sheet proves
  the motion exists.
- Determinism: fixed seeds, fixed frame numbers, no live sim in shipped files.
- Caps: sim caches <500 MB; ocean grid ≤ 7; promoted shots render at 100%, 1080p24.

## 8. Sequence of work

1. Sail + pennant re-grid (modeling pass, gates: quads, pins named).
2. Wind field + pennant bake probe (cheapest system first — proves the bake path).
3. v08: rock rig on the anchor (keys + amplitudes) — the parent motion.
4. v09: water tier 1 (ocean + ripples + wake material states).
5. Promoted shots: render 01, 07, 08, 13, 15 as moving sequences.
6. Cut rebuild: replace those five panel slots with their sequences in the VSE,
   rebuild the 1560f MP4 (timing table unchanged; only the stills become clips).
7. Beauty pass: lantern glow + gunwale emissive (still queued from v05 plan).

## 9. Owner decisions needed

1. Sail + pennant re-grid: approve the one-time topology pass on the boat's cloth?
2. Promotion list above: five moving shots — keep, cut, or add any?
3. flip_fluids hero splash: yes/no (default NO — ocean tier carries the cut).
4. Melusina's dress/hair sim: her lane; this plan only guarantees the boat
   doesn't fight it (one wind field is shared if she wants it — single writer).

-- If all four are "yes as written", step 1 starts immediately from v07.
