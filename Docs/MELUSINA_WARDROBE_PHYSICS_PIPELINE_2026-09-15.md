# Melusina wardrobe, physics and texture pipeline — reference, 2026-09-15

Written for the dress-up / wardrobe ("Infinity Nikki"-shaped) work later. Everything below was
verified against engine source, plugin source, or the live editor on 2026-09-15 — not inferred.
Where an earlier session's claim was wrong, the correction is marked **WRONG BEFORE**.

---

## 1. How a garment gets animated — the rule that governs everything

`UMelodiaWardrobeComponent` creates one `USkeletalMeshComponent` per slot and calls
`SlotComp->SetLeaderPoseComponent(BodyMesh)` (`MelodiaWardrobeComponent.cpp:179`). That single call
decides what is and isn't possible for every garment.

**A leader-pose follower can never run its own simulation.** This is engine-level, not a setting:

- `SkinnedMeshComponent.cpp:3103 AllocateTransformData()` early-outs on `LeaderPoseComponent == nullptr`,
  so a follower **never allocates `ComponentSpaceTransforms`**. Its anim graph has nowhere to write a pose.
- `bFollowerShouldTickPose` (`SkeletalMeshComponent.cpp:1885`) only lets the AnimInstance tick — montages,
  notifies, curves. Skinning still reads the **leader's** transform array, so the bone output is discarded.
- Bones the follower has that the leader lacks are resolved from the follower's **ref pose** relative to the
  nearest common ancestor (`GetMissingLeaderBoneRelativeTransform`, `SkinnedMeshComponent.cpp:3437`).
  They are rigidly frozen — adding dangle bones to a *garment mesh only* achieves nothing.

The code comment at `MelodiaWardrobeComponent.cpp:178` says the wardrobe uses "the same technique as the
hair's leader-pose sharing". **That comment is wrong**, and the wrongness is exactly why hair has physics
and the shirt does not: `MelodiaHairComponent.cpp:199` calls `SetLeaderPoseComponent(nullptr)` and then
assigns its own ABP.

### The two valid patterns

| Pattern | Used by | How it works | Cost |
|---|---|---|---|
| **A — shared-skeleton bones, simulated on the body ABP** | **skirt** | Dangle bones live in the SHARED `SK_Melusina_Skeleton`. A KawaiiPhysics node on the **body's** ABP simulates them. The garment inherits the already-simulated transforms through leader pose. | Free. No per-garment ABP, no code change, garment stays a cheap follower. |
| **B — detached component with its own ABP** | **hair** | `SetLeaderPoseComponent(nullptr)` + own ABP: `CopyPoseFromMesh(body) → LocalToComponent → KawaiiPhysics → ComponentToLocal → Output`. | Garment becomes a separately-evaluated mesh; loses the free skinning share. |

**For wardrobe/dress-up work, Pattern A is the default.** It scales to many garments at near-zero cost and
needs no per-garment asset. Reach for Pattern B only when a garment needs its own skeleton (hair does).

> **WRONG BEFORE:** an earlier plan prescribed Pattern B plus KawaiiPhysics SharedCollision for the shirt.
> That was over-engineered. Shared collision exists for garments on genuinely separate components with
> their own ABPs — Pattern A needs none of it, because the simulation happens on the body in the first place.

---

## 2. Current state of Melusina's rig

`BP_MelusinaJRPGCharacter` → `CharacterMesh0` = `SK_Melusina_V2_Body`, anim class `ABP_Melusina_Current`.
Skirt and shirt are runtime wardrobe slot components, not part of the character mesh.

All outfit meshes (`SK_Melusina_V2_{Body,Shirt,Skirt,Boots,Accessories}`) ride the shared
**`SK_Melusina_Skeleton`: 465 bones, of which 101 are `c_kilt_*` — and ZERO shirt / sleeve / hem /
collar / frill bones.**

That single fact is the whole reason the shirt has no physics. It is an art/rig gap, not a code gap.

### Live Kawaii node values (verified 2026-09-15)

| | skirt — `ABP_Melusina_Current` / `AnimGraphNode_KawaiiPhysics_0` | hair — `ABP_Melusina_WaterHair` / `AnimGraphNode_KawaiiPhysics_1` |
|---|---|---|
| RootBone | `c_kilt_master_x` | `HairExp_Rig` |
| Alpha / LODThreshold | 1.0 / −1 | 1.0 / −1 |
| Gravity | (0,0,−120) world-space | (0,0,−120) world-space |
| PhysicsSettings | damp 0.30, stiff 0.18, wDampLoc 0.80, wDampRot ~0.3, radius ~2, limitAngle | damp 0.30, stiff 0.07, wDampLoc 0.65, wDampRot 0.30, radius 2, limitAngle 75 |
| Collision | `DA_Melusina_SkirtCollisionLimits` + `SK_Melusina_PhysicsAsset` | `DA_Melusina_HairCollisionLimits` |
| Wind | on, scale 0.45 | on, scale 0.35 |
| **DummyBoneLength** | **3.0** (was 0.0 — fixed today) | 3.0 |
| **bNeedWarmUp** | **true** (was false — fixed today) | **true** (was false — fixed today) |
| SyncBones | `[]` — unused | `[]` — unused |

> **WRONG BEFORE:** an earlier report claimed hair gravity was `(0,0,0)` and that this was why the hair
> floated. Hair gravity is **−120, identical to the skirt**. The bogus reading was almost certainly
> `GravityInSimSpace`, a transient runtime field that is zero at rest. **Hair and skirt were never broken.**

### The two defects actually found and fixed today

1. **`DummyBoneLength` 0.0 on the skirt.** `AnimNode_KawaiiPhysicsModifyBones.cpp:212` adds a tip dummy only
   when `DummyBoneLength > 0`. At 0 the kilt chain tips (`c_kilt_XX_04_*`) got no extra segment, so the hem
   was stiff. Set to 3.0 (hair already used 3.0; the plugin's own test harness uses 4.0).
2. **`bNeedWarmUp` false on both.** `AnimNode_KawaiiPhysics.cpp:554` runs the settle steps only when the flag
   is set. `WarmUpFrames` was already 12 but unreachable, so hair and skirt visibly settled from ref pose on
   first activation. Teleports were already fine (`ResetDynamics` sets the flag via
   `bUseWarmUpWhenResetDynamics`) — only the FIRST activation popped, which on this route is every level load.

**Not visually verified.** See §5 for why.

---

## 3. What the shirt needs (and nothing else)

One thing: **shirt dangle bones in `SK_Melusina_Skeleton`** — sleeve cuffs, hem, collar ribbon; 2–3 bones
per chain, parented under `c_spine_03_x` / the arm chain. Done in Blender and reimported onto the same
skeleton (additive bones are fine).

Then, entirely in-editor and quick:
1. Add a second KawaiiPhysics node to **`ABP_Melusina_Current`** (the body ABP) rooted at the new shirt root.
2. Give it `DummyBoneLength` ~3 and a collision DataAsset (clone the skirt's).
3. Nothing else. The shirt inherits it through leader pose, like the skirt does.

---

## 4. KawaiiPhysics 1.21.0 (UE 5.8) — what this fork gives us

Relevant beyond the basics, for future garment work:

- **`KawaiiPhysicsSharedCollisionSubsystem`** — a `UTickableWorldSubsystem` that shares *computed* collision
  limits between Kawaii nodes in the same **attached actor family**, keyed by `FGameplayTag`
  (`bSharedCollisionSource` / `bUseSharedCollision` / `SharedCollisionGroupTag`). Solves body-collision reuse
  for Pattern-B garments. Within one AnimGraph, the source node must evaluate *before* the target.
- **`FKawaiiPhysicsSyncBone`** — documented verbatim for *"prevent skirts from penetrating legs"*. Applies a
  source bone's movement onto physics-controlled bones, with per-axis direction masks
  (`ApplyDirection{X,Y,Z}`), distance attenuation (inner/outer radius), and falloff curves. **Currently
  unused on both nodes.** This is the first thing to reach for when the skirt clips the legs — do not hand-tune
  damping to hide it.
- `AdditionalRootBones`, `BoneSubdivisionCount` (skirt 1, hair 3), bone constraints (XPBD), external-force
  structs, and `KawaiiPhysicsLibrary` runtime setters all exist.

---

## 5. Tooling truths — read before repeating this work

These cost real time today. They are properties of the tools, not of this project.

**Reading anim-node values.** `animation_query get_nodes` returns only class/title/pins. The reliable reader is:

```python
node = unreal.load_object(None,
    '/Game/.../ABP_Foo.ABP_Foo:AnimGraph.AnimGraphNode_KawaiiPhysics_0')
n = node.get_editor_property('node')      # the inner FAnimNode struct
n.get_editor_property('physics_settings')  # etc.
```

`animation_query set_anim_graph_node_property` also returns `old_value`, which is authoritative — but it
*writes*, so only use it as a reader if you restore the value afterwards.

**Texture resolution.** `Texture2D.blueprint_get_size_x()` returns the **resident streaming mip**, not the
imported size — it reported 32 and 4096 for different textures in the same call, at random. `.uasset` byte
size is also useless, because the uasset embeds the compressed *source*: a broken 32×32 build can still be a
12 MB file. **Authoritative reader: `material_query preview_textures`**, whose per-asset
`width` / `height` / `mip_count` / `pixel_format` are the real built values.

**PIE capture.** `capture_pie_movement_clip` viewport capture **only works on the first PIE session after an
editor launch**; every later session stalls at one frame with `captured_ok: false` regardless of arguments.
`capture_anim_frames` shares that path and fails the same way post-PIE. Budget one clip per editor run, or
restart the editor.

**PIE scripting hooks.** `python_script` silently does not execute (nothing in `LogPython`) *and* breaks frame
capture as a side effect. Use **`probe_scripts`** — `[{at_seconds, python}]` — which fires against the live PIE
world and reports `python_ok`. Note `console` must be an **array** of strings.

**Default PIE camera sits inside the character.** With no view target set the camera lands at the pawn origin,
so every frame is an unreadable close-up of the inside of her skirt. Spawn a `CameraActor` in a probe and
`set_view_target_with_blend`, or use the level's `CAM_MelusinaMorning_Portfolio`.

---

## 6. Texture pipeline — where Melusina's shirt art actually lives

> **WRONG BEFORE:** an earlier report called `T_Melusina_UpdatedShirt_*` / `T_Melusina_Shirt_*` "32×32
> placeholders" and assigned `MI_Melusina_Material_008` to the `T_Melusina_Material_008_*` set instead.
> Both halves of that were wrong, and the search was too narrow — it only looked in
> `Characters/Melusina/Textures`.

Complete 4K PBR sets exist in **three** places:

| Location | Set | State |
|---|---|---|
| `Content/Textures/` | `T_Melusina_UpdatedShirt_{BC,N,ORM,H,Mask,Emission}` | sources 4096², **reimported today → 4096², 13 mips, DXT1/BC5** |
| `Content/Textures/` | `T_Melusina_FrontPanel_{BC,N,ORM,H,Mask,Emission}` | same, reimported today |
| `Content/Melodia/Characters/Melusina/Textures/` | `T_Melusina_{UpdatedShirt,Shirt}_*` | valid 4096 **source** embedded, but built at **32×32 / 1 mip** — still broken, needs the same reimport |
| `Content/Melodia/Characters/Melusina/Textures/` | `T_Melusina_Material_008_*` | genuinely real 4096² DXT1, 13 mips |
| `/Game/` root + `/Game/00_Archive/RepoRoot_2026-08-31/` | `Melusina_sUpdatedShirt_*` | loose duplicates; source path points at a nonexistent `UE_5.8/Engine/Binaries/` file |

The failure mode to recognise: **a 12 MB `.uasset` that renders as a 32×32 texture.** The art was never
missing — the *import* collapsed while keeping the full-resolution source. Fix is a plain reimport
(`AssetImportTask` with `replace_existing=True`), not a re-bake or a re-export.

Also fixed today: `ORM`, `Mask` and `H` had imported as **sRGB**. Set to linear with `TC_Masks` /
`TC_Grayscale`. Same bug class as the earlier `fix(flora): linear sRGB on data maps` commit — worth checking
on every new bake.

Still open: `MI_Melusina_Material_008` is on the `Material_008_*` set. Which of `Material_008`,
`UpdatedShirt` or `FrontPanel` is the intended shirt look is an art call, not a technical one. Note
`bUseSeparateRoughnessMap` / `bUseSeparateMetallicMap` are off, so those maps are currently unused.

---

## 7. Two repo landmines found while committing this

**`Content/*` is gitignored** (`.gitignore:113`) with explicit un-ignore entries for `Content/Melodia/`,
`Content/MelodiaIntegration/`, `Content/Experiments/MelodiaJRPG/` and character content. **`Content/Textures/`
is NOT among them**, so all 12 reimported 4K shirt/front-panel textures are untracked and uncommittable.
They exist only on disk and on the G: mirror. `.gitignore` is a protected file — promoting `Content/Textures/`
needs owner sign-off. Same class of issue as the WaveHarp meshes dropped from PR #213.

**`skip-worktree` was set on two files**, which makes git silently ignore *all* local changes to them —
edits are never staged, never committed, and are lost on the next checkout:

```
Content/Melodia/Characters/Melusina/ABP_Melusina_Current.uasset
Content/Melodia/Characters/SirMelodious/Materials/MI_SirMelodious_Sirmelo.uasset
```

This is why today's skirt fix appeared to save correctly (mtime updated, 757277 vs HEAD's 757722 bytes) while
`git status` reported the file clean. Cleared on the Melusina ABP so the fix could be committed:

```bash
git update-index --no-skip-worktree Content/Melodia/Characters/Melusina/ABP_Melusina_Current.uasset
```

**`MI_SirMelodious_Sirmelo.uasset` is still flagged** — left alone deliberately, since it wasn't part of this
work and whoever set it may have had a reason. Worth an owner decision: if it was set to protect a local-only
tweak, that tweak is one `git checkout` away from being erased.

Check periodically with `git ls-files -v | grep "^S"`.
