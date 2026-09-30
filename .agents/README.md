# `.agents/` — agent lane state

Machine-local agent state lives here. See [`Docs/Production/MULTI_AGENT_LANES.md`](../Docs/Production/MULTI_AGENT_LANES.md).

| Path | Tracked? | What it is |
|---|---|---|
| `.git/agents/lanes/<lane>.json` | no — inside `.git`, never tracked | the lane descriptor: worktree path, pinned ref, claimed paths, heartbeat |
| `plans/` (here) | yes | dated plans. Deliberately tracked — see the note below |
| `skills/` (here) | yes | agent skill definitions |

**Lane descriptors live in the shared git dir, not in the working tree.**
`Tools/agent_lane_registry.py` resolves them with `git rev-parse --git-common-dir`, so the
primary checkout and every lane worktree see the same registry. The first version put them
under `.agents/lanes/` in the checkout; the pre-commit guard runs from *inside a lane
worktree*, where that path is gitignored and therefore invisible, so every claim check
silently passed. They are rebuilt by `deploy/new_agent_lane.ps1`.

`.hermes/plans/` is **not** ignored, also on purpose. The 2026-09-27 and 2026-09-28 plans
were untracked, never committed, and were destroyed with the checkout that held them;
`git log --all` has no trace of them. Keeping plans visible in `git status` is what makes
them get committed. If you write a plan, commit it.
