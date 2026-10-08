# Sir Melodious — Unreal import handoff (New Bot lane), 2026-10-03

Any agent can pick this up. Rules: owner Ctrl+S only (never Monolith save_packages / recompile_material); no scripted skeletal MESH import (AGENTS.md, past crashes); ping the room before driving the editor; commits go to `lane/sir-melodious-flight` (PR #413) only after owner save.

**2026-10-08 update:** mesh file is now `SKM_SirMelodious_ARP_CrestTie_v5_tailfix.fbx` (tail weight fix: 657 zero-weight verts -> 0, hython-verified — see CURRENT_STATE.md 2026-10-08); clips = v6; guarded importer = `Content/Python/import_sir_anim_guarded_v4.py` (auto-discovers the ARP skeleton, save OFF per §2).

## 0. State before import
- On disk + PR #413: old SK_SirMelodious_Rigged (128 bones, no crest/tie), A_Sir_*_v3 (v3.3), ABP_SirMelodious (collar Kawaii on c_kilt_master_x), BS1D_Sir_FlightSpeed_v3. Leave these untouched.
- Source of truth for new mesh/clips: `exports/ue_arp/` — use the LATEST version Study posts (v5 or newer after the feather respacing). ARP exporter only; never import a Blender-FBX export.

## 1. Mesh (OWNER drags by hand)
File `exports/ue_arp/SKM_SirMelodious_ARP_CrestTie_v5_tailfix.fbx` (v5 mesh + tail weight fix: 657 zero-weight verts -> 0, verified; plain `SKM_..._v5.fbx` stays the pre-fix archive) -> `/Game/Melodia/Characters/SirMelodious/ARP/`
- Folder `/Game/Melodia/Characters/SirMelodious/ARP/` already exists (created in-editor 2026-10-08).
- Skeleton: none (Create New Skeleton) — ARP bone names differ (root `root.x`, collar `c_kilt_*`, crest `cc_crest_*`, tie `cc_tie_*`).
- Import Morph Targets: ON (`Crest_Raise`, later `Wing_Smear_L/R`).
- Vertex Color Import Option: Replace (R feather-tip/wingtip gradient, G crest mask, B cavity) if the mask bake pass landed.
- Nanite: ON.
- Then post "in" in the room.

## 2. Clips (scripted, guarded)
- `Content/Python/import_sir_anim_guarded_v4.py` (v3 guards; auto-discovers the new ARP skeleton in the ARP folder), run in-memory with save disabled (task.save=False, no save_loaded_asset), files `A_Sir_{Fly_Loop,Hover_Idle,Glide,Takeoff,Land}_v6_ARP.fbx`.
- Check after: Force Root Lock off, translation retargeting Animation, 22/22 feathers moving, frame counts match Study's contract.
- Re-add `Downstroke` sync markers (Fly every 0.5 s, Hover every 1/3 s) if the FBX doesn't carry them.
- Add float curves from `Wingbeat_curves_v*.json` (24 fps, peak on downstroke): `Wingbeat`, and `Wing_Smear_L` / `Wing_Smear_R` if present (same name as morph = morph auto-driven).

## 3. ABP + blend space
- Duplicate ABP_SirMelodious -> ABP_SirMelodious_ARP and BS1D_Sir_FlightSpeed_v3 -> BS1D_Sir_FlightSpeed_ARP; retarget both to the new skeleton (old assets stay for PR #413).
- Blend space: Speed 0-800, Hover 0 / Fly 450 / Glide 800; Takeoff/Land states on the new clips.
- AnimGraph: StateMachine -> LocalToComponent -> KP_Collar -> KP_Tie -> KP_Crest -> ComponentToLocal -> Output.

## 4. Kawaii (values in `kawaii/KAWAII_SPEC_20261003.md`)
- KP_Collar root `c_kilt_master*`: Damping 0.3, Stiffness 0.4, WDL 0.8, WDR 0.7, Radius 0.5, LimitAngle 20, Gravity Z -400.
- KP_Tie root = knot bone `cc_tie_01*`: Damping 0.15, Stiffness 0.05, WDL 0.65, WDR 0.5, Radius 0.4, LimitAngle 55, gravity x0.6, sphere limits spine_02 + neck.
- KP_Crest `cc_crest_01..04`: Damping 0.25, Stiffness 0.35, WDL 0.8, WDR 0.7, LimitAngle 25, gravity x0.25; small external force scaled by `Wingbeat` curve.
- Colliders/Physics Asset: build from Study's collider spec when it lands (capsules body/head/wings).

## 5. Beat (runtime, NOT baked)
- Crest glow + `Crest_Raise` morph from the game's live BeatPulse (same source as sheep), warm white on beat, gold #C9A86A on Perfect only.

## 6. Sockets on new skeleton
- `wingtip_L`, `wingtip_R` (flight trail Niagara), `crest_tip` (beat glow).

## 7. Done =
Compiles BS_UP_TO_DATE, PIE flight test with collar/tie/crest moving, no clipping; post proof; owner Ctrl+S; 💧 commits to PR #413.

## 8. Later mesh (PLAN.md section 13: front coverts + tail fan)
- Tonight's mesh = v5. Clips: v5 (front/side camera) or v6 (behind-camera feather fan); same v5 mesh either way.
- When the section 13 mesh lands: feather fan goes into the rest pose; tail `cc_tail_01..05` has NO baked motion. Add `KP_Tail` (root `cc_tail_01`), start from Damping 0.2, Stiffness 0.15, WDL 0.7, WDR 0.6, LimitAngle 35, gravity x0.5; tune in PIE. Re-run steps 1-7 on the new mesh (re-import onto the same ARP skeleton if bone list only gains tail bones).
