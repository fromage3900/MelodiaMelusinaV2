# Brooch v10 — Grandmaster designer plan (Nikki-standard, final)

2026-09-16 · STATUS: FINAL for the v10 line. Supersedes `BROOCH_V10_SILHOUETTE_PLAN.md` and the
"v9 identity layer" bullet of `BROOCH_GRAND_PLAN_2026-09-16.md`; absorbs v8 gala + workshop findings.
Identity authority: `BROOCH_IDENTITY_RESEARCH.md`. Pipeline: `PIPELINE_GUIDE.md`.
One geometry authority (the builder). One writer per surface. SDF.R stays out of the geometry path.
Horizon 2 (expansion — margins, element library v2, motion split, catalogue):
`BROOCH_EXPANSION_RESEARCH_2026-09-17.md`.

## 0. Lineage at a glance

    v7   shipped   primitive petals, cast chain, hardware v6/v7, pave, sparkles, presentation
    v8   shipped   gala: faceted gems, bezel cups, reliquary SOCKET, en-tremblant dangles
    v9   REGRESSED  petal block replaced by grid slabs (blocky macro, size err 9-16%) — trees kept as compare baseline
    v10  this plan  curve-native petals + silhouette system + material presets + animation v10 + Studio panel

## 1. Expert review — the v10 silhouette plan through an Infinity Nikki lens

**Meets the house standard already (keep as-is):** curve-native construction replaces the grid slab
("smooth by construction" is the right thesis); archetype + element vocabulary (silhouette first,
decoration second); the reliquary socket and pierced negative space (already v8/identity); en-tremblant
dangles with a still pose.

**What an Infold-grade review adds — 12 upgrades, each lands below:**

1.  **Feeling-first gate.** GDC: one core feeling per piece; every element justified against it.
    -> genome carries `story.feeling`; `BUILD_REPORT_V10` must print the one-line justification an
    element list — a gate line, not prose.
2.  **Silhouette readability.** Nikki grades silhouette first, and at small scale. -> a 64-px icon render
    joins the shot set; `balance{axis,sweep}` lets the spray go asymmetric (radial symmetry is the
    "cheap" read when it is the only mode).
3.  **Jewelry material system.** Refraction + SSS + prismatic sparkle, "shimmer even at night"
    (UE interview). -> the gem stack is formalised (faceted flat + coat + thin film + optional SSS),
    pearl SSS stays, and a **night register** row exists in the presets.
4.  **Two-band motion with propagation.** Today the dangles read as one sine. -> sway band (0.15-0.6 Hz)
    + jewel-tremble band (3-6 Hz), per-dangle phase and per-link lag down the chain — authored, never
    a physics sim; freeze pose = both bands at a rest offset ("as if in water").
5.  **Dual-form beat.** dormant <-> radiant as ONE authored cycle on the bloom driver (closed + dull gems
    -> open + lit gems). No new system; a state pair.
6.  **Bench logic before fantasy.** Prong variants (4-claw / 6-claw / bezel / half-bezel) and a cut
    vocabulary per element (Tide marquise, Forte round, Arcane hex/pear, Umbral cabochon, Stone cab,
    Gale briolette, Radiant brilliant); milgrain / bright-cut borders via Inset Face + bead rows.
7.  **Negative space as story.** Pierced lattice + socket: light-through by day, glow-through by night.
8.  **Story & world.** `story{collection, lore_name, home}` per genome; suite compatibility
    (brooch + hairpin/earring) is wardrobe DATA, never duplicated geometry.
9.  **VFX showcases the feature.** Sparkle field + glow (have) + pulse + **gem glints synced to the beat**
    (delayed ~0.15 beat so it reads as catching the light).
10. **SFX hooks as consumers.** Gem chime on pulse, chain clink on motion — the audio writer consumes;
    never a new writer.
11. **Presentation discipline.** Jewelry-look vs game-look states; night-register test; photo-mode still;
    wardrobe item-icon recipe (= the intake macro).
12. **Craft, then exaggerate.** Measured hardware stays the base; fantasy (gem stamens, scrollwork) rides
    on top.

## 2. Design system (final)

### 2.1 Geometry — curve-native petals + silhouette system

- **Petal**: spine curve -> ResampleCurve (uniform arc length) -> margin profile (ShaderNodeFloatCurve)
  -> lens cross-section lofted along the spine (CurveToMesh, rounded rim by construction) ->
  SubdivisionSurface L2 on a low cage with Edge Crease down the midrib; details (engraving, borders)
  via Inset Face; thickness via Solidify/Mesh Offset. No extruded rims anywhere.
- **Archetypes**: round, acuminate, spatulate, cordate, frilled, reflexed, cupped.
- **Elements**: leaf, plume/feather, wing/paillette, whiplash scroll (Spin), ribbon (Even Curve to Mesh),
  tendril, briolette, scallop fan, cymatic diaphragm.
- **Structure**: openwork backplate (Cairo/Hex/Voronoi grids), Dynamic Catenary garlands, fancy gem cuts
  (Rounded Cube / Pyramid / Rounded Cone), Ripples Solver for the Tide register.
- **Cast recalibration**: voxel 0.20 / Fillet 1 / Mean 0 (pointed) and 0.25 / 1 / 0.5 (round) as the
  opening bid; re-derive per profile under the err<=5% law. Split the weld (metal body vs petals) if thin
  rims still step.
- **Smoothness gate**: petal boundary max turn-angle <= v7 baseline / 2; normal-step histogram clean
  except the crease line.

### 2.2 Material presets (data + apply law)

Preset row schema (JSON):

    name, register(day|night),
    gem{color, rough, ior, film_nm, sss}, metal{tone, rough, film},
    bead{tint, rough, sss}, sparkle{color, strength, rate}, glint{strength, delay_beats}, notes

Base set to author at P2 (names are product strings for manifest + wardrobe cards):

    Hero Pearl Classic (day) · Hero Pearl Classic (night)
    Forte Ember · Radiant Prism · Arcane Veil · Tide Shimmer
    Stone Jade · Gale Zephyr · Umbral Midnight
    Gala Tide (socket) · Gala Umbra (prong)

- **Storage**: `Saved/Accessories/brooch_lab/presets/materials.json` (data authority);
  `apply_material_preset(tree, name)` lives in the builder (the builder creates/updates the MID_*
  materials — same path as today's `make_gem_material`).
- **Panel**: dropdown + Apply + "save current as preset". Night register raises film + adds the gem
  emission ramp + sparkle boost; day register arms the prismatic response without emission.
- **Law**: presets never become a second material authority — they set values on the materials the
  builder owns; apply is idempotent (upgrade-in-place pattern, as `brooch_material_polish.py`).

### 2.3 Animation v10 (updated system)

All in-tree, Scene Time driven; loop = 96 frames; frame 1 = canonical base pose (measurement + shots law).

- **Bloom**: eased open/close (smoothstep or Higgsas Bezier Easing), per-whorl stagger
  (outer 0.00 / inner 0.12 / gems 0.22 phase), dual-form dormant<->radiant (gem emission + sparkle
  ramp tied to bloom phase).
- **Dangles**: sway band + tremble band; per-dangle phase (i x 0.55) + per-link lag (j x 0.35);
  terminal drop 1.3x amplitude; Still Pose socket freezes both bands at a rest offset.
- **Sparkles**: rate/size modulated by Pulse Influence; night register boosts emission.
- **Glints**: per-gem flash on beat phase + 0.15 beat delay — material emission only, no new objects.
- **New sockets**: Bloom Speed, Whorl Stagger, Tremble Amp/Freq, Still Pose, Pulse Influence,
  Register (enum), Sparkle Rate, Glint Strength.
- **Convergence hook**: expose "Musical Freq A/B / Amplitude / Influence" (the universal-music-pass names)
  so Convergence Mode can drive the brooch once it registers as a builder. Consumer only — the
  presentation writer stays the single writer.
- **Animation presets (panel)**: Idle Bloom · Performance (pulse) · Photo Still · Dormant ·
  Display Case (minimal motion).

### 2.4 Melodia Studio UI panel — "Studio · Brooch"

- **Where**: the Melodia Studio tab of the **surreal_arch addon** (the GN ecosystem). NOT the
  `melodia_studio` MIDI-bridge addon (separate, being absorbed as "Resonant World"). New module
  `melodia_gn/brooch_panel.py` beside `stack.py`; panel ids `SURREAL_ARCH_PT_brooch*`; base class per the
  `ui.py` `_V3DBase` pattern (bl_category "Melodia Studio", DEFAULT_CLOSED, poll = active object is a brooch).
- **Panel tree**:

      Studio · Brooch        genome dropdown (lab genome dir) + feeling line + Load / Build / Rebuild + status
      Brooch · Silhouette    per-whorl archetype menus, margin amp/freq/phase, bend/recurve, reflex, roll, balance/sweep
      Brooch · Elements      whorl element assignment + counts
      Brooch · Stones        element dropdown, socket/prong, sizes, cut
      Brooch · Finish        Cast on/off, voxel, fillet, Auto UV; Bake Cast operator
      Brooch · Materials     preset dropdown + register + Apply + Save-as
      Brooch · Animation     preset dropdown + the section 2.3 sockets + Still Pose + pulse toggle
      Brooch · Export        Export GLB, Intake Shots, Open Report

- **Props**: `MELBroochSettings` (PointerProperty on the brooch object or Scene) mirroring the sockets.
  Live sliders write `mod.properties.inputs[identifier]["value"]` (the verified live path); structural
  changes (genome / archetype / counts) call the builder function for a rebuild. Slow ops (cast bake,
  export, shots) are operators with INFO reports.
- **Authority**: the panel is a CONTROLLER, never a geometry authority. Panel and headless bridge scripts
  call the same builder functions; no second code path.
- **Sync law**: edit P: `deploy/surreal_arch/` first -> C: copy -> AppData copy; md5 must print
  `3 <hash>`; then `Tools/verify_addon.py` (GATE RESULT: PASS) + census PASS.

### 2.5 Genome schema v2 (+ preset schemas)

    silhouette{ whorl[ {archetype, count, margin{amp,freq,phase}, bend, recurve, reflex, roll,
                        thickness, balance{sweep,axis}} ] }
    elements{  whorl[ {type, archetype} ] }
    materials{ preset, register, overrides{} }
    animation{ bloom{speed,stagger}, tremble{amp,freq}, sparkles{rate}, glint{strength}, still_pose{} }
    story{ feeling, lore_name, collection, home }
    gems{}, dangles{}, size{}, plate{}, ...   (unchanged shapes)

Absent block = defaults; v7/v8/v9 genomes keep building (only the petal CONSTRUCTION changes for every
genome — that is the point of v10).

## 3. Build order (each phase gates on numbers before the next starts)

    P0  petal prototype (round + acuminate)         gate: smoothness metric + err<=5% cast ON
    P1  archetypes + first three elements + genome silhouette{}   gate: contact sheet + 64-px read
    P2  material system + the 11 presets            gate: apply idempotent, night register render diff
    P3  animation v10 (two-band, stagger, dual form, glints)      gate: frame-hash motion + still pose + frame-1 invariance
    P4  Studio · Brooch panel + operators           gate: live rebuild via panel; headless path identical; 3-copy md5 + verify_addon + census
    P5  Higgsas batch B: openwork, catenary, cuts   gate: numbers + macro shots
    P6  shots (incl. icon), BUILD_REPORT_V10, intake refresh, ledger rows

Deliverables: `Tools/gen_flower_brooch_v10.py`; `Saved/Accessories/brooch_lab/presets/materials.json`;
`deploy/surreal_arch/melodia_gn/brooch_panel.py` (+ import wiring); `Saved/Audit/v10_*` diagnostics;
`BUILD_REPORT_V10.txt`; updated roadmap line in `PIPELINE_GUIDE.md`.

## 4. Verification & discipline (unchanged laws)

Numbers before renders; isolate the asset in shots; err<=5% with cast ON; smoothness gate; one writer per
surface; ledger row or it didn't happen; the cast calibration law stands (re-derived for curve petals);
presets apply idempotently; panel == headless builder (single code path).

## 5. Non-goals

No SDF.R in the geometry path. No second geometry authority (no Sverchok). No physics sim for dangles
(authored motion only). No new wardrobe state from this lane (suite = data only). UE export parked until
the wardrobe hook opens.

## 6. Ledger (fill with dated PASS lines; prose is not a row)

| phase | gate | status |
|---|---|---|
| P0 | petal smoothness + sizing | **PASS 2026-09-16** — margin jaggedness 0.241 (v10) vs 0.492 (v9) / 0.447 (v7), same metric, same clay A/B/C; row-metric corroboration of the staircase measure: v10 step 0.235 vs v7 0.424 / v9 0.491; petals watertight (0 boundary / 0 non-manifold / 0 degenerate / 0 self-intersection); all 7 genomes ≤1.3% sizing after the re-solve pass (hero 60.53/60, mini 31.6/32, halo 49.6/50, comet 68.3/68, nova 55.7/55, tide 62.3/62, umbra 58.3/58). Evidence: `Tools/gen_flower_brooch_v10.py`, `Saved/Audit/v10_abc_probe.py` + `v10_abc_*_macro/top.png`, `Saved/Audit/v10_state_*.png`, `BUILD_REPORT_V10.txt` |
| P1 | archetypes + icon read | **PARTIAL 2026-09-17** — 7-archetype table (round, acuminate, spatulate, cordate, frilled, reflexed, cupped + `waist` param) WIRED into the builder; rebuild reproduces identical dims for all existing genomes (behavior-preserving, all ≤1.3%). Elements prototyped: leaf (clean ✓), plume (clean geometry but reads as split cone — needs a real ragged vane), scroll (reads clearly ✓). Contact sheet + icon-scale read done: single-peak silhouettes survive at 40-50 px; spatulate/cordate/frilled/cupped lose identity at icon scale (refine). Evidence: `v10_arch_sheet_{clay,icon,eevee}.png`, `v10_arch_<name>.png`, `Saved/Audit/v10_archetype_spike.py`. Remaining: genome `silhouette{}` block wiring; element selection per whorl; cast refinement |
| P2 | material presets | open |
| P3 | animation v10 | open |
| P4 | Studio panel + addon gates | open |
| P5 | Higgsas structure batch | open |
| P6 | report + intake | open |

## 7. Change spec — implementation delta (the concrete changes)

Authoritative list of what changes, where, and what proves each one. P0 prototype numbers below are
measured headless on the live file (2026-09-16, `Saved/Audit/v10_petal_proto.py`).

### A. Petal construction (the regression fix) — `Tools/gen_flower_brooch_v10.py`

Replaces `petal_surface()` (20x48 grid + ExtrudeMesh slab) with the verified prototype:

1. cage `MeshGrid` 11 x 20 (odd columns — the crease column must exist)
2. `w(u) = base_w * max(sin(pi * u^tip_pow), 0.04)` — the floor kills the degenerate collapse rows
3. spine `bend*u^2 + recurve*u^4`; cup `cup * (1-|x|)^2 * (1-0.4u)`;
   wave `amp * sin(u*freq*2pi) * (1-|x|)^2`; ridge `ridge * (1-|x|)`
4. thickness `t = thick * (1-|x|)^0.8 * sqrt(4u(1-u))` -> 0 at rim and both ends;
   top sheet `+t/2`, bottom sheet `-t/2`
5. Join -> MergeByDistance 1e-5 -> watertight pillow
6. SubdivisionSurface L2 with Edge Crease `clamp(1 - |x|/0.30)` -> crisp midrib, rounded rim
7. SetShadeSmooth

Measured today, prototype vs the current (regressed) file:

    v10 petal  round      : 0 boundary_e · 0 nonman_e · 0 zero_f · 0 self_x · margin 0.232
    v10 petal  acuminate  : 0 boundary_e · 0 nonman_e · 0 zero_f · 0 self_x · margin 0.316
    v9 petal   (current)  : 144 boundary_e · 670-3121 zero_f · 42,773-45,495 self_x · margin 1.25-1.79

Gate: v10 margin <= half of the regressed value, plus watertight + no self-intersection. PASS on the
prototype. The saved file keeps the v9 petals until the builder port lands.

### B. Silhouette capabilities + polished curves

- archetypes (parameter presets on A): round, acuminate, spatulate, cordate, frilled (width ripple),
  reflexed, cupped.
- new margin controls: ripple amp/freq, tip power, reflex, roll, skew; `balance{sweep,axis}` for asymmetry.
- alternatives to petals (new element subgraphs, same whorl placement): leaf (toothed margin),
  plume/feather, wing/paillette, whiplash scroll, ribbon, tendril, briolette drop, scallop fan,
  cymatic diaphragm.
- polish pass: margins from curve profiles + Bezier Resample (uniform arc length); no boundary is a
  straight polyline segment; creases only at the midrib.
- genome schema v2: `silhouette{whorl[archetype,count,margin{amp,freq,phase},bend,recurve,reflex,roll,thickness,balance{sweep,axis}]}`,
  `elements{whorl[type,archetype]}`.

### C. Higgsas wiring

Library `RawArt/BlenderLibraries/Higgsas/Blender 5.0 Higgsas Geo Node Groups v13.blend` (279 groups,
names WITHOUT the NT prefix). Builder gets `higg(tree, name)`; mapping: Spin -> scrolls/rolled rims;
Bend/Taper/Twist/Twist Curve -> whorl shaping; Loft Splines / Even Grid Profile Surface -> surfacing;
Bezier Resample -> uniform-arc-length margins; 3D Fill Curve -> margin outline -> sheet;
Solidify/Mesh Offset/Edge Offset -> thickness and rims; Inset Face -> engraving/enamel cells;
Dynamic Catenary Splines -> swags and dangle chains; Cairo/Hex/Bricks/Voronoi -> pierced openwork;
Ripples Solver -> Tide relief; Rounded Cube/Pyramid/Rounded Cone -> gem cuts; Scales Texture -> plume
vane. Restore `Tools/higgsas_gate.py` (deleted in the working tree) and extend it with the brooch path.

### D. Melodia Studio panel — `deploy/surreal_arch/melodia_gn/brooch_panel.py`

Imported in `melodia_gn/__init__.py`; Melodia Studio tab; ids `SURREAL_ARCH_PT_brooch*`. Subpanels:
Studio · Brooch (genome + feeling + Build/Rebuild/status) · Silhouette · Elements · Stones · Finish
(cast/voxel/fillet/Auto UV/Bake) · Materials (presets) · Animation (presets + sockets) · Export
(GLB/intake/report). Props `MELBroochSettings`; sliders write
`mod.properties.inputs[identifier]["value"]`; structural changes call the builder rebuild; operators
`surreal_arch.brooch_*`; sync P: -> C: -> AppData with md5 `3 <hash>` + `verify_addon` + census.

### E. Material presets — `Saved/Accessories/brooch_lab/presets/materials.json`

11 rows: Hero Pearl day/night, Forte Ember, Radiant Prism, Arcane Veil, Tide Shimmer, Stone Jade,
Gale Zephyr, Umbral Midnight, Gala Tide, Gala Umbra. Row fields: `gem{color,rough,ior,film_nm,sss}`,
`metal{tone,rough,film}`, `bead{tint,rough,sss}`, `sparkle{color,strength,rate}`,
`glint{strength,delay_beats}`. Apply via `apply_material_preset(tree, name)` in the builder;
idempotent; presets set values on builder-owned materials only (no second authority).

### F. Animations — builder sockets + drivers

New sockets: Bloom Speed, Whorl Stagger, Tremble Amp/Freq, Still Pose, Pulse Influence, Register,
Sparkle Rate, Glint Strength. Bloom eased + staggered (outer 0.00 / inner 0.12 / gems 0.22) +
dual-form dormant<->radiant. Dangles: two bands (sway 0.15-0.6 Hz + tremble 3-6 Hz) with per-dangle
phase and per-link lag; Still Pose = rest offset. Sparkles/glints pulse-synced (glint +0.15 beat).
Convergence hook exposes Musical Freq A/B / Amplitude / Influence (consumer only). Animation presets:
Idle Bloom, Performance, Photo Still, Dormant, Display Case. Loop 96 f; frame 1 = base pose.

**PERF FINDING 2026-09-17 (measured — read before touching motion).** The bloom and the dangle sway
are SceneTime math *inside* the tree, so **any timeline advance re-evaluates the whole tree and
regenerates the entire brooch**. Measured on the hero genome, per frame change: GUI viewport
**7-9 s** (subd L1: 4.6 s) vs **0.4 s** for the identical tree evaluated with all 26 addons in
background mode — the gap is the GUI context, not addons, not sverchok, not the cast socket, not
modifier/object animation (each excluded by probe). The two subd nodes feed a x16 expansion that
every downstream node reprocesses; muting them drops GUI cost 8.5 -> 1.1 s. Idle viewport (no frame
advance) = 0.000 s — the cost exists only on frame change. **Draw cost re-verified 2026-09-17 with
repeatable sampling:** steady-state redraw ~18-25 ms (~40-55 fps); ~100 ms only on the *first* redraw
after a state change. Overlay / compositor / spike / RT toggles showed no reliable steady-state delta —
the earlier "overlay = 7x" reading was a transient; corrected. Consequences:
1. "Dangles live" cannot come from regenerating the tree per frame on this machine. Motion must
   move OUT of the regenerating tree: a separate lightweight dangle object/rig driven by time, so
   the brooch body stays cached while only the chains move. That is the P3 animation revision.
2. Until then: freeze-pose presets = a socket that holds SceneTime constant (Photo Still /
   Dormant); viewport subd L1 / renders L2; wireframe overlay off during work.
3. The hero genome carries NO dangle chains (trait is gala-only: tide 10, umbra 8) — the hero
   tree's "Dangles On" socket is dead. Owner call pending on giving the hero its own `dangles{}`.

**RESOLVED 2026-09-17 night (C1/C2 landed — see `BROOCH_EXPANSION_RESEARCH_2026-09-17.md` section 4).**
Mechanism found: a GN stack containing a SceneTime node re-cooks the WHOLE stack on every frame
change (GUI seconds); muting or deleting the node does NOT clear the depsgraph flag in-session (a
clean rebuild does). Fix shipped: body tree is time-free by construction (`build(..., bloom=False)`
default); dangles live on their own object/tree (`FlowerBrooch_Dangles`, `GN_BroochDangles_<genome>`,
own SceneTime, outline mirrored); hero genome now has `dangles{}` (8 chains, 12 deg @ 0.7 Hz);
sizing uses the body+dangles gold-bbox union (all genomes 0.0% err). Measured live: 0.42-0.48 s per
frame change (was 8-22 s), body static, chains sway, twinkle/wobble frozen pending their own-object
stage 2.

### G. Order

P0 petals (prototype PASS today) -> port into `gen_flower_brooch_v10.py` + hero run (err <=5% cast ON)
-> P1 archetypes/elements -> P2 presets -> P3 animation -> P4 panel + addon gates -> P5 Higgsas
structure batch -> P6 shots/report/intake.

### H. DECISION 2026-09-17 — cast default reversed (topology)

Owner call: the in-tree SDF cast weld is a voxel remesh — its wireframe has no edge flow and is
unusable as the live model (confirmed in the viewport: "cast finish" was the switch). Changes:
pass B and the re-solve now build with `cast_default=False`; the live stack is the clean
parametric geometry; with cast off the two-pass solve is exact (all 7 genomes 0.0% err; hero
59.72 x 60.0 x 23.61 mm, 99,336 verts vs 174k cast). Cast Finish stays a socket = opt-in
finishing/derived pass (weld look, beauty renders), never the shipped state. `BUILD_REPORT_V10.txt`
carries the cast-off numbers.
