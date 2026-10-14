# BS_GodFile — AI Agent Rules (Auto-loaded by Claude)

**Front-door review:** 2026-10-05 against `main` at `e25682b3a83c5f6453a355f60a08b772309d3dad`.

## 🛑 GIT PIPELINE LAW — BINDING

This section mirrors the current repo-wide contract in `AGENTS.md`,
`Docs/Production/MULTI_AGENT_LANES.md`, and `Docs/Production/GIT_HEALTH_CONTRACT.md`.
`_AGENT_WORKING_AGREEMENT.md` outranks every agent doc. If this section ever drifts from
those newer repo-wide Git contracts, the current repo-wide contracts win until this file is
updated.

Canonical authority is `origin/main`. **`main` is a landing target, never an agent
workspace.** Normal worker execution uses a detached lane worktree created from current
`origin/main` and pinned by `refs/agents/<lane>`; workers do not create feature branches,
push, or open PRs. Commits inside the worker's own lane need no per-commit approval, and the
integrator may perform the normal bounded landing flow without asking again. The integrator
owns any temporary PR branch and retires it after landing.

Explicit owner approval is still required for destructive or history-rewriting operations:
`git reset --hard`, `git checkout -- .`, `git clean`, force-push, history rewrite,
deleting a branch/ref, and any Perforce submit. The preserved
`collab/laptop/longterm` branch remains a special Blender/Geometry-Nodes workstation source
lane; it is not the default agent workflow and must never be wholesale-merged over current
`main`.

The portable `G:` workspace may be a complete runnable project. Do not treat a laptop or
portable checkout as archive-only merely because it is not the desktop PC. Keep paths
repo-relative and obey the same lane/integration rules on every workstation.

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

**Melusina asset pipeline (2026-09-25).** Edit only the working copy
`harp_bow_pipeline/Melusina_Harp_HERO01_ArcherPoseV09_ARP_R09_HotPass.blend`; R08 is canonical and
untouched. Export with `Tools/melusina_export_dryrun.py` → staging only, check with
`Tools/validate_melusina_staged_fbx.py`, contract in `Tools/melusina_export_contract.json`.
**Reimport onto the live UE meshes is blocked** (no anim instance → T-pose) — see `CURRENT_STATE.md`
before trying again; never reimport over a live mesh without a `.uasset` backup.

**Delegation.** Jev's ruling (2026-09-25): tiered — cheap/local workers for bulk mechanical work,
Sonnet subagents for scoped rig/editor-adjacent work, the main session plans and verifies. Delegated
output is not evidence: on 2026-09-25 a subagent reported a "smooth" SDF bake whose image was
scattered dots. Look at the artifact yourself. Never let a subagent write to the blend or editor the
main session is using. **Long jobs go to Hermes** (Jev routes, Claude verifies):
[`.hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md`](.hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md)
is the one orchestration plan — extend it, never start a parallel one. Hermes reads `AGENTS.md` (not
this file), so binding rules added here must be mirrored in its "BINDING RULES" block.

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
MelodiaCore remains integration/presentation-only; Conversation2D is excluded. The turn-based ARPG / ACFU hybrid is CANON (owner, 2026-10-11; open ownership questions are listed in `CURRENT_STATE.md` "OWNER CANON") and supersedes the earlier "ACFU excluded" ruling; until those questions are answered the JRPG GameMode/pawn stays the only production boot path. The scoped battle,
grade-to-damage, Wardrobe and music-key seams are evidence-backed in `CURRENT_STATE.md`; packaged golden-run
and long-chain persistence proof remain separate open gates.

**Content-first rule:** before changing architecture, ask whether the requested experience can be authored
through `CURRENT_STATE.md` → `PROVEN CREATIVE CAPABILITY SURFACE`. If yes, author the boss, side quest,
rhythm skill, creature episode, outfit ability, musical puzzle, or procedural setpiece through the existing
entry points. Architecture work requires a demonstrated content blocker. Do not reopen old rig or system work
without current evidence of a blocker.

**This game is a finished, fully-working system.** The correct default reading of any open-gate note in
`CURRENT_STATE.md` is *polish history*, not a broken-systems agenda. When the owner invokes a build workflow
(Claireon `/workflow`, etc.), its Stage 1 must ask the **content-first question before the build question**:
"What playable content do you want more of — a boss, side quest, traversal space, encounter, skill, outfit,
interactable, setpiece — and through which existing authoring entry point does it get built?" Never propose a
workflow to "bind missing content" or "repair" a system the owner has already said works. If the owner states a
thing works ("I've already verified X"), that is ground truth — stop treating it as the blocker and ask what
content to add. The pipeline is for authoring *new* content through existing entry points, not for fixing
finished systems.

## 🌌 Niagara VFX & Material Convergence Canon (Binding Rules)

1. **Keep Unreal Engine Closed During Staging:**
   - Do not launch the Unreal Editor or run commands that spawn the editor while staging / asset recovery is running.
   - C: drive must preserve headroom (>13 GB free).

2. **No New Masters Rule:**
   - Every owned Niagara renderer must use a **unique Material Instance (MI)** parented to one of the canonical masters.
   - Canonical masters:
     - Sprite Flipbook / Static Atlas: `/Game/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook` (32 refs).
     - Soft Additive Mote / Glitter: `/Game/Melodia/VFX/Materials/M_Niagara_Morning_PollenMote`.
     - Petal Card: `/Game/Melodia/VFX/Materials/M_Niagara_Morning_PetalCard`.
     - Mist Sheet: `/Game/Melodia/VFX/Materials/M_Niagara_Morning_MistSheet`.
     - Dust / Light Shaft: `/Game/Melodia/VFX/Materials/M_Niagara_Morning_DustShaft`.
     - Ribbon: `/Game/Melodia/VFX/Materials/M_Niagara_Morning_WindRibbon` (Melodia feature) & `/Game/EnvSandbox/VFX/Materials/M_SakuraRibbon` (Library).
     - Ornament Card (SDF sprite + ribbon): `/Game/Melodia/VFX/Materials/M_Niagara_MelodiaOrnamentCard`.
     - SDF Card: `/Game/Melodia/_PROJECT/04_Materials/SDF/M_SDF_StarburstGem`.
     - Mesh Petal: `/Game/EnvSandbox/VFX/Materials/M_Niagara_PetalMesh_Loop`.
     - Surface Fabric Flipbook: `/Game/Melodia/Materials/Masters/M_SurrealFabric_Flipbook`.

3. **Fix A SubUV Flipbook Invariant:**
   - Material owns the scrub clock (`ParticleRelativeTime` / `FlipFPS`).
   - Niagara Particle Update `SubUVAnimation` module MUST be **DISABLED**.
   - Sprite Renderer `SubImageSize` MUST be **1x1** (scrub) or native atlas grid (static atlas).
   - Never enable both.

4. **Staging & Convergence Invariants:**
   - Organ Cliff staging destination: `/Game/Staging/Aeolian/`.
   - Stash restore source: Commit `424146870` (`stash@{9}^3`) for `BP_MelodiaNiagaraDriver`, `EnvSandbox` VFX library, and `SurrealFabric` textures (462 assets, local LFS verified).
   - Zero level modifications during convergence.
   - Every modified file must be backed up before editing.
   - Protected systems: `NS_Melusina_EyeSparkle` (1.5px atlas inset), `NS_Melusina_HairFlow`, and `NS_Hero_SoftSparkle` remain untouched / held.
   - Batches of at most 4 assets; user Ctrl+S after each batch.

5. **Direct Visual Video QA Verification Invariant:**
   - Every UI, Slate brush, and Niagara particle claim requires direct visual motion proof (.mp4).
   - Motion recordings must be verified via `ffmpeg -vf freezedetect` to ensure real frame repainting (0 freeze duration).
   - QA evaluations must be documented via `Tools/gemini_video_qa.py` / `Tools/video_review_lane.py` with structured audit outputs saved to `Saved/Audit/VideoQA/`.

## 🔤 Slate & UMG Font Composite Binding Law (Binding Rules)

1. **UFont Composite vs UFontFace Distinction**:
   - `FSlateFontInfo.FontObject` resolves a **UFont composite asset** (e.g., `/Game/Melodia/UI/Fonts/F_Melodia_UI`, `Font_KaiseiDecol`, `Font_KleeOne`), **NEVER a raw UFontFace**.
   - Slate cannot render a raw FontFace passed to FontObject.

2. **Explicit Slot Name Resolution & Weight Aliases**:
   - Widgets request typeface by slot name via `TypefaceFontName` (e.g. `Bold`, `Regular`, `SemiBold`).
   - Every composite font's `DefaultTypeface.Fonts` MUST register explicit aliases for all common weights (`Regular`, `Medium`, `SemiBold`, `Bold`) pointing to valid `FontFace` assets.
   - **Crucial Invisibility Trap**: `Font_KleeOne` only has Regular and SemiBold source files. Its composite MUST explicitly alias `Bold` -> `F_KleeOne_SemiBold`. TextBlocks specifying `TypefaceFontName="Bold"` on a font lacking that slot fail to match and render 100% invisible when FallbackTypeface is empty.

3. **Mandatory FallbackTypeface**:
   - Every UFont composite MUST declare a non-empty `FallbackTypeface` pointing to `/Engine/EngineFonts/Faces/DroidSansFallback` and `/Engine/EngineFonts/Faces/RobotoRegular`.
   - Without a fallback typeface (`FallbackTypeface=(Typeface=())`), any character outside the TTF glyph set (such as middle dots `·`, bullets `◆`, checkmarks `✓`, `◇`, or Japanese Kanji) fails to draw.

4. **Zero-Alpha Text Inspection**:
   - When text blocks are reported invisible, always verify `ColorAndOpacity.SpecifiedColor.A > 0.0`. Do not allow uninitialized or black zero-alpha `(0, 0, 0, 0)` colors to hide text.

