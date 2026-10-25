# Melusina — Character Grounding, Layered Costume and Rig Development

**Unreal Engine 5.8 · Houdini/KineFX · Blender · evidence captured 23–24 October 2026**

This breakdown follows one character through animation, procedural ground contact, garment deformation and source validation. The demonstrated result is a staged native idle with unfolded knees and measured boot contact. Walk, run and sprint preservation pass their compression controls; playable gait, complete costume motion and production admission remain separate acceptance gates.

The accompanying visual sequence is [grounding](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/Sheets/sheet_01_runtime_leg_grounding.png), [boot skinning](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/Sheets/sheet_02_boot_skinning.png), [skirt layers](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/Sheets/sheet_03_skirt_layers_proxies.png), [ownership](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/Sheets/sheet_04_runtime_ownership.png), [rig expansion](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/Sheets/sheet_05_rig_expansion.png), [gameplay presentation](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/Sheets/sheet_06_gameplay_portfolio.png) and [native axis correction](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/Sheets/sheet_07_native_axis_correction.png).

## 1. The folded knees: a shortened target, not skirt physics

The original runtime graph raised copied foot targets by **18.841 cm left / 21.509 cm right** before FootPlacement. The native node derives desired leg extension from those IK targets. Its pelvis solve therefore treated the lifted targets as the authored reach; LegIK folded the anatomical legs to satisfy the shortened distance. The root plane also sat approximately **17.15 cm above the collision floor**. Disabling Kawaii did not change the knees, separating the primary joint defect from costume simulation.

| Controlled observation | Left knee | Right knee | Pelvis component Z |
|---|---:|---:|---:|
| Original enabled graph | 98.83° | 93.04° | 62.765 cm |
| LegIK disabled | 179.61° | 174.72° | 62.765 cm |
| FootPlacement and LegIK disabled | 179.61° | 174.72° | 79.965 cm |
| Ground-reference candidate; both native solvers enabled | 175.89° | 173.32° | 90.766 cm |

The staged candidate neutralizes the target lifts and authors existing `c_traj` as the footwear support plane at **−28.001 cm**. Inverse changes to its two direct children, `root_x` and `c_root_master_x`, preserve the sampled world pose. FootPlacement uses this ground reference while anatomical feet remain the solver targets. [Controlled A/B](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/runtime_layer_comparison.json), [candidate contact](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/ground_frame_clean_boots.json), [native extension calculation](</C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Animation/AnimationWarping/Source/Runtime/Private/BoneControllers/AnimNode_FootPlacement.cpp:298>).

On the flat staged floor, the initial same-tick clean-boot sample has CPU-skinned minima **0.000 / +0.739 cm**. Bare-foot geometry sits **9.447 cm** above that floor; this is consistent with footwear whose bind sole extends **8.603 cm** below the bare foot. An ankle-height number alone would miss the heel and sole relationship. These are idle measurements, not slope or gait certification. [Bind geometry](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/KineFX/contact_summary.json).

## 2. Preserve motion through an honest compression control

The idle duplicate preserves **162 frames × 23 checked bones**, with maximum compressed world-position difference **0.000001907 cm** and quaternion-component difference **0**. Only the three ground-frame tracks change. [Idle preservation receipt](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/A_Shin_Idle_stand_MocapConv_ground_frame.json).

The walk initially differed from its original compressed playback by approximately **0.01168 cm / 0.00086797 quaternion component**. A separate untouched duplicate received the same three-track rewrite without the ground edit, forcing the same codec rebuild. Across **36 frames × 23 bones**, candidate versus control differs by only **0.000009537 cm / 0 quaternion component**. Both rebuilt clips share the original-versus-rebuild difference. The same control passes for **run: 36 frames** and **sprint: 111 frames**, each checking 23 bones with the same maximum position difference and zero quaternion-component difference. All three source file hashes are unchanged. This isolates codec rebuilding without loosening the preservation gate; it establishes source preservation, not live gait. [Walk](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/A_Melusina_Walk_Mocap_RootX_SeamFix_recompression_control.json), [run](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/A_Melusina_Run_Mocap_RootX_SeamFix_recompression_control.json), [sprint](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/A_Melusina_Sprint_Mocap_RootX_recompression_control.json).

## 3. Footwear: remove unrelated influences, retain the sculpture

KineFX exposed boot vertices influenced by skirt chains and the opposite leg. The localized candidate changes **843 of 5,540 vertices**, removing those unrelated contributions and renormalizing retained influences. It preserves geometry, materials, hierarchy and the **465-joint** imported bind.

All **12 round-trip gates** pass: vertex count; topology/materials; zero vertex drift; joint names; hierarchy; bind positions; bind matrices; requested weights; removal of kilt influences; removal of opposite-side influences; normalized nonzero weights; and at most four influences. [Weight delta](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/KineFX/boots_weight_delta.json), [round-trip gates](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/KineFX/boots_candidate_roundtrip.json).

**Source repair and retained equipment are separate proofs.** The initial same-tick clean-boot sample is valid, but the old capture helper reconstructed the pawn through SpringArm editor-property writes, restoring the original equipment. The later native-axis contact receipt explicitly identifies the original production boot mesh. No independent production wardrobe refresh defect was established. Persistent candidate equip through the corrected capture, re-equip and reload remains unverified. [Later mesh identity](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/native_axis_idle_contact.json).

## 4. One layered skirt, one simulation owner

The skirt has **30,509 points** and three principal hem surfaces containing **20,781 / 6,476 / 1,440 points**. They share **64 radial bones** across sixteen four-bone chains. Each measured hem pair contains **720 coincident seam vertices with identical weights**. Coincident seams are intentional construction; splitting every surface into an independent solver would disturb established correspondence. [Layer and chain measurements](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/KineFX/contact_summary.json).

The body ABP owns ground contact followed by Kawaii skirt motion. Shirt, skirt, boots and accessories consume its final pose through LeaderPose. Wardrobe requires the same `USkeleton` and disables garment component collision. Hair is a deliberate separate branch: it clears LeaderPose, installs its own ABP and receives the body as its source mesh. [Wardrobe compatibility](/C:/EnvironmentPortfolio/BS_GodFile/Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaWardrobeComponent.cpp:175), [follower binding](/C:/EnvironmentPortfolio/BS_GodFile/Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaWardrobeComponent.cpp:265), [hair ownership](/C:/EnvironmentPortfolio/BS_GodFile/Source/BS_GodFile/MelodiaIntegration/MelodiaHairComponent.cpp:266).

## 5. Rig expansion: measured proxies before new joints

Native body reference-pose inspection resolves all **16 terminal axes**: configured **+X is approximately 90° transverse**, while **−Y aligns within 0.0000361°** of the longitudinal chain direction. The staged `ABP_LegSkirt_Axis_Candidate` changes `X_Positive → Y_Negative`, retaining **3 cm** dummy length. Three stable fingerprints, exact **28-node / 25-connection** graph assertion, compile **0 errors / 0 warnings**, and native enum readback support the bounded change. Staged idle knees remain **175.8876° / 173.3249°**; this establishes reference-pose alignment and idle compatibility, not complete motion coverage. [Native axis proof](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/KineFX/native_tip_axis_verification.json), [guarded candidate](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/native_skirt_axis_candidate.json).

An **offline proposal** adds sixteen virtual terminal-support lines. Their estimated lengths range **9.421–16.475 cm**, against measured maximum longitudinal reach **17.633 cm**. All **10 source/artifact gates** pass, including unchanged inputs, unchanged canonical joints/weights, unique terminals, valid parents and finite geometry. No production skeleton was created.

These axial endpoints are not cloth-surface contacts: lateral skin offsets produce a maximum endpoint-to-nearest-skin gap of **7.805 cm**. Native reference axes are now verified; proposed reach, collision radii, runtime coverage and temporal stability remain unverified. The proposal visualizes missing support; it does not establish collision coverage. [Proxy definition](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/KineFX/skirt_terminal_support_proxy_candidate.json), [ten gates](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/KineFX/skirt_terminal_support_proxy_gate.json).

**Proposed deformation expansions:** integrate the existing seventeen-bone shirt hem—one master plus eight two-level spokes—then evaluate bounded ribbon/bow chains where rigid attachment demonstrably fails. Give each fabric region explicit weights, root ownership, collision clearance and LOD policy. The shirt candidate already has normalized weights and 232 hem-influenced vertices; runtime integration is separate. New joints must exist in the **body mesh RefSkeleton**, shared skeleton and garment bind. LeaderPose maps against the leader mesh’s bone list; adding garment-only bones leaves them at reference pose. [Shirt source acceptance](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/ShirtBones_20261020/legal_fbx_acceptance.json), [engine follower mapping](</C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/Components/SkinnedMeshComponent.cpp:3481>).

## 6. Gameplay and performance acceptance

Validate matched-camera idle → walk → turn → stop, sprint braking, bend, jump/landing, slope/stairs and action recovery on the dressed possessed pawn. Measure knee-plane continuity, sole clearance, planted-foot drift, cuff fit and inter-layer penetration. Repeat after reset, re-equip, respawn, reload and LOD/offscreen return. Preserve frozen donors and record exact tested asset hashes.

Profile body-only, full outfit and Kawaii off/on on named target hardware at controlled frame rates. Capture evaluation p50/p95/p99, warmup spikes, bone/dummy/bridge counts, collider/constraint counts, memory and world sweeps. Existing counters belong to **`stat Anim`**. Fixed substepping defaults to four catch-up steps and discards excess time; verify active settings before interpreting hitch recovery. No AAA millisecond budget has been established here. [Instrumentation](/C:/EnvironmentPortfolio/BS_GodFile/Plugins/KawaiiPhysics/Source/KawaiiPhysics/Private/AnimNode_KawaiiPhysicsInternal.h:11), [substepping](/C:/EnvironmentPortfolio/BS_GodFile/Plugins/KawaiiPhysics/Source/KawaiiPhysics/Private/AnimNode_KawaiiPhysicsSimulation.cpp:203), [reset](/C:/EnvironmentPortfolio/BS_GodFile/Plugins/KawaiiPhysics/Source/KawaiiPhysics/Private/AnimNode_KawaiiPhysics.cpp:229).

## 7. Proposed 75-second portfolio edit

| Time | Shot |
|---|---|
| 00–08 | Hero silhouette and in-engine presentation |
| 08–20 | Matched original/candidate knee and sole comparison |
| 20–32 | Boot influence isolation and unchanged bind overlay |
| 32–44 | Three hem surfaces, shared seams and radial skeleton |
| 44–57 | Kawaii off/on through turn, stop and bend, after acceptance |
| 57–67 | LOD transition and measured cost overlay, after profiling |
| 67–75 | Reset/reload proof, contribution, tools and credits |

Label shots **source**, **staged live**, **real input** or **packaged**. Keep camera, animation time, outfit and lighting matched. Publish the demonstrated repair and its limits; reserve gameplay-complete claims for the corresponding observed tests.

## 8. Necklace: restore the authored attachment frame

The separate static necklace was rest-baked around `spine_03_x`, but the character construction attached it to `neck_x`. The saved correction restores its chest attachment and computes the full relative bind transform, including rotation and scale. The existing jewellery geometry and materials are retained. Compile reports zero errors and warnings; the exact construction graph assertion matches 14 nodes and 16 connections. Every other component default compares unchanged. Fresh PIE and deliberate construction re-entry both retain the corrected socket. [Saved fix](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/necklace_persisted_fix.json), [fresh-spawn proof](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/necklace_fresh_pie.json), [comparison sheet](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/Sheets/sheet_08_necklace_attachment.png).

The capture helper now avoids SpringArm editor-property changes, which reconstructed the PIE pawn and reset temporary overrides. No production wardrobe refresh defect was established. Retained cleaned-boot equipment still needs a dedicated test; production body animation and skeleton remain unchanged.

## 9. Gacha character lessons and a bounded Jev use

These are reference lessons and proposed Melusina content, not a claim that the following performance system is integrated.

| Developer reference | Supported design choice | Melusina application |
|---|---|---|
| [Infinity Nikki, Infold's producer](https://blog.playstation.com/2024/05/30/infinity-nikki-an-open-world-dress-up-adventure-is-coming-to-ps5/) | Outfit abilities shape exploration, and photography is part of presentation. | Author each costume's silhouette, motion clearance and interaction poses as a coherent set; verify in the gameplay camera and photo camera. |
| [Genshin Impact, HoYoverse's studio technical director](https://blog.playstation.com/2021/08/20/genshin-impact-version-2-1-join-the-hunt-with-aloy-in-the-world-of-teyvat/) | Raiden's stance and combat movements were chosen to express calmness, majesty and divine power. | Define her movement vocabulary first: gait, stopping, bow handling and quiet gestures should communicate the same personality. |
| [Zenless Zone Zero, HoYoverse's technical lead](https://blog.playstation.com/2024/12/06/zenless-zone-zero-launches-version-1-4-december-18/) | Character interaction extends into city activities; haptic responses differ by combat action. | Give quiet interactions and action feedback the same care as showcase poses. Coordinate authored sound, timing, expression and optional haptics. |

My proposed art direction is poised, curious and musical. A small set of finished performances can communicate this through an eye movement, a head turn, a weight shift, a hand gesture and a believable costume settle. Test their readability in motion before adding more expressive choices.

The existing [Listening Field director](/C:/EnvironmentPortfolio/BS_GodFile/Tools/listening_field/jev_director.py:67) already chooses closed authored states at phrase boundaries, schedules decisions for the next bar and has a deterministic fallback. Its [directive vocabulary](/C:/EnvironmentPortfolio/BS_GodFile/Tools/listening_field/directive_schema.py:1) is for the meadow and flock; hero gestures are not currently part of that contract. The isolated [bow conductor prototype](/C:/EnvironmentPortfolio/BS_GodFile/Prototypes/JevBowConductor/jev_bow_director.py:1) offers reusable selection, dwell and provenance patterns, while explicitly leaving execution unwired. Presence of a referenced animation file is not performance-quality proof.

Use Jev first as a production reviewer over finished takes: supply the same camera and animation context plus measured contact/clearance results; ask it to choose among legal candidates and explain the tradeoff. A text-only decision can review telemetry and descriptions; visual judgment requires an explicitly supported image/video path or the artist. Jev confidence is not an acceptance score.

For a later hero integration, existing gameplay code should first determine whether an optional expressive moment is legal. Jev can select one approved idle reaction or post-action flourish, then the existing animation/presentation owner executes it at a safe boundary. Player input, aim, attack release, hit frames, interruption and return to control remain deterministic. Stale, invalid or missing decisions use the authored default. No network response belongs inside the animation or Kawaii evaluation loop.

The next reviewable content slice is a thirty-second walk → stop → notice → player-triggered bow release → settle sequence. Record actual input response, contact, costume clearance and target-hardware frame cost. Existing rig fixes must pass moving gameplay before this sequence is presented as finished. No live Jev judgment was run for this design brief.

## 10. Upper-waist localization and action accents

[Sheet 09](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/Sheets/sheet_09_waist_simulation_localization.png) plots recorded first-ring deviations across injected idle, walk, turn and stop. Duplicate versus single constraint authority reaches 12.542 versus 12.544 cm; Kawaii disabled reaches only 0.00002869 cm. Separate frame sampling limits this to localization evidence. Deduplication did not repair the waist. The next staged test anchors the existing first radial ring while preserving lower-chain dynamics; surface shape and root rotation still need evaluation. Actual layer-to-layer clearance remains unproven.

The staged locomotion BlendSpace now contains compatible idle/walk/run/sprint copies. The injected probe retained the intended boots and AnimBP at up to 220 cm/s, but moving boot minima span approximately −1.03 to +11.16 cm. The earlier successful idle cannot certify gait. Physical input, run/sprint, reset, reload and production admission remain open.

[Sheet 10](/C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaLegSkirt_20261023/Sheets/sheet_10_water_sparkle_beat_plan.png) turns the Fontaine direction into a proposed cue sequence: gathering droplets, crisp release glint/arc, actual-contact crown/ripple, softer follow-through and quiet recovery. Existing combat events own release and contact; authored markers own decorative pose accents. One authority per cue avoids duplicate spawns. Jev may select an approved variant before the boundary; it does not determine hit timing.

Source inspection identifies two concrete integration gaps: the existing form-beat player does not consume its declared timing offset or parameter maps, and resolved-hit effects use the target actor location rather than a verified contact point/normal. These are planned integration work after waist/layer acceptance. Reference links, access limitations and current execution state remain in CURRENT_STATE.md; no HoYoverse private implementation or exact frame timing is claimed.

## 11. Shirt hem and shared-chain preservation

Sheet 11 uses the current exported shirt, not an assumed outfit generation. Of 861 source points, 278 carry more than 1% kilt influence and 167 more than 1% thigh influence. Exact closest-triangle distances were independently spot-checked against all skirt triangles. At 167 horizontal radial intersections, the shirt remains outside the skirt in bind, with minimum 0.2393 cm radial clearance. This does not certify a deforming open garment. Preserve those shared chains and test the saved waist-root candidate in House P0 before widening the shirt or stripping skin weights.

The source intake also exposes a wrapper-name difference: the shirt FBX uses an unweighted SK_Melusina_Skeleton wrapper where the older body export uses root. The other 464 joint names agree, with maximum position difference 0.0001713 cm. No alias rename or reimport was performed. A reusable Doctor intake must surface this distinction and gate full hierarchy/bind compatibility before export.

The current tooling is native KineFX FBX Character Import plus measured audit helpers. The existing Animation Doctor Python report and Melodia_KineFX desktop are reusable project infrastructure; the Studio shelf button is an artifact lookup, not proof that a custom HDA has been recovered. Extending a universal studio starts from the owner's recovered Doctor and existing universal-rig contract. Unreal retains runtime Wardrobe, animation and physics ownership.

## 12. C++ water triggers versus attached hair effects

| Path | Verified evidence | Still unproven in P0 |
|---|---|---|
| WaterHairFluid / NinjaLiveCore | Present and active in the recorded pawn snapshot | Effective inputs, changing sim output and intended droplet |
| VFX_HairFlow child renderer | Present/active; exposes NinjaVelocityDensityBuffer texture DI | Effective texture binding and visible consumption |
| Six socket globule components | Separate NS_Melusina_Globules components present/active | Their motion and overlap with beat accents; they are not the fluid sim |
| C++ WaterChorus | Source defaults off; explicit toggle gates setup/tick/beat dispatch | Current instance enabled state, loaded DLL, live bound surfaces |
| C++ beat/burst/splash accents | Eight null-world spawn calls corrected to guarded owner context | Compilation, successful spawned components, timing and rendered output |
| Direct combat/form effects | Existing component-context spawn path | Event captures; form offsets/parameter maps remain unwired |

The native UE implementation resolves a world from the spawn context and creates nothing when that world is absent. The chorus previously supplied nullptr at all eight accent spawn sites, while dispatch counts could still advance. The source repair supplies the existing owner and preserves the separate fluid splash stamp. No new sim, timeline or renderer was introduced. The material pass retained editor control: this fix has not been compiled, hot-reloaded or verified in P0. Snapshot and current-source hashes are pinned in cpp_vs_attached_waterfx.json. Attached active flags and historical C++ logs are not pixel-output proof.
