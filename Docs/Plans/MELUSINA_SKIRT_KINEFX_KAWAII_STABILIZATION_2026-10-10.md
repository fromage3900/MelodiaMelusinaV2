# Melusina skirt — KineFX / KawaiiPhysics stabilization
**Date:** 2026-10-10  
**Status:** PLANNED / no runtime fix claimed  
**Agent canary:** StepFun 5 (bounded evaluator, not an authorized asset writer)  
**Engine:** UE 5.8 · **Houdini:** repo-backed Melodia Studio/KineFX  
**Primary goal:** Stop multilayer-skirt penetration, chain jitter/popping, and constraint conflict without disrupting Melusina's canonical rig or creating a second runtime cloth authority.

## 0. Authorities and starting point

This plan *extends* the existing production lanes; it does not supersede:
- `Docs/Production/MELUSINA_RUNTIME_CANON_2026-10-05.md` — canonical skeleton, current `ABP_Melusina_Current` graph, frozen clips, valid retarget rules.
- `Docs/Art/UNIVERSAL_GARMENT_SYSTEM_MASTER_SPEC_2026-09-02.md` — garment tiers and unified authoring authority.
- `START_HERE_HOUDINI_2026-10-07.md` and `deploy/houdini/README.md` — verified Houdini Studio package, `Melodia_Studio` and `Melodia_KineFX` desktops, shelf and evidence helpers.
- `Docs/Houdini/MELODIA_ANIMATION_OUTFIT_FINISHING_CONVERGENCE_2026-10-07.md` — existing AnimationDoctor -> KineFX -> controlled Vellum/VAT -> UE authoring pipeline.
- `Content/Python/melusina_animation_doctor.py` — existing read-only AnimationDoctor v2 report/gate; extend its cloth-hair lane rather than authoring a separate Doctor.
- `Docs/MELUSINA_WARDROBE_PHYSICS_PIPELINE_2026-09-15.md` — KawaiiPhysics v1.21.0, Sync Bones and shared-collision capabilities/limits.

**Historical evidence (not a statement of today's live editor state):**
- `Saved/Audit/MelusinaRuntimeConvergence_20261002/kawaii_postbuild_config.json`: skirt Kawaii root `c_kilt_master_x`; `DA_Melusina_SkirtCollisionLimits` bound; `PhysicsAssetForLimits=None`; one root sphere, pelvis/root, paired thigh and shin capsules. Recorded baseline: damping 0.30, stiffness 0.18, world location damping 0.80, rotation damping 0.85, angle 38 degrees, radius 2.5, subdivision 1.
- `.hermes/plans/2026-09-25_0600-melusina-blender-hot-pass.md`: 64 skirt ring constraints were staged in `DA_Melusina_SkirtBoneConstraints`; **verify asset binding and constraint contents today before crediting this as live**.
- `Saved/Audit/MelusinaSecondarySources_20261003/shared_collision_editor_readback.json`: `shared_collision_source=False`, `use_shared_collision=False` on the inspected nodes, with `PhysicsAssetForLimits=None`. Sharing copies computed limits across appropriately configured nodes; **it does not create skirt-layer self-collision**.
- `Saved/Audit/MelusinaSecondarySources_20261003/source_exports.json`: the exported R2 skirt reported `SK_Melusina_Skeleton`; older September documents report a separate companion skeleton. **Read the currently equipped runtime mesh/skeleton and follow graph, not the older claim.**
- `Docs/Production/MELUSINA_RUNTIME_CANON_2026-10-05.md`: current order includes `FootPlacement_1 -> KawaiiPhysics_0(c_kilt_master_x) -> CopyBone_0`. Do not move the solver across FootPlacement or rewrite the upper-body layer mask during diagnosis.

**Boundaries:** `SK_Melusina_V2_Body`, `SK_Melusina_V2_Skirt_R2_SmoothChains`, `ABP_Melusina_Current`, the current player wardrobe slot, and any attached trim/underskirt meshes must be identified **at runtime**. Do not presume a standalone portfolio R2 skirt actor is the equipped gameplay garment. The separate water-hair ABP is not in scope unless shared body colliders are proven to affect this case.

## 1. G0 — Freeze + read-only source/scene preflight (StepFun 5)

Before any change, capture `git status --short`, local HEAD, `origin/main`, Perforce checkout/locks if applicable, editor owner/lease and dirty assets. **Do not clean/overwrite local SSD, stashes, Perforce work, or other agents' changes.** Do not launch a second UE editor or issue Monolith editor writes while another editor owner is active.

Read the exact active `BP_MelusinaJRPGCharacter` or game-mode-selected pawn (not orphan `BP_Melusina`) and report:
1. Actual body/skirt/underskirt/trim components, skeletal meshes, skeleton paths, animation classes, attachment and LeaderPose/CopyPose use.
2. All active Kawaii nodes (including any modular garment nodes): Alpha, root/additional roots, evaluation order, affected bones, component/world space, wind and external forces, collision limits asset, PhysicsAssetForLimits, constraints data asset, iterations, subdivisions, sync bones, shared-collision flags/group tags.
3. Current sphere/capsule geometry in driving-bone component space, enabled/inner/outer modes, and mesh/rest clearance; report collider transforms with the real component/bone matrix. A data asset existing on disk does **not** mean it is connected.
4. Whether the *inner and outer physical layers* have separate bones and sim ownership or are simply separate mesh sections weighted to one `c_kilt_*` ring. Identify potential double-simulation, conflicting cross-ring links, and accidental L/R chain crossing.
5. Screenshot/video of the exact current defect, front/side/three-quarter with colliders + simulated bone debug visible.

Existing read-only assist: `Content/Python/audit_kawaii_runtime_readonly.py` plus direct inspected editor-node reflected values; note that script is primarily a hair/placement probe, **not** a complete skirt inspector. First extend a read-only reporting pass or inspect manually. Do not use a write action as an improvised getter.

**G0 PASS:** identity + authoritative bindings + baselines + clean ownership recorded. **HOLD:** wrong pawn, mismatched skeleton or source, missing assets, another writer, no repeatable runtime defect.

## 2. G1 — Controlled A/B isolation in UE

Use an isolated copy of the animation Blueprint/PIE test context or a reversible, owner-approved runtime override. Keep *the same approved clip*, starting pose, capture cadence and camera. Test in order (each test restored before next):
- **A — authored pose only:** Kawaii Alpha 0; inspect weight/rest/skeleton deformation before blaming collision.
- **B — Kawaii no collision:** Alpha 1, collision limits temporarily disabled in the **test copy**; shows chain motion/constraint behavior without body collision.
- **C — minimal body cage:** re-enable pelvis/root only, then thighs, then shins; compare penetration, pop and panel clearance separately.
- **D — constraint contrast:** same cage, ring constraints OFF then ON; inspect end-point pairs, rest lengths, topology, constraint subdivision and resulting cross-panel tugging.
- **E — full saved baseline:** restore all original data; record whether an extra solver, accessory chain, wind/force or frame-step behavior produces the regression.

Do not assume `PhysicsAssetForLimits=None` is the defect if the existing `LimitsDataAsset` already provides the intended body cage. Do not enable shared collision as a speculative cloth–cloth fix. Kawaii colliders primarily constrain bone points/proxies, not a general triangle-mesh cloth collision system.

**G1 PASS:** repeatable failure assigned to (i) weights/rest rig, (ii) collision shape/type/drive, (iii) constraint ring/spacing, (iv) multi-owner/simulation order, or (v) timestep/warm-up/reset. Record exact visual comparison and one hypothesis; no bulk parameter sweep.

## 3. G2 — Existing KineFX / AnimationDoctor offline garment lab

Reuse the **repo-backed** `Melodia_KineFX` desktop, the installed Melodia shelf's AnimationDoctor/Evidence/UE Handoff entrypoints, and the already-tracked `Content/Python/melusina_animation_doctor.py`. Verify `deploy/houdini/verify_melodia_studio.py` first if the workstation changed. Seek the owner-synced actual HIP/HDA where appropriate; **do not invent or rebuild another canonical AnimationDoctor HDA** from prose.

In a *disposable* work file with read-only copies of the current runtime-exported FBX/mesh + skeleton and one owner-approved motion clip:
1. Intake KineFX `rigpose/rest`, joint hierarchy, skin capture and animation. Verify UE-centimeter scale, axis/orientation, joint order, `root_x` subtree, `c_kilt_master_x` and skirt chain names; reject duplicate rigs or a different R2 garment generation.
2. For every skirt layer/island, measure reference silhouette, min signed or closest surface distance to body and other garment layers at idle, walk, turn, stop, jump, and bow/draw if relevant. Distinguish actual triangle penetrations from Kawaii bone-proxy noncontact; report per pose and location.
3. Visualize semantic constraints on pelvis/hips, thigh/shin capsule drives, rigid waistband, radial `c_kilt_*` ring adjacency, seam links, panel rest lengths and tip freedom. Catch crossing L/R links, bad scaling, disconnected chains and conflicting inner/outer layer ownership.
4. Diagnose upper rigid-band weighting vs free lower panels; note any weights pulling skirt onto thigh joints or missing clearance. Export **reports, overlays, proposed values and optional non-destructive constraint/proxy candidates**, not modified canonical FBX.
5. If there is a reproducible geometry problem (not a solver tuning defect), produce a minimally changed corrective *candidate* on a copy with input hashes and per-vertex/bone diff. No UE reimport without a separate approval gate.
6. Optional **reference-only**: run the already-planned *single hero outer skirt* Houdini Vellum canary with waistband pins, simple animated body collider and at most three deterministic presets. Use only to judge drape/rest silhouette or bake a cinematic option; never silently replace runtime Kawaii/Chaos or solve all layers at once.

Outputs: `Saved/Audit/melusina_skirt_kinefx_20261010/` compact JSON manifests/metrics/playblasts with source paths, hashes, solver parameters, clip/frame ranges, failed checks and proposed UE settings; keep heavy HIP/cache/FBX outside Git until explicitly selected. Follow `git check-ignore -v` rules before claiming a deliverable is committed.

**G2 PASS:** the same input clip produces reproducible topological/clearance diagnosis, reproducible metrics, and one smallest viable correction candidate. **HOLD:** no canonical source match or no approved working KineFX input.

## 4. G3 — One minimal UE change per verified root cause (single editor writer)

**The default change is NOTHING until G0–G2 identify the cause.** StepFun may prepare a precise change sheet; the owner grants the sole editor writer permission before modifying the real asset.

Decision ladder, cheapest first:
1. **Rig/rest/weight issue:** correct in a copy and review before a controlled source re-export; do not mask severe skinning deformation with damping.
2. **Body penetration:** fit existing `DA_Melusina_SkirtCollisionLimits` pelvis/thigh/shin proxies to the actual runtime skeleton and frame; test one collider edit at a time. Consider a narrowly attenuated `Sync Bone` for thigh motion only if a measured leg-contact deficiency remains; verify directions, falloff and stability.
3. **Ring shear/twisting:** confirm `DA_Melusina_SkirtBoneConstraints` asset is genuinely bound, links connect intended adjacent rows/sides, and rest lengths are sane; adjust only offending connections/iterations. Avoid using constraints to force *different physical fabric layers* into the same distance surface.
4. **Jitter/teleport instability:** assess fixed substepping, target frame rate, teleport threshold, warm-up, world/component space and external force inputs before changing damping/stiffness; record test FPS.
5. **Layer-to-layer fabric collision truly required:** declare a Kawaii limitation and choose an *explicit separately approved* option (art-directed inner petticoat clearance, authored correctives, or isolated Chaos Cloth research for one hero panel). Do not integrate a second solver or delete the existing Kawaii system inside this task.

Record before/after exact settings and asset paths; compile/save only owner-approved changed assets, revert promptly if comparison worsens. **Keep `SK_Melusina_Skeleton`, six frozen SparrowArchery clips, `ABP_Melusina_Current` layering/FootPlacement order, wardrobe/save owners and material masters untouched unless a separately approved dependency forces a change.** Do not run a speculative 10+ setting sweep.

## 5. G4 — Real gameplay and recovery acceptance

Test the **actual equipped game pawn** using the original input path, not only the isolated portfolio presenter:
- Baseline/changed paired captures: idle, walk, sprint/stop, sharp 90/180 turn, jump/landing, weapon draw/recovery if possible.
- Front/side/three-quarter + collider debug + normal beauty silhouette. Verify the underside/inner layer is not visibly exposed and the outer hem maintains its designed bell/soft-flow silhouette.
- Test 30 vs 60 FPS or deliberately bounded substep variation, teleport/reset, respawn, wardrobe unequip/re-equip, level restart, and load-from-save if the outfit appears in that state path.
- Verify Kawaii nodes evaluate at the intended LOD and no collision/constraint warnings, Blueprint runtime errors or topology/skeleton regressions are introduced.
- Compare contact metrics and captures. **PASS only on actual repeated PIE motion plus owner visual approval**; a successful headless Hython cook, ABP compile or static PNG alone is *not* a runtime physics proof.
- Packaged-build evidence is a separate later gate: label it `NOT_TESTED` unless a packaged test was really run.

Acceptance matrix, publish an explicit result per item:

| Gate | Required artifact | Verdict |
|---|---|---|
| G0 | Runtime binding/skeleton/collision snapshot; editor ownership | PENDING |
| G1 | A/B isolate + defect classification with captures | PENDING |
| G2 | Reproducible KineFX/Doctor metrics + candidate | PENDING |
| G3 | One approved patch, reversible diff, compile/save + tests | PENDING |
| G4 | Full PIE matrix, before/after video, reset evidence, owner eye | PENDING |
| G5 | Packaged build (only if performed) | NOT_TESTED |

## 6. StepFun 5 evaluation contract

**Assignment:** `Melusina skirt KineFX/Kawaii recovery`; **scope:** G0-G2 first. **Budget:** one read-only preflight, one controlled A/B test session, one Hython KineFX analysis; stop and report instead of iterating blindly.

**Report format (one concise handoff):**
```text
HEAD / WORKTREE / EDITOR LEASE:
ACTIVE PAWN + BODY/SKIRT + SKELETON + FOLLOWER PATH:
ACTIVE KAWAII NODE(s), COLLISION DA, BONE CONSTRAINT DA:
REPRO CLIP + FRAMES + FPS:
A/B FINDINGS / ROOT CAUSE (observed vs inferred):
KINEFX METRICS + SOURCE HASHES:
SINGLE LOWEST-RISK PATCH PROPOSAL:
ASSETS THAT WOULD CHANGE (NOT YET CHANGED):
ROLLBACK + OWNER PERMISSION REQUIRED:
PROOF LINKS / MISSING PROOF:
NEXT GATE: G0 | G1 | G2 | G3 | HOLD
```

**Scoring:** 40% correctly identifies the real failure; 25% accurate reuse of canonical UE/KineFX pipeline; 20% executable/reversible proposed fix; 15% evidence discipline. Subtract points for unapproved mutations, claiming an offline cache proves PIE, stale skeleton assumptions, adding duplicate cloth infrastructure, or spending time rebuilding pre-existing tools.

**STOP conditions:** write lease conflict; canonical skeleton mismatch; uncertain garment generation; wrong active pawn; clip/source missing; a proposed UE write without explicit owner approval; any unreviewed reimport; changes outside skirt/garment scope.

## 7. Immediate start command (for StepFun 5)

> Read this plan and the current Melusina runtime canon first. Inspect `START_HERE_HOUDINI_2026-10-07.md` **checkpoint update** rather than repeating the superseded setup steps. Run G0 **read-only** on the actual live player with the existing Houdini package, Kawaii node and collision DAs. Return the concise report. Do not modify editor assets, create a second HDA, relaunch another editor, or silently convert the skirt to Chaos. Proceed to one reproducible A/B diagnosis only if the editor owner grants a test window. If any part is unproven, mark HOLD.

**Relationship to Shorewake:** this is a **Melusina gameplay R2 skirt physics** recovery. The already-staged **Shorewake hero outer-skirt Vellum** lane is a reference/optional finishing follow-up, *not* an interchangeable source or an excuse to swap garment identities.
