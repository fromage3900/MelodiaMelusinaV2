# Melodia Onboarding Guide — 2026-09-01

> **Audience:** New engineers, tech artists, and designers joining BS_GodFile after P0 closeout (8/8 gates pass, 2026-09-01).
> **In 10 minutes** you will: understand the shipped loop, open the project, pass the local gate check, and know which doc to read next for your lane.
> **Companions:** `grand_review_document.md` (7-rec anchor) · `cross_system_integration_map.md` (cymatics↔Faraway↔rhythm↔wardrobe↔water) · `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` (toolchain SSOT, read before building anything emerging).

---

## 0. Start Here (5-minute orientation)

### The shipped loop you are joining

```
Quill dialogue → allowlisted encounter → JRPG battle (Melusina), rhythm-timed
  → typed result → Quill resumes once → exploration / checkpoint → Piano phrase
  → typed world result → visible route opens (portal / traversal unlock)
```

Authority is fixed — do not rebuild it:

- **QuillScript** owns narrative. **TurnBased JRPG template** owns party/turns/targeting/damage/results/inventory/saves.
- `UMelodiaNarrativeSubsystem` is only the narrow Quill bridge. `MelodiaCore` is presentation-only.
- One writer per surface — see §7 ownership table before adding any widget/material/MPC writer.

Product shape: OMORI · Music-as-key: Zelda · Visual/wardrobe bar: Infinity Nikki.
Full scope: `_VERTICAL_SLICE_SCOPE.md` · Authority: `../PROJECT.md` · Closeout plan: `Docs/P0_CLOSEOUT_PLAN_2026-08-28.md`.

### Three docs to read for any lane

| Order | Doc | Why now |
|------|-----|---------|
| 1 | `grand_review_document.md` §2–3 | Current gate evidence (8/8) + the 7-recommendation map — know where the team is |
| 2 | `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` §1–9 | **Mandatory before any render/audio/Houdini/Material/PCG work** — prevents parallel-authority defects |
| 3 | `cross_system_integration_map.md` | How your lane's subsystem connects to the other four |

Lane-specific deep docs are linked at the end of each section below — follow only yours.

---

## 1. Prerequisites & Install

| Tool | Version / Path | Note |
|------|---------------|------|
| Unreal Engine | **5.8** — `C:\Program Files\Epic Games\UE_5.8\` | Editor is single-instance (Monolith on :9316). |
| Houdini / Houdini Engine | **22.0.368** — `C:/Program Files/Side Effects Software/Houdini 22.0.368` + `Plugins/HoudiniEngine/` | Required for cymatics/COPs/GN builders; `hython` is the CLI. |
| Git + LFS | latest | `Saved/` is **not** committed — your audit outputs live locally. |
| VS 2022 + Desktop C++ | — | For UBT builds (closed-editor `Build.bat`). |
| Rider (recommended) | — | Blueprint reflection, RiderLink live tests, IWYU, shader authoring. |

Optional per lane: Blender 5.2 + Surreal Arch addon (live-collab), VOICEVOX 0.25+ (voiced NPCs), Material Maker 1.7 (material lane).

---

## 2. Checkout → First Open (Day 0 in 15 min)

```powershell
# 1. Clone (SSH) and enter
git clone <BS_GodFile-remote> && cd BS_GodFile

# 2. Lightweight onboarding (dirs, hooks, lanes)
bash deploy/collaborator_onboarding.sh lightweight

# 3. Pick your model lane (before writing code)
python Tools/model_router.py pick docs --detail      # for this guide
python Tools/model_router.py pick <your-lane>        # e.g. cpp, audit, wardrobe_catalog, beatmap_author

# 4. Open the project — single editor only
start BS_GodFile.uproject          # wait for shader compile

# 5. Verify Monolith MCP (the one editor lock)
curl http://127.0.0.1:9316/health
# expect ~1330+ tools; if empty/refused → see §9 "Editor recovery"

# 6. Verify P0 gate state (read-only, fast)
cat Docs/P0_TASK_LEDGER.json | python -m json.tool | head -n 80
cat Saved/Audit/ue_level_building_coinsheet_2026-09-01.json | python -m json.tool | head -n 60
```

**Maps to open first:** `L_MelusinaMorning` (opening route) · `L_KaleidoNave` (PCG/look-dev surface) · `MelodiaIntegrationMap` (battle + portal integration proving ground — used by all 8 gate proofs).

**If this is a level-design contribution** — stop here and switch to the dedicated lane doc: `Docs/LEVEL_DESIGNER_ONBOARDING.md` (greybox kit, PCG volumes, exclusion volumes, 5-min validation). That doc is **not** duplicated below; return here once your greybox is validated.

---

## 3. Lane Map — Where You Plug In

Find your first task by lane. Each row gives: where your code/assets live, which gate you move, and the next doc after this guide.

| Lane | You work in | Teach it / Gate it touches | Read next |
|------|-------------|---------------------------|-----------|
| **Gameplay / Battle** | `Source/MelodiaIntegration/` · `Content/MelodiaIntegration/` | `rhythm_owner` / `rhythm_grade_to_result` / `battle_integration_map` | `Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md` (owner vs dead impls) + `Docs/ORCHESTRA_CONTRACT_2026-08-20.md` (seams) |
| **Wardrobe** | `MelodiaWardrobeSubsystem` · `Content/Melodia/UI/` | `wardrobe_equip_roundtrip` · `wardrobe_gameplay_hook` (Glide) | `Docs/Research/QWEN_WARDROBE_COMPARISON…md` + `Specs/wardrobe/` |
| **Rhythm / Audio** | `MelodiaAudioReactivePresentationSubsystem` (sole MPC writer) · `MelodiaMusicClockSubsystem` · `UMelodiaCymaticsSubsystem` | `music_world_key` · cymatics tiers 1–5 | `Docs/MELODIA_AUDIO_VISUAL_SYNESTHESIA_LAYER_2026-08-28.md` (5-tier spec) |
| **Water / Sea Above** | `MelodiaWaterSimulationZone` · `Content/EnvSandbox/Monoliths/SeaAbove/` | Sea Above membrane pulse (16.0s), PCG Arpeggio Bridge, Starskiff | `Docs/Reports/OCEANOLOGY_ACFU_MELUSINA_COMPATIBILITY_2026-08-26.md` (compatibility lane — optional, HOLD) |
| **Houdini / Cymatics / Faraway** | `Tools/Houdini/copernicus/` · `Docs/Houdini/` · `Content/Textures/FarawayMother_Suites/` | Recs 1–3 (cymatics PRESENT, Faraway P1, hython↔Monolith) | Master Index §1–9 + `Docs/Houdini/MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md` + skill `melodia-copernicus-parallax` |
| **Materials / PPV / Niagara** | `Content/EnvSandbox/Materials/Masters/` · `Source/MelodiaShader/` | `static_gates` (material baseline) | `Docs/Research/MATERIAL_TAKEOVER_RESEARCH_2026-08-29.md` + `.claude/skills/melodia-ui-artist` (token SSOT) |
| **UI / Quill** | `Content/Melodia/UI/Quill/` (tracked) · `Content/Melodia/UI/Textures/` (gitignored) | `hud_single_writer` | The UI-artist skill + `Docs/P0_TASK_LEDGER.json` §Quill |
| **Portfolio / Polish** | `Content/Python/` (exporters) | Portfolio pipeline (§5 data-flow) | `CURRENT_SYSTEM_MAP.md` §2–5 |

**Model lanes enforcement** (AGENTS.md): pick class via `Tools/model_router.py pick <class> --detail`. Audit/code/cpp/mcp/playtest/daemon/review/orchestrator + prod lanes `wardrobe_catalog`/`beatmap_author`/`quill_author`/`asset_qa`/`anim_bindings`.

---

## 4. The 7 Recommendations — What They Mean for You

Your first sprint will likely touch one of these. Human-readable summary; formal matrix is `grand_review_document.md` §3.

1. **Cymatics → PRESENT (Rec 1, due 2026-10-01)** — Engineering. Graduate `UMelodiaCymaticsSubsystem` from SCAFFOLDED to Master Index §1; verify `PostConfigInit` module phase; make cymatic PBR a first-class pipeline step. You need this if you touch audio→geometry.
2. **Faraway Mother → P1 (Rec 2, due 2026-10-15)** — Tech art + GN. 16 builders + hero meshes + 3 fabric textures → into taxonomy + material orchestration + P1 ledger. You need this if you touch Faraway/cloth/mountain/column assets.
3. **Hython ↔ Monolith bridge (Rec 3, due 2026-11-01)** — Pipeline. Fix :9316; create parallel Monolith plan + `cross_path_validation.py`. You need this if you generate or validate assets either path.
4. **P1–P3 Roadmap (Rec 4, due 2026-12-01)** — Production. Closeout items → `P0_TASK_LEDGER.json`; Faraway to P1 roadmap; cymatics V3/V4 horizon. You need this for planning, not code.
5. **Ecosystem integration (Rec 5, due 2026-12-01)** — Cross-system. Wire cymatics→rhythm, textures→wardrobe, meshes→PCG, cymatics→water. You need `cross_system_integration_map.md` for this.
6. **Grand docs (Rec 6, this set)** — Docs. You are reading it.
7. **User-facing features (Rec 7, before playtest)** — UI/feature. Cymatic browser, Faraway outfit selector, adjustable cymatic params. Depends on 1, 2, 5.

Dependency graph: `Rec1 → Rec2 → Rec3 → Rec4` and `Rec1,2 → Rec5 → Rec7`; `Rec6` tracks all.

---

## 5. Common First Tasks (Pick One, Ship It, Stop)

*Working agreement: do the job asked, ship it, stop — never compensate, kill means delete.*

- **Fix one warning** — run `python Tools/bp_sweep.py` (project-wide pass after the 3-editor incident is still outstanding per AGENTS.md) and file one real defect (shadowed parent event / empty exec island / unreachable asset) as an issue — do not auto-patch.
- **Validate one asset** — run `python Tools/Houdini/copernicus/copernicus_cymatic_parallax.py --dry-run` or import one Faraway hero mesh under `Saved/Audit/faraway_mother/` and confirm `tilecheck:pass` / vertex counts match the manifest.
- **Prove one gate locally** — follow `grand_review_document.md` §2.1 evidence pointers and re-drive one outcome on `MelodiaIntegrationMap` (requires editor up — see §9). Log the evidence path like `Saved/Audit/p0_real_input_run/…` — prose without a file path is not evidence.
- **Extend, don't duplicate** — Master Index §9 checklist before any new graph/subsystem/tool: if it's PRESENT extend it; if SCAFFOLDED finish it; if WATCH it needs an owner task; if external, say so.

---

## 6. Validation Commands (Copy-Paste)

```powershell
# Offline / no editor
python -m unittest Content.Python.Tests.test_qsc_allowlist_contract          # 4/4 — expected offline pass
python Tools/bp_sweep.py                                                      # project-wide sweep
python Tools/monolith_mcp_client.py --health                                  # 9316 probe

# With editor up (Monolith 1330+ tools)
python Tools/echo_run.py status
python Tools/echo_run.py run static_gates
python Tools/project_state.py --view integration
python Tools/project_state.py --view staleness

# Hython (Houdini 22.0.368)
hython Tools/Houdini/copernicus/copernicus_cymatic_parallax.py --dry-run
hython Tools/Houdini/flipbook_aaa.py --frames 8         # 8-frame flipbook variant
# 16-frame and 4K hero sets: see grand_review_document.md §7 items 5-6

# Live PIE gates (editor must be up; see evidence policy)
# Re-drive: PCGHeroMusicNode_0 Perfect → portal IsTraversalUnlocked → TryInteract
# Evidence lands in Saved/Audit/p0_real_input_run/*.png (4 images per pass)
```

**Closed-editor rebuild** (required for any new module/shader/C++ type — Live Coding cannot register reflected types):

```powershell
"C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" BS_GodFileEditor Win64 Development -project="C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" -NoUba -MaxParallelActions=6 -WaitMutex
```
The `MelodiaShader` module is `PostConfigInit` — adding/renaming modules needs this, not Live Coding (AGENTS.md §2.1).

---

## 7. File & Ownership Map (Don't Add a Second Writer)

| Surface | Owner | You may | You must not |
|---------|-------|---------|--------------|
| Battle damage / turn / targeting / results / saves | **TurnBased JRPG template** (`BP_BattleController`) | Ride on top (rhythm scalar on the same Attack/Skill/Item/Flee decision) | Rebuild combat in MelodiaCore |
| Battle HUD overlay | **`UMelodiaUIBridgeSubsystem`** (sole writer) | Consume its widgets | Add a second HUD writer |
| Audio reactivity (MPC `MPC_Melodia_Palette`) | **`MelodiaAudioReactivePresentationSubsystem`** (sole MPC writer) | Read `BeatPulse/BeatPhase/BeatIntensity` | Add a second MPC writer |
| Audio → geometry | **`UMelodiaCymaticsSubsystem`** (read-only consumer of the MPC above) | Extend Chladni mapping | Write back into the MPC |
| Wardrobe equip / save / gameplay hook | **`MelodiaWardrobeSubsystem`** | Equip through authority; consume `MelodiaWardrobeSubsystem` + `MelodiaTraversalCapabilityRegistry` | Invent a slot or bypass the subsystem |
| Wardrobe traversal (Glide) | **`MelodiaTraversalCapabilityRegistry`** (`capability.melodia.glide`) | Query `IsTraversalUnlocked` / `RequestTraversalMode(Glide)` | Acquire Glide without the canonical quest reward |
| World music challenge | **`UMelodiaPCGNarrativeChallengeBridgeComponent`** + `MelodiaTraversalCapabilityRegistry` | Commit one idempotent `challenge.first_resonance_echo` → one visible route | Run challenge without the bridge component |
| World materials / PPV / Niagara / water | Masters in `Content/EnvSandbox/Materials/` + `M_Master_Toon_*` / `M_Water_Master_Grand_v7` | T3D inject via Monolith bulk ops; add MI on masters | Build a parallel master for the same surface |
| Houdini geo / masks / LOD | Houdini HDAs → baked meshes/textures | Manufacture reusable geo; bake — never leave playable levels dependent on live HDA cooking | Ship a level that needs live HDA cooking |

Convergence refs: `Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md` (which impl is owner vs dead), `Docs/ORCHESTRA_CONTRACT_2026-08-20.md` (seams).

---

## 8. Where to File Things & Evidence Standard

- **Your branch** — `feature/<lane>-<short-scope>` (e.g., `feature/cymatics-pbr-validate`).
- **Evidence** — `Saved/Audit/<scope>_<date>.{json,md,png}`. Every gate or visual claim needs a file on disk — prose alone is not evidence (§9 Master Index).
- **Ledgers** — `P0_TASK_LEDGER.json` / `Saved/Audit/ue_level_building_coinsheet_2026-09-01.json` are read-only unless you are explicitly closing a gate (requires `echo_run record <gate> pass|fail` + a ledger row, not just a commit).
- **Never commit** `Saved/`, `Content/Melodia/UI/Textures/`, or `Content/_PROJECT/` (AGENTS.md + Master Index §9 item 6).
- **Editor lock** — one instance, one :9316; batch saves `unattended:true`. Two simultaneous editors will corrupt `.umap`/`.uasset` saves.

---

## 9. When Things Are Broken (Known Incidents & Recovery)

| Symptom | Cause | Fix |
|---------|-------|-----|
| `editor reachable on 9316: no` · MCP refused | `MODAL_OPEN` — empty-title modal loop (New Chat dialog) | **Recover:** Task Manager → kill UE → restart → `netstat -ano | findstr :9316` confirms bound → `hermes gateway start` if needed → re-run subagents |
| `melodiaBattleUI` / `MelodiaUI` both None | Vestigial pre-bridge Blueprint vars in category `Melodia` — not the binding (real binding is `BP_BattleController.battleUI`) | No action — owner decision pending to retire them; `EnsureStockBattleUIControllerReference` silence = success |
| `liveResultsWidgetPath` empty in log | Pre-`cdda0384` — backfilled in `MelodiaUIBridgeSubsystem.cpp:131` by this branch's closed-editor rebuild | Already fixed on `main` |
| Starskiff won't board / Shorewake outfit won't equip | Genuine gaps — Starskiff is Pawn shell only; Shorewake is 2-bone vs 465-bone skeleton mismatch | Don't fake a fix — file a `HOLD` issue and link `P0_TASK_LEDGER.json` §current_source_truth |
| `MELODIA_QUANTUM draw success=false` / `127.0.0.1:8008` down | Quantum service elsewhere | Falls back to classical baseline — not a blocker |
| `F:/UE_DDC` / Zen no valid path | DDC mount (`P0_TASK_LEDGER.json` §vendor_compatibility_track) | Don't change machine env — bounded retry, then HOLD |

Full incident log: `P0_TASK_LEDGER.json` §current_source_truth + §vendor_compatibility_track; materials takeover postmortem in `Docs/Research/MATERIAL_TAKEOVER_RESEARCH_2026-08-29.md`.

---

## 10. Your First Day Checklist

- [ ] Read `grand_review_document.md` §2–3 + Master Index §1–9; routed a lane via `Tools/model_router.py pick <class>`
- [ ] Checked out, built lightweight, opened `BS_GodFile.uproject` single-instance, `curl :9316/health` shows 1330+ tools (or logged recovery)
- [ ] Ran one offline gate (`test_qsc_allowlist_contract` 4/4) and one `bp_sweep` scan — filed the result path
- [ ] Can name the single writer for your lane's surface without looking (see §7 table)
- [ ] Know which recommendation your lane feeds (see §4) and what file to produce for it

## 11. Next Docs by Lane (Pick One)

- **Gameplay/Battle/Rhythm** → `Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md` + `Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md`
- **Wardrobe** → `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION…2026-08-30.md` + `Specs/wardrobe/`
- **Water/Sea Above** → `Docs/Houdini/MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md` + `Saved/Audit/sea_above/`
- **Houdini/Cymatics/Faraway** → Master Index §2/§6 + `Docs/Houdini/MELUSINA_HOUDINI_UE58_TECHNICAL_RESEARCH_2026-08-30.md` + `cross_system_integration_map.md` §2–5
- **Materials/PPV/Shader** → `Docs/Research/MATERIAL_TAKEOVER_RESEARCH_2026-08-29.md` + `Source/MelodiaShader/Shaders/`
- **UI/Quill** → `.claude/skills/melodia-ui-artist` + `Content/Melodia/UI/Quill/` + `cross_system_integration_map.md` §6 diagram
- **Level design** → `Docs/LEVEL_DESIGNER_ONBOARDING.md` + `Docs/ORCHESTRA_CONTRACT_2026-08-20.md`
- **Research/Systems** → `Docs/Research/TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md` (16 tests, ADOPT/PARK/REJECT)

---

*Onboarding companion for Rec 6. Distinct from `LEVEL_DESIGNER_ONBOARDING.md` (greybox/PCG) and `ONBOARDING_LIVE_COLLAB.md` (Blender LiveLink) — those are linked, not duplicated. Update this file when Recs 1–5 land new assets or gates; keep Master Index §9 anti-duplication checklist as pre-commit gate.*
