# Gemini — Project Health + Documentation Handoff (2026-08-06)

**Date:** 2026-08-06
**Lens:** Project health, tooling accuracy, and documentation truthfulness
**Repo:** `C:\EnvironmentPortfolio\BS_GodFile` (UE 5.8, branch `main`)

## Guardrails (read before continuing)

- Read `AGENTS.md` + `_AGENT_WORKING_AGREEMENT.md` first — the working agreement outranks everything.
- Static graph/asset inspection is NOT runtime proof. PIE is the only runtime authority.
- Do not verify the owner's statements about their own rig, assets, or files — they are ground truth.
- Do not add mechanisms to compensate for problems; delete the cause.
- No commits, no pushes (push to `origin` is blocked anyway), no git history surgery.
- Do not touch the UE editor, Monolith, any `.uasset`/`.umap`, gameplay code, or `.mcp.json` content.

## Done 2026-08-06

1. **Fixed `Tools/bp_regression_checker.py`** — `MONOLITH_URL` changed to `http://localhost:9316/mcp`;
   every POST is now wrapped in the JSON-RPC envelope
   `{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"blueprint_query","arguments":{...}}}`;
   response parsing unwraps `result.content[0].text` then `json.loads`. Public API + CLI preserved
   (`fetch_fingerprint(asset_path, mode)`, `compare_fingerprints`, `DEFAULT_BPS`, `--all`,
   `FINGERPRINT_FILE`). Verified: `python -m py_compile` passes. Also fixes the CI `verify` job's
   first step (now moot — see task 5).

2. **`_VERTICAL_SLICE_SCOPE.md`** — added a `> **Corrected 2026-08-06.**` blockquote inside the
   "Proven now" section (after the bullet list, before "Foundation gate"): per the owner's 2026-08-06
   live verification the bullets are NOT currently reproducible (Quill dialogue not visible, battle
   non-functional, game unplayable); known-good state predates the Melodia integration + UI overhaul;
   all bullets re-tagged unverified until PIE proof. Bullets left untouched.

3. **`_TASK_QUEUE.md`** —
   a. Input-context row corrected: consumers ARE wired as of 08-04
      (`MelodiaQuillPresentationWidgets.cpp:115-117` pushes Dialogue context,
      `MelodiaAudioReactivePresentationSubsystem.cpp:78-82` pushes/pops Battle context,
      `MelodiaTraversalComponent.cpp:18`, `MelodiaTravelSubsystem.cpp:137`,
      `MelodiaSaveSlotLibrary.cpp:220` consume it). Status stays Done; open item is runtime
      push/pop balance verification, not wiring.
   b. Two new rows at the top of the Active Tasks table: Phase-0 snapshot
      (`CompatibilityLabs/Snapshot_2026-08-06`) = Done; Phase-1 bisect intake (static forensics of
      Quill + battle legs) = In Progress.
   c. New `State updates — 2026-08-06` block: migration count 5/23 → 4/23
      (`Saved/T3D/LIVE_VS_CATALOG_2026-08-06.md`); 22/23 widgets drifted 2x–4x (owner-confirmed
      intentional, Figma-sourced Melodia textures); `melodia_ci.yml` removed; `.mcp.json` untracked
      (API-key leak).

4. **`AGENTS.md` + tool references** —
   - `Tools/t3d_blueprint_injector.py` top docstring rewritten: it claimed a copy_nodes/template-BP
     flow that no longer exists; now documents the single-transaction
     `build_blueprint_from_spec` injection (library, no CLI).
   - `AGENTS.md` Core Tools table: `bp_regression_checker.py` row notes the 2026-08-06 JSON-RPC
     `/mcp` envelope fix; additionally corrected two demonstrably wrong entry points found while
     checking all rows: `pie_smoke_runner.py` (`run_pie_smoke`/`poll_pie_smoke` → `PieSmokeRunner.run()`
     / `main()`) and `regression_suite.py` (`RegressionSuite.run()` → `run_suite()`).
   - `fix_onbattlecompleted.py` references fixed to the real path + purpose: it lives at
     `Saved/T3D/fix_onbattlecompleted.py` and is a read-only diagnostic (guard-only, never mutates).
     Touched: `48H_CHANGE_REVIEW_2026-08-05.md:48` ("editor wiring helpers" → read-only diagnostics)
     and `_AUDIT_2026-08-05.md:74` (path + purpose appended).

5. **`.github/workflows/melodia_ci.yml`** — copied to `CompatibilityLabs/Snapshot_2026-08-06/melodia_ci.yml`
   (preserved for rebuild), then the original deleted. Why it cannot pass: `Plugins/Monolith/Binaries/`
   is gitignored (0 tracked files — the proxy is not in the repo), `windows-latest` has no UE 5.8
   editor, and job 1 (`verify`) invoked the then-broken `bp_regression_checker` against a Monolith
   that could never start. Rebuild spec: self-hosted runner with UE 5.8 + committed Monolith
   binaries, or drop CI until then (owner decision — below).

6. **`.mcp.json` (committed API-key leak)** — `.mcp.json` added to `.gitignore`; `git rm --cached
   .mcp.json` run (staged for deletion; the working file is untouched and keeps the owner's MCP
   config live). Verified: `git status` shows `D  .mcp.json` + ` M .gitignore`. Key strings remain in
   git history — history cannot be scrubbed safely on this repo (object storage was historically
   damaged; no rewrite). **Both keys must be rotated by the owner.**

## Owned by owner (action items)

1. **Rotate both `.mcp.json` API keys** (deepseek-v4 + kimi-k3). The file is untracked from now on,
   but the old keys are public in git history. Rotate at the provider, then update `.mcp.json`
   (it remains gitignored forever).
2. **CI decision:** rebuild `melodia_ci.yml` on a self-hosted runner with UE 5.8 + committed
   Monolith binaries, or drop CI entirely until such a runner exists. Snapshot of the removed
   workflow: `CompatibilityLabs/Snapshot_2026-08-06/melodia_ci.yml`.
3. **Confirm the 08-04 battle-widget reparent was intentional.** Owner previously said yes if the
   reparent replaced the stock UI — record that confirmation in `_DECISION_LOG.md` so the 22/23
   widget drift (2x–4x scale/position) stays classified as authored work, not regression.

## Next health tasks for Gemini (ranked)

1. **Fix stale `DOC_INDEX.md`** — it still counts "011" docs; the real count is higher
   (`_AUDIT_2026-08-05.md:94` flags this). Re-scan `Docs/` and refresh the count/index.
2. **Update `CURRENT_STATE.md`** — dated 2026-07-02, badly stale; sync to the 2026-08-06 reality
   (unplayable loop, bisect in progress, snapshot taken).
3. **Purge remaining `G:\` path references** in `.opencode.json` / configs (Decision 025 area) —
   the G:→C: migration left stragglers.
4. **Reconcile `48H_CHANGE_REVIEW_2026-08-05.md`** "5/23 migrated" text with the corrected 4/23
   (`Saved/T3D/LIVE_VS_CATALOG_2026-08-06.md`).
5. **`AGENTS.md` pipeline table sweep** — this session already fixed 3 stale rows (bp_regression_checker
   note, pie_smoke_runner, regression_suite entry points) and the `t3d_blueprint_injector.py` docstring;
   also note the "CI/CD Pipeline" section (`.github/workflows/melodia_ci.yml`) is now dead —
   replace it with the rebuild-or-drop decision outcome.
6. **Verify `Docs/Handoffs/CLINE_MONOLITH_COMMANDS_2026-07-31.md`** command list against the
   `/mcp` JSON-RPC envelope (raw URL → `http://localhost:9316/mcp`, unwrap `result.content[0].text`).
7. **Task-queue hygiene** — wallet restart-idempotence test and the remaining foundation gates stay
   `Available` (unchanged, just confirm no stale statuses elsewhere).
8. **Portfolio docs** — unaffected this session; leave alone.

## Explicitly out of scope for Gemini

- Any editor/Monolith mutations, `.uasset`/`.umap` edits, or gameplay code changes.
- Commits, pushes, or any git history surgery (push is blocked; history is not scrubbed).
