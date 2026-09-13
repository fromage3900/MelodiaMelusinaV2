# Melodia Melusina — Current State

**This is the only status document.** If any other file states what works, what is open, or what
to do next, that file is wrong: fix this one instead. Update it in the same commit as the change it
describes. Handoffs, plans, receipts and session notes go in the commit or PR message, never in a
new file.

**Updated:** 2026-09-12 · **Engine:** UE 5.8 · Blender 5.2 LTS · C++20 · Python 3.11
**Pre-collapse docs:** every deleted handoff/plan/report is recoverable with
`git show 7d271c15:<path>` (tag `docs-precollapse-2026-09-10`).

---

## 1. What the game is

A solo rhythm-JRPG. QuillScript owns narrative; the TurnBased JRPG template owns party, turns,
damage, inventory and saves. Rhythm timing rides on top of JRPG commands, outfits grant traversal,
and played phrases unlock the world. Shape: OMORI. Music-as-key: Zelda. Wardrobe bar: Infinity
Nikki. Architecture detail: [`SYSTEM_MAP.md`](SYSTEM_MAP.md), [`DATA_FLOW.md`](DATA_FLOW.md).
Settled decisions: [`_DECISION_LOG.md`](_DECISION_LOG.md).

---

## 2. What works — and how strongly it is proven

Evidence ladder (never collapse levels): SOURCE BUILT → LIVE PROVEN → RESTART PROVEN →
PACKAGED PROVEN.

| Capability | Level | Evidence |
|---|---|---|
| Editor build | SOURCE BUILT | Game + `MelodiaCore` DLLs rebuilt 2026-09-12 21:55 by a Codex UBT run from the local `cleanup/pbr-twin-landing-2026-09-10` working tree — not from `main` |
| Music node → `reward.first_resonance_echo` → Accessories auto-equip → Glide → portal unlocks | LIVE PROVEN 2026-09-01 | `Docs/Evidence/P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md`, `Saved/Audit/p0_real_input_run/` |
| Wardrobe save → full editor restart → load → outfit restored | RESTART PROVEN 2026-09-01 | slot `P0_Shorewake_Validation`, `LOADED_NARRATIVE_RESTORED` |
| Battle outcomes (victory / defeat / fled / unavailable) return a typed result; Quill resumes exactly once | LIVE PROVEN 2026-08-27 | `MelodiaIntegrationMap`, `MelodiaQuillSmoke` |
| Rhythm grade (Q/W/O/P) scales stock JRPG damage | LIVE PROVEN (owner PIE 2026-08-12/13) | `FMelodiaRhythmGradeBoundaryTest` |
| Audio reactivity on every level | LIVE PROVEN | `b1cac649`; music clock on the GameMode `5fea50c8` |
| Packaged Development route, both legs, 0 fatals | PACKAGED (bounded) | builds at `G:\melodia_packages\P0_Closeout_20260902\`, `P0_Route_20260903\`; not a golden-run certification |
| Starskiff board / move / disembark | LIVE PROVEN (PIE) | `AMelodiaStarskiffPawn` — stabilize only |
| Resonance Ecology PCG enrichment (decision 057) on Sea Above biome graphs | LIVE PROVEN 2026-09-12 — 1 of 9 graphs | #196, #198, #203; `PCG_East_PhyllotaxisCourtyard`: 140 instances, 1 per-instance custom float, Resonance 0.030–0.925. `Content/Python/pcg/apply_resonance_to_sea_above.py` applies it to the rest |
| Choral Sheep on the approved Nikki Cymatics path | LIVE PROVEN 2026-09-12 | `MI_ChoralSheep_Body` → `M_Master_Toon_Character` with `T_Chladni_C_ROOT`; child `MI_ChoralSheep_Body_Chladni_C` |
| Choral Sheep Harmonize → fleece | SOURCE BUILT 2026-09-12 | `AMelodiaChoralSheepActor::Tick` writes `CurrentHarmonizeWeight` into `HarmonizeActive` on a slot-0 MID (`2d1f8b49`); not yet captured |
| Shorewake dress on Melusina's 465-bone skeleton | owner-confirmed fixed 2026-09-02 | `SK_ShorewakeDress_Melusina465`, `MI_Melusina_Dress_Shorewake`; not yet captured in-game |

**Active P0 gates — 8/8 pass:** `rhythm_owner`, `hud_single_writer`, `rhythm_grade_to_result`,
`wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`, `music_world_key`, `static_gates`,
`battle_integration_map`. Ledger rows live in local `Saved/gate_ledger.json` — append-only, read
the **latest row per gate id**. The Aug 13–14 `runtime` / `save_load` / `repeat_consume` /
`package_launch` passes apply only to that baseline.

Automated tests: 524/524 at the 2026-09-01 captured revision (that total includes tooling suites —
MCP regression, Ollama daemon stress — not only game tests).

---

## 3. Open

- **Issue #51 — long-chain persistence.** Outfit → Starskiff → encounter → rhythm → Convergence →
  reward → save → quit → relaunch → load → load again, with no duplication. Refresh from current
  `main`; do not merge stale PR #54 wholesale. Audit `RestoreNarrativeRecord*` for partial mutation,
  add repeat-load equality tests, and separate durable vs derived Starskiff/Convergence state before
  any save schema v6.
- **Packaged golden run** of `specs/p0/core_p0_dream_golden_run.v1.json` — not certified.
- **Allowlist is relaxed in editor builds** (`bRelaxedAllowlistInEditor`); run one pass with it off
  before any packaged demo.
- **Owner decision:** retire vestigial `melodiaBattleUI` / `MelodiaUI` vars on `BP_BattleController`.
- **Audio reactivity gap:** `M_Master_Toon_Universal_Alpha` has none of the 14 `Cymatic_*`/`Audio*`
  params, so its 109 instances (incl. Melusina `SW_Dress_P01..P48`) cannot react.
- **Sea Above look-dev:** `W_Glacier_Rock` is a near-black Gaea export (re-export); an unidentified
  writer rewrites `MI_Glacier_Landscape_Layered` weights. Pin Ultra Dynamic Sky before trusting any A/B
  capture on `LV_SeaAbove_Prototype`. Measured 2026-09-12: 11 bounded PCG volumes (largest 83×15×17 m),
  not four giant ones. `PCG_East_AtlantisGrove2` is an exact duplicate of `PCG_East_AtlantisGrove`
  (same transform, seed 42, all 193 instance transforms) — delete it. PCG regenerate + save leaves the
  previous generation's spawned actors on disk: `ResonanceCathedral Music Node0–11` exists three times,
  and the 09-01 set is referenced by no volume on `main` or any branch.
- **Choral Sheep deformation is unverified in UE.** `BP_ChoralSheep` has no AnimClass. The six takes
  (Idle/Walk/WalkSlow/Run/Jump/Death) are now baked onto the canonical export skeleton offline
  (2026-09-13, `deploy/blender/choral_sheep_bake_takes.py`) and verified through an FBX round trip:
  rest and motion within 0.006 mm / 0 deg on all 117 bones, every take moves. The FBXs are local only in
  `Saved/Audit/choral_sheep/bake_canonical_2026-09-13/`. Remaining: import onto
  `SK_ChoralSheep_Skeleton`, give `BP_ChoralSheep` an AnimClass, capture. Source: the 474-bone ARP
  control rig in `Saved/Audit/choral_sheep/choralsheep_Takes_v4_20260910.blend` (local only).
  UE `SK_ChoralSheep` is the 550-vertex `ChoralSheepARPExport.fbx`, not the 1,000-vertex
  `...FINALCANON...fbx`; both share an identical skeleton, so the takes fit either.
- **`cleanup/pbr-twin-landing-2026-09-10` resurrects the docs collapse.** Its snapshot `673a5ddf`
  re-adds 830 of the 840 files `08a608bc` deleted, including `Docs/Career`. Never merge it wholesale;
  promote its real work (MK39 skiff GN, Sea Above external actors, HUD tokens) in scoped PRs.
  `Docs/Career` also sits on ~37 remote branches and in `main`'s history; purging it needs an
  owner-approved history rewrite.

---

## 4. Owner queue — now

**Thesis:** Creature → Motif → Harmony → World. **Semester (Humber Fall 2026):** First Dream is the
stable technical proof (protect and polish only). Shorewake Calling is the semester artwork.
Choral Sheep is the capstone lane.

1. **Choral Sheep UE proof.** Verify deformation; bind one C-root fleece response on the approved
   Nikki-derived Cymatics path (`MI_ChoralSheep_Body` → `M_Master_Toon_Character`, Chladni as a
   child, not a replacement shader); capture REST → ROOT_C → hit → REST. Visual lock: Board 06 +
   the two WebPs in `Docs/References/VisualBoards/2026-09-08/ChoralSheep/`. Context:
   `Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md`.
2. **UE ↔ TD proof.** One real OSC `:9000` and/or Spout connection. Do not rebuild the TD scene.
3. **One 5–10 s AE sequence** — Creature → Motif → Harmony → World. Only then promote to the site.

Then: the 3–5 minute playable Shorewake route (`Chapters/02_shorewake_calling/`), then Issue #51.

**Task filter:** a task must produce a graded Humber deliverable, a visible portfolio improvement,
or remove a real blocker to one of those (`Docs/Semester/FALL_2026_ACADEMIC_MATRIX.md`).

**Not now:** git archaeology, new frameworks or second authorities, website redesign (showcase soft
freeze since 2026-09-07), research sweeps, status-doc campaigns. Oracle / Thirteenth Note
(`Docs/Strategy/ORACLE_*`) is a gated end-of-semester stretch.

---

## 5. How progress is measured

Playable minutes and captured proof — not gates, commits, or documents. As of 2026-09-10 the
authored QuillScript is 16 `.qsc` files, about 500 lines, several of them smoke tests. A session
counts if it adds playable or presentable minutes, or removes a real blocker.

---

## 6. Where things are

| What | Where |
|---|---|
| Game (this repo, **private**, no licence file) | `fromage3900/MelodiaMelusinaV2`, local `C:/EnvironmentPortfolio/BS_GodFile` |
| Website (**public** — serves GitHub Pages; owner decision 2026-09-12) | `fromage3900/my-site` |
| TouchDesigner / AE (private) | `fromage3900/MelodiaTouchDesigner`, `C:/MelodiaTouchDesigner/td/grandmaster_melodia/` |
| AI token treasury (revenue sidecar) | my-site `tools/fromage-webgl-kit/TREASURY_LEDGER.json` — 0 entries, first gate 0/5; never displaces the capstone |
| `C:/EnvironmentPortfolio/` | workspace folder only; its root Git repo is retired |

**The game repo is private; `my-site` is public.** Never commit personal, school, career, or client documents to either.

- **Route maps:** `/Game/Melodia/Levels/Opening/L_MelusinaMorning` →
  `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype` →
  `/Game/EnvSandbox/Environments/L_KaleidoNave`; menu `/Game/Melodia/Levels/Menu/L_MelodiaMainMenu`.
- **Systems test level:** `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` — additive only.
- **Workstations:** Humber lab = primary interactive; home PC = render/bake worker
  (`deploy/render_worker.ps1`); ASUS laptop = auxiliary. `main` is the shared baseline.
  `collab/laptop/longterm` is the laptop Blender/GN lane — never wholesale-merge or delete it
  (`Docs/Production/BRANCH_WORKSTATION_POLICY.md`).
- **Packaging:** cook to `G:` (C: lacks space). `Config/DefaultGame.ini` `MapsToCook` is correct —
  omit `-map=`.
- **Git health:** `python Tools/git_ok.py` — if it prints OK, Git is not the task.
- **Art references:** `Docs/Art/VISUAL_REFERENCE_INDEX.md`. Melusina House GN:
  `MELUSINA_HOUSE_GN_START_HERE.md`.

---

## 7. Traps that keep costing sessions

- **Stale DLL.** Compare `Binaries/Win64/UnrealEditor-BS_GodFile.dll` mtime against the source
  before trusting any PIE result.
- **One editor, one MCP writer** (Monolith port 9316). A second editor logs to
  `Saved/Logs/BS_GodFile_2.log`.
- **Background agents.** OpenCode in Rider (runs a git MCP server), Hermes, and the Melodia
  scheduled tasks (disabled 2026-09-10) have switched branches and committed mid-merge. Check
  before any editor or git work.
- **Material instance writes** need `update_material_instance()` to reach the renderer.
- **Never `load_level` straight after stopping PIE** — teardown is async and crashes the editor.
- **Codex desktop drives the editor too.** `ChatGPT.exe` → `codex.exe` holds its own
  `monolith_proxy.exe`, loads maps, saves, runs `Build.bat BS_GodFileEditor` against an open editor and
  restarts it. `ListAgents`/`SendMessage` do not reach it. Check `monolith_proxy.exe` parents and a
  running `UnrealBuildTool.dll` before closing, rebuilding or PIE-driving.
- **Read-only flags keep coming back on content.** `L_MelusinaMorning.umap` and the Sheep MIs were
  read-only; editor saves fail with "because the file is read-only!". The re-applying source is unknown.
- **Monolith `run_python` cannot sleep** — `time.sleep` is intercepted and PCG `generate()` is async, so
  instance counts read in the same call race generation.
- **Headless Blender hangs on user add-ons** — pass `--factory-startup` for `-b` inspection/bake runs.

---

## 8. Keeping this healthy

**Docs.** This replaces the front-door contradiction checker: one status document cannot contradict
itself.

- A change that alters project status updates this file **in the same PR** (PR template checkbox).
- No new handoff, plan, receipt, scorecard, or session-note files. That narrative belongs in the
  commit or PR body, where it is already dated and attributed.
- A new doc is only for durable reference — pipeline, contract, spec, runbook, bible, research.
  Name it for what it teaches, not for the day it was written.
- Monthly: re-read §2 and §3 against the current build. Delete any claim you cannot point at
  evidence for. Nothing is lost — `git show 7d271c15:<path>`, tag `docs-precollapse-2026-09-10`.

**Git.** `python Tools/git_ok.py` first; if it prints OK, git is not the task. One branch per
reason, named per `CONTRIBUTING.md`. Never let a background agent commit on your behalf — check for
OpenCode (Rider) and Hermes before editor or git work.

**CI.** The doc-policing steps are gone: `repo_governance_guard.py` and `front_door_health.py`
existed to cross-check front-door docs against each other, which a single document cannot fail. PR
CI still runs the protected-asset guard, the echo manifest, the offline contract suites, and the
health scorecard.

**Hygiene.** This repo is private and `my-site` is public. Personal, school, career, and client
documents live in local-only `C:/EnvironmentPortfolio/_offgame/` and never in either repo.

**Weekly, ten minutes:** is §2 still true, is §4 still what you are actually doing, does `git_ok`
pass, and did anything get written this week that should have been an edit to this file?
