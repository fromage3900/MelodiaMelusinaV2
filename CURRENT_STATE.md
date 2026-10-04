# Melodia Melusina ? Current State

## Owner-requested animation checkpoint and next 20 minutes - 2026-10-04

Preserve the intentional hybrid in the existing WaveHarp combat owner: LMB caster basics, RMB charged Sparrow draw/hold/fire. The five-shot 0/4/7/11/12 chord progression remains in place. The floating AstrolabeOffset default is now (55,-35,25) cm. Live Coding and a fresh pawn readback passed; the subsequent closed-editor build succeeded at 13:25 with a newer native DLL. Reopened PIE, actual mouse input and visual acceptance are still owed. This checkpoint is compiled source and measured evidence, not animation closeout.

Root independently opened original WaveHarp Transform samples: the driven main grip moves from (-7.75,0,0) to (0,0,53.5) cm. The old export deletes control empties and clears parents; deployed grip geometry remains at origin across forms. The varying pivot motion was omitted. A correct evaluated geometry export is unfinished. Do not apply the older -48.15 cm offset to the current deployed mesh. Shoulder stress/reference-like pose interruptions and hero contact remain open; preserve the mostly fixed gloves/sleeves. Shinbi is installed and has suitable source candidates, but no new donor binding is promoted.

Live Jev jev-1.13.0 selected the following bounded pass with confidence 0.74. Structured text audit only; no image review claimed. Sol remains the sole Monolith editor writer.

| Minutes after editor is ready | Goal | Exit gate |
|---|---|---|
| 0-4 | Verify restarted pawn, loaded default, active AnimBP/clip and LMB/RMB ownership; capture unobstructed front baseline. | Record actual pose source and default. A stale build blocks mutation. |
| 4-12 | Finish original-versus-export measurements at Transform 0/0.5/1; stage one evaluated WaveHarp bake through the existing one-bone/morph asset path. | Correct form geometry, grip axes, vertex/morph integrity and source match. No source overwrite. |
| 12-18 | Integrate only that weapon candidate if source gates and asset backup pass, then replay caster to charged draw/hold/release to caster. Otherwise leave production unchanged and capture the failure. | At most one correction; no body reimport, retarget recreation or new animation authority. |
| 18-20 | Capture matching full-body and mandatory hero close-up views, contact sheet and a real 2-3 second loop if recording succeeds. | One proven improvement or an exact reproducible blocker. No AAA claim from the deadline. |

Six current Melusina packages have local hash-verified preservation copies. These are local snapshots, not a Perforce submit or off-machine binary backup. Code/status/evidence alone are in this scoped Git checkpoint; all other lane changes remain outside it. Evidence: Saved/Audit/MelusinaProgress_20261004/Checkpoint20Min/{jev_20min_ruling,preservation_manifest}.json, HybridAlignment/{original_transform_samples,native_ue_axis_match_summary}.json, CasterPlacement/native_fresh_pie.json. The remaining animation gate and representative family acceptance are unchanged.

## Active Work ? 2026-10-03

**Live editor resumed by owner; Melusina is the active slice.** The original 1 p.m. and extended 2 p.m. Toronto deadlines have passed. The goal remains active and P0 remains paused: visual convergence is not achieved. Owner's major Sir Melodious work is preserved and is outside this pass.

### Owner correction: rejected shoulder retarget removed
Owner rejected the repeated collapsed-shoulder result. `RTG_Sparrow_to_Melusina` was deleted from Content, along with the four idle sequences generated in this pass (two production and two scratch candidates). Unreal reported no package referencers and verified all five assets absent after deletion. MUAL was briefly restored, then failed the pose gate; subsequent editor readback identifies `Animations/Locomotion/A_Melusina_Idle_Mocap_RootX` in the existing Idle player. Five pre-existing state-transition warnings remain. Do not recreate or reuse the deleted retargeter or rejected idle bakes. Preserve the owner-approved six archery clips. Deletion and binding readback are not visual acceptance. Evidence: `Saved/Audit/MelusinaSecondarySources_20261003/{owner_rejected_retarget_deletion.json,current_proven_route_readback.json}`.

### Canonical runtime map
`BP_MelusinaJRPGCharacter.CharacterMesh0` ? `SK_Melusina_V2_Body` / `SK_Melusina_Skeleton` ? `ABP_Melusina_Current.MelusinaLocomotion` ? `DefaultSlot` ? existing `UpperBody` slot / Layered Blend Per Bone ? Kawaii skirt (`c_kilt_master_x`) ? disabled eye CopyBone / blink ? output. No connected body runtime retarget, Control Rig or hand IK. Shirt, current R2 SmoothChains skirt, boots and Accessories use Leader Pose. Hair uses its separate rig / `hair_root`, CopyPose + Kawaii, attached to body `head_x`.

### Fixed and saved ? glove/sleeve source bind offset
Measured current UE-exported glove geometry is offset in both true reference pose and calibrated native hold: reference median ~63?64 mm; hold ~59?63 mm. A bounded Blender source fit moves only glove/sleeve vertices, preserving topology, skin weights, materials and the existing skeleton. Reference glove median is now ~12 mm; held median ~13?14 mm. All 465 names/parents match after staging and canonical reimport. Shared Skeleton and six owner-approved SparrowArchery clips were not edited. Original Accessories `.uasset` backup SHA256 `e101d8752fa3b983307cc6cb25216d0532a8f4702734d21b2d4aaf394c416bde` is retained.

`SK_Melusina_V2_Accessories` is saved after two fresh Morning PIE replays. Front close-ups show curled glove fingers replacing the former flat plane. Runtime AnimBP remains active, same canonical mesh owner/Leader Pose, ten materials retained, no PhysicsAsset substitution. This is a scoped improvement, **not visual acceptance**: residual fingertip/knuckle and sleeve/contact defects remain. Receipts: `Saved/Audit/MelusinaHandsSleeves_Jev_20261003/{canonical_reimport.json,PostFit_Run1,PostFit_Run2}`. A subsequent small digit-cage fit is diagnostic only, not promoted.

### Runtime defects still reproducible
WaveHarp raised arm/weapon/head clearance and detailed hand contact remain unpassed. Normal player-camera release holds pawn yaw at 0 degrees; the prior 180-degree shot turn did not reproduce when the actual firing view target was the pawn. Projectile direction/hit alignment is not certified by this probe.

Idle returns to T-pose with active AnimBP, Idle state weight 1 and no montage; this was reproduced **before** reimport. Idle directly plays `A_CAS_Melusina_Idle_Loop`, whose current skeleton is canonical but sampled hand pose is reference-like. Other idle candidates contain invalid scale/pose data; none was blindly rebound. The previous approved Mocap RootX route also needs current visual acceptance.

VFX integration 2026-10-04: lane-hit bursts were silent (default NS_Melodia_LaneHit swept from Candidates/). Authored /Game/Melodia/VFX/NS_Melodia_LaneHit (ClickSparkle donor: one-shot, loop Once) + LaneIndex/LaneColor/LinearColor + GradeIntensity params; InitializeParticle.Color bound to User.LaneColor; controller MelodiaPresentationRhythm.LaneHitEffect reslotted to it, compiled 0e/0w + saved. Lookdev maps ready headless: Saved/Dashboards/font_sweep_map_20261003.json (74 widgets/424 rows) + color_sweep_map_20261004.json (94 widgets/870 rows; stock-template rows will die with Slice B, sweep Melodia-owned first). Motion finding: WBP_GradePop is an empty husk (like the interact prompt) — live grade motion is native-painted + NS; no UMG animation authored. Still owed: battle proof of lane bursts with per-grade colors; C++ hit-stop/grade-pop tuning needs a closed-editor build.

### Owner-requested UI/HUD pass — scoped live pass 2026-10-03/04
D2 fonts imported (F_KaiseiDecol family + F_KleeOne family); composite carries the named slots. 37 BowHUD textures imported (/Game/Melodia/UI/BowHUD/Textures/); WBP_Melodia_BowHUD created under MelodiaWaveHarpHUDWidget. Stock-template kill is replace-then-retire with pin-level proof: controller BattleUI to BP_MelodiaBattleUI, Victory to BP_MelodiaVictoryDialogue, both FadeTransitions to BP_MelodiaFadeTransitionUI (all compiled 0e/0w + saved); full spawn map enumerated (28 CreateWidget pins + 3 WidgetComponent sites). BP_MelodiaBattleUI off-screen husks (SongPickLabel, DrawBurst, zero refs) collapsed. WBP_MelodiaInteractionPrompt is an empty unreferenced husk — retire, do not revive. OverworldHUD internal layout audited clean (no sibling overlaps). Source edits awaiting Live Coding: idle bow reticle 50pct/0.32 alpha, prompt cartouche 371 to 341, coral/blue bar fills. Still owed: 12 Melodia duplicates (Info/LevelUp/UnitButtonList/Mobile/NoCursor/Pause/YesNo/ShopBuy/ShopSell/Save/Craft/ItemObtain) + 3 component repoints; live battle-spawn proof (tutorial slime needs the real F-interact); contract-test source edit needs a closed-editor build to run.

### Owner-requested Quill correction ? scoped live pass
`BP_KaleidoNaveArrivalTrigger` BeginPlay playback link is disconnected; ActorBeginOverlap is filtered to the player pawn. Fresh startup has zero interpreters. A local outside-volume approach followed by actual player overlap activates the Wardrobe interpreter after the existing delay. This proves player-entry activation, not an uninterrupted walk from spawn or full narrative completion. Receipt: `quill_walk_entry.json`.

### New secondary-motion work ? staging
Owner requests body-fitted clothing/hair collision, shirt hem bones/Kawaii staging and swinging hair ornaments/jewellery. Two Luna 6 lanes work from fresh canonical UE exports in `Saved/Audit/MelusinaSecondarySources_20261003`. Shirt is separate; its current weights include skirt chains and produce torso/side stretching in the native hold. Source fit/hem weights are being corrected in disposable staging. Two substantial PearlSheen ornaments in the separate hair mesh are unweighted; a bounded fix binds them to existing measured B strand bones. Hat/head decorations remain anchored; no substantial separate pendant geometry was identified in the supplied meshes.

Installed Kawaii supports body collision sharing across attached actor family. Current body/hair nodes have sharing disabled, each with its existing LimitsDataAsset and empty PhysicsAssetForLimits. Body-fitted shape staging and exact UE binding/readback remain owed. No new physics solver or animation architecture is authorized.

### Evidence and gates
**SOURCE:** Blender offset/clearance measurements, preserved geometry/weights, neutral FBX roundtrip. **EDITOR:** canonical reimport/save, 465-name/parent hierarchy, ten material interfaces, clean shared Skeleton. **PIE:** two fresh archery-owner replays with front full-body/close-ups and active AnimBP; Quill startup/player-entry probes. These are gameplay-owner API calls, not new keyboard-input certification. Hair root stays within ~0.03 cm of `head_x` across recorded phases; this is attachment proof, not complete hair-collision proof.

Owner supplied a real `jev-1.13.0` ruling in `SOL_NOTES.md` / `jev_ruling.json`. The earlier missing-key claim was incorrect: the existing configured credential supports live Jev. Root subsequently opened actual `jev-1.13.0` responses in `jev_existing_authority_audit.json` and `jev_shoulder_stress_audit.json`. These are structured state judgments, not image reviews. The earlier `jev_postfit_ruling.json` remains a fallback and is not Jev evidence.

### Updated animation closeout plan — 2026-10-04

**HOLD: full runtime presentation is not ready to close.** Owner confirms sleeves/gloves are mostly fixed; preserve that work. Owner also confirms the existing retarget can pop at stressed shoulder poses. No new animation architecture, solver, skeleton, donor route, or AnimBP is planned. Sol owns the single Monolith editor writer; Luna discovery stays read-only. Time boxes below bound each diagnostic pass, not a promised completion deadline. A failed gate retains its concrete failure and stops promotion.

**Current checked facts.** The native five-shot chord code remains in `MelodiaWaveHarpCombatComponent::ReleaseDraw`: semitones 0/4/7/11/12, fifth-shot chord completion and counter reset. The current source diff changes mouse/charge handling, not chord progression. A fresh five-shot runtime check did not complete because its observer requested a nonexistent `status_text` Python attribute; this is not proof that the chord was removed or that current LMB input works. The loaded build must be checked against pending native edits before input certification.

31 editor pose samples per clip show shoulder-to-arm spacing of 15.774 cm for Mocap Idle/Walk/Run versus 34.789 cm for approved Sparrow Draw/Hold/Fire. Both families currently use skeleton translation mode `Animation` at the four arm/forearm joints. A bounded `Skeleton`-mode trial made their evaluated translations agree, but fresh PIE still showed reference-like raised arms and unacceptable presentation. It was rejected: all four modes were restored to `Animation`, the original skeleton package was reloaded from disk, and no production retarget setting was saved. The existing translation probe was also restored after capture. These measurements identify a discrepancy; they do not establish the complete cause of stressed-pose deformation. Latest verified PIE state is stopped. Evidence: `shoulder_stress_measurement.json`, `shoulder_skeleton_translation_modes.json`, and `Saved/Audit/MelusinaProgress_20261003/{ShoulderStressCompare,ShoulderTranslationMode}`.

| Bounded goal | Work and limit | Required exit evidence |
|---|---|---|
| G1 — certify basic attack ownership (15 min) | Verify loaded native revision, possessed pawn, input stack and movement/action permissions. Observe five real LMB releases inside the existing chord window; then repeat after one RMB charge/release. Use existing counters/logs and montage segments, with a corrected read-only observer. | Five successful basic shots, steps 1–4 then fifth-shot reset, exactly one chord completion, caster sequence actually playing, and no stuck aim/draw/charge after RMB. API calls remain separately labeled. |
| G2 — locate the stressed-pose cause (20 min) | Trace actual live caster and charged montage/slot/layer through final mesh pose. Compare raw clip, mesh and skeleton reference translations, source-mesh provenance, FK mapping/pose and final bone transforms at the same frames. Preserve working locomotion and body/garment bindings. | One reproducible failing frame/transition and its exact responsible reference/configuration, with shoulder→upper arm→elbow→wrist chain measurements. No diagnosis inferred solely from filenames or a numeric pose-gate pass. |
| G3 — make one bounded correction (20 min per attempt, maximum two before reassessment) | Back up the responsible asset, change only the demonstrated setting/reference in the existing authority, reread it, then replay baseline and failing poses. Regenerate an existing baked clip only if correcting its established authoring path requires it. | Clear improvement in matching camera frames without locomotion, hand, root or garment regression. Exact rollback on failure. No bulk rebake or resurrection of the deleted route. |
| G4 — caster pose/contact gate (15 min) | Test caster stance, each of five basic releases, recovery, repeat-cast and a delayed click that resets the chord. Review shoulder silhouette, elbow feasibility, wrist/finger pose, prop grip and face/sleeve clearance. | Fresh full-body and hero-close-up evidence of the actual caster clips; no shoulder collapse, detached contact or reference-pose interruption. Preserve accepted glove/sleeve fit. |
| G5 — transition stability (20 min) | Exercise idle→LMB→idle, repeated LMB→RMB draw/hold/release→LMB, RMB cancellation, early release, LMB during RMB, and walk/turn/stop during supported actions. Repeat the mixed sequence 20 times across two fresh PIE sessions. | Actual input/event ordering and live pose-source trace agree; no stuck flags, unexpected montage replacement, arm-spacing pop, root jump, foot slide or dropped next basic attack. |
| G6 — presentation evidence (15 min) | Use transient diagnostic cameras in Morning with PPV disabled. Fix 36×24 mm filmback; start with full-body front at 24–35 mm, left/right 30–45° three-quarter views, side profile, and 50 mm hero contact view. Adjust distance from measured bounds until head, hands, prop and feet fit; verify no companion/environment occlusion before capture. Match camera matrices across before/after. | Labeled contact sheets: rows by view, columns by idle/cast onset/release/recovery/draw/hold/fire/return. Each frame records PIE run, time, active clip/montage/slot and settings. Include 2–3 s real-frame loops for caster and charge transitions; no generated/interpolated proof. Bone overlays are separate diagnostic views. |
| G7 — retire-route and final replay gate (15 min) | Run the existing fresh Asset Registry/native-binding stale-reference gate and existing pose gate. Resolve reachable denied assets, including recorded speed-zero blendspace references and outstanding battle bindings. Reopen/replay the saved canonical path, then sample dodge, interaction, reaction and rhythm/presentation families. | Zero unexplained retired runtime references, repeatable saved-state PIE presentation, complete milestone sheets/loops and an explicit remaining-defect list. Only then close animation convergence and resume P0. |

Jev reviews measured, bounded alternatives after G2 and matching visual evidence after G3–G6 where its available interface supports it. A structured text ruling must not be presented as image review. Sol independently opens every image/report before declaring a milestone passed. Camera framing, contact sheets and numeric gates supplement playing-runtime proof; they cannot replace it.

### Sparrow reference and WaveHarp placement ? 2026-10-04

Owner clarified the intentional hybrid: LMB is caster animation with floating astrolabe; RMB is full Sparrow charged draw/hold/fire. Sparrow remains the archery/contact reference for RMB, not a replacement for the caster mode. Fresh owner-API PIE executes CastShoot at deployment 0 and the approved Sparrow draw/hold/fire clips at deployment 1. Source Sparrow bow-base-to-left-hand transform stays constant across nine sampled draw/hold/fire frames. Do not copy its numeric socket offsets directly into Melusina's different mesh/bone axes.

Fresh exported deployed WaveHarp and native GeometryScript reference geometry falsify the old staging grip offset: all 160 main-grip vertices match at mesh origin (max residual 2.83e-7 cm), and 200 bowstring vertices prove FBX-to-UE axis conversion. Bow_Deployment leaves the measured grip stationary. Do not apply the old -48.15 cm translation. This is geometry/axis evidence, not hero contact acceptance.

Scoped caster placement change: the existing native AstrolabeOffset default is (55,-35,25) cm, lowering the float grip by 100 cm while retaining forward distance, lateral face clearance, spin/bob, and the RMB path. Live Coding succeeded and applied the patch; both native CDO and a fresh PIE pawn independently read back the new default. No skeleton, retargeter, clip, socket, BowGrip, garment or level asset was edited. Source/editor/fresh pawn default proof is established; unobstructed motion/contact acceptance and saved/reopened editor proof remain separate. Initial centering candidate (55,0,25) was not retained. Runtime captures are diagnostics and do not certify actual mouse input or full animation convergence.

Jev jev-1.13.0 independently reviewed the structured measurements and chose the existing float adjustment with zero grip translation, retaining the open shoulder/archery gate. Text audit only. Evidence: Saved/Audit/MelusinaProgress_20261004/{HybridAlignment,HybridAlignmentFramed,CasterPlacement}; native source: MelodiaWaveHarpCombatComponent.h:92.

### Today's presentation acceptance lens ? 2026-10-04

Use Infinity Nikki as a quality reference for readable graceful poses, clothing-aware movement, stable layered contact and restrained character lighting. Infold describes skeletal physics/Chaos and proprietary collision constraints; this is a visual benchmark, not authorization to reproduce its architecture. Primary reference: https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world/

Today's bounded presentation slice is idle/walk/turn/stop, five-chord caster basics, RMB draw/hold/release/follow-through and their mixed transitions. First settle actual input and the responsible stressed-pose layer. Then validate contact and the existing Kawaii secondary paths: hair rooted to head, strands/ornaments following coherently, shirt sitting over skirt, no body penetration, explosive simulation or persistent drift. Preserve owner-accepted sleeve/glove fitting; reopen it only for a reproducible current defect. New DCC rigging and aesthetic expansion do not displace these gates.

Presentation review asks whether shoulders form a continuous silhouette, elbows/wrists remain feasible, hands maintain intentional contact, feet/root stay stable, and hair/clothes settle with controlled lag without obscuring her face. These are proposed acceptance criteria, not claims of current passing behavior. Judge both neutral PPV-disabled diagnostic captures and the normal gameplay lighting/camera. Keep bone overlays separate. Fire using the actual player view; review cameras must not alter aim or projectile direction. Capture unobstructed front/three-quarter/side and hero contact views, matching before/after cameras.

Red blockers are shoulder collapse/pop, reference-pose interruption, prop/body/face penetration, broken input/chord continuity, detached garments and unstable simulation. A polished still cannot waive them. Record SOURCE, EDITOR, real-input PIE and saved/reopened replay separately. No AAA certification from a clock deadline. Existing G1?G7 remain the work plan and final gate.

Live Jev `jev-1.13.0` reviewed this structured plan and chose input/pose diagnosis before contact, secondary motion and presentation proof; it requires repeated real-input PIE and saved replay before closeout. This was a text decision audit, not image review. Receipt: `Saved/Audit/MelusinaSecondarySources_20261003/jev_today_presentation_plan.json`.

Still owed: remaining glove/finger/sleeve contact; body/weapon/head clearance; valid idle/locomotion continuity; shirt secondary staging and connected simulation; body/hair collision and ornament motion in fresh PIE; representative dodge/combat/rhythm/interaction/reaction states; existing stale-reference gate reconciliation (nine battle bindings remain); full convergence acceptance. Local structural checkpoint `4bdab4525` redirects battle BeginPlay to visible presentation mesh; compilation passed but fresh battle verification remains owed. No further commit or bulk submit in this slice.

## CORRECTION 2026-10-01 (owner, supersedes stale runtime claims)

The owner confirms: **WASD works, the bow works, damage works, the gameplay loop works.** The older "still owed" lists — real-input WASD proof, the stock-then-GOOD/PERFECT ladder, the Melusina-possessed PIE probe, the Quill-interpreter movement-lock chase — are **closed**, not pending. Active work is animation and lookdev only. The one genuinely open technical item is the **closed-editor 5.8 build** (party bootstrap UNBUILT), a build-hygiene task.

## Choral Sheep — Capstone Build

**Canon tip:** `gn_v2_20260919/choral_sheep_GNv3_S5c_decor_20260925.blend` (14/14 gates, 0 animations)
**Best base:** `gn_v2_20260919/choral_sheep_GNv3_A1_idle_20260927.blend` (HD sculpt 4000v + wool + 16 shape keys + idle + all ornaments + 474 bones)
**AAA output:** `Saved/Audit/choral_sheep/choral_sheep_AAA_v1_20261003.blend` (walk animation authored, 3-point lighting, turntable renders)
**Renders:** `Saved/Audit/choral_sheep/aaa_render_20261003/` (9 Cycles CPU frames)

### Still owed
- Run, graze, bleat, ear flick, tail wag, harmonize animations
- SSS wool material + proper eye shader
- UE integration (retarget, ABP binding)
- In-PIE follow proof
- Visual sign-off on wool, horns, and crown (all gates numeric, no owner eye yet)

## Proven Creative Capability Surface

**Default:** author content through these seams. Boss battles, new rhythm skills/attacks, side quests, encounters, creature episodes, outfit abilities, and musical world puzzles are content problems. They do not require another gameplay framework or another authority.

| Capability | Status | Entry Points |
|---|---|---|
| QuillScript narrative | LIVE PROVEN (scoped) | `Plugins/QuillScript/`, `UMelodiaNarrativeSubsystem`, `DA_MelodiaIntegrationConfig` |
| Quill → JRPG → rhythm → result → Quill resumes | LIVE PROVEN (scoped) | `MelodiaExternalJRPGBridgeSubsystem`, `MelodiaIntegrationMap` |
| Rhythm grade → JRPG damage | LIVE PROVEN | `MelodiaRhythmCombatSubsystem`, `BP_MelodiaJRPGGameInstance` |
| Wardrobe + traversal hooks | LIVE + RESTART PROVEN | `UMelodiaWardrobeSubsystem`, `MelodiaTraversalComponent` |
| Music-as-key world unlock | LIVE PROVEN (scoped) | `BP_MusicManager`, `MelodiaMusicClockSubsystem` |
| Choral Sheep companion | LIVE PROVEN (PIE) | `BP_ChoralSheep`, `DA_ChoralSheepDefinition`, `TryBeginHarmonize` |
| Save/checkpoint/reward | LIVE/RESTART PROVEN | `UMelodiaNarrativeSubsystem`, `BP_JRPGSaveGame` |
| UE 5.8 PCG | PRESENT / scoped LIVE | `Content/Python/pcg/`, `/Game/EnvSandbox/PCG/` |
| World Compiler | SOURCE + scoped LIVE | `Tools/world_compiler.py`, `recipes/morning_rainbow_bloom.v1.json` |
| Foundry converged menu | EDITOR PROVEN 2026-10-03 | LevelEditor `WorldCompiler > Foundry` menu (`init_unreal.py`): MI inspect + WC status + Foundry validate/plan via `Content/Python/foundry_converged_panel.py`; all entries executed live |
| Melodia Platforms menu | EDITOR PROVEN 2026-10-03 | LevelEditor `Melodia > Platforms`: live list/set of `AMelodiaMovingPlatform.TravelDuration` + water `Speed`, set-and-restore verified on `L_MelusinaMorning` (5 platforms), no save, no dirty packages |
| Platform PIE motion | PIE PROVEN (scoped) 2026-10-03 | `MelodiaMovingPlatform` Z 1188.20 → 1169.61 in `L_MelusinaMorning` simulate; receipt `Saved/Audit/pie_motion_proof_20261003.json` |
| Harmonize follow/call | PIE PARTIAL 2026-10-03 | Sheep left authored dell for pawn area live; `TryBeginHarmonize` accepted without error; receipt `Saved/Audit/harmonize_follow_20261003.json`. Owed: framed emissive captures, proximity-after sample |
| Chladni pitch sheet | EDITOR EXPORT 2026-10-03 | 12 authored `T_Chladni_PC_*` exported via `TextureExporterPNG` + 3 root PNGs → `Saved/Audit/chladni_pitch/contact_sheet_chladni_pitch.png` (15 tiles, verified) |
| Cymatic field west rim | PIE PROVEN (scoped) 2026-10-03 | `BP_CymaticField_WestRim` host + Field component at WestRim PCG (−5760,162,100), saved in `L_MelusinaMorning`; `TriggerHit` displaced rim instance peak 18.18 cm; receipt `Saved/Audit/cymatic_field_westrim_proof_20261003.json` |
| Melodia menu: Perches/Placement/Wardrobe | EDITOR PROVEN 2026-10-04 | `Melodia` menu sections over native owners: `ASirPerchPoint` spawn path proven (spawn/label/destroy, no residue), snap + wardrobe panels HOLD-correct outside PIE/level |
| Houdini/Hython | SOURCE/TOOL PROVEN | `Tools/Houdini/`, `Content/Python/create_hda_arpeggio_stair.py` |
| Copernicus textures | PRESENT / offline | `Tools/Houdini/copernicus/` |
| Nikki toon materials | PRESENT / scoped LIVE | `M_Master_Toon_Character`, `M_Master_Toon_Universal` |
| Audio-reactive presentation | SOURCE + scoped LIVE | `MelodiaAudioReactivePresentationSubsystem`, `MPC_Melodia_Palette` |
| Frozen PPV stack | OWNER-APPROVED / scoped LIVE | `PPV_NikkiDream`, `ET_Melodia_CharacterFX` |
| Melodia UI | PRESENT / SOURCE-TOOL | `melodia-ui-artist` skill, `Content/Melodia/UI/Quill/` |

**Full capability table:** `Docs/Research/CREATIVE_CAPABILITY_SURFACE.md` (pre-collapse docs: `git show 7d271c15:<path>`)

## Version Control

See `Docs/Production/STORAGE_ARCHITECTURE_2026-10-01.md` and `Docs/Handoffs/SESSION_CLOSEOUT_2026-10-01.md`. Git carries code/docs/plans; Perforce carries bulk binary. Perforce server root is `D:\perforce\root` on this machine. GitHub is the only offsite copy.

## Pre-collapse docs
Every deleted handoff/plan/report is recoverable with `git show 7d271c15:<path>` (tag `docs-precollapse-2026-09-10`).
