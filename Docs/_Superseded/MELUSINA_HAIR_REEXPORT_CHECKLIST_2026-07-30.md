# Melusina Hair — Blender Re-Export Checklist

**Date:** 2026-07-30
**Status:** hair still broken after re-export — `shared_bones=0`
**Goal:** get `shared_bones > 0` so `CopyPoseFromMesh` actually works and the 3ft/90° offset disappears

---

## What is actually wrong

Runtime evidence from PIE:

```
MELUSINA_HAIR_BOUND owner=BP_MelusinaJRPGCharacter_C_1 body=CharacterMesh0
  hair=WaterHairMesh anim=ABP_Melusina_WaterHair_C shared_bones=0 attach_bone=head_x
```

The hair AnimBP uses **`CopyPoseFromMesh`**, and that node copies pose **by bone name**. The two
skeletons share **zero** names, so the node copies **nothing** — the hair receives no body pose at
all. It then falls back to `AttachToComponent(..., SnapToTargetNotIncludingScale, "head_x")`, which
slams the hair component's origin onto the head bone. `HairExp_Rig`'s baked origin offset is the
3 feet you are seeing, and its axis convention is the 90°.

**This is not a UE bug and no corrective transform will fix it properly.** A hardcoded offset would
paper over it until the next re-export moved the delta again. The fix is bone names.

### The two skeletons today

| | Body | Hair |
|---|---|---|
| Asset | `SK_Melusina` | `SK_MelusinaHair` |
| Skeleton | `SK_Melusina_Skeleton` | `SK_Melusina_Hair_Skeleton` |
| Bones | 465 | 148 |
| Root | `root_x` | **`HairExp_Rig`** |
| Chain | `root_x → spine_01_x → spine_02_x → spine_03_x → neck_x → head_x` | `HairExp_Rig → hair_root → A_DEF_hair_bbone_000…` |

`HairExp_Rig` as the root bone is the smoking gun: **the hair was exported from a separate armature**,
not from the body rig. Everything else follows from that.

Your rig is **Auto-Rig Pro** (`_x` centre-bone suffix, `c_` controller prefix, `c_root_master_x`,
`c_neck_master_x`). That determines the export path below.

---

## Target state

UE needs to see hair bones whose **upper chain names exactly match the body's deform bones**, with
the hair chain hanging under `head_x`:

```
root_x
└── spine_01_x
    └── spine_02_x
        └── spine_03_x
            └── neck_x
                └── head_x
                    └── hair_root
                        ├── A_DEF_hair_bbone_000 … 017
                        ├── B_DEF_hair_bbone_000 …
                        └── (remaining 148 hair bones, unchanged)
```

Then `shared_bones` becomes ≥ 6, CopyPose anchors correctly, and Kawaii Physics keeps driving
everything below `hair_root` exactly as it does now.

---

## Blender checklist

### A. Decide the approach

- [ ] **Preferred — one armature.** Parent the hair mesh to the **same Auto-Rig Pro armature** that
      produces `SK_Melusina`. Add `hair_root` as a child of the `head_x` deform bone. Export the
      hair as its own mesh, but from that shared rig.
- [ ] *Fallback — minimal shared chain.* Keep a separate hair armature, but recreate
      `root_x → spine_01_x → spine_02_x → spine_03_x → neck_x → head_x` inside it with **exact
      names and exact rest transforms** copied from the body, then parent `hair_root` under
      `head_x`. Works, but the rest transforms must match to the millimetre or the offset returns.

The first option is what the C++ comment anticipates and is far less fragile. Do that unless there
is a production reason not to.

### B. Fix the hierarchy

- [ ] Delete or bypass the `HairExp_Rig` root bone. It is an export-rig artifact and is the direct
      cause of the origin offset. The exported root must be `root_x`, matching the body.
- [ ] Confirm `hair_root` is a **direct child of `head_x`**, not of a helper or a second root.
- [ ] Leave every `*_DEF_hair_bbone_*` name unchanged — Kawaii Physics targets `hair_root` and
      walks its children, so the chain below it must stay exactly as-is.
- [ ] Confirm the hair mesh's object transform is **applied** (Ctrl+A → All Transforms) and its
      origin is at world origin, not at the head.

### C. Auto-Rig Pro export settings

- [ ] Use **Auto-Rig Pro → Export**, not Blender's plain FBX exporter. Plain FBX will not produce
      matching deform-bone names.
- [ ] Set export type to **Universal**, not Humanoid. Humanoid remaps to a fixed bone list and will
      silently drop the 148 hair bones.
- [ ] Enable **"Only Deform Bones"** if available, so the `c_*` controllers are excluded. UE only
      needs the deform chain — this is why the body is 465 and not double that.
- [ ] Units: **Centimeters**. Scale **1.0**. Do not "Apply Unit Scale" twice.
- [ ] Axis: **Y up / -Z forward** for UE, or use ARP's built-in Unreal preset if present.
- [ ] Bake/Add leaf bones: **off**.
- [ ] Export **selected mesh only** (the hair), with the armature — not the whole scene.

### D. UE import settings — this step is where it usually goes wrong

- [ ] On import, set **Skeleton = the existing `SK_Melusina_Skeleton`.**
      Do **not** let UE create a new skeleton. If you leave Skeleton blank, UE mints
      `SK_MelusinaHair_Skeleton` again and you are back to `shared_bones=0`.
- [ ] If UE refuses the existing skeleton, the bone names or hierarchy still do not match — go back
      to section B rather than forcing a new skeleton.
- [ ] Import Mesh: on. Import Animations: off.
- [ ] Do not enable "Use T0 As Ref Pose" unless the body used it.

---

## Verify — one line, no guessing

PIE and read the log:

```
MELUSINA_HAIR_BOUND ... shared_bones=? attach_bone=?
```

| Result | Meaning |
|---|---|
| `shared_bones=0`, `attach_bone=head_x` | Still broken. Names did not match — recheck B and D. |
| `shared_bones>0`, `attach_bone=None` | **Fixed.** CopyPose is anchoring; hair should sit correctly. |

If `shared_bones > 0` but the hair is still visually off, the problem has moved from naming to rest
pose, and the next thing to check is whether the hair armature's rest transforms match the body's.

---

## If it lands, a simplification becomes available

With matching bone names you no longer need `CopyPoseFromMesh` at all — `SetLeaderPoseComponent`
is cheaper and exact. `UMelodiaHairComponent` already calls `SetLeaderPoseComponent(nullptr)` to
disable it. Once `shared_bones > 0` is confirmed stable, switching to leader-pose removes an entire
anim-graph node and its per-frame cost.

Not urgent. Do not attempt it until the re-export is verified.

---

## What I did not do, and why

No corrective transform was added to `MelodiaHairComponent.cpp`. The component currently uses
`SnapToTargetNotIncludingScale` with a stale comment claiming it preserves local offset — it does
not. Fixing that mismatch, or adding a measured offset, would mask the naming problem and produce a
*new* wrong offset as soon as the rig changes again. The naming fix is the real one; the code is
correct once `shared_bones > 0`.
