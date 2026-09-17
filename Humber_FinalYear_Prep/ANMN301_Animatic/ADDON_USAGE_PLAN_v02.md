# Addon Usage Plan — Shorewake Animatic v02 (Blender 5.2.1, school-only, no UE)

Inventoried 2026-09-17 from the live 5.2 user addon shelf. Rule of the task:
Blender-only. Anything that exports, bridges, or phones home to UE stays OFF.

## LIVE-SESSION FINDINGS (2026-09-17 evening, verified in the running session)

**Enabled and already earning:** surreal_arch GN kit (584 builders — the
MEL_star_finial star crown now crowns the MK38 masthead; skiff rib/joint/plate
builders), Sanctus decals (56 ops), nijigp, LightPainter, Beavel, MustardSimplify,
ornament_generator, melodia_* personal kit (melodia_studio batch_render/render_proof).

**Installed but NOT enabled** (folder present, zero registered ops until enabled
in Preferences): MESHmachine 0.16, MACHIN3tools 1.10.1, SimpleBake 2.3.2,
CURVEmachine 1.4.1. Enable on demand — none needed so far.

**Dead in 5.2:** physical-starlight-atmosphere 1.9.2 throws on register
(enable attempt failed). Night sky must be hand-built nodes or another route;
do not plan around it.

**Crash lesson (19:20):** the GUI died in the UI panel-draw thread right after
hardops / kushiro_tools / cloth_next / pro_particles were installed mid-session.
Live-only edits (dedupe, rib flip, balljoints, finial) were lost with the process
and rebuilt headless into v06. Rules: restart Blender after any mid-session addon
install; structural edits persist to disk (headless roll scripts), never live-only;
the open session is for looking.

## USE — enable for this animatic

### 1. VSEQF-master (VSE Quick Functions) — the fades + titles tool
Why: the beat board allows exactly 3 fades (shots 06/13/17 boundaries) and the
title/end slugs are still black. VSEQF gives one-key fades and VSE transform
helpers without leaving the Video Editing workspace.
Steps: enable > open SHOREWAKE_VSE_animatic_v02.blend > Video Editing workspace
  > select cut point at each (*) boundary > VSEQF fade (video only, NO audio —
  the cut is silent, adding an audio strip breaks the brief) > add Text strips
  "SHOREWAKE CALLING / your name" over 00_Title and end mark over 18_End.
Pitfall: VSEQF defaults can add audio fades — verify the strip stack stays
  video-only before export (ffprobe must show 1 video stream, 0 audio).

### 2. nijigp (NijiGP) + Grease Pencil Essentials library — the acting layer
Why: Lane A from the Nikki chart. GP accents over the 17 proxy renders are how
a 3D-proxy animatic reads as authored: motion lines on the push-off (14), ripple
rings on 07-08, glow scribbles on bells 09-10, held-pose smears on the doubt (11).
Library is synced (OneDrive + repo-local Assets/GreasePencil, inventory JSON in
Saved/Audit). Name objects GP_<shot>_<pass>_v01.
Pitfall: draw over RENDERED PNGs in a 2D/GP scene, never inside the 3D proxy
  scene — keeps the stage blend clean and the VSE timing untouched.

### 3. animaide + Animation Layers + AnimationRetimer — pose refinement
Why: v02 holds 17 keyed poses (frames 10-170) on 8 FK bones. These three refine
without destroying: Layers for non-destructive elbow/hand passes (review flagged
rigid FK arms reaching for the lyre), animaide for easing between the keyed
acting beats, Retimer ONLY if a shot's hold needs lengthening — and if you
retime, the VSE strip + MP4 must be rebuilt to match (timing is one chain:
pose keys > VSE > MP4).
Pitfall: never retime without rebuilding the cut. Never touch thigh/leg keys —
  the sit is load-bearing for every shot.

## HOLD — installed, not for the animatic

### 4. flip_fluids_addon — HOLD (Ocean modifier instead)
One hero splash close-up at most, and only in the capstone look pass. Flip bakes
gigabytes for a sim that fights the toon look; the proxy water is a shaded plane
and the wake reads through emission, not fluid. Ocean modifier (built-in, verified
res 7 in 5.2) is the upgrade path if a shot needs real waves.

### 5. Cascadeur (C:/Program Files/Cascadeur/) — HOLD until capstone weeks 6-8
Canonical Melusina motion authority per repo docs, 30 FPS export contract. Adds
nothing to 17 held storyboard stills. Revisit for real motion cleanup.

### 6. Rokoko + rokoko-studio-live — HOLD (mocap, capstone motion)
### 7. surreal_arch / surreal_greybox / surreal_world / archipack_20 — OPTIONAL
Set-dressing reserve only: if the mooring needs architecture beyond bench + hull
+ post. Do not redress the approved proxy before panels are submitted — new
geometry invalidates rendered panels.

## SUPPORT — enable as needed for prop/model fixes

MACHIN3tools / MESHmachine / ZenUV / quad_remesher / Mesh Cleaner / speedsculpt:
lyre-proxy refinement (torus + neck are storyboard-grade; round them if a close-up
demands it), skirt density watch (24k polys, densest mesh — fine for stills x17).

## NEVER for this task

- send2ue / Blender-Unreal-Export-Addon / BlenderTools-20231109043947: UE bridge.
  The task is school Blender-only. Enabling risks writing into the game tree.
- LiquiFeel: ZOMBIE BUG — hangs background/headless Blender (proven twice today:
  plain --background runs never return; --factory-startup required). Keep DISABLED
  everywhere; if a scene needs it, render that scene from the GUI only.
- melodia_stage / melodia_showroom / melodia_fx_audit_panel and the rest of the
  personal melodia_* kit: game-pipeline helpers, out of scope for school work.
- blender_mcp_addon: agent bridge, leave exactly as it is.

## Order of work

1. VSEQF: 3 fades + title/end text in the VSE blend (this session's next step).
2. nijigp/GP: accent passes per shot over panel renders.
3. animaide/Layers: elbow/hand refinement on 06-12 (lyre acting).
4. Rebuild MP4 only after 1-3 settle — one encode, frame-exact, silent.
