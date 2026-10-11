# Runtime convergence — wardrobe, dress, KineFX constraints — 2026-10-09 (tonight)

Status of each item, with the evidence level the project uses. Receipts:
`Saved/Audit/MelusinaKineFXAudit_20261008/` and `Saved/Audit/MelusinaKineFXAudit_20261008/runtime_staging_20261009.md`.

## 1. Build — live-proven

`native_build_wardrobe_20261008.log`: **Result: Succeeded, 589/589, zero errors, 2716.60 s.**

The build stalled hard mid-run (1 action in ~9 min, stuck at 279/589). Root cause was **process
contention, not hardware** — 12 `claude` processes were running but only **two** were consuming CPU
(742 s and 713 s, live since ~8 PM), while **ten were frozen** at identical CPU across a 25 s sample.
Disk 37.8 GB and RAM 30.4 GB were both healthy, so neither was the constraint.

Owner authorized clearing the stale ones. Killed the ten frozen `claude` processes plus a stale
`dotnet` (alive since 7:20 PM the prior day); the two actively-working agents were left alone
deliberately. Effect: **279 → 384 actions in ~2 minutes**.

**The gate that matters is the DLL timestamp, not the log line.** `UnrealEditor-MelodiaWardrobe.dll`
went from Oct 7 23:05 (530,432 B) to **Oct 9 12:23 (531,968 B)** — proof the patch compiled in.

Full builds here are ~589 actions and **exceed the 420 s terminal cap**; run them backgrounded with
notify. Note `pgrep -f "UnrealBuildTool|dotnet"` gave a **false "exited"** under MSYS — trust the
`[n/589]` counter and the DLL timestamp instead.

## 2. Launch + clean slate — live-proven

`Start-Process` from PowerShell **silently failed**; a `cmd /c` batch wrapper worked
(`Saved/Audit/MelusinaKineFXAudit_20261008/launch_ue.bat`) using the canon's pinned DDC policy
`-DDC=NoShared -LocalDataCachePath=C:/UE_DDC`.

Editor PID 19900, 9.8 GB, port 9316 with exactly one listener, MCP answering. Dirty packages were
**0** at launch — the seven `L_MelusinaMorning` packages that were dirty beforehand cleared in the
restart.

## 3. Dress weights verified — live-proven (resolves a 2026-09-02 blocker)

The blocker doc warned `SK_ShorewakeDress_Melusina465` "may not have proper weights." Measured:

- On `SK_Melusina_Skeleton`, **465 bones**; LOD 1, sockets 3, **48 materials**.
- All probe bones present, including **`c_kilt_master_x`** (the Skirt follow bone and the drapery
  spec's designated waist-anchor pin row).
- Bone-chain segment stability across the idle clip: waist anchor **0.000 cm** spread, shoulder
  **0.000 cm**, hem 0.003 cm, head 0.007 cm.

**Verdict: WEIGHTS-LOOK-STABLE.** The retarget is sound; the blocker's warning does not apply.
Receipts `dress_weight_readback.json`, `dress_weight_stability.json`.

## 4. Hat: root cause found, fix proven on head_x, and a double-hat exposed

**Root cause of the floating hat, now pinned:** `BP_MelusinaJRPGCharacter` authors a plain
`SkeletalMeshComponent` named **`HatMesh` with `attach_to=None`**, parented to `CollisionCylinder`.
No bone — so the hat rode at the character origin. It is not created by the wardrobe plugin or by
`MelodiaHairComponent`; it lives in the pawn's own component list.

**Fix proven live** (spawned the pawn, equipped, read back, destroyed the pawn):

```
WardrobeSlot_EMelodiaWardrobeSlot::Hat | mesh SK_Melusina_V2_Hat
  parent CharacterMesh0 | socket head_x | visible true     head_x_index: 202
```

Implemented in the **existing** `Plugins/MelodiaWardrobe` plugin (a duplicate subsystem was
authored earlier on a bad premise — the plugin already existed — and was removed):

- `GetDefaultFollowBone(slot)` — Hat→`head_x`, Skirt→`c_kilt_master_x`, Boots→`foot_l`,
  Gloves→`hand_l`, Shawl→`spine_03_x`, Shirt/Trail→`spine_01_x`; HairCharm/Accessories/Body→none.
- Attach after `SetLeaderPoseComponent` (order is required), guarded with `GetBoneIndex`/`INDEX_NONE`
  and a `MELODIA_WARDROBE_MISSING_BONE` fallback so a garment missing its bone cannot attach blind.
- Hair is excluded on purpose: it runs its own 148-bone `SK_Melusina_Hair_Skeleton`.

**But equipping renders TWO hats** (`count_before: 1 → count_after: 2`, both visible) — the legacy
`HatMesh` is left visible alongside the new bone-attached one. This is a side effect of the fix, not
a pre-existing bug.

### The duplicate-hat fix — authored in source, NOT yet built

`RetireDuplicateMeshComponents()` hides any *other* component carrying the same mesh when a slot
equips. Chosen over deleting the BP's `HatMesh` because the legacy component is authored on the
Blueprint and this plugin does not own it — hiding is reversible and fixes the **class** of bug for
Gloves/Shawl/Trail later. Logs `MELODIA_WARDROBE_DUPLICATE_HIDDEN`.

**Two APIs in my first attempt would not have compiled** — caught by grepping the installed UE 5.8
source before building:

| assumed | reality |
|---|---|
| `OwningActor->GetComponentsByClass<T>()` | Blueprint-only `K2_` variant; engine comment says use `GetComponents()` + cast in C++ (Actor.h:3804). `GetComponents()` returns `const TSet<UActorComponent*>&` (Actor.h:4083) |
| `TMap::FindKey(...)` | **does not exist** in UE 5.8's TMap; replaced with an explicit value scan |

## 5. KineFX / Vellum constraints for the dress — source-proven

- **The KineFX work in `Tools/Houdini/sir_kinefx/` is Sir's, not Melusina's** (12 scripts, zero
  Melusina references). What transfers is its **measured failure**: Vellum v1 on a cm-native scene
  stretched the collar **~6×** because Vellum assumes metres. v2 converts (`SCALE=0.01`), uses
  `-9.81`, scales back ×100 on write, and **measures the gravity axis from the rig** rather than
  guessing. Melusina's dress is cm-native too, so the same trap applies.
- **Melusina Vellum work does exist** — `Docs/Art/UNIVERSAL_GARMENT_FABRIC_DRAPERY_2026-09-02.md`
  (status Active). Verified node set; **`veler` is NOT installed**, so Vellum Erosion is excluded
  from all recipes (relaxation = `vellumrestblend` + `vellumpostprocess`). Tiered budget A–D:
  `M_Bodice_Upper` rigid (the waist anchor), collar/shoulder-trim soft pin, sleeve/underskirt WPO,
  **`M_Skirt_Full` = tier D, offline Vellum drape → VAT bake**.
- `specs/wardrobe/wardrobe_shorewake_manifest.v1.json` **already maps the dress to the `Skirt` slot**
  against `SK_ShorewakeDress_Melusina465` — consistent with the runtime work above.
- **Correction to earlier advice:** the hero skirt is a *bake*, not a runtime solver. Do not add a
  runtime cloth solver for it; Chaos/WPO cover the cheap secondary pieces.
- Live hazard: **three dress variants at three scales** — reef cm-native, magical 100×, chaos proxy
  matching magical ("divide by 100 on UE import, do NOT rewrite source"). Reconcile before promotion.

## 6. Tooling added (verified, not claimed)

| tool | what it gates | tests |
|---|---|---|
| `Tools/animation/verify_clip_gate.py` | arm canon (hard) + local-space loop seam on true loops + foot-z (informational) | 5 pass |
| `Tools/animation/verify_nlens.py` | N2/N3/N5/N9 from the contract's `nikki_regions` | 16 pass |
| `Tools/animation/repair_loop_seam.py` | feathers position **and** rotation (shortest-arc quat) into a new folder | — |

21 tests pass together. In `--live` the N-lens gate computes only **N9** (bone transforms, not vertex
soup); N2/N3/N5 report `NOT MEASURABLE` with the reason rather than being skipped or faked.

**Loop-seam correction:** the earlier 13 cm "seam" was a **measurement artifact** — world-space Euler
decomposition wraps 360°→0°. The real defect is a **~10.1° `foot_r` local rotation pop on Walk/Run**
(sprint 4.54° and idle 0.11° are clean); local position delta is 0.000 cm everywhere.

**Arm regression, resolved:** the defect is inherent to every *raw* retarget. Forcing the retargeter
chain `translation_mode=None` **still reproduces** 34.789/9.520, so the clip-level fix is the only
lever — which is why it "keeps regressing" after every fresh retarget. All 13 fleet clips and all six
frozen Sparrow clips currently **pass** the canon and animate. Gate with `verify_clip_gate.py`.

## 7. Blocked — needs an owner decision before the next build

**Dirty packages: 141** (130 `L_MelusinaMorning` external actors + 11 `EnvSandbox`/`Melodia`
materials). None are from this work — this session touched only `Plugins/MelodiaWardrobe/Source/`
and `Tools/`. **Another lane is actively authoring materials and level dressing.**

The duplicate-hat fix needs a **closed-editor build** (it is a header change), so the editor must
close — but closing now would discard 141 packages of another lane's uncommitted work. Not done,
deliberately. Options when that lane is clear:

1. That lane saves/commits, then close and build (recommended).
2. Owner explicitly authorises discarding the 141 packages (not recommended — real authored work).
3. Wait for the next window.

**Then:** build → re-run the hat probe and confirm `count_after == 1` with `socket == head_x`.

## 8. Probe pitfalls worth keeping

- `get_relative_location()` and calling a `UFUNCTION` static from Python are both unavailable in this
  binding. Use `get_editor_property("relative_location")` and `mesh.get_bone_index(unreal.Name(...))`.
- Monolith `run_python` returns `output` as a **mixed `warning`/`info` list** — parse the **last
  `info`** entry, not `[0]`. A deprecation warning read as `[0]` produced a false failure.
- `EditorLevelLibrary.destroy_actor` is deprecated (Editor Scripting Utilities); still works.
- Python reflection on a `UClass` returns only generic UObject plumbing, so a component's own methods
  are absent from `dir()` — that proves nothing about whether they exist. Use the symbol in the DLL
  plus the wired call sites.
