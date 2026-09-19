# World-compiler use cases — 2026-09

**First vertical: B.** Castle or Zen shrine surreal plan → HISM with `ROLE_UE_HINTS`.
Architecture: [`REALTIME_CONVERGED_PIPELINE.md`](REALTIME_CONVERGED_PIPELINE.md).
Status: [`CURRENT_STATE.md`](../../CURRENT_STATE.md) only. This scaffold is **not LIVE PROVEN**.

---

## B — first live proof (do this)

Castle (`WESTERN_CASTLE` / `SurrealPlan_Castle`) or Zen shrine (`ZEN_SHRINE` / `SurrealPlan_ZenShrine`) exported from Melodia Studio, imported through the existing WIA path. No parallel importer.

### Entry points

| Step | File | Job |
|---|---|---|
| Produce | [`deploy/surreal_world/export.py`](../../deploy/surreal_world/export.py) | Writes `{WorldRoot}.world.json`, `hism_groups`, `ue_material_hint` |
| Hint SSOT | [`deploy/surreal_world/role_ue_hints.py`](../../deploy/surreal_world/role_ue_hints.py) | `ROLE_UE_HINTS` + `STYLE_ROLE_OVERRIDES` (bpy-free; export and conductor share it) |
| Schema | [`Config/world_schema.json`](../../Config/world_schema.json) | `format` must be `surreal_arch_world_v1` |
| Consume | [`Content/Python/import_world_manifest.py`](../../Content/Python/import_world_manifest.py) | Validate + `--apply` into the open level |
| Conduct | [`deploy/realtime_world_conductor.py`](../../deploy/realtime_world_conductor.py) | Default manifest is the Castle fixture; diffs dirty HISM groups only |

### `ROLE_UE_HINTS` (from `role_ue_hints.py`, not a second table)

Default sacred slot is **`MI_Zen_Karesansui`**. Gate default is `MI_Show_ContactRimHero`.

`ZEN_SHRINE` style overrides at export time:

| Role | Default `ROLE_UE_HINTS` | `ZEN_SHRINE` override |
|---|---|---|
| `sacred` | `/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_Karesansui` | `MI_Zen_HondenSanctum` |
| `gate` | `/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Show_ContactRimHero` | `MI_Zen_ToriiVermillion` |
| `large` | `MI_Show_StoneCliff` | `MI_Zen_MossGarden` |
| `monument` | `MI_Show_StoneCliff` | `MI_Zen_SakuraDrift` |

`Config/material_hints.json` is a copy with a `Stylistic` path typo. **Producer SSOT is `export.py` / `role_ue_hints.py` (`Stylized`).**

### In-repo manifests (no live Blender `SurrealPlan_*.world.json` was in git)

| File | Style | Plan |
|---|---|---|
| [`deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json`](../../deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json) | `WESTERN_CASTLE` | `SurrealPlan_Castle` — conductor default |
| [`deploy/fixtures/SurrealPlan_ZenShrine_WorldRoot.world.json`](../../deploy/fixtures/SurrealPlan_ZenShrine_WorldRoot.world.json) | `ZEN_SHRINE` | `SurrealPlan_ZenShrine` |

### Checklist (must all pass)

1. **Format** `format == "surreal_arch_world_v1"` (`Config/world_schema.json`).
2. **HISM groups** keyed by `(role, lib)` — one group per pair, matching `export.build_hism_groups`.
3. **Materials resolve** — every instance `ue_material_hint == material_hint(style, role)` (Castle sacred → `MI_Zen_Karesansui`; Zen sacred/gate → Honden / Torii overrides).
4. **Counts match** — `instance_count == len(instances) == sum(hism_groups[].instance_count)`.
5. **Live (UE session, still owed)** — `py Content/Python/import_world_manifest.py --manifest deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json --apply` on a running editor; one HISM (or explicit SMA) per group; no second importer.

Offline gate:

```text
python deploy/realtime_world_conductor.py --once
python deploy/realtime_world_conductor.py --once --manifest deploy/fixtures/SurrealPlan_ZenShrine_WorldRoot.world.json
python deploy/test_realtime_world_conductor.py
```

Live apply (Windows UE 5.8, not this checkout):

```text
py Content/Python/import_world_manifest.py --manifest deploy/fixtures/SurrealPlan_Castle_WorldRoot.world.json --apply
```

---

## Later (not this vertical)

| ID | One line |
|---|---|
| A | Sea Above / Morning set-dress refresh without editor restart — after B’s importer path is live. |
| C | Houdini Copernicus → Nanite + existing MPC. Live HDA cook still unproven. |
| D | PCGEx scatter from `collections` / `setup_pcg_universal.py`. |
| E | Day/night/vapor lookdev packs on frozen PPV, no new geometry. |
| F | Greybox → hero mesh on the same instance `id`. |
