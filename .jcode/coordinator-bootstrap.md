> **CURRENT DISCOVERY RULE:** Read [`CURRENT_STATE.md`](../CURRENT_STATE.md) first. It is the only current status / priority / open-work authority. Use [`SYSTEM_MAP.md`](../SYSTEM_MAP.md) and [`DATA_FLOW.md`](../DATA_FLOW.md) for architecture, [`Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md`](../Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md) for the laptop/DCC workstation contract, and [`Docs/Art/VISUAL_REFERENCE_INDEX.md`](../Docs/Art/VISUAL_REFERENCE_INDEX.md) for visual references.
>
> Dated handoffs, old task queues, session notes, recovery docs, and historical snapshots are not task authority. Do not create replacements for them; current status belongs in `CURRENT_STATE.md` and session narrative belongs in the PR/commit body.

# Coordinator bootstrap — Melodia jcode fleet

Paste into the **root** jcode session after `.\deploy\setup_agent_lanes.ps1` (once) and
`.\deploy\start_jcode_swarm.ps1`.

---

You are the Melodia **coordinator** (light swarm). Read `CURRENT_STATE.md`, `AGENTS.md` (BINDING RULES),
and `.jcode/swarm-prompt.md`. Each worker gets its own worktree from `origin/main`, returns a patch
branch, and never pushes/merges. No editor access for any worker. Cap 6.

## Fleet 1 — 2026-09-26 (four file-disjoint packets)

1. **harness-frames** · lane `code` · may_write `Tools/regression_suite.py` (PIE capture section only) ·
   goal: find why `test_pie_melusina_morning` reports `frames_captured 0` from a static read of the
   capture path; fix it without starting Unreal · done_when: a unit-level repro/fix note in the patch +
   `python -m py_compile Tools/regression_suite.py` clean. Editor proof is handed back as a packet.
2. **harness-battle** · lane `code` · may_write `Tools/regression_suite.py` (KaleidoNave battle section only
   — coordinate with packet 1: land 1 first, rebase 2) · goal: replace the `WalkForward`/`Interact` console
   trigger with the highway gate's tagged-contract start (`Prototypes/RhythmHighwayCues/highway_cue_gate.py`
   `START_BATTLE`) · done_when: `py_compile` clean + diff shows the reused snippet, no new battle path.
3. **router-lease** · lane `code` · may_write `Tools/agent_lease.py`, `Tools/test_agent_lease.py`,
   `Tools/model_router.py` (append-only: a `route` subcommand that asks Jev via `typesafe_sdk` to choose
   a class for a task packet, falling back to a keyword table) · goal: orchestrator plan H1 editor lease
   (`Saved/Agents/editor.lease`, refuses a second holder, honours `deploy/*_LOOP_STOP`) · done_when:
   `python Tools/test_agent_lease.py` passes.
4. **figma-kit-export** · lane `fast` · may_write `Tools/figma_export_kit.py` · goal: W2 of
   `.hermes/plans/2026-09-26_storybook-ui-work-plan.md` — export the Storybook component variants at 2×
   via the Figma images API, token from env `FIGMA_TOKEN` (never in files), output to a staging folder
   outside `Content/` · done_when: `--dry-run` lists the node ids without network writes.

**Not for the swarm:** ladder rung 4 (`Tools/issue51_ladder.ps1 launch` + log triage) and every editor
task go to Hermes-in-Claireon, one at a time.

## Stop conditions

- A worker wants to write outside `may_write`, touch the editor, or push → reject and rescope.
- Two packets need the same file → serialize them.
- A worker proposes a new status/plan/handoff file or a new router/framework → redirect to
  `CURRENT_STATE.md` / the existing plan / `Tools/model_router.py`.
