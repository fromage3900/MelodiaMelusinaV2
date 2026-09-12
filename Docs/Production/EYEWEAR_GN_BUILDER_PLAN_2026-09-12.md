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

### 8.0 Fix first — it blocks 8.4, and it is a real defect (but not the one first reported)

**`MEL_nikki_bead_string`'s `Bead Radius` parameter does not control the bead size.**
Measured with Taper and Jitter forced to 0, so nothing else can move the number
(`Tools/eyewear_verify/bead_size_check.py`):

    Bead Radius 0.022  ->  bead radius 47.80 mm
    Bead Radius 0.010  ->  bead radius 39.10 mm
    Bead Radius 0.044  ->  bead radius 47.80 mm   <- identical to 0.022
    defaults (Taper .55, Jitter .12)  ->  28.89 mm

Doubling the parameter changes nothing at all, and halving it moves the bead by
18%. The value is dominated by something that is not the parameter, so a designer
turning this dial gets almost no response and no indication why.

Correction to the earlier note in this document: the claim that beads come out "an
order of magnitude larger than the parameter" was wrong, and so was the inferred
cause (`_set_group_param(bead_grp, "Radius", 1.0)` fighting the instance Scale).
The earlier evidence was a single spread measurement that happened to sit near
22 mm x Taper x Jitter, which is consistent with correct behaviour. Isolating Taper
and Jitter is what exposed the real fault, and it is a different one.

Prime suspect on the evidence: `_set_group_param(bead_grp, "Radius", 1.0)` does not
reach the nested template, so the bead is the template's own geometry scaled by a
size that is not the author's parameter. Two co-operating values, one comment
claiming the other is authoritative - the same shape of defect as the guide switch
that was added but never wired.

Why it matters beyond the chain: this is the bead/cord authority behind the eave
swag and the wall drop in the study scene. Any garland built with it inherits the
dead dial.

Acceptance: with Taper and Jitter at 0, bead radius equals `Bead Radius` exactly,
at three different values, and scales linearly between them. Anything else is not
fixed.

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
