# Faraway Mother: Vellum usage plan and technical breakdown (2026-10-26)

Design note, not a status document. Status stays in `CURRENT_STATE.md`. Houdini 22.0.368 (Education/Indie category).
Rule of this page: **VERIFIED** means a script ran and a gate passed; **PLANNED** means designed, never cooked.

## 0. What Vellum is for in this level

Faraway Mother is "fabric as geology". Terrain is analytic (SilkPeak HDA: global Chladni phase pleats). Vellum is
reserved for the places where fabric must **look like it was placed and settled**: draped patches on peaks, banners
between peaks, ribbons, and the soft sculpted figures. It never runs at runtime. Every use is baked offline to a static
mesh, a VAT (vertex animation texture) or a flipbook, and imported through the existing UE paths.

## 1. Use table

| # | Use | Status | Bake target | Collision | Notes |
|---|---|---|---|---|---|
| V1 | Hero drape patch on a SilkPeak tile | **VERIFIED** (spike) | static mesh `SM_FabricRidge_Hero` | the tile itself | `Tools/Houdini/faraway/build_faraway_hero_drape.py` |
| V2 | Wind-flutter sky ribbons (SilkRibbon HDA strip) | PLANNED | VAT, 64-frame loop | none (pinned ends) | pins on both ends, wind noise |
| V3 | Bunting/banners strung between two SilkPeak crests | PLANNED | static + VAT sway | none | catenary from pinned points, 3 pin pairs per peak |
| V4 | La Berceuse gown + shawl (38 m guardian) | PLANNED | static at rest pose, VAT breath | body proxy | model does not exist yet |
| V5 | Thimble's knitted hat | PLANNED | static | head proxy | tiny; hand-tuned, not simulated at scale |
| V6 | Lace Wings wing flutter | NOT VELLUM | n/a | n/a | wing flap is a GN/vertex-shader beat curve; Vellum is too heavy for a 160-creature flock |
| V7 | Seam-line "stitch-pull" puckering | PLANNED | height/normal bake | the seam SDF | gather cloth toward F=0 so the ground reads as stitched |

## 2. V1 as run (VERIFIED)

Script `build_faraway_hero_drape.py` (hython). Network, in order:
1. `HDA_Faraway_SilkPeak` cooked at defaults, geometry saved as `peak_tile.bgeo.sc` (250 x 12.7 x 250 m, 16,641 pts).
2. `file` SOP loads it as the collision mesh.
3. `grid` SOP cloth sheet, 96% of the tile, 80 x 80 divisions (6,561 pts), placed `lift` = 6 m above the highest peak point.
4. `vellumconstraints` (cloth) -> `vellumsolver`, substeps 4, collision mesh on the third input, 80 frames.
5. `OUT_drape` null; exported `SM_FabricRidge_Hero_drape.bgeo.sc` + `.obj`, `FarawayDrape_hero.hiplc`, `manifest.json`.

Gate (all required): zero cloth points below the terrain sample, zero NaN, cloth height span > 1 m, more than 50 contact
points. Result: 0 below terrain, gap -0.18 to +0.82 m, 3,281 sampled contacts, 12.1 m of relief, no NaN.

**Honest limits.** The first version of this gate passed a cloth that had fallen flat without touching anything; the gate
now requires real contact. The tile it drapes over is the old 250 m tile with 12 m of relief, not the 670-1150 m
blockout peaks, and the SilkPeak tile has known border-normal, pleat-aliasing and origin-pinch defects (handoff). Rerun on
SilkPeak v1.1 before using any output. Output folder: `Saved/Staging/HoudiniForge/FarawayDrape_20261026/`.

## 3. Solver settings and why (planned values are marked)

| Setting | V1 (run) | V2 ribbons | V3 banners | Reason |
|---|---|---|---|---|
| Substeps | 4 | 3 | 3 | enough to stop cloth tunnelling a 2.5 m collision lattice |
| Cloth res | 80 x 80 over 240 m (3 m cells) | 0.5 m cells | 0.4 m cells | cell size must be well under the pleat wavelength (36 m) for drape; ribbons need finer cells for flutter |
| Stiffness | solver default | low bend, high stretch | medium | silk drapes, does not crumple |
| Pins | none (settles) | both ends | both ends | ribbons/banners are anchored, not free |
| Collision | tile mesh | none | none | only V1/V4/V5 touch geometry |
| Frames | 80, keep last | 96, loop | 96, loop | V1 is a rest pose; V2/V3 loop for VAT |
| Wind | none | noise vector, period = 4 beats | same | ties flutter to the beat (BeatPhase) in UE |

Rest scale follows the spec in `FARAWAY_MOTHER_DRAPE_SPEC_2026-09-01.md` (sheet first, collision second, pins by manifest).

## 4. Bake and UE intake path (all PLANNED except V1 mesh export)

- **Static (V1, V4, V5):** FBX, Nanite on, collision `simple`, UVs global (u,v from the 8 km field, no tile resets), material
  slot name `Mantle` -> existing `MI_Mother_Mantle` (HDAs already hard-code `MI_Mother_*`; keep them).
- **VAT (V2, V3, V4 breath):** 64-96 frames, position texture + normal texture, power-of-two, no new materials: bind to an
  existing VAT-capable instance, or leave the mesh static if none exists (owner rule: no new masters).
- **Placement:** from `Saved/Staging/HoudiniForge/FarawayBiomes_20261026/placements.json` (SilkCrest biome for V1/V2/V3,
  VelvetBasin for V4).
- **Budget:** a 6,400-quad patch bakes to roughly 13 k triangles; instance patches, never one giant sheet (an 8 km sheet
  would be about 8,000 x 8,000 cells at 1 m and is not feasible).

## 5. Risks and open items

1. SilkPeak v1.1 (owner is building it) changes the collision, so every V1 number must be re-measured.
2. VAT needs a VAT-capable existing instance; none is confirmed in `MI_Faraway_*` / `MI_Mother_*`. If none exists, V2/V3
   ship as static, wind sway from the existing wind vertex animation in the flower master pattern.
3. Vellum solve time on a 500 x 500 m patch at 0.5 m cells is not measured. Measure on one patch before scheduling more.
4. La Berceuse (V4) and Thimble's hat (V5) wait on models that do not exist.
5. Stitch-pull (V7) is a displacement bake on top of terrain height and is not Vellum-solved per vertex; treat as a mask.
