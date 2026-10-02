# ANMN 301 Shorewake Animatic — working scene handoff

**Deadline:** Fri Oct 9 2026, 5:00 PM EDT.

## Open these

```
P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic\
    SHOREWAKE_ANIMATIC_working_scene.blend            <- edit here
    SHOREWAKE_swap_test.blend                         <- the canonical-character scene
    ShepherdBrennan_AnimaticCreation_2026-10-09_v04.mp4   <- the cut, verified
    proof/                                            <- before/after renders
    CANONICAL_RIG_CONTROL_MAP.md                      <- how to pose the real rig
    CANONICAL_RIG_REVIEW_2026-10-01.md                <- why the first pass was grey
```

## State of the cut

```
ShepherdBrennan_AnimaticCreation_2026-10-09_v04.mp4    32.3 MB, 22:05
  1920x1080  PASS     24 fps  PASS     1560 frames  PASS
  65.000s    PASS     silent  PASS     h264         PASS
  19 strips, 3 gamma-cross fades (06/13/17), coverage 1560/1560, 0 gaps
```

All 17 panels were re-rendered against the canonical rig. The previous cut had
an untextured grey figure in six shots and an **empty deck** in seven others
(02, 04, 05, 06, 07, 08, 14) — `panels_v3` was built from a scene with zero
armatures, so those acting shots never had a character at all.

## The character is now real

```
character_rig   759 bones / 234 deform, dot notation (root.x, foot.l, toes_01.l)
Melusina        18,791 verts, 4 materials, 4096x4096 BaseColor + Normal
67 image textures, 66 node materials
```

Pose it from `CANONICAL_RIG_CONTROL_MAP.md`. The short version:

```
rotation   c_spine_01/02/03.x  c_neck.x  c_head.x  c_subneck_1.x
           c_shoulder.l/r (Z)  c_root_master.x
           +X on any of these = lean/bow FORWARD
translate  c_hand_ik.l/r   Z negative lowers the arm
           c_foot_ik.l/r   Y positive swings the foot forward
           c_root.x        Y positive lowers the body (seated)
```

Everything else is dead: every `c_p_*`, every `*_fk`, every `DEF-*`, and the
bare `spine_*.x` / `neck.x` / `root.x` bones. They are constraint-driven;
setting them moves nothing and raises no error.

The old `MelusinaRig` (464 bones, underscore names, `head_x` / `spine_02_x`) is
a **different rig** — an untextured FBX round-trip. Its pose table does not
transfer to `character_rig` and vice versa.

## Pipeline

```
render_all_panels.py   -> proxy/panels_v5/panel_NN.png   (17 panels, 1920x1080)
burn_cards.py          -> panels_final/                  (numbering + title/end)
build_vse.py           -> SHOREWAKE_VSE_animatic_v04.blend + the MP4
```

`render_all_panels.py` takes `ONLY_SHOTS=11,16` for a cheap subset and `TRIAL=1`
to write to `panels_v5_trial`, so a test can never overwrite good panels. It
asserts framing before every render and reports `fails=[...]`.

Camera distance is **derived from the lens and the subject's size**, never
hardcoded. The establishing shots frame the hull (`frame="boat"`) and fit both
its width and height — the hull is 7.68 long but only 1.21 tall, so fitting
height alone put the boat off both sides of the frame.

## Three traps worth remembering

**The VSE double-tonemapped the whole cut.** Blender 5.x defaults
`view_transform` to AgX. Each panel was rendered to PNG through that transform
(already tonemapped), and the VSE applied it *again* on the way to h264. The
submission was uniformly **16-19 levels darker** than the panels, max channel
delta 70. `build_vse.py` now sets `view_transform = 'Standard'` so final images
pass through untouched. Verified after the fix: brightness delta -0.8/-1.2/-0.4,
frame diff 43% -> 0.8% (the residue is h264 compression).

Any VSE cut built from already-rendered images needs this. If the panels are
ever re-rendered with a non-AgX transform, revisit it — the rule is that the
transform must be applied exactly once, in whichever stage produces the images.

**The vision model is unreliable for pose direction.** Asked "is the head bowed
or lifted?" it answered *backwards*, twice, on renders that were correct, and
the pose was nearly flipped on that say-so. Direction was settled by tracking
one vertex — the nose, by index — across `+0.5` and `-0.5`:

```
+0.50:  nose dz=-0.116 (down), back-of-skull dz=+0.098 (up)  -> BOW
-0.50:  nose dz=+0.119 (up)                                   -> LOOK UP
```

Track a single vertex index. Sampling "the frontmost 5% of head verts" as a set
cancels itself out, because which verts are frontmost changes as the head turns.
Same caution for contact sheets: at 384x216 thumbnails a seated figure vanishes
into the boat's pink-and-purple rigging and reads as "no character present".

**Textures are packed, and must stay packed.** All 67 image paths point at
`C:\Users\froma\...` and `G:\...` — a different user account and an unmounted
drive. **Every file is missing.** The character renders only because 53 of 67
images are packed into the blend. Never rely on those paths.

## Still open

- **Corneas.** `L_Cornea` / `R_Cornea` ship with `hide_render=True`. The render
  script flips them, but the flag is upstream in `FinalUERig43` — fix it there
  and it stops biting every future use of the rig.
- **14 unpackable images** (`bow_*`, `SHAWL_*`, `DPM2.004_BaseColor`,
  `Material.020_*`). Their source files are gone upstream. If the bow or shawl
  ever needs to read properly, those maps must be re-exported from the desktop.
- **Title card text** is still my default, not your copy. Strings at the top of
  `burn_cards.py`.
- **A second figure** appears in the crow's nest in some frames. Not
  investigated — worth a look if it is not meant to be there.
- **Nothing is committed.** The 32.3 MB MP4 supersedes the 19.6 MB one in
  `c0063d1c`. That push is your call.

## Session notes

Blender API traps from this work are in the `blender-5-2-api-traps` skill:
`media_type` gating FFMPEG, dissolve arithmetic, `libraries.load()` not linking
objects, `mesh.data.transform` vs `rig.scale`, control-vs-deform-vs-IK layers,
and verifying pose direction by vertex rather than by eye.