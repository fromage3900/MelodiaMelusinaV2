# Muse Code — Handoff 2026-08-12 (afternoon: core gameplay closeout)

**Host:** Muse Code, WSL2, v0.1.0 · auth `~/.config/muse/auth.json` · reads `AGENTS.md` + `.mcp.json`
**Lane:** host-side **code edits + harness work**. You have a filesystem and a shell.
**You do NOT have:** the Unreal editor, PIE, or the ability to certify a runtime gate.
**Repo:** `C:\EnvironmentPortfolio\BS_GodFile` (WSL: `/mnt/c/EnvironmentPortfolio/BS_GodFile`),
branch `main`, tracking `v2/main` @ `62c7920d`, **in sync (0 ahead / 0 behind)**.

> Read `CLAUDE.md` first. Rule 1 binds you: **do the job asked, ship it, stop.** Do not open a
> design discussion on any item below. If you find something real while fixing, one sentence at
> the end.

## ⚠ Live-session updates (appended after you started)

- **You already landed `0e34eaed`** — "accept 12 material drifts + scope graph_reachability/bp_sweep
  to shipped defects, static chain ALL OK". Good. **`static_gates` is no longer failing**; any doc
  on disk that says it is, including §0 of the closeout plan, is stale as of now.
- **This repo has a second writer.** `0e34eaed` landed mid-commit from another lane and caused a
  `cannot lock ref 'HEAD'` failure. Before every commit: `git log -1`, expect to re-stage.
  **Never `git reset` to recover from a lock failure** — re-add and commit on top.
- **`43d0a9ae` landed after yours**: the playable route levels + authored PCG graphs are now tracked
  (214 files, ~48 MB LFS). `.gitignore` changed. If you had it open, re-read it.
- **The LFS budget is funded** (~$10 ≈ 50 GB as of 2026-08-12). The 512 MB per-change CI gate still
  applies, but you are no longer working against a hard cap. **This does not change M5** — commit
  the Python, leave the bulk art ignored.
- **M-task status check before you start anything new:** M1 (`RestorePartyAfterBattle` wiring) is
  the one that matters. It is the only item on this list that moves a completion gate.

---

## 0. Ground truth you must not re-verify

These are settled. Acting on them is correct; going to check them is scope creep (CLAUDE.md rule 4).

| Fact | Source |
|---|---|
| `curentMP` is a **real typo in the stock struct** `S_PlayerUnitData`, confirmed by live reflection. The library's spelling is correct. Only the **call-site wiring** remains. | `533352d8` |
| Damage-scalar sequencing is **PASS** — quoted call order verified. Do not re-audit it. | `78867a33`, `CLOSEOUT_SOURCE_VERDICTS_2026-08-11.md` |
| Melusina locomotion is fine — owner confirms she walks. | `62c7920d` |
| The 08-10 root cause was a **missing `BP_BattleController` in the level**, now placed in `L_KaleidoNave`. | `SESSION_CLOSEOUT_2026-08-10.md` |
| The route is **Morning → KaleidoNave**. Dreamstate is merged out; its `.umap` is preserved in `Saved/Recovery/DreamstateRemoval_2026-08-10/`. | closeout plan §Step 4 |
| Echo tools (`echo_run.py`, `record_gate.py`) are **canonical and present**. The "they were deleted" claim in older lane docs is a stale scare. | `AGENT_INFRASTRUCTURE_2026-08-11.md:65` |

---

## 1. Your tasks this afternoon, in order

### M1 — Wire `RestorePartyAfterBattle` (closeout Step 5) ← **highest value, unblocks nothing else but is fully yours**

The library is written and compiles; it has **zero callers**. That is the whole remaining gap.

- Hang `UMelodiaJRPGPostBattleLibrary::RestorePartyAfterBattle(BattleController)` off the proven
  battle-end path: `CompleteBattle` → `ResumeQuillOnce()` (exactly-once already confirmed).
- **Owner decision, already made:** heal only. No retry-on-defeat.
  `NotifyDeathRecovery` / `NotifyRetryRecovery` stay uncalled. Do not add them.
- Use `curentMP` as spelled in the stock struct when you touch the MP half. It is not a bug to fix.
- Header: `Source/BS_GodFile/Public/MelodiaJRPGPostBattleLibrary.h`.
- **Do not** open the Blueprint to do this if a C++ call site is available — one authority.

**Done =** the call site exists, the module builds, you said what you changed in three lines.

### M2 — Fix `lane_dispatcher.py` queue authority

`Tools/lane_dispatcher.py:23` parses `NEXT_ACTIONS.md` as the queue. That file is the **platform /
website** queue. The gameplay queue lives in `_VERTICAL_SLICE_SCOPE.md` and
`Docs/Handoffs/CORE_SYSTEMS_HANDOFF_2026-08-10.md`.

- Repoint `QUEUE` at the gameplay authority.
- Generate `Saved/dispatch_report.md` — it has **never** been generated once.
- Tool stays **READ ONLY**. Do not let it write to the tree.

### M3 — Rebuild the stale memory index

`Saved/memory_index.json` was built 13:46 on 08-11, before the tool-hardening commit and before the
quarantine. Its cache may still assert the "echo tools deleted" fiction.

```bash
python Tools/memory_index.py
```

### M4 — Split `AGENTS.md` under the 32 KB subagent cap

It is 35.6 KB and **truncates for every subagent that loads it** — including you. Extract the
working agreement into an included file and reference it. Keep `_AGENT_WORKING_AGREEMENT.md` as the
canonical text; do not duplicate the rules into two places that can drift.

### M5 — Commit the loose `surreal_arch` geometry work

The working tree has **13 untracked `deploy/surreal_arch/melodia_gn/` modules** plus 3 modified ones,
none of them committed:

```
aaa_quality.py  castle_extras.py  env_extras.py  geometry_extras.py  music_instruments.py
notation_extras.py  ornament_extras.py  pcg_integration.py  presets.py  ribbon.py
set_dressing.py  water.py  + Docs/     (modified: __init__.py, core.py, mesh_tools.py)
```

These are pure Python, no LFS, no budget risk. Commit them as one batch. **Leave the root scratch
scripts alone** (`check_bp*.py`, `fix_rhythm*.py`, `fix_var*.py`, `pie_*.py`, `pie_smoke_*.json`) —
they are session debris; propose a `.gitignore` line, do not delete files you did not create.

---

## 2. Hard boundaries

- **Do not push Content/LFS.** The 512 MB budget gate is real and LFS is metered billing.
  Your commits this afternoon should be Python, C++, and Markdown only.
- **Do not merge `recovery/melodia-main-sync-20260811`.** It is a stale cold snapshot that would
  revert the 08-09 quarantine and delete `.jcode`/`.opencode`. It exists as a backup. Leave it.
- **Do not touch** `.gitignore`, `.gitattributes`, `Config/DefaultEngine.ini`, `Config/DefaultGame.ini`,
  `Content/Materials/MF_MeshBlend_*.uasset`, `deploy/run_verify.ps1` without asking the owner.
  Note M5 asks you to *propose* a `.gitignore` line — propose, don't write.
- **Do not claim a gate.** `record_gate.py <id> pass` is not yours to run this session. Every gate
  left open needs the editor and real input, which you do not have.

---

## 3. Known host limitations (don't burn time rediscovering)

- OpenRouter key is **free tier**. Paid models 402 after the daily quota exhausts mid-day.
  TokenRouter (kimi) drops out sporadically. Free models are unaffected.
- Junie CLI headless is **broken on Windows** (`readPipedInput` IOException "Incorrect function").
  Interactive only. Do not script it.
- `video_review_lane.py` free-tier vision is broken — paid-model image input 402s. Text-only.

---

## 4. Report back with

Three lines per task: what changed, that it builds, and any single real thing you noticed.
Not a table. Not a plan for next time.
