# Melusina Performance Capture Studio — OBSBOT Meet 2 → Cascadeur 2026 → UE5.8

**Status:** RESEARCHED SEMESTER ANIMATION PIPELINE — SETUP / VALIDATION REQUIRED  
**Date:** 2026-09-08  
**Owner lane:** Animation / performance authoring  
**Canonical repo:** `fromage3900/MelodiaMelusinaV2`

This document extends the existing Cascadeur Melusina pipeline. It does **not** replace the current skeleton/export contract in `Docs/CASCADEUR_MELUSINA_PIPELINE_2026-08-07.md`.

## 1. Goal

Create a small repeatable performance-capture studio for Melusina where the owner can act motions quickly, turn those performances into editable animation drafts in Cascadeur 2026, and preview the result on Melusina in Unreal Engine 5.8 through Live Link.

The intended creative loop is:

```text
perform
  → OBSBOT Meet 2 clean fixed-camera capture
  → MP4 reference
  → Cascadeur Mocap (Alpha)
  → AutoPosing / key-pose / contact / physics cleanup
  → Cascadeur Live Link
  → UE5.8 Melusina preview
  → final animation polish / export
```

This is a **performance-sketching and animation-authoring pipeline**, not a claim of optical-stage-quality mocap.

## 2. Research-verified capability boundary

### Cascadeur 2026

Verified against current Cascadeur documentation on 2026-09-08:

- current documentation identifies **Cascadeur 2026.2** as the recent release;
- Mocap remains explicitly **Alpha**;
- Mocap accepts reference images/video and currently supports **.mp4** video input;
- Mocap currently captures **one performer**;
- it requires an **AutoPosing rig** on the target character;
- single-camera depth estimation is a documented limitation;
- Cascadeur recommends a clearly visible performer, clothing/silhouette distinct from the background, and a performer close enough to camera;
- Cascadeur Live Link is available in Cascadeur **2026.1+**;
- the current Live Link plugin supports **Unreal Engine 5.5–5.8**;
- the new Cascadeur Live Link plugin is Windows-only and is a paid feature on Indie / Pro / Teams.

Therefore:

- use video mocap as an editable first pass;
- expect to repair depth, feet, contacts, arcs, hands and weight;
- keep Unreal as the live evaluation surface rather than treating raw mocap output as final animation.

### Unreal Engine 5.8

Epic's UE5.8 documentation confirms Live Link is the engine's supported interface for streaming animation data from external DCC tools or mocap systems.

For skeletal animation, Epic recommends the **Live Link Skeletal Animation Component** over the generic Live Link Controller for animation use.

Live Link Pose in an Animation Blueprint remains available where retargeting/blending is required.

### OBSBOT Meet 2

OBSBOT's current official product listing identifies the Meet 2 as:

- an AI-powered fixed 4K webcam;
- up to **4K @ 30 fps**;
- up to **1080p @ 60 fps**;
- AI Auto Framing.

For Cascadeur capture, the pipeline recommendation is:

- **1080p60** as the normal full-body performance capture mode;
- **4K30** as an optional slower acting/reference/detail mode;
- disable Auto Framing for the mocap source so the effective crop stays stable.

The 1080p60 choice is a Melodia workflow recommendation based on available camera modes and the value of temporal sampling for body motion. It is not a claim that Cascadeur mandates 60 fps.

## 3. Camera setup

### Capture preset — mocap source

```text
OBSBOT Meet 2
resolution: 1920×1080
frame rate: 60 fps
auto framing: OFF
digital zoom/crop: fixed
camera position: fixed
exposure: stable/manual where practical
white balance: stable/manual where practical
focus: stable; confirm full-body sharpness
recording: clean H.264/MP4-compatible capture
```

Do not dynamically reframe during the take.

The camera is fixed, so no PTZ-motion compensation is required.

### Reference preset — optional

Use 4K30 or Auto Framing only for non-mocap reference work where the goal is acting/detail review rather than pose reconstruction.

Examples:

- facial/upper-body acting reference;
- hand/instrument closeups;
- rehearsal;
- wardrobe/cloth reference.

## 4. Physical studio

Target a simple, repeatable capture corner rather than a complex stage.

Preferred conditions:

- enough floor area for full-body action and safe footwork;
- camera on a stable tripod or fixed mount rather than relying on a monitor position;
- camera height roughly around torso/chest range unless a shot requires otherwise;
- whole body remains in frame, including feet;
- broad, even lighting;
- performer silhouette clearly separated from background;
- floor marks for neutral position and action bounds;
- no moving camera/crop during the mocap take.

Clothing for the base solve should preserve readable limbs and joints.

Do **not** attempt to encode final Melusina skirt/hair physics in the capture. Capture body intent first; add secondary motion downstream.

## 5. First benchmark performance

Use one benchmark that exposes most failure modes:

```text
NEUTRAL
→ reach / instrument pickup
→ 4–8 bar performance phrase
→ weight transfer
→ turn
→ expressive flourish
→ settle / return to neutral
```

This tests:

- foot contacts;
- hip/root translation;
- shoulder arcs;
- hand/arm timing;
- turns and single-camera depth;
- rhythm timing;
- settle behavior;
- ability to preview the result on Melusina in UE.

Do not begin with acrobatics.

## 6. Cascadeur processing lane

1. Record a clean Meet 2 take.
2. Save an archival source take outside Unreal content.
3. Import the selected `.mp4` as Cascadeur reference video.
4. Confirm Melusina's Cascadeur target scene has a valid AutoPosing rig.
5. Run Mocap only on the required frame interval.
6. Treat generated poses as a draft.
7. Repair:
   - depth;
   - feet and floor contacts;
   - root/center of mass;
   - hands;
   - silhouette;
   - arcs;
   - weight and momentum.
8. Use AutoPosing, physics tools and manual editing as appropriate.
9. Preserve the existing Melusina skeleton/export contract.
10. Preview continuously in UE through Live Link once the connection is validated.

The owner remains the animation author. Mocap is source material, not final authority.

## 7. Unreal Live Link studio

Create one small dedicated evaluation map, proposed name:

`L_Melusina_MocapStudio`

Keep it intentionally minimal:

- Melusina skeletal mesh / animation preview actor;
- neutral floor;
- clean silhouette lighting;
- CineCamera;
- Live Link subject;
- Live Link Skeletal Animation Component;
- retarget path only if required by the actual source/target skeleton relationship;
- Sequencer or animation recording path for proof.

Do not turn this map into a gameplay level.

### First Live Link gate

Pass only when all of the following are actually observed:

1. Cascadeur appears as a Live Link source/subject in UE.
2. The correct Melusina skeleton receives the stream.
3. Rotations and root orientation are sane.
4. A simple arm raise / weight shift updates in UE while edited in Cascadeur.
5. No axis flip or obvious bone-name mismatch blocks evaluation.
6. A short capture or screenshot proves the live connection.

Until then, status is **SOURCE-PLANNED / SETUP REQUIRED**, not LIVE-PROVEN.

## 8. Existing Melodia animation infrastructure to reuse

Current repo already contains:

- `Docs/CASCADEUR_MELUSINA_PIPELINE_2026-08-07.md`;
- `Tools/Cascadeur/Melusina/`;
- `Tools/import_takes_to_cascadeur.py`;
- `Tools/run_cascadeur_import.ps1`;
- `Tools/run_cascadeur_retarget_pipeline.py`;
- `Tools/scan_cascadeur_fbx.py`;
- `Content/Python/import_cascadeur_anim.py`;
- `Content/Python/import_cascadeur_animation.py`;
- `specs/anim_presets/cascadeur_melusina_animation_contract.json`;
- existing Cascadeur and mocap animation assets under `Content/Melodia/Characters/Melusina/Animations/`.

Do not build another importer unless the existing tools are concretely insufficient.

## 9. Skeleton / export safety

The older Cascadeur pipeline records a real staging mismatch between a historical `updated_melusina_rig_noclothes.fbx` and the live UE contract.

That warning remains in force.

Live Link setup must not silently redefine:

- Melusina's canonical Unreal skeleton;
- ARP/deform bone names;
- export frame-rate contract;
- root-motion policy.

If Live Link requires mapping or retargeting, document the mapping and keep the game skeleton authoritative.

## 10. Semester animation usage

Once the studio passes its first live gate, use it for rapid performance ideation such as:

- idle breathing / weight shifts;
- turning toward sound;
- instrument pickup / putdown;
- melodic conducting gestures;
- casting / rhythm phrases;
- nervous or quiet hand acting;
- kneeling / reaching;
- creature interaction;
- conversational body language;
- traversal starts/stops;
- stylized flourishes.

Pipeline:

```text
body intent
→ Cascadeur cleanup
→ UE preview
→ final skeletal animation
→ Control Rig / manual correction if needed
→ cloth / hair / secondary motion
→ final game validation
```

## 11. Explicit non-goals

Do not:

- buy another camera before testing the Meet 2;
- treat Auto Framing as part of mocap capture;
- claim the video solve is real-time live mocap;
- claim Cascadeur Mocap is production-final;
- replace the Melusina skeleton;
- bake dress/hair physics into the body capture;
- rebuild the existing animation import stack;
- make this a prerequisite for the immediate Choral Sheep capstone proof.

This is a **semester animation workflow lane**, not today's owner P0.

## 12. Evidence ladder

Use the project evidence language:

```text
RESEARCHED / SOURCE-PLANNED
→ CAPTURE-PROVEN
→ LIVE-LINK-PROVEN
→ ANIMATION-PROVEN
→ PACKAGED-PROVEN
```

Do not skip levels.

## 13. Official research sources

Verified 2026-09-08:

1. Cascadeur — Introduction / current release documentation  
   https://cascadeur.com/help/introduction
2. Cascadeur — Mocap (Alpha)  
   https://cascadeur.com/help/category/203
3. Cascadeur — FAQ / Mocap limitations and capture recommendations  
   https://cascadeur.com/help/faq
4. Cascadeur — Live Link for Unreal Engine  
   https://cascadeur.com/help/category/268
5. Epic Games — Live Link in Unreal Engine 5.8  
   https://dev.epicgames.com/documentation/en-us/unreal-engine/live-link-in-unreal-engine
6. Epic Games — Skeletal Mesh Animation System / Live Link entry point  
   https://dev.epicgames.com/documentation/en-us/unreal-engine/skeletal-mesh-animation-system-in-unreal-engine
7. OBSBOT — official current product catalogue, Meet 2 capability summary  
   https://www.obsbot.com/

## 14. Next setup session

The first implementation session should stop after this proof:

```text
Meet 2 1080p60 fixed capture
→ one simple performance MP4
→ Cascadeur Mocap draft
→ manual cleanup of a few poses
→ Live Link into Melusina in UE5.8
→ one saved proof capture
```

After that succeeds, the studio is operational and further work should be animation creation, not infrastructure expansion.
