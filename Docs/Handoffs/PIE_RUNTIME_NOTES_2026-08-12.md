# PIE / Runtime notes — 2026-08-12

Owner + cloud reconciliation. **Owner statements about the rig are ground truth.**
This file is the living board for the P0 play loop until `runtime` has a ledger row.

## Gate ledger (truth)

| Gate | Status | Notes |
|------|--------|-------|
| `static_gates` | **PASS** (`0e34eaed`) | Material drifts accepted; sweeps scoped |
| `runtime` | **FAIL** (honest) / OPEN for re-cert | Needs real Q/W/O/P via `BP_BattleUI::OnKeyDown` + assertion JSON + `record_gate.py runtime` |
| `save_load` | OPEN | Never closed |
| `repeat_consume` | OPEN | |
| `package_launch` | OPEN | |

Probe-only / Python-injected rhythm hits are **not** play evidence.

## Owner progress (2026-08-12) — verify owed

| Item | Owner status | Verify in PIE |
|------|--------------|---------------|
| **Quill / WillScript** (authored narrative) | Updated; **should work at runtime** | Morning intro → battle notify → typed result → resume once |
| **P0 battles on dreamstate path** | Still **do not work properly** | Confirm route is Morning → **KaleidoNave** (Dreamstate merged out; wake portal dest = KaleidoNave) |
| **Collider-name level battles** | Still **broken / working through** | Encounter tag `melodia_smoke_encounter` + `BP_BattleController` in level + stock `StartBattle` contract |
| **Rhythm highway** | Ownership fix in source; **not PIE-verified** | Stock rhythm session: notes survive both HUD writers (`bExecutionDrivingHighway`) |

## Code / PR status (cloud)

| Deliverable | State |
|-------------|--------|
| RestoreParty call site (`BP_BattleController` iterator) | **PR #6** (rebased) — not on `main` until merge |
| Git health (LFS gate, ignore brush pack/pycache) | **PR #4** — ready, not merged |
| Highway ownership (`MelodiaRhythmHUDWidget`) | In MelodiaCore tree; needs closed-editor build + PIE |
| Playable levels under VCS | **On `main`** — `43d0a9ae` (`L_MelusinaMorning`, `L_KaleidoNave`, Melodia/EnvSandbox PCG) |

## PIE checklist (short)

1. **One** UnrealEditor + Monolith `:9316`. Merge **#4 → #6**, pull `C:\EnvironmentPortfolio\BS_GodFile`.
2. Full closed-editor build (highway + RestoreParty).
3. Walk: Morning Quill/WillScript → KaleidoNave encounter (not a missing Dreamstate map).
4. Battle end: log `MELODIA_RECOVERY restored N…` (or no-controller warning).
5. Rhythm skill: highway visible; ambient lane does not wipe stock notes next tick.
6. `python Tools/playtest_harness.py` real keys → JSON beside frames → `record_gate.py runtime pass|fail`.

## Do not re-verify

- `curentMP` spelling (live reflection confirmed typo in stock struct).
- Damage-scalar sequencing PASS (quoted FinishSession order).
- Melusina walks (owner confirmed).

## Related

- Campaign: `Docs/ECHO/campaign_01_rhythm_damage_delta.md`
- Closeout: `Docs/Handoffs/CORE_GAMEPLAY_CLOSEOUT_PLAN_2026-08-11.md`
- Cloud git prep: `Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md`
