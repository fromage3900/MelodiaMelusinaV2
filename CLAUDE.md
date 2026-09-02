# BS_GodFile — AI Agent Rules (Auto-loaded by Claude)

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
table for a one-line fix; you are proposing a design where the ask was a repair.
→ Stop, make the change, build it, report in three lines.

**Done = the change is made, it builds, you said what you changed.** Nothing else.

---

> This file is auto-loaded by Claude at session start. Read it before doing anything.
> **Read next:** [`_SESSION_HANDOFF.md`](_SESSION_HANDOFF.md) (current state, overwritten each
> session) · [`_DECISION_LOG.md`](_DECISION_LOG.md) (settled questions — check before
> re-litigating) · [`_ROADBLOCKS_2026-07-31.md`](_ROADBLOCKS_2026-07-31.md) (what is actually
> blocked, and which docs currently lie).

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
PGA/MPA/PPA/WIA/SQA boundaries and the "no cross-owner writes" rule no longer apply. `AGENTS.md`,
`AGENT_BOUNDARIES.md`, `AGENT_OPERATING_MODEL.md` and `AGENT_OWNERSHIP.md` are **historical** — read
them for tool-capability context, not as process.

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
- Update `CURRENT_STATE.md`, `NEXT_ACTIONS.md`

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
**Melodia/Melusina** — the eventual authored game is deliberately small: `bedroom/VN → overworld exploration → simple fixed turn-based battle → buddy/VN → bed`. No procedural roguelike depth in the current scope.

> **Blender version:** 5.1 is **not installed** — that directory is empty. Only 4.3, 4.5 and **5.2**
> have executables, and the full addon set (including Melodia Studio / `surreal_arch`) runs on 5.2.
> Docs that still target 5.1 — notably `Docs/MELODIA_STUDIO_SHIP_CHECKLIST.md` and the default in
> `sync_surreal_to_live.ps1` — describe steps that cannot currently run.

**Current focus (updated 2026-07-31)**: **First Dream vertical slice, foundation closeout.** Both
tracks are active — Decision 008 (2026-07-29) put the vertical slice first with the portfolio
proceeding in parallel via delegation. The native build is green, five test suites pass, and the
route packages clean; the remaining work is **Blueprint wiring**, not code. Start at
`Docs/BLUEPRINT_WIRING_CHECKLIST_2026-07-30.md`.

> The older line here said *"Gameplay work is paused during this push."* That was the 2026-07-26
> portfolio-first stance and it was superseded by Decision 008. `Docs/QUEUE.md` is now the
> **environment-art/portfolio** tracker only; gameplay lives in `_TASK_QUEUE.md`.

**Agent tooling — three Unreal MCP surfaces registered in `.mcp.json`, two enabled by default**
(Decision 025 as reversed 2026-07-31; Decision 027 for the third):

| Server | Transport | Shape | Enabled by default? |
|---|---|---|---|
| `monolith` | `Plugins/Monolith/Binaries/monolith_proxy.exe` → port 9316 | ~116 Blueprint actions via `blueprint_query({action, params})`: full graph read (`export_graph`, `get_graph_data`), the verification loop (`get_graph_fingerprint`, `assert_graph_matches`, `set_node_property`), and atomic T3D authoring (`validate_nodes_t3d`, `inject_nodes_t3d` — whole clusters in one transaction, see MONOLITH_GUIDE Recipe 16) | Yes |
| `it-is-unreal` | HTTP, port 8088 (VibeUE) | ~150 flat tools (`add_node`, `connect_nodes`, `analyze_blueprint_graph`, `take_screenshot`, …) | Yes |
| `ueblueprintmcp` | Python venv (`Plugins/UEBlueprintMCP/Python/venv`) → TCP port 55558 | ~60 tools: Blueprints, graph nodes, event dispatchers, Enhanced Input (Input Actions/Mapping Contexts), materials, UMG, editor control | **No — deliberately off** |

`ueblueprintmcp` is registered so it's one line away from live, but not in `enabledMcpjsonServers`.
It's a 9-commit, 36-star third-party plugin (`zolnoor`) with no audit history, and its ~60 commands
substantially overlap the two surfaces already enabled — installing it live-by-default would be a
third authority over exactly the graph-mutation surface this project has spent real effort
consolidating onto one owner (Decision 025's own reasoning, extended). Enable it deliberately, for a
scoped task, when its Enhanced Input command set covers something Monolith's `set_node_property`
doesn't. **Requires a closed-editor build first** — it's a new plugin module with reflected types
(`UCLASS`/`GENERATED_BODY`), so Live Coding cannot register it; only a full `Build.bat` pass with the
editor closed does.

Prefer Monolith where more than one surface can do the job. **Never run two surfaces against the
same graph in one session** — this applies to all three, not just the original two.

All three need the editor running. Monolith additionally cannot answer while a modal dialog blocks
the game thread — grep the log for `MODAL_OPEN` before assuming the plugin is at fault.

**MCP servers load at session start.** Editing `.mcp.json` mid-session does nothing until the
session is restarted — check what you actually have before promising editor work.

**Gameplay authority correction (2026-07-26, read before touching any gameplay system)**: MelodiaCore is quarantined as runtime-unstable and does **not** own battle/turn/save authority. The complete standalone TurnBased JRPG template is the provisional mechanical authority instead. QuillScript is an isolated narrative candidate (not yet proven to own gameplay state). ACFU is archived/reference-only and must not run parallel to the JRPG authority. Full decision record and ownership map: `Docs/MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md`. Do not rebuild JRPG-native mechanics in MelodiaCore, ACFU, or a parallel Blueprint graph.
