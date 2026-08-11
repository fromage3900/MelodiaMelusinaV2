# Melodia PCG Salvage Map

Reference content lives at `/Game/_PROJECT/PCG/` (~50 graphs, 9 collections, 28 test levels). EnvSandbox does not binary-port these; we salvage patterns via Python rebuild and thin wrappers.

## Tier A — Rebuild in EnvSandbox (priority)

| Melodia asset | EnvSandbox target | Notes |
|---------------|-------------------|-------|
| Ground scatter patterns | `PCG_FoliageDensity` | Volume/surface sampler + density filter |
| Rock scatter | `PCG_RockScatter` | Transform + spawner chain |
| Exclusion / falloff | `PCG_ExclusionFalloff` | PCGEx when available; passthrough stub today |

## Tier B — Collection references

| Melodia | EnvSandbox |
|---------|------------|
| Scatter mesh collections | `SMC_Portfolio_ScatterKit`, `SMC_Greybox_ScatterKit` |
| Foliage MI presets | Sakura / landscape instances |

## Tier C — Style wrappers

| Melodia biome graphs | EnvSandbox wrapper |
|---------------------|-------------------|
| Sakura / meadow ground | `PCG_Sakura_GroundCover` → calls universal build + showcase preset |

## Tier D — Level-specific (defer)

| Melodia | Action |
|---------|--------|
| `L_PCGTest_*` levels | Reference only; do not migrate |
| Baroque columns / walls | `setup_pcg_baroque.py` stub → `PCGCol_Baroque_*` paths |

## Tier E — Deprecate / do not port

| Asset | Action |
|-------|--------|
| `PCG_MeadowScatter` (EnvSandbox orphan) | Move to `_Deprecated/` via `organize_pcg_library.py` |
| Duplicate test graphs | Ignore |

## Audit script

`audit_melodia_pcg_reference.py` scans `/Game/_PROJECT/PCG/**` and writes `Saved/Audit/melodia_pcg_reference.json` with graph names, collection paths, and tier hints from `pcg_portfolio_standards.MELODIA_TIER_HINTS`.

## PCGEx probe

`probe_pcgex_nodes.py` lists available PCGEx Settings classes so exclusion and advanced nodes can be wired without guessing API names.
