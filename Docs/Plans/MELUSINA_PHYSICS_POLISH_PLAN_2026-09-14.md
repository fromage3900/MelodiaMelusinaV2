# Melusina Physics Polish Plan — 2026-09-14 (evening)

Evidence in hand, no prose-as-proof. Owner eye is the beauty gate throughout.

## 1. Proven tonight (ledger, not lore)
- PIE `melusina_physics_0914b`, MelodiaIntegrationMap, 12 s: OK, 0 Blueprint errors, 0 Accessed None.
  Report: `Saved/PIE/melusina_physics_0914b/melusina_physics_0914b_report.json`
- 11 frames, distinct md5, lit (mean 132 → 180 across run; frame_000 black = loading, judge from 001+).
- BUT: bIsMoving=false on all 35 samples. Idle-only. Collisions unstressed.
- Body ABP (`ABP_Melusina_Current`): 11 nodes, orphan `BlendSpacePlayer_0` with no pose output (verified tonight via validate_bindings). Its "correct speed binding" is carried from the 08-20 review, NOT re-verified tonight.
- Hair ABP (`ABP_Melusina_WaterHair`): 6 nodes, `SequencePlayer_0` no pose output — same family, unconfirmed.
- Pawn check CORRECTION (tonight): the `MelodiaSmokeCharacter` parent cited earlier came from `BP_Melusina`, which the 08-20 correction doc identifies as the ORPHANED pawn — wrong target. Live pawn is `BP_MelusinaJRPGCharacter` (parent `BP_JRPGCharacterBase_C`, also `inherited`, re-checked tonight). Resolved anim class on the live pawn is still unverified — skeleton-match stays open against the right pawn.
- Vision service down (3 fails). No agent beauty claims. Owner to open `Saved/PIE/melusina_physics_0914b/frame_005.png` + `frame_010.png`.
- LIVE-VERIFIED TONIGHT via Monolith `run_python` CDO read (supersedes all Aug tuning prose):
  Skirt (`ABP_Melusina_Current`, node _0, root `c_kilt_master_x`, skel `SK_Melusina_Skeleton`): damping 0.30 / stiffness 0.18 / worldLoc 0.80 / worldRot 0.75 / radius 2.5 / limit 45° / dummy 0.0 / subdiv 1 +densify / constraint-subdiv 3 / ComponentSpace / gravity −120 / teleport 300°/10°.
  Limits BOUND: `DA_Melusina_SkirtCollisionLimits` = 2 capsules (`thigh_stretch_l/r`, r=9, len 32) + 1 sphere (`c_kilt_master_x`, r=11). The thigh-capsule recipe is present — verify offsets live, don't re-add blindly.
  Hair (`ABP_Melusina_WaterHair`, node _1, root `HairExp_Rig` — NOT `hair_root`; architecture changed since Aug docs, skel `SK_Melusina_Hair_Skeleton`): damping 0.30 / stiffness 0.07 / worldLoc 0.65 / worldRot 0.30 / radius 2.0 / limit 75° / dummy 3.0 / subdiv 3 / constraint-subdiv 0 / ComponentSpace / gravity −120.
  Limits BOUND: `DA_Melusina_HairCollisionLimits` = 1 sphere (`hair_root`, r=8.5). THIN — single-sphere coverage per the skill pitfall, and it drives `hair_root` while the sim roots at `HairExp_Rig`: confirm the drive bone is inside the sim chain or the sphere protects nothing.
  Prime instability suspects: hair worldRot 0.30 (70% of head rotation pours into the sim) + limit 75° + soft 0.07 stiffness = whip; both nodes ComponentSpace under a bobbing run cycle; skirt dummy 0 (no hem tip).

## 2. Work queue (in order, one writer, one change at a time)
1. OWNER EYE — DONE 2026-09-14 (~22:30 UTC): kilt CLIPS thighs / hair GLUED / pose clean. No T-pose.
   Follow-up reads same night: hair pipeline is LIVE (log shows MELUSINA_HAIR_SOCKET + MELUSINA_HAIR_BOUND firing, anim=ABP_Melusina_WaterHair_C on head_x; skeleton 148 bones, sim root HairExp_Rig = bone 0, drive hair_root = bone 1, chains A/B/C intact). "Glued" is therefore expected at idle — she stood still all run (bIsMoving=false), sim had no input. Hair judgment moves to the moving run. Kilt clip at idle is the TRUE defect: capsules are zero-offset r9/len32 on thigh_stretch — coverage vs the V2 kilt rest pose is now the viewport question.
2. MOVING RUN — BLOCKED 2026-09-14 (~23:00 UTC), full findings: `WalkLoop` is a GHOST (named in harness, implemented nowhere; no locomotion IA exists in Content — only legacy W/S/A/D axes in DefaultInput.ini). Live-drive attempt: viewport PIE on L_MelusinaMorning, possessed pawn confirmed BP_MelusinaJRPGCharacter (MOVE_Walking, MaxWalkSpeed 380). AddMovementInput RPC works but too sparse (~3Hz vs 2048 braking). LaunchCharacter works vertically (jump+fall verified) but reads ZERO in all 4 horizontal dirs even at 1500 within 0.3s — spawn at (1305,1861,-520) is PENNED on all sides. Anim instance live-confirmed ABP_Melusina_Current_C (Speed 0, bIsMoving false throughout — locomotion defect A still open, so even delivered input may not leave Idle). Banked frames: Saved/PIE/melusina_sprint_0914/ (44 frames, all idle). CHEAPEST UNBLOCK: owner viewport Simulate — walk her with W for 10s and eyeball kilt+hair (1 min, beats 25 agent turns). Agent lane needs one of: real WalkLoop exec, teleport-to-open-ground, or braking=0 transient.
3. LIMITS AUDIT (not bind — both DAs already bound, verified tonight): skirt capsules sit on the right bones — verify offsets/radii against the sim skeleton in viewport; hair needs 2–3 more spheres down the chain (head/neck-adjacent per skill; `hair_root`-in-`HairExp_Rig` confirmed tonight). Re-tune pass after.

## 7. HAIR DEATH INQUEST — 2026-09-14 (~23:30 UTC, owner: static even in freefall)
EXONERATED (all live-verified): AnimGraph fully wired CopyPose→Local→Kawaii→Comp→Root with source var bound (native export_graph read); node Alpha 1.0, connected both sides; compiles UpToDate 0/0; runtime logs MELUSINA_HAIR_SOCKET+BOUND fire with anim=WaterHair_C; mesh↔ABP skeletons match; flip-cache component hidden; mesh visible; tick mode AlwaysTickPoseAndRefreshBones; limit sane (OUTER r8.5); EventGraph innocent (VFX vars only).
HISTORY: July checklist — separate-armature export, shared_bones=0; C++ inverse-bind socket is the standing workaround. SK_Melusina_FIXED_Hair found beside the live mesh: rigid fallback on the BODY skeleton (465 bones, no hair chains) — not a sim path, do not promote it as one.
REMAINING SUSPECTS (ranked): (1) skin weights — mesh verts may grip only rigid bones, sim dances unseen (weights unreadable via Python/MCP; needs editor Skeleton-Tree weight view or DCC); (2) node never evaluates at runtime (ModifyBones empty — stat path inconclusive); (3) global CVar kill (default true, not in Config).
DECISIVE TEST (owner running): PIE console `a.AnimNode.KawaiiPhysics.Debug 1` — bones writhe but mesh frozen = weights; no bones = eval dead. Stage is clear (agent PIE stopped) for the rite.
4. HEM TIP: `dummy_bone_length` 0 → ~3–5. Art call, changes silhouette. Owner decides.
5. ORPHAN BLENDSPACE: wire or remove `BlendSpacePlayer_0`; confirm `SequencePlayer_0` in hair. Locomotion can't be trusted at run speed until this lands.
6. SKELETON CONFIRM: resolve inherited-anim-class warning (mesh vs ABP skeleton equality) before any mesh swap.
7. V2 PROMOTION (parked): V2Test assets on disk (verified tonight by listing); "live pawn on Current" is carried from the 08-20 review of the production pawn, NOT re-verified on the JRPG pawn tonight. Do not promote until 1–6 green.

## 5. Hallucination audit (tonight, self-review)
- FIXED: wrong-pawn check (`BP_Melusina` orphan). Re-checked the live `BP_MelusinaJRPGCharacter`. Lesson: always resolve the pawn from `BP_MelodiaJRPGGameMode` default pawn first.
- CARRIED (flagged inline, not fresh): Kawaii tuning values + limits-unbound + ModifyBone removal (Aug docs); speed-pin binding (08-20); Current-is-live (08-20).
- Web research FAILED tonight (search billing 402) — author-parameter facts below come from the vendored plugin source (`Plugins/KawaiiPhysics`, v1.21.0 headers), not a live github read. Do not cite upstream README claims.

## 6. Infinity Nikki polish bar (what "done" looks like, per project docs)
Author ground truth, not agent taste:
- Plugin author defaults (`KawaiiPhysicsTypes.h`): Damping 0.1, Stiffness 0.05, WorldDamping 0.8/0.8, Radius 3.0, LimitAngle 0. Our skirt sits far above default stiffness with more motion transfer (0.70/0.65) — expect lively-to-wild. The header itself warns: LimitAngle 0 = unbounded rotation ("suppress excessive shaking by setting it properly").
- Anti-penetration recipe (`AnimNode_KawaiiPhysics.h`): `BoneSubdivisionCount` 2+ dummies between bones + radius densify ("prevents skirts penetrating legs"), bridge dummies across columns for cloth sheets, limits DA with thigh capsules / head-neck spheres. Our subdivision is 0 and limits unbound per Aug record — that IS the instability story, pending live re-read.
- Sim space: default ComponentSpace blows up on sudden root motion; WorldSpace/BaseBone exists for exactly that. Revisit if run-cycle pelvis bob (1.067 s genuine gait) keeps exciting the hem.
- Nikki hybrid (WaveHarp doc §2–3, from the UE interview): big panels simmed, trims/ribbons/charms as 4–6-bone chains with bendy stiffness + sinusoid drivers — deterministic, game-realtime. Recommendation: keep Kawaii for skirt body + hem, convert dangling trims to authored sway chains where full sim is unneeded.
- Fabric/material half of "flowy": sheen/velvet lobe on the kilt mats, ≤2 sorted sheer layers, world-space pattern so print doesn't slide with UV, WPO micro-swell reading BeatPulse so the cloth visibly breathes with her music. Stills get an editorial drape shape key (baked settle), never a live sim.
- VFX bar (`NS_SakuraPetals_v2` standard): GPU sim, renderer matches the name, event-driven layering, fixed bounds + sane warmup, one template per idea. Hair ribbons/vfx must meet the same five.

## 3. Next session start
- Read this file + the 0914b report. No re-discovery.
- ⚠ OWNER SAVED 2026-09-14 night (editor closed): worktree shows modified `ABP_Melusina_WaterHair`, `SK_MelusinaHair`, BOTH limits DAs — owner's viewport tweaks may supersede tonight's live-read values. Re-read node settings + limits before tuning anything.
- First command: owner green-bone verdict (weights vs eval-dead), unless it redirects.
- Close each step with compile + save + 0-dirty 0-errored check. Kawaii changes gated on owner viewport, never stills.

## 4. Explicit non-goals (freeze respect)
- No redesign, no new capture framework, no parallel physics authority. Kawaii stays the single skirt/hair owner. Chaos Cloth stays out.
