# Melusina E1–E8 execution goal — Infinity Nikki lens

**For Hermes:** Execute the parent plan task-by-task through the existing Melusina DollKit and UE owner seams. Keep the Infinity Nikki lens as the art-direction filter, not a new architecture or second runtime.

**Goal:** Finish E1–E8 for the segmented Melusina DollKit, polish it to an Infinity Nikki-grade close-up, and prove it on the existing Melusina ARP/SK lane in UE 5.8.

**Execution SSOT:** `CURRENT_STATE.md`
**Detailed plan:** `.hermes/plans/2026-09-24_073500-melusina-e1-e8-ue-arp-sk-plan.md`
**Blender workfile:** `C:/EnvironmentPortfolio/harp_bow_pipeline/Melusina_DollKit_SurfaceDetail_20260924.blend`
**P9 export:** `C:/EnvironmentPortfolio/harp_bow_pipeline/Melusina_DollKit_20260923_P9.glb`
**UE DollKit:** `/Game/Melodia/Characters/Melusina/DollKit/`
**Canonical runtime owner:** `BP_MelusinaJRPGCharacter`

## Infinity Nikki lens

Use these criteria at every visual gate:

1. **Silhouette first:** segmented porcelain body, exposed ball joints, readable cuff edges, and restrained clockwork clusters.
2. **Hero close-up:** warm bisque ceramic with subtle SSS, anisotropic warm brass, controlled pearlescence, and no black gear blobs.
3. **Material hierarchy:** porcelain, brass, and steel must read differently under independent key/fill/rim lighting.
4. **Fashion-luxury restraint:** no full armor conversion, no noisy surface detail, no decorative clutter that hides articulation.
5. **Motion beauty:** every moving piece must remain attached and readable while Melusina moves, idles, and turns.
6. **References are study-only:** Ashlotte and Orianna guide joint/cog language only; never ship their meshes or textures.

## Ordered goal

### E1 — authority, then Infinity Nikki joint polish

- Reconcile the detached legacy E1 meshes against the live evaluated P9 procedural station assembly.
- Use P9 design radii and the 4 mm minimum rim clearance as numerical truth.
- Do not move balls onto legacy rings by eye; do not rerun E0/P9 bulk scripts blindly.
- Render corrected neck/shoulder/elbow/wrist evidence and a full assembly under real materials.
- Hold for owner taste approval or explicit waiver.

**Gate:** 14/14 stations accounted for; 0 detached keepers; P9 gates remain green; owner approval/waiver recorded.

### E2 — clockwork gear polish

- Build shoulder/hip gear clusters through the installed Higgsas Spur Gear lane.
- Preserve the Infinity Nikki balance: cog silhouette readable, not oversized black stars.
- Prove evaluated motion with frame 0/40 geometry and actual material renders.
- No silent native fallback.

### E3 — segment surface finish

- Add restrained seams, rim holds, and edge treatment to the 15 `MEL_seg_*` shells.
- Keep the body porcelain and articulated, not armored.
- Measure rest/neutral/posed clearances, including the elbow mechanical limit.

### E4 — 15-bone binding

- Bind balls, cuffs, rings, gears, and segments to `MEL_DollRig` using the existing Orianna station map.
- Preserve world placement with inverse-rest transforms.
- Require zero `parent=null` exported keepers, no separation, and no double transforms.

### E5 — reusable GN authority

- Convert the approved P9/E1 result into `MEL_doll_ball_joint`, `MEL_doll_cuff_ring`, and `MEL_doll_gear_cluster` presets on the existing `melodia_gn` chassis.
- Reuse `MEL_doll_socket`; do not create a competing joint authority.
- Prove resolved groups, measured output, repeatable presets, and parameter changes headlessly.
- Ensure default dials are neutral and do not bloat the mesh.

### E6 — export and UE visual gate

- Export corrected original Melusina geometry only.
- Verify names/counts/materials/transforms before import.
- Use the owner-gated UE reimport path; no agent package save.
- Preserve `IK_MEL_DollRig`, `RTG_Melusina_to_DollRig`, `BP_MelusinaDollKit_Preview`, and Nikki MIs.
- Verify seated joints, gear motion, CuteIdle, materials, and reload safety in UE.

### E7 — runtime on the existing Melusina owner seam

- Keep `BP_MelusinaJRPGCharacter` as the sole runtime owner; no second pawn or new gameplay framework.
- Use the existing Melusina ARP/SK body/retarget lane (`SK_Melusina_V2_Body`, `SK_Melusina_Skeleton`, `ABP_Melusina_Current`) for the existing body presentation and motion reference.
- Keep `MEL_DollRig` as the DollKit's 15-bone component authority; do not merge the 465-bone body skeleton with the 15-bone rig.
- Add sockets for weapons, familiar, chest VFX, shoulder gears, and hip gears on their named DollRig bones.
- Add segment collision capsules; keep balls/gears kinematic/cosmetic.
- Prove actual PIE: possession, movement, camera, CuteIdle, joint motion, socket tracking, and no scoped runtime errors.

### E8 — closeout

- Audit E1–E7 against this goal and `CURRENT_STATE.md`.
- Require Blender measurements, real materials, geometry motion, UE visual evidence, and live PIE assertions.
- Update `CURRENT_STATE.md`; do not create another status/handoff document.
- Mark the goal complete only when every gate is green.

## Hard boundaries

- `MEL_DollRig` remains 15 bones.
- Existing ARP/SK assets remain the Melusina body/motion lane; never replace or merge them silently.
- No new gameplay framework, second pawn, second combat path, or second UI/audio authority.
- No agent UE package saves; owner Ctrl+S remains the save gate.
- No destructive Git commands or broad staging of the dirty tree.
- `CURRENT_STATE.md` is the only status authority.
- Do not call E1 complete without owner taste approval or waiver.

## Required evidence

- `Saved/Audit/melusina_doll_surface_20260924/` — E1–E4 geometry/material/pose receipts.
- `Saved/Audit/melusina_doll_gn/` — E5 headless GN receipts.
- `Saved/Audit/DOLLKIT_P9_UE_REIMPORT_RECEIPT.md` — E6 owner reimport receipt.
- `Saved/Audit/melusina_doll_runtime_20260924/` — E7 PIE JSON and frames.
- `CURRENT_STATE.md` — E8 authoritative closeout.

## Current starting point

- E0 historical/complete.
- P9 Blender seating/gates: PASS (`p9_seating_done.json`).
- E1 currently HOLD: legacy named keeper renders are detached from the authoritative P9 values.
- E2–E8: OPEN.
- UE editor is live on PID 49388 with Monolith :9316; Blender MCP :9876 is currently not responsive.
- Do not start E2 while E1 is held.
