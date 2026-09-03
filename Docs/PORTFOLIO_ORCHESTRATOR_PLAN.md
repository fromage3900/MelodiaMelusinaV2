# Portfolio Environment Orchestrator

Rotating **10-minute loop** that advances one specialist workstream per tick across PCG, Sakura VFX, UDS/toon lighting, storybook post-process, and UE Water simulation.

## Loop entry

```text
py Content/Python/run_portfolio_orchestrator_loop_tick.py
python Content/Python/run_portfolio_orchestrator_loop_tick.py   # headless
```

Editor menu: **LiveLink → Portfolio → Portfolio Orchestrator Tick (10m loop step)**

Full editor session with orchestrator step:

```text
py Content/Python/run_editor_session.py --orchestrator
```

## Task rotation (mod 5)

| Tick | Track | Script | Audit JSON |
|------|-------|--------|------------|
| 0 | PCG anti-cluster | `setup_pcg_greybox.py`, `audit_pcg_clustering.py` | `pcg_clustering_audit.json` |
| 1 | Sakura petal Niagara | `run_sakura_niagara_plan.py`, `audit_sakura_petal_niagara.py` | `sakura_petal_niagara.json` |
| 2 | UDS ↔ toon | `setup_time_of_day_mpc.py --apply` | `uds_toon_integration.json` |
| 3 | Storybook outline | `setup_audio_outline.py`, `setup_storybook_outline.py` | `storybook_outline_audit.json` |
| 4 | UE Water sim | `setup_ue_water_simulation.py` | `ue_water_sim_audit.json` |

State: `Saved/Audit/portfolio_orchestrator_loop_state.json`  
Report: `Saved/Audit/portfolio_orchestrator_loop.json`

## PowerShell loop sentinel

```powershell
while ($true) {
  Start-Sleep -Seconds 600
  Write-Output 'AGENT_LOOP_TICK_PORTFOLIO_ENV {"prompt":"Run portfolio orchestrator tick: advance next workstream (PCG/VFX/UDS/PP/Water), fix failures from last audit JSON, update loop state."}'
}
```

## PIE verification gates (editor only)

| Track | Pass criteria |
|-------|---------------|
| PCG | ISM within bands; no piles; path/pond exclusion visible |
| VFX | Petals fall; ground pile; gust on MPC pulse |
| UDS+Toon | Time scrub changes rim/fill; wetness on stone with weather |
| Outline | Ink edges; vines along silhouettes |
| Water | Pond ripples; no z-fight with hidden KoiPond plane |

## Key modules

- [`portfolio_scene_integration.py`](../Content/Python/portfolio_scene_integration.py) — UDS actors, PP stack
- [`pcg_portfolio_standards.py`](../Content/Python/pcg_portfolio_standards.py) — anti-cluster presets
- [`pcg_graph_builder.py`](../Content/Python/pcg_graph_builder.py) — surface sampler, prune, exclusion

Headless `-nullrhi` runs are **structural only**; ISM counts, Niagara motion, post-process, and water sim require an open editor / PIE.
