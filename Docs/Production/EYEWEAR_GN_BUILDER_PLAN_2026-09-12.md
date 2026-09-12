# Eyewear GN builder — research findings and build plan — 2026-09-12

**Objective.** A Melodia Studio geometry-nodes builder that generates CAD-level glasses
(frame front + temple arms) and couture accessory mockups from real-world measurements,
producing a web-optimised deliverable.

**Status:** research complete, plan drafted, **not built.** Two empirical findings below
change the shape of the build and are load-bearing.

---

## 1. Provenance of these findings

Four parallel research tracks plus one local empirical spike:

| Track | Evidence class |
|---|---|
| Editorial / luxury eyewear production pipelines | web, cited; practitioner + vendor + one peer-reviewed paper |
| Measurement standards, sizing, fit anatomy | web, cited; ISO/EN/ANSI/FDA texts read via secondaries |
| Web-optimised realtime asset pipeline | **measured locally** on Blender 5.2.1 + gltfpack 1.2 |
| Blender 5.2 GN techniques for frames and arms | manual-verified only — **the subagent did not run Blender** |
| Local spike `Saved/Audit/eyewear/eyewear_spike.py` | **measured**, Blender 5.2.1 LTS, this session |

Track 4 was manual-only, so its core recommendation was re-tested locally. That test is
section 4 and it changed three things.

## 2. Corrections to the brief

Three premises were wrong and are corrected here so they do not propagate into the build:

- **`ANSI Z80.10` is Tonometers, not frames.** The frame standard was `ANSI Z80.5`, which the
  ASC Z80 chart lists as *replaced by* the ISO set (ISO 7998 / 8624 / 12870). US frame
  compliance now runs through ISO. Do not cite Z80.10 for frames.
- **The `Set Position → Offset` removal could not be corroborated.** The 5.2 manual documents
  Offset on that node. Treat "Set Position has no Offset" as unconfirmed; verify at build time
  rather than coding around it.
- **There is no `GeometryNodeCylinder`.** The mesh primitive is `GeometryNodeMeshCylinder`.
  A plan that says "use the Cylinder node" will fail on `nodes.new()`.

Additionally, `ResampleCurve.Mode` and `FilletCurve.Mode` are **menu input sockets**, not node
properties — `node.mode = "LENGTH"` raises `AttributeError`. Confirmed local socket dumps:

```
GeometryNodeResampleCurve : Curve, Selection, Mode(MENU, default 'Count'), Count, Length
GeometryNodeFilletCurve   : Curve, Radius, Limit Radius, Mode(MENU, default 'Bézier'), Count
GeometryNodeCurveToMesh   : Curve, Profile Curve, Scale, Fill Caps
GeometryNodeObjectInfo    : Object, As Instance      (transform_space is a PROPERTY)
```

Accepted menu strings on this build: `ResampleCurve.Mode = 'Length'`, `FilletCurve.Mode = 'Poly'`.

## 3. The measurement contract

### 3.1 Boxing system — the parameter surface

| Symbol | Meaning | Standard range | Stamped on frame |
|---|---|---|---|
| A | horizontal boxed lens size (eye size) | 40–60 mm; everyday 50–54 | yes |
| B | vertical boxed lens size | 32–38 mm | no |
| ED | effective diameter (smallest enclosing circle) | ≥ A | no |
| DBL | distance between lenses (bridge) | 14–24 mm; everyday 16–19 | yes |
| — | temple / side length | 120–150 mm; 140 most common | yes |
| — | frame width (endpiece to endpiece) | 125–150 mm | no |
| — | frame PD = A + DBL, exactly | — | no |

Label format is `54□18-145`. Also needed for a complete fit: **LTB** (length to bend, hinge
barrel centre to middle of bend) and **LoD** (length of drop); printed side length = LTB + LoD.
Minimum blank size = ED + 2·decentration + 2 mm.

### 3.2 Tolerances (ISO 12870, non-rimless)

Horizontal boxed lens size ±0.5 mm · DBL ±0.5 mm · overall side length ±2.0 mm.

### 3.3 Fit parameters — industry convention, **not** standards-body numbers

| Parameter | Working range | Default |
|---|---|---|
| Pupillary distance | adult mean 61.2 mm, SD 7.0 (n=14,904); range 54–74 | — |
| Vertex distance | 8–20 mm fitted; average 13–14 | 12.3 (HOYA compensated) |
| Pantoscopic tilt | 8–12° typical; fitted 0–15 | ~10° (HOYA 8.3°) |
| Wrap / face-form | 0–10° standard; 12–25° sunglasses | 4.4° (HOYA) |
| Temple bend point | begins at the top of the ear; dropped end sits ½–⅔ down the ear; bend ≈45° | — |

Correcting rule to encode: optical centres drop 1 mm per 2° of pantoscopic tilt.

**There is no ISO/ANSI number for tilt, wrap, vertex distance, or nose-pad geometry.** The
builder must not label these "the standard". ISO 12870 also explicitly **excludes
custom-made frames**, so couture is ungoverned by published specs — everything couture in the
research came from retailer/editorial sources, not engineering documents.

### 3.4 Structural tests worth knowing (they bound what "CAD-level" must survive)

- Stability at temperature: 55 ± 5 °C for 2 h; side tips move no more than +6 / −12 mm.
- Bridge deformation: 5 N applied, deformation < 2 %, no fracture.
- Endurance: 500 cycles at 40 cycles/min; permanent deformation ≤ 5 mm.
- Ignition: 650 ± 20 °C rod, 5 s, no continued combustion.
- FDA 21 CFR 801.410 drop ball: 5/8 in (15.875 mm) steel ball, ~15.9 g, from 50 in (1270 mm).

## 4. Construction decision — and the local spike that settles it

### 4.1 Chosen approach: cyclic profile swept along a cyclic silhouette

`Curve to Mesh` with **both** the silhouette and the profile spline cyclic. Measured locally:

```
len=3.0   verts=472    tris=944    faces=472   quads=472   ngons=0  trif=0  nonmanifold=0  uv=NONE
len=1.0   verts=1416   tris=2832   faces=1416  quads=1416  ngons=0  trif=0  nonmanifold=0  uv=NONE
len=0.5   verts=2824   tris=5648   faces=2824  quads=2824  ngons=0  trif=0  nonmanifold=0  uv=NONE
```

**All-quad. Zero n-gons. Zero triangles. Zero non-manifold edges. Fully closed.** The lens
aperture is free — it is the hole in the middle, no boolean and no cut. This confirms the
recommendation and refutes the boolean route empirically, not just by manual reading.

Evaluation density is the dominant cost lever: `Length 0.5 → 3.0` is a 6× swing.

### 4.2 Rejected

- **Boolean inset for the aperture.** Produces n-gon/triangle mix at the intersection curve, no
  controlled quad flow, no clean loop for a bevel to follow; coplanar-face failures unless the
  Exact solver is used; the Manifold solver fails outright on non-manifold input.
- **Grid-based frame body.** Grid output is planar; conforming it to a closed rim either breaks
  even thickness or introduces a distortion singularity. **Keep Grid for the lens blank only.**

### 4.3 The corner-collapse fix (do this before the sweep, not after)

A swept profile self-intersects on the inside of a corner when the inner profile half-width
exceeds the local corner radius, and 5.2's Curve to Mesh has **no even-thickness or miter
option**. The only robust fix is to guarantee no corner is tighter than the rim inner
half-width: `Fillet Curve` (Limit Radius **on**) then `Resample Curve` (Length mode) before the
sweep. Both are confirmed working on this build.

### 4.4 Consequences to design around

- **No Mirror node** exists in the 5.2 mesh-operation set. Mirroring = `Transform` with negative
  X scale **plus `Flip Faces`**. Pre-5.2 tutorials that reach for a Mirror node are wrong.
- **No Solidify node.** Thickness = `Extrude Mesh` + `Move`/`Scale`.
- **A flat single-surface silhouette cannot be beveled at all.** Its border edges touch one
  face, so `Mesh Bevel` (manifold edges only) silently skips them. This is why the sweep route
  is not just nicer but necessary.
- **Rim thickness comes from construction**, never from a node flag: a constant cyclic profile
  expressed in millimetres, times the Curve to Mesh `Scale` input. Local thickening (end-piece,
  top bar) is driven off Spline Parameter, not off tangent change.
- **End-piece**: no separate joined block — thicken a bounded run of the same sweep, or the two
  boundary loops are unfused (`Join Geometry` does not weld) and the mesh stops being manifold.
- **Hinge**: `GeometryNodeMeshCylinder` for the barrel, with its Top/Side/Bottom selection
  outputs for per-face material. Articulation is Transform maths — hinge axis and pivot as
  Vector group inputs, one scalar fold angle. There is no hinge primitive.
- **`ObjectInfo.transform_space` defaults to `ORIGINAL`.** Already cost this project a placement
  defect once; must be `RELATIVE` when the host object is offset.

## 5. The two load-bearing empirical findings

### 5.1 Export: `export_apply=False` silently ships an empty file

Measured GLB export of the swept frame with `export_gn_mesh=True`:

```
export_apply=False   176 bytes    meshes=0   primitives=0
export_apply=True    17764 bytes  meshes=1   primitives=1   attrs=[NORMAL, POSITION]
```

The `apply=False` export **reported success and contained nothing**. The exporter logged
`Primitives created: 0` / `Mesh has no primitives and will be omitted` — but the operator
returned cleanly. This is the single most dangerous trap in the pipeline: a builder can be
perfect and the delivered asset empty, with no exception raised anywhere.

The four flags default wrong for this pipeline and must be set explicitly every export:
`export_apply`, `export_gn_mesh`, `export_attributes`, `export_gpu_instances`.

### 5.2 GN output carries no UVs — the GLB ships POSITION and NORMAL only

Every measurement came back `uv=NONE`, and the exported GLB attributes are exactly
`['NORMAL', 'POSITION']` — **no `TEXCOORD_0`**. Geometry nodes do not author UVs; a graph that
does not create them produces an asset that cannot be textured on the web. The builder must
author UVs in-graph, and the export gate must assert `TEXCOORD_0` present.

## 6. Web budgets

| Source | Budget |
|---|---|
| Khronos glTF Asset Auditor defaults | 100,000 tris · 5,120 KB · 5 materials · 2048 px textures |
| Khronos 3D Commerce, single-item mobile AR / web catalogue | 3 MB · 150,000 tris · <20 draw calls · 2K textures |
| Khronos 3D Commerce, desktop 3D web view | 3 MB · 250,000 tris · <100 draw calls |
| Amazon eyewear spec (the only machine-checkable eyewear asset spec found) | **≤200,000 tris**; textures 2K–4K, square, power-of-two; node names **Frame, TempleR, TempleL, LensR, LensL**; no modifiers, no animation, no cameras, no lights |
| Measured uncompressed GLB cost | ~24 bytes/triangle; ~0.6 vertices per triangle |

Measured compression on a 183,380 B / 7,696-tri mesh:

```
Blender Draco (lvl 6, pos14/nrm10/uv12)  13,696 B  ->  12,035 B gzipped
gltfpack -c  (EXT_meshopt_compression)  37,312 B  ->  12,405 B gzipped
gltfpack -cc (max)                      31,832 B
plain gzip of uncompressed GLB          85,099 B
```

**Draco and meshopt land within 3 % of each other once gzipped** — meshopt is engineered to
gzip well. So meshopt is the better default: same delivered bytes, far faster decode, no
100 KB Draco decoder. Route through `gltfpack` or glTF-Transform, **not** Blender's built-in
meshopt flag (Blender's own meshopt output measured 79,584 B — 43 %, weak).

LOD ladder measured two independent ways and consistent: 7,696 → 3,848 (0.5) → 1,924 (0.25) →
768 (0.1) tris.

Geometry is never the bottleneck — 4k–20k tris is 10–40 KB compressed. **Textures dominate.**
Amazon forces ≥2K maps, which is 0.4–2 MB across four maps; KTX2 is what fits the 3 MB target.

Known loader seam: `drei`'s `useGLTF()` has **no KTX2 support** (open issue pmndrs/drei#2639);
naive per-asset wiring duplicates the decoder WASM. If the viewer is r3f, either use an
app-level singleton KTX2 loader created after the renderer exists, or ship WebP/JPEG first.

## 7. Where this actually stands

Sections 7-10 originally described intent. This is the measured state.

**Built, in the addon, verified by `Tools/eyewear_verify/`:**

| builder | state |
|---|---|
| `MEL_eyewear_front` | done. Cyclic silhouette swept by a cyclic profile. Boxing arithmetic verified 3/3. |
| `MEL_eyewear_temple` | done. Arm, ear drop, fold rotation, endpiece clearance. |
| `MEL_eyewear_hinge` | done. Barrel stack on the derived endpiece axis. |
| `MEL_eyewear_pair` | done. Auto-assembles front + 2 temples + 2 hinges. 15/15 measurement checks. |
| `MEL_eyewear_lens` | done. Flat plano, centred, `2A + DBL` across both eyes. |

Registry: **566 builders, 0 build errors.** All gates green (A-F), census PASS.
Eyewear parameters are in **millimetres**, converted once at the graph input.

## 8. The close-out plan

### 8.0 Fix first — it blocks 8.4. Beads come out ~25% overscale

**`Bead Radius` works, but the bead is consistently about a quarter larger than the
parameter says.** Measured with Taper and Jitter forced to 0, a FRESH tree per value,
and the set asserted so a silent failure cannot masquerade as a result
(`Tools/eyewear_verify/bead_size_check.py`):

    Bead Radius   expected_mm   measured_mm   ratio
    0.010              10.00         11.56     1.16
    0.022              22.00         27.99     1.27
    0.044              44.00         55.20     1.25

Monotonic and roughly proportional, so the dial is alive — but every value lands
16-27% high. That is a scaling constant somewhere between the parameter and the
bead, not a dead input.

### Two earlier conclusions on this item were wrong, and both were test faults

This item has now been reported three times. Recording why, because the pattern is
the lesson:

1. **First claim: "beads are an order of magnitude larger than the parameter."**
   Wrong. It rested on one spread measurement that sat near
   `22 mm x Taper x Jitter`, which is what correct behaviour looks like.
2. **Second claim: "`Bead Radius` is a dead dial."** Also wrong. That test reused a
   single bead-string tree across four runs and mutated its interface defaults in
   place, so a failed set silently kept the previous value. `0.022` and `0.044`
   appearing identical was the tell, and it was the harness, not the builder.

The fix for both was the same and should have been the first move: isolate one
variable, use a fresh tree per case, and assert that the input actually took. The
same discipline that caught the guide-switch and the `new_geometry_tree` template
invalidation.

### Where the 25% lives

Presumed between the template's `Radius` and the instance scale, both of which
currently claim to be authoritative. `_set_group_param(bead_grp, "Radius", 1.0)` is
intended to normalise `MEL_nikki_bead` to unit radius so that the instance `Scale`
is the single source of truth; a ~1.25 factor surviving that normalisation means one
of the two is not doing what its comment says. Needs a read of `build_nikki_bead`
rather than more measurement from outside.

### Why it matters beyond the chain

This is the bead/cord authority behind the eave swag and the wall drop in the study
scene. Every garland built with it inherits the 25% - visible on a chunky Nikki
bead, and it will show on any accessory chain sized against a frame.

### Acceptance

With Taper and Jitter at 0, measured bead radius equals `Bead Radius` within 2%, at
three values spanning the range. The existing harness already reports exactly that
and currently fails, so it is the test to make green - not a new one.

### Decisive measurement — the template's Radius is not linear

Reading `build_nikki_bead` and measuring it directly settles this:

    Radius=1.0    ->  Xhalf=1000.00 mm   factor 1.000
    Radius=0.044  ->  Xhalf=  57.23 mm   expected 44.00
    Radius=0.022  ->  Xhalf=  36.31 mm   expected 22.00

So `_set_group_param(bead_grp, "Radius", 1.0)` **works** — at 1.0 the template is
exactly 1000 mm, which is 1 Blender unit, so the unit normalisation the bead string's
comment describes is genuine and the instance `Scale` really is meant to be the
single source of truth. The instance path is not the fault.

The fault is upstream of it: `MEL_nikki_bead`'s `GeometryNodeMeshUVSphere` radius
does not track its own `Radius` parameter. Driving that parameter to 0.022 yields
36.31 mm, not 22.00. The relationship is neither linear nor a clean power, and the
error is not constant either, so it is not a simple offset that a single constant
can absorb.

Note also that the sphere measures differently on X and Y (36.31 vs 42.00 at
Radius=0.022, converging to 1000 vs 1020 at 1.0), so the template is not radially
symmetric at small parameters either. That is a second symptom of the same thing and
worth explaining rather than patching.

Because the template is only correct at Exactly 1.0, every consumer that drives
`Radius` to anything other than 1.0 inherits an unpredictable size — which is why the
bead string, the star pendant and the heart filigree can all be wrong at once.

Next step is inside `build_nikki_bead`: find why the sphere's radius input does not
follow the parameter, and whether the `Squash`/`Teardrop` branch or the param's own
min/max range is implicated. Do not fix this by scaling the result at the call site —
that would bury a template defect under per-consumer constants.

### 8.1 Silhouettes — the literal 5.2 nodes

`build_eyewear_front` currently makes one shape: a `CurvePrimitiveQuadrilateral`
(`eyewear.py:90`) filleted at `:141` — a rounded rectangle, no matter what. This build has
the dedicated nodes:

    CurveArc                      round / panto
    CurvePrimitiveBezierSegment   cat-eye, aviator teardrop (real cubic control)
    CurvePrimitiveQuadrilateral   square, browline, rectangular
    MenuSwitch / IndexSwitch      literal selector across the profile branches

Work: branch the aperture silhouette, select it with `MenuSwitch` (label) or `IndexSwitch`
(index), and keep the existing cyclic sweep downstream untouched so the rim, aperture and
`2A + DBL` contract are unchanged. Every branch must satisfy the same measurement checks,
which means the harness grows a case per silhouette — that is the acceptance test, not a
render.

Note the boxing caveat: A and B describe the **lens aperture box**. A cat-eye or aviator
does not fill its boxing rectangle, so each silhouette needs its own expected-width
assertion rather than reusing 134.000.

### 8.2 `MEL_eyewear_edge_break`

Section 5 work that was never done. The earlier plan called for a reusable manifold-safe
bevel "like `MEL_garment_smart_bevel`". It cannot use `GeometryNodeMeshBevel`: measured
twice now, it is unusable in 5.2 (a 0.3 mm offset took a 54 mm lens to 322 mm, both
unrestricted and restricted to the extrude `Side` selection; the same defect removed it from
the decor star and heart builders). The edge break has to be **constructed into the
profile** — a chamfered or rounded rim cross-section — not applied as a post-pass.

### 8.3 `MEL_eyewear_lens` base curve

The lens is currently flat. Real lenses are not. Add a base-curve sag driven by radial
distance (`Set Position` with a spherical offset, or a `CurveArc`-derived profile) and expose
the sag in mm. Keep the flat case exact so the existing 15 checks still pin the aperture.

### 8.4 `MEL_eyewear_chain` and the accessory family

The chain is **unblocked** — the earlier "bead path is broken" conclusion was withdrawn after
measurement, and the in-graph `Guide Curve` path works for cord and beads alike. What it
needs:

    MEL_eyewear_chain     bead strand between the temple tips. Anchors are already derived
                          and measured correct: x +/-64.75, y -30.00, z -119.00. Hang the sag
                          on the guide curve in -Y and set the nested Droop to 0 — the nested
                          builder sags along Z, which is the depth axis in this family.
    MEL_finding_ring      jump ring / bail
    MEL_finding_clasp     eyeglass clasp
    MEL_finding_loop      the endpiece loop the chain terminates in

The findings are what let any decor attach to a frame at all, so they are worth more than the
chain alone: they compose with the whole `MEL_nikki_*` family.

One unresolved measurement must be re-taken with the 8.0 fix in place: in the backed-out
chain attempt the assembled strand sat ~16 mm above its own guide while the guide line itself
measured correctly. 8.0 is the prime suspect. Re-measure rather than assume.

### 8.5 Web-export hygiene — `MEL_eyewear_uv`, `MEL_eyewear_export_gate`

Both exist because of section 5. Measured: GN output carries **no UV layer** (the exported
GLB had `POSITION` and `NORMAL` only), and `export_apply=False` **reports success while
shipping an empty 176-byte file**. These two are the only thing standing between the pipeline
and a silently empty, untexturable asset:

    MEL_eyewear_uv           asserts/creates TEXCOORD_0
    MEL_eyewear_export_gate  realizes, exports, asserts the file is non-empty AND UV'd

### 8.6 Audio reactivity — clarification, then a decision

Universal Music Influence now defaults ON across the addon, but it is **not audio reactive**.
It is a procedural radial harmonic — `sin(Z*FreqA) + sin(atan2(Y,X)*FreqB)` — with no audio
input anywhere in the graph. This build exposes no audio-input geometry node.

So "audio reactivity" is a separate question. If it is wanted, it goes through the existing
MIDI bridge; it must not become a second music authority. Spike it, then decide.

## 9. Definition of done

A builder is closed out when all of these hold, and not before:

1. It is registered and appears in the census at the expected id.
2. `Tools/eyewear_verify/` asserts its **arithmetic**, not its looks — mm dimensions from the
   parameters, symmetry, manifold, aperture. Every new silhouette gets its own expected width.
3. Gates A-F green, eyewear suite PASS, census PASS, three copies byte-converged.
4. Any new `BoundBox` measures **realized** geometry. Gate F catches this and it has already
   bitten twice.
5. It composes rather than duplicates: beads, cord, stars and hearts stay in `nikki_decor.py`.

## 10. Order, and why

    8.0  bead size          blocks the chain and is already live in decor
    8.1  silhouettes        independent, highest visual value, uses the literal nodes
    8.2  edge break         front geometry, do with 8.1 while in the profile
    8.3  lens base curve    small, after 8.1
    8.4  chain + findings   after 8.0
    8.5  uv + export gate   last — they gate delivery, they do not shape the asset
    8.6  audio              spike only; needs a decision, not code

Nothing is half-built in the tree: `MEL_eyewear_chain` has zero occurrences in `eyewear.py`,
so 8.4 starts clean.

---

# Appendix — render workflow

## Use `MEL_eyewear_pair`

One builder emits the whole thing: front, two temples, two knuckles, already
positioned. The separate `MEL_eyewear_front` / `_temple` / `_hinge` builders remain
for parts work, but for a beauty render start with the pair.

Every parameter is in **millimetres**. Defaults are a 54▯18 frame:

    Lens Width A 54   Lens Height B 34   Bridge DBL 18   Rim Thickness 4   Rim Depth 6
    Length to Bend 100   Tip Drop 28   Temple Width 4.5   Temple Thickness 3
    Fold Angle 0   Barrel Radius 1.4   Barrel Length 2.4

Verified assembly (Saved/Audit/eyewear/final_verify.json, 10/10):

    width    134.00 mm   exactly 2A + DBL + 2*RimThickness
    symmetry   0.00 mm   x spans [-67.0, 67.0]
    depth    126.18 mm   frame plane back to temple tip
    height    49.93 mm   frame top to ear-drop bottom
    1912 verts / 3788 tris

## Three things that will bite you on the first render

**1. Orientation.** The family uses `Y` as vertical, not Blender's `Z`:

    X  across the face        Y  vertical (ear drop is -Y)        Z  viewing axis (-Z is behind)

The pair therefore loads **lying on its side**. Rotate the object **-90° about X**
and it stands up. This is deliberate — it keeps the lens plane in `XY` so the
boxing-system A/B map directly onto X/Y — but it is the first thing to fix.

**2. Scale.** The builder is millimetre-accurate, so 1 unit = 1 m and a 54▯18 pair
is **0.134 BU wide (13.4 cm)**. Dropped into a scene built in metres it will look
microscopic. That is correct, not broken.

**3. No UVs.** Geometry-nodes output carries no UV layer (measured: the exported
GLB has `POSITION` and `NORMAL` only), so use solid / Principled materials rather
than image textures, or add a UV pass first.

The lens now exists — `MEL_eyewear_lens` fills the aperture. Add it as a second
modifier alongside `MEL_eyewear_pair`; it is a separate builder because the lens
wants a different material (transmission/IOR) from the frame. It is a flat plano
solid, 2 mm thick, centred on `Z = 0`, spanning `2A + DBL` across both eyes. No
base curve yet, so it reads flat rather than slightly domed.

## Materials

The pair emits a single joined mesh with no material slots assigned. For a first
pass, one acetate-ish Principled shader on the whole object reads fine: roughness
0.4–0.7, and for tortoiseshell layer a semi-transparent speckle over the base
colour rather than a flat tint. Metal frames are better served by the separate
builders, so you can put a metal shader on the hinges and temples and acetate on
the front.

---

# Status: the chain is UNBLOCKED - my earlier "defect" was a test bug

**Superseded.** An earlier version of this section claimed the in-graph
`Guide Curve` path steered the cord but not the beads, and that
`MEL_eyewear_chain` therefore could not be built. That claim was wrong and is
withdrawn. The bead path was never broken.

## What is actually true (measured)

Reading `build_nikki_bead_string` shows the beads come from
`_resample(_drooped_curve(guide_geom))` - the same `guide_geom` the cord uses,
straight through the `Guide From Curve` switch. There is no separate read of the
guide object.

Testing both routes with **identical** guide geometry and direct group-node
socket lookup (`Saved/Audit/eyewear/bead_path_definitive.py`):

    object route   use_curve=False  3124 verts   ~14 beads
    curve route    use_curve=True   3124 verts   ~14 beads
    RESULT PASS

Both routes work. `_guide_params` / `_guide_geometry` need no further change.

## Why the earlier tests lied

Two harness faults, both mine, neither in the addon:

1. **Name-mapping group-node sockets through the sub-tree interface.** Group node
   inputs support direct lookup (`grp.inputs["Guide Curve"]`), so the indirection
   was unnecessary and could resolve the wrong socket silently. The definitive
   test uses direct lookup and prints every socket it touches.
2. **Destroying the template before using it.** One test measured the bare
   `MEL_nikki_bead` template *before* evaluating a bead string built earlier in the
   same process. `new_geometry_tree` removes and re-creates a tree by name, so that
   call nulled the template tree the bead string's group node pointed at - cord
   still rendered, beads vanished. Exactly the defect recorded in the
   `melodia-studio-gn-builders` skill, and I walked into it while writing the test
   for it.

Lesson: when a builder's own code contradicts a test result, the test is the
suspect. Read the wiring first.

## Still outstanding on the chain

One unexplained measurement from the backed-out attempt: the assembled strand sat
about 16 mm above its own guide. The guide line itself measured correctly
(`x +/-64.75, y -30.00, z -119.00`), so this is in the composition, not the
anchors. Chase it with the definitive-test method above - direct socket lookup,
one variable at a time - rather than by name mapping.

## Two traps found on the way (both cost real time)

1. **A two-point poly line cannot carry a sag.** `SplineParameter.Factor` is 0 and
   1 at the ends only, so `1 - (2t - 1)^2` evaluates to zero everywhere and the
   strand comes out perfectly straight - measured as a single distinct Y at
   exactly -30 with the whole 28 mm droop discarded. Subdivide (Resample Curve,
   COUNT) before offsetting.

2. **`MEL_nikki_bead_string` sags along Z, not Y.** `_drooped_curve` offsets Z,
   which in the eyewear family is the depth axis; using it there would push the
   strand backwards behind the head instead of hanging it. Apply the hang to the
   guide curve along -Y and force the nested `Droop` to 0.

## Also unresolved, lower priority

When the chain was assembled the whole strand sat about 16 mm above its own
guide. Not chased down, because the bead path had to be fixed first - recheck it
afterwards rather than assuming it is separate.

---

# Materials and lenses — research, 2026-09-12

Extends section 5.2 (no UVs) and the Appendix "Materials" note. Everything below assumes
that finding holds: **the GN output ships POSITION and NORMAL only**, so image-texture
options in the photoreal playbook are closed until `MEL_eyewear_uv` exists.

## M1. Four materials, four draw calls

| id | parts | glTF primitive |
|---|---|---|
| `MEL_mat_eyewear_acetate` | front, temple tips, moulded ends | 1 |
| `MEL_mat_eyewear_metal` | hinges, metal temples, nose-pad arms | 1 |
| `MEL_mat_eyewear_lens` | lens solid | 1 |
| `MEL_mat_eyewear_silicone` | nose pads | 1 |

Each material slot is one glTF primitive, i.e. one draw call. Four is far inside the
Khronos 3D Commerce single-item web budget (<20 draw calls). Follow `materials_kit.py`'s
`_set_principled(bsdf, **kwargs)` pattern — it sets Principled sockets by name and skips
unknown keys, which is what keeps socket renames from breaking the build.

`MEL_eyewear_pair` currently emits one joined mesh with **no material slots**. It needs a
`GeometryNodeSetMaterial` per part. `MEL_eyewear_hinge` already derives
`GeometryNodeMeshCylinder` Top/Side/Bottom selections, so the barrel's side is a ready-made
material selection.

## M2. Vertex colour is the only texturing channel this pipeline can ship

No UVs ⇒ no textures. But glTF carries `COLOR_0`, and viewers multiply it into base colour.
That is enough for tortoiseshell marbling and for a lens gradient tint.

    GeometryNodeStoreNamedAttribute   data_type FLOAT_COLOR, domain CORNER, name "Col"

Blender 4.x+ exports colour attributes as `COLOR_0` without a dedicated flag. Two traps:

1. The exporter runs vertex colours through sRGB→linear conversion (`color_srgb_to_scene_linear`).
   Author in sRGB and check the GLB, or the result double-darkens.
2. **Vertex alpha does not become opacity in three.js** — `vertexColors` consumes RGB only.
   Put the gradient in RGB, not in alpha.

Acetate palette, sRGB hex → **linear** (computed, standard sRGB transfer):

    dark tortoise base   #2B2118  ->  0.024, 0.015, 0.009
    medium tortoise      #5A3A22  ->  0.102, 0.042, 0.016
    amber honey          #8A5A32  ->  0.254, 0.102, 0.032
    blonde tortoise      #C8A882  ->  0.578, 0.392, 0.223
    black acetate        #141414  ->  0.007, 0.007, 0.007

Resolution limit: at the measured `Length 0.5` setting the front is 5,648 tris across
~134 mm, roughly one vertex per 2.4 mm. Marbling detail finer than ~5 mm will alias —
keep the noise scale coarse, or densify the sweep for the colour pass only.

## M3. Acetate

Base colour = one of the palette entries. Physically it is a plain dielectric with a
buffing lacquer on top, so the coat *is* the material.

    Metallic             0.0
    Roughness            0.35-0.55   (bulk)
    IOR                  1.48-1.49   (cellulose acetate, measured; CAMEO / refractiveindex.info)
    Specular IOR Level   0.5         (default; F0 for n=1.49 is 0.0387, vs 0.04 at n=1.5)
    Coat Weight          0.6-1.0     -> KHR_materials_clearcoat
    Coat Roughness       0.08-0.15

`KHR_materials_clearcoat` exports from Blender 5.2 and is parsed by three.js, Babylon,
model-viewer and UE's Interchange glTF importer. Safe.

Crystal/transparent acetate is **not** a transmission material — it is a very dark-tinted
dielectric. Alpha-blend it (alpha 0.25-0.45), keep the coat, and do not reach for
`KHR_materials_transmission`.

## M4. Metal / titanium

    Metallic             1.0
    Roughness            polished 0.20-0.30 · satin 0.45-0.60 · matte 0.65-0.80
    Base Color           Ti (0.542, 0.497, 0.449)  [UE physically-based list]
                         Ti (0.441, 0.400, 0.361)  [physicallybased.info]
                         Cr (0.549, 0.556, 0.554) · Ag (0.972, 0.960, 0.915) · Au (1.000, 0.766, 0.336)

Roughness bands are industry convention, **not measured**. The two titanium base colours
are both legitimate measurements/derivations and differ because UE's chart is tuned for UE
tonemapping — pick one and stay with it per-lens.

Anodised titanium: keep the same base colour, add Coat Weight 0.3-0.5. Do not tint the metal.

Anisotropy (`KHR_materials_anisotropy`) exports from 5.2 and three.js parses it, **but
Blender requires the Anisotropic tangent socket linked to a Tangent node with a UVMap** —
so it is a non-starter until `MEL_eyewear_uv`. Flag, not a task.

## M5. The lens — cheap approximation by default

Do **not** ship `KHR_materials_transmission` as the default path. Reasons, in order:

- three.js `MeshPhysicalMaterial.transmission` costs an extra full scene render into a
  transmission render target per frame; drei's `MeshTransmissionMaterial` is a second
  full-screen pass per material. Two lenses = two more scene renders.
- Transmissive materials cannot see each other, and the Blender manual itself warns support
  "is not yet widespread".
- model-viewer has an open defect where transmission loses colour (`google/model-viewer#4047`).
- On a 2 mm slab inside a 134 mm assembly the refraction is visually negligible.

Instead:

    Base Color      tint (or one of the acetate palette entries for sun tints)
    Metallic        0.0
    Roughness       0.02-0.06
    IOR             1.50 default · 1.53 CR-39 · 1.67 / 1.74 high-index
    Coat Weight     1.0
    Coat Roughness  0.02
    alphaMode       BLEND when alpha < 1 (clear lenses alpha 0.15-0.35, sun 1.0)

Three cues carry the whole read:

1. **Environment reflection** at roughness <=0.06 — this is 90 % of "glass". Requires the
   viewer to supply an env map: model-viewer does by default, r3f needs `<Environment>`.
   With no env map a roughness-0.04 dielectric reads as flat dark.
2. **Fresnel edge** — free from a dielectric BSDF. Strengthen it, if wanted, by writing a
   rim-darkened RGB into `COLOR_0`.
3. **Gradient tint** — dark at the top of the lens fading down, the single most
   recognisable sunglasses tell. Author it in `COLOR_0` from the lens mesh's vertical
   coordinate (`Position` → Separate XYZ → Map Range → ColorRamp → StoreNamedAttribute).
   This is the one place vertex resolution is comfortably enough: 34 mm of lens height at
   ~2.4 mm spacing is smooth.

## M6. Mirror / flash coating

A mirror is a metal, not a dielectric: Metallic 1.0, Roughness 0.05-0.12, base colour from
the metal list. Gradient mirror (mirror on top, tinting through below) cannot be driven from
`COLOR_0` — **metallic is not a per-vertex channel in glTF**. The export-safe route is a
second lens solid split at the gradient line with its own mirror material: +1 primitive,
+1 draw call.

## M7. Nose pads and temple tips

Silicone nose pad (PDMS, n 1.40-1.43 measured; F0 ≈ 0.029-0.031):

    Base Color      0.75-0.85 linear near-white
    Roughness       0.45-0.65   (the matte is what reads as rubber)
    IOR             1.42
    Metallic 0.0 · Coat 0.0

`KHR_materials_subsurface` is an Initial Draft only and no common viewer supports it — do
not use it to fake translucency; raise the base colour slightly instead.

Moulded acetate temple tips reuse the acetate material at roughness ~0.5; give them a
distinct colour through `COLOR_0` so they cost no extra material.

## M8. Anti-reflective coating

Physically AR takes per-surface reflectance from 4.0 % (n=1.50) / 5.3 % (1.60) / 7.3 %
(1.74) to under 1 % with a hue-dependent residual sheen. Real-time, approximate it as
Specular IOR Level 0.15-0.25 plus a faint Specular Tint (0.70, 0.90, 0.75) green or
(0.85, 0.80, 1.00) violet. Both ride `KHR_materials_specular`, which exports.

`KHR_materials_iridescence` would be the correct layer; Blender 5.2 documents an
iridescence export path but does **not** list the extension in its supported-export set —
**unverified, do not depend on it.**

For a stylized look AR is often *subtracted*: the sheen is a photoreal cue and can read muddy.

## M9. What will not survive export, or breaks in viewers

| Item | Status |
|---|---|
| Procedural nodes (Noise/ColorRamp) driving Base Colour or Roughness | **Not exported.** glTF has no procedural textures. Bake to `COLOR_0` or an image texture. |
| Any texture map (ORM, metalness, gradient alpha, thickness) | Blocked — no `TEXCOORD_0`. |
| `KHR_materials_anisotropy` | Exports, but Blender needs a Tangent node + UVMap. Blocked. |
| `KHR_materials_iridescence` | Not in Blender 5.2's export list. Unverified. |
| `KHR_materials_sheen` | Exportable, but Blender's sheen model is not glTF-compatible. Prefer Coat. |
| `KHR_materials_subsurface` / `diffuse_transmission` | Draft / RC. No viewer support. |
| Metallic from `COLOR_0` | Not a thing. Gradient mirror needs two primitives. |
| Vertex alpha as opacity | three.js ignores it. Gradient goes in RGB. |
| `export_apply=False` | Still the empty-176-byte trap from 5.1. |

Blender 5.2 export-supported set, confirmed from the manual: `clearcoat`, `transmission`,
`volume`, `sheen`, `specular`, `anisotropy`, `dispersion`, `ior`, `emissive_strength`,
`unlit`, `variants`, `texture_transform`, `draco`, `lights_punctual`,
`EXT_mesh_gpu_instancing`.

## M10. Implementation order

    M-1  MEL_eyewear_materials.py   four build_*_material() fns, materials_kit conventions
    M-2  material slots on the pair + hinge side selection
    M-3  lens material + lens sharp tint
    M-4  MEL_eyewear_tortoise / MEL_eyewear_lens_gradient  (COLOR_0 writers)
    M-5  extend MEL_eyewear_export_gate: COLOR_0 present, extensionsUsed matches intent,
         no material with transmission>0 unless explicitly enabled
    M-6  UE 5.8 import check (Interchange handles clearcoat / ior / specular / sheen)
    M-7  viewer wiring: env map mandatory, transmission off, lens alphaMode BLEND last

## M11. Sources

- Blender 5.2 glTF manual (export extension list, clearcoat/specular/transmission/anisotropy/
  volume/IOR rules): https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html
- Khronos glTF extension registry (ratified vs in-progress):
  https://github.com/KhronosGroup/glTF/blob/main/extensions/README.md
- `KHR_materials_volume` (manifold/closed mesh requirement):
  https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_materials_volume/README.md
- Khronos PBR glossary: https://www.khronos.org/gltf/pbr/
- Blender glTF I/O PBR-extension support notes (sheen/specular model incompatibility):
  https://www.khronos.org/blog/blender-gltf-i-o-support-for-gltf-pbr-material-extensions
- three.js GLTFLoader / MeshPhysicalMaterial transmission cost; drei `MeshTransmissionMaterial`
  extra render pass: https://drei.docs.pmnd.rs/shaders/mesh-transmission-material
- model-viewer transmission colour-loss defect: https://github.com/google/model-viewer/issues/4047
- Cellulose acetate refractive index 1.48-1.51: https://cameo.mfa.org/wiki/Cellulose_acetate
- PDMS refractive index: https://refractiveindex.info/?shelf=organic&book=polydimethylsiloxane
- Lens index ↔ reflectance (AR, 8 % at 1.74): https://www.opterio.com/learn/anti-reflective-coatings-guide
- Metal base colours: https://physicallybased.info/ · UE physically-based materials chart
- UE glTF importer extension support (5.0+): Epic glTF Importer roadmap / UE glTF exporter docs


---

# Appendix B — presentation: hero render and turntable (2026-09-12)

Appendix A covers getting *a* render out. This appendix covers getting an **AAA product
render** out — the hero still and the turntable — and what the builder must emit so that
render is repeatable rather than luck. It extends Appendix A; it does not repeat it.

The existing builders supply geometry and nothing else. `MEL_eyewear_pair` emits **one joined
mesh with no material slots**. Everything below therefore starts from "the builder must emit
more" rather than "the artist must work harder".

## B.1 What the photography rigs actually are

The one practitioner source found that documents an eyewear rig in numbers rather than
adjectives is the eyewear chapter of *Lighting for Fashion Accessories* (Rocky Nook):

| Case | Rig |
|---|---|
| Prescription, flat lenses | **a large diffused light box for the lenses + small diffused sources for the temples and edges** |
| Sunglasses | **backlight** through a large light box + a **rounded reflector in front** of the frame |
| Lens coverage ("family of angles") | **180° for flat lenses, up to 250° for curved, 300° for goggles** |
| Reference distances | **60 in octabox ≈ 3 ft from the frame, behind a 98 × 60 in diffusing fabric** |
| Reflection angle on the lens | light placed **slightly descending, ~10–20°** |
| Catalog presentation | **shadowless**, frame on an **elevated sheet of glass** |
| Advertising presentation | **high-key, large and very soft**, "glasses are made so you can see better" |

Three load-bearing readings from that:

1. **Eyewear is not a three-point product rig.** The dominant source is one very large
   diffuser sized to cover the *whole* family of angles, plus small sources specifically for
   the acetate edges and the temples. The small sources exist because the big one is too
   diffuse to describe an edge.
2. **The diffuser is huge relative to the subject** — 2.5 m of fabric for a 134 mm object,
   ~15–20× the subject width, at roughly 6–7× subject width of distance. Proportion, not
   absolute size, is what ports to 3D: any small area light will read as a hard, wrong
   glaze on acetate.
3. **Shadowless is the catalog default**, which is why the elevated glass sheet exists. The
   contact shadow is an editorial/advertising choice, not a catalog one.

`Light: Science & Magic` (Hunter/Biver/Fuqua) is the underlying theory — "the family of
angles" and "the angle of incidence equals the angle of reflectance" on a smooth surface. The
relevant consequence for a lens: **you never light glass, you light what it reflects.** The
lens is a mirror with a slight tint; the visible content of the lens is the virtual image of
whatever large bright shape sits inside that family of angles.
This is convention-as-physics: it is the documented model, and it applies to a 3D renderer
directly because a path tracer computes the same reflection.

## B.2 Acetate edge glow

Retailer/editorial sources (Warby Parker, eluno, shutterstock descriptions) consistently
describe the same thing: translucent tortoise/crystal acetate **glows at the edges**, and on a
polished rim the edge reads "jewellery-like". This is documented as a *look*, not as a
measured optical figure — treat it as convention. It is also physically obvious: at an edge
the material is thin, so transmitted light escapes there that cannot escape through the
6 mm-deep rim face.

For the builder that means **the rim edge is a separate region that must be identifiable**,
because the shader that produces the glow is a thickness/edge-mask shader, and there is no UV
layer to build that mask from.

## B.3 Lens

- Uncoated optical surfaces reflect ~4 % per surface; AR coating takes that under ~0.5 % and
  leaves a faint residual colour (green is the common one; magenta/purple also occurs). No
  measured source in this research gave the coating figure — **convention**.
- Clear lenses: keep near-full transmission with the faint green cast. Sunglasses: subject to
  tint, roughly 10–30 % VLT depending on category.
- The blowout failure is not the lens transmission, it is the **specular lobe** of whatever
  bright shape is in the family of angles. Polish the lens to roughness ≈ 0.02–0.08 and shape
  the *source* (a large soft plane, not a hot point) and it reads as glass. Leave the default
  white specular and a small light and it reads as a white blob.

## B.4 Turntable numbers

| Source | Number |
|---|---|
| Miops (360 product photography guide) | **24 frames / 15° = functional minimum; 36 frames / 10° = the standard recommendation** for ecommerce |
| ProductPhoto.com | offers **24, 36, 72** frames |
| Iconasys turntable hardware | up to 10,200 frames / 360°, 0.03° precision — the ceiling, not the norm |

Easing: a real product spin is **constant angular velocity**. Ease-in/ease-out on a 360° loop
produces a visible hitch at the seam; if easing is wanted it has to be a per-shot video
decision, not part of the spin rig. This is convention (no vendor document states it), but it
follows from the seam.
Also conventional and important for reflective products: in a real turntable **the product
rotates and the lights do not**. Orbiting the camera instead holds the highlight still and
makes a specular product look subtly wrong across the spin.

## B.5 Product versus editorial

E-commerce/product: neutral, even, shadowless (or minimal contact shadow), honest colour,
frame silhouette legible, lens deliberately quiet. Editorial/beauty: directional key with
falloff, one graphic highlight, gradient environment, shallow depth of field, a mood, lens
either dramatised or vanished. Both are documented distinctions in fashion-photography
writeups (ArtChick, Elixxier) — the useful part for us is that **they are two rigs, not two
grades**, so they have to be two presets.

## B.6 Bake versus post

Rule that follows from the turntable: **anything that must be identical across 36 frames has
to be in-scene.** A lens reflection, an acetate glow, a gradient background — in-scene is one
change; in post it is 36 or 72 retouches that will drift.
In-scene: geometry, material separation, vertex-attribute masks, orientation/origin, camera,
lights, view transform, and depth of field.
Post: crop, dust, white balance, background compositing behind the alpha, campaign grade,
and the small retouch that removes a fixture reflection the rig could not avoid.

## B.7 Pipeline requirements this implies

1. `MEL_eyewear_present` — nests `MEL_eyewear_pair` + `MEL_eyewear_lens`, applies the
   **−90° X** stand-up rotation, sets the object origin to the **optical centre** (not the
   bounding-box centre, or the spin wobbles), and emits material slots.
2. Named material slots on the joined mesh, aligned with the Amazon eyewear node names where
   they map: `Frame`, `TempleR`, `TempleL`, `LensR`, `LensL`, plus `Metal` for the hinge
   barrel. Acetate and metal cannot share a shader; the lens cannot share with either.
3. Named vertex attributes (the only spatial channel available without UVs), via the existing
   `MEL_store_named_attr`: at minimum a part id, and a **rim-edge / thickness mask** to drive
   the acetate edge glow. Suggest `eyewear_part_id`, `eyewear_edge`, `eyewear_thickness`.
4. Camera presets in `presets.py` (`BUILDERS_PRESETS` already carries the preset shape):
   `HERO_3Q`, `FRONT_ORTHO`, `PROFILE`, `TOP`, `HINGE_MACRO`, and a `TURNTABLE` rig.
   Front elevation wants an **orthographic** camera — it is the technical/product view.
5. Lighting presets, proportionally scaled to a 134 mm subject: `CATALOG_SHADOWLESS`
   (large diffuser + elevated glass), `STUDIO_ACETATE` (big key + small edge sources),
   `SUNGLASS_BACKLIGHT` (backlight + front rounded reflector), `EDITORIAL_GRADE`.
6. Scale contract stated in the asset: keep mm (1 BU = 1 m). Then the render rig must set
   `camera.clip_start ≈ 0.0005` (the 0.1 m default clips the whole asset away) and light
   sizes/powers authored in the same unit space. A `PRESENT_CM` variant at ×10 (1 BU = 1 cm,
   frame ≈ 1.34 BU) is the more comfortable authoring space and is worth emitting.
7. Smooth-shading contract: `Shade Smooth` with an angle-based auto-smooth (~30–40°) so the
   rim reads as one polished sweep while the endpiece and hinge barrel keep their breaks.
