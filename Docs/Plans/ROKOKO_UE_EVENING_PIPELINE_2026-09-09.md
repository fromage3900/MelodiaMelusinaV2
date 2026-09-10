> **MATERIALS GATE (2026-09-09):** UE restart / Live Link verify is **blocked** until Nikki landscape + Oceanology + SDF masters are merged to main with receipts under `Docs/Materials/`. See `Docs/Plans/MATERIALS_NIKKI_OCEAN_SDF_FINALIZATION_2026-09-09.md`.
# Rokoko to UE Melusina pipeline - evening plan (2026-09-09)

**Owner chat:** STudy my Melodia Melusina project?
**Pair bot:** New Bot
**Goal tonight:** Close a working Rokoko body mocap path into Unreal on SK_MocapSource then RTG_Mocap_to_Melusina_Current, with one approved take on Melusina.

## Hard rules
- Live preview / live drive: source / quarantine only. Never gameplay SK_Melusina / BP_Melusina until viewport approve.
- Blender hero harp grip on character_rig is locked. Live drive uses character_rig_RokokoLive only.
- Ship clips = FBX inbox to import to IK retarget, not live on production mesh.
- Blender Melodia mesh Live Link port 9876 is not Rokoko mocap (Rokoko receiver = 14043).
- One editor writer; no hand-edit .uasset; no Monolith save_packages.

## Already done (do not redo)
| Item | Status |
|------|--------|
| Epic LiveLink + LiveLinkHub + LiveLinkControlRig in .uproject | Done |
| Plugins/Smartsuit (Rokoko Studio Live 1.13.1 source) | Installed (UE 5.8 may compile on first load) |
| SK_MocapSource + skeleton under /Game/Melodia/Mocap/Source/ | Present |
| Imports/Mocap/Rokoko/Inbox/ + CharacterRef/ | Ready |
| Docs/ROKOKO_MELUSINA_MOCAP.md | Canonical |
| Blender addon on Rev02 session | Enabled |
| Receiver listening UDP 14043 | Running |
| Quarantine arm character_rig_RokokoLive + T-pose + 21/21 ARP FK map | Wired |
| Auto-attach first Studio actor to RokokoLive | Timer armed |
| Checkpoint ..._checkpoint_pre_rokoko_live_20260909_155712.blend | Saved |

## Lane split (tonight)

### Lane A - Melodia bot (Blender live + capture + docs)
1. Confirm Studio stream then auto-attach fires (marker harp_bow_pipeline/_evidence/ROKOKO_ACTOR_AUTOATTACH.json).
2. Smoke-drive character_rig_RokokoLive (idle sway / T-pose to A-pose). Fix bone map gaps if limbs twist.
3. Record short body take in addon (or Studio export) to FBX.
4. Drop FBX in Imports/Mocap/Rokoko/Inbox/ with verb name (IdleTest, WalkLoop, ...).
5. Keep harp hero untouched; evidence stills to Saved/SemesterEvidence/2026-W37/Mocap/.

### Lane B - New Bot (UE plugin bring-up + import/retarget)
1. Coordinate UE editor restart so LiveLink + Smartsuit load (expect Smartsuit compile if no binaries).
2. Verify Edit > Plugins: Live Link + Rokoko Studio Live / Smartsuit enabled.
3. Open Window > Virtual Production > Live Link; confirm Rokoko subject when Studio streams (optional live preview on SK_MocapSource / Newton, not Melusina).
4. Export CharacterRef: SK_MocapSource to Imports/Mocap/Rokoko/CharacterRef/SK_MocapSource.fbx for Studio character profile if missing.
5. When Inbox has a take: run import_rokoko_mocap (editor) to A_Src_Rokoko_* then RTG_Mocap_to_Melusina_Current to A_Mocap_Rokoko_*.
6. Viewport approve on Melusina body; leave ABP / levels alone unless owner says swap.

### Shared gate (both)
- One approved body clip on Melusina (Idle or Walk) with spine/neck acceptable.
- Receipt: Saved/SemesterEvidence/2026-W37/Mocap/ROKOKO_UE_FIRST_TAKE_RECEIPT_2026-09-09.md.
- If neck warps: stop library recording; note ARP neck rewire doc; do not mass-retarget yet.

## Suggested evening order (America/Toronto)
1. Now: Studio streaming + auto-attach confirm (Lane A); UE restart + plugin verify (Lane B) in parallel.
2. Live smoke: Blender RokokoLive moves; optional UE Live Link subject on SK_MocapSource.
3. First take: record/export FBX to Inbox.
4. Import + retarget: Lane B runs import/retarget; Lane A captures before/after stills.
5. Approve / receipt: owner eyeball; write receipt; park or queue Walk/Run samples.

## Scripts / paths
- Tools/setup_rokoko_livelink_plugins.ps1 (Epic plugins already enabled)
- Content/Python/import_rokoko_mocap.py
- Tools/run_headless_mocap_retarget.ps1
- Retargeter: RTG_Mocap_to_Melusina_Current / IK_Melusina_Body_Current
- Repo: fromage3900/MelodiaMelusinaV2
- Checkout: C:\EnvironmentPortfolio\BS_GodFile

## Out of scope tonight
- Shorewake Phase 1 pearl bridge / PearlWoven
- Meet2 capture session (kit ready; separate lane)
- Finger/prop harp contact via mocap
- Live drive onto production Melusina ABP

## Handoff checklist for New Bot
- [ ] UE restarted with Smartsuit + LiveLink green
- [ ] Live Link panel opens; note whether Rokoko subject appears
- [ ] CharacterRef FBX exists or explicitly blocked
- [ ] First Inbox FBX imported + retargeted
- [ ] Melusina viewport still or short note of issues (neck/shoulders)
- [ ] Ping Melodia bot with paths of A_Src_* / A_Mocap_* created

