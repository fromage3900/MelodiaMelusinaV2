# Agent lanes

Split out of `AGENTS.md` on 2026-08-13. **Read [`AGENTS.md`](../AGENTS.md) first.**

Rider/Junie-assisted Unreal work must also follow [`RIDER_JUNIE_UNREAL_WORKFLOW_2026-08-28.md`](RIDER_JUNIE_UNREAL_WORKFLOW_2026-08-28.md), which defines the current portable-path, fail-closed-proof, live-UE-validation, shared-Rider-config, Junie-guidance, and atomic-commit train.

## How work is partitioned

The rule, from AGENTS.md safe-working rule 17: **parallelise research, never the editor.**

- **Read-only research** parallelises freely. Six explorer agents ran concurrently on
  2026-08-09 with no incident because none touched the editor.
- **Source/C++ work** parallelises — it builds with the editor closed.
- **All editor work** (PIE, CDO edits, T3D, graph reads) serialises through one holder.
  A second MCP surface does not help; Monolith is in-process, so it is a second writer
  on the same lock.
- **Concurrent git writers corrupt the index.** When several agents work in one
  checkout, exactly one commits. Subagents edit files; the parent stages and commits.

## Plan files — `.agents/plans/`

Live work is specified as a plan file with explicit Goal and Success Criteria sections,
e.g. `.agents/plans/2026-08-12-rhythm-highway-live-feedback.md`. This convention exists,
is where work is actually scoped, and went undocumented until now.

`.agents/` is **gitignored** as of 2026-08-13. Tracking it is a deliberate follow-up, not
an oversight — decide whether plan files are project record or scratch before flipping it.

## STOP sentinels — check before writing anything

If any of these exist, the corresponding work is halted. They outrank any task list.

| Sentinel | Blocks |
|---|---|
| `deploy/SURREAL_ARCH_LOOP_STOP` | writes to `/Game/EnvSandbox/` |
| `deploy/SURREAL_TIERB_LOOP_STOP` | as above |
| `deploy/SURREAL_WORLD_LOOP_STOP` | as above |
| `deploy/AGENT_LOOP_STOP_*` | as above |
| `Saved/Audit/MELUSINA_SHADER_AGENT_STOP` | **all** material/world edits and stage saves |
| `Saved/Audit/sheet_hud_loop_STOP` | agent wake loops |

## Blender stage saves are gated

Policy: `Docs/MELODIA_STAGE_SAVE_POLICY.md`.

**No agent may call `bpy.ops.wm.save_mainfile()` on `Melodia_Portfolio_Stage_*.blend`**
unless `MELODIA_ALLOW_STAGE_SAVE=1` is set *and* the operator explicitly passed `--save`.
The stage is the owner's authored work and an unwanted save is not recoverable.

## Owner locks — do not reopen

| Lock | Date | Canonical |
|---|---|---|
| Rhythm game / highway **WORKED** in live PIE | 2026-08-12 | `Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md` |
| QuillScript / WillScript **WORKED** | 2026-08-12 | `Docs/Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md` |
| `runtime` gate — real keyboard input verified | 2026-08-13 | ledger `[PASS] runtime 2026-08-13`, session `owner-realkey-20260813` |

Owner statements are ground truth (`_AGENT_WORKING_AGREEMENT.md` rule 4). Do not go
verify them, and do not schedule work to re-prove them.

## Current lane dispatch

Live partition: [`Docs/Handoffs/PARALLEL_LANES_2026-08-12.md`](Handoffs/PARALLEL_LANES_2026-08-12.md)
· paste prompts [`PARALLEL_SESSIONS_2026-08-12.md`](Handoffs/PARALLEL_SESSIONS_2026-08-12.md).
History: `PARALLEL_LANES_2026-08-08.md`.

**Never write a PID into a lane prompt.** On 2026-08-12/13 the editor turned over twice
in one night and fourteen locations across seven docs ended up pointing at a dead
process. Say "the one running editor" and have the reader run `Get-Process UnrealEditor`.

## 5. jcode Swarm (parallel coding lane)

Primary **repo-side** parallel coding uses [jcode](https://jcode.sh) light-swarm on the Windows UE workstation — not `deploy/cursor_*_loop.ps1` wake ticks.

*   **Policy:** [`.jcode/swarm-prompt.md`](../.jcode/swarm-prompt.md) — PGA/MPA/PPA/WIA/SQA/WEB/MUSE spawn scopes, concurrency cap 6, no recursive worker spawning.
*   **Bootstrap:** `.\deploy\start_jcode_swarm.ps1` then paste [`.jcode/coordinator-bootstrap.md`](../.jcode/coordinator-bootstrap.md).
*   **MCP:** [`.jcode/mcp.json`](../.jcode/mcp.json) → Monolith stdio proxy (`Plugins/Monolith/Scripts/monolith_proxy.bat`); requires Unreal open for editor tools.
*   **Skills:** `.\deploy\install_jcode_melodia_skills.ps1` installs Monolith skills into `%USERPROFILE%\.jcode\skills\`.
*   **Companion IDE lanes:** OpenCode in Rider (C++/PIE) via [`.opencode/opencode.jsonc`](../.opencode/opencode.jsonc) + `.\deploy\start_opencode_muse_lane.ps1`; Muse Code (WSL) via [`Docs/Production/MUSE_CODE_LANE_2026-08-11.md`](Production/MUSE_CODE_LANE_2026-08-11.md). Tonight prep: [`Docs/Handoffs/TONIGHT_FIRST_DREAM_OPENCODE_2026-08-11.md`](Handoffs/TONIGHT_FIRST_DREAM_OPENCODE_2026-08-11.md).
*   **Keep running:** surreal/world/`run_verify` production loops.
*   **Deprecated for parallel coding wakes:** `deploy/cursor_*_loop.ps1` (left in tree; do not start for new work).
*   **Phone/Cursor cloud agents** remain the PR / mobile lane; do not overlap write paths with a live local swarm without coordination.

Full guide: [Docs/PhoneOps/JCODE_SWARM_PIPELINE.md](PhoneOps/JCODE_SWARM_PIPELINE.md) · [`.jcode/README.md`](../.jcode/README.md)