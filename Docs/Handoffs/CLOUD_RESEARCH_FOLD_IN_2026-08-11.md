# Cloud/Linux Research Fold-In + Git Reconciliation — 2026-08-11 (evening)

**Session type:** git-state reconciliation + fold-in of research done by cloud/Linux agents that
could not reach the PC (SuperGrok, Cursor iOS cloud, Muse WSL, Junie, Mistral, Kimi, Nemotron,
DeepSeek fallbacks).
**Scope:** capture everything they learned, match it to the real tree, list every loose end and
remote branch, and record today's committed work. No editor/UE writes in this pass.

---

## 1. Git state vs local (verified this session, HEAD `69f76813`)

| Layer | State |
|---|---|
| Canonical repo | **`v2`** = `github.com/fromage3900/MelodiaMelusinaV2` (`main` tracks `v2/main`) |
| `main` | `69f76813`, **4 ahead** of `v2/main` (`533352d8`), 0 behind — no divergence |
| LFS pending push | 3 nebula texture blobs (`Blue_Nebula_8`, `Purple_Nebula_6/7`) — real content changes in `fb3b8297` |
| Working tree | **clean** of real changes after this session's commit (below) |
| Staged leftovers | 14 `MeshBlend/*.uasset` LFS pointers — **identical OIDs both sides, zero content change** (cosmetic re-mark); un-staged this session, not committed |
| `origin` / `melodia` / `legacy-origin` | point at the **website** repo (`MelodiaMelusina`, tip `950d2688`) — NOT the codebase |
| Second checkout `C:\EnvironmentPortfolio\MelodiaMelusinaV2` | **does not exist on disk** despite `GIT_LEFTOVERS_TRIAGE_2026-08-11.md` calling it the published V2 mirror — doc-reality drift, see §5.4 |

### Committed today (2026-08-11) — 24 commits `13717fb3..69f76813`

V2 repo migration (`13717fb3`, `2623f02a`), LFS pointer conversion for NotoMusic/assimp (`b598fb0a`),
V2 refresh + paths + push guard (`fd645ce3`), agent infrastructure — model_router/playtest_harness/
video_review_lane/memory_index/lane_dispatcher + Figma key redaction (`87b2938d`), closeout source
verdicts (`78867a33`), AGENTS §5 jcode swarm (`e3908f57`), jcode acceptance/study (`fedbda98`,
`cd257ee3`), CI V2 pipeline (`fbc1b178`), LFS pointer commit merge (`7ed886fa`), OpenCode/Muse lane
(`70803330`), UI transparency audit fix — invisible rhythm HUD text → opaque (`2770c0e9`), README V2
badges (`4a2a0555`), session handoff (`c6d932f1`), MCP count correction (`c868ece6`), portfolio blends
→ `Exports/PortfolioStages` (`17ac26ca`, `c0454177`), Step 5 HOLD resolved via live reflection —
`curentMP` typo is real in the stock struct (`533352d8`), mobile Metal flag + nebula textures +
cathedral handoff (`fb3b8297`), 33-asset mirror quarantined (`eb6ff433`), MUSE lane Done (`f1948852`),
and **this session's tool hardening (`69f76813`)**: input-node ENTRYISH + AssetRegistry discovery +
canonical live-path + named-graph reachability (bp_live_path, bp_sweep, echo_run, graph_reachability,
ui_lint).

---

## 2. Cloud/Linux research inventory (agents that could not reach the PC)

All read-only; sources are on disk. **No runtime evidence was produced by any of these lanes** —
they confirm the evidence standard, they do not replace it.

| Source | Lane(s) | What it says |
|---|---|---|
| `Saved/Intake/INTAKE_SYNTHESIS_2026-08-11.md` + `prompts/pA..pF` | Muse (A), Junie→Nemotron (B), Mistral (C), Grok→DeepSeek (D), Kimi→DeepSeek (E), Nemotron→DeepSeek (F) | 6-lane read-only fan-out, ~$0.0014. **Consensus:** runtime gate is THE blocker; input-path ambiguity (raw OnKeyDown vs Enhanced Input); HUD dual-writer; queue-authority mismatch; untracked Content push risk; Kimi's Q/W/O/P 6-key W→O hand-shift finding |
| `Docs/PhoneOps/{SETUP,INDEX,SCRATCHPAD,NORTH_STAR,BACKLOG,RECENT_STUDY}.md` | SuperGrok + Cursor iOS (`bc-019ff1ec`, source `mobile`) | SuperGrok wrote 5 planning docs under `/opt/cursor/artifacts` but did not push; Cursor recreated them in-repo. Site-truth = `wix/`; surreal loop v2.131; open PRs #80/#81/#55; Monolith skills inventory (18); `.junie`/`.kiro` scaffolds |
| `Docs/Reports/RECENT_CHANGES_AND_JCODE_STUDY_2026-08-11.md` | jcode/phone lane | V2 topology map; 2026-08-11 commit spine; agent-tools roster; jcode harness port note |
| `Docs/Reports/GIT_LEFTOVERS_TRIAGE_2026-08-11.md` | git lane | Authority checkouts table; cold-backup paths; LFS renormalization done; force-push to legacy `origin/main` deliberately NOT done |
| `Docs/Reports/jcode_swarm_acceptance.md` + `jcode_swarm_recipe_a.md` + `recipe_b_mpa/ppa` | jcode swarm | Recipe A PASS; Recipe B MPA/PPA partial (no single `recipe_b.md`); acceptance checklist filled |
| `Docs/Production/AGENT_INFRASTRUCTURE_2026-08-11.md` | infra lane | 5 new tools; **line 65: `echo_run.py`/`record_gate.py` remain canonical** — resolves Lane A/C/F's "deleted" scare (they were restored mid-session; docs written earlier said gone) |
| `Docs/Production/MUSE_CODE_LANE_2026-08-11.md` | Muse lane | WSL2 muse 0.1.0, auth `~/.config/muse/auth.json`, host re-verify PASSED |
| `Docs/Handoffs/CLOSEOUT_SOURCE_VERDICTS_2026-08-11.md` | opencode lane | Step 3 damage-scalar sequencing **PASS** (quoted call order); Step 5 **RESOLVED** (`curentMP` real); UI transparency audit **FIXED** |
| `Docs/Handoffs/CORE_GAMEPLAY_CLOSEOUT_PLAN_2026-08-11.md` | opencode lane | Four gates (`runtime` FAIL honest, `save_load`/`repeat_consume`/`package_launch` OPEN); Steps 1–9 |
| `Docs/Handoffs/SESSION_HANDOFF_2026-08-11_CATHEDRAL_RIG.md` | cathedral lane | **CORRECTION: rig prep ran against OLD `FinalUERig43`; current rig is `Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend` (`Melusina.001`, 120 shape keys, `character_rig` 1124 bones)** — all next steps target v22 |
| `Docs/Handoffs/ENVIRONMENT_BUILD_VALIDATION_2026-08-11.md` | setup lane | `validate_setup.ps1` 0 hard issues; Python suite 294 passed; static_gates=fail (12 drift, 10 shadowed, 239 dead-exec, 16 dup short names, AMBIGUOUS(2)) — **several of those findings are addressed by commit `69f76813`** |

---

## 3. Loose ends found by this reconciliation (owner decisions marked)

1. **`lane_dispatcher.py` reads the wrong queue.** It parses `NEXT_ACTIONS.md` as queue authority,
   but that file is the generic 5-pillar platform/website queue. The gameplay queue lives in
   `_VERTICAL_SLICE_SCOPE.md` / `Docs/Handoffs/CORE_SYSTEMS_HANDOFF_2026-08-10.md`. Consensus finding
   #4 (lanes A/C/F, verified by reading `lane_dispatcher.py:23`). Fix: point `QUEUE` at the gameplay
   authority or restore a gameplay queue header; regenerate `Saved/dispatch_report.md` (never generated).
2. **`Saved/memory_index.json` is stale** (built 13:46, before the tool-hardening commit and the
   quarantine; cache may still hold the "echo tools deleted" fiction). Rebuild with
   `Tools/memory_index.py`.
3. **`Saved/dispatch_report.md` missing** — never generated; see #1.
4. **Figma API key was public on v2** (in `Docs/Reviews/MCP_SURFACE_SCAN_2026-08-03.md`; redacted in
   the doc by `87b2938d`). **OWNER MUST ROTATE the live key at figma.com** and update root
   `.mcp.json`/`.opencode.json`. OpenRouter/TokenRouter/Muse keys verified NOT in v2.
5. **AGENTS.md 35.6 KB exceeds the 32 KB subagent delegation limit** (Muse warning, Lane A) — it
   truncates for subagents. Consider splitting the working agreement into an included file.
6. **`video_review_lane.py` free-tier vision is broken** — paid-model image input 402s on the
   free-tier OpenRouter key (Lane F + session). Use text-only or paid key; documented limitation.
7. **Q/W/O/P spatial layout risk** (Kimi, strongest single finding): W→O is a 6-key hand shift —
   timing-failure risk above ~1 note/sec. Do NOT redesign yet; test in Campaign 1 real-input first
   (intake recommendation #4).
8. **Kill-vs-re-prove runtime row** — resolved: keep the honest `FAIL` row, re-run harness, add
   `PASS` later. No history rewrite.
9. **`Docs/ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md` "missing"** — **RESOLVED**: the
   file exists on disk and in v2 root `13717fb3` and recovery tip. `RECENT_STUDY` claim was stale.
10. **`restore`-style commands remain catastrophic** — confirmed again by Lane F; do not run
    `git clean -fd` / `git checkout -- .` (bulk `Content/` untracked).
11. **Kiro locomotion bugfix spec (`.kiro/specs/melusina-jrpg-exploration-locomotion/`) — NEW
    loose end, verified on disk:** `BP_MelusinaJRPGCharacter` (the intended exploration pawn on
    `MelodiaIntegrationMap`) **does not walk**. Spec: restore the stock TurnBasedJRPG exploration
    control path, keep Melusina's presentation stack; evidence says animation replacement is NOT
    the fix (audit JSONs already rule that out). Interactive runtime evidence remains user-owned.
    This is gameplay-blocking and sits outside the four closeout gates — flag for the gameplay
    lane. (Companion: `Docs/GIT_BATCH_DISCIPLINE.md` exists on disk.)
    **RESOLVED 2026-08-12 (owner):** "she walks fine now" — locomotion is working in current play;
    the spec's premise (pawn doesn't walk) is stale. Keep the `.kiro` spec as archive; no action.

---

## 4. Remote/local branches from cloud agents — disposition

**All `origin/*` branches live on the WEBSITE repo (`MelodiaMelusina`), not the v2 codebase.** None
should be merged into v2 `main` without content review.

| Branch | Tip | Verdict |
|---|---|---|
| `recovery/melodia-main-sync-20260811` (local) | `2fce475a` | **Cold snapshot of old PC state** rebuilt from website `origin/main` + working tree. STALE vs v2: it would revert the quarantine, delete `.jcode`/`.opencode`/Echo workflows. Do NOT merge; keep as cold backup (owner may archive/delete) |
| `origin/cursor/phone-ops-docs-0e29` | `65bc9257` | jcode harness + PhoneOps docs — **content already ported to v2** (`78867a33`, `e3908f57`, `fedbda98`). Close/archive |
| `origin/cursor/setup-dev-environment-f49c` | `affd758d` | Cloud dev-env docs — superseded by `ENVIRONMENT_BUILD_VALIDATION_2026-08-11.md` on main. Review for unique content, then close |
| `origin/cursor/surreal-architecture-slices-{0287,23b0,50a4,518c,5f20,b618,f4dc}` | 2026-07-16 | Surreal loop spam; PRs #67–#79 closed duplicates, **#80 open** (`b618`). Website repo, not v2; triage #80 per `RECENT_STUDY` §1 |
| `origin/feature/touchdesigner-mcp-integration` | `0b0a55de` | Pre-V2 legacy; on website repo. Archive unless revived |
| `origin/fix-final-gaps` | `d3635b83` | Pre-V2 legacy (Material Maker subgraphs / surreal_arch); PR #55. Content review before any fold-in |
| `origin/fix-melodiacore-source` | `fe7b1da9` | **Already merged** into old main via PR #54 (`991d5be2`); v2 root snapshot includes MelodiaCore C++. Close |
| `origin/agents/sakura-petal-niagara-effects` | `16e4ec7e` | June-era; Sakura-adjacent (red line). Leave untouched |
| `melodia/main`, `origin/main` | `950d2688` | Website repo trunk — NOT the codebase. No action |

---

## 5. Actionable carry-forward (not done in this read-only reconciliation)

1. Push `main` → `v2/main` (4 commits) + the 3 nebula LFS blobs. GitHub `:443` has been flaky all
   day — retry, never force.
2. Fix `lane_dispatcher.py` queue authority (#3.1) and regenerate `Saved/dispatch_report.md`.
3. Rebuild `Saved/memory_index.json` (#3.2).
4. Update `GIT_LEFTOVERS_TRIAGE_2026-08-11.md` (remove the nonexistent `MelodiaMelusinaV2` mirror
   checkout row; note recovery-branch staleness).
5. Owner: rotate Figma key (#3.4); decide recovery-branch archive (#4).
6. Editor pass (one editor, Monolith 9316): re-run `bp_live_path /Game/.../BP_BattleUI --json` +
   scoped `bp_sweep` to prove `69f76813` clears the `ENVIRONMENT_BUILD_VALIDATION` AMBIGUOUS/dead-island
   findings — **probe/research only, never a `runtime` ledger row** (evidence standard §2).

---

## 6. Evidence-standard status (unchanged)

- `Saved/gate_ledger.json`: `runtime` = FAIL (honest row, 2026-08-11); `save_load`, `repeat_consume`,
  `package_launch` = OPEN. `Saved/Echo/state.txt` matches.
- No ledger row was added or changed by this reconciliation. Prose in this file is not evidence.
- The four closeout gates close only via real keyboard input through `BP_BattleUI::OnKeyDown`,
  process-restart save/load, and a Development-package launch, each with committed harness +
  assertion JSON (per `CORE_GAMEPLAY_CLOSEOUT_PLAN_2026-08-11.md`).
