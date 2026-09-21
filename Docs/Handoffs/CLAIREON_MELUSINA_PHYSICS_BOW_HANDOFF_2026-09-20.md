# Claireon handoff — Melusina skirt, hair, bow, and V2 battle presentation

**Date:** 2026-09-20
**Authority:** `CURRENT_STATE.md` plus `Docs/P0_TASK_LEDGER.json`
**Scope:** Unreal gameplay and portfolio-render readiness only. Do not absorb the concurrent Niagara, PPV, MPC, Oceanology, Sea Above, Choral Sheep, or Humber lanes.

## Outcome landed

- The live player and the battle-presentation Blueprint use `SK_Melusina_V2_Body`; legacy `SK_Melusina` is no longer the intended presentation body.
- The player and battle wardrobe now select `/Game/Melodia/Characters/Melusina/Outfits/V2/Polish_20260920/SK_Melusina_V2_Skirt_R2_SmoothChains` for the skirt slot.
- The accepted R2 mesh preserves the original bounds and bone order. Blender audit moved the skirt from 10.9295% rigid vertices to 0.39%, and mean kilt influences from 2.583433 to 4.593782. All four original skirt material slots were restored.
- `ABP_Melusina_Current` contains the bounded skirt Kawaii pass: damping `.30`, stiffness `.18`, world damping location `.80`, rotation `.85`, limit angle `38`, gravity `-120`, one subdivision, constraint iterations `1/1`, warm-up `20`, wind `.25`.
- `ABP_Melusina_WaterHair` contains the accepted safe tune: damping `.18`, stiffness `.08`, world damping `.50/.50`, limit angle `60`, one subdivision, warm-up `20`, wind `.20`.
- `/Game/Melodia/Characters/Melusina/Animations/Polish_20260919/AM_Melusina_BowAttack_Bound` is bound to the presentation Blueprint and plays successfully in PIE. Its source sequence is `A_Melusina_BowAttackV2_A_RangeAttack`, 1.3 seconds / 39 frames, with the attack notify at approximately 0.5004 seconds.
- `UMelodiaWardrobeComponent` now supports generic actor presentations and prefers `MelusinaPresentationMesh` / `CharacterMesh0`, allowing the battle presenter to receive the same V2 wardrobe ownership as the player.

## Runtime receipts

### Clean skirt and hair motion

`Saved/Screenshots/MelusinaPolish_20260920/SkirtR2_HairTune_R3`

- `pie_smoke_10_145903`
- 16 frames, 14 valid after warm-up.
- Deterministic launch fired successfully.
- Expected `ABP_Melusina_Current` matched.
- Zero Blueprint runtime errors, assertions, or ensures.
- Skirt shows independent panel response instead of the original rigid single-bell motion.

### Superseded capture — do not use as presenter proof

`Saved/Screenshots/MelusinaPolish_20260920/Portfolio_Bow_V2_Clean`

- `pie_smoke_13_150250`
- 16 frames, 14 valid after warm-up.
- Retained Python audit at `Saved/MCP/PythonAuditLog/scripts/2026-09-20_082539_001.py` shows this run selected the normal player `Character`, configured its SpringArm, and played `AM_Melusina_BowAttack_Gameplay`.
- It did **not** prove the spawned battle presenter, and it did **not** play `AM_Melusina_BowAttack_Bound`.
- Zero Blueprint runtime errors, assertions, or ensures.
- The images are cow/architecture-obstructed and visually unusable. Treat the old presenter wording as retracted.

### Corrected V2 presenter and bound-montage runtime proof

`Saved/Screenshots/MelusinaPolish_20260920/Portfolio_V2_Bound_Framed_R2`

- `pie_smoke_2_204615`
- Spawned `/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation.BP_MelusinaSwordsman_Presentation_C` as `BP_MelusinaSwordsman_Presentation_C_0`.
- The same live run logged `SK_Melusina_V2_Body`, `AM_Melusina_BowAttack_Bound`, and a successful montage-play result.
- 13 frames captured, 9 valid after warm-up; zero Blueprint runtime errors, `Accessed None`, assertions, or ensures.
- **Runtime gate only:** the reused player camera was buried in foreground geometry. These frames are not portfolio deliverables.

### Rejected framing attempts after the corrected runtime proof

- R1 used the stale map path and is invalid.
- R3 still inherited foreground companion geometry.
- R4–R7 exercised unsupported or unavailable Unreal Python calls; their stage scripts failed and they are invalid.
- R8 proved a dedicated `CameraActor_0` view target and clean bound-montage runtime, but framed empty sky.
- R9 failed while attempting to read an unavailable component `bounds` property.
- R10 and R11 completed clean runtime gates but still framed empty sky. R11 additionally proved the queried `head` and `pelvis` socket locations collapsed to the actor origin at capture time, so they cannot currently drive framing.
- Rejected directories are `Portfolio_V2_Bound_Framed_R1` through `R11`. Do not select stills from them for the portfolio.
- No accepted hero-framed bow shot or stitched clip was produced in this continuation.

### Build

Closed-editor command:

```text
C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat BS_GodFileEditor Win64 Development -Project=C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject -WaitMutex -FromMsBuild
```

Result: **Succeeded**, 8/8 actions, 40.79 seconds. The editor was deliberately left closed after the build.

## Known limitations — do not overclaim

1. Hair is parameter-improved, not re-rigged. Its skeleton is 73 independent two-bone strand chains under `hair_root`, leaving only one simulated joint per strand. True flowing hair requires a new multi-segment hair rig and redistributed weights.
2. The R2 skirt currently carries its imported companion skeleton and physics asset. Leader-pose runtime passed because the bone order matches, but a later production consolidation should reimport the corrected weights against the canonical Melusina skeleton or explicitly bless the duplicate skeleton.
3. The stock `/Game/TurnBasedJRPGTemplate/Maps/BattleMap` emits unrelated template errors and does not naturally spawn this presenter. Do not use that map as a clean proof environment until its battle bootstrap is repaired.
4. Bow montage playback is proved, but grip, string, arrow timing, and a hero-framed front/three-quarter render remain open.
5. The rejected R1 skirt candidate was a 100x-scale import and must never be selected. Use R2 only.
6. Every tested `Melusina_Harp_HERO01*.blend/.blend1` file in the redirected `C:/EnvironmentPortfolio/harp_bow_pipeline` fails Blender 5.2 with `Missing DNA block`. All 16 share the failure. Preserve them for recovery; do not overwrite them. The Unreal retargeted bow assets remain intact.
7. Kawaii emits `inter-bone dummy bones` warnings five times during the corrected capture. No runtime failure accompanied them, but they are a performance/topology warning and must remain disclosed.
8. Jev was not live in the continuation. `scenario_bow_capture.py` returned `source="classical-fallback"`; this process and the persistent user/machine environment did not expose `TYPESAFE_API_KEY`, and no callable Jev connector was available. Do not relabel fallback output as Jev evidence.

## Claireon execution plan

### P0 — first clean editor session

1. Launch exactly one Unreal Editor with Monolith on `127.0.0.1:9316`.
2. Confirm these saved bindings before mutation:
   - player body: `SK_Melusina_V2_Body`
   - player skirt slot: `SK_Melusina_V2_Skirt_R2_SmoothChains`
   - battle presentation body: `SK_Melusina_V2_Body`
   - battle skirt slot: `SK_Melusina_V2_Skirt_R2_SmoothChains`
   - battle montage: `AM_Melusina_BowAttack_Bound`
3. Run one short deterministic locomotion/jump clip. Reject any startup pop, persistent oscillation, leg penetration, or missing outline material.
4. Do not retune the hair unless the same repeatable capture shows a regression. Its current ceiling is topology, not another damping number.

### P1 — portfolio render tonight

1. Use `L_MelusinaMorning`, not the noisy template `BattleMap`.
2. Use a deliberately placed editor camera or a small purpose-built capture level/sequence whose subject is visibly confirmed before recording. The transient runtime camera experiments R8–R11 resolved as view targets but failed to locate the visible modular presentation meshes.
3. Capture three short beats:
   - neutral three-quarter idle with readable skirt silhouette;
   - lateral step or small jump showing skirt panel lag and hair response;
   - full bow anticipation, draw, release, follow-through, and recovery.
4. Record live component identity and montage playback in the same run. A beautiful frame without identity evidence is not acceptance.
5. Select 3–5 final PNGs plus one short stitched clip. Avoid the existing cow/architecture-obstructed player-camera composition.
6. Do not claim completion until the V2 face/body, R2 skirt, hair, and bow are visibly present in the same front/three-quarter frames. Runtime log identity alone is insufficient.

### P2 — production hardening after renders

1. Consolidate R2 weights onto the canonical skirt asset/skeleton with a reversible backup and repeat the same PIE gate.
2. Recover or rebuild the hair source into multi-segment chains; then retune Kawaii from the current R3 values instead of starting over.
3. Recover the harp/bow Blender source from an independent backup, autosave, source-control object store, or disk-recovery image. Never save over the damaged files.
4. Repair the real battle bootstrap so `BP_MelusinaSwordsman_Presentation` spawns through gameplay rather than a proof harness, then repeat the bow capture in the true encounter flow.

## Ownership and safety

- One editor/Monolith writer only.
- Do not save unrelated dirty assets.
- Do not touch the active Morning Niagara rewire, frozen PPV, MPCs, `DefaultEngine.ini`, Choral Sheep, Oceanology, Sea Above external actors, or Humber assets from this handoff.
- The accepted proof tier is PIE plus a closed-editor build. Packaged proof is still open.
- Route accept/reject and next-action judgments through Jev when the TypeSafe credential is available; do not treat Jev as an Unreal mutation agent.

## Exact continuation point

Commit `b1146a3e7` is the scoped implementation baseline. The next operator should **not** retune physics, re-author in Cascadeur, or repeat the rejected transient-camera loop. Open `L_MelusinaMorning`, place the existing presentation Blueprint and a real camera where both are visible in the editor viewport, verify the modular V2/R2 components visually, then run `AM_Melusina_BowAttack_Bound` and capture the three beats above. If Jev is required, first run one bounded wrapper evaluation and require `source="jev-live"`; stop immediately if it says `classical-fallback`.
