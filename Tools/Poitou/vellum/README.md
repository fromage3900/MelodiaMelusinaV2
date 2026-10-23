# Poitou Vellum bake lane — college click-path

Rest geo + solver scaffold: `vellum_bake.hiplc` (built headless by
`build_vellum_rest.py`; rest branch gate PASSes). Sims are NOT tuned —
wind, stiffness and the bake frame are eyes-on decisions.

## The three pieces (rest at ORIGIN, local space)

| Piece | Rest | Pin group | Place at |
|---|---|---|---|
| Tillet canopy | 4.8 x 1.8 panel, 24x8, y=1.2 | `pin_gunwale` (long edges) | barque at lock-tail jetty (CANOE lane) |
| Garland rope | 6 m catenary, 48 segs, 0.8 sag | `pin_rope_ends` | chamber span / jetty posts |
| Awning | 7.2 x 1.5 panel, tilted -15 deg | `pin_eave` (top edge) | lockhouse front eave |

## Bake session (full engine, GUI)

1. Open `vellum_bake.hiplc`. Each piece has cloth+pin
   `vellumconstraints` merged into `vellum_bake_solver`.
2. REVIEW-marked: stiffness / bend / damping / substeps on the
   constraint nodes; add fan wind 0.3 m/s from the marsh (+x) in DOPs
   or a velocity volume.
3. Play 48 frames @24. Scrub for the silhouette (silhouette is the
   product, per the kit header) - tillet mid-swell, garland settled,
   awning belly.
4. Timeshift the best frame -> filecache to
   `Tools/Poitou/vellum/baked/<piece>.$F.bgeo` (create the dir).
5. Sculpt export follows the fountain precedent (headless Blender
   OBJ->FBX) into the sculpt library; wire through `inst.vex`
   placeholders (POP/GRS pattern). Heroes hand-placed, rule 9.

## Never

- No live sim inside `poitou_layout_live` - recook policy stays fast
  and deterministic. Bakes only, like the fountain FLIP sector.
- No new masters for cloth: linen reads through the existing toon
  master + vertex paint (lime/damp/moss/alpha channels per kit.vex).
