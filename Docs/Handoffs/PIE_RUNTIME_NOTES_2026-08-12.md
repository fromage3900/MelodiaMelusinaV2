# PIE / Runtime notes — 2026-08-12

Owner + cloud reconciliation. **Owner statements about the rig are ground truth.**
This file is the living board for the P0 play loop until `runtime` has a ledger row.

Older checklists still apply as walk scripts (do not duplicate status into them):

- [Docs/PIE_VERIFICATION_CHECKLIST_2026-08-03.md](../PIE_VERIFICATION_CHECKLIST_2026-08-03.md)
- [Docs/FIRST_DREAM_20_MINUTE_PLAYTEST_2026-08-01.md](../FIRST_DREAM_20_MINUTE_PLAYTEST_2026-08-01.md)
- Campaign: [Docs/ECHO/campaign_01_rhythm_damage_delta.md](../ECHO/campaign_01_rhythm_damage_delta.md)

## Gate ledger (truth)

| Gate | Status | Notes |
|------|--------|-------|
| `static_gates` | **PASS** (`0e34eaed`) | Material drifts accepted; sweeps scoped |
| `runtime` | **FAIL** (honest) / OPEN for re-cert | Needs real Q/W/O/P via `BP_BattleUI::OnKeyDown` + assertion JSON + `record_gate.py runtime` |
| `save_load` | OPEN | Never closed |
| `repeat_consume` | OPEN | |
| `package_launch` | OPEN | |

Probe-only / Python-injected rhythm hits are **not** play evidence.

## Owner progress (2026-08-12) — ground truth

| Item | Owner status | Verify in PIE |
|------|--------------|---------------|
| **Quill / WillScript** | Updated; **should work at runtime** | Morning intro → `melodia:battle:…` notify → typed result → Quill resumes **once** |
| **P0 battles — dreamstate path** | Still **do not work properly** (working through) | Route is Morning → **KaleidoNave** (Dreamstate merged into KaleidoNave; wake portal dest = KaleidoNave). Do not look for a live `L_Melodia_Dreamstate` map. |
| **P0 battles — collider-name level** | Still **broken** (working through) | Encounter tag `melodia_smoke_encounter` + `BP_BattleController` in level + stock `StartBattle` contract |
| **Rhythm highway** | Ownership fix in MelodiaCore source; **not PIE-verified** | Stock rhythm session: notes survive both HUD writers (`bExecutionDrivingHighway`); ambient lane must not wipe stock notes next tick |

## Merge / pull status (cloud cannot finish)

| Deliverable | State |
|-------------|--------|
| **PR [#4](https://github.com/fromage3900/MelodiaMelusinaV2/pull/4)** git health | OPEN · MERGEABLE · **BLOCKED** — needs **1 approving review** (write access). CI reds were self-hosted **network** to github.com/codeload, not code. Prefer **squash**. |
| **PR [#6](https://github.com/fromage3900/MelodiaMelusinaV2/pull/6)** RestoreParty | OPEN · rebased · same review block. Prefer **squash**. Merge **after** #4. |
| Cloud agent merge attempt | Failed: merge commits disallowed; admin still needs approving review; auto-merge not enabled |
| PC pull | **Not done** until #4+#6 land on `main` — then `git pull` in `C:\EnvironmentPortfolio\BS_GodFile` |
| Highway ownership (`MelodiaRhythmHUDWidget`) | In MelodiaCore tree; needs closed-editor build + PIE |
| Playable levels under VCS | **On `main`** — `43d0a9ae` |

**Owner action to unblock:** approve + squash-merge [#4](https://github.com/fromage3900/MelodiaMelusinaV2/pull/4) then [#6](https://github.com/fromage3900/MelodiaMelusinaV2/pull/6) (or approve and ask agent to retry after checks).

## PIE checklist (short)

1. One UnrealEditor + Monolith `:9316`. Squash-merge **#4 → #6**, pull `C:\EnvironmentPortfolio\BS_GodFile`.
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

- Cloud git prep: `Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md`
- Closeout: `Docs/Handoffs/CORE_GAMEPLAY_CLOSEOUT_PLAN_2026-08-11.md`
- Phone queue: `Docs/PhoneOps/BACKLOG.md`
