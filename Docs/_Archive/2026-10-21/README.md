# Archived documentation — 2026-10-21

**These are historical session documents. None of them is current authority.**
For what works, what is open, and what to do next, use
[`CURRENT_STATE.md`](../../../CURRENT_STATE.md) — the only status document.

## Why these are here rather than deleted

The 2026-09-11 documentation collapse (`08a608bce`, "docs: collapse status docs to
one CURRENT_STATE.md") deleted 840 status, handoff, plan and receipt files
outright. Their content survives only in git history, readable with
`git show 7d271c15:<path>` (tag `docs-precollapse-2026-09-10`).

These 40 files were **not** part of that collapse, and they had drifted back in
afterwards. Each one was verified before being moved here:

1. **Zero inbound references.** The file's path *and* its basename appear in no
   other tracked file in the repository — not in a doc, not in a tool, not in a
   spec, not in a workflow.
2. **Session-shaped.** The name marks it as a handoff, closeout, plan, session
   record or audit for one working session, not a durable contract.
3. **Its subject is live elsewhere.** Where the document described real work,
   that work is tracked in `CURRENT_STATE.md`, in `specs/`, or in the tooling
   that implements it. Archiving the note does not archive the work.
4. **No open work stranded in it.** The few documents that still carried an
   open item were checked against `CURRENT_STATE.md` first; that work is
   either already tracked there or genuinely dead.

The original path of each file is preserved under this directory, so
provenance is obvious: a file at `Docs/_Archive/2026-10-21/Docs/Handoffs/X.md`
was `Docs/Handoffs/X.md`.

## What is NOT here

- **Contracts and references.** Anything a build, gate or agent reads at run
  time stays in place. `Docs/Production/`, `Docs/References/`, `Docs/Architecture/`
  and `specs/` are not session notes.
- **Anything with a live referrer.** A document that another tool or spec
  points at stays where it is, even if it looks like a session note.
- **The status authority.** `CURRENT_STATE.md` is the only status document.
  A file named `current_state.md` under `Docs/Poitou/` was renamed
  `poitou_v2_state_2026-10-20.md` for exactly this reason — its basename
  shadowed the real authority.

## Reading an archived document

```sh
# this archive (content is unchanged except for link repairs)
git show refs/agents/docs-archive-20261021:Docs/_Archive/2026-10-21/<path>

# the 840 files removed by the 2026-09-11 collapse
git show 7d271c15:<path>
```

## The rest of the 2026-10-21 review

This directory is one part of a wider review. The same pass also:

- took the documentation gate from **36 errors to 0** (`Tools/doc_lint.py --ci`,
  a hard CI gate that was red on `main`);
- fixed a bug in the gate itself, which resolved `FILE.md#anchor` as a literal
  path and so flagged every section link in the repository;
- removed four files that were tracked **twice** under `Docs/` and `docs/`
  (same blob, two index entries) because `core.ignorecase` is true;
- removed fourteen byte-identical duplicate documents, after proving each one
  had an identical copy retained at its canonical path;
- landed the Kenney retirement write-up that `main` already linked to but
  which existed only on an unlanded lane, correcting its stale
  "not submitted" claim (change 292 *was* submitted, 25 minutes after the
  document was written);
- mirrored seven material instances out of git that Perforce change 292 had
  already deleted, so a fresh clone can no longer resurrect assets the depot
  no longer has.
