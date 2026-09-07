# Recruiter / Professor Repository Hardening — 2026-09-07

**Status:** ACTIVE / safe showcase cleanup  
**Branch policy:** direct `main`; no new branch created for this pass.

## Landed

- Public README now leads with the live portfolio, Selected Art, Resume, and current verified state.
- Removed stale "production-grade" marketing language in favor of evidence-backed project framing.
- Reconciled the apparent P0 count contradiction:
  - `Docs/P0_TASK_LEDGER.json` / `CURRENT_STATE.md` = **8/8 active P0 gates**.
  - the older 10-row matrix is retained only as historical closeout taxonomy.
- `UNIVERSITY.md` and `PORTFOLIO.md` no longer advertise a nonexistent "coming soon" portfolio.
- Public-facing document titles no longer lead with the internal `BS_GodFile` codename.
- Root raw-art spill moved into `RawArt/Inbox/` without deleting the tracked blobs.
- Removed root git/agent scratch: `.git-rewrite/`, `.codex_staged_paths.txt`, and accidental `g`.
- Added ignore guards so git rewrite/scratch artifacts do not return.
- Root entry count reduced **154 → 135** in the safe first pass.

## PR #114 safety status

PR #114 contains valuable root-trim work, but it is **not safe to merge wholesale**.

Its branch mixes:
- root renames/deletions;
- material `.uasset` changes;
- gameplay Blueprint assets;
- wardrobe/runtime work;
- additional semester-prep content.

The PR description also previously said `BP_BattleController.uasset` and
`MelodiaQuillDefeat.uasset` were not included while the actual diff includes them.
The PR title/body now carry an explicit DO-NOT-MERGE-WHOLESALE warning.

## What remains

### P1 — reference-aware root document moves

The large remaining root trim should be done only after searching and updating inbound
references. Do **not** mechanically replay PR #114's moves because several root files
are discovery entry points used by agents and humans.

Candidates:
- dated audit/report files → `Docs/Archive/` or `Docs/Reports/`;
- pipeline-specific docs → `Docs/Pipeline/`;
- long-horizon planning docs → `Docs/Planning/`.

Keep these easy-to-find entry points at root unless/until every discovery contract is
updated:
- `README.md`
- `CURRENT_STATE.md`
- `AGENTS.md`
- `AGENT_START_HERE.md`
- `INDEX.md`
- `PORTFOLIO.md`
- `UNIVERSITY.md`
- `QUICKSTART.md`
- `BS_GodFile.uproject`

### P2 — public issue tracker edit

Do not close research issues just to make the tracker look small. Close a spike only
when its result is captured as ADOPT / PARK / REJECT / WATCH in the current research
SSOT. The desirable public end state is a short active roadmap plus closed research
with outcome comments, not erased history.

### P3 — stable showcase tag

After the new UE5.8 Melusina B2 render set and the next canonical world beauties are
accepted, cut a stable portfolio/showcase tag or release so external reviewers have a
fixed reference while `main` continues to evolve.

## Showcase principle

A recruiter should be able to answer these within one screen / one click:

1. What is Melodia?
2. What did Brennan personally build?
3. Does the technical slice actually work?
4. Where is the strongest art?
5. What is intentionally still in progress?

Anything that does not help those answers belongs below the root entry layer.
