# jcode Swarm — Recipe acceptance log

Workstation validation (Recipes A/B) runs on the Windows UE box after:

```powershell
.\deploy\start_jcode_swarm.ps1
```

Paste `.jcode/coordinator-bootstrap.md` into the coordinator session.

## Recipe A (docs)

Expected artifact: `Docs/Reports/jcode_swarm_recipe_a.md` (created by SQA worker).

| Check | Pass? | Notes |
|---|---|---|
| WEB + SQA spawned, no path overlap | | |
| `jcode_swarm_recipe_a.md` written | | |
| No Content/Plugin binary edits | | |
| Coordinator commit or clean no-op | | |

## Recipe B (audits)

Expected: `Docs/Reports/jcode_swarm_recipe_b_mpa.md`, `Docs/Reports/jcode_swarm_recipe_b_ppa.md`.

| Check | Pass? | Notes |
|---|---|---|
| MPA + PPA read-only | | |
| No master regenerate / no `.uasset` writes | | |
| Completion reports have outcome/paths/validation/blockers | | |

## Sign-off

- Date:
- Operator:
- jcode version (`jcode --version`):
- Monolith MCP tested (Y/N):
