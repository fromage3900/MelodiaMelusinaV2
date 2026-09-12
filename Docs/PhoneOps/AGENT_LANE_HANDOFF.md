# Agent lane handoff

Shared lightweight tip-of-lane record for Claude / Codex / Kimi / OpenCode / Pi / Cursor / Hermes operators.

**Current authority:** 2026-09-04

This is **not** a project-management system. Read [`../../AGENT_START_HERE.md`](../../AGENT_START_HERE.md) first.

Product/task authority comes from:

- the owner's current request;
- `AGENT_START_HERE.md`;
- `TODO.md` / current vertical-slice docs;
- current Git state, including relevant non-main branches;
- current evidence.

Deleted `_TASK_QUEUE.md` and `_SESSION_HANDOFF.md` are historical scratch references and must not be recreated as authority.

## When to write a handoff

Use one when:

- handing a multi-hour task to another machine/agent;
- leaving work on a non-main branch;
- closing a lane that changed multiple files/commits.

For laptop work, also make sure the branch is discoverable from `Docs/Production/LAPTOP_WORK_DISCOVERY_2026-09-04.md`.

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

## STATUS values

| State | Meaning |
|---|---|
| DESIGNED | plan/spec only |
| IMPLEMENTED | files committed on a branch |
| SOURCE_BUILT | relevant build/compile passed |
| LIVE | observed in editor/PIE |
| RESTART_PROVEN | survived full process restart/load |
| PACKAGED_PROVEN | reproduced in packaged build |
| BLOCKED | cannot proceed; blocker stated |
| DEFERRED | explicitly parked |

Do not call probe-only or screenshot-only behavior `LIVE`/proof unless the acceptance contract actually permits it.

## Identity checklist

Before changing product files, know:

1. exact current branch;
2. current SHA;
3. owner's requested scope;
4. current authority document;
5. whether newer work exists on another workstation branch;
6. strongest validation/evidence level.

## Paste template

```markdown
## Lane handoff — YYYY-MM-DD

TASK: …
STATUS: …
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

## Related current discovery

- [`../../AGENT_START_HERE.md`](../../AGENT_START_HERE.md)
- [`../Production/LAPTOP_WORK_DISCOVERY_2026-09-04.md`](../Production/LAPTOP_WORK_DISCOVERY_2026-09-04.md)
- [`../Art/VISUAL_REFERENCE_INDEX.md`](../Art/VISUAL_REFERENCE_INDEX.md)
- [`../../MELODIA_TECHNICAL_VERTICAL_SLICE.md`](../../MELODIA_TECHNICAL_VERTICAL_SLICE.md)
