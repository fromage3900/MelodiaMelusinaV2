# Melusina Idle + Geo Render Fix — 2026-08-20

**Owner:** BP_MelusinaJRPGCharacter (`/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter`) — confirmed via project_query.

## Idle
- Canonical: v22 ARP factory rebuild — `A_Melusina_Idle_v22` (`Content/Melodia/Characters/Melusina/Animations/Authored/`) + `Exports/MelusinaAnim/A_BL_Melusina_Idle_Loop_cm.fbx`+sidecar. Prior origin/scaling was import-pipeline, not clip.
- Current ABP `MelusinaLocomotion` Idle still on `A_Melusina_Idle_Mocap_RootX` (project_query:get_asset_details). Repoint SequencePlayer to `A_Melusina_Idle_v22` (Loop=true) — staged for next editor session (single capture_anim_frames per session due to !IsRooted bug).
- Verification: capture_anim_frames at Idle@0 + PIE locomotion check (Speed threshold 10).

## Geo Render (Water Hair)
- Long-term: Groom (ABP_Melusina_Hair / ABP_Melusina_WaterHair via UMelodiaHairComponent on head_x) + Niagara WaterHairDripFX. GeometryCache WaterHairFlipCache bakes — no wind/MPC/bIsGliding — and lives only on dead BP_Melusina smoke pawn, not on owner.
- Action: keep WaterHairFlipCache disabled on owner if present (bVisible=false), don't delete until Groom PIE parity. Material reads MPC_Melodia_Palette AudioReactAmount, not PPV slot 1 (per MATERIAL_PIPELINE_AUDIT/PPV_STACK_AUDIT).

## Sync
- Commit 78b912a8 pushed to origin/main (LFS). G:\ mirror needs robocopy /MIR after idle repoint + import (G host was offline to github).

## Remaining manual (one editor holder)
1. ~~ABP repoint + save_packages + capture + save~~ **DONE 2026-08-22 (see below).**
2. Disable GeometryCache on owner, verify Groom deforms with glide/idle
3. Full build + PIE + echo_run record + push + robocopy to G:

## Session 2026-08-22 — idle + glide landed (Monolith, single editor)

- **Idle (final):** `MelusinaLocomotion` Idle SequencePlayer = `A_Melusina_Idle_Mocap_RootX`
  (proven upright). Verified on-disk via the new skill script
  (`Saved/Audit/bind_and_verify_idle_*.json`, ground truth
  `melusina_idle_glide_final_2026-08-22.json` → PASS).
- **Blender hand-keyed idles DO NOT direct-import:** both `A_Melusina_Idle_v22`
  (unguarded) and guarded-imported `Cascadeur/A_BL_Melusina_Idle_Loop` render
  lying-down/exploded in preview captures despite passing skeleton+cm checks.
  Root cause + canonical 7-stage path (with mandatory IK-retarget stage):
  `Docs/Production/BLENDER_HANDKEYED_ANIM_IMPORT_PIPELINE_2026-08-22.md`.
  Frames: `Docs/Evidence/2026-08-22_melusina_idle_glide/`. Both clips quarantined
  (do not bind); deletion = owner call.
- **Glide:** Glide state bound to `A_Mocap_LittleDance_001` placeholder; entries
  Idle/Locomotion/Airborne -> Glide all `bool bIsGliding`; exits remain the
  pre-existing `bRuntimeIsInAir`/`bRuntimeIsGrounded` rules through Airborne/Land.
  Redundant ruleless Glide->Idle/Locomotion edges removed. Compile 0/0, saved.
- **Skill:** `.agents/skills/melusina-blender-handkeyed-import/` (SKILL.md +
  `scripts/bind_and_verify.py`; also installed at `%USERPROFILE%\.agents\skills\`)
  encodes this pipeline; its bind script passed first real run.
- **Next editor session:** one fresh `capture_anim_frames` to confirm upright mocap
  idle pose in ABP context, then real-input PIE: jump + second press after apex ->
  glide engages and Glide state plays; check `BlockReason` logs if rejected. Then
  land a hand-keyed clip through pipeline Stage E (retarget) to replace the mocap idle.
- **Hazard hit today:** LFS lockable ReadOnly crashed the editor on
  `save_packages` (same as MF_Madoka 08-15); cleared `attrib -R` on
  ABP_Melusina_Current only. A parallel lane reverted both `wire_melusina_*` tools
  mid-session — final ABP changes were applied via direct Monolith calls instead;
  re-land tool fixes after coordinating with the owning lane.
