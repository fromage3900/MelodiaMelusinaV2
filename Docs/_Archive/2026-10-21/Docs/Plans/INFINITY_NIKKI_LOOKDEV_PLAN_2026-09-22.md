# Infinity Nikki Lookdev Plan — Melusina & Melodia (2026-09-22)

North star: the project's visual/wardrobe bar is **Infinity Nikki** — soft painterly toon,
clean readable silhouettes, layered cloth with visible physics, and wardrobe-as-fantasy.
This plan is the staged route from the current canon (V2 body + R2 skirt + WaterHair,
toon masters tracked, 5 measured Rokoko clips staged) to portfolio renders that read at
that bar. Every step names its owner lane and its proof.

Status authority: `CURRENT_STATE.md`. Evidence for animation claims:
`Docs/Handoffs/ROKOKO_MELUSINA_ANIM_EVIDENCE_2026-09-22.md`.

## Where we are (verified 2026-09-22)

- **Toon material spine is canon**: `M_Master_Toon_Character` / `M_Master_Toon_Universal`
  tracked; marketplace reconvert done (Megascans 237/237, Brushify 98/13/0). Custom_MS is
  not the target. (CURRENT_STATE §Nikki-derived toon path.)
- **Melusina presentation canon**: V2 body + R2 skirt + tuned WaterHair; capture level
  `/Game/Melodia/Characters/Melusina/Portfolio/L_MelusinaPortfolioCapture`; V13 +
  WaveHarpTransform_V3 LIVE PIE PROVEN (19/20 frames, 0 runtime errors).
- **Eyelash/iris polish in flight (2026-09-22 ~01:10, NOT all saved)**: `MI_Melusina_Eyelash`
  saved; iris twinkle + ORM MIs saved; `Staging_Lash_Pair` spawned in the capture level but
  the **level was NOT saved before editor exit** — respawn/re-verify on reopen
  (bounds: eye midpoint (-0.43, 31.4, 155.2), scale 6). Iris discs `bHidden=True`, scale 0.01.
- **Animation**: 5 Rokoko clips imported with measured root-motion speeds (WalkElegant
  54 cm/s, GlideForward 217 cm/s, BowKneelAim 55 cm/s, BowDraw v1/v2 in place). ABP main
  chain healthy; Glide state still plays the LittleDance placeholder; Hybrid blendspace has
  duplicate samples; a presentation actor (`BP_MelusinaSwordsman_Presentation`) T-poses in
  PIE (anim class unconfirmed).

## Lookdev lanes (staged, isolated)

### L1 — Face & eye finish (owner lane, resume first)
1. Reopen editor → re-verify `Staging_Lash_Pair` in capture level (respawn at the recorded
   bounds if lost); save the level with owner Ctrl+S.
2. Socket lash to `head_x`; iris discs: unhide decision + scale 1.0; blink-drive proof.
3. Proof: one `HighResShot` close-up + `Saved/Audit/` receipt; no graph edits outside
   the lash/iris staging.

### L2 — Animation lookdev (Kimi lane, this pipeline)
1. Bind `A_Melusina_GlideForward_Mocap_RootMotion…Action` into the `Glide` state via
   `bind_and_verify.py --state Glide --clip <path>`; set `rate_scale =
   controller_glide_speed / 217` so the measured take matches movement (no foot slide).
2. Confirm/fix `BP_MelusinaSwordsman_Presentation` anim class (the runtime T-pose).
3. Clean `BS_Melusina_Locomotion_Hybrid` duplicate samples; leave
   `BS_Melusina_Locomotion` axes untouched (in-place clips have no measurable speed).
4. Bow set (BowDraw v1/v2, BowKneelAim 55 cm/s) → terminal-action/presentation staging;
   capture 3-point turnaround on the portfolio map.
5. Junk cleanup after owner OK: 65 `*_clip_Base_Layer` strays in `Animations/Mocap/`.

### L3 — Portfolio render pass (Claireon lane, needs owner go per task)
1. Beauty capture on `L_MelusinaPortfolioCapture` with L2's glide + bow clips bound.
2. Post: PPV storybook-outline premium candidate (untracked at
   `Content/EnvSandbox/Materials/PostProcess/Candidates/`) — A/B one plate before any
   level-wide switch.
3. Every render proof = live PIE `HighResShot` + audit JSON; asset previews
   (`capture_scene_preview`/`capture_anim_frames`) are not evidence.

### L4 — Wardrobe silhouette pass (future, after L1–L3 land)
Infinity Nikki reads through outfit layering: use the existing Wardrobe hooks (owned
`UMelodiaWardrobeSubsystem`) to stage one full alternate look (shirt slot already present
on the capture rig) and one cloth-physics moment (R2 skirt + Kawaii) per render set.
No fifth wardrobe track; no parallel implementations.

### L5 — Cascadeur integration (owner installed; research done 2026-09-19)
43 inbox manifests are legacy Quaternius/UAL1 Lane-B; `SC_Melusina_Golden.casc`
unauthored; `character_rig_RokokoLive` absent from the v23 grandmaster — rebuild before
the next suit session. Cascadeur role: physics-polish pass on top of Rokoko takes
(second-pass contact/weight), exported back through the same guarded FBX lane.

## Rules that survive this plan

- One editor instance; Monolith 9316 is the only MCP surface; Jev never mutates the editor.
- Live PIE `HighResShot` + `Saved/Audit/` JSON is the only render/pose evidence class.
- Recipe 15 (fingerprint → mutate → compile → assert → save) on every graph edit;
  compile NEVER between CDO set and save.
- No `git clean`/`checkout -- .`; commits use exact pathspecs; handoff content lands in
  the commit/PR message as well as the doc.
- Do not reopen the damaged Missing-DNA Blender sources; v23 grandmaster is zstd-healthy.
