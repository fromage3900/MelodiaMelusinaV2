# Melusina Benchmark Take — 2026-09-08

**Purpose:** First canonical performance-capture take. One continuous shot that stress-tests the full OBSBOT → Cascadeur → UE pipeline before any production quantity.

**Status:** Spec. No assets yet — run this take to prove the lane.

---

## 1. The Sequence (one unbroken take)

Perform in order, no cuts. ~90–120s total including holds.

| # | Beat | What to do | Hold |
|---|------|------------|------|
| 1 | **Neutral** | T-pose 1s → relaxed A-pose / standing neutral, feet planted, hands visible, breathe 3s. Establishes rest pose + scale. | 3–5s |
| 2 | **Reach / Grasp** | Reach to instrument rest (left/right as staged), grasp, lift to playing position. Clean silhouette, no occlusion. | 2s at grasp |
| 3 | **48-Bar Phrase** | Play one full 48-bar Melusina phrase at tempo. Real musical timing — this is the rhythm anchor. | continuous |
| 4 | **Weight Shift / Turn** | Half-step weight shift + 90–180° turn toward imaginary sound/cue. Feet must slide/plant visibly, weight commits. | 2s post-turn |
| 5 | **Flourish** | Expressive flourish / release gesture — arms overhead or wide arc, fingers open, chest open. Tests max extension. | 1–2s peak |
| 6 | **Return** | Re-seat or lower instrument, return to neutral (same as #1). Breathe, settle. Proves loopability. | 3s |

**Direction:** Act it, don't mime it. Keep full body in frame the entire time. No dress, no prop occlusion — body intent only.

---

## 2. What This One Take Tests

| System | Failure this exposes |
|--------|----------------------|
| **Feet / Contacts** | Sliding, floating, penetration. One weight shift + turn forces Cascadeur contact rebuild. |
| **Hands** | Finger splay, grasp pose, instrument-hold plausibility. 48-bar phrase keeps hands active. |
| **Depth (monocular)** | Reach forward/back + turn. Single-camera depth is the known Alpha weak point — this is the detector. |
| **Shoulder Arcs** | Flourish + playing phrase. Reveals IK pops, clamped arcs, collapsed chest. |
| **Rhythm Timing** | 48 bars at tempo. Keep vs. rebuild — timing and phrasing must survive cleanup. |
| **Dress-Aware Posing** | Perform as-if-dressed (wider knee clearance, no crotch-clipping strides) but capture without the dress. Dress solves downstream. |
| **Retargeting** | End-to-end skeleton fit: OBSBOT H.264 → Cascadeur AutoPosing → UE `SK_Melusina_Skeleton`. Catches bone-name / scale breaks (see `Docs/CASCADEUR_MELUSINA_PIPELINE_2026-08-07.md`). |

**Pass criteria:** Feet stick without manual pin on every step, hands read at 1080p60, depth reads without Z-jitter, flourish arc is smooth, phrase stays on beat after Cascadeur polish, and `AS_Melusina_48Bar` plays on `SK_Melusina` with no T-pose collapse.

---

## 3. Capture Spec

- **Camera:** OBSBOT Meet 2 4K — **MOCAP preset only.** 1080p60, PTZ/auto-framing OFF, zoom 1× fixed, manual/stable focus, fixed exposure + WB, locked tripod at chest height. Full body always in frame, 3×3m clear area, plain contrasting background, floor contact markers, two broad lights at ~45°.
- **Format:** Clean H.264 MP4. 1080p60 > 4K30 for this test — temporal resolution matters more than spatial.
- **Duration:** Single uncut file. No edits before Cascadeur.

---

## 4. Naming / Export Convention

One take, three artifacts. Names stay linked:

```
Capture:   Melusina_Take01_48Bar_1080p60_20260908.mp4
Cascadeur: Melusina_48Bar.casc          (scene, same root name — no Take#)
UE Anim:   AS_Melusina_48Bar            (Animation Sequence, /Game/Melodia/Characters/Melusina/Animations/Cascadeur/)
```

**Rules:**
- Increment `Take##` only on the MP4. Cascadeur scene and UE asset drop the Take# — they represent the *move*, not the attempt.
- Date suffix only on the MP4 (`YYYYMMDD`). Cascadeur/UE assets are dateless.
- Cascadeur scene → UE via **Cascadeur Live Link** (2026.1+) or FBX fallback to `Imports/Animations/Cascadeur/Inbox/CAS_Melusina_48Bar.fbx` (30 FPS, baked, animation-only — per Cascadeur pipeline doc).
- UE import must target `SK_Melusina_Skeleton` directly (Lane A). If `updated_melusina_rig_noclothes` scale/names drift, use retarget fallback — don't force a broken import.

**Folder contract:**
- Raw MP4: `Raw/Capture/Melusina/2026-09-08/`
- Cascadeur: `Cascadeur/Melusina_48Bar.casc`
- UE: `/Game/Melodia/Characters/Melusina/Animations/Cascadeur/AS_Melusina_48Bar`

---

## 5. Do It

1. Set MOCAP preset, verify locked frame.
2. Perform beats 1→6 uncut. Clap or audible downbeat at start for sync if needed.
3. Ingest MP4 to Cascadeur Video Mocap (AutoPosing) → repair feet/depth/hands → AutoPhysics/pass → Live Link preview in `L_Melusina_MocapStudio`.
4. Export/bake `AS_Melusina_48Bar`. Verify in PIE, not just viewport.
5. Log result here or in next handoff — note which row in §2 failed.

**Not in scope for this take:** Cloth, hair, final dress sim, facial. Body intent → skeletal animation only.
