# Brooch v10 — silhouette system + polished petals (plan)

SUPERSEDED 2026-09-16 by `BROOCH_V10_GRANDMASTER_PLAN.md` — kept for the diagnosis record (§1) and the
construction detail (§2). The grandmaster plan is the working authority.

2026-09-16 · Supersedes the "v9 petal block" of `BROOCH_GRAND_PLAN_2026-09-16.md`.
Identity authority: `BROOCH_IDENTITY_RESEARCH.md`. Pipeline discipline: `PIPELINE_GUIDE.md` (unchanged).
No second geometry authority. SDF.R stays out of the geometry path.

## 1. What regressed — measured, 2026-09-16

**SDF.R is not the cause.** R1 spike re-checked against its artifacts: feeding the gold body
produced `SDF_Snapshot_002`/`003` at dims **200.0 x 200.0 x 200.0 mm, 19,268 verts** — identical
at res 320 and 512. That is the name-classified parametric blob, not the brooch. The spike was
read-only; `sdfr_cleanup.py` (19:17) removed `_LAB_SDFR_gold`, `SDF_Collection`, `SDF_History`,
snapshots; a cold read (`--factory-startup`) of the saved `FlowerBrooch.blend` shows **zero
SDF-R residue**. Trap on record: the spike renders looked plausible because the hidden-set rule
kept `_LAB_SDFR_gold` visible — they show the SOURCE, and the blob is hidden behind it. Verdict
stands: SDF.R = standalone parametric findings lab only.

**The regression is the v9 petal surgery** — the petal block was replaced with a uniform 20x48
grid surface + ExtrudeMesh slab (`petal_surface()`, `Tools/gen_flower_brooch_v9.py:339`).
Measured symptoms (renders `Saved/Audit/v9_state_front_flat.png`, `v9_state_petal_macro.png`,
`v9_cast_on_macro.png`, `v9_cast_off_macro.png`; spike shots `petal_spike_*.png`):

- margin sampled at 48 uniform rows -> staircase silhouette (48 straight segments on the outline)
- ExtrudeMesh thickness -> knife-edge rim, no rolled edge; petals read as thin fins
- glossy metal shows flat specular patches across the coarse grid (facet lattice at macro)
- cast weld on thin slabs is an amplifier not the root: cast OFF still faceted; cast ON adds
  stair-steps at the rim/tip
- sizing slipped: hero 53.75/60 (-10.4%), mini -13.9%, halo -15.7% worst-axis; the law is <=5%
  (v8 was within ~7%)

Everything else is v8-intact: hardware, pave seating, gems, dangles, materials, compositor.

## 2. v10 petal — smooth by construction (curve-native)

Build the prototype ONCE (subd on the prototype), then instance. Never extrude a rim.

    A. SPINE     CurvePrimitiveLine (or Quadratic Bezier) base->tip; bend/recurve via
                 SetPosition on spline points or Higgsas Bend; ResampleCurve (Count ~40-64)
                 for uniform arc-length samples.
    B. MARGIN    half-width w(u) from a curve profile (ShaderNodeFloatCurve) -> SetCurveRadius;
                 frill = second harmonic added into the width field.
    C. LENS      closed lens cross-section swept along the spine (CurveToMesh, Profile Curve)
                 -> boat/canoe volume with a ROUNDED rim for free. Sheet variant: margin outline
                 -> FillCurve -> Solidify (rounded-rim mode).
    D. POLISH    SubdivisionSurface (Level 2) on a LOW cage (10x24 -> ~40x96 effective);
                 Edge Crease = 1 down the midrib keeps the spine crisp; vertex crease at tip.
    E. DETAIL    midrib ridge via crease + z-offset field; striations = wave field on the lofted
                 surface (keep the existing mathx pattern).
    F. THICKNESS Solidify (Higgsas) or Mesh Offset; rim rounding is part of the lens profile.

Density follows curvature (per-archetype resample + subd level), never one global grid.
New per-whorl sockets: Archetype (menu), Spine Bend / Recurve, Margin Amp / Freq / Phase,
Tip Sharpness, Reflex, Roll, Thickness. The §3 socket contract of the guide is unchanged.

## 3. Silhouette vocabulary (petals + alternatives to petals)

- **Petal archetypes**: round, acuminate, spatulate, cordate, frilled/ruffled, reflexed, cupped
  (margin function + tip + reflex, all curve-driven).
- **Non-petal elements** (same whorl placement, new element trees):
  leaf (toothed margin, midrib crease) · plume/feather (ragged vane + Scales Texture microrelief)
  · wing/paillette (asymmetric shear) · whiplash scroll (Higgsas Spin, Art Nouveau S-curve)
  · ribbon (Even Curve to Mesh / Curve Offset on a wave spine) · tendril (spiral, decaying radius)
  · briolette/drop (revolved lens; gem cap) · fan/shell (scallop — House REF_01 motif; CurveStar
  or radial ribs) · cymatic diaphragm (Chladni nodal pattern -> pierced openwork).
- **Genome**: add `silhouette{}` — per whorl {archetype + §2 sockets}. Absent = archetype mapped
  from `petal_profile` (round/pointed), so v7/v8 genomes keep building. Chaos/tilt/roll keep
  working per instance.

## 4. Higgsas layer (verified on disk — use with purpose)

Library: `RawArt/BlenderLibraries/Higgsas/Blender 5.0 Higgsas Geo Node Groups v13.blend`
(279 groups; v13 names are UNPREFIXED — `Spin`, not `NTSpin`). Load: `bpy.data.libraries.load`
+ append (recipe in `Tools/probe_higgsas3.py`). Add a 2-line `higg(tree, name)` appender to the
builder; keep the NT alias rule for addon-side callers.

| Higgsas node | job in the brooch |
|---|---|
| Bend / Taper / Twist / Twist Curve | whorl-level form shaping (reflex, curl, swoosh) |
| Spin | whiplash scroll accents; rolled rims |
| Loft Splines / Even Grid Profile Surface / Phyllotaxis Profile Surface | smooth petal lofting + whorl placement |
| Bezier Resample | uniform-arc-length margins — the anti-staircase pass |
| 3D Fill Curve | margin outline -> sheet petal (feed Solidify) |
| Solidify / Mesh Offset / Edge Offset / Face Offset / Curve Offset | even thickness, rounded rims, border bevels |
| Inset Face | engraved border cells / enamel channels |
| Dynamic Catenary Splines | draped pearl swags + true-hanging dangle chains |
| Cairo Tile / Bricks / Hexagon / Triangle Grid; Distance to Edge Voronoi | pierced openwork backplate (scallop lattice / filigree) |
| Ripples Solver | Tide-element water-shimmer relief |
| Rounded Cube / Rounded Cone / Pyramid | fancy-cut gem seats (emerald / pear / marquise read) |
| Scales Texture | feather vane / scale microrelief (plume archetypes) |
| Mesh Face Subdivide / Recursive Subdivision | controlled smoothing where SubdSurface over-rounds |
| Voxel Remesh | NOT for petals (blockiness family); derived-bake helper only |
| SDF Spiral / Torus / Heart / Capsule (Higgsas) | motif sketches only — not geometry authority |

## 5. Cast recalibration + the new curve gate

- Petal-first cast: hero voxel 0.20 mm / Fillet 1 / Mean 0 for pointed; 0.25 / 1 / 1 for round.
  Re-derive per profile under the err<=5% law.
- If the weld still stair-steps thin rims: split the cast — weld the metal body, keep petals out
  of the voxel pass (material gate).
- Sizing: keep two passes, add ONE re-solve iteration (pass B measure -> S correct -> rebuild)
  so err lands <=5% BEFORE shots (v9 slipped because the solve was single-shot).
- NEW GATE — silhouette smoothness (numbers, not vibes): walk the evaluated petal boundary loop,
  compute max turn angle per segment at macro scale; record the v7 baseline; v10 must be
  <= baseline x 0.5. Per-archetype line in `BUILD_REPORT_V10.txt`.
- Normal continuity: face-normal angle-step histogram; no isolated jumps except the crease line.

## 6. Build order

    P0  v10 petal prototype (round + acuminate) + subd/crease — gate: smoothness metric + err<=5% cast ON
    P1  full archetype set + genome silhouette{} + back-compat map; contact-sheet shots
    P2  Higgsas batch A: Spin scrolls + Catenary garlands on existing dangles
    P3  Higgsas batch B: openwork backplate (Cairo/Hex/Voronoi) + Ripples (Tide) + gem fancy cuts
    P4  non-petal elements (leaf / plume / ribbon) as alternate whorls; hero variants
    P5  shots + BUILD_REPORT_V10 + intake refresh; keep v9 trees as compare baselines

Deliverables: `Tools/gen_flower_brooch_v10.py` (copy-and-patch from v9, same helper set);
`Saved/Audit/v10_*` diagnostics; `BUILD_REPORT_V10.txt`; one roadmap line in the guide.

## 7. Verified 5.2 node facts for this build (probed 2026-09-16)

`GeometryNodeSubdivisionSurface` exists — inputs Mesh/Level/Edge Crease/Vertex Crease/... —
Catmull-Clark in-tree with creases. `ResampleCurve`, `CurveToMesh`, `FillCurve`, `TrimCurve`,
`SampleCurve`, `SplineLength`, `InputTangent`, `SetCurveRadius`, `SetCurveTilt`,
`CurvePrimitiveLine/Circle/Quadrilateral`, `CurveQuadraticBezier`, `CurveStar`, `CurveSpiral`,
`ShaderNodeFloatCurve` (works as the profile curve node), `GeometryNodeMenuSwitch` all present.
MISSING: `CurveCubicBezier`, `SweepMesh`, `BlendCurve`. Probes: `Saved/Audit/node_probe_v10*.py`.

## 8. Non-goals

No SDF.R in the geometry path (R1 verdict stands). No second geometry authority, no Sverchok.
Cast chain remains the finishing stage. Hardware / gems / dangles / materials untouched in P0.
UE export stays parked until the wardrobe hook opens.
