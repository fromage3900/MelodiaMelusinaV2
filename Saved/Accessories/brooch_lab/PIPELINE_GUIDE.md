# Melodia Blender asset pipeline — PIPELINE_GUIDE (v7 era)

Repeatable system for building production assets (brooch now; jewelry, props, accessories next)
as **live Blender sessions driven through the MCP bridge**, with the genome layer as data
authority and one Geometry Nodes tree as the geometry authority.

If you are an agent picking this up: read this file, then look at the exemplar pair
`Tools/gen_flower_brooch_v10.py` + `Tools/gen_brooch_sparkles_v7.py`, and copy the pattern for a
new asset. Everything below is hard-won — do not "improve" it without a measurement.

---

## 1. Architecture (ownership)

    genome JSON (traits)  ->  GN builder (Tools/gen_<asset>_vN.py)
        -> [optional in-tree cast SDF finish: MeshToSDFGrid -> Fillet -> Mean -> GridToMesh]
        -> [optional auto UV: UV Unwrap (SLIM) -> StoreNamedAttribute "UVMap"]
        -> object modifier stack: GN -> Bevel_Detail -> (user Outline) -> GN_Sparkles
        -> verification (numbers + renders) -> SDF.R / Deep Paint finishing stages (one-way)

- **Genome owns intent** (counts, sizes, materials names, real-world mm target).
- **The GN tree owns geometry.** Never fork geometry into a second authority (that is why
  Sverchok was retired from brooch scenes — the addon stays installed, but out of these scenes).
- **SDF.R / Deep Paint are finishing stages, one-way**: snapshot input -> finished mesh output.
  They never become live geometry authorities and never overwrite the parametric object.
- **One editor, one writer**: all live edits go through the bridge
  (`Saved/Audit/nikki_decor/blender_live.py`). Serialize; never run two writers on one session.

## 2. Scene + unit conventions (do not deviate)

- Scene scale: **1 unit = 100 mm** (`unit_settings.scale_length = 0.1`, `length_unit = 'MILLIMETERS'`).
- Builder computes in "pre-scale" units where the crown spans O(1); `mm(v) = (v / 100.0) / max(S, 1e-9)`.
- **Two-pass sizing**: pass A builds at `Real Scale = 1.0` with cast OFF, measures the GOLD
  material slot only (frame pinned to 1, non-GN modifiers hidden -> `gn_only`), solves `S`;
  pass B rebuilds with `Real Scale = S` (cast ON). Report `err%` vs `traits.size.real_mm`.
- Report is written to `Saved/Accessories/<asset>_lab/BUILD_REPORT_V<N>.txt` on every run.

## 3. The socket contract every builder must expose

Design intents (counts, radii, tilt, materials switches) + this fixed core:

| Socket | Type | Default | Meaning |
|---|---|---|---|
| Real Scale | Float | solved S | final uniform scale (pass 2) |
| Cast Finish | Bool | **OFF by default (opt-in)** | in-tree SDF weld/fillet of the metal body. The SDF weld is a voxel remesh — it destroys edge flow (owner call 2026-09-17); keep it OFF for the live model and use it only as a finishing/derived pass |
| Cast Voxel (mm) | Float | 0.25 round / 0.35 pointed | voxel size for the cast chain (when cast is ON) |
| Cast Fillet Iters | Int | 1 | SDF fillet iterations |
| Auto UV | Bool | OFF | UV Unwrap (SLIM) + store `UVMap`; slow — ON for export/final |

Cast calibration law (measured, keep it): **mean smoothing erodes thin blades.** Round-petal
genomes: voxel 0.25 mm + mean 2 iterations. Pointed/thin genomes: voxel 0.35 mm, **mean 0**.
With those, all five brooch genomes land within 5% of target with cast ON. Finer voxel =
prettier surface + heavier eval; coarser + mean = thin geometry shrinks.
**Cast is OFF by default since 2026-09-17 (owner call):** the in-tree SDF weld is a voxel remesh
and the resulting wireframe has no edge flow — unusable as the live model's topology. The live
stack is now the clean parametric geometry (quad-dominant; subd petals); with cast off the
two-pass solve is exact (all 7 genomes 0.0% err). Turn Cast Finish ON only for an opt-in
finishing/derived pass (beauty renders, weld look), never as the shipped state.

## 4. Run it (exact commands)

    # sanity: session alive
    python Saved/Audit/nikki_decor/blender_live.py --ping          # -> {"pong": true}

    # build all genomes (passes A+B, measure, attach hero, save)
    python Saved/Audit/nikki_decor/blender_live.py --file Tools/gen_flower_brooch_v7.py

    # sparkle companion (second modifier, togglable, never enters bevel/outline)
    python Saved/Audit/nikki_decor/blender_live.py --file Tools/gen_brooch_sparkles_v7.py

    # UV verify + presentation (compositor glare) + glow/flat comparison renders
    python Saved/Audit/nikki_decor/blender_live.py --file Saved/Audit/v7_presentation.py

    # proof render set (front tq / top / back / catch macro / petal macro) + save
    python Saved/Audit/nikki_decor/blender_live.py --file Saved/Audit/v7_shots.py

    # portfolio intake: beauty set + wireframe/clay breakdown + manifest -> Saved/Portfolio/Intake/
    python Saved/Audit/nikki_decor/blender_live.py --file Saved/Audit/brooch_intake.py

Notes: the bridge runs scripts inside the already-open session; it returns the script's stdout.
Frame is pinned to 1 for shots because the in-tree bloom driver animates geometry; restore the
user's frame afterwards (`v7_shots.py` does).

## 5. Verification standard (no vibes)

1. **Numbers before renders**: per-genome gold dims vs `real_mm` target, err% printed; hardware
   span (hinge->pin tip) printed; material-slot breakdown printed.
2. **Renders are evidence only with a committed script** that produced them (`v7_shots.py`).
3. **Hide everything but the asset** for shots (all object types except lights/cameras/_LAB*),
   restore after. Stray scene objects otherwise read as asset defects (this happened twice).
4. When an image shows something suspicious, **diff against a re-render** before believing it
   (the "floating white cluster" was three stray baked objects, proven numerically).
5. Keep an eye on Moiré reads from vision: check the actual numbers when a visual claim matters.

## 6. Pitfalls ledger (each one cost a run — keep them here)

- **No torus primitive node in this build.** Rings = curve circle + circle profile + curve-to-mesh.
- **Mesh CONE primitive is 0-based** (base at z=0, apex at +depth); every other primitive is centered.
- **SDF Grid To Mesh outputs no UVs** (and neither does the rest of the parametric chain) — the
  final mesh needs the opt-in Auto UV chain to be texture-ready.
- **There is no Pack Islands node** in this build; the UV Unwrap node (Method = MINIMUM_STRETCH)
  is the unwrap authority. `GeometryNodePackUVIslands` does not exist.
- **The Auto UV chain needs its Geometry input linked**: `Store Named Attribute` with an
  unconnected Geometry input yields an empty branch — the switch silently produces no attribute.
- **Interface defaults do not drive a bound modifier in a live session.** To flip a socket at
  runtime write `mod.properties.inputs[<socket identifier>]["value"] = v` (identifier from
  `tree.interface.items_tree`); setting the tree's interface default alone is a no-op for the
  already-attached modifier.
- **UV Unwrap `Method` is an enum of display strings** ('Angle Based' / 'Minimum Stretch');
  iterate `enum_items` and match the identifier, then read the value back to confirm.
- **Compositor moved in 5.x**: scenes have `scene.compositing_node_group` (a `CompositorNodeTree`
  node group); `scene.node_tree` is gone. Build **Render Layers -> Glare -> Group Output("Image")**
  inside the group — there is no `CompositorNodeComposite` node in this build. The Glare node is
  socket-driven: `Type` menu takes display strings ('Fog Glow', 'Streaks', ...), `Quality` takes
  ('High'/'Medium'/'Low'), and there is NO `Mix` input any more — use `Strength` (~0.5) with
  `Threshold` 1.0 and `Size` 0.6. Renders fail with "Cannot render, no camera" when the scene
  camera is None — shot scripts that create and remove a temp camera leave it unset.
- **Int sockets reject floats**: RandomValue `Seed` must be set with `int(seed)`.
- **Field nodes have no Geometry in/out**: `UV Unwrap` is a field source (out: `UV`); wire it into
  `Store Named Attribute` (data_type FLOAT2, domain CORNER, name `UVMap`).
- **Measure with `gn_only`**: the user may have extra modifiers (e.g. their toon Outline) whose
  shells pollute the evaulated material list and bbox. Measure the GN output only, frame pinned.
- Blender's SDF mean pass: see §3. Median exists too (`GeometryNodeSDFGridMedian`) — use it when
  you want noise reduction that preserves sharp features better than mean.
- `Raycast` node exists (single ray, inputs Source Position / Ray Direction / Ray Length) — useful
  for future engraving/inlay detail; per-element queries use `Sample Nearest Surface` (proven).
- Modifier order is load-bearing: **GN -> Bevel_Detail -> user Outline -> GN_Sparkles**.
  Bevel before Outline keeps the outline shell from remapping material slots.

## 7. Presentation state (editorial polish)

- Scene compositor group `Melodia_Presentation`: Glare FOG_GLOW (threshold 1.0, size 7,
  mix -0.7). It is scene-level; to render "flat" set `scene.compositing_node_group = None`.
- Two presentation modes are legitimate: **game look** (Outline modifier ON — toon/anime read)
  and **jewelry look** (Outline OFF — cast gold read). The shoot script isolates the asset; the
  outline belongs to the user's stack, not the builder.
- `MID_Sparkle` (created by the sparkles script) is emissive: emission color (1.0, 0.62, 0.78),
  strength 3.5. `MID_Bead` already carries thin-film iridescence (460 nm / IOR 1.5).
- VFX layer today: the sparkle field (time-driven twinkle, per-point scale/rotation). Next
  candidates: volume glow around the bloom, per-petal emissive veins — both must ride sockets,
  never hard code.

## 8. SDF.R + Deep Paint (evaluated — keep staged, one-way)

- **SDF.R (rust_gpu_sdf_addon)**: R1 spike RAN. Finding: **it does not ingest mesh geometry.** Objects
  in its stack are classified from their NAME ('box'/'cube' -> box, 'torus' -> torus, 'cylinder' ->
  cylinder, anything else -> sphere); the mesh's vertices are ignored. Feeding the v7 gold body
  produced a default 2-unit sphere — a 200 mm cube/ball, not the brooch. Its real capability is a
  PARAMETRIC primitive stack (primitives + deformers + lathe/curve shapes, per-item Round/Sharp/
  Soft/Tight/Chamfer edge profiles and smoothness, noise fields), resolved by a Rust GPU mesher
  (MC or DC, chunked fallback, async engine + timer). Verified working: a 3-piece test vocabulary
  (cylinder / rounded box / torus, chamfer profile, res 448, DC) baked to 48,550 verts / 97,096
  polys with 0 non-manifold edges. Working notes: ops are object-context dependent; the engine is
  ASYNC — trigger with `rust_gpu_sdf_addon.engine.update_sdf_mesh(out)` (or the panel buttons),
  results land on an app timer, so poll `len(out.data.vertices)` / `rust_gpu_sdf.is_updating()`
  between bridge calls (a `time.sleep` loop works, since the Rust compute runs off the main
  thread); `sdf.bake_mesh` writes `SDF_Snapshot_NNN`; diagnostics via
  `eng.set_diagnostics_flags(mesh_debug=True)`.
  Verdict: keep SDF.R as an optional PARAMETRIC FINDINGS LAB (standalone parts -> bake -> derived
  artifact). It is not a mesh-finishing pass for the crown; the in-tree GN cast chain stays the
  finishing authority. Scripts: `Saved/Audit/sdfr_spike_setup.py`, `sdfr_spike2.py`,
  `sdfr_parametric.py`; evidence render `sdfr_parametric_vocab.png`.
- **Deep Paint Pro**: surface stage on the finished hero — nacre variation, gold patina/wear,
  plus its quadify / voxel remesh / boundary-aligned remesh as cleanup for baked meshes; its
  outline vertex-group tooling can drive the user's Outline modifier per part.
- Do not wire SimpleBake -> blender_to_unreal until the wardrobe/accessory hook actually needs it.

## 9. Adapting to a new asset (checklist)

1. `Saved/Accessories/<asset>_lab/genome/` — traits JSON(s) with `size.real_mm` set from real
   reference research (this is how the hero brooch got its 60 mm target).
2. `Tools/gen_<asset>_vN.py` — copy the previous builder file, then patch. Keep the helper set
   (`mk/L/d0/dn/mathx/combine/geo_switch/iface/measure/gn_only/attach`) — it is the portability layer.
3. Expose the §3 socket contract even if the asset has no cast/UV story yet (uniformity lets the
   same verification scripts run).
4. Write `Saved/Audit/<asset>_shots.py` — isolate, shoot set, restore, save.
5. Record results in `Saved/Accessories/<asset>_lab/BUILD_REPORT_V<N>.txt` + a short session note.
6. Only then consider an SDF.R / Deep Paint pass — as a derived artifact, never the source.

## 10. Session results — 2026-09-16 (v7 + this doc)

- v7 built, calibrated over 5 live runs; all genomes ≤5% err with cast ON (hero 59.4/60 mm,
  mini 31.1/32, halo 49.5/50, comet 65.8/68, nova 52.2/55).
- Cast finish: in-tree SDF chain with per-profile defaults; stair-stepping resolved by the mean
  pass at 0.25 mm (round profiles).
- Hardware v7: hinge end-collars + jaw pivot boss; pavé seated by surface sampling
  (bead center = surface + 0.38 r; cups at -0.45 r).
- Sparkles: GN_Brooch_Sparkles_v7 + MID_Sparkle emissive.
- Auto UV: opt-in chain (UV Unwrap SLIM -> StoreNamedAttribute `UVMap`) verified live — the uv
  layer appears with the socket ON, at a 42 s re-eval cost on the 235k-vert cast body (keep OFF
  while dialing). Measured pack utilization is poor (u 0..0.025, v 0..0.76) — tune the unwrap
  before texturing (there is no Pack Islands node in 5.2).
- Presentation: `Melodia_Presentation` compositor group (Render Layers -> Glare -> Group Output),
  tuned to Fog Glow, strength 0.28 / size 0.40 / threshold 1.2 / warm tint — reviewed as subtle
  and presentable ("light escaping the metal"). Scene-level; set `compositing_node_group = None`
  for flat renders.
- Materials polish (live, idempotent via `Saved/Audit/brooch_material_polish.py`): MID_Bead
  roughness 0.12 + subsurface 0.12 + IOR 1.55 (pearls now read volumetric); MID_Sparkle base
  colour pink + emission 4.0 (grazing star faces no longer read as dark slivers).
- Known residual at review time: the top-right accent pearl shows a dark wedge (petal overlap or
  clipped reflection), and the toon Outline remains the dominant stylization — both are knobs,
  not defects: outline off for jewelry-look renders, nudge that accent's radial offset if it
  matters.
- v8 GALA shipped (same day): faceted gems + bezel cups + prong-set centre or EMPTY SOCKET
  (reliquary), en-tremblant dangles with per-dangle sway + still-pose control; two gala genomes
  (tide 61.4/62 mm socket, umbra ~57/58 prong); originals unchanged (traits-absent = v7 path).
  Intake lane: `Saved/Portfolio/Intake/<AssetId>/` (beauty + wireframe/clay breakdown + manifest);
  contract in Saved/Portfolio/Intake/README.md; runner `Saved/Audit/brooch_intake.py`.
- Roadmap now: R1 SDF.R — DONE (negative result: parametric only), R2 Deep Paint surface pass,
  R3 pearl/gem material polish, R4 rhythm-pulse VFX hook, R5 UV fix + texture + UE export bake.
- v10 PETAL REBUILD LANDED 2026-09-16 (P0 of `BROOCH_V10_GRANDMASTER_PLAN.md`): curve-cage
  dual-sheet petals + SubdivisionSurface L2 with a midrib crease replace the v9 grid slabs.
  Margin jaggedness 0.49 -> 0.24 (v7 was 0.45); petals watertight; all 7 genomes <=1.3% sizing via
  the new re-solve pass (cast erosion absorbed automatically). Builder:
  `Tools/gen_flower_brooch_v10.py`; report `BUILD_REPORT_V10.txt`; A/B/C shots
  `Saved/Audit/v10_abc_{v7,v9,v10}_macro.png`. The v9/v7 trees remain in the file as baselines.
- v10 ARCHETYPES WIRED 2026-09-17 (P1 partial): `petal_profile` now selects from a 7-archetype
  table (round, acuminate, spatulate, cordate, frilled, reflexed, cupped) + a `waist` margin
  control; existing genomes rebuild to identical dimensions. Element prototypes (leaf / plume /
  scroll) + contact sheet: `Saved/Audit/v10_arch_sheet_{clay,icon,eevee}.png`.
- v10 TOPOLOGY DECISION 2026-09-17: cast weld (SDF voxel remesh) default REVERSED — live stack is the
  clean parametric geometry; cast stays an opt-in finishing pass. Two-pass solve now exact (0.0% err,
  all 7 genomes). Details in the grandmaster plan, decision H.
- PERF TRUTH 2026-09-17: in-tree SceneTime motion = full brooch regen per frame (GUI 7-9 s/frame,
  headless 0.4 s); idle 0.000 s; draw steady ~18-25 ms. Motion architecture fix = section C of the
  horizon-2 plan below.
- HORIZON 2 OPENED 2026-09-17: `BROOCH_EXPANSION_RESEARCH_2026-09-17.md` — margin system
  (super-ellipse + authored spline margins), curve-polish pass, element library v2 (petal
  alternatives incl. ginkgo / orchid lip / bellflower / snowflake / snail coil / seed-head),
  openwork + setting deep pass, motion split (body cached, dangles live), Studio genome browser,
  catalogue by Melodia registers. Order: C1 motion split first, then A1 margin system.
- C1/C2 LANDED 2026-09-17 (verified live): dangles moved OUT of the body tree into
  `FlowerBrooch_Dangles` (`GN_BroochDangles_<genome>`, own SceneTime per chain; outline mirrored;
  parented, identity local transform). Body tree now time-free by design (`build(..., bloom=False)`
  — bloom is a build-time option; Outline + Sparkle trees' SceneTime removed, outline Freeze
  Frames -> 1). Hero genome gained `dangles{count 8, front arc 150 deg @ 270, links 3, sway 12 deg
  @ 0.7 Hz}`. Sizing law now measures the gold-bbox union of body + dangles: all genomes 0.0% err
  (hero 60.0 mm; hero dangles 13,136 verts). Measured live frame-change cost: 0.42-0.48 s (was
  8-22 s); body static across frames; dangle bbox moves (sway alive). Open: sparkles twinkle (its
  SceneTime is removed until the sparkle field gets its own object) — stage 2. Mechanism note:
  SceneTime in a stack = whole-stack re-cook per frame; muting/deleting the node does NOT clear
  the flag in-session (clean rebuild does).
- M1 MATERIAL IDs LANDED 2026-09-17: per-part IDs with copy-on-first-use (no look change) —
  MID_Metal_Petal / _Dome / _Body / _Setting / _Chain + MID_Bead_Pearl / MID_Bead_Pave; hero
  genome names them, other genomes fall back (byte-identical builds). Cast-ON collapses the metal
  split (SDF weld loses face IDs — why UVs run cast-OFF). `per_mat` in BUILD_REPORT now prints the
  per-part breakdown (verified: petals 59.72, dome 31.49, body 45.81, setting 10.7, pearl/pave/pin
  all sensible; all genomes 0.0% err). Full architecture (IDs + UV/texel-density/UDIM plan + gates):
  `BROOCH_MATERIAL_UV_ARCHITECTURE_2026-09-17.md`. Next: U1 `Tools/brooch_uv_pass.py`.
- SMOOTHNESS RESOLVED 2026-09-17: the last per-frame cost was the hero's TURNTABLE ACTION — any
  animated transform on a heavy object (own action or parent-empty) re-cooks its whole stack per
  frame (0.30-0.50 s). Action detached (kept, fake user) → live frame change 0.015-0.017 s
  (from 8-22 s at the start of the night). Turntables animate the CAMERA, never the piece.
- PETAL MOTION SPIKED 2026-09-17: instanced petal whorls + per-instance SceneTime flutter measured
  IN-TREE at 0.13 s/frame; splitting petals to their own object (dangle pattern; no realize; no
  stack bevel on instanced output) is the planned C3 step, expected 0.02-0.08 s/frame.
- BEAD-RIM SEATING FIXED 2026-09-17: the pave border ring rode a ~25 deg tilted phantom surface
  (z spread 21.4 mm across a constant-radius ring) because `SampleNearestSurface`'s `Value` slot
  (fed a `Position` field) returned positions from the wrong geometry context. Replaced with a
  downward **Raycast** onto `gold_surf` (plate + step) — `Hit Position -> Separate XYZ -> Z + lift`
  — for BOTH the pave ring and the gem sampler. After rebuild: pave z extent 21.41 -> 3.13 mm
  (one bead diameter = a level row); body 20.62 -> 3.34 mm. **Seating law: raycast, never
  SampleNearestSurface + Position-field.** Lesson: `inp.links[0]` on a multi-input socket shows
  ONE link — print the full list before declaring a link missing (the join was never broken).
- PRESENTATION RIG LANDED 2026-09-17: `Tools/brooch_pres_rig.py` (idempotent PRES_RIG collection:
  dark-field backdrop, white + black reflection cards — the black window is the luxury tell — soft
  key, hard gem point, rim, kick, AgX Medium-High, EEVEE 96 spp + raytracing) and
  `Tools/brooch_pres_shot.py` (bbox-framed front / three-quarter / macro stills; toon outline
  forced OFF for stills and restored after). Run: `blender -b FlowerBrooch.blend --python
  Tools/brooch_pres_rig.py --python Tools/brooch_pres_shot.py`. The rig is NOT saved into the
  working file — regenerated per render run, so the scene stays clean. Stills:
  `Saved/Audit/pres_front.png`, `pres_tq.png`, `pres_macro.png`. Tuning dials: key 26 W, gem point
  8 W, white card emission 1.0 — raise carefully; polished-metal edges clip first.
- PAVE JITTER DIAL 2026-09-17 (same day, follow-up): new `Pave Jitter` socket (0..1, default 0.0;
  genome key `pave.jitter`, DERIVABLE) — the border row is machine-regular by construction now.
  Measured after the dial: 79 distinct beads (was 66 with merges), z spread 0.70 mm, plane tilt
  0.01 deg (was 18-25), angular-gap CV 0.311. Residual CV = the phyllotaxis packing law itself
  (gaps 2.9-7.7 deg); if a true single uniform row is wanted, the next dial is an even-coil
  angular law (theta = i*2pi/n) or bead-count-for-touching (~48 beads at r 20 mm for 2.6 mm
  beads) — design call, not yet taken.
- PAVE EVEN LAW 2026-09-17 (same day, second pass): `Pave Even` socket (bool, default ON; off =
  legacy golden-angle spiral) — theta = i*(2pi/n), radius staggered inner/outer by parity (two-row
  pave). Final: **80/80 distinct beads, angular gaps mean 4.500 / std 0.000 / CV 0.000, plane tilt
  0.00 deg, z spread 0.70 mm, pave bbox 44.53 x 44.53 (symmetric)**. Vision reads of identical
  structure disagreed between passes — the row is judged by measurement, not by the vision model.
  If a classic single-strand border is preferred, that is a bead-count dial (~48 beads at r 20 mm
  for 2.6 mm beads), not a defect.
- LUXURY LAYER OPENED 2026-09-17: `BROOCH_LUXURY_AUDIT_2026-09-17.md` (product audit + the bead-rim
  addendum) and `BROOCH_LUXURY_RESEARCH_2026-09-17.md` (web-verified luxury craft) — ranked moves:
  presentation rig (LANDED), the hand/engraving, stones + pearls (phenomenal register = the Melodia
  element language), motion quiver, the story layer.
- MELUSINA SKY PLAN 2026-09-17 (planned, not built): `MELUSINA_SKY_SHADER_PLAN_2026-09-17.md` —
  procedural editorial sky for the pres rig; 8-layer stack, 12 dials, 8 variants (editorial_dark +
  7 element registers, genome-derived); key finding: `PRES_Back` fills the frame, so the sky needs
  TWO carriers (world for metal reflections + backdrop card for visible pixels; dome as fallback);
  builder to be `Tools/brooch_sky.py`; v1 = gradient+glow+grain, v2 = clouds+stars, v3 = variants
  + aurora. Genome colour cross-checks in the doc are correct (linear->sRGB of the live JSONs).
- MELUSINA SKY **v1 LANDED** 2026-09-17: `Tools/brooch_sky.py` (14-node stack per carrier: L0 base
  gradient, L1 horizon glow, L6 grain, L7 strength trim; world + PRES_Back card carriers; no
  textures, no SceneTime). Rig: `--sky <variant>` (default `editorial_dark`; `--sky none` = old flat
  world for A/B). Shot tool writes `sky_<variant>_*.png`; `pres_*.png` remains the no-sky baseline.
  Gates: G1 cost 117s baseline vs 116-118s sky (+0%); G2 pixel-identical reruns (0/12.8M channels
  differ; PNG bytes differ in metadata only); G3/G9 asserted (0 textures, 14<=60 nodes); G4 headless
  x5; G5 black-window reflection intact; G8 zero-dial -> flat field, no regression. G6 note: no
  world-sun threshold exists on `scene.eevee` in 5.2 (`bokeh_threshold`/`light_threshold` only) -
  the plan's sun-extraction action is moot on this build; no shadow change observed.
  Evidence: `Saved/Audit/sky_editorial_dark_{front,tq,macro}.png`, `sky_zerodial_front.png`,
  logs `Saved/Audit/sky_v1_run{2,3,4}.log`, `pres_baseline_run.log`. v2 next: clouds + stars +
  the two decisive experiments (EEVEE background sharpness, Is-Camera-Ray A/B).
- MELUSINA SKY **v2 LANDED** 2026-09-17: `brooch_sky.py` now 30 nodes/carrier: L4 stars (Voronoi
  F1 crush x brightness-variance noise x zenith ramp x star_density; composited BEFORE clouds) and
  L3 cloud band (3D noise x height mask x cloud_coverage; occludes stars). Two bugs found + fixed:
  (1) the backdrop card is rotated 90 deg about X, so its local Z is HORIZONTAL -- the card carrier
  must read local **Y** as up (world carrier keeps Generated.Z); (2) the first-pass cloud colour was
  invisible under the doctrine clamp -- lifted by a base grey (clouds now +0.010 top-strip at full
  coverage). **Experiment 1 (star sharpness): PASS** -- stars render sharp in the EEVEE background,
  world carrier sufficient, no dome needed. **Experiment 2 (Is-Camera-Ray split): WORKS in this
  build** -- two-colour test world showed the camera branch in the background and the other branch
  in the lighting (recorded as available; NOT adopted -- the dark world + card doctrine already
  covers it). Gates: G1 114s vs 117s baseline (+0%), G9 30<=60, G3/G4/G8 hold. Backdrop gradient
  (pure-sky, spec dials): top 0.0114 vs bottom 0.0087 (subtle by design; clouds +0.010 at cov 1.0).
  Evidence: `sky_only_{stars_clouds,clouds}.png`, `sky_cloudnum_{cov0,cov1}.png`,
  `sky_exp_camray.png`, `sky_exp_stars_front.png`, `sky_editorial_dark_{front,tq,macro}.png` (v2),
  logs `sky_exp{1c,2}.log`, `sky_cloudnum.log`, `sky_v2_run1.log`. v3 next: 7 element variant rows
  + aurora + genome auto-select.
- MELUSINA SKY **v3 LANDED** 2026-09-17: `brooch_sky.py` now 37 nodes/carrier: L5 aurora added
  (streak noise stretched vertically x soft upper falloff x aurora_strength, emissive-only per plan
  2.7; non-zero only for gale/umbral). Variant auto-select implemented per plan 3.3:
  `sky_for_genome(gid)` (compose_style -> gems.material_a -> editorial_dark) + `sky_for_object(ob)`
  (reads the hero's GN tree name); the rig's default is now `--sky auto` (verified: hero ->
  editorial_dark, melodia_gala_tide_v1 -> tide, melodia_gala_umbra_v1 -> umbral; a missing genome
  falls back to editorial_dark). All 8 variants rendered (8 x 3 stills, 894 s total ~= 37 s/shot,
  no cost surprise); contact sheet `sky_variants_sheet.png` (row 1: editorial_dark, forte, radiant,
  arcane; row 2: tide, stone, gale, umbral). G10 PASS: all 8 front stills md5-distinct. G5 PASS for
  radiant (piece stays focal, black window reads, the lift reads intentional). The 7 element rows
  are FIRST-PASS values by design (plan 4.4) - the sheet is the review artifact; per-variant tuning
  happens on owner taste. Note: `--sky none` writes `sky_none_*.png` (prefix rule), `pres_*.png`
  remains the untouched pre-sky baseline.
