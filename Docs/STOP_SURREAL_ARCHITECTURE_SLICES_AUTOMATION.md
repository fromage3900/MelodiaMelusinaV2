# STOP — surreal-architecture-slices Cursor Automation

**Status: MUST DISABLE ON CURSOR.COM** (local stop alone cannot kill cloud schedule)

| Field | Value |
|-------|--------|
| Name | surreal-architecture-slices |
| Automation ID | `0e666647-74b2-11f1-a8a0-cafc5ef88358` |
| Direct URL | https://cursor.com/automations/0e666647-74b2-11f1-a8a0-cafc5ef88358 |
| Agents list | https://cursor.com/agents |
| Cadence | ~15 minutes (PRs #64–#78 identical Art Deco lobby rematerialize) |

## What was done locally ($(Get-Date -Format o))

- Ran `deploy/stop_surreal_loop.ps1`, `stop_surreal_tierb_loop.ps1`, `stop_world_loop.ps1`, `stop_cursor_agent_loop.ps1`
- Wrote stop sentinels under `deploy/` and `Saved/Audit/SURREAL_ARCHITECTURE_SLICES_AUTOMATION_STOP`
- Closed open duplicate PRs from `cursor/surreal-architecture-slices-*` branches

## What YOU must do (cloud)

1. Open the automation URL above while signed into Cursor.
2. **Pause / Disable / Archive** the automation (not just one run).
3. Confirm no new PR appears for 20+ minutes.

Agents cannot sign into cursor.com for you.
