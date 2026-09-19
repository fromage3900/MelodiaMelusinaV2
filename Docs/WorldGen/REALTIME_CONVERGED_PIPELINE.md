# Realtime Converged World-Compiler Pipeline

**Status:** CANONICAL WORLD-COMPILER PIPELINE CONTRACT — 2026-09-19  
**First vertical:** use case **B** — Castle / Zen shrine surreal plan → HISM with `ROLE_UE_HINTS`.  
**Evidence:** SOURCE-TOOL PROVEN (schema + offline B checklist). **Not LIVE PROVEN.**

This is not a sixth gameplay authority and not a second importer. The existing stack stays:

```text
Blender surreal_arch  (export.py + ROLE_UE_HINTS)
  -> surreal_arch_world_v1  (Config/world_schema.json)
  -> import_world_manifest.py --apply
  -> StaticMeshActor when static_mesh_path is set
     (HISM from hism_groups is not implemented in the importer yet)
```

The realtime conductor only watches that path and diffs dirty `(role, lib)` groups. Use cases: [`USE_CASES_WORLD_COMPILER_2026-09.md`](USE_CASES_WORLD_COMPILER_2026-09.md). World ownership: [`Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`](../WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md). TD contract: [`deploy/SURREAL_WORLD_MANIFEST.md`](../../deploy/SURREAL_WORLD_MANIFEST.md). Status: [`CURRENT_STATE.md`](../../CURRENT_STATE.md).

---

## 1. Use case B — entry points (do not replace)

| Piece | Path | Job |
|---|---|---|
| Produce | `deploy/surreal_world/export.py` | `{WorldRoot}.world.json`, `hism_groups`, `ue_material_hint` |
| Hint SSOT | `deploy/surreal_world/role_ue_hints.py` | Default `sacred` → `MI_Zen_Karesansui`; StoneCliff → `Instances/Showcase`; `ZEN_SHRINE` overrides gate/large/monument (sacred stays Karesansui until HondenSanctum is authored) |
| Schema | `Config/world_schema.json` | `format`: `surreal_arch_world_v1` |
| Consume | `Content/Python/import_world_manifest.py` | **The** importer. Validate + dry-plan; `--apply` is SMA-only today |
| Conduct | `deploy/realtime_world_conductor.py` | Default: `deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json` |
| Orchestrate | `deploy/monolith_orchestrator.py` | Five agents unchanged; `realtime_world` routes to **integration** |
| Slow pulse | `deploy/start_world_loop.ps1` | Compose, do not replace |

Authored instance truth: `import_world_manifest`. Runtime census: `capture_scene_metadata`. Combat/save/HUD: not this pipeline.

No live `SurrealPlan_*.world.json` from Blender was in git. In-repo stand-ins:

- `deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json` (`WESTERN_CASTLE`) — conductor default
- `deploy/fixtures/SurrealPlan_ZenShrine_WorldRoot.world.json` (`ZEN_SHRINE`)

Local Proof B dry-run (Windows checkout, not git, not live UE): `Saved/Audit/proof_b_zen_shrine/SurrealPlan_ZenShrine_ProofB.world.json` — `ZEN_SHRINE` / `SurrealPlan_ZenTemple`, 8 instances, 6 `hism_groups`, schema **PASS**.

---

## 2. B checklist

Offline (conductor `--once` writes this into `Saved/Audit/realtime_world_conductor_status.json` → `use_case_b`):

1. Schema PASS — `format == surreal_arch_world_v1`
2. Hints resolve — `ue_material_hint == material_hint(style, role)` (Showcase StoneCliff; Zen sacred = Karesansui)
3. `hism_groups` unique on `(role, lib)`; counts match
4. Live UE apply — still owed (see importer gap below)

### Importer gap (true HISM)

`import_world_manifest.py` validates and dry-plans. `--apply` only spawns `StaticMeshActor` when `static_mesh_path` is set. It does **not** spawn `HierarchicalInstancedStaticMeshComponent` from `hism_groups`. Full B live proof needs either filled `static_mesh_path` **or** an importer extension to spawn HISM from those groups. Schema PASS is not that proof.

Live (UE 5.8 session, still owed):

```text
py Content/Python/import_world_manifest.py --manifest deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json --apply
```

---

## 3. Stage graph (B is the first slice)

```text
Author (Blender surreal_arch, WESTERN_CASTLE or ZEN_SHRINE)
  -> Compile (export.py → surreal_arch_world_v1)
  -> Dress (ROLE_UE_HINTS / ZEN_SHRINE overrides — no new master)
  -> Place (import_world_manifest — SMA today; HISM groups authored in JSON)
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

**Scaffolded:** B checklist offline, Castle/Zen fixtures, shared `role_ue_hints.py`, conductor default path, Proof B local schema PASS.

**Still needs Windows UE 5.8:** `import_world_manifest --apply` with filled `static_mesh_path` (SMA) or a HISM-from-`hism_groups` extension. Until that receipt exists, call this source-tool proven and stop.
