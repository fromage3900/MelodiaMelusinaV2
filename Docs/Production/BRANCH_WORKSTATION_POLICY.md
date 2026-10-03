# Branch & Workstation Policy

**Status:** Superseded by owner-directed main-only workflow (2026-09-29)

Use the existing local project checkout on `main` as the only work lane. Do not create or switch
branches, lane refs, detached checkouts, linked worktrees, clones, GitHub branches, or pull requests
for project work. A dirty or occupied `main` is not a reason to route around it. Make scoped edits in
place and preserve existing work. Do not fetch, push, merge, rebase, reset, stash, clean, stage,
commit, delete refs, or start another checkout/agent unless the owner explicitly requests that exact
operation.

The branch-class, fresh-branch, temporary-PR, and laptop-lane procedures formerly documented here
are historical and must not be used as current instructions. Owner-directed retirement of a named
worktree/branch requires a verified recovery snapshot first, a check for editor/build ownership, and
removal of only the named item. `CURRENT_STATE.md` records live status and any specifically retired
checkout.