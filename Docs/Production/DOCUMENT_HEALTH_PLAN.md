# Document Health Plan

Status: ACTIVE MAINTENANCE PLAN
Last updated: 2026-09-09

## Purpose

Keep the repository's documentation coherent enough that a new agent or collaborator can land, find current truth quickly, and not waste a day on stale or conflicting pages.

This is maintenance, not a rewrite project. The existing front door documents are already good. The job is to keep them that way.

## Scope

Applies to the documents an agent or collaborator is likely to read during a normal session:

- Repository front door and Git authority
- Current production queue and state
- Agent start path and working agreement
- Branch and workstation policy
-any per-lane canonical docs referenced as current authority from those pages

Out of scope: legacy notes, superseded handoffs, research packets, and dated snapshots that are explicitly retained as history.

## Current core document set

These are the pages that should stay mutually consistent:

- `README.md` — public and collaborator-facing entry
- `Docs/Production/CANONICAL_PROJECT_PIPELINE_2026-09-08.md` — canonical cross-repo front door
- `AGENT_START_HERE.md` — current discovery authority for agents
- `_AGENT_WORKING_AGREEMENT.md` — binding working rules
- `Docs/Production/BRANCH_WORKSTATION_POLICY.md` — branch and workstation classification
- `Docs/Production/SEMESTER_SCOPE_LEDGER_2026.md` — Fall 2026 production priority
- `CURRENT_STATE.md` — current verified state

If a later doc is promoted to current authority, it should be added here and referenced from the front door docs, not left as an unlabeled footnote.

## Health criteria

A document set is healthy when:

1. Current authority is easy to identify.
   There is a short, stated reading order for the first five minutes of a session, and it points at the actual current doc, not a dated snapshot.

2. Stale and current are distinguishable.
   Dated files keep their date for a reason. If a page is still true, its date is historical context. If it is no longer true, it is either updated or moved to superseded storage with a note pointing at the replacement.

3. The front door documents agree with each other.
   README, canonical pipeline doc, agent start path, and current-state doc should not tell a fresh reader three different answers to "what is the current authority?"

4. Git truth is gated, not narrated.
   `python Tools/git_ok.py` is the fast gate. If it says OK, no document should spend a session re-litigating git health.

5. Ownership is clear enough to act on.
   Every current authority doc has a known owner class and a known update path. If a doc is stale, someone can say who should look at it without digging.

## Maintenance rhythm

### Before any doc change

1. Identify the document's class.
   Is it current authority, current evidence, or historical context?

2. Identify what it points at.
   If it claims to be current, check the doc it claims to supersede or augment.

3. Update the smallest thing that restores agreement.
   Prefer a pointed edit over a rewrite. If two pages disagree, fix the one that is wrong, not both.

### Periodic review

Once per working week, or when a major lane changes, do a fifteen-minute coherence pass:

1. Re-read the current front door doc first.
2. Confirm it still points to the right current state doc, queue doc, and agent start path.
3. Confirm the branch policy and workstation roles still match reality.
4. Confirm no dated doc is still being cited as current where a newer current doc exists.
5. Confirm git_ok still passes before writing anything git-related.

### After arecovery, handoff, or large merge

Re-check the front door docs against what actually changed. If the event changed what "current" means, update current-state or the canonical pipeline doc, then stop. Do not retroactively sanitize every older page that merely predates the change.

## What gets archived, not rewritten

Archive rather than debate when a doc is:

- superseded by a newer current authority;
- a dated snapshot that is now only useful as evidence;
- a handoff, roadblock, or task queue file that the current authority says is not authoritative.

Archived docs should stay findable if they carry evidence, but they should not sit in the main reading path pretending to be current.

## What gets a fresh date

Date a doc when its content materially changes, not when it is touched. A touch that only fixes a typo or updates a pointer does not need a new date unless the date is part of how the doc is used as evidence.

## What to avoid

- Adding a "document health" file to prove health.
  Health is shown by the docs being coherent and current, not by a report about them.

- Rewriting the whole set because one page is stale.
  Fix the stale page.

- Letting dated handoffs and roadblocks become the default reading again.
  If current authority exists, use it.

- Writing another git archaeology doc when `git_ok.py` already covers the gate.
  If git_ok fails, fix the printed lines. If it passes, stop.

## Owner and escalation

Primary owner class: the person maintaining current production truth on the desktop machine.

When a doc conflict appears during agent work:

1. Prefer the newer current authority.
2. If the conflict is between two dated docs, treat both as historical until checking source or current evidence.
3. If the conflict affects what a session should do next, fix the current front door doc and current-state doc, then continue.
4. If the conflict is larger than a pointed edit, note it and raise it rather than silently choosing one side for a whole section.

## Success state

The doc set is healthy when a new session can do this:

1. Open the front door.
2. Read the stated reading order.
3. Run `python Tools/git_ok.py`.
4. Know where current authority lives.
5. Start the actual task without another documentation discovery pass.

If that works, the plan is working. If it does not, fix the mismatch that broke it and keep going.
