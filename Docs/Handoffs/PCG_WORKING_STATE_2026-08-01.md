# PCG — from "unusable" to two working levels, 2026-08-01

## ⚠️ Editor Ensure caused by probe-asset churn — process note

An Ensure fired at 20:46 (`ObjectTools.cpp:4043`, surfaced via `UnrealEditor-MonolithEditor.dll`).
Cause: **repeatedly creating and deleting temporary `_probe_*` PCG graphs** to introspect PCGEx node
pins. Deleting a freshly-created, still-referenced asset trips that Ensure. It is a *caught*
assertion, not a hard crash, but it produces a crash report and is avoidable.

**Rule going forward: do not delete probe assets mid-session.** Create them once under
`/Game/EnvSandbox/PCG/_Dev/` (already the designated scratch folder — it holds five older
`PCG_TEST_*` files) and leave them. Three remain: `_probe_pcgex`, `_probe_pcgex2`, `_probe_pcgex3`.
They are harmless, unreferenced, and safe to remove via the Content Browser when the editor is idle.

Introspection itself was worth it — it is how the PCGEx shape/tensor architecture below was mapped —
but the create-then-delete cycle was the wrong shape.

## Graph library — all verified emitting

| Graph | Style | Inst | Technique |
|---|---|---:|---|
| `PCG_Escher_SpiralAscent` | Escher | **196** | **PCGEx Tensor** — spin field + `ExtrudeTensors`, Z spread −594→+487 (true 3D sweep) |
| `PCG_Nikki_PhyllotaxisGarden` | Sakura | 140 | PCGEx `Fiblat` — golden-angle Fibonacci lattice |
| `PCG_DreamWalls` | Escher | 144 | core `CreatePointsGrid` |
| `PCG_Nikki_DreamStones` | Sakura | 81 | core grid, full yaw, 0.6–2.4× scale |
| `PCG_Escher_SteppedColonnade` | Escher | 64 | core grid, zero yaw, 900 uu Z-step |
| `PCG_BaroqueColonnade` | Baroque | 48 | core `CreatePoints` ×5 |
| `PCG_Nikki_MandalaBloom` | Sakura | 36 | PCGEx `Circle`, closed loop |
| `PCG_Escher_PenroseRing` | Escher | 25 | PCGEx `Polygon`, 5-fold |

### PCGEx architecture (1419 classes, 381 node types available)

**Shape system:** `CreateShapeCircle`/`Fiblat`/`Polygon` do **not** emit points — each outputs a
**"Shape Builder"** factory that plugs into `PCGExCreateShapes` alongside a **"Seeds"** point input.
One seed grid × one builder = a shape at every seed, so seed spacing multiplies the pattern for free.

**Tensor system** (the "moving architecture" answer): `CreateTensorSpin` takes **Effectors** →
outputs **Tensor**; `ExtrudeTensors` takes **Seeds** + **Tensors** → outputs **Paths**, which feed
`TransformPoints` → `StaticMeshSpawner` directly. `iterations` controls path length. This is what
produces sweeping vertical structure rather than flat scatter.

### API gotchas (each cost an attempt)

- PCGEx config lives in a `config` struct, not top-level props.
- Numeric PCGEx fields (`resolution`, `potency`) are `PCGExInputShorthandSelector*` structs — set
  `.constant`, never a raw float.
- `graph.add_edge(node,'Out',node,'In')` — there is no `add_labeled_edge`.
- `StaticMeshSpawner.mesh_selector_parameters` is **read-only** — mutate the existing selector.
- `TransformPoints` uses `offset_min`/`offset_max`, not `translation_min/max`.
- `PCGComponent.cleanup(True)` requires the argument explicitly.

**Volume scaling:** use `pcg_graph_builder.fit_volume_to_ground()` — it derives scale from a tagged
`Ground` actor's bounds (`extent*2/100`) instead of guessing, and falls back to a preset when no
ground is tagged. Do not hand-multiply volume scale; that is what crashed the editor.

## Headline

**The PCG library was never broken. It was dormant.** Every graph inspected was fully wired with
valid mesh references; the volumes had simply never been generated. Two levels now emit.

| Level | Graph | Instances | State |
|---|---|---:|---|
| `L_FallenMoon` | `PCG_DreamWalls` | **144** | working, **saved** |
| `L_KaleidoNave` | `PCG_BaroqueColonnade` | **48** | working, **saved** |
| `L_MelusinaMorning` | `PCG_Morning_MemoryDressing` | 0 | blocked — VolumeSampler, see below |
| `ZenForestTest` | — | — | deliberately untouched (protected map; Foliage tool already dresses it) |

## The rule that predicts success

Four graphs tested. The split is clean and total:

| Graph | Source node | Result |
|---|---|---:|
| `PCG_DreamWalls` | `PCGCreatePointsGrid` | **144** |
| `PCG_BaroqueColonnade` | `PCGCreatePoints` ×5 | **48** |
| `PCG_Dreamstate_DistantRuin` | `PCGVolumeSampler` | 0 |
| `PCG_Morning_MemoryDressing` | `PCGVolumeSampler` | 0 |

**Graphs sourced from `CreatePoints`/`CreatePointsGrid` work. Graphs sourced from `VolumeSampler`
emit nothing** — and it is *not* volume size: the Morning volume was enlarged from 270×270×150 to
5400×5400×1200 and still produced zero. The scale change was reverted and that level was **not saved**.

Diagnosing `VolumeSampler` is its own task. Until then, **prefer CreatePoints graphs** — that alone
unlocks most of the library, since `CreatePoints` graphs need no landscape, spline, or surface.

## Three traps that made a working library look dead

1. **`generate()` is async.** Counting instances in the same call returns 0. This is documented in
   `pcg_false_zero_audit.py` and is almost certainly the origin of "most PCG is unusable."
2. **PCG may spawn onto managed actors**, so counting ISM components on the volume itself is a second
   false-zero shape. Count **level-wide**, excluding `InstancedFoliageActor`.
3. **`InstancedFoliageActor` masks everything.** `ZenForestTest` has **633,274** foliage-tool
   instances — none of them PCG. Any level-wide count that includes it looks healthy no matter what
   PCG does.

## Two landmines fixed in `apply_four_level_pcg_pass.py`

- **It crashed the editor.** `set_actor_scale3d(100, 100, 10)` — a `PCGVolume` spawns at default
  scale **(25, 25, 10)**, already 5000×5000×2000 uu, so this is **4× default in XY →
  20,000 × 20,000 × 2,000 uu (200 m × 200 m × 20 m)**, four generating simultaneously. Now uses
  default scale. Very likely why the four-level dressing pass was authored and never landed.
  *(Corrected: an earlier version of this note said "5 km" — that assumed scale 1 = 5000 uu, but
  scale 1 is 200 uu and the default spawn scale is 25. Tenfold overstatement, now fixed.)*
- **`L_FallenMoon` has no landscape** — 22 static meshes, no terrain — yet was assigned four
  surface-scattering graphs. They could never emit there. Replaced with `PCG_DreamWalls`; the
  originals are named in a comment so nobody re-adds them thinking they were forgotten.

## ⚠️ The polish blocker is BROKEN MESH SCALE, not PCG

Owner reviewed both levels: "look ok, could use polish and mesh alignment fixes." Measured, the
alignment is already perfect — a clean 400 uu grid, all instances at Z=0, rotation 0, scale 1. **The
meshes themselves are authored at ~1/100th scale.**

| Mesh | Actual size | |
|---|---|---|
| `SM_wallhi` | 6 × **0** × 5 uu | broken — zero thickness |
| `SM_wallhi_001` | 7 × **0** × 2 uu | broken — zero thickness |
| `SM_surrealtower1` | 3 × 2 × 5 uu | broken |
| `SM_Block_Column_05` | **0** × **0** × 3 uu | broken |
| `SM_Greybox_Rock_A` | 118 × 100 × 119 uu | correct |

Classic metres-vs-centimetres import error. So `PCG_DreamWalls` is placing 144 six-centimetre cards
on a four-metre grid, and `PCG_BaroqueColonnade` is doing the same with columns. The graphs, the
grid, and the generation are all correct — the source assets are two orders of magnitude too small.

**Usage check before fixing:** these four meshes are **not placed directly** in `ZenForestTest`, and
in `L_KaleidoNave` they appear *only* via the PCG volume. So correcting them at source has a small
blast radius — but other levels were not exhaustively checked, and any existing actor compensating
with a ×100 scale would suddenly become enormous.

Two viable fixes, owner's call:
1. **Fix at source** — set Build Scale on the four static meshes. Correct, permanent, benefits
   everything; requires checking for compensating placements first.
2. **Fix in the graph** — set a uniform scale on the mesh descriptor / `TransformPoints` node.
   Local and reversible, but leaves the assets wrong for every future use.

`SM_Greybox_Rock_A` being correctly sized is the control that proves this is an asset problem and not
a project-wide unit convention.

## Next, in order

1. **Diagnose `VolumeSampler`** — likely a voxel/point-spacing setting on the node itself. Unblocks
   `L_MelusinaMorning` and `L_KaleidoNave`'s original Dream_Atmosphere volume.
2. **Capture** the two working levels and judge whether the scatter reads as intentional.
3. **Feed this rule into the Gemini triage** — bucketing 127 graphs is far cheaper now that
   "source node type" is a known predictor of whether a graph can emit at all.

## Rules for anyone continuing

- One volume, one generate, one separate-call count. No batches.
- Default scale until a volume is proven.
- Never save `ZenForestTest`.
- If a count is zero, suspect the measurement before the graph — that was wrong three times today.
