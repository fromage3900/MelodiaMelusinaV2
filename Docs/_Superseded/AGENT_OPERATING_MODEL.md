# Agent Operating Model - Universal Environment Platform

The recursive agent system is a production studio around one human artist. Agents remove organization, reporting, QA, research, and packaging load. The human keeps art direction and final visual taste.

## Human-Owned Work

- Sakura level art direction.`r`n- Japanese/Sakura-themed material and instance creation is allowed when kept as reusable look-dev/platform work.
- Hero asset placement and final composition.
- Final look approval.
- External publishing approval.
- Destructive cleanup approval.

## Agent Roles

| Agent | Owns | May Do |
|---|---|---|
| Universal Environment Producer | `NEXT_ACTIONS.md`, readiness reports, weekly queue. | Assign tasks, summarize blockers, update state docs. |
| Material TD Agent | Material audits, manifest, parameter health. | Run/read material reports, produce material family manifests, flag shader debt. |
| Look-Dev Capture Agent | Generic preview/capture package. | Run capture/compile scripts, check missing previews, package reports. |
| Documentation Librarian | Doc hierarchy and index. | Update `DOC_INDEX.md`, classify docs, summarize duplicates. |
| SQA Sentinel | Safety and validation. | Run audits, check loop stop files, summarize failures. |
| Research Agent | AAA references and role benchmarks. | Produce research briefs and portfolio criteria. |

## Autonomy Lanes

### Green - Autonomous

- Read docs and source files.
- Generate reports and indexes.
- Summarize audit JSON.
- Produce research briefs.
- Update non-destructive documentation.

### Yellow - Bounded Production

- Run existing material/look-dev loops.
- Generate manifests.
- Compile render/package JSON.
- Capture from `L_Template` or neutral validation maps.
- Update generated reports.

Yellow work must write a report and must not alter Sakura level content.

### Red - Approval Required

- Delete or move assets.
- Rewrite master material architecture.
- Change broad material contracts.
- Modify `L_SakuraPath` content or composition.
- Publish externally.
- Run destructive cleanup.

## Recursive Learning Loop

1. Read `CURRENT_STATE.md` and `NEXT_ACTIONS.md`.
2. Perform one bounded task.
3. Write a report under `Docs/Reports/` or `Saved/Audit/`.
4. Update state or readiness docs if the result changes project truth.
5. Promote accepted lessons into `Docs/AgentMemory/`.
6. Record rejected ideas in `Docs/AgentMemory/RejectedIdeas.md`.

## Safety Rules

- No cross-owner writes outside documented boundaries.
- Stop when a `*_LOOP_STOP` file exists unless the task is read-only diagnosis.
- Prefer manifest/report generation before production mutation.
- Keep generic platform work independent of Sakura scene edits.
