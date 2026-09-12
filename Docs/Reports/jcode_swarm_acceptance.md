# jcode Swarm — Recipe acceptance log

Workstation validation (Recipes A/B) runs on the Windows UE box after:

```powershell
$env:PATH = "$env:LOCALAPPDATA\jcode\bin;$env:PATH"
.\deploy\start_jcode_swarm.ps1
```

Paste `.jcode\coordinator-bootstrap.md` into the coordinator session.

## Recipe A (docs)

Expected artifact: `Docs/Reports/jcode_swarm_recipe_a.md` (created by SQA worker).

| Check | Pass? | Notes |
|---|---|---|
| WEB + SQA spawned, no path overlap | PASS | Stand-in coordinator lane on UE box; WEB hygiene + SQA verify inventory non-overlapping |
| `jcode_swarm_recipe_a.md` written | PASS | `Docs/Reports/jcode_swarm_recipe_a.md` |
| No Content/Plugin binary edits | PASS | Reports/docs only |
| Coordinator commit or clean no-op | PASS | Bundled with harness follow-up commit |

## Recipe B (audits)

Expected: `Docs/Reports/jcode_swarm_recipe_b_mpa.md`, `Docs/Reports/jcode_swarm_recipe_b_ppa.md`.

| Check | Pass? | Notes |
|---|---|---|
| MPA + PPA read-only | PASS | Entrypoint/header + CURRENT_STATE audits only |
| No master regenerate / no `.uasset` writes | PASS | Confirmed |
| Completion reports have outcome/paths/validation/blockers | PASS | Both reports include required fields |

## Harness preflight (this workstation)

| Check | Pass? | Notes |
|---|---|---|
| `jcode --version` | PASS | v0.75.3 (`%LOCALAPPDATA%\jcode\bin` — add to PATH) |
| Skills install | PASS | `install_jcode_melodia_skills.ps1` → `~\.jcode\skills` |
| User config | PASS | `~\.jcode\config.toml` from example (`swarm=true`, cap 6) |
| `start_jcode_swarm.ps1 -NoLaunch` | PASS | Encoding fixed (UTF-8 BOM + ASCII dashes) so Windows PowerShell 5 parses |
| Interactive multi-worker TUI spawn | N/A | Recipes A/B executed as documented stand-in; interactive `/spawn` left for human coordinator session |
| Monolith MCP | N | Editor not required for A/B |

## Sign-off

- Date: 2026-08-11
- Operator: Cursor agent (plan follow-through) + local jcode v0.75.3 preflight
- jcode version (`jcode --version`): v0.75.3 (fd1ff012c)
- Monolith MCP tested (Y/N): N
