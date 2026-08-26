# Agent lane handoff (lightweight)

Shared tip-of-lane record for Claude / Codex / Kimi / OpenCode / Pi / Cursor / Hermes operators.

**Not** a project-management system. Product authority stays:

- `_AGENT_WORKING_AGREEMENT.md`
- `_TASK_QUEUE.md` / `Docs/P0_TASK_LEDGER.json` (gameplay P0)
- `Docs/PhoneOps/BACKLOG.md` (phone Now)
- Git (`main` + lane branches)

Handoffs **describe** work. Git is persistent state. Evidence establishes truth ([AGENTS.md](../../AGENTS.md) Echo rules).

## When to write one

- Starting a multi-hour / multi-machine lane
- Handing off mid-task to another agent or the owner’s phone
- Closing a lane that touched more than one commit

Skip for one-line doc typos. Prefer one short file or a block at the top of `_SESSION_HANDOFF.md` — do not invent a parallel tracker.

## Required fields

```text
TASK:
STATUS:
BRANCH:
START SHA:
END SHA:
FILES CHANGED:
AUTHORITY:
VALIDATION:
EVIDENCE:
BLOCKER:
NEXT ACTION:
DO NOT TOUCH:
```

### Field notes

| Field | Meaning |
|-------|---------|
| TASK | One sentence; the ask is the scope |
| STATUS | One of the states below |
| BRANCH | Exact branch name (`cursor/...` or `agent/<tool>/...`) |
| START SHA / END SHA | Full or 7+ char SHAs; END blank while in progress |
| FILES CHANGED | Paths only; no essays |
| AUTHORITY | Doc or decision that permits the write (e.g. owner ask, Decision NNN) |
| VALIDATION | What was run (build, fingerprint, docs-only N/A) |
| EVIDENCE | Ledger row, PR URL, screenshot path, or `none — docs only` |
| BLOCKER | Empty if none; otherwise what stops PROVEN |
| NEXT ACTION | Single next step for the next operator |
| DO NOT TOUCH | Paths/systems this lane must not edit |

## Valid STATUS values

| State | Means |
|-------|--------|
| DESIGNED | Spec / plan only; no product change claimed |
| IMPLEMENTED | Code/docs landed on a branch |
| SOURCE_BUILT | Closed-editor / CI build green for the change |
| LIVE | Running in editor / PIE on the owner box |
| PROVEN | Acceptance met **and** Echo/ledger or owner lock where required |
| BLOCKED | Cannot proceed; BLOCKER filled |
| DEFERRED | Explicitly parked; not a silent drop |

Probe-only or screenshot-only claims are not PROVEN for runtime gates.

## Branch naming (convention — create only when asked)

```text
agent/claude/<short-topic>
agent/codex/<short-topic>
agent/kimi/<short-topic>
agent/opencode/<short-topic>
agent/pi/<short-topic>
```

Cursor Cloud: keep `cursor/<descriptive>-ca02` (or the run’s required suffix).

## Identity checklist (every agent)

Before writing product files, know:

1. Current branch (`git branch --show-current`)
2. Current commit (`git rev-parse --short HEAD`)
3. Task (owner message or TASK field)
4. Authority (working agreement + allowlist for the paths)
5. Handoff location (this template or session handoff pointer)
6. Validation status (STATUS + VALIDATION/EVIDENCE)

## Paste template

```markdown
## Lane handoff — YYYY-MM-DD

TASK: …
STATUS: DESIGNED | IMPLEMENTED | SOURCE_BUILT | LIVE | PROVEN | BLOCKED | DEFERRED
BRANCH: …
START SHA: …
END SHA: …
FILES CHANGED:
- …
AUTHORITY: …
VALIDATION: …
EVIDENCE: …
BLOCKER: …
NEXT ACTION: …
DO NOT TOUCH: …
```

## Related

- [REMOTE_WSL_AGENT_STACK_2026-08-25.md](REMOTE_WSL_AGENT_STACK_2026-08-25.md) — phone → WSL → tmux stack status
- [MOBILE_LANES.md](MOBILE_LANES.md) — phone vs PC ownership
- [`_SESSION_HANDOFF.md`](../../_SESSION_HANDOFF.md) — stacked session notes (prefer current tip only when editing)
