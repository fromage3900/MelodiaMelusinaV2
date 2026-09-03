# EnvSandbox Universal PCG Library — Portfolio Plan

## Goal

One reusable PCG stack under `/Game/EnvSandbox/PCG/` that powers greybox, template, Sakura, and future biomes. Sakura is a thin style wrapper; universal graphs own sampling, density, and spawn logic.

## Architecture

```
/Game/EnvSandbox/PCG/
  Graphs/Universal/     PCG_FoliageDensity, PCG_RockScatter, PCG_ExclusionFalloff, PCG_WallDetail
  Graphs/Style/         PCG_Sakura_GroundCover (wrapper)
  Collections/          SMC_Portfolio_ScatterKit, SMC_Greybox_ScatterKit
  _Deprecated/          PCG_MeadowScatter (orphan)
```

## Greybox presets

| Preset    | Voxel (cm) | Density | ISM band   | Use case              |
|-----------|------------|---------|------------|-----------------------|
| minimal   | 120        | 0.35    | 50–800     | L_Template, fast iter |
| standard  | 80         | 0.55    | 200–2000   | blockout levels       |
| showcase  | 50         | 0.75    | 500–5000   | Sakura, portfolio     |

Apply via `setup_pcg_greybox.apply_greybox_pcg(level, preset)`.

## Run order (editor / headless)

1. `audit_melodia_pcg_reference.py` — Melodia salvage inventory
2. `organize_pcg_library.py` — folder tree, deprecate orphan meadow graph
3. `setup_pcg_universal.py` — build universal graphs
4. `setup_pcg_greybox.py` / `setup_pcg_template.py` / `setup_pcg_sakura.py` — level wiring
5. `audit_pcg_portfolio.py` — plugins, inventory, dead systems
6. `fix_pcg_dead_systems.py --apply` — remediation
7. `run_specialist_pcg_loop_tick.py` — rotating maintenance

## Editor menus

`init_unreal.py` adds Portfolio entries:

- **Run Universal PCG Build** — `setup_pcg_universal.build_all`
- **Apply Greybox PCG (Template minimal)** — `setup_pcg_greybox.apply_greybox_pcg`
- **Audit PCG Portfolio** — `audit_pcg_portfolio._audit_in_ue`
- **Run Sakura PCG (showcase wrapper)** — `setup_pcg_sakura.build_all`

## Standards module

`Content/Python/pcg_portfolio_standards.py` — canonical paths, tags (`PCG_Ground`, `PCG_Volume`), ISM bands, preset tables.

## Validation

`pcg_validate_helpers.py` — generate-wait, ISM count, bounds checks. Sakura helpers re-export this module.

## Phase 3 (advanced)

- `PCG_WallDetail` — spline-tagged wall scatter (stub)
- `setup_pcg_baroque.py` — Melodia baroque collection references
- PCGEx exclusion falloff — expand when `probe_pcgex_nodes.py` confirms node classes

## Audits

Written to `Saved/Audit/`:

- `pcg_portfolio_audit.json`
- `pcg_universal_build.json`
- `melodia_pcg_reference.json`
- `pcgex_node_probe.json`
