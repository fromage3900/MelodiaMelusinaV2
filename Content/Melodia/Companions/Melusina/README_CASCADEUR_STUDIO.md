# Melusina Cascadeur Studio — Placeholder

**UE path:** `Content/Melodia/Companions/Melusina/`
**Live Link map:** `Content/Melodia/Levels/Mocap/L_Melusina_MocapStudio` (see `Docs/Handoffs/MELUSINA_CASCADEUR_LIVELINK_STUDIO_2026-09-08.md`)
**Skeletons:** `SK_Melusina` / `SK_Melusina_Skeleton` · **ABP:** `ABP_Melusina_Current` · **IK:** `IK_Melusina`

## What lives here

- Canonical Cascadeur scene (`Melusina_BodyCapture_2026.casc`) — **AutoPosing** rig bound once to `SK_Melusina` and reused for every take.
- Captured `AnimSequences` → `Animations/Capture/` as `AS_Melusina_<Action>_<Take>_<Date>`.

## Boundary

**Body capture is skeletal only.** Cascadeur Video Mocap (H.264 MP4 → AutoPosing → key pose repair → contacts → AutoPhysics → polish) produces body intent. **Cloth, hair (Groom), and secondary motion are separate downstream passes** in UE (Control Rig / Chaos Cloth / physics) — do not bake the dress into the mocap.

## Pipeline

`OBSBOT Meet 2 4K 1080p60 (locked)` → `H.264 MP4` → `Cascadeur 2026.2 Video Mocap Alpha` → `Live Link (root/skeleton/sequence choice)` → `L_Melusina_MocapStudio` → `Sequencer/Take Recorder` → `AnimSequence`

Live Link requires Cascadeur **2026.1+ / 2026.2**, UE **5.5–5.8**, **Windows**, paid tier (Indie/Pro/Teams).

## Status

Placeholder — map and `.casc` scene to be committed. Keep this README as the in-content pointer to the handoff doc.
