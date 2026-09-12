# Folding the retargeted suite into UE BlendSpaces — 2026-08-15

**Prereq:** the skin-topology fix (`Tools/fix_melusina_eye_weights.py` + the finger decision).
Nothing below is worth doing on clips that still tear the face apart.

**Scope:** how retargeted clips become playable locomotion. Not a retarget doc.

---

## 1. What the live BlendSpace actually is

`/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion_Hybrid` — read live:

- 1D, axis `GroundSpeed`, range **0–650**, 4 grid divisions, `interpolate_using_grid: false`
- **7 samples, but only 4 unique clips**

| x | clip | |
|---|---|---|
| 0 | Idle | |
| 150 | Walk | |
| 180 | Walk | ← same asset as 150 |
| 300 | Run | |
| 420 | Run | ← same asset as 300 |
| 540 | Sprint | |
| 630 | Sprint | ← same asset as 540 |

Duplicating one clip at two X values creates a **plateau**: nothing changes between 150 and 180,
then the whole visual change is crammed into 180→300. That is the "hybrid" — it is a workaround for
not knowing where the samples belong, not a design.

**The load-bearing defect.** Every sample reports:

```
root_motion_speed_known: false
"root motion disabled (root-locked) — authored speed is unknowable"
```

So all seven X positions are **guesses**. A BlendSpace axis is a contract: "this clip is what the
character looks like at N cm/s." If the clip's real ground speed isn't N, the feet slide — and no
amount of blend tuning fixes it, because the error is in the axis, not the blend.

Two smaller notes from the same read: Walk and Run have **identical duration** (1.1667 s), which is
worth a look — they may be one source clip retimed. And each locomotion clip already carries **2 sync
markers**, so foot-phase alignment infrastructure exists and does not need building.

---

## 2. The rule

> **A clip's X position is measured from the clip, never chosen by hand.**

Everything else follows from that.

---

## 3. Procedure, per clip

All of these are existing Monolith `animation_query` actions — nothing needs writing.

1. **Retarget with root motion preserved.** The current suite is root-locked
   (`in_place_root_locked_for_locomotion`), which is why speed is unknowable. Locomotion clips must
   keep root translation through the retarget; the AnimBP can still consume them in-place.
2. **Measure:** `get_root_motion_speed(anim_path)` → cm/s. *That number is the X position.*
   For a clip that must stay root-locked, `bake_distance_curve` gives the same information as a
   curve instead.
3. **Foot phase:** `derive_foot_sync_markers` — auto-derives left/right foot-plant markers from data
   already in the clip via its availability cascade. Existing clips have 2 markers; confirm the new
   ones match the same naming so they share a sync group.
4. **Place:** one sample per clip at its measured speed. `edit_blendspace_sample` to move an existing
   sample, `add_blendspace_sample` for new. **Delete the duplicates** — 7 samples collapse to 4 real
   ones plus whatever new coverage the retarget adds.
5. **Sync group:** `set_sync_group` on the BlendSpace player node so blends align on foot plants
   rather than on time. Without this, two clips at different cadences cross-fade mid-stride.
6. **Rebuild:** `bake_blend_space` to re-triangulate after moving samples. Skipping this leaves the
   asset's grid describing the old layout.
7. **Axis range:** set max to the fastest measured speed, not 650. Compare against the character's
   actual `MaxWalkSpeed` — `Tools/` records sprint at 714 uu/s, which is **above** the current 650
   axis max, so sprint currently clamps.

---

## 4. Where each band lands

The retargeted suite is wider than locomotion; not all of it belongs in a BlendSpace.

| Band | Clips | Destination |
|---|---|---|
| Locomotion | RunCycle, RunCycle_Sprint, Walk, Idle | `BS_Melusina_Locomotion_Hybrid`, measured X |
| Jump / air | Jump, Jump_001/002, LiftOff, GracefulLanding, Jump_Loop | **State machine states**, not a BlendSpace — they are one-shots with entry/exit conditions |
| Dodge | Dodge, Dodge_001 | Montage, root-motion-driven |
| Bard / performance | FairyWand, LittleDance(_001/_003), Twirl_001 | Montages on a dedicated slot |
| Combat | Stab, MercyStab | Montages, existing battle slot |
| Swim | **none valid** | Blocked — the only swim clips are the rejected Quaternius ones. Source gap, tracked separately |

Only the first row is BlendSpace work. Putting one-shots in a BlendSpace is the usual way these get
tangled.

---

## 5. Gates before promotion

The current live suite stays authority until all of these pass:

1. `get_blend_space_info` shows **no duplicate animation across samples**, and every sample's X
   equals its measured `get_root_motion_speed` within tolerance.
2. Axis max ≥ the character's real sprint speed (714 uu/s per the sprint gate), so nothing clamps.
3. Every sample clip carries foot sync markers under one shared sync group.
4. `Tools/test_melusina_skin_topology_contract.py` still reports **0 new** violations — the clips
   must not reintroduce orphan-bone dependence.
5. Eye-offset regression: `get_animated_bone_transform` on an eye bone composed against `head_x`
   holds constant across frames. This is the numeric form of "corneas stay in the skull" and is the
   check that was missing for three sessions.
6. Side-by-side PIE against the current V1 BlendSpace before swapping authority.

---

## 6. Sequencing

The retarget cannot be finished before the skin fix, and the BlendSpace cannot be finished before
the retarget preserves root motion. In order:

```
skin topology fix (eyes + finger decision)
  -> re-export + reimport V2 body/accessories
  -> retarget WITH root motion preserved
  -> measure speeds -> place samples -> sync group -> bake
  -> gates 1-6 -> swap authority
```

Sourcing external packs (Digital Kinetics / AAA Motion / Rokoko) is **step 3 work at the earliest**.
Buying before the skin fix reproduces the same tearing on more expensive clips.
