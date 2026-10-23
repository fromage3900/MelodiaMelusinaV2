# Faraway Mother — Heart Gate HDA (2026-10-23)

Design/build note, not a status document (`CURRENT_STATE.md` stays the status authority).
Governing plan: commit `90bfa88` ("Harmonic Continental Genesis", in
`Docs/Art/FARAWAY_MOTHER_FABRIC_MOUNTAIN_BUILD_2026-09-02.md`). That plan says no production HDA is
*declared* from it. This HDA is therefore a **lab build**: measured, registered, not yet promoted, not yet in UE.

## What exists

| Item | Path |
|---|---|
| HDA | `hda/HDA_Faraway_HeartGate_1.0.hda` (mirror `Content/HDA/`) — type `HDA_Faraway_HeartGate`, Object context, 17 controls on the type |
| Builder | `Tools/Houdini/faraway/build_faraway_heart_gate_hda.py` (`--verify`) |
| Geometry source | `Tools/Houdini/faraway/heart_gate_geometry.py` — pure Python, no `hou`; embedded verbatim in the HDA's Python SOP |
| Registry | `faraway_heart_gate` in `Tools/Houdini/hda_verify/hda_registry.v1.json` — repo gate: PASS |

`Tools/*` is gitignored: **force-add** the builder and geometry file or the HDA cannot be rebuilt from git.

Measured at defaults (Houdini 22.0.368 Education, hython): `output0` 1266 pts / 1170 prims, `output1`
(collision = pier boxes only, doorway stays walkable) 64 / 48. Every closed solid is outward by Houdini's own
prim normals (rib +3.89, pier +2.03, cusp +0.26, stretcher +0.05, heart frame +0.09, stem +0.005 m³); heart
glow has 48 tris facing +Z and 48 facing −Z. Moving `lancet` 1.0→1.4 moved the apex 7.12→8.21 m;
`rib_layers` 3→2 dropped prims 1170→904. Winding follows the clockwise-front rule in the Houdini-winding
finding — orientation is decided by signed volume, never by hand.

Not done: UE import, a render, texture/UV art pass (UVs are planar on the gate face), Nanite/LOD tiers.

## Shape and real-life reference

| Part | Geometry | Reference |
|---|---|---|
| Pointed arch | two-centred arch, radius = `lancet` × span; 1.0 = equilateral (apex 0.866 × span) | Sainte-Chapelle and Amiens; rule set in `GOTHIC_GEOMETRY_REFERENCE_2026-10-05.md` §1 |
| Nested ribs | concentric offsets of one arch, so ribs stay parallel and apexes align | archivolts of Poitevin portals (Notre-Dame-la-Grande, Poitiers) — ties the gate to the Poitou identity |
| Cusps | spearhead leaves hung from the innermost intrados | cusped arches of the Alhambra; Gothic trefoil cusping |
| Stretchers | thin radial bars between ribs | openwork "ladder" tracery of Ulm Minster's spire |
| Lace read | filigree-thin members, deep shadow gaps | Chantilly and Burano bobbin lace; mashrabiya screens |
| Heart | cordiform curve x=16sin³t, y=13cos t−5cos 2t−2cos 3t−cos 4t, hung on a stem from the apex | the Sacred-Heart / heart-reliquary motif in French Gothic glass |
| Glow | two flat sheets (front/back) with `piece=heart_glow` for the emissive material | Rose-window light at Chartres |

Materials are set as `unreal_material` prim strings, using only **existing** instances (no new masters):
`MI_Mother_Veil` (ribs, cusps, stretchers), `MI_Copernicus_GildedLoom` (piers, heart frame, stem),
`MI_Copernicus_FinalDreamweaver` (heart glow, per the 09-02 plan's "frozen moonlight iridescence").

## For a Blender user — controls, labelled

Houdini controls here read like Geometry Nodes group inputs. The HDA is the "node group"; the parameter
panel is its modifier panel.

| Control | Plain meaning |
|---|---|
| Span / Pier Height | gate width and the height of the straight legs |
| Lancet | 1.0 = classic pointed arch; higher = narrower, sharper |
| Rib Layers / Rib Width / Rib Depth / Layer Step | how many nested arches, and how thick, deep and spaced |
| Cusps per Side / Cusp Size / Stretchers per Side | lace detail density |
| Heart Width / Heart Height / Heart Frame Width | the hanging heart; auto-shrinks to fit the opening |
| Arc / Heart Segments | smoothness (cost goes up with these) |
| Seed | small hand-made variation in cusp size |
| Preview Mode | cheap proxy for fast viewport work; no lace detail |

Blender → Houdini: modifier stack ≈ SOP network; Geometry Nodes group ≈ HDA; Vertex Group ≈ group;
Custom Attribute ≈ attribute (`piece`, `unreal_material`, `collision_proxy`). Right-click the HDA →
*Allow Editing of Contents* to look inside (here: one Python SOP → Fuse → Normal → UV → flags → two Output SOPs).

## Houdini layout — state found today

- The repo ships the **Melodia Studio** package (desktops `Melodia_Studio`, `Melodia_KineFX`; shelf `Melodia` with 8 tools).
- Your live prefs (`Documents/houdini22.0`) had **no** custom desktop file and an empty `packages/` folder: the layout was **not installed**.
- I ran `deploy/houdini/install_melodia_studio.ps1 -Verify`. It wrote one pointer file,
  `Documents/houdini22.0/packages/melodia_studio_local.json`, and nothing else. **24/24 headless checks pass**
  (package env, both desktops parse, shelf loads 8/8, all tool handlers launch).
  Receipt: `Saved/Audit/houdini_studio/setup_20261023_061049.json`.
- Not proven: how the desktop looks in the GUI — that acceptance is yours. Undo: `install_melodia_studio.ps1 -Remove`.
- If you have a hand-saved personal desktop from another machine/session, it is not in either Houdini 22 pref folder on this PC (`Documents/houdini22.0`, `~/houdini22.0`; `houdini21.0` was not searched) — copy its `.desk` into `deploy/houdini/melodia_studio/desktop/` and it will be picked up.

## College lab notes (owner-stated, unverified here)

Planned for the college machines: full Education licence, extreme crowd sims, 128 GB RAM for headless
work, 4K Copernicus bakes. These figures come from the owner; this PC was not measured against them.
Practical consequences: keep sims and bakes headless (`hython`), write caches under `Saved/HoudiniFoundry`
(the package's `MELODIA_CACHE_ROOT`), and keep HDAs parameter-driven with a Preview toggle so the
GUI stays light. Education output is non-commercial (`.hdanc`-class limits) — fine for portfolio work, check
before any commercial delivery.

## Silk Peak tile HDA (second build, same day)

`hda/HDA_Faraway_SilkPeak_1.0.hda` (mirror `Content/HDA/`), builder `Tools/Houdini/faraway/build_faraway_silk_peak_hda.py`,
registry id `faraway_silk_peak`. One static far-field terrain tile, evaluated in **global** Faraway coordinates
(±4000 m, `u=(X+4000)/8000`), as the 90bfa88 plan requires — no tile-local UV resets.

- Field: six Gaussian silk peaks + pleats whose crest direction follows the Chladni (3,5) tension gradient
  (same math as `Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py`) + a smooth walkable valley where
  |Chladni| < `seam_width` (ResonantSeamWay). No Vellum; hero cloth is a later gate.
- Real-life reference: pleated/gathered silk (Fortuny Delphos pleating), Zhangjiajie-style layered karst relief
  read as folds, and sand-ripple/ridge fields following standing-wave patterns (Chladni plates).
- Measured (hython): 128-division tile = 16,641 pts / 16,384 prims, all faces up. **G1-style border check:**
  two adjacent 250 m tiles share an edge of 65 samples with worst |dY| = 0.000000 m (plan limit 0.01 m).
  `height_scale` 90→180 raised the peak 31→67 m. Repo gate: PASS (positions-hash drive probe).
- Controls for a Blender user: *Tile Origin X/Y* = where this tile sits on the 8 km map (move it to get the
  neighbour); *Tile Size/Divisions* = size and mesh density; *Peak Height*, *Pleat Wavelength/Depth* = mountain and
  fold scale; *Seam Valley Width/Depth* = the walkable path carved along nodal lines.
- Not done: 2×2 stitched tiles with normals check, Vellum wedge, LOD/Nanite export, UE import, any render.
  The default tile (-125,-125) sits between peaks, so it reads as pleated lowland, not a summit — move
  `tile_x/tile_y` toward (-900, 300) for a peak.

## Next in the build order (from the 10-17 inventory and the 90bfa88 gates)

1. Silk Mountain: 2×2 stitched tiles + one coarse Vellum wedge (tile HDA above is the base).
2. Terraced cliff islands + waterfalls.
3. Lace bridge HDA taking a UE spline (reuse this gate's rib + stretcher code).
4. Per plan: place **one** lace-arch gesture on the continuous seam — the Heart Gate is the candidate.

Observed, not touched: the repo HDA gate shows `arpeggio_stair` FAIL and several stale
`hda/backup/*_bakN.hda` stubs from other builders; I removed only the Heart Gate backups my own rebuilds created.

---

## Fan-out results (agent-built, 2026-10-23)

Each section below is the building agent's own report. All clay renders in `Saved/Audit/faraway_hda/` come from numpy/hython rasterisers (the headless OpenGL ROP crashes here); the agents viewed them. Nothing is imported into UE.

### Review: Heart Gate + Silk Peak (2026-10-23, clay renders)
**What:** First visual review of the two Faraway HDAs, which had only been checked numerically. The clay renders come from my rasteriser, Tools/Houdini/faraway/render_review_clay.py, not Mantra or OpenGL. PNGs are in Saved/Audit/faraway_hda/review/.
**Real-life refs:** Heart Gate follows the lancet-arch cusped portals of Cologne Cathedral and the Alhambra. Silk Peak is pleated silk: Issey Miyake pleating, and the draped ridges of the Karst peaks of Guilin.
**Heart Gate measured:** 6.24 x 8.2 x 0.62 m. 1156 prims, 16 cusps after the fix (18 before). Heart 1.4 m wide, 0.133 m clear of the innermost rib. All 6 closed-solid pieces have positive signed volume and no back faces are visible in any render.
**Fix applied (heart_gate_geometry.py):** cusps that touch the heart outline (grown 0.08 m) are skipped, and the HDA was rebuilt with --verify PASS. The two cusps beside the heart's upper lobes used to pierce the heart frame. The cusp loop variable was renamed (s to cj) because moving the heart block up would otherwise have overwritten the heart scale.
**Silk Peak measured (not modified):**
- Default tile: 250 m, 128 divisions (1.95 m cells), 32768 tris, relief 14.9 m.
- Peak tile (tile_x=-1025, tile_y=175, centred on the anchor at (-900,300)): relief 16.4 m, height 83..100 m.
- Actual pleat wavelength: the nominal 22 m is compressed to 2.1..7.4 m on the default tile (median 7.4 m) and 6.9..12.6 m on the anchor tile. The phase is dot(p,dir(p)) with p up to 4 km, so the dir(p) term multiplies the frequency. Seen as moire and checkerboards on the default tile, and as faceting on the anchor tile.
**Blender-user labels (unchanged):** Preview Mode, Span, Pier Height, Lancet, Rib Layers, Cusps per Side, Heart Width, and so on. Silk Peak: Tile Origin X/Y, Tile Size, Divisions, Peak Height, Pleat Wavelength/Depth, Seam Valley.
**Not done:** the Silk Peak aliasing and profile defects are not fixed. See known_gaps.

Known gaps (review_existing):
- SILK PEAK (SEEN, NOT FIXED) pleat aliasing: phase = dot(p, dir(p)) * 2pi/wl with global p up to 4 km lets the rotating Chladni-gradient direction multiply the local frequency. Effective wavelength is 2.1..7.4 m (median 7.4) on the default tile against a nominal 22 m, and 6.9..12.6 m on the anchor tile, against a 1.95 m cell. The default tile shows checkerboard and sawtooth moire in peak_default_top.png and peak_defau
- SILK PEAK (SEEN, NOT FIXED) pleat profile pow(|sin|,0.7)*sign(sin) has infinite slope at every zero crossing, so it makes near-vertical walls, not the 'sharper crests, rounded gathers' the comment intends (the exponent is on the wrong side). In peak_anchor_lowside.png the near-edge walls are steep enough that their back faces show magenta. In the top-down views those walls read as hard stripes. Use an exponent >= 1 o
- SILK PEAK (SEEN, NOT FIXED) default-tile pinch point: the Chladni gradient is near zero around u=v=0.5, i.e. the world origin, so dir flips and every pleat converges to a star-shaped singularity at tile centre (peak_default_top.png). The default tile (-125,-125) sits exactly on it.
- SILK PEAK scale: a 250 m tile on the (-900,300) anchor (sigma 520 m, 90 m high) shows only a gentle 16 m swell. It reads as a pleated slab, not a peak, and even a 1 km tile shows 63 m relief with slopes of a few degrees. This is a scale/design observation. A 'peak' silhouette needs a larger tile or a smaller radius.
- SILK PEAK needs more divisions for its own default pleat settings. At 128 divisions on 250 m the cells are 1.95 m, so a real 7 m wavelength is only about 3.5 cells. Raising divisions to 256 or widening the wavelength would help.
- HEART GATE heart is small and floats: 1.4 m wide against a 6 m span. It is hung on a 0.06 m stem that visually ends at the cleft and is only attached at the apex by a 0.03 m overlap into the rib. Nothing is wrong with the solids, but the pendant reads weak.
- HEART GATE stretchers are only 0.07 m wide, 0.54 m deep tabs. The 'ladder lace' reads as sparse stubs, not openwork. Cusps are flat plain pentagons with no foliation or trefoil.
- HEART GATE plinth box centre is at y=0 with half-height 0.09, so the gate bbox bottom is y=-0.09 m instead of the stated floor y=0. Output bbox is -3.12..3.12 x -0.09..8.2 x -0.31..0.31.
- HEART GATE heart_glow is two flat zero-thickness fans at z=+-0.005, in the same clay as the frame, so the heart looks solid in the clay render. Whether it reads as glow depends entirely on MI_Copernicus_FinalDreamweaver in UE, which was not checked (no Unreal).
- HEART GATE check not repeated for non-default settings. Only the default parm set was rendered and numerically checked. Preview Mode, lancet != 1, and heart_width at the high end were not rendered. The new cusp keep-out was only tested at defaults.
- RENDER: renders are my own z-buffer rasteriser (flat per-face clay for the gate, per-point N for terrain), not Mantra or OpenGL. Isolated magenta slivers on the terrain silhouettes are partly a facing-test artefact at grazing angles. The large magenta walls in peak_anchor_lowside.png are genuine steep-wall back faces. The gate 'side' view was dropped because it only shows a 0.6 m thin slab.
- HDA is untracked in git (?? hda/HDA_Faraway_*). Nothing was added or committed, per the rules. The 3 HeartGate backup stubs (bak1-3) I created were deleted.

## Faraway Lace Bridge (HDA_Faraway_LaceBridge, 2026-10-23)
**What:** thin arched footbridge, Object-context HDA, `hda/HDA_Faraway_LaceBridge_1.0.hda` (mirror `Content/HDA/`). Input 0 = optional plan curve (first polyline prim, else points in order; only X/Z and the first point's Y are used). With nothing connected it cooks a built-in gentle S-curve of `span` m. output0 = bridge, output1 = walkable deck slab only (collision). Builder `Tools/Houdini/faraway/build_faraway_lace_bridge_hda.py --verify`; pure-Python source `lace_bridge_geometry.py` (embedded in the Python SOP; rib/cusp/stretcher math copied from heart_gate_geometry.py).
**Real-life reference:** Rialto's single low segmental arch (rib profile; crown-point angle 0 = pure round arc); Gothic openwork parapets and tracery of Ulm Minster (quatrefoil/trefoil rings, ladder stretchers); Alhambra / Gothic cusping (lappets under the intrados); Chantilly and Burano bobbin lace (thin members, deep gaps). Existing UE SM_Cathedral_BifrostBridge / EscherBridge are style references only, nothing reused.
**Measured (hython 22.0.368, defaults):** output0 7936 pts / 7458 prims; output1 148 / 146. Length 14.34 m (14 m chord + sway), deck 2.4 m wide, bbox 14.7 x 5.1 x 3.8 m, springing 2.84 m below the landings. Every closed solid outward by Houdini prim.normal() (deck +4.82, rib +2.26, pier +6.15, rail +0.44, post +0.50, cusp +0.27, tie +0.26, mullion +0.16, lace +0.13, stretcher +0.04 m^3); deck top faces +Y, underside -Y. rise changes positions, lace_density 1.6 to 2.4 changes prims 7458 to 10220, rib_layers 3 to 2 gives 7002, Preview Mode gives 1210 prims. With a bent 24.5 m curve on input 0 the bridge follows it, deck still outward.
**Blender-user labels:** Span if No Curve / S-Curve Sway if No Curve (built-in path only); Deck Width, Deck Thickness, Deck Hump at Crown (how humped the walkway is); Arch Rise under Deck; Crown Point Angle (0 = round arc, higher = pointed); Rib Layers, Rib Width, Rib Thickness Sideways, Layer Step (stepped ribs); Lace Cells per Metre (parapet rings, cusps, stretchers, posts, ties all scale with it); Parapet Height; Mesh Resolution (samples/m); Seed (ring variant parity and cusp size); Preview Mode (drops all lace for fast viewport).
**Materials (existing MIs only):** MI_Mother_Cradle deck, MI_Mother_Veil ribs/posts/ties/cusps/stretchers, MI_Mother_Ornament lace rings, MI_Copernicus_GildedLoom rails/mullions, MI_Mother_Mantle abutments. Prim attrs: piece, unreal_material, collision_proxy; detail: unreal_output_name, bridge_length, from_input, springing_y; i@unreal_nanite_enabled=1.
**Not done:** UE import; registry entry not yet written (returned separately); only the first polyline prim of the input is used and the deck is level between landings (no slope/tilted input, no Y from the curve beyond the start); sharp curve bends tighter than about the half-width would fold the inner side; rings are simple lobed bands, not true ogee-cusp tracery; UVs are planar (u along path); no end landings/ramps or railings terminating posts; one-sided deck (no thickness taper). Tools/* is gitignored: force-add the three Python files.

Known gaps (faraway_lace_bridge):
- Not imported to UE; no .uasset exists; registry file not edited (entry returned only); hda_verify.py not run because it reads the shared registry.
- Clay renders come from a software numpy rasteriser (render_review_clay.raster), not Mantra/OpenGL; underside lighting is dark only due to light direction.
- Input curve: only first polyline prim, only X/Z plus the first point's Y; deck is level between landings (no sloped/tilted spans); curve bends with radius smaller than about the deck half-width would self-fold the inner side.
- Lace rings are lobed star-shaped bands (quatrefoil/trefoil), not true ogee-leaf tracery; spandrel is plain posts plus ties, no cusped spandrel panels.
- Rib crown has a hard pointed kink (crown_point angle); abutments are plain wall blocks; no ramp/landing geometry; UVs planar only.
- Tools/* is gitignored: lace_bridge_geometry.py, build_faraway_lace_bridge_hda.py and render_lace_bridge_clay.py must be force-added. Two backup stubs from my rebuilds (hda/backup/HDA_Faraway_LaceBridge_1.0_bak1..9) were deleted.

## HDA_Faraway_TerracedIsland (faraway_terraced_island)
**What:** floating flat-topped rock island: 3-6 stepped terrace strata (vertical-ish cliff + flat tread each), seeded irregular outline, 3 stacked strata bands per cliff with small ledge lips, tapering underside to an apex, ledge waterfalls. Prim attrs `@strata` (terrace index, -1 = underside), `@cliff` (1 on cliff faces), `@band`, `piece` (cliff/tread/plateau/underside/waterfall), `unreal_material`; Nanite on for rock, off for falls. Not an inverted dome.
**Outputs:** `output0` island + waterfall ribbon strips (piece=waterfall, UV v 0..1 down the fall, `@flow`, `@fall_height`, `@wf_id`); `output1` waterfall EMITTER POINTS (`@N` down-slope, `@fall_height`, `@width`, `@flow`, `@strata`) - not collision; `output2` collision proxy (stepped low-poly hull, `collision_proxy=1`).
**Real-life reference:** Zhangjiajie pillars (floating-mountain read), Yuanyang / Banaue rice terraces (stepped strata, noisy contour outlines), Angel Falls / Iguazu (ledge falls over cliff lips), Monte Roraima tepui (flat top + vertical sheer cliffs + tapered base).
**Measured (defaults r=40 m, 4 terraces x 5 m, noise 0.3, lean 12, 3 falls, seed 7):** bbox 92.4 x 54.0 x 84.7 m (plateau y=+20, apex y=-34, origin = lowest cliff base); output0 1652 pts / 3228 tris (3168 rock + 60 ribbon); output1 3 pts / 0 prims; output2 226 pts / 448 tris. Preview Mode: 552 tris. Island volume 130.8k m^3; hull contains island within 3.3 cm (ray probe, 400 samples); cook ~0.5 s.
**Blender-user controls:** Preview Mode (low-poly) / Island Radius (m) / Terrace Count (3-6) / Terrace Height (m) / Outline Roughness (0-0.5) / Cliff Lean (deg from vertical) / Waterfall Count / Seed.
**Materials (existing MIs only):** cliff+underside MI_Mother_Mantle, tread+plateau MI_Mother_Gown, falls MI_Copernicus_SilkWaterfall.
**Not done:** not imported to UE (no .uasset, collision naming `UCX_SM_Faraway_TerracedIsland_00` untested in HE); underside and cliffs are smooth (no rock/stalactite noise or SDF erosion); ribbons are simple 2-column strips, no splash/mist/pool geometry or Niagara hookup (emitters are ready for it); no river channel carved on treads leading to the lips; cliff lean is capped at 35% of tread width on extreme radius/height/slope combos; collision is stepped and only near-convex per tier; waterfalls placed by seed, not by a drainage rule; cylindrical UVs stretch on the underside.

Known gaps (faraway_terraced_island):
- Not imported to UE; collision output name UCX_SM_Faraway_TerracedIsland_00 and output1 emitter-point consumption untested in Houdini Engine
- Underside and cliff faces are smooth (no rock detail, stalactites or erosion); strata banding is geometric lips only
- Waterfall ribbons are flat 2-column strips: no mist/pool/splash, no flow-shader test, edge-on read is thin; falls are seed-placed not drainage-driven
- output0 uses prim attrs @strata/@cliff/@band (not point attrs) because points are shared across pieces
- Renders are clay Mantra only (no UE materials) and carry the license watermark; they predate a collision-only envelope tweak (output0 unchanged)
- Verification of containment is a 400-sample ray probe, not an exhaustive proof; ray offset 3 mm below each sample
- I did not write the registry; registry_entry was validated by running hda_verify.py against a temp registry in the scratchpad (PASS)
- Houdini backup stubs HDA_Faraway_TerracedIsland_1.0_bak1-12 were created by my rebuilds and deleted; hda/README.md and other Faraway HDAs untouched

### Faraway Motherfold Basin (`HDA_Faraway_MotherfoldBasin_1.0.hda`)
**What it is:** a global-coordinate terrain tile (world +-4000 m, same grid convention as SilkPeak) that carves a turquoise lake basin into a gentle pleated-silk base. A smooth bowl, a flat shallow shelf, a travertine-stepped bank and a low rim lip. `output0` is the terrain, with point `@depth01` (0 dry to 1 deepest), `@carve` and global `uv`. `output1` is the shoreline polylines at water level, with prim `@depth`, `@closed` and `@loop_id`. Closed loops are emitted where the tile holds the whole shore. Open chains end exactly on the tile border. They are sorted closed-first, then longest-first, and every closed loop winds with positive (x,z) area, so water is inside. `output2` is a single flat water quad (`piece="water"`) at water level, clipped to the tile and the lake square, with world-metre/100 UVs. Water level = `base_height - basin_depth*(1-water_level_frac)`, independent of the tile.
**Real-life reference:** Lake Tekapo and Lake Pukaki (glacial turquoise basins), Plitvice terraced lakes (shelves and drop-offs), Pamukkale travertine rims (the stepped bank and rim lip).
**Measured (default tile -250,-250, 500 m, 128 divs):** 16641 pts / 16384 prims, all prims face +Y by `prim.normal()`. Land height 30 m, water level 25.2 m, terrain 6.1 to 33.8 m, max water depth 19.2 m. Shoreline is 1 closed loop, 626 pts, mean radius 155.5 m, area 75,825 m^2. The water quad is 396x396 m. Two adjacent 250 m tiles (x=-250 and x=0, divisions 64) that both hold lake: shared edge shows 41 wet / 24 dry samples, worst |dY| = 0.000000 m (limit 0.01), depth01 identical. Both shorelines end at the same border point (z=-158.5).
**Blender-user controls:** Preview Mode (coarse grid, caps at 32 cells); Tile Origin X/Y (m, global); Tile Size (m); Divisions; Lake Centre X/Y (m, global); Lake Outer Radius (m); Basin Depth below Rim (m); Shallow Shelf Width (m); Water Level (0.3 low to 0.95 brim); Land Height at Rim (m); Silk Pleat Wavelength (m); Silk Pleat Height (m); Seed.
**Materials (existing MIs only):** terrain `MI_Mother_Mantle`, water `MI_Copernicus_SilkWaterfall`, shoreline `MI_Mother_Veil`. Nanite on for terrain only. Output names are `SM_Faraway_MotherfoldBasin_{Terrain,Shoreline,Water}`.
**Not done:** no UE import and no .uasset. No rim-scatter, PCG water-edge hookup or Oceanology water in UE. Water is one static quad with no waves, flow map or shore foam. Shoreline is a contour of the 3.9 m grid, so it is scalloped; finer divisions give a smoother curve. Dry land is bounded so it cannot dip below water, so there are no stray puddles from base relief. Only one lake per tile (one centre). Tiles need the same `divisions` and `tile_size` to share edges vertex-for-vertex. Water is not Nanite. Not rendered with Mantra or Unreal.

Known gaps (faraway_motherfold_basin):
- Not imported into Unreal; no .uasset, no PCG_WaterEdgeScatter or Oceanology hookup
- Registry entry not written to hda_registry.v1.json (per instructions); it was tested via hda_verify.py with a temporary registry in the scratchpad: PASS (16641/16384, 626/1, 4/1, drives and restores ok)
- Shoreline is a contour of the terrain grid at ~3.9 m cells and looks scalloped; no smoothing or resampling pass
- Water is a single flat static quad: no flow, wave, depth-fade or foam; depth01 is exported on terrain for the shader, nothing consumes it yet
- Only one basin per tile; adjacent tiles must share tile_size and divisions for vertex-for-vertex edge match
- Preview Mode changes the grid (32 cells), so preview tiles will not share edges with full-resolution tiles
- Clay render is a custom numpy rasteriser with a few tiny grazing-silhouette back-face specks from its smoothed-normal test; no Mantra or Unreal render
- Builder, geometry module and render script live under gitignored Tools/ and need git add -f; no git add or commit was done
- Houdini bak stubs created for this HDA were deleted; no shared registry, README, CURRENT_STATE or .gitignore touched

### HDA_Faraway_SilkRibbon (`faraway_silk_ribbon`)
**What:** wide floating silk ribbon for the Faraway sky. Optional input 0 is a guide curve; with nothing connected, a built-in swooping 3D spline of `length` metres is used. output0 is the ribbon: two oppositely wound sheets (front/back, +-1.5 mm apart) with width taper, sinusoidal edge ripple and a twist. output1 is the guide, resampled to points plus one polyline, with `@pscale` = local width. Materials: front MI_Copernicus_SilkWaterfall, back MI_Copernicus_FarawayCelestialSilk. Nanite flag is set to 1; WPO on Nanite is a material-side decision and has not been tested.
**Real-life reference:** Heian/Hanfu hagoromo ribbon sleeves; rhythmic-gymnastics ribbon arcs; Fortuny pleated silk; aurora curtains.
**Measured (defaults):** output0 2178 pts / 1920 prims (121 x 9 grid per sheet, 8 across); output1 121 pts / 1 prim. Guide length 24.003 m. Bbox about 18.1 x 6.4 x 5.8 m. Tightest bend radius 1.77 m. Width 1.2 m tapering to 0.72 m. Preview mode gives 410 pts / 320 prims. Every front/back pair faces away from each other by Houdini's own `prim.normal()` (960/960 and 960/960, with and without an input curve), and there are 0 normal fold-overs along the strip.
**Attributes for a VAT or UE WPO pass:** points carry `rest_u` (0-1 along length), `flutter_phase` (0-1 turns of the ripple), `edge_weight` (0 centre, 1 edge), `uv` (u along length, v across width) and `N`. Prims carry `piece` (front/back), `unreal_material` and `is_guide`. Detail attributes: `unreal_output_name`, `ribbon_length`, `min_bend_radius`, `from_input`.
**Controls for a Blender user:** Preview Mode (low-res); Ribbon Length (m; ignored when a curve is plugged in); Ribbon Width (m); Twist (full turns along length); Edge Ripple Height (m); Ripple Wavelength (m); Taper to Tip (0 none, 1 point); Length Segments; Seed; Base Tilt (deg; 0 = upright curtain, 90 = flat sheet; extra control beyond the brief).
**Not done:**
- No Vellum solve and no baked VAT texture. Only the attributes a later pass needs are provided.
- Not imported to UE; no .uasset exists.
- No collision output, by design.
- A plugged-in curve is Catmull-Rom smoothed. A curve bending tighter than half the ribbon width will self-intersect, and only the built-in curve is checked for this.
- Back sheet UVs match the front's (not mirrored).
- Quad tessellation is fixed at 8 across (4 in preview).
- The `ArpeggioStair` and other HDAs were not touched.

Known gaps (faraway_silk_ribbon):
- Not imported to UE; the Nanite flag is set but no UE import was done, and no UE material or WPO was tested.
- No Vellum or VAT bake: only the rest_u, flutter_phase and edge_weight attributes are provided for a later pass.
- I did not run hda_verify.py, because it reads the shared registry and I was told not to edit it. The registry_entry is a hand-built object whose counts match a fresh default cook (2178/1920 and 121/1).
- Self-intersection is only checked for the built-in guide (bend radius 1.77 m at seed 11, and 1.24 m at seed 12345 in a separate pure-Python run). A user curve with a bend tighter than half the width will intersect itself.
- Clay renders use a custom numpy rasteriser, not Mantra. The Houdini logo is not present. The shading of some surfaces is near-black from the two-light clay setup. I did not open ribbon_side.png or ribbon_under.png.
- I added one control beyond the brief, base_roll (Base Tilt). I also fixed an early bug where the default guide had a near-kink, found by the facing check, by softening the built-in spline.
- The builder and geometry files sit under the gitignored Tools/ directory and need force-adding. The registry, README and CURRENT_STATE were not edited.

## Listening Orchard Tree HDA (`HDA_Faraway_ListeningOrchardTree_1.0`, registry id `faraway_orchard_tree`)

**What it is.** One bespoke hero blossom tree for the Listening Orchard (no Brushify, no scanned asset). Pure-Python geometry (`Tools/Houdini/faraway/orchard_tree_geometry.py`) embedded in a Python SOP; builder `build_faraway_orchard_tree_hda.py --verify`; clay review `render_faraway_orchard_tree.py`. Tools/ is gitignored: force-add the three scripts. HDA at `hda/` with mirror in `Content/HDA/`. Lab build: not imported to UE, not promoted.

**Real-life reference.** Jindai Zakura (Yamanashi, ~2000-yr weeping cherry, fluted buttressed trunk), the Yoshino/Okazaki cherry crowns, Hokusai-era gnarled sakura, and the layered tiered branching of Cedar of Lebanon.

**Method.** Fluted trunk (3 spiral lobes, twisting centreline, base flare) + 5 buttress roots + central leader and 4 limbs, then recursive tapered-tube branching (3 children per branch, radius x0.68, shorter and more drooping each level), deterministic by seed. Every tube and blob is a closed capped solid oriented by signed volume.

**Pieces (`@piece`).** `trunk`, `root`, `branch` (bark MI `MI_Copernicus_CherryBlossomWood`); `blossom_cards` (`MI_ProcFoliage_Sakura`, random-orientation quads, `@blossom_id` unique, `@blossom_tint`, vertex `uv` 0-1); `canopy_proxy` (6 lumpy low-poly blobs for LOD, same MI); `trunk_collision` (output1 only). Also `@branch_level`, `@solid_id`, `i@unreal_nanite_enabled`.

**Measured (default, hython 22.0.368).** output0 11,176 pts / 4,770 prims (2,063 cards, 78 closed solids, 0 inverted); output1 16 / 10. Height 8.78 m to branch tips (bbox y max 9.19), crown radius 5.7 m, trunk 2.7 m tall at 0.75 m radius, trunk volume 5.0 m3. Preview Mode 4,770 -> 1,656 prims. Trunk base is buried about 0.5 m below y=0.

**Blender-user controls.** Tree Height (m); Trunk Radius (m); Branch Levels (1-4, like subdivision depth); Branch Spread (higher = flatter, wider crown); Trunk Twist (turns of spiral fluting and wobble); Blossom Cards per Metre of Twig (like a particle count); Seed; Preview Mode (fast viewport, quarter cards and low-poly tubes).

**Not done.** No UE import or Nanite/LOD tier setup; blossom look depends on the alpha card material (untested in UE); crown is clumpy rather than a dense full-bloom dome; no weeping-willow droop control; twigs are 3-5 sided hard-faceted; leader joins the trunk with a small visible collar; no wind/pivot-paint vertex data; seed variety not yet reviewed beyond seed 12.

Known gaps (faraway_orchard_tree):
- Not imported to UE; blossom_cards and canopy_proxy use MI_ProcFoliage_Sakura which I only confirmed exists in origin/main, not that it suits quad cards (needs an alpha/mask card texture in the MI).
- Crown reads as clumps of cards at twig tips rather than a dense continuous bloom; card flat-shading is visually crude outside the engine.
- Trunk base cap is tilted and buried about 0.5 m below ground (bbox y min -0.52); small collar step where the leader leaves the trunk.
- Collision proxy is a straight 8-sided tapered cylinder; the twisting trunk deviates from it by up to about 0.3 m.
- Nanite flag set to 1 on all prims including cards and the LOD proxy, following the template; may need per-piece handling at UE import.
- Registry entry returned only; did not run hda_verify.py (it reads the shared registry). Builder --verify passes on its own checks. Renders used the numpy rasteriser, not Mantra.
- No PIE/UE import, pivot or wind vertex data, and only seeds 11 and 12 were cooked.

### G1 stitch proof (lab, Houdini-only, 2026-10-23)
**What it is:** `Tools/Houdini/faraway/g1_stitch_proof.py` (hython) cooks four 250 m SilkPeak tiles (existing HDA, untouched) into a 500x500 m crop with min corner (-1150,-100), 128 divisions each. The crop is built so the peak anchor near (-900,300) is inside. It proves the borders, extracts the Chladni nodal seam, conforms it to the terrain and places the Heart Gate on it. Output is in `Saved/Audit/faraway_g1/`.
**Real-life reference:** a seam-matched tile set works like DEM tile mosaics (USGS, swisstopo): shared edge samples, no tile-local resets. The nodal line is the Chladni sand-figure line of a vibrating plate. The gate is a Gothic lancet portal in the Sainte-Chapelle and Poitevin archivolt manner.
**Measured gates** (acceptance.json; Houdini 22.0.368 education, 68.3 s, peak working set 889 MB):

| Gate | Result |
|---|---|
| 4 tiles cook, 16641 pts each, on the global lattice | PASS (snap error 0) |
| Border positions, 4 internal edges x 129 samples | PASS, worst 3D delta 0.0 m (limit 0.01) |
| Merged+fused mesh | PASS, 66049 = 257^2 pts, 65536 prims, 100% prim.normal() +Y |
| HDA VEX re-run vs tile heights (exact oracle) | PASS, max dh 0.0 m |
| **Border NORMALS dot >= 0.98** | **FAIL**: min A tile/tile -0.816, B tile/merged 0.303 (primary), C tile/analytic -0.255, D merged/analytic -0.116 |
| Seam weld (marching squares, 0.5 m lattice, per tile) | PASS: 1 polyline, 500.0 m, 1 border key welded, 0 breaks, per-tile segments identical to whole-crop pass |
| Oblique stress seam (field-only, anti-diagonal X+Y=0, 45 deg across both borders) | PASS: 2 border keys welded, 0 breaks, identical |
| Seam conformed | PASS: 1001 pts, mesh vs true field deviation in seam_longest_conformed.json |
| Gate outward (signed volume by prim.normal(), world = local x S^3) | PASS |
| Gate straddles seam | PASS: piers at +-12.5 m have Chladni -0.0086 / +0.0086, tangent error 0.000 deg, gate centre on seam |
| Gate grounded (placed at (-931,0), base 74.0 m, yaw -90, scale 4) | PASS under my own rule (embed <= pier height 12 m); embed 8.54 m, float 0 |

**Normals method, stated:** B = each tile's exported Normal-SOP vertex normal (point-averaged) vs the normal of an object_merge, fuse (0.001 m) and Normal SOP chain using the HDA's own compute_normals parms. A and C are reported beside it. The threshold was not tuned. Cause, measured: the pleat field pow(abs(sin),0.7) is so sharp at 1.95 m cells (max edge slope 76 deg) that one-sided normals disagree on any row or column, not only on tile borders. Interior row cuts have 85% of nodes below 0.98; the y-border row cut has 93%. Interior column cuts have 18%; the x-border column cut has 18%. Positions stitch exactly. Normals need a 1-cell halo, normals recomputed from the global field in UE, or a softer pleat profile.
**Blender-user labels used:** Tile Origin X/Y, Tile Size (m), Divisions, Peak Height, Pleat Wavelength, Pleat Depth, Seam Valley Width/Depth. Gate left at default params; only the object transform (uniform scale 4, yaw -90) was set.
**Not done:** no UE import; no Mantra render (clay rasteriser only); SilkPeak HDA not changed; gate has no pier skirts or flattened pad; the nodal seam in this crop is the straight line Y=0; the plan section "Harmonic Continental Genesis" was not found by grep, so the G1 wording came from the task text.

Known gaps (g1_stitch_proof):
- G1.07 border normals FAIL, not tuned: min dot 0.303 (tile vs merged+fused, primary), -0.816 (tile vs tile), -0.255 (tile vs analytic). Positions are exact (0.0 m). Cause measured: pow(abs(sin),0.7) pleats at 1.95 m cells give 36% of edges over 45 deg and 85% of interior row cuts under 0.98 dot, so the border is not special. Needs a SilkPeak HDA fix (halo or analytic normal output, or a softer pleat profile), which wa
- Gate embeds 8.54 m on the high pier side, about 71% of the 12 m pier height, because the pleats are about 9 m peak-to-peak every 22 m and run along the seam. My pass rule (embed <= pier height, nothing floats) is my own invention, not from the plan. A real build needs pier skirts or a flattened pad.
- The main seam is the axis-aligned nodal line Y=0 and sits exactly on lattice rows. The oblique anti-diagonal stress test is field-only (no terrain cooked) and uses a different crop.
- Renders are a numpy z-buffer clay rasteriser, not Mantra or UE; shading uses analytic normals so they cannot show the normal seam; seam and border ribbons are lifted overlays.
- Gate placement is Houdini-only: gate_placement.json holds translate, yaw and scale. No UE import or collision proxy placement was done.
- The plan section 'Harmonic Continental Genesis' was not found by grep in the fabric-mountain build doc; the G1 spec was taken from the task text.
- The gate scale of 4 is a free lab choice (--gate-scale); embed was about 8 m at scales 2, 3 and 4 alike.

### Silk ribbon status
Builder `--verify` passes but the repo gate FAILS its restore-after-drive probes (restored cook returns the 121-pt guide curve instead of the 2178-pt ribbon). Registry status is `missing` (owed); the HDA and builder are NOT in the safety commit.

### G1 proof gates (acceptance.json)
| Gate | Status |
|---|---|
| G1.01_tiles_cook | PASS |
| G1.02_global_coords | PASS |
| G1.03_border_positions | PASS |
| G1.04_merged_fused_mesh | PASS |
| G1.05_prims_face_up | PASS |
| G1.06_height_oracle_matches_tiles | PASS |
| G1.07_border_normals | FAIL |
| G1.08_seam_weld | PASS |
| G1.08b_seam_weld_oblique_stress | PASS |
| G1.09_seam_found | PASS |
| G1.10_seam_conformed | PASS |
| G1.11_gate_cook_outward | PASS |
| G1.12_gate_straddles_seam | PASS |
| G1.13_gate_grounded | PASS |
| G1.14_hero_renders_written | PASS |
| G1.15_visual_review | PASS_WITH_NOTES |

Overall **FAIL**; failed: ['G1.07_border_normals']; pending: ['G1.15_visual_review']. Elapsed 68.3 s, peak 889.2 MB.
