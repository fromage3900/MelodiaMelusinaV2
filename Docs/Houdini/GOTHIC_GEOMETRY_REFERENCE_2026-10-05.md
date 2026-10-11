# Gothic Cathedral Geometry — Source Reference (2026-10-05)

Sourced rules for the Baroque/Crystal Cathedral lane. This file is a **design
reference**, not a status document — `CURRENT_STATE.md` remains the only status
authority. Verified tooling facts live in
`Docs/Houdini/HYTHON_HEADLESS_RENDER_FACTS_2026-10-05.md`.

## Read this first: implemented vs. planned

The lane's real controls, read off the live `controls` node, are exactly:

    depth, span, height, tracery, bays, crystal, facets, seed,
    wall_thickness, bevel_width, bevel_segments, floor_divisions

**None of `pointed`, `buttresses`, `undulation_amp`, or `rose_tracery` exists
yet.** Sections 1, 3 and 4 below are *specifications for work not yet written* —
do not read them as descriptions of the current mesh. Verified 2026-10-05 by
`render_cathedral.py`, which prints the parm list at cook time.

Current geometry, measured: OUT_Cathedral cooks to **9278 pts / 8641 prims**,
bounding box ~**12.04 x 45.46 x 25.63 m** (min (-6.02, -0.23, -0.35), max
(6.02, 45.23, 25.28)), centred near y = +22.5.

## 1. The pointed arch (ogive) — SPEC, not yet implemented

- **Two-centred arch**: two circular arcs meeting at a point (cusp). The Gothic
  signature; earlier forms in Byzantine/Sasanian/Islamic architecture.
- **Equilateral arch** (the canonical first Gothic form): arc centres sit at the
  *opposite springing points*, radius = span. Apex height = (√3/2)·span ≈ 0.866·span.
- **Lancet arch**: radius > span → more acute. **Four-centred**: late/Islamic.
- **Structural consequence**: arches of different spans can share one apex height —
  which is what made rib vaults and big glazed windows possible.
- **Planned mapping** (NOT yet built): a `pointed` float (0..1) blending the
  current power-curve profile toward the normalised equilateral arc pair. Apex
  height stays `height`, so the envelope is unchanged and only the curve
  character moves (round apex to cusp).

The profile that exists today is `base = 1 - pow(|x|/half, 1.5 + depth*0.15)` in
`ARCH_PROFILE_VEX`, plus a fractal sub-peak near t in (0.4,0.6) and a tracery
wobble. That is a fractal gothic-*ish* curve, **not** a true two-centred arch.

## 2. Rib vault (quadripartite) — partially implemented

- Two diagonal ribs cross each bay; **severies** (panels) fill between ribs; loads
  run to corner piers. Pointed arches let ribs of different spans meet at one height.
- **Current state**: `NAVE_VEX` does emit two crossing diagonal rib quads per bay
  at `apex_z - rib_w`, with crystal shards growing along them. The armature is
  present; it is not a true quadripartite vault with severies.

## 3. Flying buttress — SPEC, not yet implemented

- **Two-part composite**: (i) a massive **pier**, a vertical block away from the wall,
  and (ii) a **flyer** — a segmental or quadrant arch — bridging pier→wall.
- Defining feature: the flyer does **not** touch the wall at ground level.
- Gothic churches typically used **two stacked flyers**: lower resists vault thrust,
  upper resists roof wind-loading.
- Piers are usually **capped with pinnacles** (cone or pyramid), often crocketed.
- **Planned mapping** (NOT yet built): a `buttresses` toggle. Per bay boundary:
  pier (~0.9 m square section) rising to about 0.55*height; a single segmental
  flyer ribbon (bulge about 0.8 m) from the pier top to the vault curve at about
  0.62*height; keep a small gap at the wall so the seam-weld fuse can never fuse
  decoration into the shell.

## 4. Baroque undulation (the lane's core correction) — SPEC, not yet implemented

- San Carlo alle Quattro Fontane: *"the walls move in and out, they undulate"*;
  plan armature is back-to-back equilateral triangles (1:sqrt3 relation).
- **Planned mapping** (NOT yet built): `undulation_amp` (m) + `undulation_period`
  (m, default `bay_len*sqrt3`); lateral X offset `ox(y) = amp*sin(2*pi*y/period)`,
  applied **per y-station** so both rings of a bay at a shared y take the same
  offset and the seams stay coincident — that is what keeps the weld/bevel chain
  intact. The rib quad endpoints need the same `ox(y0)/ox(y1)` so ribs follow the
  wall.

`render_cathedral.py --undulate AMP` already probes for such a parm and prints
`NOTE: no undulation parm exists yet` when it is absent — that is the intended
signal, not a bug.

## 5. Rose window — existing, radial depth deferred

- **Plate tracery**: pierced stone plate. **Bar tracery**: moulded bars; the
  classic radial "wheel" is most often **12-fold**.
- **Current state**: the rose is a Chladni (8,6) disc plus a crystal overlay,
  cooking to **1032 verts / 288 prims** with **2 non-manifold edges at the centre
  hub (0,0,0)**. A radial depth pass is a later bounded item.

Open question, still owner-level: the recipe expected 290 rose faces and the HDA
produces 288. The goal doc records that the old 290 encoded a real bug, so 288 is
recommended — but this has not been formally accepted.

## Non-manifold status (measured, not assumed)

`Tools/Houdini/cathedral/probe_nonmanifold.py` reports **240 edges at the z=0
floor/wall junction** (y-stations 0.0 / 4.0 / 7.5) plus **2 at the rose hub**.
Not a mystery any more: two identifiable sites, both at coincident-point joins.

## Sources

- Wikipedia — *Pointed arch*, *Flying buttress*, *Rib vault*, *Rose window*
  (retrieved 2026-10-05; full pages cached under
  `C:/Users/froma/AppData/Local/hermes/cache/web/`).
- `G:/Melodia_Houdini_Foundry/GOAL_BAROQUE_CATHEDRAL.md` — Borromini / San Carlo
  audit and the lane's hard constraints.
