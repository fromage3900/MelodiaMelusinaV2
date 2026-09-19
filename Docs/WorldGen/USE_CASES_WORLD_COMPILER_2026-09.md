# World-compiler use cases — 2026-09

**First vertical: B.** Castle or Zen shrine surreal plan → HISM with `ROLE_UE_HINTS`.
Architecture: [`REALTIME_CONVERGED_PIPELINE.md`](REALTIME_CONVERGED_PIPELINE.md).
Status: [`CURRENT_STATE.md`](../../CURRENT_STATE.md) only. This scaffold is **not LIVE PROVEN**.

---

## B — first live proof (do this)

Castle (`WESTERN_CASTLE` / `SurrealPlan_Castle`) or Zen shrine (`ZEN_SHRINE` / `SurrealPlan_ZenShrine` / `SurrealPlan_ZenTemple`) exported from Melodia Studio, imported through the existing WIA path. No parallel importer.

### Entry points

| Step | File | Job |
|---|---|---|
| Produce | [`deploy/surreal_world/export.py`](../../deploy/surreal_world/export.py) | Writes `{WorldRoot}.world.json`, `hism_groups`, `ue_material_hint` |
| Hint SSOT | [`deploy/surreal_world/role_ue_hints.py`](../../deploy/surreal_world/role_ue_hints.py) | `ROLE_UE_HINTS` + `STYLE_ROLE_OVERRIDES` (bpy-free; export and conductor share it) |
| Schema | [`Config/world_schema.json`](../../Config/world_schema.json) | `format` must be `surreal_arch_world_v1` |
| Consume | [`Content/Python/import_world_manifest.py`](../../Content/Python/import_world_manifest.py) | Validate + dry-plan; `--apply` spawns **StaticMeshActors** only when `static_mesh_path` is set |
| Conduct | [`deploy/realtime_world_conductor.py`](../../deploy/realtime_world_conductor.py) | Default manifest is the Castle fixture; diffs dirty HISM groups only |

### `ROLE_UE_HINTS` (from `role_ue_hints.py`, not a second table)

Default sacred slot is **`MI_Zen_Karesansui`**. Gate default is `MI_Show_ContactRimHero`.

`MI_Show_StoneCliff` is on disk at **`/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_StoneCliff`**, not `Environment/Stylized`. `corner_tower` / `large` / `monument` all use that Showcase path.

`ZEN_SHRINE` style overrides at export time:

| Role | Default `ROLE_UE_HINTS` | `ZEN_SHRINE` override |
|---|---|---|
| `sacred` | `/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_Karesansui` | *(none — keep Karesansui until `MI_Zen_HondenSanctum` is authored)* |
| `gate` | `/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Show_ContactRimHero` | `MI_Zen_ToriiVermillion` |
| `large` | `/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_StoneCliff` | `MI_Zen_MossGarden` |
| `monument` | `/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_StoneCliff` | `MI_Zen_SakuraDrift` |
| `corner_tower` | `/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_StoneCliff` | *(none)* |

`Config/material_hints.json` is a copy. **Producer SSOT is `role_ue_hints.py`.**

### In-repo manifests (no live Blender `SurrealPlan_*.world.json` was in git)

| File | Style | Plan |
|---|---|---|
| [`deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json`](../../deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json) | `WESTERN_CASTLE` | `SurrealPlan_Castle` — conductor default |
| [`deploy/fixtures/SurrealPlan_ZenShrine_WorldRoot.world.json`](../../deploy/fixtures/SurrealPlan_ZenShrine_WorldRoot.world.json) | `ZEN_SHRINE` | `SurrealPlan_ZenShrine` |

### Proof B dry-run (local Windows checkout — not live UE, not in this git tree)

Owner-run fixture: `Saved/Audit/proof_b_zen_shrine/SurrealPlan_ZenShrine_ProofB.world.json`

| Field | Result |
|---|---|
| `style` | `ZEN_SHRINE` |
| `plan` | `SurrealPlan_ZenTemple` |
| `instances` | 8 |
| `hism_groups` | 6 |
| Schema vs `Config/world_schema.json` | **PASS** |

That is schema / grouping evidence only. It is **not** an `import_world_manifest --apply` receipt and **not** HISM spawn proof.

### Checklist (must all pass, in this order)

1. **Schema PASS** — `format == "surreal_arch_world_v1"` against [`Config/world_schema.json`](../../Config/world_schema.json).
2. **Hints resolve** — every instance `ue_material_hint == material_hint(style, role)`. StoneCliff roles hit Showcase. Zen `sacred` is `MI_Zen_Karesansui` until `MI_Zen_HondenSanctum` exists on disk. Zen `gate` is Torii.
3. **`hism_groups` by `(role, lib)`** — one group per pair, matching `export.build_hism_groups`. Counts: `instance_count == len(instances) == sum(hism_groups[].instance_count)`.
4. **Live UE apply (still owed)** — existing importer only. `--apply` currently spawns **StaticMeshActors** when `static_mesh_path` is set; it does **not** spawn `HierarchicalInstancedStaticMeshComponent` from `hism_groups`. Full B live proof therefore needs either filled `static_mesh_path` **or** an importer extension to spawn HISM from those groups. No second importer.

Offline gate:

```text
python deploy/realtime_world_conductor.py --once
python deploy/realtime_world_conductor.py --once --manifest deploy/fixtures/SurrealPlan_ZenShrine_WorldRoot.world.json
python deploy/test_realtime_world_conductor.py
```

Live apply (Windows UE 5.8, not this checkout) — SMA path only until HISM spawn is added:

```text
py Content/Python/import_world_manifest.py --manifest deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json
py Content/Python/import_world_manifest.py --manifest deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json --apply
```

Dry-run (no `--apply`) validates + plans. `--apply` without `static_mesh_path` fails per instance; it never infers a mesh from `lib`.

---

## Later (not this vertical)

| ID | One line |
|---|---|
| A | Sea Above / Morning set-dress refresh without editor restart — after B’s importer path is live. |
| C | Houdini Copernicus → Nanite + existing MPC. Live HDA cook still unproven. |
| D | PCGEx scatter from `collections` / `setup_pcg_universal.py`. |
| E | Day/night/vapor lookdev packs on frozen PPV, no new geometry. |
| F | Greybox → hero mesh on the same instance `id`. |
