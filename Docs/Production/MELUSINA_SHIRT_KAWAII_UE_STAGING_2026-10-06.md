# Melusina Shirt — UE Staging Runbook (Kawaii) — 2026-10-06

**Verdict: READY FOR STAGING with the checklist below.** Houdini proved the fix
headless; nothing below edits a live asset until its gate passes. Canon:
`Docs/Production/MELUSINA_RUNTIME_CANON_2026-10-05.md` (still binding — no body
reimport, no new solver, Sparrow×6 frozen).

## 1. What was proven today (staging, headless Houdini 22)

| Claim | Evidence |
|---|---|
| Leg-chain weights removed | `shirt_fix/shirt_weight_fix_v1.json` — 234 verts thigh_twist→torso, re-read from disk: **0 leg-bound, max 4 influences, 0 renorm violations** |
| Clearance, no touching | `shirt_fix_manifest.json` — min **0.52 cm**, 0 within 0.5 cm (source was 0.002 cm / 57) |
| Winding defect recorded | 1163/1195 torso prims inward, staged as `g_inward` (UE must recalc-outside or double-side) |
| Hem rig staged | 8-spoke `c_shirt_hem_master_x`, 17 bones, Kawaii profile (damp 0.62 / stiff 0.72 / drag 0.24 / grav 0.16 / wind 0.12 / radius 3 cm) |
| Visual proof | `turntable/shirt_fix_contact.png` + `shirt_fix_00..07.png` (8 angles, all clean) |
| Health gate | doctor `doctor_report_20261006_shirt.json` — **22/23 PASS, 0 FAIL** |

## 2. UE application path (tonight)

1. **Apply weight deltas** on the Blender/UE reimport path (`shirt_weight_fix_v1.json`:
   per-vert `[[bone, weight]]`, top-4, sums 1.0). Reference geometry:
   `shirt_skinfix_v1.bgeo` (cm frame, y-up — matches `current_body_readonly.fbx`).
2. **Units + winding on import:** source is meters — import at cm; recalc normals
   outside (or double-sided material) per the `g_inward` finding.
3. **Skeleton gate (OWNER):** candidate carries a 481-bone staging skeleton (464 +
   17 hem). Runtime needs same-USkeleton + LeaderPose — integrate the 17 hem
   bones; do **not** ship the staging skeleton.
4. **Kawaii authoring (editor):** Kawaii node on `c_shirt_hem_master_x` with the
   staged profile; collision from shared body source tag
   `Melodia.Melusina.BodyCloth` (existing sharing authority, body + WaterHair
   pattern); limits via `PhysicsAssetForLimits`.
5. **Verify (PIE, normal cadence):** walk/stop + arm raise + hold pose; garment
   separation, no body penetration, hem settle with lag, face clear. Re-run
   `Content/Python/melusina_animation_doctor.py` after; any FAIL keeps the
   previous `.uasset` (rollback backups already on file).
6. **At most ONE bounded change** before re-proving. Sparrow clips, body mesh,
   skeleton stay frozen.

## 3. Standing BLOCKED / OWNER items (not tonight unless directed)

- `skeleton_fbx_export` (jointed UE skeleton → unblocks Houdini capture weights)
- Same-USkeleton hem integration (§2.3)
- Sparrow×6 arm-defect decision, BowGrip look (canon §4)

## 4. File inventory (repo-relative)

- `Saved/Audit/melusina_animation_doctor/shirt_fix/` — bgeo, deltas, manifests
- `Saved/Audit/melusina_animation_doctor/turntable/` — 8 frames + contact sheet
- `Saved/Audit/melusina_animation_doctor/doctor_report_20261006_shirt.json`
- `Saved/Audit/melusina_animation_doctor/rig/rig_manifest_{melusina,sheep}.json`
- `Content/Python/melusina_animation_doctor.py` (v2 + shirt_rig check)
- `Tools/Houdini/universal_rig/` + `specs/universal_rig/rig_contract.v1.json`
- `Tools/Houdini/build_melusina_weight_lab.py` (H22 port), both staged hips
- D snapshot for tonight: `D:\melodia_bundles\melusina-shirt-20261006\` (mirrored
  paths + `MANIFEST.txt`); git commit pending a working git binary on this
  machine (both MinGit exes fail `STATUS_DLL_NOT_FOUND`, no other copy on disk).
