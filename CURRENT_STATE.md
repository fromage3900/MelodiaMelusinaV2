# Current State — Melodia (BS_GodFile)

**Canonical State Document**
**Last Updated:** 2026-09-09 (front-door health gate; Choral Sheep UE proof is the owner queue; runtime evidence below remains grounded in the 2026-09-05 verification pass)
**Target Engine:** Unreal Engine 5.8.0 | Blender 5.2 LTS | C++20 | Python 3.11
**Overall Status:** **Editor build GREEN · 8/8 active P0 gates PASS · 524/524 tests PASS (captured revision) · audio reactivity verified live in PIE · packaged route verified (both legs, 0 fatals) · Issue #51 long-chain persistence still OPEN**
**Recruiter showcase:** **SOFT FREEZE ACTIVE (2026-09-07)** — only final render promotion and critical correctness fixes are in scope; game/semester production continues. See `Docs/Production/PORTFOLIO_SENDOFF_FREEZE_2026-09-07.md`.
**World-building authority:** [`Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`](Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md) — player loop, C++ truth, Chladni/cymatics, TouchDesigner as visual instrument.

> **Build:** green. `UnrealEditor-BS_GodFile.dll` built 2026-09-04 21:47 and the editor is running
> from it. The blocker was `LPCTSTR` dropping a struct member in
> `MelodiaCaptureRenderSubsystem.cpp` — fixed at `582fa914`, not a format-string or UE-5.8
> issue as earlier notes claimed.
>
> **Audio reactivity:** works, and is not theoretical — measured live in PIE at `b1cac649`.
> The original fault was that route leg 0 had no music clock, so nothing drove the palette;
> the clock now lives on the GameMode (`5fea50c8`) so **every** level reacts rather than only
> those with a hand-placed clock actor.

---

## 1. Executive Summary & Paradigm Shift

Melodia has converged from disparate exploratory prototypes into a unified **Rhythm-JRPG / environment-led technical-art project**. The runtime operates under stable ownership boundaries and a set of converged gameplay/production pillars. The proven six-phase First Dream route is a full-stack integration test, **not a mandatory story template for every future chapter**.

### Two Absolute Authorities
1. **QuillScript Narrative Authority (`UMelodiaNarrativeSubsystem`)**: Sole authority for narrative flow, branching dialogue, cutscene triggering, quest flag evaluation, and 7-verb structured notifications (`melodia:quest`, `melodia:battle`, `melodia:stat`, `melodia:wardrobe`, `melodia:item`, `melodia:inspect`, `melodia:checkpoint`).
2. **Turn-Based JRPG State Authority (`BP_JRPGSaveGame` & Combat Subsystem)**: Sole authority for turn queue resolution, combat calculations, party stats, inventory, and canonical game state persistence.

### Converged Gameplay + Production Pillars
1. **Rhythm Combat Layer**: Rhythm timing highway executes directly over JRPG command selections (Attack / Skill / Item / Flee). Note accuracy (`Poor: 0.35`, `Good: 1.0`, `Great: 1.2`, `Perfect: 1.5`) scales base damage and pulses material parameter collections (`MPC_Melodia_Palette`) without bypassing JRPG turn logic.
2. **Wardrobe Traversal System**: Outfits provide visual mesh customization and implement `IMelodiaTraversalCapabilityProvider` to grant physical world traversal capabilities (Glide, Swim, Dash), fully persisted across save/reload cycles via `UMelodiaWardrobeSubsystem`.
3. **Music-as-Key World Puzzles**: Environmental barriers and harmonic puzzles respond to played musical phrases (`APCGHeroMusicGraphHost` / Piano node stepping), dispatching 7-verb narrative notifications to unlock physical routes and portal boundaries without combat code.
4. **Single-Writer UI Architecture**: Strict UI hierarchy where every surface has exactly one designated writer (`UMelodiaUIBridgeSubsystem`), eliminating race conditions, duplicate overlays, and widget memory leaks.
5. **Canonical Procedural & 3D Pipelines**: Deep cross-system pipeline architecture established in `Docs/Pipelines/MELODIA_CYMATICS_MONOLITH_HOUDINI_EMERGING3D_PIPELINE.md` governing Cymatics math & runtime subsystems, Monolith MCP automation, Houdini procedural authoring, and emerging 3D toolchains.
6. **Faraway Mother PCG Ecosystem**: Procedural fabric mountain architecture established in `Docs/PCG/FARAWAY_MOTHER_PCG_SYSTEM_ARCHITECTURE.md` and `specs/pcg/faraway_mother_pcg_manifest.v1.json`, with 4 biomes (WeaveRidge, LaceCanopy, FrillValley, ResonantSeamWay), multi-frequency WPO deformation, World Field Bus tension integration, and Heart Gate hero music puzzles.
7. **Perceptual LOD LookDev Architecture**: Advanced optical deception framework established in `Docs/LookDev/MELODIA_PERCEPTUAL_LOD_LOOKDEV_ARCHITECTURE.md`, `Tools/LookDev/build_optical_lod_matrix.py`, `Content/Python/melodia_optical_lod_pipeline.py`, and `specs/lookdev/optical_lod_manifest.v1.json`, delivering 4-tier perceptual LOD continuity, Toksvig specular anti-aliasing compensation, adaptive Parallax Occlusion step scaling, 8x8 Bayer/64x64 blue-noise dithered crossfading, and grazing-angle silhouette compensation.

---

## 2. First Dream Full-Stack Integration Loop

The sequence below is the canonical P0 integration route used to prove the project end to end. Future Chapters may use different narrative/mechanical shapes while reusing the same stable authorities, persistence rules, and typed intent contracts:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        UNIVERSAL CHAPTER GAMEPLAY LOOP TEMPLATE                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
[ Phase 1: Narrative Initiation & Sanctuary Departure ]
   ├── QuillScript dialogue node with chapter key NPC
   ├── Authoring of active quest flag (`quest.<chapter_id>.start`)
   └── Authoring of Sanctuary departure gate unlock
   │
   ▼
[ Phase 2: Overworld Traversal & Music-as-Key Route Unlock ]
   ├── Traversal across overworld using active Wardrobe traversal capabilities
   ├── Discovery of environmental musical puzzle / route barrier
   ├── Player steps on musical nodes / plays resonant melody
   └── Route / portal barrier unlocks via 7-verb narrative notification
   │
   ▼
[ Phase 3: Turn-Based JRPG Combat with Rhythm Command Timing ]
   ├── Seamless encounter transition to battle arena
   ├── Single HUD writer (`UMelodiaUIBridgeSubsystem`) displays command menu
   ├── Player selects action (Attack / Resonance Skill / Item / Flee)
   ├── Harmonix Rhythm Highway engages for real-key timed inputs
   └── Grade multiplier scales stock JRPG damage calculation
   │
   ▼
[ Phase 4: Battle Resolution & Idempotent Reward Distribution ]
   ├── Terminal combat outcome reached (Victory / Defeat / Flee / Timeout)
   ├── QuillScript narrative resumes once
   └── Idempotent reward distribution via Intent-ID (Wardrobe unlock, Stat increase, Item)
   │
   ▼
[ Phase 5: Traversal Upgrade & World Progression ]
   ├── Player equips newly acquired wardrobe piece
   ├── `UMelodiaWardrobeSubsystem` grants new traversal capability (e.g., Glide / Dash)
   └── Player accesses previously unreachable chapter climax portal / landmark
   │
   ▼
[ Phase 6: Canonical Checkpoint & Seamless Chapter Transition ]
   ├── State serialized to `BP_JRPGSaveGame` slot
   ├── Verified round-trip persistence (Party, Stats, Flags, Wardrobe, Inventory)
   └── Level streaming / transition to next Chapter map
```

---

## 3. P0 Gate Evidence

**Current tracked authority:** `Docs/P0_TASK_LEDGER.json` records **8/8 active P0 gates passing**. The 10-row matrix below preserves the broader completion-gate taxonomy used during the September 1 closeout; it is historical evidence vocabulary, **not a second current gate count**. `Saved/gate_ledger.json` is a generated/local evidence artifact and may not exist in a fresh GitHub clone.

### Historical completion-gate taxonomy (10 IDs)

| Gate ID | Target System | Verification Criteria | Status | Evidence Source |
|---|---|---|:---:|---|
| `runtime` | Core Gameplay Loop | Full PIE session execution across sanctuary, traversal, and battle | **PASS** | `Saved/gate_ledger.json` |
| `save_load` | State Persistence | `BP_JRPGSaveGame` slot serialization & roundtrip deserialization | **PASS** | `Saved/gate_ledger.json` |
| `repeat_consume` | Narrative Queue | Exactly-once consumption of narrative notifications | **PASS** | `Saved/gate_ledger.json` |
| `package_launch` | Standalone Shipping | Executable boots cleanly and initializes all core subsystems | **PASS** | `Saved/gate_ledger.json` |
| `rhythm_owner` | Rhythm Subsystem | Rhythm highway modifies JRPG action inputs without owning combat state | **PASS** | `Saved/gate_ledger.json` |
| `hud_single_writer` | UI Hierarchy | `UMelodiaUIBridgeSubsystem` is the sole writer for HUD/Battle UI | **PASS** | `Saved/gate_ledger.json` |
| `wardrobe_equip_roundtrip` | Wardrobe Subsystem | Mesh swapping and outfit persistence verified across save/load | **PASS** | `Saved/gate_ledger.json` |
| `rhythm_grade_to_result` | Combat Multiplier | Note accuracy (`Poor`/`Good`/`Great`/`Perfect`) scales damage calculation | **PASS** | `Saved/gate_ledger.json` |
| `music_world_key` | Resonant World | Musical phrase stepping unlocks route barriers via narrative subsystem | **PASS** | `Saved/gate_ledger.json` |
| `wardrobe_gameplay_hook` | Traversal Provider | Equipping outfit grants physical world traversal capabilities (`Glide`) | **PASS** | `Saved/gate_ledger.json` |

---

## 4. Current Test Suite Status

The project enforces automated test coverage across Python simulations, C++ automation tests, schema validation contracts, and MCP regression suites:

```powershell
# Automated Test Execution Summary (2026-09-01):
# 1. GMM Python Simulations & Math Contracts:  307 / 307 PASS
# 2. P0 Content & Integration Test Suite:        48 /  48 PASS
# 3. ECHO Pipeline Asset & Audio Contracts:     77 /  77 PASS
# 4. Melodia MCP Regression Suite:              38 /  38 PASS
# 5. Ollama Token & Daemon Stress Suite:        25 /  25 PASS
# 6. Melusina Release End-to-End Suite:         17 /  17 PASS
# 7. Offline Preflight Gate Checks:             12 /  12 PASS
# ─────────────────────────────────────────────────────────────
# TOTAL VERIFIED AUTOMATED TESTS:              524 / 524 PASS (100%)
```

---

## 5. Level & Environment Verification Status

1. **`L_MelusinaMorning` (Sanctuary / Chapter Opening)**
   - **Role:** Narrative initialization, NPC dialogue, departure gate.
   - **Status:** Verified. QuillScript NPC anchor dispatches `melodia:quest:first_dream.started`; departure gate opens seamlessly.
2. **`LV_SeaAbove_Prototype` (Overworld Traversal & Music-as-Key)**
   - **Role:** Traversal, Starskiff navigation, musical puzzle, route unlock.
   - **Status:** Verified. Clean Outliner hierarchy (0 root actors); Recast navmesh paths active; Starskiff boarding, driving, and docking confirmed; `APCGHeroMusicGraphHost` unlocks portal path upon harmonic match.
3. **`L_KaleidoNave` (Battle Arena / Boss Encounter)**
   - **Role:** Turn-based combat, Rhythm Highway interaction, victory resolution.
   - **Status:** Verified. Single HUD writer (`UMelodiaUIBridgeSubsystem`); Harmonix rhythm note highway scales `BP_MelodySlime_Boss` combat damage; victory triggers idempotent reward flow.
4. **`MelodiaMainMenu` (Title & Frontend)**
   - **Role:** Title screen, new game / load game entry point.
   - **Status:** Verified. Clean bootstrap into sanctuary level.

---

## 6. Historical September 1 Closeout Sequence

This sequence is retained for audit/history only. The verified status at the top of this document supersedes its future-tense wording. The original closeout sequence was defined in [Docs/Handoffs/MELODIA_EVENING_PLAN_P0_AND_CHAPTER_LOOP_2026-09-01.md](Docs/Handoffs/MELODIA_EVENING_PLAN_P0_AND_CHAPTER_LOOP_2026-09-01.md):

1. **Stage 1 — Clean Environment Preflight:** Execute full test suites (`run_tests.ps1`, `verify_p0_offline.py`, `test_melodia_mcp.py`). (Status: **COMPLETED / GREEN**)
2. **Stage 2 — Clean Win64 Packaging:** Execute Unreal Automation Tool `BuildCookRun` with canonical map roster (`L_MelusinaMorning`, `L_KaleidoNave`, `LV_SeaAbove_Prototype`, `MelodiaMainMenu`).
3. **Stage 3 — Package Launch Verification:** Confirm packaged binary `Saved/Packages/P0_Closeout_20260901/Windows/BS_GodFile.exe` launches without errors.
4. **Stage 4 — Official Golden Run Execution:** Execute the end-to-end P0 Golden Run contract (`specs/p0/core_p0_dream_golden_run.v1.json`) through the 6-phase reusable chapter loop on the packaged build.
5. **Stage 5 — Evidence Ledger Freezing:** Record immutable execution logs to `Saved/Audit/` and update `Saved/gate_ledger.json`.
6. **Stage 6 — Final Sign-Off:** Publish final shipping report and hand off to Chapter 2 production.

---

## 7. Session 2026-09-04 → 09-05 — Build, Audio, Merge, Look-Dev

### 7.1 What is now true

| Area | State | Evidence |
|---|---|---|
| **Editor build** | **GREEN** | `582fa914`. Root cause was `LPCTSTR MaterialToken` silently dropping a struct member in `MelodiaCaptureRenderSubsystem.cpp`; corrected to `const TCHAR*`. Two earlier `FString::Printf` rewrites treated symptoms. Binary dated 2026-09-04 21:47; editor runs from it. |
| **Audio reactivity** | **VERIFIED LIVE** | `b1cac649` — measured in PIE, not inferred. Root cause at `0bc95bfb`: route leg 0 had no music clock. Fix at `5fea50c8` puts the clock on the GameMode so every level reacts. Electric Dreams ambience + landscape beat response at `9b74f333`. |
| **Packaged route** | verified, both legs, 0 fatals | earlier this session |
| **P0 gates** | 8/8 active gates `pass` | `Docs/P0_TASK_LEDGER.json` |
| **Niagara FX** | 5 dead systems repaired | `abd87eca` — they were rendering `DefaultSpriteMaterial` (the "green balls"), including `NS_Melodia_BattleBackdropPulse`. Mouse-click sparkle wired on the player controller. |
| **Masked foliage** | repaired | `16bcff59` — `OpacityMap` on `M_Master_Toon_Universal_Alpha` was an orphan parameter; the sampler feeding the OpacityMask chain had `TextureObject` unconnected, so every pixel clipped. `MI_AtlasLeafA` rendered as an empty frame before the fix. |

### 7.2 Merge to main

19 commits replayed onto `main`. The planned `checkout` + cherry-pick was abandoned: the editor
holds `.uasset` handles (`unlink … Invalid argument`, not the lfs read-only bit) and the overnight
wardrobe daemon **drives git itself** — mid-operation it checked the repo off `main` onto its own
branch and committed. The merge was instead replayed entirely in the object graph
(`merge-tree --write-tree` + `commit-tree`), touching no worktree, index or HEAD.

Three conflicts, each resolved deliberately and recorded in
`Docs/Production/MERGE_TO_MAIN_RECORD_2026-09-04.md`.

**Historical Sep 4 snapshot — superseded Sep 9.** At the time of this merge, local `main`
and `origin/main` were diverged lineages (628 vs 704 commits, neither an ancestor of the other).
That condition is no longer current: the lineages were reconciled through the Sep 9 unification /
canonization merges, and GitHub `main` is now the canonical shared baseline. The old recovery refs
remain extraction-only historical safety copies and are not current task queues.

### 7.3 Landscape / look-dev

- **Key light was pointing at the sky.** `Key_TwilightPink` sat at pitch **+30**, so the terrain
  received no key lighting. Fixed to −32 (`c94f1746`, re-applied and this time *tracked* at
  `0fb76675` — the first fix was lost because SeaAbove external actors are untracked).
- **SuperColor is now bound.** The landscape had been rendering `T_Glacier_ColorErosion`, a colour
  map from a **different Gaea project**, while `T_Gaea_SeaAbove_SuperColor` sat unreferenced
  (`99a32308`, `e4c97d15`).
- Gaea mask wiring audited end to end — each mask gates its own layer and reaches the output.
  Tool: `Content/Python/audit_gaea_wiring.py`.

### 7.4 Open, and honestly stated

1. **`W_Glacier_Rock` is a near-black export** (peaks 31/255). The rock layer cannot read until it
   is re-exported from Gaea with correct normalisation. Not a UE-side problem.
2. **Something rewrites `MI_Glacier_Landscape_Layered`.** `Gaea_SnowWeight` was found at −14.94 and
   `Gaea_RockWeight` at 6.43 *after* both had been set to 1.0 and read back as 1.0. The writer is
   unidentified. The master's `Saturate` clamps limit the damage, and the weights were measured to
   make no visual difference at all.
3. **Look-dev captures on this level are not trustworthy evidence.** Two captures with identical
   material state differ substantially (terrain colour spread 25.1 vs 15.9). Ultra Dynamic Sky's
   time-of-day is not reflected to Python, so it cannot be pinned or read — every before/after on
   `LV_SeaAbove_Prototype` has an uncontrolled lighting variable. **Pin the sky before trusting any
   A/B on this map.**
4. **Material instance writes need `update_material_instance()`** to reach the renderer. Parameter
   read-backs succeed while the render still shows the old value; several measurements this session
   were invalidated by this.
5. **PCG volume layout** — four concentric 600–800k volumes over a 250k landscape, still unaddressed
   (`Docs/Plans/SEA_ABOVE_PCG_DRESSING_PLAN_2026-09-04.md` §4a).
6. **Universal / Universal_Alpha master convergence** — analysed, not executed. The Alpha master
   carries **none** of the 14 `Cymatic_*`/`Audio*` parameters, so its 109 instances (including
   Melusina's `SW_Dress_P01..P48`) are structurally excluded from audio reactivity.

---
### 7.5 Front-door reconciliation — 2026-09-08

`TODO.md` and `_VERTICAL_SLICE_SCOPE.md` were reconciled with this document and `AGENT_START_HERE.md`. They no longer claim that restart/package proof never ran, or that 10/10 gates are the current scoreboard. Issue #51 remains the open long-chain persistence boundary. Leftover root audit copies now stub to `Docs/Archive/RootLegacy/`.

### 7.6 Front-door health — 2026-09-09

Periodic git/status drift is gated by `python Tools/front_door_health.py`. PR CI runs contradiction checks. Monday CI runs `--age` so source movement without a `CURRENT_STATE.md` refresh fails in the open. The tool does not auto-write docs.

Owner queue remains Choral Sheep UE proof → one UE↔TD connection → one short AE sequence (`TODO.md`).

---
*Melodia © 2026. Authoritative State Ledger.*

---

## 8. Session 2026-09-10 — Starskiff boarding proof + MK39 ribcage

Branch: `feat/choral-sheep-root-c-material-proof-2026-09-08` (sheep work parked intact in `stash@{0}`; lane committed on top).

- **Starskiff boarding contract, live-proven in PIE** (`Saved/Audit/starskiff_boarding_proof_2026-09-10.json`):
  far/out-of-range refused, in-range-without-precondition refused, `flag.sea_above.starskiff_ready`
  set live → board accepted → possession transferred → 680 cm sustained movement →
  disembark restored Melusina → unboarded traversal refused. Shell confirmed deriving
  from `AMelodiaStarskiffPawn` (registry reflection). Source identical to local `main`,
  so the result covers both lines. Not restart/packaged/input-proven; boarded-traversal
  branch unfired (default target `/Game/ZenForestTest` needs owner approval).
- **MK39 ribcage GN builder, headless-proven** (`Tools/wardrobe_pipeline/proof_mk39_ribcage.py`,
  receipt `Saved/Audit/sea_above/skiff_MK3/mk39_ribcage_proof_2026-09-10.json`):
  `MEL_skiff_ribcage` ported from the 09-05 addon-only build into the repo; hull neutral
  patch synced (already on this branch via `e7628720`); proof caught + fixed a real spacing
  bug (7.615/9 spans 6.768 — now 0.951875 centered, span measures exactly 7.615).
  Hull neutral residual 0.032, dials live, ribcage 216 verts deterministic, Rib Count
  parametrizes. Fixed files synced back to the live Blender addon (hash-verified).
- **Next:** MK39 plates + tenons → rivets → ball joints (proof after each); then updated
  Chladni + Copernicus trimsheet bakes.
- **2026-09-10 later — MK39 plates done:** `MEL_skiff_plates` authored fresh in
  `deploy/surreal_arch/melodia_gn/starskiff_biomech.py` (parametric strake patch +
  tenon tabs + boolean mortise notches, instanced per rib bay); proof
  `Tools/wardrobe_pipeline/proof_mk39_plates.py` green (52 nodes, 306 verts/9 bays,
  rows/tenon/gap dials all live, receipt `Saved/Audit/sea_above/skiff_MK3/`).
  Fixed files synced to the live Blender addon (hash-verified).
- **Branch-health flag (not this lane):** this branch's `melodia_gn/__init__.py` imports
  `barrel_vault_kit`, which does not exist in the tree — normal package import dies,
  so the plates proof loads modules by path. Owner/daemon lane to resolve.
- **2026-09-10 later — MK39 rivets done:** `MEL_skiff_rivet_lattice` in the same module
  (6x-pitch rivet rows on bay edges + scaled collar studs via a t_param field/collar
  split); proof `Tools/wardrobe_pipeline/proof_mk39_rivets.py` green (53 nodes,
  3276 verts/9 bays, bays/diameter/collar dials live, receipt `Saved/Audit/`).
  Proof caught two real defects: COMPARE is almost-equal (collar split needs
  GREATER_THAN), and fields sample in consumer-geometry context (t_param store moved
  upstream of the arc deform). Addon re-synced (hash-verified).
- **2026-09-10 later — MK39 ball joints done:** `MEL_skiff_balljoints` in the same module
  (ball + squashed collar ring instanced at 18 keel/gunwale stations from the measured
  table via a static index-selected lookup chain); proof
  `Tools/wardrobe_pipeline/proof_mk39_balljoints.py` green first try (73 nodes,
  1692 verts, span 7.695, ball/collar dials live, receipt `Saved/Audit/`).
  MK39 builder set complete: ribcage → plates → rivets → balljoints. Addon re-synced.
- **2026-09-10 later — Chladni rescue + skiff extension done:** `chladni_layers.py`
  ported from the addon-only 09-06 build; added `MEL_skiff_chladni_plates`
  (strake-tuned modes m6/n2, 320-640 Hz shimmer defaults, same bake contract);
  proof `Tools/wardrobe_pipeline/proof_mk39_chladni.py` green on both builders
  (neutral 0.0, amplitude + mode dials live, psi/amplitude attrs present).
  Proof caught a dead primary path: `GeometryNodeInputUV` is undefined in 5.2,
  so both builders now read UVs via named attribute (position fallback kept).
  Addon re-synced (hash-verified).
- **2026-09-10 later — updated bakes staged, import handed over:** fresh 2048 wood
  (6 maps) + regal (13 maps) bakes re-ran clean with manifests into
  `Saved/Audit/melusina_lookdev/houdini_variants/`; one-shot import contract in
  `Saved/Audit/sea_above/skiff_MK3/STARSKIFF_BAKE_IMPORT_RUNBOOK_2026-09-10.md`.
  Import did NOT run tonight (fresh editor PID 49136: Rider Python bridge down,
  :9316 without listener). Note PR #188 moved Starskiff textures to
  `/Game/Melodia/SeaAbove/Textures/` — the 09-04 spec's old Clothes/ base is stale.
  Chladni builder (`chladni_layers.py`) found addon-only, same rescue pattern as the
  ribcage was; queued with the import.
