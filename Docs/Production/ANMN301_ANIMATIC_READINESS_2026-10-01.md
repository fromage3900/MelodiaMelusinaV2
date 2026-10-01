# ANMN301 animatic — submission readiness, 2026-10-01

**Verdict: NOT submittable as-is. The container is exact; the character is not.**

Deadline: **Friday 2026-10-09, 5:00 PM EDT**. Eight days at time of writing.
Submission is a resumable Blackboard test with multiple attempts — submit early
versions freely.

Every number below came from a run on this tree, Blender 5.2.1 LTS
(hash 9e2066aef7ef) headless unless stated. Prose is not a row.

---

## 1. What passes

`ffprobe` on `ShepherdBrennan_AnimaticCreation_2026-10-09_v04.mp4`:

```
codec_name=h264  width=1920  height=1080
r_frame_rate=24/1  nb_frames=1560  duration=65.000000  size=24469415
audio streams: (none)
```

Brief requirement was MP4 / 1920x1080 / 24 fps / silent. **All pass.**
65.000 s is exactly 1560 frames at 24 fps.

Filename matches the required `lastNameFirstName_assignmentName_dueDate`.

Title card verified by reading the rendered panel: **SHOREWAKE CALLING** /
**ANMN 301 — Animatic Story Edit** / **Brennan Shepherd**. All three elements
present.

`panels_final/` holds 19 PNGs — `panel_01`..`panel_17`, `title`, `end`.
`SHOREWAKE_VSE_animatic_v04.blend` contains **zero scene objects** and a
SequenceEditor with **19 strips**, declared coverage 1560, measured coverage
1560, overlap 36. The timeline is correct.

## 2. What fails

Panels 11, 12, 16 and 17 — the acting beats — do not read as a performance:

| Panel | What renders |
|---|---|
| 11 | a white arm and hand only; no head, no body |
| 12 | arm and shoulder; head and legs occluded |
| 16 | figure with arms straight out, head cropped by the frame edge |
| 17 | same, plus untextured white surface |

In an animatic whose purpose is to show story and acting, four panels where the
protagonist is invisible or in a reference pose will read as "the character was
never animated."

## 3. Root cause — measured, and it is NOT the pose dict

### 3a. A real bug, found and fixed

`animatic_fix.py`'s `REDO` table posed panels 16 and 17 with **`c_head_x`**:

```python
"16": pose={"c_head_x": (0, -0.35, 0)}, glide_x=-2.4,
"17": pose={"c_head_x": (0, -0.35, 0)},
```

Probing all 464 bones in `MelusinaRig`: there is **no `c_head_x`**. The
neck/head controls are `c_neck_x`, `c_neck_master_x`, `c_subneck_1_x`, `neck_x`.
`apply_pose()` logged nothing for a missing bone, so both panels rendered with
the head in rest — **silently, with exit code 0**.

Neither panel posed an arm either. Fixed in the working tree: both now pose
`c_neck_x`, `c_spine_02_x` / `c_spine_03_x`, `c_arm_fk_*`, `c_forearm_fk_*`,
`c_hand_fk_*`. All 9 referenced controls were verified present before running.

### 3b. The deeper cause — posing the rig does not move the character

Re-rendering after that fix produced **still** a reference-pose figure. Probes:

```
# rotate c_arm_fk_l / c_arm_fk_r by 1.4 rad on Z, measure EXPORT_Body
ARM2 rest  mean [1.25777, -0.50001, 1.84909]  xspan 1.0059..1.4710  n=18891
ARM2 posed mean [1.25777, -0.50001, 1.84909]  xspan 1.0059..1.4710  n=18891
ARM2 VERDICT BONES_DO_NOTHING

ARM2 c_arm_fk_l rotation_euler = [0.0, 0.0, 1.4]
ARM2 c_arm_fk_l matrix row0    = [0.9895, 0.1419, 0.0278, 17.4402]
ARM2 modifier preserve_volume=False show_viewport=True show_render=True
```

The **bone matrix does rotate**. `EXPORT_Body` does not move a single vertex.

The skin is not at fault:

```
VG EXPORT_Body   vgroups=164  verts=18891  groups matching bone names 164/164
VG   verts with weight>0 across all groups: 55852
VG   groups with ZERO weighted verts: 0 / 164
VG EXPORT_Shirt  40/40   2670 weighted   0 empty
VG EXPORT_Skirt  73/73  62871 weighted   0 empty
VG EXPORT_Boots  12/12   8619 weighted   0 empty
```

And the geometry is **not shaped like the figure in the panels**:
`EXPORT_Body` xspan **0.46** against zspan **2.0**. A reference-posed human is
roughly as wide as tall. This mesh is a narrow slab.

### 3c. Where the character comes from

`proxy/SHOREWAKE_proxy_v30_perch.blend` — the stage — contains **212 objects,
zero armatures, no `EXPORT_*` meshes**. It is entirely skiff:

```
STAGE mesh Hull_Shell  verts=532  dims=[7.63, 1.39, 1.02]  parent=Starskiff_MK38
STAGE camera CAM_Wide  loc=[6.5, -6.5, 3.2]
STAGE camera CAM_Intimate loc=[1.8, -2.6, 1.7]
STAGE camera CAM_SkiffClose loc=[3.0, -1.6, 1.1]
```

The character exists only because `animatic_fix.py` appends it at runtime. That
run reports:

```
ANIMFIX appended 17 objects from v02
ANIMFIX linked 17/17 appended objects into the scene
ANIMFIX   parented EXPORT_Shirt -> MelusinaRig
ANIMFIX   parented EXPORT_Skirt -> MelusinaRig
ANIMFIX   parented EXPORT_Boots -> MelusinaRig
ANIMFIX scale: hull_len=3.763 char_h=2.074 -> MESH scale=0.819617
ANIMFIX post-scale EVALUATED height = 2.031 (target 1.70)
ANIMFIX link check OK: [...]
```

`EXPORT_Body` is absent from the `parented` log — consistent with it arriving
already parented, and with it being the only one of the four carrying an
Armature modifier in the source.

**Open question for the next session:** why does the appended, correctly-bound
`EXPORT_Body` evaluate without deforming? Candidates, none yet excluded:
the source `.blend`'s rig is in a pose-library/edit mode the append does not
carry; the modifier's object reference resolves to a *different* armature
instance after append; or the panels are not showing `EXPORT_Body` at all.

## 4. Fastest way to settle it

Open the live Blender (**PID 18036, MCP on 127.0.0.1:9876**), load
`proxy/SHOREWAKE_proxy_v02_storyboard.blend`, select `EXPORT_Body`, and look.
Ten seconds of viewport answers what four headless probes did not:

- Is it a real Melusina body, or a narrow slab?
- Does posing `c_arm_fk_l` move it?

If the body is fine in that file, the defect is in `animatic_fix.py`'s append or
its scale/seat step. If it is a slab there too, the source geometry is wrong and
the append is innocent.

## 5. Working-tree state

`animatic_fix.py` carries the 3a fix and is **uncommitted**. It is a strict
improvement — `c_head_x` never existed, so those panels can only render better
after it — but it does **not** fix the submission on its own, because 3b is
upstream of it.

Also uncommitted and regenerated this session: the six `proxy/panels_v4/*.png`
and the six matching `panels_final/*.png`.

**The committed MP4 and the working-tree MP4 differ.** `c0063d1c` captured the
19.6 MB file; the working tree holds the 24.5 MB one:

```
-oid sha256:2b368e0e...  size 20602133   (committed)
+oid sha256:2ac30dfd...  size 24469415   (on disk)
```

This is not pointer drift — it is a real rebuild that landed after the commit,
from a `build_vse.py` run in an earlier session. Both pass the spec in §1. **No
decision was made about which to keep; that is an owner call.**

## 6. Do not

- Do not re-aim cameras. Framing is a consequence of 3b, not the cause. The rig
  reports `FRAMING ... on_screen=True` and 47% frame overlap, so the character
  is on screen and adequately sized — it is the *geometry* that is wrong.
- Do not treat a clean exit code as evidence. `apply_pose()` skipped two
  nonexistent bones and the render still returned 0.
- Do not re-cut the VSE. The timeline is correct at 1560/1560.
- Do not sync the addon or re-cut the registry baseline until Blender is closed
  (see the main handoff).

## 7. Reproduction

```bash
cd "/p/MelodiaMelusinaV2-Laptop/Humber_FinalYear_Prep/ANMN301_Animatic"
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"

"$B" -b --factory-startup --python probe_vg.py            # skin binding census
"$B" -b --factory-startup --python probe_arm_moves2.py    # do bones move the mesh
"$B" -b --factory-startup --python probe_stage.py         # what the stage contains
"$B" -b --factory-startup --python probe_vse_contents.py  # strips + coverage
"$B" -b --factory-startup --python animatic_fix.py        # re-render panels 11,12,13,15,16,17
"$B" -b --factory-startup --python build_vse.py            # reassemble + render MP4
```

Probes are committed as-is so every number above can be re-derived.