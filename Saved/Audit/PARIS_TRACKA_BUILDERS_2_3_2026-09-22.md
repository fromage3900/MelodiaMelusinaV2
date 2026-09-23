# PARIS Track A builders 2-3 — build record (2026-09-22)

Two new Maison Impossible builders, both landed with presets, health scripts,
and the two brand packs they were reserved for now fully resolved.

## What shipped

### GN_PARIS_FountainLoop (`deploy/surreal_arch/melodia_gn/paris_fountain_loop.py`)

The courtyard fountain carrying the Escher device: a water channel that leaves
the basin, climbs, and arrives back at its own spout. The impossibility is a
DIAL, same shape as the ladder's Join Error:

- `Loop Error` 0.0 = the channel's mouth meets its own spout (working read);
  + = it arrives above the mouth (spills past it); - = it never gets there.
- `Feed Rise` is the channel's own height above the water - the two dials are
  independent (how tall the impossible arch stands / whether it meets).

23 parameters, Infinity-Nikki lens (every ornament a dial): Basin Radius /
Height, Flutes, Shell Count / Size, Rim Beads / Bead Size, Tiers (1-4 slots,
unreached slots deleted, no stubs), Tier Rise / Shrink, Crown Spikes / Size,
Water Level, Ripple Amp / Count, Streams / Stream Radius, Droplets / Droplet
Size, Self Feed, Feed Rise, Loop Error, Channel Radius.

NOT a reimplementation of MEL_public_fountain (civic, plaza, no circulation
logic, no water) - different device, different defect, documented in the module.

### GN_PARIS_DayNightFacade (`deploy/surreal_arch/melodia_gn/paris_daynight_facade.py`)

Escher's Day-and-Night as a Haussmann bay wall. `Night Mix` is the seam: 0.0 is
full day (all windows dark, recessed, shutters folded open), 1.0 is full night
(all lit, panes pushed proud, brass trim) - and in between the light climbs
DOWN from the top floor one window at a time. The roofline carries the actual
device: two interlocking flocks of birds (wings-up / wings-down) with
`Bird Lock` controlling how deep the flocks mesh.

31 parameters: Bay/Floor counts, Bay Width, Floor Height, Wall Depth, Plinth
Height, Window Width/Height/Base/Recess, Muntins + Muntin Bars, Night Mix,
Lit Pop, Brass Trim, Shutters + Shutter Open (full 180-degree swing),
Balconies + Balcony Bars + Rail Height, Dentils + Dentil Size, Flower Boxes +
Bloom Count + Bloom Size, Portal Width, Oculus, Birds + Bird Size + Bird Lock,
Seed (bloom jitter).

NOT a reimplementation of GN_PARIS_WallDetail (one wall surface at bay scale) -
this is the whole facade body the wall-detail pass dresses.

## Evidence (all re-run on the final tree)

```
_melodia_health_paris_fountain_loop.py   -> problems=0 PASS
  verts 14482 (defaults); tiers 1/2/4 = 14226/14482/14994 (slots delete clean)
  self feed off delta 236; loop error slides (zmax 2.060 -> 2.400, same verts)
  rim beads 0->120 delta 10320; streams 0->6 delta 192

_melodia_health_paris_daynight_facade.py -> problems=0 PASS
  night mix 0.0/0.5/1.0 = 10528/10592/10648 (split is live, extremes safe)
  bays 2->5200 5->10528; floors 1->4192 3->10528
  toggle deltas: Shutters 240, Balconies 416, Flower Boxes 7920, Muntins 360
  birds 0->14 delta 896; shutter open 0.0/0.5/1.0 same verts (swing), ymax
  0.531 -> 0.904 -> 0.531 (the swing MOVES)

deploy/_melodia_preset_audit.py          -> exit 0; 152 builders / 473 presets;
                                            0 shadowed / 0 orphans;
                                            ALL THREE packs 5/5 resolved
Tools/verify_addon.py                    -> GATE RESULT: PASS (6/6), 596 ids
Tools/melodia_studio_census.py           -> CENSUS RESULT: PASS, lost 0 new 0
```

Baseline: re-cut with `Tools/verify_full_registry.py` (596 ids);
previous baseline preserved at
`Saved/Audit/registry_baseline_pre_trackA_20260922.json`.

## Defects the harnesses caught (both would have shipped green)

1. `NEGATE` is not a valid ShaderNodeMath operation - the house `mathn` helper
   swallows the bad op and the node stays on ADD, so the flower boxes were
   placed ABOVE the windows instead of below. Caught by the facade health
   script's operation census. Fixed to MULTIPLY x -1.
2. The water disc sat INSIDE the solid drum (invisible) because "Water Level as
   a fraction of Basin Height" puts the surface below the drum top. Now the
   surface sits in the basin mouth (lip height fraction); droplets re-seated
   above it. Caught by a preview render + vision read, not by numbers.

Also caught in the preview harness itself: background-mode EEVEE reuses cached
results between render calls - a stale shot rendered the previous state. Fixed
by bumping the frame before each render (`scene.frame_set(+1)`).

## Wiring closed

`melodia_gn/__init__.py` now imports `paris_escher_ladder` (the one-line wiring
the Maison doc left pending on 2026-09-20), plus the two new modules. Registry
593 -> 596.

## Previews

`Saved/Audit/paris_trackA_previews/` (rendered by
`deploy/_melodia_render_paris_previews.py`, EEVEE, framed 3/4):
fountain_defaults, fountain_self_feed, facade_nuit, facade_crepuscule,
facade_jour. Vision reads: fountain = basin + beaded rim + flutes + shell
bosses + the return-channel arch; facade = 5 bays, 3 floors, mullions, panel
shutters, sills + flower boxes, bird frieze along the cornice.

## Known-open (not defects, tune later)

- Jamb bottoms sit 0.07 below z=0 (cosmetic, ground-plane dependent).
- Blooms read small at default Bloom Size 0.075 in a 720px preview; the dial
  is there.
- Uncommitted on `collab/laptop/brooch-sky-20260917` per git law - commit is
  the owner's call.
