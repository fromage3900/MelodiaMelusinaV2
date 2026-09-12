# PCG render polish + universal control — 2026-08-02

Written as the closing PCG pass before returning to lookdev / outline PPV work.

## Render polish — what actually matters, measured

I checked the assumptions rather than listing generic advice. Two of them were wrong.

### ❌ "PCG is excluded from the outline" — NOT TRUE

The outline (`M_PP_StorybookOutline_Premium_Candidate`) does depend on custom stencil via
`MF_StencilDepthAlpha` → the HLSL node's `StencilAlpha` input. And every PCG spawner descriptor
defaults `render_custom_depth = False`.

But measuring `L_FallenMoon`: **nothing writes custom depth — not PCG, not hand-placed meshes.**

| Component kind | render_custom_depth | count |
|---|---|---:|
| `InstancedStaticMeshComponent` (PCG) | False | 19 |
| `StaticMeshComponent` (hand-placed) | False | 42 |

So the stencil channel is a **dormant hook**, not a PCG-specific gap. The outline currently derives
edges from depth + normal (`DepthWeight` / `NormalWeight`), and PCG geometry participates in those
exactly like everything else. **PCG content is already outlined.** No action needed, and I did not
enable custom depth — turning it on for 1900 instances to feed a feature nothing consumes would be
pure cost.

**The opportunity, for the lookdev pass:** the stencil hook is free real estate. Setting
`render_custom_depth = True` + a `custom_depth_stencil_value` per category on PCG spawners would let
the outline ink architecture differently from ornament, or exclude distant scatter from the ink
entirely. That is a lookdev decision, so it is exposed as a knob (below) rather than baked in.

### ❌ "Enable Nanite on the PCG meshes" — ALREADY DONE

| Mesh | verts | Nanite |
|---|---:|---|
| `SM_column_02` | 814 | ✅ |
| `SM_Greybox_Star` | 517 | ✅ |
| `SM_Greybox_Pole` | 185 | ✅ |
| `SM_Greybox_Rock_A` | 176 | ✅ |

All hero meshes are Nanite-enabled and 176–814 verts. Nothing to win here.

### ✅ The real lever: cull distances are all zero

Every PCG descriptor ships `instance_start_cull_distance = 0` and `instance_end_cull_distance = 0`,
which means **never cull**. With 1898 instances in `L_FallenMoon` and the Penrose tiling alone at
1196, per-instance culling is the one genuine cost saving available.

It is deliberately a *knob*, not a default: hero renders want zero culling, gameplay wants culling.
Same for `world_position_offset_disable_distance` and `affect_distance_field_lighting` (currently
`True` on 1196 decorative gems, which is waste in gameplay and irrelevant in a still).

## `BP_MelodiaPCGControl` — built

`/Game/EnvSandbox/PCG/Universal/BP_MelodiaPCGControl`, compiles clean, 11 instance-editable knobs:

| Category | Knobs |
|---|---|
| Shape | `Depth`, `Density` |
| Walkability | `WalkWidth` |
| Array | `ArrayCount`, `ArraySpacing` |
| Curve | `ResampleSpacing` |
| Transform | `ScaleMin`, `ScaleMax` |
| **Render** | `CullDistance`, `StencilValue`, `WriteCustomDepth` |

Tag an instance `PCG_Control` and graphs read it live.

## `PCG_Melodia_Universal_Scatter` — built, partially wired

`/Game/EnvSandbox/PCG/Universal/PCG_Melodia_Universal_Scatter`

```
CreatePointsGrid ─> [spline carve] ─> TransformPoints ─> StaticMeshSpawner
   ▲ Overrides                ▲ Overrides
ArraySpacing knob        WalkWidth knob
```

The carve reuses the verified `pcg_graph_builder._wire_exclusion_filter()`. Knob nodes are
`PCGDataFromActor` in `GET_DATA_FROM_PROPERTY` mode, `ALL_WORLD_ACTORS` + `ByTag "PCG_Control"`.

### ⚠️ Unfinished — the override name-matching problem

Two things were learned the hard way and the second is not yet solved:

1. **Typed property pins reject generic data.** Connecting a knob to `CellSize` silently fails —
   `add_edge` returns without error and no edge appears. Connections must go to the node's
   **`Overrides`** pin. Both knobs are now correctly on `Overrides` pins.
2. **Overrides match by attribute name.** A knob whose property is `ArraySpacing` emits an attribute
   called `ArraySpacing`, but the target property is `CellSize` — **the names do not match, so the
   override will not apply.** The graph is structurally correct and will generate, but the knobs do
   not yet drive anything.

**The fix** (next session, small): insert a rename between knob and target so the attribute name
equals the target property name — either `PCGGetPropertyFromObjectPath` (it has an
`output_attribute_name`, unlike `PCGDataFromActor`), or a `PCGCopyAttributes`/rename node. Then
re-verify by changing a knob and confirming the output changes.

Do not assume it works until that positional check passes — the same "structure looks right,
behaviour is absent" trap cost three wrong conclusions this session.

## Mesh repair — 18 of 29 done

See `MESH_SCALE_REPAIR_2026-08-02.md`. Headline: the feared blast radius largely does not exist,
because the referencing actors are PCG volumes, not hand placements. Remaining: 6 safe ones in
`L_WP_BaroqueGrotto` / `DistanceFieldBlendLab`, and 3 blocked on owner approval
(`L_MelusinaMorning`, `L_SakuraPath`).

## Handing back to lookdev — the three things worth knowing

1. **PCG geometry is already outlined** via depth+normal. Nothing to fix before capture.
2. **The stencil channel is unused across the whole project.** If the outline pass wants per-category
   ink, `WriteCustomDepth` + `StencilValue` on the controller is the entry point.
3. **Nothing culls.** For stills that is correct; before any gameplay perf pass, set `CullDistance`.
