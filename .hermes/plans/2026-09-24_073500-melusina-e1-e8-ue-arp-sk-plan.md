# Melusina E1–E8 UE staging, polish, and test plan

**For Hermes:** Execute this plan task-by-task. Keep Blender and Unreal work serialized through one live holder at a time. Do not claim completion from source, exports, or probe-only receipts.

**Goal:** Finish the segmented Melusina DollKit from E1 surface correction through E8 closeout, then prove it in UE 5.8 using the existing Melusina ARP character rig/skeleton and its existing `SK_Melusina_Skeleton`/`SK_Melusina_V2_Body` runtime assets.

**Architecture:** The 15-bone `MEL_DollRig` remains the DollKit asset and UE preview authority. The existing Melusina ARP rig is the motion/reference/retarget source; it is not a replacement for `MEL_DollRig`, and it is not the 15-bone export target. The canonical runtime pawn remains `BP_MelusinaJRPGCharacter`; promotion is additive onto that owner seam, not a second pawn or new gameplay authority.

**Status authority:** `CURRENT_STATE.md`. Existing execution contracts:
- `Docs/Plans/MELUSINA_FULL_EXECUTE_PLAN_2026-09-24.md`
- `Saved/Audit/MELUSINA_EXECUTE_TO_COMPLETION_GOAL_2026-09-24.md`
- `Docs/Plans/MELUSINA_GN_PLAN_2026-09-24.md`
- `Saved/Audit/DOLLKIT_RUNTIME_GAP_MAP_2026-09-24.md`
- `Docs/Architecture/MELUSINA_V2_RUNTIME_CONTRACT.md`

**Important correction:** The user asked for the existing ARP rig and SK. The repo evidence names the live Melusina target as `SK_Melusina_Skeleton` (465 contract bones) and `SK_Melusina_V2_Body`; the ARP source rig is a retarget/export source, not the DollKit's 15-bone map SSOT. Use the existing ARP animation/deform source plus the existing UE Melusina SK as the motion/reference lane. Never silently replace the DollKit skeleton with the 465-bone body skeleton.

---

## Phase 0 — Freeze the lanes and prove the starting state

**Objective:** Prevent authority drift before touching geometry or assets.

**Do this first:**
1. Read `_AGENT_WORKING_AGREEMENT.md`, `CURRENT_STATE.md`, and the five contracts above.
2. Re-run a read-only status check: branch, dirty paths, `git status --short`, and the current UE process/port state.
3. Verify these exact inputs exist before staging:
   - Blender source: `C:/EnvironmentPortfolio/harp_bow_pipeline/Melusina_DollKit_SurfaceDetail_20260924.blend`
   - P9 export: `C:/EnvironmentPortfolio/harp_bow_pipeline/Melusina_DollKit_20260923_P9.glb`
   - UE folder: `/Game/Melodia/Characters/Melusina/DollKit/`
   - existing UE keepers: `IK_MEL_DollRig`, `RTG_Melusina_to_DollRig`, `BP_MelusinaDollKit_Preview`, `MI_Melusina_*` porcelain/brass keepers
   - existing Melusina UE body/skeleton lane: `SK_Melusina_V2_Body`, `SK_Melusina_Skeleton`, `ABP_Melusina_Current`
   - existing ARP/source animation lane: the live ARP export/retarget contract and its current 465-bone target contract; verify the exact ARP FBX path before using it.
4. Treat the known E1 discrepancy as the immediate blocker: named E1 meshes report neck separation 60.18 mm and shoulder-L 142.62 mm; legacy radii 26/24 mm do not equal P9 radii 35/42 mm. Do not rerun E0, P9, or bulk E1 scripts blindly.
5. Mark `E0` historical/complete; leave E1–E8 open until their evidence exists.

**Evidence:**
- `Saved/Audit/melusina_doll_surface_20260924/E1_seating_discrepancy.json`
- `Saved/Audit/melusina_doll_surface_20260924/E1_material_preview.json`
- `Saved/Audit/p9_seating_done.json`
- `Saved/Audit/mel_dollrig_hierarchy_2026-09-24.json`

**Stop if:** the writable SurfaceDetail blend is not the connected Blender file, `MEL_DollRig` is not 15 bones, the P9 export is missing, or the live editor is not uniquely owned. Report the exact blocker; do not improvise a substitute.

---

## Phase 1 — E1: reconcile authority and polish joints

**Objective:** Make the 14 P9 station assemblies the single visual authority before adding detail.

1. Inspect the live evaluated P9 hardware object and `MEL_dollkit_stations` point attributes: `axis`, `ball_r`, `ball_off`, `rim`, `ball_scale`, `ring_proud`.
2. Compare the evaluated P9 procedural keepers with the named E1 meshes and the P9 receipt. Classify every object as authoritative P9 keeper, legacy duplicate, or segment shell.
3. Hide/retire legacy duplicates from the production view without deleting evidence. Never move balls onto old rings by eye.
4. Reconcile all 14 stations: neck, waist, shoulder L/R, hip L/R, elbow L/R, wrist L/R, knee L/R, ankle L/R. Preserve P9 design radii and the ≥4 mm rim clearance.
5. Apply restrained hero surface treatment to the corrected keepers:
   - porcelain ball silhouette and seam readability
   - metal cuff/ring seating and bevels
   - no full armor conversion
   - no clearance regressions at the elbow mechanical limit
6. Render a full assembly plus neck/shoulder/elbow/wrist closeups under separate key/fill/rim lights, with actual materials. Keep the reproducible capture script beside the receipt.
7. Require owner taste approval or explicit waiver after the evidence is reviewable. Do not mark E1 complete on the owner's behalf.

**Acceptance:**
- 14/14 station measurements are recorded from the authoritative evaluated assembly.
- 0 detached ball/ring assemblies, 0 duplicate hardware pieces, 0 unaccounted station keepers.
- P9 radii/clearance gates remain PASS.
- Full-body and closeup renders show exposed ceramic joints, distinct cuffs, and readable material separation.
- Owner approval/waiver is recorded.

**Do not start E2 until this gate closes.**

---

## Phase 2 — E2: clockwork gears

**Objective:** Add only the gear language that improves silhouette and motion.

1. Resolve the installed Higgsas v13 Spur Gear through `higgsas_bridge`; inspect sockets before authoring. No silent native fallback.
2. Rebuild shoulder and hip cog clusters on the corrected P9 keepers using restrained tooth counts and sizes. Micro gears at wrist/ankle are optional only if they remain readable and do not clutter the joint language.
3. Preserve ball exposure and cuff clearance. Keep gears cosmetic until the UE kinematic contract is implemented.
4. Verify the evaluated node graph, parameter changes, frame 0/40 geometry difference, and material separation.
5. Capture full-body and shoulder/hip closeups at two animation samples.

**Acceptance:**
- Higgsas group resolution is recorded; no fallback warning is hidden.
- Gears move in the evaluated Blender scene.
- No gear intersects a ball/cuff/segment or hides the joint silhouette.
- 14 P9 station gates remain PASS.

---

## Phase 3 — E3: segment surface detail and clearance

**Objective:** Give the 15 `MEL_seg_*` shells enough material/edge language to read as authored porcelain without becoming armor.

1. Add restrained panel seams, rim holds, and edge treatment to the 15 segments.
2. Preserve the segment partitions, UVs, articulation clearances, and the existing doll-joint language.
3. Check rest, neutral, and a posed sample around the elbow mechanical limit; measure minimum clearance and record it.
4. Render neutral full-body plus joint closeups under the same key/fill/rim setup.

**Acceptance:**
- 15/15 segments processed and named consistently.
- No new z-fighting, no seam crosses, no clearance violation.
- Full silhouette remains clean; joint balls remain the visual focal points.
- Receipt contains geometry counts, clearance measurements, and render paths.

---

## Phase 4 — E4: bind the corrected keepers to the 15-bone rig

**Objective:** Make every exported keeper follow the existing DollRig map without separation or double transforms.

1. Use the existing 15-bone `MEL_DollRig`; do not replace it with the 465-bone Melusina body skeleton.
2. Map each keeper to the existing station map: waist→spine boundary, neck→neck, shoulders/arms, hips/thighs, elbows/forearms, wrists/hands, knees/legs, ankles/feet.
3. Bone-parent balls, cuffs, rings, gears, and segment shells where needed. Clear `parent=null` debt.
4. Preserve world placement during parenting; use inverse-rest placement rather than corrective runtime transforms.
5. Verify rest and multiple posed samples, including arm swing, elbow flexion, leg flexion, and idle. Record a hierarchy JSON with no unbound exported keeper.

**Acceptance:**
- 15-bone hierarchy unchanged.
- 0 exported keeper with `parent=null`.
- No world-space jump at bind time.
- No separation, double transform, or locked joint at rest/pose.
- Existing `IK_MEL_DollRig` and `RTG_Melusina_to_DollRig` remain valid.

---

## Phase 5 — E5: convert the approved result into reusable GN presets

**Objective:** Make repeatable joint hardware parametric without creating a second authority.

1. Implement/refresh `MEL_doll_ball_joint`, `MEL_doll_cuff_ring`, and `MEL_doll_gear_cluster` through the existing `melodia_gn` chassis.
2. Seed presets from reconciled P9/E1 measurements. Keep `MEL_doll_socket` as the cup helper; do not fork a competing ball API.
3. Add the `Melusina Doll` Stack category when the first builder is registered.
4. Run headless Blender evaluation on a copy/scratch scene. Test meaningful parameter changes for radius, seat offset, ring proudness, gear tooth count, and gear spin.
5. Verify resolved node groups and outputs, then export only after the evaluated result matches the approved hand-polished keepers.

**Acceptance:**
- Builders register and load in Blender 5.2.
- Presets reproduce P9/E1 measurements within the recorded tolerance.
- Headless output is repeatable and non-empty.
- Higgsas groups resolve; no silent fallback.
- One authority remains: P9/E1-approved geometry, not a parallel GN output.

---

## Phase 6 — E6: export and UE visual gate

**Objective:** Bring the corrected DollKit into UE without destroying the existing ARP/SK/Melodia keepers.

1. Export the corrected 15-segment DollKit detail GLB. Verify names, counts, dimensions, materials, hierarchy, and transforms before import.
2. Use the existing owner-gated reimport path: `Saved/Audit/_dollkit_p9_reimport_inner.py`; the agent must not call `save_packages` and must not claim owner Ctrl+S.
3. Preserve `IK_MEL_DollRig`, `RTG_Melusina_to_DollRig`, `BP_MelusinaDollKit_Preview`, and Nikki porcelain/brass MIs.
4. In UE, verify the DollKit preview:
   - balls seated at P9 measurements
   - rings/cuffs visible and attached
   - gears move with animation
   - CuteIdle still plays
   - no duplicate legacy hardware
   - materials remain Nikki porcelain/brass
5. Keep the existing Melusina ARP/SK runtime lane untouched during import: `SK_Melusina_V2_Body`, `SK_Melusina_Skeleton`, and `ABP_Melusina_Current` remain the body/retarget/reference assets. Do not create a second body skeleton or overwrite the V2 contract.

**Acceptance:**
- Owner reimport and save receipt exists.
- UE visual gate has real PIE/viewport evidence, not an import-success flag.
- Existing Melusina body/skeleton/ABP assets are unchanged and reload-safe.
- `BP_MelusinaDollKit_Preview` plays the retargeted CuteIdle with corrected hardware.

---

## Phase 7 — E7: runtime unit on the existing Melusina owner seam

**Objective:** Promote the corrected DollKit from preview to the canonical runtime character without creating a competing gameplay path.

1. Start from `BP_MelusinaJRPGCharacter`; do not build a new game framework or second pawn.
2. Add DollKit presentation through the existing pawn/mesh ownership seam. Keep input, rhythm hit volumes, stats, inventory, combat, and traversal on the existing JRPG owner.
3. Use `MEL_DollRig` for DollKit components and the existing Melusina ARP/SK assets for the body/retarget/reference lane; do not merge the 15-bone rig into the 465-bone body skeleton.
4. Add and verify sockets on the relevant DollRig bones:
   - `socket_weapon_r` on `hand.r`
   - `socket_weapon_l` on `hand.l`
   - `socket_familiar` on `spine_03.x`
   - `socket_vfx_chest` on `spine_03.x`
   - `socket_gear_shoulder_l/r` on `arm.*`
   - `socket_gear_hip_l/r` on `thigh.*`
5. Add segment collision capsules for head/chest/hips/limbs; keep balls kinematic/no-collision and gears cosmetic/no-collision.
6. Verify camera boom and grip-gate proportions against the DollKit, using the existing camera owner.
7. Retarget/test the existing Melusina CuteIdle and locomotion through `RTG_Melusina_to_DollRig`; preserve the existing `SK_Melusina_Skeleton` 465-bone contract for the body lane.
8. Run actual PIE: possession, movement, camera, CuteIdle, locomotion, joint articulation, weapon/familiar/VFX socket placement, and no runtime errors/Accessed None.
9. Capture full-body gameplay frames from the canonical Morning level and joint closeups. Keep evidence next to the harness that produced it.

**Acceptance:**
- Existing `BP_MelusinaJRPGCharacter` remains the runtime owner.
- No second gameplay pawn, HUD, combat authority, save authority, or traversal path.
- All named sockets resolve and track their parent bones.
- Segment collision behaves; cosmetic balls/gears do not block movement.
- PIE proves possession, input, camera, CuteIdle, locomotion, and joint motion.
- No Blueprint Runtime Error, Accessed None, or relevant LogChooser failures in the scoped log window.

---

## Phase 8 — E8: closeout and evidence ledger

**Objective:** Close the task only after every prior gate is independently evidenced.

1. Re-audit E1–E7 against this plan and `CURRENT_STATE.md`.
2. Verify all evidence exists as files and is reproducible:
   - Blender station/seating JSON
   - E1/E2/E3 render stills
   - E4 hierarchy/pose JSON
   - E5 headless GN receipt
   - E6 UE reimport/visual receipt
   - E7 PIE JSON + frames
3. Confirm no legacy P6/E1 duplicates remain in the production export/UE view.
4. Confirm the existing Melusina ARP/SK body, skeleton, ABP, and CuteIdle contract were preserved.
5. Update `CURRENT_STATE.md` with distinct Blender, export, UE, and live PIE evidence. Do not put status in a new handoff/plan file.
6. Mark the E1–E8 execution goal complete only if all gates are green. If any gate is red, keep the goal open and name the exact next gate.

**Final completion definition:**
- E1: authority reconciled + owner taste approval/waiver.
- E2: evaluated gear detail and motion proof.
- E3: segment finish and clearance proof.
- E4: all keepers bound to 15 `MEL_DollRig` bones.
- E5: repeatable GN builders/presets and headless proof.
- E6: owner UE reimport/save + preview visual gate.
- E7: canonical runtime integration and real PIE proof.
- E8: evidence audit and `CURRENT_STATE.md` closeout.

**Do not claim “finished” from any one of these alone:** a GLB exists, a package imported, a preview BP exists, a probe returned success, a source audit passed, or a single beauty still looks good.

---

## Test matrix and commands

Use the repo's existing harnesses first; do not invent a parallel test suite.

**Blender/headless:**
- Run the existing P9 and E1 gate scripts on a copy/scratch scene.
- Run the existing `Tools/higgsas_gate.py` gate for every claimed Higgsas group.
- Evaluate frame 0 and frame 40 for gear motion.
- Export and inspect the GLB hierarchy/material/name manifest before UE.

**UE:**
- Before editor mutation: verify one `UnrealEditor.exe`, one :9316 listener, and no modal-open log condition.
- Use the existing owner-gated reimport script; agent performs no package save.
- Verify by re-reading assets, graph fingerprints, and dirty packages; `success: true` is not proof.
- Run actual PIE, not direct subsystem invocation only.
- Capture JSON assertions beside frames: actor possession, mesh/skeleton/animation paths, socket transforms, collision capsule count, movement/camera state, and scoped error counts.

**Python tooling:**
```bash
python -B -m unittest discover -s Content/Python/Tests -p 'test_*.py'
```

This repository-wide suite previously returned exit 1; capture and classify the failure before using it as a completion gate. Do not call the task green if the relevant tests fail.

**Git safety:**
- Do not use `git checkout -- .`, `git clean`, or broad reset.
- Do not stage the pre-existing `BP_Melusina.uasset` case collision, `.codex/config.toml`, or unrelated untracked assets.
- Do not commit or push unless explicitly asked. The working tree is already heavily dirty/untracked; isolate only task-owned files if a commit is later authorized.

---

## Decisions and risks

1. **ARP vs MEL_DollRig:** Existing ARP/465-bone Melusina assets are the motion/reference/runtime-body lane; `MEL_DollRig` is the 15-bone DollKit authority. The plan keeps those lanes separate and tests compatibility rather than forcing a skeleton merge.
2. **Authority mismatch:** The current E1 renders inspect legacy named meshes, not necessarily the P9 procedural assembly. The first deliverable is a direct evaluated-P9 comparison.
3. **Owner gates:** UE package saving and final taste approval remain owner-controlled in this project. The agent can prepare and verify around them, but cannot substitute for them.
4. **Dirty tree:** The branch has many unrelated modified/untracked files. No broad Git operation is allowed.
5. **Evidence over prose:** Every phase ends in measurable JSON, actual render/PIE frames, or a reproducible receipt. No “done” based on a plan, source diff, or probe-only result.

## Files likely to change during execution

**Blender/source lane (owner-gated or SurfaceDetail-only):**
- `C:/EnvironmentPortfolio/harp_bow_pipeline/Melusina_DollKit_SurfaceDetail_20260924.blend`
- `C:/EnvironmentPortfolio/harp_bow_pipeline/Melusina_DollKit_20260923_P9.glb` (new corrected export; keep prior P9 export as evidence)
- `deploy/surreal_arch/dollkit_pipeline/` (only if the reconciled P9/E1 process needs a bounded script correction)
- `deploy/surreal_arch/melodia_gn/` (new MEL_doll_* builders/presets and registration)

**UE lane:**
- `/Game/Melodia/Characters/Melusina/DollKit/` (owner-gated reimport and explicit package saves)
- `BP_MelusinaDollKit_Preview` (E6/E7 integration)
- `BP_MelusinaJRPGCharacter` (only for the additive runtime presentation/seams; no new authority)
- existing ARP/SK/Melusina body/skeleton/ABP assets (read-only verification; do not overwrite)

**Evidence/status:**
- `Saved/Audit/melusina_doll_surface_20260924/`
- `Saved/Audit/DOLLKIT_P9_UE_REIMPORT_RECEIPT.md`
- `Saved/Audit/melusina_doll_gn/`
- `Saved/Audit/melusina_doll_runtime_20260924/`
- `CURRENT_STATE.md` (same commit as any eventual state-changing work)

---

## Recommended execution order

1. **Now:** owner/live-Blender E1 authority reconciliation.
2. **Then:** E2/E3 detail passes.
3. **Then:** E4/E5 binding and GN repeatability.
4. **Then:** owner UE reimport and E6 visual gate.
5. **Then:** E7 additive runtime promotion on the canonical Melusina pawn.
6. **Finally:** E8 audit and `CURRENT_STATE.md` closeout.

No commit, push, package save, or broad tree cleanup is part of this plan unless separately authorized.
