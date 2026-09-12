# PCG + PPV session — durable wins and reusable recipes, 2026-08-02

The consolidated record. Written so the *reasoning* survives, not just the outcomes — most of these
cost several wrong attempts, and the wrong attempts are the valuable part.

---

# 1. The silent killers — defaults that fail without an error

These produced healthy-looking output while being completely wrong. Each one wasted real time.

### `PCGCreatePointsGrid.coordinate_space` defaults to **WORLD**

A grid graph generates around the **world origin and ignores the volume that owns it**. Moving the
volume does nothing. It was masked in `L_FallenMoon` because the first volume happened to sit at
(0,0,0) — the other five were stacked invisibly on top of it, and the instance count looked perfect.

**Always set `LOCAL_COMPONENT` explicitly on every grid.**

### `PCGActorSelectorSettings.actor_filter` defaults to **Self**

Any by-tag actor search finds nothing. Affects `PCGDataFromActor` *and* `PCGGetSpline`. Set
`ALL_WORLD_ACTORS`.

### Typed property pins reject generic data **silently**

`graph.add_edge(knob, 'Out', grid, 'CellSize')` returns without error and creates no edge. Property
overrides must go to the node's **`Overrides`** pin. Always read `input_pins[].edges` back to confirm
an edge actually exists — the return value tells you nothing.

### `MaterialExpressionCustom.inputs` **replaces all inputs**

Passing `inputs` to `update_custom_hlsl_node` wipes every existing connection. Update `code` alone
when you can; if you must add pins, plan to re-wire every connection.

### `PCGAttributePropertyInputSelector.set_attribute_name()` returns `True` and does nothing

The selection stays `PROPERTY($Density)`. Only text import works:

```python
sel.import_text('PCGBegin(PathDist)PCGEnd')   # -> ATTRIBUTE, name PathDist
sel.import_text('PathDist')                   # -> name '@Last'  (WRONG)
```

---

# 2. PCGEx — how the shape system actually behaves

### Shapes fit to the **seed point bounds**, not their own `default_extents`

The tell: a Fiblat sphere came out at exactly `cell_size/2` radius. `default_extents`,
`bounds_source: CONSTANT` and `PCGExFlatProjection` were all tried and **all ignored**.

**To resize or flatten a PCGEx shape, change the seed grid's `cell_size`.**

### Fitting is **uniform** by default — this is what makes flattening fail

`scale_to_fit_mode: Uniform` + `scale_to_fit: Min` means shrinking `cell_size.Z` shrinks the *whole*
shape. A 4000 uu garden collapsed to a 20 uu ball. For a flat disc:

```python
sf.set_editor_property('scale_to_fit_mode', unreal.PCGExFitMode.INDIVIDUAL)
for ax in ('scale_to_fit_x','scale_to_fit_y','scale_to_fit_z'):
    sf.set_editor_property(ax, unreal.PCGExScaleToFit.FILL)
```

Then `grid_extents.Z = 0`, or a flattened cell produces **stacked seed layers** (140 → 700 instances).

### Tensor reach is set by **effector placement**, not potency

A vault made 8 stub poles because effectors sat at Z≈0 while seeds were at Z=1174 — outside the
field. Moving effectors onto the seed plane turned 8 stubs into 300 poles with a full 2400 uu sweep.

A spin field rotates **one direction**, so seeds on opposite sides arc opposite ways — one row swept
up and over, the other swept *down through the floor*. Symmetry needs **two chains**, the second with
`mutations.invert = True`. No parameter fixes this; it is the geometry of a single rotational field.

### `TransformPoints` offsets are **point-local** by default

A rose window scattered to ±7500 in all axes instead of landing at X 7600, because Fiblat points
carry varied orientations and the offset gets rotated per-point. Set `absolute_offset = True`.
Grid points have identity rotation, which hides this bug until you hit a shape node.

---

# 3. The spline carve — solved, with the diagnostic that cracked it

**`PCGDifference` was abandoned, not fixed.** It depends on the spatial-data semantics of whatever
`PCGDataFromActor` emits, which stayed opaque across two actor classes and three source modes with
verified genuine overlap.

The working chain is numeric instead:

```
CreateShapes ──> PCGExSampleNearestSpline ──> PCGAttributeFiltering ──> …
                        ▲                        (InsideFilter = keep)
   PCGGetSpline ────────┘
   ALL_WORLD_ACTORS + ByTag "PCG_Spline"        GREATER than corridor width
```

Measured: threshold 1200 → 53 survivors of 160, closest at 1203 uu; threshold 700 → 97 survivors,
closest at 707 uu. **Zero inside the corridor both times.** It carves to the spline's actual ribbon
rather than an actor's bounding box, and width is one tunable number.

Live in `pcg_graph_builder._wire_exclusion_filter(graph, prev, pin, corridor_cm=700.0)`.

### The bisect that found it

1. **Does the data reach PCG at all?** `PCGGetSpline → PCGSplineSampler → StaticMeshSpawner` in a
   probe graph. 28 instances appeared along the spline → the actor query works, the consumer is
   the problem. **This step was never run on the Difference chain and would have redirected the
   entire effort.**
2. Bypass the filter → 160 through → sampler fine, filter at fault.
3. Threshold −1 with GREATER → all pass → the attribute resolves; values were simply below it.
4. **Inspect positions, not counts** → exposed the collapsed 20 uu ball. The count still read a
   healthy 160.

### ⚠️ Known limit: the filter threshold is **not overridable**

`PCGAttributeFiltering` exposes only `Operator` and `TargetAttribute` as pins. The threshold lives in
the `attribute_types` struct and cannot be driven from a controller. Two routes remain untried:
drive `PCGExSampleNearestSpline.max_range` from a per-point attribute, or name controller variables
after the target PCG properties so the emitted attribute name matches directly.

---

# 4. Hero graph techniques

### Penrose P3 tiling — mathematically exact

Robinson-triangle deflation, 5 generations, baked into `PCGCreatePoints.points_to_create` as explicit
transforms. **780 edges, every one 631.40 uu, in exactly 5 directions 36° apart** (18/54/90/126/162°)
— re-measured on the *spawned instances*, not just in the generator.

Two things that made it work after two failures:

- **The rhomb side is the MIDDLE of three lengths.** Deflation yields sides in golden progression
  L, Lφ, Lφ²; the short and long values are the thin/thick rhomb *diagonals*. Filtering wrongly gave
  8 distinct lengths and 15 directions — which is exactly what a fake Penrose looks like.
- **An edge lattice suits instancing; rhomb faces do not.** All Penrose edges are equal length, so
  one beam mesh with position + yaw covers the whole tiling. Faces would need shear, which a point
  transform cannot express. The mesh constraint pushed toward the better-looking result.

### Walkability by construction, not subtraction

The Infinite Nave places columns only at Y = ±1200, so the aisle is **permanently clear** — 126 m
walkable, verified zero blockers. This sidesteps the carve entirely. Prefer geometric clearance over
subtraction wherever the layout allows it; it cannot silently fail.

---

# 5. Mesh scale — the repair and the trap

**18 of 29 broken meshes repaired.** Method (multiply the *existing* scale, don't assign, so a mesh
already carrying a non-default scale isn't silently reset):

```python
bs = unreal.EditorStaticMeshLibrary.get_lod_build_settings(mesh, 0)
cur = bs.get_editor_property('build_scale3d')
bs.set_editor_property('build_scale3d', unreal.Vector(cur.x*100, cur.y*100, cur.z*100))
unreal.EditorStaticMeshLibrary.set_lod_build_settings(mesh, 0, bs)
```

Correctness proof: `SM_Block_Cube_1` → exactly 100³, `SM_Block_Wall_4x3` → exactly 400×30×300. The
names encode metres; after the fix the geometry matches the names.

### The feared blast radius mostly didn't exist

~100 referencing external-actor packages looked like artist placements needing migration. They are
**PCG volumes**. In `L_Template`: 11 PCG-spawned ISM entries, **0 hand-placed actors**. PCG
regenerates, so corrected meshes just come back right. Check per level — count plain
`StaticMeshComponent` users vs `InstancedStaticMeshComponent` users. Only plain ones need migrating.

### ⚠️ The REAL hazard: graphs that compensate

`L_KaleidoNave`'s colonnade rendered at **3200 m across**. `PCG_BaroqueColonnade` bakes ×100 into all
48 `CreatePoints` transforms — compensation from when its meshes were tiny. The meshes were fixed in
an earlier session; the compensation never was, so the correction applied **twice**.

**Before Build-Scale-fixing any mesh, check whether the graphs using it bake a compensating scale.**
15 graphs still carry the pattern; `PCG_CathedralNave` (100/140/120/220/110) and
`PCG_BezierCathedralAxis` (100) are unambiguous, the rest need judgement.

### Size thresholds are not sufficient to detect "broken"

`SM_GlassBottle_Object1715` at 6×4×**12 uu** is a plausible 12 cm bottle; `SM_LanternGlass` at 28 uu
is a lantern. Scaling either would have produced a 12-metre bottle. Judge by **intended real-world
size**, not by a "max dimension < 30 uu" rule.

---

# 6. PPV

### The handoffs were wrong about the live state

`CLAUDE_TO_KIRO_STATE_2026-08-01.md` claimed all four levels ran outline + grade + sky. Measured:
**two had zero blendables**, `L_FallenMoon` ran the outline at **0.08** (invisible) against the raw
material instead of the Hero profile, and `L_KaleidoNave` was on a **superseded parent**. No level
had the sky. **Verify PPV state; do not trust a handoff.**

All four now carry an identical stack at priority 10: `MI_Outline_PremiumV3_Hero` +
`MI_MeluColorGrade_PortfolioHero` + `MI_StarryNight_Hero`, weight 1.0.

The second volume per level (`MoonPost` etc.) has **zero blendables but real overridden settings** —
they are base-grade layers, not duplicates. Don't delete them. `MoonPost` carries 26 overrides
against 1–2 elsewhere, so `L_FallenMoon`'s baseline differs materially from the others.

### Outline jitter — root causes identified, **not solved**

Owner confirms it is **still visible**. Three compounding causes found from measured values:

1. **`MinWidthPx = 0.6`** — sub-pixel tap radius. Neighbour taps land in the *same pixel* as centre,
   so the depth delta is decided by TSR's jitter. Now floored at 1.0 px in code.
2. **AA band collapsing to zero** — `fwidth` → 0 on a thin silhouette turns smoothstep into a hard
   step. Added a ~1 px temporal floor (`rcp(max(widthPx,1.0))`).
3. **`max()` over 8 taps amplifies noise** — the mean is stable. `InkBlurStrength` 0.28 → 0.45.

Cost 335 → 339 PS instructions. **An attempted optimisation did not pay off**: removing 8 redundant
`normalize()` calls on neighbour normals saved **zero** measured instructions — the compiler was
already folding them. Don't expect savings from that trick.

Remaining suspects for the residual jitter, untried: the outline runs *after* TSR resolve, so it
re-derives edges every frame from a jittered depth buffer that TSR has already converged — no
amount of UV compensation fixes a post-resolve recompute. Worth testing whether the effect belongs
earlier in the chain, or whether responsive-AA / velocity hints help.

### Grade expanded

`M_PP_MeluColorGrade` went from 7 lines to a colourist-ordered chain: expose → filmic shoulder →
vibrance → split-tone anchored to the MPC's `PrimaryColor` → paper highlights → rhythm → vignette
last. New dials are **`const`, not pins**, precisely because `inputs` wipes connections; all 8
original connections verified intact. Promotion to parameters is mechanical.

---

# 7. Verification discipline — the meta-lesson

**Three wrong conclusions this session came from trusting a count over a position.**

- 605 instances "spread across the level" — all stacked at the origin.
- 160 instances "healthy" — the garden had collapsed to a 20 uu ball.
- A carve that "worked" — tested while the geometry didn't overlap at all, so the result was void.

Rules that actually hold:

- `generate()` is **async** — count in a **separate call**.
- Count **level-wide**, excluding `InstancedFoliageActor` (ZenForestTest has 633k that mask everything).
- **Assert the loaded world before any save.** Generate calls landed on `ZenForestTest` by accident
  once because this was skipped.
- Prove a change *positionally*: centroid vs volume location, distance-to-spline per instance,
  Z-range per layer.
- Confirm regeneration is live before trusting a negative — change a resolution and check the count
  follows.
- Default volume scale only; a multiplier crashed the editor.
- **Never save `ZenForestTest`.**
- Don't create-and-delete probe assets mid-session — it trips an editor Ensure
  (`ObjectTools.cpp:4043`). Park them in `/Game/EnvSandbox/PCG/_Dev/`.

---

# 8. Traversal envelope (for future level design)

| Source | Value |
|---|---|
| `MelodiaSmokeCharacter.cpp` | `JumpZVelocity 620`, `GravityScale 1.6`, **`JumpMaxCount 1`** |
| `MelodiaTraversalComponent.h` | `GlideTerminalFallSpeed 240`, `MaxGlideStamina 3.5` |

→ **jump clears ≈ 122 uu** (keep step rises ≤ 100), **glide descends ≈ 840 uu** over ~2000–3000 uu.

`AMelodiaMovingPlatform` / `AMelodiaPuzzleRelayVolume` / `AMelodiaExplorationInteractionVolume`
already exist in C++ and are Blueprint-ready. **Their components are already `MOVABLE` with
`BlockAllDynamic` collision** — I predicted a mobility bug from reading the constructor and was
wrong; the CDO says otherwise. No rebuild needed.

`PCGSpawnActor` can spawn them directly, with `tags_to_add_on_actors` and per-instance property
overrides via `spawned_actor_property_override_descriptions`.

### ⚠️ Caution learned the hard way

Generating a graph with `PCGSpawnActor` + `delete_actors_before_generation` into `ZenForestTest`
left the editor **hung — not crashed**. That node has to reconcile against every actor in the level,
and ZenForestTest carries 633k foliage instances plus World Partition external actors. **Test
actor-spawning graphs in a light level first.**

---

# Assets produced

| Asset | State |
|---|---|
| `PCG_Hero_InfiniteNave` | 480 inst, 126 m walkable aisle, 23.8 m vault, 0 blockers |
| `PCG_Hero_PenroseTiling` | 1196 inst, exact P3, 5-fold verified in-engine |
| `PCG_Hero_TeaGarden` | built + saved, **placement unverified** (editor hung) |
| `PCG_Nikki_PhyllotaxisGarden` | flattened, Z ±1986 → ±10 |
| `PCG_Nikki_PhyllotaxisGarden_Walkable` | spline carve working |
| `BP_MelodiaPCGControl` | 11 knobs, compiles — **knobs inert**, see §3 |
| `pcg_graph_builder._wire_exclusion_filter` | rewritten, verified |
| Heatmap artifact | https://claude.ai/code/artifact/86244ae1-3e81-4939-b0e8-cbdc013e53e1 |
