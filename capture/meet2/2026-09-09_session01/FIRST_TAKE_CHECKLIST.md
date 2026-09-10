# Meet2 first take — checklist (2026-09-09 session01)

## Gear
- [ ] OBSBOT Meet2 4K plugged in / OBS sees it
- [ ] Tripod locked, camera ~ waist-to-head centered, **full body in frame** (headroom + feet)
- [ ] Plain backdrop, key light on face/torso, no blown windows behind you
- [ ] Record to: `capture/meet2/2026-09-09_session01/raw/`

## Meet2 / OBS settings (target)
- Resolution: **4K** if stable, else 1080p
- FPS: **30** (60 only if disk/CPU fine)
- Lens: fixed zoom for whole session (no auto-reframe mid-take if it crops feet)
- Disable aggressive tracking crop that cuts ankles/hands
- Audio: mic optional (slate verbally is enough)

## Per take
1. Start recording
2. **Slate 1s**: say take name + clap once in frame
3. Hold **T-pose or A-pose 1s** (helps solver)
4. Perform **one intention only** (see SHOTLIST.md)
5. End in a still 0.5s → stop
6. Rename file immediately:
   `20260909_s01_T##_slug.mp4`
   Example: `20260909_s01_T01_idle_sway.mp4`

## After session
- Fill `notes/takes_log.csv`
- Ping me — I’ll verify files in `capture/meet2/2026-09-09_session01/raw/`
- Solve path (next agent beat): video → FBX matching **SK_MocapSource** bone names → drop into `Imports/Mocap/Meet2/Inbox/` (or Rokoko Inbox if using Rokoko Vision CharacterRef export) → `import_rokoko_mocap`-style import → `RTG_Mocap_to_Melusina_Current` quarantine under `/Game/Melodia/Mocap/Meet2/`

## Hard rules
- Body only — no finger/prop acting for this lane
- Do not overwrite V10 idle / ABP until viewport approve on `SK_Melusina_V2_Body`
- Do not trust `capture_anim_frames` alone
