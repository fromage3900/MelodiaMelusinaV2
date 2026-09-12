# jcode Recipe B — MPA material pipeline audit (read-only)

**Outcome:** done  
**Role:** MPA (light-swarm stand-in)  
**Date:** 2026-08-11  
**Validation:** path existence + header/entrypoint read of material pipeline scripts  
**Blockers:** none. **No** master regenerate, **no** `.uasset` writes.

## Entrypoints

| Path | Size | Notes |
|------|------|-------|
| `Content/Python/setup_master_universal.py` | ~136KB | Builds `M_Master_Toon_Universal`. Docstring warns to run via `run_force_universal.py` wrapper, not direct. Still references legacy `C:/EnvironmentPortfolio/...` paths in examples. |
| `Content/Python/material_family_manifest_full.py` | ~12KB | Disk-only family manifests for portfolio packaging; safe without Unreal imports. Writes under `Saved/Portfolio/Materials/`. |
| `Content/Python/material_family_manifest.py` | ~10KB | Lighter sibling of full manifest. |
| Related masters | — | `setup_master_toon.py`, `setup_master_water.py`, `setup_master_water_v7.py` present |

## Findings

1. **Single-editor rule still applies:** swarm must not parallelize live master regenerates (`setup_master_universal` / force wrappers).
2. **Path drift:** universal master docstring still shows `C:/EnvironmentPortfolio` examples; V2 docs refresh moved authority to `C:\EnvironmentPortfolio` — docs/examples should be swept in a later Green task (out of Recipe B scope).
3. **Safe swarm work:** prefer `material_family_manifest_full.py` audits/manifest diffs and reports under `Docs/Reports/` over any `.uasset` master rewrite.
4. **Master asset targets (from full manifest):**  
   - `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`  
   - Landscape height-blend master  
   - `M_Water_Master_Grand_v6`

## Paths touched

- `Docs/Reports/jcode_swarm_recipe_b_mpa.md` (this file only)
