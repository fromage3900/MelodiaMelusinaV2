# Realtime Converged World-Compiler Pipeline

**Status:** CANONICAL WORLD-COMPILER PIPELINE CONTRACT — 2026-09-19  
**First vertical:** use case **B** — Castle / Zen shrine surreal plan → HISM with `ROLE_UE_HINTS`.  
**Evidence:** SOURCE-TOOL PROVEN (schema + offline B checklist). **Not LIVE PROVEN.**

This is not a sixth gameplay authority and not a second importer. The existing stack stays:

```text
Blender surreal_arch  (export.py + ROLE_UE_HINTS)
  -> surreal_arch_world_v1  (Config/world_schema.json)
  -> import_world_manifest.py --apply
  -> HISM / explicit StaticMeshActors
```

The realtime conductor only watches that path and diffs dirty `(role, lib)` groups. Use cases: [`USE_CASES_WORLD_COMPILER_2026-09.md`](USE_CASES_WORLD_COMPILER_2026-09.md). World ownership: [`Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`](../WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md). TD contract: [`deploy/SURREAL_WORLD_MANIFEST.md`](../../deploy/SURREAL_WORLD_MANIFEST.md). Status: [`CURRENT_STATE.md`](../../CURRENT_STATE.md).

---

## 1. Use case B — entry points (do not replace)

| Piece | Path | Job |
|---|---|---|
| Produce | `deploy/surreal_world/export.py` | `{WorldRoot}.world.json`, `hism_groups`, `ue_material_hint` |
| Hint SSOT | `deploy/surreal_world/role_ue_hints.py` | Default `sacred` → `MI_Zen_Karesansui`; `ZEN_SHRINE` overrides gate/sacred to Torii / Honden |
| Schema | `Config/world_schema.json` | `format`: `surreal_arch_world_v1` |
| Consume | `Content/Python/import_world_manifest.py` | **The** importer. `--apply` in the editor |
| Conduct | `deploy/realtime_world_conductor.py` | Default: `deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json` |
| Orchestrate | `deploy/monolith_orchestrator.py` | Five agents unchanged; `realtime_world` routes to **integration** |
| Slow pulse | `deploy/start_world_loop.ps1` | Compose, do not replace |

Authored instance truth: `import_world_manifest`. Runtime census: `capture_scene_metadata`. Combat/save/HUD: not this pipeline.

No live `SurrealPlan_*.world.json` from Blender was in git. In-repo stand-ins:

- `deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json` (`WESTERN_CASTLE`) — conductor default
- `deploy/fixtures/SurrealPlan_ZenShrine_WorldRoot.world.json` (`ZEN_SHRINE`)

---

## 2. B checklist

Offline (conductor `--once` writes this into `Saved/Audit/realtime_world_conductor_status.json` → `use_case_b`):

1. `format == surreal_arch_world_v1`
2. `hism_groups` unique on `(role, lib)`
3. `ue_material_hint == material_hint(style, role)` — Castle `sacred` is `MI_Zen_Karesansui`; Zen `sacred`/`gate` use the `ZEN_SHRINE` overrides
4. `instance_count == len(instances) == sum(group instance_count)`

Live (UE 5.8 session, still owed):

```text
py Content/Python/import_world_manifest.py --manifest deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json --apply
```

One HISM (or explicit SMA) per `(role, lib)`; materials load; counts match. Then the same command on the Zen shrine fixture.

---

## 3. Stage graph (B is the first slice)

```text
Author (Blender surreal_arch, WESTERN_CASTLE or ZEN_SHRINE)
  -> Compile (export.py → surreal_arch_world_v1)
  -> Dress (ROLE_UE_HINTS / ZEN_SHRINE overrides — no new master)
  -> Place (import_world_manifest — HISM groups)
```

LookDev / Houdini / PCGEx / World Partition remain later slices (use cases A, C–F). They are not this vertical.

Monolith keeps five agents. The conductor is not a sixth agent. Dirty-group apply still calls `import_world_manifest.import_manifest` — never a second importer, never `probe_world_pipeline.py` from CI.

---

## 4. Commands

```text
python deploy/realtime_world_conductor.py --once
python deploy/realtime_world_conductor.py --once --manifest deploy/fixtures/SurrealPlan_ZenShrine_WorldRoot.world.json
python deploy/test_realtime_world_conductor.py
deploy/start_realtime_world_loop.ps1
python deploy/monolith_orchestrator.py --workflow realtime_world
```

`--once` with no `--manifest` uses the Castle fixture.

---

## 5. Scaffold vs live UE

**Scaffolded:** B checklist offline, Castle/Zen fixtures, shared `role_ue_hints.py`, conductor default path.

**Still needs Windows UE 5.8:** `import_world_manifest --apply` of Castle then Zen shrine. Until that receipt exists, call this source-tool proven and stop.
