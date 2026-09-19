# Realtime Converged World-Compiler Pipeline

**Status:** CANONICAL WORLD-COMPILER PIPELINE CONTRACT — 2026-09-19  
**Evidence:** SOURCE-TOOL PROVEN (schema, conductor `--once`, offline diff). **Not LIVE PROVEN.** A UE session still has to hot-reimport dirty HISM groups before anyone claims editor-restart-free streaming.

This is not a sixth gameplay authority and not a second world compiler. It is the realtime face of the existing Melodia world compiler:

```text
surreal_arch_world_v1
  -> Monolith 5-agent orchestrator
  -> import_world_manifest / setup_pcg_universal / setup_master_universal
  -> World Partition / HISM / PCGEx
  -> Melodia world systems consume
```

Current status / blockers still live only in [`CURRENT_STATE.md`](../../CURRENT_STATE.md). World-building ownership still lives in [`Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`](../WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md). The TD producer/consumer contract remains [`deploy/SURREAL_WORLD_MANIFEST.md`](../../deploy/SURREAL_WORLD_MANIFEST.md).

Use cases: [`Docs/WorldGen/USE_CASES_WORLD_COMPILER_2026-09.md`](USE_CASES_WORLD_COMPILER_2026-09.md).

---

## 1. What already owns this

Do not replace these. The realtime conductor watches them.

| Piece | Owner | Job |
|---|---|---|
| `Config/world_schema.json` | surreal_arch_world_v1 | Authored placement contract (`schema_version` 1 or 2) |
| `deploy/surreal_world/export.py` | Blender Melodia Studio | Produce `{WorldRoot}.world.json` + HISM groups + `ROLE_UE_HINTS` |
| `deploy/monolith_orchestrator.py` | 5 agents | geometry (PGA) → material (MPA) → placement (PPA) → integration (WIA) → qa (SQA) |
| `Content/Python/import_world_manifest.py` | WIA | Authored actors from the manifest. Owns **authored** instance truth |
| `Content/Python/capture_scene_metadata.py` | Portfolio census | Owns **runtime** actor/PCG/material census. Does not author placement |
| `Content/Python/setup_master_universal.py` | MPA | Canonical toon master / lookdev identity |
| `Content/Python/setup_pcg_universal.py` + PCGExtendedToolkit | PPA | Scatter graphs. Resonance Ecology remains the proven Sea Above lane |
| `deploy/start_world_loop.ps1` | World micro-loop | 10-minute slice + `run_verify.ps1 -Mode world` |
| `deploy/probe_world_pipeline.py` | Blender probe | Library/enum health inside Blender. Not CI-importable (`bpy`) |
| `Tools/world_compiler.py` | Seeded ecology compiler | Offline recipe → points/fx tables. Separate Issue #221 lane. Do not merge it into this conductor |

Field ownership (SCHEMA_ALIGNMENT_MAP pattern, kept here instead of a second status doc):

| Field family | Writer | Must not |
|---|---|---|
| `instances`, `hism_groups`, `ue_material_hint`, `static_mesh_path`, `lod_group`, `stream_priority`, `sector_id`, `seed`, `stages`, `tiles` | Producer (`export.py` / Houdini handoff) then `import_world_manifest` | `capture_scene_metadata` rewriting authored transforms |
| Runtime actor labels, PCG volume graphs, live material counts | `capture_scene_metadata` | Becoming the placement authority |
| Combat / save / quest / HUD | Phoenix, Quill, UI bridge | World-compiler involvement |

---

## 2. Stage graph

```text
LookDev
  existing PPV_NikkiDream / optical LOD / toon masters / lookdev_capture.py
    -> Author
         Blender surreal_arch  (deploy/surreal_architecture_gen.py + blender-mcp)
         Houdini Copernicus+HDA  (Tools/Houdini/copernicus/*, Plugins/HoudiniEngine)
    -> Compile
         surreal_arch_world_v1  schema_version 1 (single root)
         optional schema_version 2 fields (sector tiles, seed, stages, payload_rules)
    -> Dress
         Monolith material agent: setup_master_universal.py
         ROLE_UE_HINTS + lookdev stage packs (day / night / vapor)
    -> Place
         PCGEx + setup_pcg_universal.py
         manifest collections / scatter_kits
    -> Stream
         World Partition cells, HISM groups, stream_priority bands, payload_rules
    -> Runtime consume
         Melodia world systems already on the maps (PCG, wardrobe traversal, music-as-key)
         not a new world runtime
```

LookDev does not regenerate geometry. Stage packs swap PPV / MPC / material instances on already-placed HISM and PCG.

Houdini stays the production lane it already is: Hython/Copernicus is SOURCE-TOOL PROVEN; a custom HDA cooked inside UE is still **not** live-proven (`CURRENT_STATE.md`).

---

## 3. How Monolith expands

Keep the five agents. Add a **realtime conductor**, not a sixth agent.

```text
monolith_orchestrator.py          health + workflow routing (unchanged owners)
start_world_loop.ps1              slow verify pulse (unchanged)
realtime_world_conductor.py       watch manifest deltas, dirty HISM only
start_realtime_world_loop.ps1     starts the conductor; documents the compose
```

Workflow `realtime_world` on the orchestrator routes to the existing **integration** agent. The conductor is what decides *which* HISM groups are dirty.

Dirty-group contract:

1. Read `*.world.json` whose `format` is `surreal_arch_world_v1` (skip Resonant World / TouchDesigner lookalike files).
2. Follow optional `tiles[].manifest_path` so a `world_root` can fan out to sector files.
3. Fingerprint each HISM group `(role, lib, static_mesh_path)` over transforms + material hint + lod/stream/sector.
4. Diff against `Saved/Audit/realtime_world_conductor_receipt.json`.
5. Write a filtered dirty manifest `Saved/Audit/realtime_dirty_{world_root}.world.json`.
6. If Unreal is present and `--apply` was passed, call `import_world_manifest.import_manifest(...)`.
7. Otherwise leave a TODO hook in `Saved/Audit/realtime_world_conductor_status.json`. Never import `deploy/probe_world_pipeline.py` from CI — it needs Blender.

A full rebuild remains available: run the five-agent `build_environment` workflow. The conductor is the incremental path.

---

## 4. No-Mans-Sky-scale contract (authored data, existing streamers)

This is a **manifest contract**, not a new streaming engine. UE 5.8 World Partition, HISM, Nanite, and PCGEx already exist. The compiler’s job is to label payloads so those systems can stream them.

| Lever | Manifest field | Existing consumer |
|---|---|---|
| Seeded sector | top-level `seed`, `sector_id` | Hython/Copernicus manifests already carry seeds; Blender export may omit |
| Biome | `biome_tags` | PCG collections + Resonance Ecology tags |
| Mesh LOD | instance / group `lod_group` | UE LOD groups / optical LOD lookdev |
| Stream band | `stream_priority` integer | World Partition / HISM keep vs unload |
| Payload class | `payload_class` = `hero` / `hism` / `scatter` / `impostor` | import plan + PCG scatter vs authored hero |
| Unload rules | `payload_rules.*_m` | Distance bands in metres; WP/HLOD still do the actual unload |
| Chunking | `world_root` + `tiles[]` | One root file, many sector `*.world.json` tiles |

Suggested `stream_priority` bands (convention, not schema-enforced):

| Band | Meaning | Typical payload |
|---|---|---|
| 0 | Always loaded | Hero shrine / piano / traversal gate |
| 1 | Near | HISM architecture |
| 2 | Mid | PCGEx foliage / props from `scatter_kits` |
| 3 | Far | Impostor / Nanite vista |

v1 files omit every one of those fields and remain valid. `additionalProperties` stays `false` at the root and on instances; new keys must be added to `Config/world_schema.json` rather than smuggled.

---

## 5. Two compilers, one stack

| Compiler | Format | When to use |
|---|---|---|
| Surreal world compiler (this pipeline) | `surreal_arch_world_v1` | Authored architecture, shrine/castle HISM, set-dress refresh, greybox→hero |
| Seeded ecology compiler | `Tools/world_compiler.py` recipe bundle | Radial Chladni bands / dressing tables (Issue #221). Offline. Do not import `unreal` |

The realtime conductor watches the first. It does not compile ecology recipes and it does not become Phoenix, Quill, or a second PCG graph authority.

---

## 6. Commands

```text
python deploy/realtime_world_conductor.py --once
python deploy/realtime_world_conductor.py --once --manifest deploy/fixtures/surreal_arch_world_v2_sector.world.json
python deploy/realtime_world_conductor.py --watch --interval 5
deploy/start_realtime_world_loop.ps1
deploy/stop_realtime_world_loop.ps1

# existing, keep running when you want the slow QA pulse
deploy/start_world_loop.ps1
python deploy/monolith_orchestrator.py --once
python deploy/monolith_orchestrator.py --workflow realtime_world
```

Live apply (UE editor Python, not this cloud checkout):

```text
py Content/Python/import_world_manifest.py --manifest Saved/Audit/realtime_dirty_<WorldRoot>.world.json --apply
```

---

## 7. Scaffold vs still needs a live UE session

**Scaffolded here**

- schema_version 2 optional fields that do not break v1 readers
- conductor `--once` / `--watch`, dirty-group filter, audit status JSON
- compose scripts and use-case map

**Still needs the Windows UE 5.8 session**

- `import_world_manifest --apply` of a dirty HISM group without editor restart
- World Partition cell load/unload driven by `stream_priority`
- Houdini HDA cook inside the editor
- PCGEx graph generate from `scatter_kits` on `L_MelusinaMorning` / Sea Above
- Lookdev stage pack swap (day/night/vapor) on the frozen PPV identity

Until those receipts exist, call this source-tool proven and stop.
