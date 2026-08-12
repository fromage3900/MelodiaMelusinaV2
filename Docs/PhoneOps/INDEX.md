# Phone Ops Index

Front door for driving MelodiaMelusina from iOS / Cursor mobile.

**Artist bridge (read first on phone):**
[PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md](../Handoffs/PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md)
— what phone Cursor is for (Drive + git + Remote Control), not sandbox ops.

## Start here (order)

1. [../Handoffs/PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md](../Handoffs/PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md) — phone artist intent + Drive-ready protocol
2. [SETUP.md](SETUP.md) — SuperGrok + Cursor Pro + phone/GitHub agents
3. [NORTH_STAR.md](NORTH_STAR.md) — goal, this-week focus, milestones, open decisions
4. [BACKLOG.md](BACKLOG.md) — Now / Next / Backlog
5. [RECENT_STUDY.md](RECENT_STUDY.md) — recent main changes + Monolith/Cursor skills inventory
6. [JCODE_SWARM_PIPELINE.md](JCODE_SWARM_PIPELINE.md) — **Implemented** jcode swarm install + Recipes A/B
7. [SCRATCHPAD.md](SCRATCHPAD.md) — research notes (append-only)

Harness files: [`.jcode/README.md`](../../.jcode/README.md) · `.\deploy\start_jcode_swarm.ps1`

Then, if you need deeper truth:

| Doc | Why |
|---|---|
| [../../README.md](../../README.md) | Project pitch + onboarding paths |
| [../../CURRENT_STATE.md](../../CURRENT_STATE.md) | Implementation truth table |
| [../../NEXT_ACTIONS.md](../../NEXT_ACTIONS.md) | Platform producer queue |
| [../../DOC_INDEX.md](../../DOC_INDEX.md) | Full doc map |
| [../../AGENTS.md](../../AGENTS.md) | Multi-agent ownership |
| [../../PIPELINE.md](../../PIPELINE.md) | Blender ↔ UE ↔ portfolio map |
| [../AgentMemory/Decisions.md](../AgentMemory/Decisions.md) | Locked decisions |
| [../Production/MODEL_LANES_2026-08-12.md](../Production/MODEL_LANES_2026-08-12.md) | Model lanes + local daemon policy |

## How to use from phone

### Kick a focused agent

Paste one of these:

```text
Read Docs/Handoffs/PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md.
Drive is connected. Pull my Melodia scan/research folder, consolidate into the repo, open one draft PR. No process docs. No UE/Blender from cloud unless Remote Control is on.
```

```text
You are on MelodiaMelusinaV2. Read Docs/PhoneOps/NORTH_STAR.md and Docs/PhoneOps/BACKLOG.md.
Do only the first Now item. Stay Green/Yellow autonomy. No Sakura level edits. PR when done.
```

```text
Summarize CURRENT_STATE.md for phone: Implemented vs Broken vs Partial only. Max 12 bullets.
```

```text
Update Docs/PhoneOps/BACKLOG.md from NEXT_ACTIONS.md + NEXT_HIGHEST_LEVERAGE_TASK.md.
Do not invent work; cite existing docs.
```

### Review a PR on phone

1. Open the agent URL / PR link from the run summary.
2. Check: branch prefix `cursor/`, docs under `Docs/PhoneOps/` or append-only Docs, no `Content/_PROJECT/` writes.
3. Merge only if scope matches NORTH_STAR this-week focus.

### Sync Grok → repo

If Grok dropped files in `/artifacts` (and did not push):

```text
Recreate Docs/PhoneOps/{SETUP,INDEX,SCRATCHPAD,NORTH_STAR,BACKLOG}.md from the pasted content
and reconcile with CURRENT_STATE.md / NEXT_ACTIONS.md. Open a draft PR.
```

## Directory map (mental model)

```text
Blender surreal_os/arch  →  world.json  →  UE import/HISM
Material masters/MIs     →  manifests   →  portfolio_package → website configs
PCG graphs               →  EnvSandbox scatter
JRPG + MelodiaIntegration →  playable First Dream loop (not MelodiaCore combat)
PhoneOps docs            →  your mobile control plane
```

## Red lines (always)

- Do not edit Sakura level composition (`L_SakuraPath` / human-owned art).
- Do not write into `Content/_PROJECT/`.
- Do not publish externally without explicit approval.
- Prefer `EnvSandbox`, `deploy/`, `Docs/`, `Content/Python/` for agent work.
- Do not rebuild JRPG combat authority in MelodiaCore this phase.
