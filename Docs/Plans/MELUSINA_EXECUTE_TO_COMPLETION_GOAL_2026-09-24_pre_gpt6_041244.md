# Melusina DollKit -- EXECUTE TO COMPLETION GOAL (2026-09-24)

**Status:** CURRENT EXECUTE GOAL
**Date:** 2026-09-24 (America/Toronto)
**Doctrine:** EXECUTE TO COMPLETION -- checklist until COMPLETE with date stamp. Not research-only.
**Machine:** fromage (`6402dab1-6635-4abb-8220-27a07354b444`)
**Blender:** 5.2 LTS (session; hierarchy dump used 5.2.1 LTS)

**Agent/work SSOT:** `Saved/Audit/MELUSINA_EXECUTE_TO_COMPLETION_GOAL_2026-09-24.md`
**Owner browse path:** `Docs/Plans/MELUSINA_EXECUTE_TO_COMPLETION_GOAL_2026-09-24.md`
(Identical full copies in both places.)

**Pointer:** `Saved/Audit/MELUSINA_GOAL_POINTER.txt`

**Supersedes as active execute SSOT:**
- `Saved/Audit/DOLLKIT_CONVERGENCE_GOAL_2026-09-24.md` remains the **runtime / convergence companion** (phases A-D language kept; execution checklist lives here).

**Complements (still authoritative for their lanes):**
- `Saved/Audit/MELUSINA_GN_PLAN_2026-09-24.md` (+ Docs/Plans twin) -- GN builders / House lane; Phase 1+ surface detail executes under THIS goal; GN builders still apply.
- `Saved/Audit/DOLLKIT_RUNTIME_GAP_MAP_2026-09-24.md` -- preview BP -> runtime unit gaps.
- `Saved/Audit/DOLLKIT_SSOT_PARK_2026-09-24.md` -- Staging DollBall_* is NOT SSOT.
- `Saved/Audit/ORIANNA_TO_MELDOLLRIG_MAP_2026-09-24.md` -- head/station map; MEL_DollRig **15 bones**.
- `Saved/Audit/ASHLOTTE_CENSUS_2026-09-24.md` -- balljoint + cogwheels study vocabulary (IP study-only).

---

## 1. North star

Finalized **segmented BJD Melusina runtime unit** with **detailed surface modelling** at joints / segments / gears (porcelain seams, cuff rims, gear teeth, panel gaps) using **MESHmachine + MACHIN3tools + CURVEmachine** for edit-mesh detail and **Higgsas Geometry Nodes** (via `higgsas_bridge` / `melodia_gn`, no silent fallback) for parametric / repeatable builders (+ support plugs as needed), then **UE P9 authority** + pawn path.

User ask folded in: *"use MeshMachine 5.2 and various plugs for detailed surface modelling"* = Blender **5.2** + **MESHmachine** (and companion MACHIN3 / CURVE plugs), not a product named MeshMachine 5.2. Owner also folded **Higgsas nodes** into the primary parametric lane.

### Definition of DONE (mark COMPLETE when all checked)

- [x] **E0** Plug audit receipt + surface-detail workfile duplicate created; Staging DollBall not treated as SSOT
- [ ] **E1** MeshMachine joint/cuff surface pass on all P9 ball stations; stills banked under `Saved/Audit/melusina_doll_surface_20260924/` *(PARTIAL 2026-09-24 ~04:03 ET: neck+shoulder_L MCP stash/bevel/OpenGL stills saved in SurfaceDetail; Y-menu chamfer/fuse/normal_transfer taste still owner; NOT COMPLETE — do not start E2)*
- [ ] **E2** Gear / moving-piece tooth + cluster silhouette pass (shoulder/hip primary)
- [ ] **E3** Light hard-surface language on segment SKM edges (not full armor)
- [ ] **E4** Bone-parent balls/cuffs/gears to MEL_DollRig 15 bones; keeper parent=null debt cleared
- [ ] **E5** GN parametrize `MEL_doll_*` with presets from P9+E1 measurements; headless receipts (parallel OK after E1 reference)
- [ ] **E6** P9/detail GLB export; owner Output Log reimport; Ctrl+S; CuteIdle visual gate green
- [ ] **E7** Runtime unit scaffold from gap map (sockets, capsules, camera, pawn)
- [ ] **E8** CURRENT_STATE bump; docs PR; **this goal marked COMPLETE with date stamp**

---

## 2. Tooling bible (Blender 5.2 addons -- verified 2026-09-24)

**Addons root:** `C:\Users\froma\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\`

### Primary (use heavily)

| Plug | Verified version | When to use |
|---|---|---|
| **MESHmachine** (MACHIN3) | **0.16.0** | Fuse/unfuse, chamfer, fillets, stashes, Boolean cleanup, normal transfers, surface patches on ball sockets and segment rims. Primary tool for porcelain seam + cuff rim detail. |
| **MACHIN3tools** | **1.10.1 DeusEx** | Focus, smart vert/edge/face, mirror, align, cleanup, modes. Daily navigation + topo hygiene around MeshMachine ops. |
| **CURVEmachine** | **1.4.1** | Seam curves, cable/pipe accents, cuff profile sweeps -- **sparingly**; protect silhouette. |
| **Higgsas Geometry Nodes** | **v13** (Blender 5.0 library) | Node-group library under `RawArt/BlenderLibraries/Higgsas`; loaded via `deploy/surreal_arch/higgsas_bridge.py` -- **NEVER silent fallback**. Character-relevant DollKit groups: Spur Gear / gear generators (E2 teeth); Rounded Cube / Capsule / Cone (ball+cuff primitives before MeshMachine polish); SDF Boolean / SDF Round Cone (socket cups); Circular Array / Distribute Points on Edges (rivet/fastener rows); Curve FK/IK + Even Curve to Mesh (CURVEmachine companion for hose/wire); Mesh Curvature / AO / Thickness (bake masks later); Surface Bind / Mesh Offset / Solidify (optional conformal plating E3+/Phase4). |

**Doctrine (surface vs parametric):** Edit mesh detail = **MESHmachine + MACHIN3tools**; Parametric / repeatable / GN builders = **Higgsas via melodia_gn** (no silent fallback) + **CURVEmachine** for curve accents.

### Support surface / topo / UV / export (use as needed)

| Plug | Verified version | When to use |
|---|---|---|
| Beavel | 1.1.0 | Bevel weight hygiene on hard edges / cuff rims |
| MeshCleanerPro | 0.1.3 | Post-boolean / post-fuse cleanup |
| SurfaceFill | 0.2.7 | Patch holes / surface fills after MeshMachine ops |
| speedsculpt | 0.2.3 | Organic porcelain softening **only if needed**; do not destroy hard edges |
| quad_remesher | 1.3.0 | Only when topo must ship for bake -- not mid-sculpt thrash |
| quad_unwrap | 1.0.1 | Companion unwrap when bake UVs required |
| ZenUV | 5.0.3.0 | UV ship / bake readiness -- not mid-pass thrash |
| UvSquares-master | 1.15.0 | Square UV islands when packing for bake |
| AdvancedCones | 2.0.2 | Occasional procedural cones / accents |
| coiled_spring | 1.0 | Optional micro spring accents (silhouette-safe only) |
| Handy Curve Profile | 1.4.5 | Profile sweeps with CURVEmachine when cuff profiles need control |
| collider_tools | 1.0.1 | Collision proxy helpers before UE capsule pass |
| send2ue | 2.4.3 | Export/rig bridge -- **careful**; prefer known DollKit GLB path when authority matters |
| ue2rigify | 1.6.2 | Rig bridge -- **careful**; do not explode MEL_DollRig 15-bone map |
| archipack_20 | 2.7.2 | **House lane only** (optional) |
| sverchok-master | 1.4.0 | **House-adjacent only** (optional) |

### NOT found in 5.2 addons (do not claim installed)

HardOps, BoxCutter, DECALmachine, Cablerator, PunchIt, Fluent, KitOps.

These are **optional if owner installs later**; do **not** block E1-E8 on them.

### Optional installs (candidates on disk -- DO NOT install without owner ask)

Scanned `D:\Blender` and `D:\Blender\Blender addons 4.2+` on 2026-09-24:

- **No HardOps / BoxCutter / DECALmachine / Cablerator / PunchIt / Fluent / KitOps zips found.**
- `D:\Blender\Blender addons 4.2+\` holds unrelated packs (SimpleBake, Quad Remesher 1.3, House Craft, etc.) -- not HOps/BC/DECAL install candidates.
- Top-level `D:\Blender\` zips present are unrelated (ARP, UVPackmaster, stylized hair, etc.).
- One incidental path: `...\SimpleBake\...\decal_operators.py` (SimpleBake module name only -- **not** DECALmachine).

If owner later drops HOps/BC/DECAL zips, park paths here and wait for explicit install ask.

**Owned optional zips on disk (DO NOT install without owner ask):**
- `D:\Blender\auto_rig_pro_3.76.14.zip`
- `D:\Blender\uvpackmaster3-addon-3.4.4-u3.zip`
- `D:\Blender\deep_paint_pro_v2.2.0.zip`
- `D:\Blender\stylized_hair_pro_v4_1_2.zip`

HardOps / BoxCutter / DECALmachine remain **non-blocking optional** (not installed; do not block E1-E8).

---

## 3. Workfile discipline

| Rule | Detail |
|---|---|
| Live WIP SSOT (do not casually save) | `C:\EnvironmentPortfolio\harp_bow_pipeline\Melusina_DollKit_WIP_20260923.blend` (~2.46 GB; last saved 2026-09-23 23:45 ET) |
| Surface-detail workfile (preferred) | `C:\EnvironmentPortfolio\harp_bow_pipeline\Melusina_DollKit_SurfaceDetail_20260924.blend` -- **duplicate copy** for MeshMachine passes |
| Promote | Copy approved geo back into SSOT / export set only after visual gate; owner or deliberate agent save of the **duplicate**, never casual overwrite of harp hero |
| Bank keepers | Before destructive fuse/boolean: stash (MESHmachine) + duplicate objects + Audit stills |
| Session lock | **No second interactive Blender** on live harp WIP if another session owns it |
| UE | No agent Monolith `save_packages`; owner Ctrl+S only |
| Export authority | Prefer `Melusina_DollKit_20260923_P9.glb` lineage; detail GLB may be `Melusina_DollKit_20260924_Surface.glb` once E1-E3 ship |

---

## 4. Phases (execute to completion)

### E0 -- Gate (exit before surface damage)

**Exit criteria:**
- [x] Receipt: MESHmachine 0.16.0, MACHIN3tools 1.10.1 DeusEx, CURVEmachine 1.4.1 **present** on Blender 5.2 addons disk (`__init__` versions); headless importable (interactive Preferences enable remains owner confirm if disabled)
- [x] Workfile duplicate `Melusina_DollKit_SurfaceDetail_20260924.blend` created from WIP (do not overwrite WIP)
- [x] P9 stations listed (14 balls): neck, waist, shoulder_l/r, hip_l/r, elbow_l/r, wrist_l/r, knee_l/r, ankle_l/r
- [x] Confirm Staging `DollBall_*` is **not** SSOT (`DOLLKIT_SSOT_PARK_2026-09-24.md`)
- [x] Confirm MEL_DollRig = **15 bones** (not ARP ~1124)
- [x] **Higgsas resolve:** library path exists (`RawArt/BlenderLibraries/Higgsas` v13, 279 groups); `higgsas_bridge` resolved Spur Gear / Rounded Cube / Circular Array (smoke `_e0_smoke.json`); no silent fallback

**Evidence:** `Saved/Audit/melusina_doll_surface_20260924/E0_plug_audit.md` (+ alias `E0_PLUG_AUDIT_2026-09-24.md`); workfile under `harp_bow_pipeline/`
**E0 stamped:** 2026-09-24 ET — PASS (disk gate); proceed E1

### E1 -- Surface detail: joints (MeshMachine primary)

**Intent:** Ashlotte readability -- visible **balljoint ceramic vs metal rim** (study-only cues; Nikki porcelain/brass stay UE keepers).

**Prep landed 2026-09-24 ET (headless):** inventory + station collections + bevel/smooth hints saved into SurfaceDetail; see `melusina_doll_surface_20260924/E1_STATUS_2026-09-24.md` + `OWNER_E1_MESHMACHINE_CLICKLIST.md`.

**MCP partial 2026-09-24 ~04:03 ET (GUI + BlenderMCP :9876):** MESHmachine/MACHIN3tools enabled after Py3.13 `register_classes` patch; neck + shoulder_L stashed via `utils.stash.create_stash`; rim `mesh.bevel` 0.8 mm fallback (modal `machin3.chamfer`/`fuse`/`normal_transfer` cannot finish from MCP); OpenGL stills banked `stills_e1/E1_neck_{key,fill,rim}.png` + `E1_shoulder_l_{key,fill,rim}.png`; SurfaceDetail saved. **E1 = PARTIAL, not COMPLETE.** Owner Y-menu taste + remaining stations still required before E2.

**Exit criteria:**
- [ ] MeshMachine pass on **all** ball stations + cuff rings (fuse/unfuse, chamfer/fillets, seam rings, Boolean cleanup, normal transfers as needed)
- [ ] MACHIN3tools used for mirror/align/cleanup; Beavel / MeshCleanerPro / SurfaceFill as support
- [ ] CURVEmachine only if a cuff profile sweep improves rim without silhouette bloat
- [ ] Stills (key/fill/rim) under `Saved/Audit/melusina_doll_surface_20260924/` for each major station cluster (at least: neck, waist, shoulder, elbow, wrist, hip, knee, ankle) — *neck + shoulder_L MCP stills exist in `stills_e1/` 2026-09-24; owner re-frame recommended; other stations pending*
- [ ] P9 seating numbers remain canon -- surface detail must not bury balls or break station radii

### E2 -- Surface detail: gears and moving pieces

**Prefer:** Higgsas **Spur Gear** / Circular Array (via `higgsas_bridge` + `melodia_gn`, no silent fallback) for parametric teeth before hand-modeling gear teeth. MeshMachine polish after parametric base.

**Exit criteria:**
- [ ] Gear tooth silhouette readable at shoulder/hip clusters (primary) -- **prefer Higgsas Spur Gear / arrays** over hand-modeled teeth
- [ ] Optional micro wrist/ankle gears **only if** silhouette stays clean
- [ ] Stills banked beside E1 set
- [ ] No IP textures/meshes from Ashlotte/Orianna imported into Content

### E3 -- Segment shells (light hard-surface)

**Exit criteria:**
- [ ] Light hard-surface language on segment SKM edges (panel gaps / rim hints) -- **not** full armor plating
- [ ] Conformal plating deferred (GN Phase 4 / optional later) -- do not block DONE
- [ ] speedsculpt only for gentle porcelain soften; hard edges preserved

### E4 -- Bone-parent + bind

**MEL_DollRig 15 bones:**
`spine_01.x`, `spine_03.x`, `neck.x`, `arm.l`, `forearm.l`, `hand.l`, `arm.r`, `forearm.r`, `hand.r`, `thigh.l`, `leg.l`, `foot.l`, `thigh.r`, `leg.r`, `foot.r`

**Station -> bone (from Orianna map / GN plan):**

| Station | MEL bone |
|---|---|
| waist | spine_01.x <-> spine_03.x |
| neck | neck.x |
| shoulder_l/r | arm.l / arm.r |
| elbow_l/r | forearm.l / forearm.r |
| wrist_l/r | hand.l / hand.r |
| hip_l/r | thigh.l / thigh.r |
| knee_l/r | leg.l / leg.r |
| ankle_l/r | foot.l / foot.r |

**Exit criteria:**
- [ ] Balls / cuffs / gears bone-parented to correct MEL_DollRig bones
- [ ] Keeper `parent=null` debt cleared for surface keepers (dump may still note historical nulls until this lands)
- [ ] Motion smoke: pose arm/leg -- balls/gears follow; seating not buried

### E5 -- GN parametrize (parallel OK after E1 reference)

From GN plan builders (still apply):
- `MEL_doll_ball_joint`, `MEL_doll_cuff_ring`, `MEL_doll_gear_cluster` (+ compose existing `MEL_doll_socket`; migrate useful bits from `MEL_bionic_joint`)
- Presets seeded from **P9 seating + E1 measured radii/bevels**
- Headless receipts under `Saved/Audit/melusina_doll_gn/`
- **Prefer Higgsas Spur Gear / Circular Array** for `MEL_doll_gear_cluster` parametric teeth (via bridge + gate; **no silent fallback**) before hand-modeled teeth
- GN Stack category **"Melusina Doll"** when first new builder lands

**Exit criteria:**
- [ ] Builders register + headless construct smoke green
- [ ] Presets encode E1 reference measurements
- [ ] Gear builders prefer Higgsas Spur Gear / arrays (gate loud if unresolved)
- [ ] Do not casual-replace instances inside live WIP; scratch/construct first

### E6 -- Export + UE

**Exit criteria:**
- [ ] Detail/P9 GLB exported (seating gates intact)
- [ ] Owner Output Log: `py "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/_dollkit_p9_reimport_inner.py"` (or updated surface-aware driver)
- [ ] Owner **Ctrl+S** (agents do not save packages)
- [ ] Visual gate: balls seated, gears move, **CuteIdle** still plays on `BP_MelusinaDollKit_Preview`
- [ ] Stamp `Saved/Audit/DOLLKIT_P9_UE_REIMPORT_RECEIPT.md` (assets touched)
- [ ] Do not overwrite keepers: `IK_MEL_DollRig`, `RTG_Melusina_to_DollRig`, preview BP, Nikki MIs

**Blocker known:** UE remote Python UDP 6766 not advertising -- owner one-liner is the path.

### E7 -- Runtime unit (from gap map)

**Exit criteria:**
- [ ] Socket board on preview / scaffold: `socket_weapon_r/l`, `socket_familiar`, `socket_vfx_chest`, `socket_gear_shoulder_l/r`, `socket_gear_hip_l/r`
- [ ] Capsule chain per major segment (not one blob); camera boom compatible with doll proportions
- [ ] Pawn scaffold from `BP_MelusinaDollKit_Preview` (child or replace Melusina pawn path)
- [ ] ABP owns `MEL_DollRig` (not hero Melusina body)
- [ ] Physics: balls kinematic or no-collision; gears cosmetic

### E8 -- Docs / ship

**Exit criteria:**
- [ ] `CURRENT_STATE` DollKit G1->G2 (or equivalent) when E6 visual gate green
- [ ] Docs-only PR: this goal + pointer + surface still index (no fat content)
- [ ] Content PR only after owner Ctrl+S and clean package list
- [ ] **Mark this goal COMPLETE with date stamp** (YYYY-MM-DD ET)

---

## 5. House lane note

House GN continues **in parallel** per `MELUSINA_GN_PLAN_2026-09-24.md` (foundation -> shell -> openings; `MEL_mh_porch_stair` next when Packet D pulled).

**House is NOT required for DollKit DONE.** Do not park House on character; do not park DollKit on House.

archipack_20 / sverchok-master remain optional House-adjacent plugs only.

---

## 6. Explicit non-goals / constraints

- No Monolith `save_packages` / `recompile_material` from agents.
- Do not casually save live harp / DollKit WIP blend; prefer SurfaceDetail duplicate.
- Do not open a second interactive Blender on live harp WIP if another session owns it.
- Staging `DollBall_*` and takeover FBX are **not** DollKit SSOT.
- Orianna + Ashlotte = **study only** -- never ship their IP into Melodia Content.
- Do not explode bone count (fingers/toes) without mocap need.
- Do not overwrite IK / RTG / preview BP / Nikki MIs on reimport.
- New Bot materials / HandpaintPrep / smart-mats converge later -- **do not wipe** Nikki porcelain/brass keepers.
- Runtime Sample Sound on the doll pawn forbidden (bake-lane audio attrs only).
- Silent Higgsas fallback forbidden.
- Do not claim HardOps / BoxCutter / DECALmachine / Cablerator / PunchIt / Fluent / KitOps are installed.
- Do not install optional addons without owner ask.
- Do not download archives as part of this goal execute.
- Do not thrash quad_remesher / ZenUV mid-sculpt; bake-ship only.

---

## 7. Owner actions owed

- [ ] Enable / confirm MESHmachine + MACHIN3tools + CURVEmachine in Blender 5.2 if any are disabled
- [ ] Output Log P9 (or surface) reimport one-liner when E6 ready
- [ ] Ctrl+S after dirty UE reimport
- [ ] Optional: install HOps/BC/DECAL later if desired -- not blocking
- [ ] Optional: re-enable Python Remote Execution (UDP 6766) so agents can push UE scripts

---

## 8. Agent next actions (immediate 5 steps)

1. **E0 DONE** (2026-09-24 ET disk gate PASS) — SurfaceDetail workfile + plug audit + Higgsas resolve.
2. **E1 inventory:** open SurfaceDetail only; dump ball/cuff/gear objects → `melusina_doll_surface_20260924/E1_station_inventory.json`.
3. **E1 MeshMachine prep (scriptable):** bevel weights / smooth / stash-ready / station selection sets; neck + shoulder_L first.
4. **E1 interactive (owner/Brennan):** MeshMachine Y-menu fuse/fillet/seam on neck + shoulder_L per `OWNER_E1_MESHMACHINE_CLICKLIST.md` if headless cannot drive UI.
5. **Parallel (non-blocking):** scaffold `MEL_doll_ball_joint` dial/preset matrix from P9+E1 numbers under `Saved/Audit/melusina_doll_gn/` without replacing WIP instances.

---

## 9. Evidence path index

| Path | Role |
|---|---|
| `Saved/Audit/MELUSINA_EXECUTE_TO_COMPLETION_GOAL_2026-09-24.md` | This execute SSOT |
| `Docs/Plans/MELUSINA_EXECUTE_TO_COMPLETION_GOAL_2026-09-24.md` | Browse twin (identical) |
| `Saved/Audit/MELUSINA_GOAL_POINTER.txt` | Active execute pointer |
| `Saved/Audit/DOLLKIT_CONVERGENCE_GOAL_2026-09-24.md` | Runtime/convergence companion |
| `Saved/Audit/DOLLKIT_RUNTIME_GAP_MAP_2026-09-24.md` | E7 gaps |
| `Saved/Audit/DOLLKIT_SSOT_PARK_2026-09-24.md` | Staging park |
| `Saved/Audit/MELUSINA_GN_PLAN_2026-09-24.md` | GN builders + House |
| `Saved/Audit/ORIANNA_TO_MELDOLLRIG_MAP_2026-09-24.md` | Station/head map |
| `Saved/Audit/ASHLOTTE_CENSUS_2026-09-24.md` | Balljoint/cogwheel study |
| `Saved/Audit/mel_dollrig_hierarchy_2026-09-24.json` | 15-bone dump |
| `Saved/Audit/melusina_doll_surface_20260924/` | E0-E3 stills + receipts (create) |
| `Saved/Audit/melusina_doll_gn/` | E5 GN receipts (create) |
| `Saved/Audit/_dollkit_p9_reimport_inner.py` | Owner UE reimport |
| `harp_bow_pipeline/Melusina_DollKit_WIP_20260923.blend` | Live WIP SSOT (no casual save) |
| `harp_bow_pipeline/Melusina_DollKit_SurfaceDetail_20260924.blend` | Surface pass workfile (create) |
| `harp_bow_pipeline/Melusina_DollKit_20260923_P9.glb` | P9 export lineage |
| `/Game/Melodia/Characters/Melusina/DollKit/` | UE DollKit content |

---

## 10. Completion stamp

When E0-E8 are checked:

```
STATUS: COMPLETE
Completed: YYYY-MM-DD HH:MM ET
```

Until then: **STATUS: CURRENT EXECUTE GOAL -- IN PROGRESS**

---

*End of EXECUTE TO COMPLETION GOAL 2026-09-24.*
