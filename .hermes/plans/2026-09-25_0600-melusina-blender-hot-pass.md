# PLAN — Melusina Blender "hot pass": the rig/asset work we will be glad we did now (2026-09-25)

**Bounded:** one Blender pass on the canonical blend, one UE reimport pass. Everything that forces a re-export is batched here so UE assets are reimported **once**.
**Canonical blend (owner-confirmed 2026-09-25):** `C:/EnvironmentPortfolio/harp_bow_pipeline/Melusina_Harp_HERO01_ArcherPoseV09_ARP_R08_WIP_20260912.blend` (saved 2026-09-24 17:10). The DollKit is a later unlockable form — **out of scope**.
**Working copy:** all edits in `…_R09_HotPass.blend` next to it; the canonical file is never overwritten until the owner approves.
**Supersedes / converges:** `2026-09-24_131800-melusina-final-rig-today.md` (R1 blink, R2 hair-over-eye, R3 brows, R4 Kawaii perf), `2026-09-24_124500-melusina-hair-lookdev-finalize.md` (face framing, hair ties), the Jev pro-setup ruling (garment conformance → skirt constraints → body collision source → hair on body skeleton), and backlog goal `2026-09-25_0010-p0-backlog-oneshot-goal.md` W1.1/W1.3.
**Evidence:** `Saved/Audit/p0_closeout_2026-09-24/blend_audit_melusina{,2}.json` (read-only headless audits of the saved file).

## What the audit says (why this pass exists)

| # | Finding | Consequence in UE today |
|---|---|---|
| A1 | Everything (body, skirt, garments, lashes, irises, hat, hair strands) is already bound to one rig, `character_rig` (1124 bones, 380 deform; ARP export = 465-bone `SK_Melusina_Skeleton`). | The duplicate skirt skeleton and the separate hair skeleton are **export/import mistakes**, not rig design. |
| A2 | Hair deforms on `DEF_hair_bbone.*` **bendy bones**. ARP docs: bendy-bone chains are **not FBX-exportable** (only Twist mode / soft-link). | UE gets 73 rigid 2-bone strands → no curvature, 219 Kawaii dummy bones, bangs held off the eyes by ModifyBone compensations, flow impossible. |
| A3 | Runtime hair `SK_MelusinaHair` was exported from outside the project (`C:/Program Files/Exports/SK_MelusinaHair.fbx`) on its own `HairExp_Rig`, metre units (hair_root CS scale 100); scene unit scale is 0.1. | Hair colliders can only ride the head; unit mismatch hides offset errors (the 9 cm head sphere). |
| A4 | `Hair Strand.004/.007/.010` carry weights on face bones (`DEF-brow*`, `DEF-cheek*`, `DEF-forehead*`) and chains under `arm_twist.l/r`. | Hair follows brows/cheeks/arms — part of "hair clipping through her body". |
| A5 | UE skirt R2 came from a *Candidates* FBX imported without `SK_Melusina_Skeleton`. | Default skirt refused at every spawn; new game starts skirtless. |
| A6 | `eyeBlinkLeft/Right` are mirror-identical in the saved blend (R1 fix landed 09-24); UE body still has the pre-fix morphs. | Left eye still won't close in UE until the body is re-exported. |
| A7 | `character_rig.002` (759 bones) binds nothing and has no unique bones; `Melusina.001` is a hidden duplicate body bound to `character_rig` twice. | Export ambiguity; dead weight in a 2.4 GB file. |
| A8 | No physics/collision proxies exist on the body or hair. | Kawaii colliders are hand-placed in UE, twice (skirt, hair), and drift from the mesh. |

## Principles (Infinity Nikki bar, applied to a solo pipeline)

- **One skeleton, one unit system, one export contract** — every part leaves Blender the same way, and UE refuses anything else (Jev step 1).
- **Structured garments keep an authored silhouette; only soft parts simulate** (Infold: constraint-based, soft-driven stage prevents clipping; petticoats hold shape).
- **Collision comes from the body, authored once** (single source for skirt, hair, future cloth).
- **Fix causes, not compensations:** the bangs ModifyBones, the head-driven hair colliders and the skirt reassignment all disappear when the export is right.

## Jev audit (2026-09-25, `jev-1.13.0`, jev-live — `Saved/Audit/p0_closeout_2026-09-24/jev_melusina_hot_pass.json`)
- First step **H0_CONTRACT** 1.00 · hair **REAL_CHAINS_GROUPED** 1.00 · collision **BLENDER_PHYSICS_ASSET** 1.00.
- Include in this pass: H4 correctives 0.90, H6 material masks 0.88, H7 rigid bones 0.93, H8 poses 0.89.
- Worst risk **HAIR_RERIG_SCOPE** 0.58 (conf 0.45), then PERMISSION_BLOCK 0.34. Plan quality 2.79/4 (sound, risky scope).
- **Mitigation adopted:** execution order is H0 → H2 → H3 → H5 → H7 → H6 → H1 → H4 → H8 → H9. The hair re-rig (H1) runs after the cheap wins and is **time-boxed**: if the grouped chains are not proven in one sitting, the old hair ships in H9 unchanged and H1 continues alone — it never blocks the reimport of the other parts. Permission rule is requested before H9, not at the end.

## Steps (numbered by topic; execution order above; each ends in a measured gate)

### H0 — Hygiene + export contract (prerequisite for everything)
- Working copy `…_R09_HotPass.blend`. Remove `character_rig.002`; exclude `Melusina.001` from export (delete only with owner OK).
- Write the contract once: FBX via Auto-Rig Pro Game Engine export (Unreal preset, UE-compliant naming `head.x`→`head_x`, scene scale → **centimetres**, `Add leaf bones` off, deform-only, morph targets on, smoothing = face), saved as a named ARP export preset + `Tools/melusina_export_contract.json` (bone count 465 + new hair bones, units, file list, target UE assets).
- A headless validator (`Tools/validate_melusina_export.py`, Blender side) that fails if any exported part is bound to anything but `character_rig`, has non-cm scale, stray vertex groups on non-deform bones, or missing morphs.
- **Gate:** validator passes on the body alone; UE reimport of `SK_Melusina_V2_Body` over the existing asset keeps 465 bones, 120 morphs, all MIs.

### H1 — Hair: real multi-segment chains on the body rig (A2, A3, A4; Jev hair = body skeleton)
- Replace the bendy-bone deformation with **real bone chains** per strand group (ARP spline-IK / custom chains or stylized_hair_pro chain generation): 4–6 bones per strand, fewer strands (group the 73 cards into ~24–30 chains: bangs, side locks, back sheet, ties). Bones parented under `head.x`, so hair exports **with the body skeleton**.
- Re-weight hair to hair chains + `head.x` only (strip every face/arm group). Comb the bangs and right-eye side locks in the **rest pose** so the face is clear without ModifyBones (R2).
- Hair ties (`Cosmos` rings) weighted rigidly to their chain root.
- **Gate:** validator; UE: hair on `SK_Melusina_Skeleton` (leader pose off, Kawaii on the chain roots), ABP ModifyBone bang lifts **deleted**, Kawaii dummy-bone warning gone, both eyes visible front/¾ at rest, hair colliders re-authored on torso bones (H3).

### H2 — Skirt: structured waist + simulated panels (A5; Jev skirt = Kawaii constrained)
- **Progress 2026-09-25:** stray leg weights cleaned (42 verts). UE: `DA_Melusina_SkirtBoneConstraints` (64 ring links: neighbours per side per row + front/back seams) + `BoneConstraintSubdivisionCount` 1 on the skirt Kawaii node — compile 0/0, topology unchanged, saved; idle PIE: 0 surface contacts, hem chain spacing 12–18 cm (effective collision gap ~7.6 cm). **Missing layer found:** `NurbsCurve_profile.001` (metal hip trim, Metal 2 (Matcap), 66–78 cm) is in no UE mesh — added to the skirt export in the contract; `PM3D_Cube3D1.001` (chest glitter gem) added to garments.
- Export `Melusina_Skirt` + `Melusina_SkirtPanel` bound to `character_rig` (fixes the refused default skirt at the source).
- Weight polish of `c_kilt_*` chains: waistband rows rigid to the pelvis (no sim), lower rows free; smooth falloff between chains so ring constraints read as fabric.
- Author the **rest silhouette** (petticoat bell) in Blender so Kawaii settles to the designed shape.
- **Gate:** skirt appears on a new game; Kawaii bone constraints (UE side) + H3 colliders: 0 surface-chain penetration idle and in a run/jump clip.

### H3 — Body collision proxies authored from the mesh (A8; Jev step 3)
- `collider_tools` capsules fitted to the body: pelvis, thighs, shins, spine ×2, chest, neck, head, upper arms — bound to their deform bones, exported as the body's **physics asset** (`SK_Melusina_V2_Body_PhysicsAsset`).
- UE: both Kawaii nodes use `PhysicsAssetForLimits` = that asset; the hand-placed DA capsules from 2026-09-24 are removed (the DA keeps only non-body extras).
- **Gate:** penetration check unchanged or better with DA capsules removed.

### H4 — Deformation polish: weights + corrective shapes (Nikki motion beauty)
- ROM test action (shoulders up/fwd, elbows, hips, knees, spine twist) run in Blender; fix candy-wrapper/collapse by weight smoothing on shoulders, elbows, hips, knees.
- Corrective shape keys only where weights cannot fix it (shoulder-raise, knee-bend, hip-flex), named `corr_<joint>_<pose>`; driven in UE by a **Pose Driver** (RBF) node — Blender drivers do not export.
- **Gate:** ROM sheet before/after; UE Pose Driver drives the correctives in PIE.

### H5 — Face set (A6, R3)
- Re-export body so UE gets the fixed left blink. Verify ARKit-52 completeness with faceit; confirm `eyesCloseL/R`, `eyeBlinkLeft/Right` symmetric.
- Brows: `L_Eyebrow`/`R_Eyebrow` (68 shape keys each) exported with the body instead of the separate `Melusina_Brows_Export_*` fit.
- Irises/lashes: finish the `MEL_IrisPaintKit` (owner paints) and export `SM_Melusina_Irises`/`R_Eyelash` as skinned parts on `head.x` instead of offset static components.
- **Gate:** both eyes close fully in PIE; brows on the brow line front/profile.

### H6 — Material IDs + masks (Nikki four-layer fabric)
- One slot-naming table for every part (`MAT_<part>_<fabric>`), mapped 1:1 to existing Nikki MIs (no new masters).
- Vertex-colour masks per garment (R = fabric layer A/B blend, G = sparkle/iridescence, B = sim weight / stiffness hint, A = AO) and a second UV set for layered fabric tiling — the inputs `M_Master_Nikki` already consumes.
- **Gate:** every slot on every exported part resolves to a named MI on reimport; no `Material_0xx` left.

### H7 — Rigid attachments as bones
- Hat (`Retopo_tophat!.001`), regalia wings + clockwork rings, bow: bound rigidly to named socket bones (`head.x`, `spine_03.x`) in Blender instead of UE-side offset components.
- **Gate:** they ride through run/jump with no slip; UE `EyeIrises`/hat offset hacks removed.

### H8 — Reference poses + QA animations
- Clean bind pose; a small pose library (idle, dress-display, battle-ready, harp) with sakura_poselib for portfolio stills; the ROM action exported for UE QA.

### H9 — Export, reimport once, prove
- Export all parts through the H0 contract → UE reimport **over existing assets** (references and MIs survive) → repoint Kawaii nodes → headless `Melodia.` (expect 101/103) → penetration check → PIE four views + motion clip → Nikki-bar sheet → `CURRENT_STATE.md`.
- **Needs:** `mcp__monolith__editor_query` in `.claude/settings.local.json` (UE asset writes are otherwise blocked).

## Signature phase — "what screams Melusina" (owner-approved 2026-09-25, in order)
Built only on existing systems: `MPC_Cymatics_Driver`, the music clock, rhythm grades, the PhraseBus (:9002), Choral Sheep's Chladni material path, `UMelodiaMagicalTransformComponent`, the resonant-world score/voicing. No new masters, no second authority.

### S1 — Hair that listens
- Music clock → `ABP_Melusina_WaterHair`: Kawaii wind/gravity/damping ride the beat (sway on downbeat, settle in rests); `MI_Melusina_Nikki_Hair` shimmer pulses on `Cymatic_BeatPulse`; droplet burst on accents; a Perfect grade sends one ripple through the hair.
- Wiring starts now on the current hair (the ABP survives H1); final look is judged after the H1 real-chain re-rig.
- **Gate:** PIE clip — hair motion visibly phase-locked to the beat (sampled bone offsets vs beat times), a Perfect-grade ripple on cue, no clipping regression.

### S2 — The dress plays back your performance
- Chladni figures bloom across the skirt from rhythm grades: clean geometry on Perfect, broken on Miss. Reuse the Choral Sheep Chladni path.
- **No master edit needed (verified 2026-09-25):** all 36 `SW_Dress_P*` MIs parent `M_Master_Toon_Universal`, which already exposes `Cymatic_ModeM/ModeN`, `Cymatic_BeatPulse`, `CymaticAmplitude`, `Cymatic_EmissiveScale` and the Audio gains. S2 = MI parameters + grade → mode mapping at runtime.
- **Gate:** grade → pattern in PIE battle; readable at gameplay distance.

### S3 — Transformations on a cadence
- Outfit swaps resolve on the beat via `UMelodiaMagicalTransformComponent` + PhraseBus phrase boundaries (magical-girl sequence on a musical phrase).
- **Gate:** swap lands within one beat of the phrase boundary; wardrobe state and save unaffected.

### S4 — Melusina × Sir Melodious duet
- SDF iris sparkle pulses on the beat (existing `MF_Melusina_SDFIris` beat input); Sir's chirps answer her hums (call/response through the existing score/voicing).
- **Gate:** one call/response exchange in PIE, audio + iris pulse aligned.

### S5 — Silhouette test (permanent gate)
- Black-silhouette capture at gameplay distance (water hair + top hat + bell skirt) added to the Nikki-bar sheet; every outfit must pass.
- **Gate:** silhouette sheet for current outfits; any failing outfit listed.

## Not in this pass
DollKit E1–E8 (later form) · Chaos Cloth conversion (Jev: Kawaii constrained) · FluidNinja/FLIP water layer · new master materials · Groom strands.
