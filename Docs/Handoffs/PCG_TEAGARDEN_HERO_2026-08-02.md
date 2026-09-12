# Tea Garden hero graph + traversal platforms — 2026-08-02

## Status: graph built and saved. Placement NOT verified — editor went down mid-check.

`PCG_Hero_TeaGarden` (`/Game/EnvSandbox/PCG/Styles/Sakura/`) is complete and saved: **16 nodes,
5 layers, all edges verified**. It was placed in `ZenForestTest` and generation was dispatched, but
the editor dropped before the instance count came back. **The counts below are intended, not
measured.** Re-run the verification block at the bottom first thing next session.

`ZenForestTest` was never saved, per the standing rule, so nothing is at risk either way.

## Two step-1 blockers — both resolved, one of them was my error

**`PCGSpawnActor` works.** `PCGSpawnActorSettings` exists with `template_actor_class`,
`tags_to_add_on_actors`, `delete_actors_before_generation`, and
`spawned_actor_property_override_descriptions` (per-instance property overrides). All three Melodia
exploration actors are Python-visible. Actor spawning from PCG is viable — no fallback needed.

**❌ My "moving platform mobility bug" was wrong.** I predicted `AMelodiaMovingPlatform` would fail
because its constructor never calls `SetMobility`. Checking the CDO directly:

```
Root           mobility=MOVABLE
PlatformMesh   mobility=MOVABLE  collision=BlockAllDynamic
```

Both already Movable, collision already correct. **No C++ change and no rebuild is needed.** I
inferred a defect from reading the constructor instead of measuring the CDO — the same mistake
pattern as trusting counts over positions.

## Design — every height derived from the shipping traversal code

| Source | Value |
|---|---|
| `MelodiaSmokeCharacter.cpp` | `JumpZVelocity 620`, `GravityScale 1.6`, **`JumpMaxCount 1`** |
| `MelodiaTraversalComponent.h` | `GlideTerminalFallSpeed 240`, `MaxGlideStamina 3.5` |

→ **jump clears ≈ 122 uu**, **glide descends ≈ 840 uu** over ~2000–3000 uu horizontal.

| Layer | Content | Traversal role |
|---|---|---|
| 1. Garden terrace | 7×7 grid of `SM_Greybox_TeaHouse` / `SM_SM_TeaHouse_001` / `_002`, spline-carved at 900 uu | walkable ground |
| 2. Pagoda | 3 × `SM_SurrealRoof_PAGODA` tiers at **550 uu** rise, top at 1500; `SM_Greybox_Pole` mast | summit — glide launch |
| 3. Deck spiral | 14 × `SM_Greybox_BuildingBlock_C` at **90 uu** rise → summit 1230 | **jumpable**: 90 < 122, and no double jump exists |
| 4. Platforms | 4 × `AMelodiaMovingPlatform`, ring R900 at Z1230 | 1230 + 300 default lift = **1530**, closing the gap to the 1500 pagoda top |
| 5. Gates | 4 × `SM_Greybox_Torii` flanking the approach | framing |

The numbers interlock deliberately: the deck spiral tops out 270 uu below the pagoda, which is more
than a jump (122) — so the platforms are *required*, not decorative. From the 1500 uu summit a glide
spends its full 840 uu of controlled descent and lands out in the garden.

Platforms are tagged `PCG_Platform` + `Melodia_Traversal`, with `delete_actors_before_generation`
on so regeneration does not accumulate duplicates.

## ⚠️ Controller knobs — still inert, and now I know exactly why

The plan called for binding `WalkWidth` to the carve. **It cannot be done through the override pin.**
`PCGAttributeFiltering` exposes only two overridable pins:

```
In · Filter · Execution Dependency · Overrides · Operator · TargetAttribute
```

**There is no threshold pin.** The threshold lives in the `attribute_types` struct
(`double_value`), which is not marked overridable, so no amount of attribute renaming can reach it.
My planned fix — swapping in `PCGGetPropertyFromObjectPath` for its `output_attribute_name` — would
not have helped either, and that node selects by explicit object path rather than by tag, so it
cannot even find the controller.

Two real options for next session:

1. **Drive the sampler instead of the filter.** `PCGExSampleNearestSpline.max_range` is a PCGEx
   shorthand selector that accepts an *attribute* rather than a constant. Set
   `sample_method = WITHIN_RANGE`, drive `max_range` from a per-point attribute, and filter on
   `bSamplingSuccess`. Requires broadcasting the controller value onto every point first.
2. **Name the BP variables after the target PCG properties** (`CellSize` as a Vector, etc.) so the
   emitted attribute name matches the override target directly. Simplest thing that works, at the
   cost of PCG-internal names leaking into the designer-facing controller.

Corridor width is currently a fixed 900 uu in the graph. Everything else about the graph is live.

## Verification to run first next session

```python
# 1. counts + Z bands per mesh (CZ = -2100 volume origin)
# 2. platform actors:  [a for a in actors if 'PCG_Platform' in a.tags]  -> expect 4 at Z 1230
# 3. walkability: no instance within 900 uu of the spline polyline (positional, not count)
# 4. collision: line-trace down onto a deck and a teahouse; a miss means the player falls through
# 5. traversal: assert deck rises == 90, pagoda tier rises == 550, platform lift == 300
```

Collision is the one genuinely unknown risk: PCG `StaticMeshSpawner` inherits collision from the
mesh asset, and the greybox kit has not been checked for simple collision. Geometry the player falls
through will not show up in any instance count — only a trace will find it.

## Also still open

- Outline jitter — owner confirmed still visible; ongoing core-look polish, out of scope here.
- 15 graphs carrying compensating scale (`PCG_CathedralNave`, `PCG_BezierCathedralAxis` unambiguous).
- 6 safe mesh repairs pending, 3 blocked on `L_MelusinaMorning` / `L_SakuraPath` approval.
- `PCGVolumeSampler` emits zero project-wide — 40 graphs.
