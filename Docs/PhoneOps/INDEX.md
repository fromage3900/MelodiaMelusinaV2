# Phone Ops Index

Front door for driving **MelodiaMelusinaV2** from iOS / Cursor mobile / SuperGrok.

**Artist bridge (read first on phone):**
[PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md](../Handoffs/PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md)
— what phone Cursor is for (Drive + git + Remote Control), not sandbox ops.

## Start here (order)

1. [../Handoffs/PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md](../Handoffs/PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md) — phone artist intent + Drive-ready protocol
2. [HIGHEST_LEVERAGE_NOW.md](HIGHEST_LEVERAGE_NOW.md) — **RT-001…007 / PH-*** (read first)
3. [../Handoffs/PIE_2026-08-11.md](../Handoffs/PIE_2026-08-11.md) — owner runtime truth (Kaleido triggers, UI alpha, Sir CTRL, highway)
4. [MOBILE_LANES.md](MOBILE_LANES.md) — phone vs PC; Drive / Live Link / Polycam
5. [SETUP.md](SETUP.md) — SuperGrok + Cursor Pro + phone/GitHub agents
6. [NORTH_STAR.md](NORTH_STAR.md) — **Ship Melodia** · P0 live proof · P1 sendoffs (OpenCode first; NVIDIA withdrawn)
7. [BACKLOG.md](BACKLOG.md) — Now / Next · P0 gates + [RECRUITER_SENDOFFS…](../Career/RECRUITER_SENDOFFS_2026-08-25.md)
8. [ENV_PACK_RESEARCH_POINTER.md](ENV_PACK_RESEARCH_POINTER.md) — cute/mystical/underwater packs
9. [../MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md](../MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md) — Polycam/Kiri → ZBrush → Rokoko
10. [RECENT_STUDY.md](RECENT_STUDY.md) — recent main changes + Monolith/Cursor skills inventory
11. [JCODE_SWARM_PIPELINE.md](JCODE_SWARM_PIPELINE.md) — **Implemented** jcode swarm install + Recipes A/B
12. [SCRATCHPAD.md](SCRATCHPAD.md) — research notes (append-only)

Harness: [`.jcode/README.md`](../../.jcode/README.md) · `.\deploy\start_jcode_swarm.ps1`

Then, if you need deeper truth:

| Doc | Why |
|---|---|
| [../../README.md](../../README.md) | Public V2 + Echo front door |
| [../../CURRENT_STATE.md](../../CURRENT_STATE.md) | Implementation truth table |
| [../../NEXT_ACTIONS.md](../../NEXT_ACTIONS.md) | Platform producer queue |
| [../../_TASK_QUEUE.md](../../_TASK_QUEUE.md) | Gameplay P0 tracker |
| [../../DOC_INDEX.md](../../DOC_INDEX.md) | Full doc map |
| [../../AGENTS.md](../../AGENTS.md) | Working agreement + Echo evidence |
| [../../PIPELINE.md](../../PIPELINE.md) | Blender ↔ UE ↔ portfolio map |
| [../LIVEOPS_GIT_SOP_2026-08-11.md](../LIVEOPS_GIT_SOP_2026-08-11.md) | 50 MB collab / LFS |
| [../ECHO_PIPELINE_2026-08-09.md](../ECHO_PIPELINE_2026-08-09.md) | Echo stages + ledger |
| [../AgentMemory/Decisions.md](../AgentMemory/Decisions.md) | Locked decisions |
| [../Production/MODEL_LANES_2026-08-12.md](../Production/MODEL_LANES_2026-08-12.md) | Model lanes + local daemon policy |

## How to use from phone

### Kick a focused agent

```text
Read Docs/Handoffs/PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md.
Drive is connected. Pull my Melodia scan/research folder, consolidate into the repo, open one draft PR. No process docs. No UE/Blender from cloud unless Remote Control is on.
```

```text
You are on MelodiaMelusinaV2. Read Docs/PhoneOps/HIGHEST_LEVERAGE_NOW.md
and Docs/Handoffs/PIE_2026-08-11.md. Docs only unless I say editor is free.
One RT-* or PH-* only. No Sakura. No Done without Echo ledger evidence.
```

```text
Summarize CURRENT_STATE.md for phone: Implemented vs Broken vs Partial only. Max 12 bullets.
Respect PIE_2026-08-11 over older “build-green” claims.
```

### Review a PR on phone

1. Open the agent URL / PR link from the run summary.
2. Check: branch prefix `cursor/`, docs under `Docs/PhoneOps/` or append-only Docs, no `Content/_PROJECT/` writes.
3. Merge only if scope matches HIGHEST_LEVERAGE / NORTH_STAR this-week focus.

### Sync Grok → repo

If Grok dropped files in `/artifacts` (and did not push — common 403 write):

```text
Recreate the PhoneOps/PIE/env-pack docs from the Grok share into MelodiaMelusinaV2
on cursor/v2-game-foundation-098b (or docs branch). Reconcile with PIE_2026-08-11.
Open/update draft PR. Do not claim runtime gates Done.
```

Share that seeded this pack: https://grok.com/share/bGVnYWN5LWNvcHk_c7761e0a-252b-44bf-b4de-4940025d6de0

## Directory map (mental model)

```text
Blender surreal_os/arch  →  world.json  →  UE import/HISM
Material masters/MIs     →  manifests   →  portfolio_package → website configs
PCG graphs               →  EnvSandbox scatter
MelodiaIntegration+JRPG  →  First Dream loop (runtime still OPEN)
PhoneOps docs            →  mobile control plane
```

## Red lines (always)

- Do not edit Sakura level composition (`L_SakuraPath` / human-owned art).
- Do not write into `Content/_PROJECT/`.
- Do not publish externally without explicit approval.
- Do not push LFS meshes from phone.
- Prefer `EnvSandbox`, `deploy/`, `Docs/`, `Content/Python/` for agent work.
- Do not rebuild JRPG combat authority in MelodiaCore this phase.
- Echo `runtime` needs real input + ledger — not probe-only.
