# Melusina Cascadeur / Performance Capture Pipeline

**Status:** CANONICAL DURABLE ANIMATION AUTHORING CONTRACT  
**Current task / proof state:** `CURRENT_STATE.md`

This document defines the stable Melusina animation path from authored or captured performance through Cascadeur into Unreal. It does **not** maintain a current clip queue, setup checklist, or claim about what is presently live-proven.

## 1. Authority

Cascadeur is the primary authoring/editing environment for new Melusina skeletal animation.

Two lanes are allowed:

### Lane A — canonical skeleton authoring

Animate / clean up against the real Melusina deform skeleton and preserve its ARP/deform naming and export contract. Prefer this when the source already targets Melusina correctly.

### Lane B — explicit retarget

Use retargeting only for generic motion libraries, video-mocap drafts, or another source skeleton. Retargeting must end on the canonical Melusina Unreal skeleton; it may not redefine that skeleton.

Historical source/retarget findings belong in provenance docs, Git history, or the task/PR context rather than this current contract.

## 2. Canonical export contract

- animation only unless a specific diagnostic explicitly needs mesh;
- **30 FPS** for Unreal-target animation exports;
- bake required deform joints;
- preserve canonical ARP/deform bone names;
- root motion disabled for locomotion clips unless explicitly requested;
- preserve required canonical bones including `DEF_eye_L`, `DEF_eye_R`, `c_kilt_master_x`, `head_x`, and `root`;
- one animation clip per FBX;
- never silently change the live Unreal skeleton to accommodate a source clip.

## 3. Folder / naming contract

Unreal-target exports land in:

```text
Imports/Animations/Cascadeur/Inbox/
```

Preferred naming:

```text
CAS_Melusina_<Action>_<Variant>.fbx
```

Examples:

- `CAS_Melusina_Idle_Serene.fbx`
- `CAS_Melusina_Land_Soft.fbx`
- `CAS_Melusina_Victory_Twirl.fbx`
- `CAS_Melusina_Glide_Start.fbx`

## 4. Offline gate

Before opening Unreal, scan the export with:

```text
blender --background --python Tools/scan_cascadeur_fbx.py -- input.fbx report.json
```

For direct Lane A import, the report must confirm the expected frame rate, armature, and required canonical bones. If it fails, repair/export or explicitly choose Lane B; do not force the importer through a skeleton mismatch.

## 5. Unreal import

Inside Unreal:

```python
import import_cascadeur_anim as cascadeur
print(cascadeur.import_inbox())
```

Canonical targets:

- Mesh: `/Game/Melodia/Characters/Melusina/SK_Melusina`
- Skeleton: `/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton`
- Destination: `/Game/Melodia/Characters/Melusina/Animations/Cascadeur`

Lane A imports directly to the canonical skeleton. Lane B uses an explicitly verified retarget path.

## 6. Performance-capture source — OBSBOT Meet 2

The OBSBOT Meet 2 is an optional **performance source**, not animation authority.

Recommended body-capture preset:

```text
1920x1080
60 fps
Auto Framing OFF
fixed crop / fixed camera
stable exposure and white balance where practical
whole body + feet visible
clean MP4 capture
```

Use 4K30 or reframing only when the goal is acting/reference detail rather than body-pose reconstruction.

A capture session should favor:

- stable camera position;
- readable limb silhouette against the background;
- broad even lighting;
- enough floor area for safe footwork;
- floor marks for neutral/action bounds;
- body intent first, secondary cloth/hair later.

## 7. Video mocap -> Cascadeur

Video mocap is an editable draft generator, not final animation.

```text
owner performance
  -> fixed-camera MP4
  -> Cascadeur Mocap draft
  -> AutoPosing / manual cleanup / physics tools
  -> canonical Melusina target
  -> Live Link or FBX export
  -> UE evaluation
  -> final polish
```

Expect to repair depth, foot contacts, root/center of mass, hands, silhouette, arcs, weight, and momentum.

Do not attempt to encode final skirt/hair physics into the body capture.

## 8. Cascadeur Live Link -> UE5.8

Live Link is an evaluation/iteration path. It does not change skeleton ownership.

A valid proof requires actual observation that:

1. Cascadeur appears as a Live Link source/subject in UE;
2. the intended Melusina skeleton receives the stream or a verified retarget maps it;
3. root orientation/rotations are sane;
4. a simple edited motion updates correctly in UE;
5. no axis/bone mismatch blocks evaluation;
6. a capture proves the connection.

Do not call the lane live-proven from configuration alone.

A minimal mocap/evaluation map may exist for this purpose, but it must remain an animation studio/test surface rather than becoming a gameplay level.

## 9. Animation quality / pizzazz

Authoring may add breathing, weight shifts, glances, stylized landings, glides, victory flourishes, conducting/casting gestures, creature interaction, conversational body language, and other performance detail.

Secondary systems remain downstream:

```text
body intent
  -> Cascadeur cleanup
  -> UE skeletal evaluation
  -> manual / Control Rig correction where needed
  -> cloth / hair / secondary motion
  -> final game validation
```

Cosmetic animation/VFX must not delay damage, turns, battle results, traversal truth, or save transitions.

## 10. Existing tools to reuse

Reuse existing infrastructure before building another importer or scanner:

- `Tools/Cascadeur/Melusina/`
- `Tools/import_takes_to_cascadeur.py`
- `Tools/run_cascadeur_import.ps1`
- `Tools/run_cascadeur_retarget_pipeline.py`
- `Tools/scan_cascadeur_fbx.py`
- `Content/Python/import_cascadeur_anim.py`
- `Content/Python/import_cascadeur_animation.py`
- `specs/anim_presets/cascadeur_melusina_animation_contract.json`
- `Tools/t3d_anim_injector.py` for approved Blend Space / AnimBP wiring paths.

Do not create a second animation-import framework unless a concrete deficiency is proven.

## 11. Evidence language

Use accurate evidence labels:

```text
SOURCE / CAPTURE PREPARED
  -> CAPTURE-PROVEN
  -> RETARGET / ANIMATION-PROVEN
  -> LIVE-LINK-PROVEN (when applicable)
  -> IN-GAME-PROVEN
  -> PACKAGED-PROVEN
```

Current evidence level and the next required animation belong in `CURRENT_STATE.md`, not this contract.

## 12. Non-goals

Do not:

- replace the canonical Melusina skeleton;
- rebuild the existing import stack without a demonstrated blocker;
- treat raw video mocap as final animation;
- claim Live Link proof without an actual stream capture;
- bake dress/hair physics into the body capture;
- make performance-capture infrastructure a prerequisite for unrelated capstone work;
- create a dated animation handoff/task-plan document instead of updating `CURRENT_STATE.md` or this durable contract.
