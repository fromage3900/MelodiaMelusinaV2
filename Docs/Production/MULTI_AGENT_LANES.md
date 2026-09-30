# Multi-agent lanes — retired by owner directive, 2026-09-29

Project work uses the existing local `main` checkout only. Do not create or switch a branch, lane ref,
detached checkout, linked worktree, clone, GitHub branch, or pull request. Do not route around a
dirty `main`; preserve its work and make scoped edits in place. Do not start additional agents or
checkouts unless the owner explicitly asks for them.

`deploy/new_agent_lane.ps1` and `deploy/land_agent_lane.ps1` are disabled. The instructions in the
former lane workflow (including detached worktrees, `refs/agents/*`, temporary remote branches, and
PR landings) are historical only. To retire an existing named worktree, first archive its tracked,
staged, unstaged, untracked, and relevant ignored work, then verify no editor/build process owns it.