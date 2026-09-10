# OBSBOT Meet2 4K — Melodia body mocap lane

**Status:** READY (unparked 2026-09-09 after harp grip gate pass)
**Not for:** finger wrap, harp/prop contact, facial micro (authored ARP / Faceit).
**For:** full-body idles, chapter gestures, sheep-react beats.

## Capture
1. Meet2 4K, locked framing, full body in frame, 30 fps (60 optional), plain backdrop.
2. Session folder: `capture/meet2/YYYY-MM-DD_sessionNN/raw/`
3. Name: `YYYYMMDD_sNN_T##_slug.mp4` — one intention per take; clap + A-pose slate.

## Solve → UE (canonical Melusina mocap lane)
Meet2 outputs **video**. Bridge must produce FBX whose bones match **`SK_MocapSource`**
(Rokoko CharacterRef profile from that skeleton — see `Docs/ROKOKO_MELUSINA_MOCAP.md` if present).

4. Drop FBX in `Imports/Mocap/Meet2/Inbox/` (or Rokoko Inbox if using that exporter).
5. Import like Rokoko takes → `A_Src_Meet2_*` under `/Game/Melodia/Mocap/Source/Anims` (or Meet2 quarantine source).
6. Retarget with **`RTG_Mocap_to_Melusina_Current`** / `IK_Melusina_Body_Current` (19 chains, `root_x` pelvis).
   Headless helper exists: `Tools/run_headless_mocap_retarget.ps1` (editor CLOSED).
7. Output quarantine: `/Game/Melodia/Mocap/Meet2/` (do not scatter into FemaleBard* folders).
8. Visual gate: thumbnail + viewport on **`SK_Melusina_V2_Body`** — never `capture_anim_frames` alone.
9. Only then consider ABP wiring; keep V10 cute idle as fallback.

## Hard rules
- Fingers/props stay hand-keyed.
- One clip → one quarantined asset until approved.
- Do not call `set_retargeter_rigs` to repoint live retargeters.
