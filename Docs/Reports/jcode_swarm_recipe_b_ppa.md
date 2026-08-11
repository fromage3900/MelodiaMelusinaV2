# jcode Recipe B — PPA PCG / spline blockers (read-only)

**Outcome:** done  
**Role:** PPA (light-swarm stand-in)  
**Date:** 2026-08-11  
**Validation:** read `CURRENT_STATE.md` PCG/spline sections; searched for `.junie/plans/pcg-universal-expansion.md` (missing)  
**Blockers:** plan file `.junie/plans/pcg-universal-expansion.md` not present in this checkout — used CURRENT_STATE as authority.

## Summary from CURRENT_STATE.md

### Working patterns

- **`BP_PathSplineProvider` direct-host spline** proven on `PCG_WallDetail` and **`CorniceEx`** (0 → 40 instances).
- Escher room set in `/Game/EnvSandbox/PCG/Styles/Escher/` verified via spawn/generate/count.
- Cathedral grammar rebuild uses explicit per-node clear (shared `load_or_create_graph(force=True)` / `remove_nodes()` is a no-op on this engine build).

### Active blockers

| Item | Status |
|------|--------|
| `BalconyEx` | 0 instances — terminal `PCGSubgraphSettings.subgraph` C++-protected / unreadable via Python |
| `NaveVaultEx` | 0 instances after spline-host fix — suspect `PCGExPathHatchSettings` config, not spline input |
| Baroque `*Ex` with `PCGExCreateShapes` | **Do not batch-generate** — confirmed hard crash on `AtriumEx` / `ColonnadeEx` / `RotundaEx` |
| `FacadeEx` | No crash but non-functional (0 instances) with CreateShapes fed from surface sampler |
| Orphaned/unresolvable assets | `PCG_Sakura_PetalDrift`, `PCG_RockScatter` drift pattern |
| Placeholder scaffolds | `PCG_FractalButtress_BS` / `PCG_M1_GrammarNave_BS` are not real recursive systems |

### Swarm-safe next slices (not executed here)

- Docs-only maps of safe vs crash `*Ex` graphs
- One-at-a-time generate protocol notes (already in CURRENT_STATE)
- Avoid any live `.uasset` PCG graph edits in swarm v1 without single Integration owner

## Paths touched

- `Docs/Reports/jcode_swarm_recipe_b_ppa.md` (this file only)
- No `.uasset` / master regenerates
