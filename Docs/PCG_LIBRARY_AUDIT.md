# PCG Library Audit

## Purpose

`audit_pcg_portfolio.py` produces `Saved/Audit/pcg_portfolio_audit.json` with plugin status, graph inventory, level PCG volumes, and dead-system flags.

## Checks

1. **Plugins** — PCG, PCGEx enabled
2. **Inventory** — all `.uasset` under `/Game/EnvSandbox/PCG/`
3. **Universal graphs** — required paths from `pcg_portfolio_standards.py`
4. **Level volumes** — actors tagged `PCG_Volume` or labelled `PCG_*`
5. **Dead systems** — orphan `PCG_MeadowScatter`, volumes without graph, missing ground tag

## Remediation

`fix_pcg_dead_systems.py`:

- `--dry-run` (default) — report only
- `--apply` — move orphan to `_Deprecated/`, relabel volumes, log fixes

## Related audits

| Script | Output |
|--------|--------|
| `audit_pcg_universal.py` | Universal graph existence |
| `audit_melodia_pcg_reference.py` | `/Game/_PROJECT/PCG/**` inventory |
| `probe_pcgex_nodes.py` | PCGEx Settings class probe |

## Clean criteria

`clean: true` when:

- Required universal graphs exist
- No unresolved dead-system issues
- PCG plugin enabled

## Run

```text
# In editor Python or headless session
import audit_pcg_portfolio
audit_pcg_portfolio._audit_in_ue()
```

Or headless via `run_editor_session.py` (includes pcg portfolio audit step).
