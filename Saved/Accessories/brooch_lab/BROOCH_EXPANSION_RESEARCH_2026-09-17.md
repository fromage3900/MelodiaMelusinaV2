# Brooch system — expansion research (horizon 2)

2026-09-17 · STATUS: research agenda. Sits ON TOP of `BROOCH_V10_GRANDMASTER_PLAN.md` (the v10 line
build order, P0-P6) — that plan ships v10; this one expands the *system* past v10.
Identity authority stays `BROOCH_IDENTITY_RESEARCH.md`; pipeline law stays `PIPELINE_GUIDE.md`.
One geometry authority (the builder). The Studio panel is a controller, never an authority.
No Sverchok, no SDF.R in the geometry path, no physics sim for motion.

## 0. Verified starting state (2026-09-17, live session probes)

    petals        curve-native v10, watertight, smoothness 0.241 vs v9 0.492 / v7 0.447 (same metric)
    sizing        cast OFF default, two-pass solve exact: all 7 genomes 0.0% err (hero 59.72 x 60.0)
    cast          opt-in finishing pass only (voxel remesh destroys edge flow — owner call)
    motion        IN-TREE SceneTime -> full-tree regen per frame: GUI 7-9 s/frame, headless 0.4 s.
                  This is the #1 blocker for anything "live". Fix is section C.
    dangles       genome trait, gala-only today (tide 10 / umbra 8 chains); hero tree has none
    OWED          hero dangles decision; P1 residuals (silhouette{} wiring, element-per-whorl,
                  plume vane); P2-P6 of the grandmaster plan.

## 1. Thesis

The brooch stops being "one flower asset" and becomes a **parametric jewelry system**: one builder,
a genome library, a motion model that can actually run live, and a catalogue organised by the Melodia
element registers. Three axes, in build order: **Craft -> Motion -> System -> Catalogue**. Craft is
most of this document because that is the ask: more silhouette capability, polished curves, new
silhouettes, alternatives to petals, Higgsas used creatively (not decoratively).

## 2. Axis A — silhouette & curve craft (master-GN lens)

All node names below are VERIFIED against the shipped library
`RawArt/BlenderLibraries/Higgsas/Blender 5.0 Higgsas Geo Node Groups v13.blend` (279 groups).

### A1. From 7 archetypes to a continuous margin system

The grandmaster plan's archetype table is a set of parameter presets over one construction. Expand it
from a menu into a *language*:

1. **Super-ellipse margins** (`Super Ellipse`). One exponent n drives the whole outline family:
   n≈2 round -> n>2 squarish (cordate shouldered) -> n<2 needle/acuminate. Gives smooth interpolation
   BETWEEN archetypes instead of snapping; archetype presets become named points in that space.
2. **Authored spline margins** (`Loft Splines`, `Even Grid Profile Surface`, `Bezier Resample`).
   The designer draws a margin curve; it is resampled uniform and lofted as the petal's edge profile.
   This kills the "staircase from parameter-only shapes" class of defect for good: any drawn curve is
   legal, and the resample makes the cage uniform before subd.
3. **Ornamental margin fields** (bounded, subtle — jewelry, not foliage):
   fringe -> `Scales Texture` microrelief; serration -> `Triangle Grid` height cuts; scalloped rim ->
   `Circle Packing` arc trim; pierced notches -> `Maze Solver` cuts through the skirt only.
4. **Tip language**: tip power stays; add needle cheat (exponent on the last 5% of u) and a
   droop tip (u^3 pull) for reflexed forms.

### A2. Curve polish pass (run before subdivision, always)

    Mesh Relax -> Bezier Resample (uniform arc length) -> margin curve -> Edge Crease midrib
      -> SubdivisionSurface L2 -> Boundary Edge Smooth (rim only) -> SetShadeSmooth

- `Curve Offset` gives parallel decorative veins following the margin — the vein/rib system.
- `Align Curve to Surface` binds veins/ribbons onto the finished petal (no floating geometry).
- `Curve Deform` + `Twist Curve` give controlled curl (rolled petal edges beyond the current `roll`).
- Law: creases only ever at the midrib; every other boundary is smooth-by-construction.

### A3. Alternatives to petals — element library v2

Each element = one subgraph, same whorl placement contract (type + archetype + count). P1 prototyped
three; the expansion set:

    leaf            finish: toothed margin (A1.3 serration), midrib crease
    plume/feather   ragged vane: scales microrelief + graded fringe; quill via Curve Offset (P1 residual)
    wing/paillette  `Loft Splines` sheet, edge taper, `Twist Curve` roll
    whiplash scroll `Spin` + `Taper` + `Even Curve to Mesh` (v7 cousin exists — polish the riffle)
    ribbon          `Even Curve to Mesh`, flattened profile, `Twist Curve` for the loop memory
    tendril         `Spherical Spiral` or `Curve Deform` spiral; tip `Taper`
    briolette drop  `Rounded Cone` + `Pyramid` facet cuts; hangs as dangle terminal
    scallop fan     `Circle Packing` arcs rotated into a fan; `Solidify`
    cymatic diaphragm `Ripples Solver` rings + `Solidify` — the Tide signature
    NEW ginkgo fan      fan of graded ribbons (the fans read beautifully at icon scale)
    NEW orchid lip      3-lobe loft, centre lobe split — a "face" flower, not a rosette
    NEW bellflower      profile revolve (`Spin` on a margin curve) — bell/campanula silhouette
    NEW snowflake star  `Snow Crystal Growth` — the winter register centrepiece
    NEW snail coil      `Spherical Spiral` + `Taper` — scroll shell for Arcane
    NEW seed-head       `Phyllotaxis Disk` + `4 Points Sphere` bead seeds — a gem-head alternative
    NEW mobius scroll   `Mobius Transformation` — a single-surface scroll for high fans

Rule: elements assemble as WHORLS (same placement math), so every new element is immediately usable in
every genome, and silhouette QC (A4) applies unchanged.

### A4. Silhouette QC (extend the existing gates)

- 64-px icon gate per element + per genome (already in the grandmaster plan).
- NEW: **archetype separation metric** — for each candidate silhouette, distance to the archetype
  target profile; a shape that cannot be told apart from its neighbour at icon scale fails.
- Multi-view contact sheet (front/tq/edge) + the existing clay/eevee/icon triplet.

## 3. Axis B — structure, setting, garlands (deepen the bench)

1. **Openwork backplate library** (`Cairo Tile Grid`, `Hexagon Grid`, `Bricks Grid`, `Triangle Grid`,
   `Triangle Mesh to Voronoi`, `Maze Solver`). Constraint: pierced area <= a fixed budget per genome
   (the backplate must still read as load-bearing at 64 px; light-through by day, glow-through by night).
2. **Filigree / organic veins**: `Edge Bundling` and `Differential Growth` on the backplate border —
   the two nodes that make drawn-looking, non-repeating scrollwork.
3. **Milgrain & borders**: `Inset Face` border -> instanced micro-beads (`4 Points Sphere`) along the
   inset ring; bright-cut alternative via thin `Edge Offset` ridges.
4. **Stone setting v2**: prong variants (4-claw / 6-claw via capsule posts + rounded tips), bezel and
   half-bezel (`Inset Face` + `Taper`), pave rows along `Curve Offset` borders, channel runs for the
   ribbon elements. Cuts stay: `Rounded Cube` (step), `Pyramid` (rose), `Rounded Cone` (briolette),
   `SDF Polygon` (table/emerald), `Super Ellipsoid` (cabochon).
5. **Garlands & dangles v2**: `Dynamic Catenary Splines` for swags strung between hardware points;
   chain links via `Torus` + `Rotate Element`; per-link lag via `Curve Forward Kinematics` (authored
   motion, not physics); terminal drops = briolette or seed pearls.

## 4. Axis C — motion architecture (the measured blocker; do this FIRST)

**STATUS 2026-09-17 night: items 1-2 + bloom DONE and verified in the live session.**
Dangles build as their own object (`FlowerBrooch_Dangles`, parented, outline mirrored; tree
`GN_BroochDangles_<genome>` with its own SceneTime per chain). The body tree is TIME-FREE by
construction (`build(..., bloom=False)` default — the bloom is a build-time option for offline
renders). Outline + Sparkle trees had their SceneTime removed, with `Freeze Frames -> 1` as the
divide guard. Measured live: frame change 0.42-0.48 s (was 8-22 s), body geometry static across
frames, dangle bbox moves (sway alive), sizing law held via the gold-bbox union across body +
dangles (all genomes 0.0% err; hero 60.0 mm). **C3 — petal motion (spike measured 2026-09-17).** Animated petals need the same treatment as the
dangles: petals move to their own object with their whorls kept as UNREALIZED instances, and the
flutter is a per-instance rotation field (SceneTime -> rate -> +index*0.55 phase -> sine -> amp ->
added to each whorl's instance rotation). Measured in-tree (petals inside the body tree, realize
muted, flutter wired): **0.13 s/frame** live — the body tree re-cooks with them. Split to the petal
object (own tree: 2 prototypes + 2 instance whorls + flutter, no realize), the re-cook should land
in the dangle range (0.02-0.08 s) with the body cached at 0.017 s. Tradeoff to verify on the split:
the Bevel_Detail modifier cannot ride on instanced output — petals lose the stack bevel (they are
smooth-by-construction, so the visible cost should be nil on the blades; A/B a macro render).
Constraints honored: same genome, same archetypes, same material ID (MID_Metal_Petal), outline
mirror on the petal object, sizing union extends to body + petals + dangles.

**Item 3 (sparkles/glints as their own object) stays open** — the twinkle is frozen (its SceneTime
removed); restoring it means moving the sparkle field onto its own object with an Object Info feed.

**Smoothness law learned the same night:** ANY animated transform on a heavy object (its own action
OR a parent-empty keyframe) re-cooks that object's whole stack per frame — the hero's turntable
action alone cost 0.30-0.50 s/frame; detached, the same file frame-changes in 0.015-0.017 s.
Turntables therefore animate the CAMERA, never the piece.
Mechanism note (do not relearn this the hard way): a GN stack that contains a SceneTime node
re-cooks the WHOLE stack on every frame change (GUI: seconds); muting OR deleting the node does
NOT clear the depsgraph's time-dependency flag until a structural refresh — a clean rebuild
produces the correct state, in-session edits do not. Keep every time node on the small object.

Verified today: any in-tree time animation = full brooch regen = 7-9 s/frame in the GUI. "Live dangles"
at a usable frame rate requires motion OUT of the regenerating tree. Design:

1. **Static body.** The brooch body regenerates only when a socket/genome changes (cached otherwise:
   0.000 s idle, measured). Subd stays L2 for renders.
2. **Dangles move as their own object.** Extract the chains into a small separate GN object (or
   linked copy) whose tree is ONLY chains + sway; time changes then touch ~10 small meshes, not the
   flower. Parent/bind to the body so the piece moves as one. Same genome trait, same sockets
   (Dangles On / Sway / Rate), same still pose.
3. **Sparkles/glints move as their own object** too (they are instances — cheap, independent of body).
4. **Bloom becomes a state pair, not a continuum, for live use**: bake the dormant and radiant poses;
   presentation crossfades or cuts between them; the continuous growth animation stays an OFFLINE
   render feature (it is beautiful, it is just not interactive). If a hero moment needs the growth,
   render it headless (0.4 s/frame at full quality — 96 frames = ~40 s of render).
5. **Budget (new gate)**: animated-subset frame change <= 0.5 s headless / <= 2 s GUI; static-body
   idle 0.000 s; draw steady-state <= 25 ms (measured today: 18-25 ms).
6. **Music register**: the Convergence hook stays consumer-only (Musical Freq A/B / Amplitude /
   Influence on the existing sockets). No new writer.

## 5. Axis D — systemization (Melodia Studio)

Material-ID + UV/texel-density/UDIM architecture: `BROOCH_MATERIAL_UV_ARCHITECTURE_2026-09-17.md`
(M1 material IDs landed 2026-09-17; U1-U4 the UV pass, next in order).

1. **Panel (grandmaster P4) plus the expansion ops**: genome browser (thumbnails), "save genome from
   current", A/B compare two genomes, presets manager (materials + animation), one-click export pack
   (GLB + intake shots + report), suite builder.
2. **Genome schema v3** = v2 (`silhouette{}`, `elements{}`, `materials{}`, `animation{}`, `story{}`)
   + `margin{mode: archetype|superellipse|spline, params}` (A1) + `qc{icon_gate}` + `suite{family, of}`.
   Absent block = default (v7/v8/v9 genomes keep building — the standing law).
3. **Export/intake**: GLB for the UE wardrobe stays PARKED until the wardrobe hook opens (standing
   non-goal). Icon macro + turntable + report lines are ready to run today.
4. **Docs discipline**: this file + grandmaster ledger + guide pointer; every phase lands as a
   ledger row, numbers first, renders second.

## 6. Axis E — catalogue (the Melodia element registers)

Registers are the world spine (Forte · Radiant · Arcane · Tide · Stone · Gale · Umbral). Each register
gets a design language, not just a material:

    Forte     ember gems, heavy warm bezels, seed-head element
    Radiant   prismatic brilliant cuts, glint-forward, ginkgo fan
    Arcane    hex/pearl, pierced lattice, snail coil + mobius scroll
    Tide      catenary swags, ripples diaphragm, marquise cuts, pearl spray
    Stone     jade/stone cabochons, robust prongs, orchid lip
    Gale      feather/wing/paillette, zephyr ribbons, briolette drops
    Umbral    dark cabochon + negative space, night register, snowflake star

Catalogue v1 target: 2 genomes per register (14) + the shipping hero; each genome = one wardrobe item
id + one 64-px icon; **suites are DATA** (brooch + hairpin/earring from one genome — the geometry is
reused, never duplicated).

## 7. Order (each step gates before the next)

    C1  motion split (dangles + sparkles as own objects; bloom = baked state pair)      <- FIRST
    C2  hero dangles decision -> genome + rebuild (ships with C1)
    A1  margin system (super-ellipse + spline mode) into the builder + silhouette{}
    A3  element library v2 (finish P1 three; add ginkgo, orchid, bell, snowflake, coil, seed-head)
    B   openwork + filigree + setting batch (Higgsas batch B, absorbs grandmaster P5)
    A2/A4  polish pass + QC gates (icon + separation metric)
    D   panel completion + genome browser + presets manager (grandmaster P4 expanded)
    E   catalogue build-out per register; suites as data
Offline (not gating): bloom growth renders; cast-on beauty passes; UE export.

## 8. Laws carried forward (do not relitigate)

- one geometry authority = the builder; the panel and headless scripts call the SAME functions
- sizing <= 5% with cast OFF = exact two-pass solve; cast is opt-in finishing only
- no physics sim: all motion authored; still pose exists in every preset
- creases only at the midrib; no boundary is a straight polyline; no extruded rims
- presets set values on builder-owned materials only (no second material authority)
- ledger row or it did not happen; a dated "missing/broken" doc is history until re-probed
- motion budget (C4) is a gate from now on: live-or-offline, never "maybe it will get faster"

## 9. Open questions (owner)

1. Hero dangles: add a `dangles{}` block to the hero genome (8-10 chains, 12 deg @ 0.7 Hz as already
   on its socket) — yes/no? (C2 blocks on this.)
2. Bloom in live use: state pair (recommended) vs full growth regen when the hero is showcased?
3. Element priority for the first expansion batch (default: finish plume vane + ginkgo fan + orchid lip)?
4. Suites: which piece first from the hero genome — hairpin or earrings?
5. Catalogue: hold 2-per-register for v1, or go deeper on one register first?
