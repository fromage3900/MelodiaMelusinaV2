# Superseded documents

Nothing here is current. These files are kept because they explain **why** decisions
were made, and because deleting project history is how the same argument gets had twice.

**Do not act on anything in this folder.** If a file here contradicts a live doc, the
live doc wins. If it contradicts `_DECISION_LOG.md`, the decision log wins.

## Archived 2026-08-13

Sixteen root-level documents, moved during the repo lock-in pass. Root `.md` count went
from 57 to 42.

### The five-way "what to do next" split

`_TASK_QUEUE.md` is the only maintained task authority. Four other documents claimed the
same job, three of them asserting SSOT or priority status:

| File | Last true | Why it went |
|---|---|---|
| `NEXT_ACTIONS.md` | 2026-07-16 | Env-art strategic priorities, pre-dating the gameplay pivot |
| `NEXT_HIGHEST_LEVERAGE_TASK.md` | 2026-07-14 | Claimed SSOT for gameplay issues; GS-001…007 pre-date the JRPG/Quill bridge |
| `PORTFOLIO_READINESS.md` | 2026-07-15 | A checklist scoring itself on "doc X was created" |
| `_AGENT_GOALS_2026-08-02.md` | 2026-08-02 | A single night's goal sheet ("the site ships tonight") |

`DOC_INDEX.md:3` already warned against exactly this — "prefer updating this index over
creating another floating status document."

### Retired by Decision 002 (the 5-agent ownership model)

`AGENT_OPERATING_MODEL.md`, `AGENT_BOUNDARIES.md`, `AGENT_OWNERSHIP.md`. The
PGA/MPA/PPA/WIA/SQA boundaries no longer apply; this is a solo project. `AGENT_OWNERSHIP.md`
was a near-verbatim duplicate of `AGENT_BOUNDARIES.md` under a different title. Read them
for tool-capability context only.

> Note: `.github/CODEOWNERS` still says it "mirrors AGENT_OWNERSHIP.md". That reference is
> to this archived file and should be rewritten against real paths.

### Superseded by the vertical-slice pivot (Decision 008)

`ROADMAP.md` (6-phase env-art plan ending at "Portfolio Showcase"; also targets Blender 5.1
and Houdini, neither in the live pipeline), `UNIVERSAL_ENVIRONMENT_PIPELINE.md`,
`SYSTEM_EVOLUTION_MAP.md` (plans a "Portfolio Package v2" that was never built),
`TASK_GRAPH.md` (a static mermaid DAG of env-art work).

### Dead on their own terms

| File | Why |
|---|---|
| `AUTOMATION_OPPORTUNITIES.md` | Every link is `file:///g:/...` — the G: drive is not the project root |
| `UNMAPPED_DATA_POINTS.md` | Same broken `g:/` links; assumes Blender 5.1 |
| `FIGMA_LAYOUT_GAPS.md` | Gap list for a Figma set superseded by the 2026-08-12 UI suite |
| `CHANGELOG_24H.md` | A 24-hour changelog last true 2026-07-09, tracking a branch that no longer exists |
| `WORKING_SOLUTION.md` | A scratch troubleshooting note about a Cursor provider error, not documentation |

## Two facts these files get wrong, repeatedly

Worth knowing before reading any of them:

1. **"Push to `origin` is blocked — `github.com:443` unreachable."** Connectivity is
   *intermittent*, not blocked. Pushes have succeeded since 2026-08-11.
2. **"Blender 5.1."** 5.1 is not installed. The project runs **5.2**. A retarget was marked
   complete (`TODO.md` A6, `_ROADBLOCKS` C7) but only covered `Docs/` — root-level docs, i.e.
   most of this folder, still said 5.1.

## The one file here that predates this pass

`MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md` — archived earlier, when this
convention was first invented and then not used again for a month.
