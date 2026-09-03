# Grand Review Document — 2026-09-01

**Date:** 2026-09-01
**State:** post-cymatics-commit, editor-stuck, ready-for-level-build
**Last successful commit:** `cdda0384` — fix(input): cymatics ticker include, mobile touch, cursor role mapping
**Companion manifests:** `ue_level_building_coinsheet_2026-09-01.json` · `grand_review_expansion_plan_2026-09-01.json` · `P0_TASK_LEDGER.json` (8/8 gates pass)
**SSOT:** `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` §1–9 · `CURRENT_SYSTEM_MAP.md`

---

## 1. Purpose & Authority

This document is the **grand-review anchor** (Recommendation 6 of 7). It consolidates the
2026-09-01 coinsheet state, the 7-recommendation expansion plan, and the toolchain master index
into a single navigable record. It does **not** replace `P0_TASK_LEDGER.json` (gate truth),
the Master Index (toolchain SSOT), or `CURRENT_SYSTEM_MAP.md` (portfolio pipeline map).

**Evidence policy:** Source presence, offline proof, live proof, and packaged proof are distinct
(P0_TASK_LEDGER.json `evidence_policy`). Historical passes apply only to their captured baselines.

---

## 2. Where We Are (Coinsheet Summary)

### 2.1 P0 Gates — 8/8 pass

| Gate | Status | Evidence pointer |
|------|--------|-----------------|
| `rhythm_owner` | **pass** | Ledger 2026-08-28T21:43:00 session-7aa8ad8a — BP_BattleController sole damage authority; MelodiaUIBridgeSubsystem viewport overlay; consume-once session lifecycle. Re-verified 2026-09-01 hython+UE import. |
| `hud_single_writer` | **pass** | 2026-08-27 live PIE — BP_BattleController ↔ BP_BattleUI_C_0 bidirectional link MATCH; vestigial `melodiaBattleUI`/`MelodiaUI` vars are inert (owner decision pending to retire). |
| `rhythm_grade_to_result` | **pass** | Ledger 2026-08-28T21:43:05 — Q/W/O/P → EMelodiaSkillGrade translation; monotonic multipliers verified. |
| `static_gates` | **pass** | Ledger 2026-08-29T03:22:56 session-e4ee8de9 — full editor-backed chain 5/5 PASS; canonical reorder 6/6; verify_baseline 55 clean. |
| `battle_integration_map` | **pass** | 2026-08-27 live PIE on MelodiaIntegrationMap — all 4 terminal outcomes (victory/defeat/fled/unavailable) typed correctly; Quill resumes exactly once; atomic commit proven (quest→reward→flag→Script end). |
| `wardrobe_equip_roundtrip` | **pass** | 2026-09-01 focused-viewport real-input — Cos_Accessories_MelusinaV2 auto-equip verified; save→restart→load restores Accessories slot; visual evidence `Saved/Audit/p0_real_input_run/02_music_node_stepped_outfit_unlocked.png`. |
| `wardrobe_gameplay_hook` | **pass** | 2026-09-01 — Accessories unlocks `capability.melodia.glide`; airborne Glide accepted / grounded rejected (`glide_requires_airborne_state`). Visual evidence `…/03_jump_and_airborne_glide.png`. |
| `music_world_key` | **pass** | 2026-09-01 — PCGHeroMusicNode_0 Perfect(100) → `challenge.first_resonance_echo` → Glide cosmetic → `BP_MelodiaPortal_Hub` IsTraversalUnlocked false→true → TryInteract succeeded. Visual evidence `…/01_initial_playerstart_portal_locked.png` + `…/04_portal_unlocked_and_interacted.png`. |

Source: `ue_level_building_coinsheet_2026-09-01.json` §recorded_gates + `P0_TASK_LEDGER.json` §active_p0_gates.
Bounded historical evidence (runtime/save_load/repeat_consume/package_launch — all 2026-08-13/14) remains stale and is not current certification.

### 2.2 Hython Asset State (completed 2026-09-01)

| Asset class | Count | Detail |
|-------------|-------|--------|
| Cymatic variants | 21 | 1665 PNGs 1024×1024, height PNGs 185, contact sheets 7 — manifest `copernicus_cymatic_manifest.json` |
| Faraway Mother GN builders | 16 | 8 existing + 8 V3 (walkway straight/curved, frill rock/arch, lace tree, pearl bush, silk vine, brocade flower) |
| Hero meshes | 3 | SM_FM_MotherSilhouette (66177 pts / 65536 faces), SM_FM_EyeLandmark, SM_FM_Lantern; plus SM_ClothMountains_v0.obj (8.8 MB) |
| Fabric textures | 3 | T_FM_PleatDetail_N, T_FM_PleatDetail_2_N, T_FM_SeamMask — all tilecheck:pass |
| Structural columns | 5 | Doric/Ionic/Corinthian/Fluted/Twisted — 9 PBR maps each |
| Flipbooks | 80 frames × 5 maps / 199.8 MB (8-frame variant also present) | via `Tools/Houdini/flipbook_aaa.py --frames 8` and full set |

Hython: `22.0.368` ✅. Editor gate: `MODAL_OPEN` — port 9316 MCP unreachable until restart (see §7).

### 2.3 Known Gaps (not P0 blockers)

- **Starskiff** — unplaced Pawn shell `BP_Starskiff_MK2`, no boarding/movement/input/consumer.
- **Shorewake dress** — 2-bone skeleton vs Melusina 465-bone incompatibility.
- **Editor modal** — recurring empty-title modal blocks 9316/Monolith/PIE/gates.

---

## 3. The 7 Recommendations — Cross-Reference Matrix

Each recommendation below maps to its expansion-plan phase, coinsheet entry, Master Index section,
deliverables, dependencies, and deadline.

### Rec 1 — Cymatics to PRESENT (§1) ⭐ Entry gate

| Field | Value |
|-------|-------|
| **Action** | Promote `UMelodiaCymaticsSubsystem` from SCAFFOLDED (§2) to PRESENT (§1) |
| **Plan phase** | `phase_1_cymatics_present` — deadline **2026-10-01** |
| **Coinsheet ref** | `grand_review_recommendations.recommendation_1_cymatics_present` — pending; deps: uplugin wiring, PostConfigInit verification |
| **Master Index refs** | §1 PRESENT (add row), §2 SCAFFOLDED (graduate row), §7 cymatics thread, §9 checklist items 1–2 |
| **Deliverables** | `cymatics_present_status.json` · `cymatics_in_master_index.md` |
| **Blocking** | Recs 5, 6, 7 depend on this |
| **What "done" means** | `UMelodiaCymaticsSubsystem` listed in Master Index §1; `BS_GodFile.uproject` verifies PostConfigInit module load; cymatic PBR is a first-class pipeline step (not ad-hoc); World Field Bus §5 adds cymatic pattern fields; `P0_TASK_LEDGER.json` records `cymatics_present` status |

Depends on: *(none — entry gate)*.

### Rec 2 — Faraway Mother to P1 First-Class

| Field | Value |
|-------|-------|
| **Action** | Elevate Faraway Mother to P1 first-class subsystem with ledger, docs, taxonomy, pipeline |
| **Plan phase** | `phase_2_faraway_p1` — deadline **2026-10-15** |
| **Coinsheet ref** | `recommendation_2_faraway_p1` — pending; deps already satisfied: P0 closeout ✅, asset verification ✅ |
| **Master Index refs** | §6 Houdini execution plan (upgrade from `MARA_P0_P3_HOUDINI_EXECUTION_PLAN` — note: Faraway Mother is P2 scope, distinct from Mara terrain HDAs) |
| **Deliverables** | `faraway_p1_status.json` · `faraway_onboarding_guide.md` · `faraway_in_taxonomy.md` |
| **Work items** | Add to `P1_TASK_LEDGER.json` with pass+evidence; integrate 16 GN builders into §2 Master Taxonomy; add Faraway Mother texture pipeline to material orchestration flow; add GN parallel lane to main hython plan |

Depends on: **Rec 1**.

### Rec 3 — Hython ↔ Monolith Dual-Path Bridge

| Field | Value |
|-------|-------|
| **Action** | Fix Monolith 9316 connectivity + create parallel hython/Monolith generation with cross-path validation |
| **Plan phase** | `phase_3_hython_monolith_bridge` — deadline **2026-11-01** |
| **Coinsheet ref** | `recommendation_3_hython_monolith_bridge` — pending; deps: firewall, monolith restart, validation script; *note: coinsheet typo `hythm_monolith_bridge_report.json` → correct `hython_monolith_bridge_report.json`* |
| **Master Index refs** | §1 Houdini/Monolith PRESENT, §6 Houdini plan, §9 item 6 (one editor, one :9316) |
| **Deliverables** | `hython_monolith_bridge_report.json` · `cross_path_validation.py` · `monolith_execution_plan_parallel.py` |
| **Work items** | Fix 9316 (check `.monolith_running`, firewall, restart — see `LEVEL_DESIGNER_ONBOARDING.md` editor-recovery steps); create Monolith execution plan parallel to hython (Phase A material ops, Phase B hair/WP captures, Phase C docs); validation script comparing height maps/meshes/texture sets; promote Monolith from alternative to first-class generation path |

Depends on: **Rec 1, Rec 2**.

### Rec 4 — P1–P3 Scope & Roadmap

| Field | Value |
|-------|-------|
| **Action** | Extend P0 scope to P1–P3 with proper roadmap integration |
| **Plan phase** | `phase_4_p1p3_ecosystem_integration` (shared with Rec 5) — deadline **2026-12-01** |
| **Coinsheet ref** | `recommendation_4_p1p3_scope` — pending; deps: P0 closeout ✅, grand review approval |
| **Master Index refs** | §5 contracts (World Field Bus + SpeedTree bridge) — roadmap must reuse, not reinvent |
| **Deliverables** | `p1p3_roadmap.json` · `cross_system_mappings.json` (shared with Rec 5) |
| **Work items** | P1 closeout items → `P0_TASK_LEDGER.json`; P2/FarawayMother → P1 closeout roadmap; P3 horizon (cymatics V3/V4, new GN families); align to `CURRENT_SYSTEM_MAP.md` §5 data-flow |

Depends on: **Recs 1, 2, 3**.

### Rec 5 — Ecosystem Integration (Cymatics ↔ Faraway ↔ Water/Rhythm/Wardrobe)

| Field | Value |
|-------|-------|
| **Action** | Wire cymatics + Faraway Mother into the broader Melodia ecosystem |
| **Plan phase** | `phase_4_p1p3_ecosystem_integration` — deadline **2026-12-01** |
| **Coinsheet ref** | `recommendation_5_ecosystem_integration` — pending; deps: cymatics_present, faraway_p1, hython_monolith_bridge |
| **Master Index refs** | §5a SpeedTree semantic bridge (9 fields), §5b World Field Bus (8 fields), §7 synesthesia tiers, §8 integration spikes |
| **Deliverables** | `ecosystem_integration_report.json` · `p1p3_roadmap.json` · `cross_system_mappings.json` |
| **Work items** | cymatic patterns → rhythm combat grades; Faraway textures → wardrobe fabric authority; Faraway meshes → PCG population; cymatic standing waves → water ripples; cross-system material mappings (cymatic PBR → water PBR → wardrobe PBR). See `cross_system_integration_map.md` §2–6. |

Depends on: **Recs 1, 2, 3**.

### Rec 6 — Grand Documentation (This Document Set) ← You Are Here

| Field | Value |
|-------|-------|
| **Action** | Produce durable onboarding and integration documentation |
| **Plan phase** | `phase_6_grand_documentation` — deadline **before new team member onboarding** |
| **Coinsheet ref** | `recommendation_6_grand_documentation` — **this task fulfills it** |
| **Master Index refs** | §9 evidence standard (offline + live PIE + ledger row); §1–9 anti-duplication checklist |
| **Deliverables** | `grand_review_document.md` (this file) · `onboarding_guide.md` · `cross_system_integration_map.md` — all in `Saved/Audit/` |
| **Duplication guard** | Intentionally scoped to NOT duplicate: `LEVEL_DESIGNER_ONBOARDING.md` (greybox/PCG), `ONBOARDING_LIVE_COLLAB.md` (Blender LiveLink), `Docs/Research/` toolchain research — see §6. |

Depends on: **Recs 1–4 in progress** (docs track the plan; they do not block it — they codify it).

### Rec 7 — User-Facing Features (Cymatic Params + Wardrobe Selection)

| Field | Value |
|-------|-------|
| **Action** | Build user-adjustable cymatic parameters + Faraway Mother wardrobe selection UI |
| **Plan phase** | `phase_user_facing` — deadline **before next user playtest** |
| **Coinsheet ref** | `recommendation_7_user_facing_features` — pending; deps: cymatics_present, faraway_p1, ecosystem_integration |
| **Master Index refs** | §1 audio-reactive writer (single writer — never add a second); UI token SSOT `melodia-design-system/tokens.json` (see AGENTS.md UI/artist skill) |
| **Deliverables** | `user_facing_features_spec.json` |
| **Work items** | Cymatic pattern browser (21 variants); Faraway Mother outfit selector through `MelodiaWardrobeSubsystem` (must not invent slots); adjustable cymatic params via `UMelodiaCymaticsSubsystem` (read-only consumer of `MPC_Melodia_Palette`); integration with rhythm patterns; playtest-ready |

Depends on: **Recs 1, 2, 5**.

### Dependency Graph (ASCII)

```
Rec1 (Cymatics PRESENT) ─┬─► Rec2 (Faraway P1) ──► Rec3 (Hython↔Monolith) ─┬─► Rec4 (P1-P3 roadmap)
                         │                    ▲                          │         ▲
                         └────────────────────┘                          └─────────┘
                         │                                               ▲
                         └──────► Rec5 (Ecosystem) ◄────────────────────┘
                                    │
Rec6 (Docs) ◄──── Rec1,2,3,4 ───────┘  (tracks; does not block)
Rec7 (User-facing) ◄──── Rec1,2,5 ───┘
```

---

## 4. Faraway Mother — Current Inventory (for Recs 2, 5, 7)

| Layer | Detail |
|-------|--------|
| GN builders (16) | MEL_mother_head_silhouette, hair_cascade, valley_depression, fog_volume, fabric_ridge, shoulder_fold, heart_gate, moonlight_rig (existing 8) + walkway_straight/curved, frill_rock/arch, lace_tree, pearl_bush, silk_vine, brocade_flower (V3 8) |
| Hero meshes | SM_FM_MotherSilhouette / EyeLandmark / Lantern + SM_ClothMountains_v0 (8.8 MB) |
| Textures | Content/Textures/FarawayMother_Suites — 6 suites × full PBR (BC,N,R,ORM,AO,H,M,Sheen,Alpha,Mask); 12 V3 assets (walkways, frill rocks, lace trees, ...); contact sheet 2.2 MB + V3 pending |
| Constants | BASE_H 140 / PLEAT_AMP 60 / PLEAT_PERIOD 88 / SEAM_DEPTH 90 / SEAM_WIDTH 26 / MOTIF_PERIOD 46 / MOTIF_H 9 — hython 22.0.368, 100× cm, Nanite hero mesh |
| Pipeline | 5→9 cymatic variants added (CherryBlossomWood, GildedCoral, StarlitAbyss, FrozenFracture); all 9 baked 1024² + 2048² (81 PNGs); skill `melodia-copernicus-parallax` updated; 3 cron jobs (flipbooks, expansion, session saver) |

---

## 5. Cymatics — Current Inventory (for Recs 1, 5, 7)

| Layer | Detail |
|-------|--------|
| Generator | `Tools/Houdini/copernicus/copernicus_cymatic_parallax.py --cook` — 21 variants, schema `melodia.copernatic_cymatic_parallax.v2`, seed 2026-08-31 |
| Variants (21) | CymaticMarble, CherryBlossomWood, DancingCrystals, GildedCoral, GildedLoom, SilkWaterfall, StarlitAbyss, FinalDreamweaver, FractalCathedral, FrozenFracture, CavernWeave, GlitterCrystal/Gold/Holographic/Iridescent/Rainbow, GoldenSpiralGrove, SingingConstellations, SpiralMonument, TessellationSanctum, VoronoiSacredGeometry |
| Output | 1665 PNGs + 185 height maps + 6 PIL contact sheets; cosmic/gilded confirmed 21/21 |
| Engine hook | `Source/.../MelodiaCymaticsSubsystem.h/.cpp` — read-only consumer of `MelodiaAudioReactivePresentationSubsystem` MPC writer (single audio writer — never add a second). Committed change: `#include "Containers/Ticker.h"` + newline at EOF; `MelodiaInputContextSubsystem.cpp` Tick + platform touch + cursor role mapping |
| Integration path | Cymatic PBR → `UMelodiaCymaticsSubsystem` → MPC BeatPulse/Phase/Intensity → PPV/Niagara/Material (tiers 1–3 are PRESENT per §7) |

---

## 6. Duplication Guard — What This Does NOT Replace

| Existing doc | Its lane | This doc's relation |
|-------------|----------|---------------------|
| `Docs/LEVEL_DESIGNER_ONBOARDING.md` | Greybox→PCG→validation loop | Not duplicated — onboarding_guide.md §2 links to it as prerequisite |
| `Docs/ONBOARDING_LIVE_COLLAB.md` | Blender ↔ Unreal LiveLink streaming | Not duplicated — onboarding_guide.md §3 links to it for live-collab lane |
| `Docs/GRANDMASTER_MASTER_PLAN_V2.md` (2026-07-15) | TouchDesigner/Spout/OSC integration | Superseded scope — not duplicated; TD lane now inherits Master Index §4 external-tool rule |
| `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` | Torchchain SSOT §1–9 | Extended, not replaced — §3 cross-refs it; §5 items 1–2, 5–7 build on its contracts |
| `CURRENT_SYSTEM_MAP.md` + `Docs/Research/AGENT_TOOLCHAIN_DISCOVERY_INDEX_…` | Portfolio pipeline / toolchain discovery maps | Complemented — integration map uses them as subsystem boundaries |
| `P0_TASK_LEDGER.json` | Gate ledger (8/8 pass) | Sourced, not rewritten — §2.1 is a dated snapshot; ledger remains authority |

Verification method: `hermes_search_files` + manual `ls` of `Docs/` and `Saved/Audit/` on 2026-09-01 found no prior `grand_review_document.md`, `cross_system_integration_map.md`, or `grand_review`-scoped onboarding guide — this set is net-new.

---

## 7. Critical Path & Immediate Next Steps

From `ue_level_building_coinsheet_2026-09-01.json` §critical_path — ordered, editor is gate 0:

1. **Editor recovery** — kill MODAL_OPEN, restart Unreal, verify `netstat -ano | findstr :9316`, `hermes gateway start` if needed (from coinsheet §2.1 recovery_steps).
2. Verify MCP on 9316 (`curl http://127.0.0.1:9316/health` → 1330+ tools).
3. Faraway Mother material audit (parallax, COPs, Nikki review).
4. Expand GN variant builders (V3 new 8).
5. Run flipbooks `--frames 16` for selected variants.
6. Generate 4K hero sets for strongest 2–3 variants.
7. Update `melodia-copernicus-parallax` skill (done for 9-variant set; needs 21-variant refresh).
8. Close remaining P0 gates — already 8/8 pass; re-run `static_gates` with refreshed baseline (ledger row required).
9. Re-run `static_gates` with refreshed baseline.
10. Long-term doc generation — **this filing closes Rec 6 items 1–3.**

Subagent queue (7): rec_1 cymatics_present → rec_2 faraway_p1 → rec_3 hython_monolith_bridge → rec_4 p1p3_scope / rec_5 ecosystem_integration (parallel) → rec_6 grand_documentation (this) → rec_7 user_facing.

---

## 8. File Index for This Review

| File | Role | Status |
|------|------|--------|
| `Saved/Audit/ue_level_building_coinsheet_2026-09-01.json` | Coinsheet SSOT (state, assets, gates, 7 recs) | committed |
| `Saved/Audit/grand_review_expansion_plan_2026-09-01.json` | Phases 1→4 + subagent queue + phase deliverables | committed |
| `Saved/Audit/copernicus_cymatic_manifest.json` | 21-variant generation manifest | committed |
| `Saved/Audit/faraway_mother/` | Fabric texture + cloth-mountain manifests | committed |
| `faraway_mother_heroes_manifest.json` / `cloth_mountains_v0_manifest.json` | Hero mesh manifests | committed |
| `Saved/Audit/cross_system_integration_map.md` | System interconnect map (companion) | **this review — new** |
| `Saved/Audit/onboarding_guide.md` | New-member onboarding outline (companion) | **this review — new** |
| `Saved/Audit/grand_review_document.md` | This file — Rec 6 deliverable 1/3 | **new** |

---

*Generated for Rec 6 — `recommendation_6_grand_documentation`. Mark that JSON entry to `in_progress`/`complete` and append a ledger note when human review approves this set. Sources are cited inline; prose is not a gate row.*
