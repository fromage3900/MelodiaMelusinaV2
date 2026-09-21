# BS_GodFile — AI Agent Rules (Auto-loaded by Claude)

**Front-door review:** 2026-09-14 against `origin/main` at `7edba5167bc0f17e73dfb9d55ef33fcb32c56d81`.

## 🛑 GIT PIPELINE LAW — BINDING (owner directive 2026-09-06; outranks everything in this file)

This is a PROFESSIONAL GAME PIPELINE, not an AI playground. Canonical authority is
`origin/main`, maintained on the desktop PC. This laptop clone is ONLY a Blender /
asset-prep / mobile hub — its local `main` must mirror `origin/main` exactly and never
diverge. No agent may create branches, commit, merge, rebase, reset, or push without
explicit owner permission for that specific operation plus a written plan stated first.
Never consolidate or restructure git history from this machine. Destructive commands
(`git reset --hard`, `git checkout -- .`, `git clean`, `git push --force`, any history
rewrite) are forbidden without explicit per-command owner approval. Long-lived laptop
asset work lives on `collab/laptop/longterm`. Verify read-only before and after any
approved mutation. Poor git management has already caused real regressions and missed
deadlines here — do not add to that history.

## ⛔ READ FIRST — [`_AGENT_WORKING_AGREEMENT.md`](_AGENT_WORKING_AGREEMENT.md)

**This is a working portfolio and a livelihood, not a technical sandbox.** When the owner asks for
something, they want the task done — not an analysis, a framework, or a discussion.

The five rules, in full, binding, outranking everything else in this file:

1. **Do the job asked. Ship it. Stop.** The request is the scope — not the request plus what you
   noticed on the way.
2. **Never add a mechanism to compensate for a problem.** If your fix needs a new property, flag,
   branch or corrective step whose only job is to cancel out something else, the fix is wrong.
   Delete the cause.
3. **When told to stop or remove something, remove it — fully, immediately.** "Kill it" means
   delete and rebuild. Not deprecate, not gate behind a flag, not leave a stub.
4. **Do not investigate what you have already been told.** The owner knows their own rig, assets and
   files. "The bones are correct" is ground truth. Act on it; do not go verify it.
5. **A fix request is not a review request.** If you spot something real while fixing, note it in
   one sentence at the end and move on.

**You are scope-creeping if:** you are three tool calls in and haven't changed the thing yet; you
are reading logs to confirm something the owner stated; you are writing a ranking or comparison
table for a one-line fix; you are proposing a design where the ask was a repair; you are spawning
a subagent for a task the owner scoped in one sentence; you are asking a multi-option question when
the blocker fits in one sentence with one question; you are updating a doc nobody asked you to update.
→ Stop, make the change, build it, report in three lines.

**The 2026-09-21 failure, so it is not repeated.** The ask was mesh placement and screenshots. The
session produced three Explore agents, a collision audit, a Jev capability investigation, a
four-option decision matrix and two doc rewrites — and almost no placement and no screenshots. Caution
became inaction, and inaction got written up at length instead of reported in a line. Finding that a
plan is wrong is a one-sentence report plus the next action, not a deliverable.

**Done = the change is made, it builds, you said what you changed.** Nothing else.

---

> This file is auto-loaded by Claude at session start. Read it before doing anything.
> **Status, queue, and where everything is: [`CURRENT_STATE.md`](CURRENT_STATE.md) — the only status document.**
> Sheep / Chladni / Nikki Cymatics work must also open [`Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md`](Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md).
> Do not create handoff, plan, receipt, or session-note files. Update `CURRENT_STATE.md` in the same commit as the change; everything else goes in the commit or PR message.

## ⏱ Read dates before you trust a doc

A doc's filename date is when it was **written**, not when it was last **true**. This project moves
faster than its documentation: `Docs/GAMEPLAY_REVIEW_2026-07-30.md` was wrong about the travel
system three minutes after it was saved, because the code landed immediately after. Before acting on
any doc claim that something is missing or broken, check the relevant source file's mtime.

---

## 🛑 NEVER Touch These Files

No AI agent may modify these without `SKIP_PROTECTION=1` or explicit human instruction:

| File | Why |
|------|-----|
| `.gitignore` | Protects 3.6GB+ of Blender autosaves and binary caches from being staged |
| `.gitattributes` | Controls LFS for all `.uasset`/`.umap`/`.blend` files — corrupting this breaks git |
| `Config/DefaultEngine.ini` | Shared engine config — wrong edits break all launch modes |
| `Config/DefaultGame.ini` | Game config — owner is MPA/WIA only |
| `Content/Materials/MF_MeshBlend_*.uasset` | Core material functions used by the Universal master |
| `deploy/run_verify.ps1` | The SQA gate — modifying it bypasses all safety checks |

**Before touching `Config/` or `Content/Materials/`: ask the user.**

---

## 🔴 Check These Before Writing Anything

1. **Loop STOP files**: If any of these exist in `deploy/`, NO agent may write to `/Game/EnvSandbox/`:
   - `deploy/SURREAL_ARCH_LOOP_STOP`
   - `deploy/SURREAL_TIERB_LOOP_STOP`
   - `deploy/SURREAL_WORLD_LOOP_STOP`
   - `deploy/AGENT_LOOP_STOP_*`

2. **GPT may be actively working** on `Content/Melodia/Characters/` and `Content/Python/`. If git status shows those files modified, coordinate before writing to them.

3. **Editor crash traps (found 2026-09-21 — each one cost a live editor).**
   - **Source control must stay `Provider=None`** (`Saved/Config/WindowsEditor/SourceControlSettings.ini`).
     With `Git`, the editor runs `git add` on every `asset_move`, hits `.gitignore`, and throws
     `FATAL: SEH exception 0x00004000`.
   - **Never call `asset_fixup_redirectors`.** Hard-crashed the editor, no log flush. Redirectors are
     harmless; leave them.
   - **Test one asset move end-to-end before batching.** `/Game/` paths derived from *filenames* are
     wrong where filename ≠ asset object name, and a batch turns that into N failures.

4. **Do NOT execute `Saved/Audit/mesh_reorg_execution_plan_2026-08-30.md`.** Its merge premises were
   measured false on 2026-09-21: Greybox_Kit 94 colliding names / 0 identical, Library 254 / 0,
   `_PROJECT` 134 shared with only 7 identical. No side is authoritative and `Content/EnvSandbox/*`
   is gitignored, so a merge destroys content with no git undo. Evidence:
   `Saved/Audit/mesh_merge_collisions_2026-09-21.json`. Canonical `_PROJECT` is `/Game/_PROJECT/`.

5. **Jev ranks authored options; it cannot audit a level.** No Unreal import, no `--level` argument.
   Verify the `source` field is `jev-live` / `jev` — `TYPESAFE_API_KEY` is set at User scope but is
   not inherited by every shell, and a missing key returns a confident `classical-fallback` with no
   log line. That is not Jev evidence.

6. **Use Standalone PIE, not Client.** `UClaireonSettings::DisabledPIENetModes` is set in the C++
   constructor, so **every rebuild re-disables Standalone**. Re-apply after any build — the one-line
   command is in `CURRENT_STATE.md` §3 (2026-09-21). In Client mode Claireon cannot see
   `BP_BattleController_C` or the player character at all, and `BP_JRPGPlayerController` throws two
   `Accessed None` that are net-mode artifacts, not bugs.

7. **Melusina renders start from the canonical state**, not from scratch:
   `L_MelusinaPortfolioCapture` + `CAM_Melusina_BeautyFront34` + the corrected-shoulder capture clip
   (`A_Melusina_BowAttackV2_PortfolioShoulders` as a dynamic montage on `DefaultSlot`), **not**
   `AM_Melusina_BowAttack_Bound`, which carries the hiked shoulders. Her front is **-X/+Y**. Full
   detail and the wardrobe/hair fixes are in `CURRENT_STATE.md` §3 (2026-09-21) — read it before
   touching her presentation, and do not re-derive findings recorded there.

---

## 🧪 `MelodiaIntegrationMap` — THE test level. Do not break it.

`/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` is **the** integration/test level: everything
in one place so Echo-pipeline tests are cheap to run. Battle controller, player/enemy spawn sets,
NPC/shop/forge/shrine/chest/save-point interactables, encounter + traversal-gate + portal +
state-anchor fixtures, the PCG hero music host, a parked Oceanology ocean, and the debug cameras all
live here **on purpose, together**. Its clutter is the feature — that is what makes one PIE run
exercise the whole pipeline.

Rules:

- **It is usually the level open in the editor.** If you query Monolith / `it-is-unreal` and get
  `MelodiaIntegrationMap` back, that is expected — it is not a stale or wrong level, and it is not an
  invitation to load a different map. Do not `load_level` away from it without asking; PIE teardown
  is async and load-straight-after-stop crashes the editor (`SESSION_CLOSEOUT_WATER_MATERIALS_2026-08-29` §5.4).
- **Do not "clean it up."** Do not delete the duplicate cubes, the spawn-point spheres, the
  TextRenderActors, the multiple `BP_Camera*` actors, or the parked
  `OceanologyInfiniteOcean` at Z −5000 ("Melodia Integration - Oceanology Ocean (parked z-5000)").
  They are test fixtures, not debris.
- **Additive only.** Add a fixture if a test needs one; do not reorganise, rename, or re-lay-out what
  is already there. Other tests reference these actors by name/label.
- Per-monolith art levels (`LV_SeaAbove_Prototype`, `L_MelusinaMorning`, `L_SakuraPath`, …) are where
  *look* is authored. `MelodiaIntegrationMap` is where *systems* are proven. Do not mix the two jobs.

---

## 🏗️ Agent Ownership — RETIRED

**Decision 002 (2026-07-26) retired the 5-agent ownership model.** This is a solo project; the
PGA/MPA/PPA/WIA/SQA boundaries and the "no cross-owner writes" rule no longer apply.
`AGENT_BOUNDARIES.md`, `AGENT_OPERATING_MODEL.md` and `AGENT_OWNERSHIP.md` were removed in the
2026-09-10 docs collapse; recover one with `git show 7d271c15:<path>` if you need its tool-capability
notes. None of them is process.

The constraints that *do* still bind are specific and asset-named: the never-touch table above,
Decision 021's three content-reference cleanups, and `L_SakuraPath` art direction (human-owned).
Do not apply the retired general rules on top of those — that is how work that is actually
permitted gets talked out of.

---

## 🟢 Green (Do Freely)
- Read any file, generate reports, update non-destructive docs
- Run existing audit scripts (read-only output)
- Generate manifests and research briefs

## 🟡 Yellow (Do With a Report)
- Run material/look-dev loops — must write a `Saved/Audit/` report
- Generate PCG graph changes — must not alter Sakura level content
- Update `CURRENT_STATE.md`

## 🔴 Red (Ask First)
- Delete or move `.uasset` files
- Modify master material architecture
- Change `L_SakuraPath` or `L_MelusinaMorning` content
- External publishing
- Destructive cleanup of any kind

---

## Project Overview (Quick Context)

**Environment Portfolio** — Surreal/Zen/Baroque/Sakura environment art in **Blender 5.2** + UE5.8.
**Pipeline**: Blender → world.json manifest → UE import → PCG scatter → Material masters → Portfolio captures.
**Melodia/Melusina** — an authored rhythm-JRPG with a working Quill → Phoenix/JRPG → rhythm → typed-result
core, Wardrobe/traversal hooks, music-key world progression, and a renewable Chapter/content layer. The
procedural tools author world/content variation; they are not a second gameplay authority.

> **Blender version:** 5.1 is **not installed** — that directory is empty. Only 4.3, 4.5 and **5.2**
> have executables, and the full addon set (including Melodia Studio / `surreal_arch`) runs on 5.2.
> Docs that still target 5.1 — notably `Docs/MELODIA_STUDIO_SHIP_CHECKLIST.md` and the default in
> `sync_surreal_to_live.ps1` — describe steps that cannot currently run.

**Current focus and queue:** [`CURRENT_STATE.md`](CURRENT_STATE.md) §4.

**Agent tooling — Unreal MCP surfaces.** They are registered in the workspace-level
`C:/EnvironmentPortfolio/.mcp.json`, not in this repo's `.mcp.json` (which lists only `agent_bridge`,
`claireon` and `melodia`). Verified 2026-09-14:

| Server | Transport | Shape | Enabled by default? |
|---|---|---|---|
| `monolith` | `Plugins/Monolith/Binaries/monolith_proxy.exe` → port 9316 | ~1,426 actions in 24 namespaces (`blueprint_query`, `editor_query`, `material_query`, …): full graph read, the verification loop (`get_graph_fingerprint`, `assert_graph_matches`), atomic T3D authoring (`validate_nodes_t3d`, `inject_nodes_t3d`, see MONOLITH_GUIDE Recipe 16), `run_python` | Yes |
| `ueblueprintmcp` | Python venv (`Plugins/UEBlueprintMCP/Python/venv`) → TCP port 55558 | ~60 tools: Blueprints, graph nodes, event dispatchers, Enhanced Input (Input Actions/Mapping Contexts), materials, UMG, editor control | **No — deliberately off** |

`it-is-unreal` (VibeUE, port 8088) is gone: the plugin is not in `Plugins/` and no `.mcp.json`
registers it.

`ueblueprintmcp` is registered so it's one line away from live, but not enabled.
It's a 9-commit, 36-star third-party plugin (`zolnoor`) with no audit history, and its ~60 commands
substantially overlap the two surfaces already enabled — installing it live-by-default would be a
third authority over exactly the graph-mutation surface this project has spent real effort
consolidating onto one owner (Decision 025's own reasoning, extended). Enable it deliberately, for a
scoped task, when its Enhanced Input command set covers something Monolith's `set_node_property`
doesn't. **Requires a closed-editor build first** — it's a new plugin module with reflected types
(`UCLASS`/`GENERATED_BODY`), so Live Coding cannot register it; only a full `Build.bat` pass with the
editor closed does.

Prefer Monolith where more than one surface can do the job. **Never run two surfaces against the
same graph in one session** — this applies to every surface.

Both need the editor running. Monolith additionally cannot answer while a modal dialog blocks
the game thread — grep the log for `MODAL_OPEN` before assuming the plugin is at fault.

**MCP servers load at session start.** Editing `.mcp.json` mid-session does nothing until the
session is restarted — check what you actually have before promising editor work.

**Current gameplay authority (verified 2026-09-14 against `origin/main`)**: QuillScript is the narrative
authoring authority; `UMelodiaNarrativeSubsystem` is its runtime bridge for authored facts, consequences,
checkpoints and exactly-once progression transactions. TurnBased JRPG / Phoenix owns party, turns, skills,
targeting, action resolution, damage, terminal results, inventory and stock gameplay saves. Rhythm executes
on the selected JRPG action and returns grade/performance data; Wardrobe owns owned/equipped fashion state
and its existing traversal/battle/rhythm/Convergence capability hooks. One writer owns each UI/audio surface.
MelodiaCore remains integration/presentation-only; ACFU and Conversation2D are excluded. The scoped battle,
grade-to-damage, Wardrobe and music-key seams are evidence-backed in `CURRENT_STATE.md`; packaged golden-run
and long-chain persistence proof remain separate open gates.

**Content-first rule:** before changing architecture, ask whether the requested experience can be authored
through `CURRENT_STATE.md` → `PROVEN CREATIVE CAPABILITY SURFACE`. If yes, author the boss, side quest,
rhythm skill, creature episode, outfit ability, musical puzzle, or procedural setpiece through the existing
entry points. Architecture work requires a demonstrated content blocker. Do not reopen old rig or system work
without current evidence of a blocker.
