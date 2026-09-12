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

## 7. Builder decomposition

Following the established couture precedent in this addon: `MEL_garment_*` is **nine small
single-purpose builders** (UV unwrap, smart bevel, tension folds, trim UV, vertex AO, material
ID, xpbd drape), not one monolith. Eyewear should decompose the same way:

```
MEL_eyewear_front        cyclic silhouette + cyclic profile sweep  -> frame body, free aperture
MEL_eyewear_temple       arm solid + tip downturn
MEL_eyewear_hinge        barrel + clevis + fold transform
MEL_eyewear_lens         Grid / conformed blank + edge break, separate mesh
MEL_eyewear_edge_break   the manifold-safe bevel pass (reusable, like MEL_garment_smart_bevel)
MEL_eyewear_uv           asserts/creates TEXCOORD_0            <- required, see 5.2
MEL_eyewear_export_gate  realizes + exports + asserts the file is non-empty and UV'd
```

The last two exist purely because of section 5. Without them the pipeline can silently
produce an empty, untexturable asset.

## 8. Units decision — the blocker

The addon has **no units convention at all**: zero uses of `scene.unit_settings`,
`scale_length`, or a length unit anywhere in `deploy/surreal_arch/`. Every existing builder
works in raw Blender units.

Because this builder's entire premise is real measurements, units must be settled first:

- Blender default is 1 unit = 1 m. A 54 mm lens is 0.054 BU.
- **Proposal:** author the group's parameters in **millimetres**, and convert once at the graph
  input (`mm × 0.001`) so every authored number matches the frame's printed marking and the
  published standard. Do not scatter conversions through the graph.
- Consequence: the builder emits geometry 0.001× the scale of the architecture builders. That is
  correct for eyewear, but it means the builder needs its own scene-scale note and will look
  microscopic if dropped into the nave scene.

This needs a decision before any code is written.

## 9. Open items — must be closed before or during the build

1. **Units convention** (section 8) — a decision, not research.
2. **The `void` block / lens material on the web.** `KHR_materials_transmission` is the
   unquantified risk: Blender's own manual warns support is not widespread. For a product where
   the lens *is* the product, this needs its own spike against the actual target viewer.
3. **Re-run the spike on a real builder output.** All measured numbers came from a proxy (one
   bezier rim outline, 2.5 mm bevel). They are valid as relative comparisons and orders of
   magnitude; absolute counts for a finished frame will differ.
4. **Verify `Set Position → Offset`** (section 2) empirically before coding around or with it.
5. **Alpha/transmission and draw-call budget** interact: a 5-node split is 5 primitives = 5 draw
   calls, and that did **not** fall when materials were shared — draw calls track node count,
   not material count.

## 10. What this document is not

It is not the builder, and nothing here has been written into the addon. No file under
`deploy/surreal_arch/` has been touched. The next step is the units decision, then
`MEL_eyewear_front` as a single registered builder with the measurement contract as its
parameter surface.

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
