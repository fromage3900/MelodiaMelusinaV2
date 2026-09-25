> **SUPERSEDED 2026-09-24:** Action SSOT is now `Docs/Plans/MELUSINA_GN_PLAN_2026-09-24.md` (twin: `Saved/Audit/MELUSINA_GN_PLAN_2026-09-24.md`). Keep this file as historical research; do not treat it as the current character/bionic GN plan.

# Ultimate Geometry Nodes Framework — Bionic Waifu / Hard-Surface Research & Plan

> **Status:** RESEARCH → PLAN. Date: 2026-09-23.
> **Trigger:** doll-joint staging (12 balls + cuff rings) proved the mechanical-doll
> aesthetic direction; next expansion needs a real GN framework, not hand-made meshes.
> **Live testbed:** canonical Blender 5.2.1 session, MCP on 9876, `melodia_gn` framework.

---

## 1. External research — top GN pipelines & hard-surface canon

### 1.1 Higgsas Geometry Nodes Toolset (v13 on disk; the "Jiggsas" nodes)

250 node groups in 15 categories (Superhive, Blender 5.0 build). The complete
catalog was reviewed; the groups that matter for **character/bionic hard-surface**:

| Category | Groups we will actually use | Why |
|---|---|---|
| Curves | Curve Forward Kinematics, Curves Inverse Kinematics, Loft Splines, Even Curve to Mesh, Align Curve to Surface, Blend Curves | bionic limb actuators follow the armature pose; pipe/piston sweeps with even radius |
| Deformers | Surface Bind, Mesh Offset, Solidify, Taper, Sharpen Mesh, Bend | armor plates that ride the body mesh; panel offset control |
| Geometry Measure | Mesh Curvature, Mesh Ambient Occlusion, Mesh Thickness, Mesh Tension, Mesh Fresnel, Geometry Center, Fit Plane | **direct input to Copernicus bake priority** (curvature/AO maps) + procedural placement masks |
| Mesh Primitives | Rounded Cube, Capsule, Rounded Cone, Spur Gear, Torus, Super Ellipsoid | mechanical joint vocabulary (gear rings, capsule pistons) |
| Generators | Inset Face, Edge Offset, Mesh Face Recursive Subdivision, Voxel Remesh, Mirror, Spin | panel-gap generation, rotational symmetric parts |
| Distribution | Circular Array, Distribute Points on Edges/Volume, Circle Packing | bolt circles, rivet rows along panel seams |
| SDF | SDF Boolean, SDF Round Cone, SDF to Mesh | watertight boolean unions for joint sockets (no coplanar-face artifacts) |
| Selection | Edge Angle Selection, Expand/Contract Selection, Is Inside Volume | boolean-edge detection for weighted bevels |
| UV | Cylinder UV Mapping, UV Seam, Triplanar UV Mapping, UV Unfold | trim-sheet discipline for Copernicus 9-map bakes |
| Simulation | Differential Growth, Reaction Diffusion | organic-mechanical fusion surfaces (late-phase, optional) |
| Utilities/Falloffs | Spherical/Object Falloff, Vector fields | pose-aware bulges at joint sites |

### 1.2 Hard-surface canon (how people actually build accurate mecha/bionic)

Consensus techniques across Blender Artists / Blender Secrets / pro courses:

1. **Conformal projection is the foundation.** Shrinkwrap (modifier) and its GN
   equivalents (Raycast node, Sample Nearest Surface) project panel/kit geometry
   onto the body. Modifier-order discipline: Shrinkwrap → Solidify → Bevel; GN
   equivalent ordering: Raycast/Set Position → Solidify → bevel-weighted edges.
2. **Panel work = boolean cuts + bevel-weight management.** Non-destructive
   panel cuts with the Boolean node's *Intersecting Edges* output driving bevel
   weights (since 3.3) — the industry answer to "bevels on boolean edges".
3. **Detail is instanced, not modeled.** Screws/bolts/vents are kitbash pieces on
   Circular Array / Distribute Points on Edges; "floaters" (free-floating detail
   shells) baked to normal maps for distant LOD.
4. **Curves do the mechanical plumbing.** Curve-to-mesh pipes with profile
   curves; cable harnesses via catenary + advect; IK curve rigs for actuators.
5. **Decal/mesh-decal systems** (DeckardX08-style GN decals) apply topology-
   independent surface markings — directly applicable to seam lines / serial
   plates / warning stripes on bionic limbs.
6. **The parametric-vs-apply tension is real.** Community practice: stay
   parametric through design; apply once for UV/texture pass; keep the
   parametric backup. Our framework mirrors this as **bake-boundary discipline**:
   GN builders → staged FBX export → Copernicus bake (never re-edit baked maps
   by hand).

### 1.3 Character-specific GN state of the art (5.x)

- **Sample Sound Frequencies node** (5.2 LTS, first-class GN): sound strip → FFT
  amplitude fields. Already adopted in our audio pipeline research — bionic
  emissive seams can ride the same contract as cymatic fabric.
- **Curve IK/FK in GN** (Higgsas): hard-surface cables that follow a posed rig
  without armature weighting — key for bionic limbs on an animated waifu.
- **Mesh Tension / rest_position**: deformation-aware detail (plating that
  "flexes" visually at joints) without simulation.

---

## 2. Repo review — existing GN plans & what they already prove

| Asset | State | Relevance |
|---|---|---|
| `deploy/surreal_arch/melodia_gn/core.py` (1514 lines) | LIVE | The framework core: `register_builder`, preset schema, `new_geometry_tree`, `link_sockets` + link-failure ledger, universal music pass, audio bake-lane contract (`audio_amp`/`audio_band` ↔ UE MPC). This is the chassis the new framework extends — not replaces. |
| `melodia_gn/` builders (173 claimed; angel/castle/kits/…) | LIVE | Builder-family pattern proven: parametric dials, presets over tree copies, headless verify receipts (angel_convergence pattern: node counts + preset keys + audio contract). |
| `deploy/surreal_arch/higgsas_bridge.py` (132 lines) | LIVE but narrow | Loads Higgsas groups from `RawArt/BlenderLibraries/Higgsas/...v13.blend`, NT-prefix aliasing, `higg_node()` with native fallback. **Today used only for arch surface overlays (brick/hex/voronoi).** |
| `Tools/higgsas_gate.py` (F1 gate) | LIVE | Gates G1–G6 prove library resolution + real GeometryNodeGroup (no silent fallback). The audit pattern to clone for the bionic layer. |
| `Docs/Research/BLENDER_AUDIO_GEOMETRY_NODES_PIPELINE_2026-09-02.md` | RESEARCH | 2-track audio strategy (procedural Sample-Sound + baked-to-UE). Bionic emissive hooks into this. |
| `Tools/Houdini/copernicus/` + `Saved/Audit/copernicus_cymatic/` (1665 PNGs, 9-map contract) | PRESENT | Bake lane and acceptance probe (PNG magic + count) already exist. Geometry Measure groups (§1.1) feed it. |
| Doll joints (12 balls + 2 cuff rings) | HAND-MADE | Proof of concept, but every part was sculpted manually. This is exactly what builders should generate. |

**Doctrine already in force** (keep): one builder = parametric family; presets are
dial sets, never tree copies; audio is bake-lane attributes, never runtime GN;
every builder has a headless verify receipt; Higgsas groups must never silently
fall back (F1 gate pattern).

---

## 3. Gap analysis — what a bionic waifu needs that we don't have

1. **No body-conformal layer.** Nothing raycasts/shrinkwraps panel geometry onto
   Melusina's mesh. Today's doll balls are free-floating spheres.
2. **No mechanical-joint builder family.** Ball + socket + seam ring + cuff ring
   were hand-made today; should be `MEL_bionic_joint` with dials.
3. **No fastener/greeble instancing on seams.** Rivets/bolts along panel edges
   don't exist.
4. **No boolean panel-cut discipline** with bevel-weight control for hard-surface
   plating on soft body parts.
5. **Higgsas is underused**: 33 of 250 groups, arch-only. The character-relevant
   subset (§1.1, ~25 groups) is untapped.
6. **No UV/trim-sheet layer** for the Copernicus 9-map contract on character parts.

---

## 4. The expanded framework — MEL_bionic (working name)

Four layers, all extending existing chassis:

### Layer 0 — core.py additions (small, shared)
- `raycast_set_position(tree, loc, target_obj_input, direction, length)` — wraps
  Raycast + Set Position conform helper (the shrinkwrap-GN equivalent).
- `bevel_weight_from_boolean(tree, ...)` — boolean intersecting-edge → edge
  weight attribute, feeding Set Edge Weight.
- `link_higgsas(tree, name, loc, monolith, fallback)` — promote existing
  `higgsas_bridge.higg_node` into core so every builder uses Higgsas uniformly.

### Layer 1 — curated Higgsas character subset (~25 groups)
Extend `HIGGSAS_ARCH_NODES` into `HIGGSAS_CHARACTER_NODES`: Curve FK/IK, Loft
Splines, Even Curve to Mesh, Surface Bind, Mesh Offset, Solidify, Rounded
Cube/Cone/Capsule, Spur Gear, Circular Array, Distribute Points on Edges,
Inset Face, Edge Offset, Edge Angle Selection, Cylinder UV Mapping, UV Seam,
Triplanar UV Mapping, Mesh Curvature, Mesh AO, Mesh Thickness, SDF Boolean,
SDF Round Cone, Taper, Sharpen Mesh, Mesh Tension.

### Layer 2 — new builder families (melodia_gn register pattern)
| Builder | Dials (examples) | Notes |
|---|---|---|
| `MEL_bionic_joint` | ball radius, socket depth, seam ring count/width, cuff ring on/off, taper | **Absorbs today's hand-made balls + rings**; SDF boolean socket; gear-ring option (Spur Gear) |
| `MEL_armor_panel` | conform offset, thickness, panel gap width, taper to wrist/ankle | Raycast onto body mesh; Solidify; bevel weights |
| `MEL_fastener_field` | spacing, diameter, pattern (circle/row), falloff | Distribute on Edges along panel seam curves |
| `MEL_panel_cut` | cutter set, bevel width, intersecting-edge only | Boolean discipline with weighted bevels |
| `MEL_actuator` | stroke, segments, cable radius | Curve IK following armature bones (no weighting) |
| `MEL_seam_decals` | decal set, density | DeckardX08-style mesh decals; UV-driven for trim sheet |
| `MEL_trim_uv` | unwrap mode, seam set | Feeds Copernicus 9-map bake contract |

Every builder: preset schema + audio-lane attributes (emissive seam option) +
headless verify receipt (node counts, preset keys, audio contract, **evaluated
bounds sanity** — the throne flame-radius bug class is caught by bounds, not
node counts).

### Layer 3 — audio-reactive + bake contract
- Bionic emissive seams ride the existing `audio_amp`/`audio_band` contract
  (UE MPC mirror unchanged — one vocabulary, two ends).
- Copernicus 9-map bake per family; Higgsas Mesh Curvature/AO/Thickness groups
  double as **bake masks** (edge-worn metal from curvature, cavity dirt from AO).
- Bake boundary: builders → FBX staging → Copernicus → UE MI. No hand map edits.

### Governance
- **F2 gate** (clone of F1): all `HIGGSAS_CHARACTER_NODES` load; bionic trees
  contain real GeometryNodeGroup where a Higgsas group is claimed; evaluated
  bounds within expected envelope per builder.
- Higgsas calls never silently fall back (existing rule, now enforced on the
  character lane too).
- Ball-joint expansion (knuckles/neck/waist/sheep, per the 2026-09-23 staging
  plan) becomes the **first consumer** of `MEL_bionic_joint` instead of more
  hand-made spheres.

---

## 5. Build order (next sessions)

1. **Layer 0** core helpers + F2 gate skeleton (1 session).
2. **`MEL_bionic_joint` v1** — regenerate the existing 12 balls + 2 rings
   parametrically; diff evaluated bounds against today's hand-made reference
   (must match within tolerance — this is the acceptance test).
3. **Knuckle/neck/waist/sheep expansion** through the builder (presets, not copies).
4. **`MEL_armor_panel` + `MEL_fastener_field`** on one bionic forearm plate
   (conform onto Melusina's arm, bolt row along the seam) as the vertical slice.
5. **Copernicus bake pass** for the bionic set (9-map contract, curvature/AO masks).
6. Actuator/decal builders once the slice is accepted.

## 6. Open decisions for owner

- Bionic coverage: full limbs vs. joint-adjacent accents only (doll vs. cyborg dial).
- Plate material family: porcelain / painted steel / brass (drives Copernicus style).
- Whether Higgsas groups may be **linked** (live) or must be **appended** (current
  bridge behavior) in shipped character files.
