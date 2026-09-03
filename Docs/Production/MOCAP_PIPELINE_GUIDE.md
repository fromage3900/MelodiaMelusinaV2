# Mocap Pipeline Guide

**Status:** Production reference — covers Rokoko FBX, Cascadeur, and Quaternius retarget paths.
**Last updated:** 2026-09-03
**Canonical retargeter:** `RTG_Mocap_to_Melusina_Current` → `IK_Melusina_Body_Current` (root_x, 19 chains)

---

## Table of Contents

1. [Rokoko Export Settings](#1-rokoko-export-settings)
2. [Import to UE](#2-import-to-ue)
3. [Retargeting](#3-retargeting)
4. [Headless Batch Retarget](#4-headless-batch-retarget)
5. [Mocap Cleanup](#5-mocap-cleanup)
6. [Existing Mocap Library](#6-existing-mocap-library)
7. [Add a New Mocap Clip End-to-End](#7-add-a-new-mocap-clip-end-to-end)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Rokoko Export Settings

### Profile
- **Use the CharacterRef profile** built from `SK_MocapSource` — NOT a generic Mixamo/Manny profile.
- If you export with a mismatched profile, import still lands but retarget quality will be wrong (bone names won't match `SK_MocapSource_Skeleton`).
- CharacterRef FBX lives at: `Imports/Mocap/Rokoko/CharacterRef/SK_MocapSource.fbx`

### Bone Names
- FBX bone names **must match** `SK_MocapSource_Skeleton` exactly.
- Rokoko Studio: import the CharacterRef FBX → drag onto your actor → calibrate T-pose/shoulder width to Melusina's proportions.
- If bones diverge: duplicate `RTG_Mocap_to_Melusina` → `RTG_Rokoko_to_Melusina` and remap chains once.

### Format
- **FBX** (animation-only — no mesh, no materials).
- **30 FPS**.
- One animation clip per FBX file.
- Root motion: disabled for locomotion unless explicitly requested.

### Naming Convention
```
IdleTest.fbx   →  A_Src_Rokoko_IdleTest  →  A_Mocap_Rokoko_IdleTest
WalkLoop.fbx   →  A_Src_Rokoko_WalkLoop  →  A_Mocap_Rokoko_WalkLoop
```
Prefer combat-aligned stems: `Idle`, `Walk`, `Run`, `Dodge`, `Stab`, `HitReact`, `Victory`.

### Drop Location
```
Imports/Mocap/Rokoko/Inbox/*.fbx
```

---

## 2. Import to UE

### Script: `Content/Python/import_rokoko_mocap.py`

**What it does:**
1. Scans `Imports/Mocap/Rokoko/Inbox/*.fbx`
2. Imports each FBX onto `SK_MocapSource` (source skeleton/mesh)
3. Names output `A_Src_Rokoko_<Take>` in `/Game/Melodia/Mocap/Source/Anims`
4. Optionally retargets to Melusina (if `import_only=False`)
5. Writes report to `Saved/Melodia/rokoko_import_report.json`

**Key paths:**
| Path | Role |
|------|------|
| `Imports/Mocap/Rokoko/Inbox/` | Drop new FBX takes here |
| `/Game/Melodia/Mocap/Source/SK_MocapSource` | Source mesh (import target) |
| `/Game/Melodia/Mocap/Source/SK_MocapSource_Skeleton` | Source skeleton |
| `/Game/Melodia/Mocap/Source/Anims/A_Src_Rokoko_*` | Imported source animations |
| `/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_*` | Final retargeted clips |

**Run (editor open):**
```python
import import_rokoko_mocap as m
m.main(import_only=False)   # import + retarget
# or:
m.main(import_only=True)    # import only, retarget later via headless
```

**Run (editor closed — headless):**
```powershell
powershell -ExecutionPolicy Bypass -File Tools\run_headless_mocap_retarget.ps1
```

**Do NOT** import Rokoko FBX directly onto `SK_Melusina`. Always go through `SK_MocapSource` + IK retargeter.

---

## 3. Retargeting

### Canonical Retargeter
- **Asset:** `/Game/Melodia/Mocap/Retarget/RTG_Mocap_to_Melusina_Current`
- **IK Rig:** `IK_Melusina_Body_Current`
- **Chain count:** 19 chains + root_x
- **Source mesh:** `SK_MocapSource`
- **Target mesh:** `SK_Melusina` (binds `SK_Melusina_Skeleton`)

### Chain Mapping
- Uses `AutoMapChainType.EXACT` — source and target chains share identical bone names.
- Both V1 (`SK_Melusina`) and V2 (`SK_Melusina_V2_*`) meshes bind `SK_Melusina_Skeleton`, so output clips play on V2 via leader pose with **zero re-retargeting**.

### Retarget Flow
```
A_Src_Rokoko_<Take> (on SK_MocapSource)
        │
        ▼
RTG_Mocap_to_Melusina_Current (auto_map_chains EXACT)
        │
        ▼
A_Mocap_Rokoko_<Take> (on SK_Melusina)
        │
        ▼
ABP_Melusina / montages / blend spaces
```

### Skeleton Rebind
The headless script performs an **unconditional skeleton rebind** via `MelodiaAssetRepairLibrary.set_skeletal_mesh_skeleton()` because Python-side reads of `Mesh.Skeleton` are unreliable (returned None in one boot, non-None in another). If rebind fails, the script aborts before writing junk clips.

---

## 4. Headless Batch Retarget

### Script: `Tools/run_headless_mocap_retarget.ps1`

**Why headless:** The interactive batch retarget pops a per-clip "Duplicating animation | Cancel" modal that severs the Monolith MCP socket and silently cancels, producing 0 or null-skeleton assets. `-run=pythonscript` has no Slate modals.

**Preconditions:**
- Editor must be **CLOSED** (Slate modals break interactive batch retarget).
- FBX already imported as `A_Src_*` in `/Game/Melodia/Mocap/Source/Anims`.

**Usage:**
```powershell
powershell -ExecutionPolicy Bypass -File Tools\run_headless_mocap_retarget.ps1
```

**Manual equivalent:**
```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  'C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject' `
  -run=pythonscript -script='C:/EnvironmentPortfolio/BS_GodFile/Content/Python/headless_retarget_mocap.py' `
  -unattended -nop4 -nosplash
```

### What the Report Means

**Location:** `Saved/Melodia/retarget_report.json`

**Format:**
```json
[
  {
    "src": "A_Src_Dodge",
    "created": ["/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Dodge1"],
    "ok": true,
    "skeleton": "SK_Melusina_Skeleton"
  }
]
```

| Field | Meaning |
|-------|---------|
| `src` | Source animation name (in `Source/Anims`) |
| `created` | Output path(s) in `Animations/Mocap/` |
| `ok` | `true` = valid skeleton bound, `false` = null-skeleton junk |
| `skeleton` | Resolved skeleton name — should be `SK_Melusina_Skeleton` |

**Success criteria:** `ok: true` AND `skeleton: "SK_Melusina_Skeleton"` for every entry.

**Idempotent:** `overwrite_existing_files=True` — safe to re-run.

---

## 5. Mocap Cleanup

### Common Artifacts & Fixes

#### Foot Slide
**Symptom:** Feet drift across the floor during standing/walking.
**Cause:** Root motion mismatch or IK foot pin not engaged.
**Fix:**
- Enable IK foot pinning in the IK Retargeter (chain settings → foot chains → pin to ground).
- For locomotion: ensure root motion is extracted from the correct bone (root_x).
- In Animation Editor: use "Snap to Floor" or adjust root motion scale.
- For cyclic clips: trim to exact loop points (use `Jump_Loop` → verify first/last frame match).

#### Hand Penetration
**Symptom:** Hands clip through body, skirt, or weapon.
**Cause:** Source skeleton proportions differ from Melusina (shorter/longer arms).
**Fix:**
- Adjust chain IK goals in `IK_Melusina_Body_Current` (hand chain offset).
- Use Animation Editor → Modify Curve → add hand position offset keys.
- For weapon holds: create a socket on the weapon and use IK constraint to snap hand to socket.
- In severe cases: re-author the clip in Cascadeur with corrected proportions.

#### Shoulder Twist
**Symptom:** Shoulders rotate unnaturally, collarbone twists.
**Cause:** Retargeter maps shoulder chain to a different twist axis.
**Fix:**
- In `RTG_Mocap_to_Melusina_Current`: adjust shoulder chain's "Twist Axis" setting.
- Reduce shoulder chain FK influence (blend toward parent spine).
- Add a "shoulder stabilization" curve in Animation Editor (clamp rotation Z).
- Check source data: if Rokoko suit was loose on shoulders, re-capture with tighter fit.

#### Jitter
**Symptom:** High-frequency noise on joints, especially hands/feet.
**Cause:** Rokoko sensor noise, magnetic interference, or low-pass filter too wide.
**Fix:**
- In Rokoko Studio: enable "Post-Processing" → "Smoothing" before export.
- In UE Animation Editor: apply "Filter" → "Butterworth" or "Fourier Transform" filter.
- Use `Tools/anim_utils.py` (if available) to batch-smooth curves.
- For finger jitter: disable finger chains in retargeter if not needed.

#### Neck/Spine Warp
**Symptom:** Head bends unnaturally, spine curves wrong.
**Cause:** Neck hierarchy mismatch between source and target.
**Fix:**
- Verify `SK_MocapSource_Skeleton` neck chain matches Melusina's.
- If Melusina's spine/head warps: finish the ARP skeleton rewire before recording a large library (see `Docs/ROKOKO_MELUSINA_MOCAP.md` §Known gate).
- In retargeter: reduce spine chain FK blend weight, increase IK.

#### Scale Mismatch
**Symptom:** Melusina's feet float above ground or sink below.
**Cause:** Source actor height ≠ Melusina's height.
**Fix:**
- In Rokoko Studio: calibrate T-pose to Melusina's proportions.
- In retargeter: adjust "Root Motion Scale" (global or per-chain).
- In Animation Editor: modify root motion Z offset.

---

## 6. Existing Mocap Library

### Primary Mocap Folder
**Path:** `Content/Melodia/Characters/Melusina/Animations/Mocap/`

**20 clips (A_Mocap_*):**

| Clip | Type | Notes |
|------|------|-------|
| `A_Mocap_Dodge` | Combat | Dodge roll |
| `A_Mocap_Dodge_001` | Combat | Dodge variant |
| `A_Mocap_FairyWand` | Combat | Fairy wand attack |
| `A_Mocap_GracefulLanding` | Locomotion | Landing |
| `A_Mocap_Jump` | Locomotion | Jump |
| `A_Mocap_Jump_001` | Locomotion | Jump variant |
| `A_Mocap_Jump_002` | Locomotion | Jump variant |
| `A_Mocap_Jump_Loop` | Locomotion | Jump loop (air) |
| `A_Mocap_LiftOff` | Locomotion | Jump takeoff |
| `A_Mocap_LittleDance` | Dance | Little dance |
| `A_Mocap_LittleDance_001` | Dance | Dance variant |
| `A_Mocap_LittleDance_003` | Dance | Dance variant |
| `A_Mocap_MachineGun` | Combat | Machine gun aim/fire |
| `A_Mocap_MercyStab` | Combat | Mercy stab finisher |
| `A_Mocap_RunCycle` | Locomotion | Run cycle |
| `A_Mocap_RunCycle_Sprint` | Locomotion | Sprint |
| `A_Mocap_RunCycle_Sprint_Loop` | Locomotion | Sprint loop |
| `A_Mocap_Sniper` | Combat | Sniper aim |
| `A_Mocap_Stab` | Combat | Basic stab |
| `A_Mocap_Twirl_001` | Dance | Twirl |

### Locomotion Subfolder
**Path:** `Content/Melodia/Characters/Melusina/Animations/Locomotion/`

13 clips with `_Mocap_RootX` suffix (root-motion extracted):
- `A_Melusina_Idle_Mocap_RootX`
- `A_Melusina_Walk_Mocap_RootX`
- `A_Melusina_Run_Mocap_RootX`
- `A_Melusina_Sprint_Mocap_RootX`
- `A_Melusina_JumpStart_Mocap_RootX`
- `A_Melusina_JumpLoop_Mocap_RootX`
- `A_Melusina_Land_Mocap_RootX`
- Plus non-root-motion variants (`A_Melusina_Idle`, `A_Melusina_Walk`, etc.)

### FemaleBardRetargeted
**Path:** `Content/Melodia/Characters/Melusina/Animations/FemaleBardRetargeted/`

16 clips (`A_FB_Melusina_A_Src_*`) — retargeted from FemaleBard source. Same content as Mocap/ but via a different source skeleton.

### Other Retarget Folders
| Folder | Content |
|--------|---------|
| `Cascadeur/` | 2 clips: `A_CAS_Melusina_Idle_Loop`, `A_BL_Melusina_Idle_Loop` |
| `QuaterniusRetargeted/` | 42 clips (full Quaternius library: walk, run, jump, combat, spell, sitting, etc.) |
| `SourceRetargeted/` | 3 clips (Blender source retarget tests) |
| `FemaleBardRetargeted_V1Pose/` | 1 clip (V1 pose test) |
| `FemaleBardRetargeted_InPlace/` | 1 clip (in-place test) |
| `FemaleBardRetargeted_LocalAxes/` | 1 clip (local axes test) |
| `MannequinRetargeted/` | 1 clip (walk test) |

### Blend Spaces
- `BS_Melusina_Locomotion` — primary locomotion blend space
- `BS_Melusina_Locomotion_Hybrid` — hybrid variant

---

## 7. Add a New Mocap Clip End-to-End

### Step 1: Capture
- Record in Rokoko Studio (suit) or Cascadeur (physics-based).
- For Rokoko: use CharacterRef profile from `Imports/Mocap/Rokoko/CharacterRef/`.

### Step 2: Export
- **Rokoko:** FBX, 30 FPS, animation-only → `Imports/Mocap/Rokoko/Inbox/<TakeName>.fbx`
- **Cascadeur:** FBX, 30 FPS, preserve ARP bone names → `Imports/Animations/Cascadeur/Inbox/CAS_Melusina_<TakeName>.fbx`

### Step 3: Import
**Option A — Editor open (Rokoko only):**
```python
import import_rokoko_mocap as m
m.main(import_only=False)
```

**Option B — Editor open, import only:**
```python
import import_rokoko_mocap as m
m.main(import_only=True)
```

**Option C — Cascadeur:**
```python
import import_cascadeur_anim as cascadeur
print(cascadeur.import_inbox())
```

### Step 4: Retarget
**If you used Option A above, skip this step (already done).**

**Headless (recommended for batch):**
```powershell
powershell -ExecutionPolicy Bypass -File Tools\run_headless_mocap_retarget.ps1
```

### Step 5: Verify
1. Open `Saved/Melodia/retarget_report.json` — confirm `ok: true` and `skeleton: "SK_Melusina_Skeleton"`.
2. Open the output clip in Animation Editor on `SK_Melusina` / `BP_Melusina`.
3. Check: spine/neck orientation, foot contact, hand penetration, shoulder twist.
4. If issues → see [§5 Mocap Cleanup](#5-mocap-cleanup).

### Step 6: Wire to Game
- **Locomotion:** Add to `BS_Melusina_Locomotion` blend space.
- **Combat:** Create montage on `BP_Melusina` (e.g., Stab, MercyStab, FairyWand, Twirl).
- **Idle:** Replace speed-zero sample in blend space.
- Use `Tools/t3d_anim_injector.py` for Blend Space and AnimBP wiring.

### Step 7: Report
- `Saved/Melodia/rokoko_import_report.json` (import details)
- `Saved/Melodia/retarget_report.json` (retarget results)

---

## 8. Troubleshooting

### "Inbox empty" warning
**Cause:** No `.fbx` files in `Imports/Mocap/Rokoko/Inbox/`.
**Fix:** Drop Rokoko FBX exports into the Inbox folder. Re-run.

### Null-skeleton clips (`ok: false`, `skeleton: null`)
**Cause:** Target skeleton rebind failed, or batch retarget ran before skeleton resolved.
**Fix:**
1. Verify `SK_Melusina_Skeleton` exists and is valid.
2. Re-run headless retarget (script performs unconditional rebind).
3. If persistent: open editor, manually rebind `SK_Melusina` skeleton, save, re-run headless.

### "Unable to retrieve target USkeleton"
**Cause:** Target mesh skeleton not loaded or resolved.
**Fix:** The headless script handles this via `MelodiaAssetRepairLibrary.set_skeletal_mesh_skeleton()`. If it still fails, the C++ helper returned false — check Unreal log for the error.

### "FbxImportUI: Failed to find property 'skeletal_mesh'"
**Cause:** (Cascadeur path) Import task not configured with a skeletal mesh.
**Fix:** Ensure `import_cascadeur_anim.py` sets `options.skeletal_mesh` to `SK_Melusina`. This is a Cascadeur importer bug, not Rokoko.

### Neck/spine warp on retargeted clips
**Cause:** Neck hierarchy mismatch between `SK_MocapSource` and `Melusina`.
**Fix:**
- Finish the ARP skeleton rewire before recording a large library.
- See `Docs/ROKOKO_MELUSINA_MOCAP.md` §Known gate — neck hierarchy.
- If already captured: you must re-retarget everything after the skeleton swap.

### Bone name mismatch
**Cause:** Rokoko export used wrong character profile.
**Fix:**
1. Export `SK_MocapSource` FBX from UE → `Imports/Mocap/Rokoko/CharacterRef/`.
2. Import into Rokoko Studio → assign to actor.
3. Re-export takes with correct profile.
4. If names still diverge: build `RTG_Rokoko_to_Melusina` with custom chain mapping.

### Foot slide after retarget
**Cause:** IK foot pin not engaged or root motion scale wrong.
**Fix:** See [§5 Foot Slide](#foot-slide).

### Hand penetration through skirt
**Cause:** Arm chain length mismatch.
**Fix:** See [§5 Hand Penetration](#hand-penetration).

### Shoulder twist
**Cause:** Twist axis misalignment in shoulder chain.
**Fix:** See [§5 Shoulder Twist](#shoulder-twist).

### Jitter on hands/feet
**Cause:** Rokoko sensor noise or magnetic interference.
**Fix:** See [§5 Jitter](#jitter).

### Batch retarget produces 0 clips
**Cause:** Editor was open (Slate modal interrupted), or `A_Src_*` not found in `Source/Anims`.
**Fix:**
1. Close the editor.
2. Verify source clips exist: check `/Game/Melodia/Mocap/Source/Anims/` for `A_Src_*`.
3. Re-run headless script.

### "Duplicating animation | Cancel" modal
**Cause:** Interactive batch retarget (in-editor) pops a per-clip modal.
**Fix:** Use headless retarget (`run_headless_mocap_retarget.ps1`) — no Slate modals.

### Retargeted clip plays on V1 but not V2 (or vice versa)
**Cause:** Should not happen — both bind `SK_Melusina_Skeleton`.
**Fix:** If it does: verify V2 mesh skeleton binding. Rebind if needed via `MelodiaAssetRepairLibrary`.

### Report file not generated
**Cause:** Script crashed before `_write()`, or `Saved/Melodia/` directory missing.
**Fix:** Check Unreal log for errors. Ensure `Saved/Melodia/` exists (script creates it, but permissions may block).

### "No imported paths" warning
**Cause:** FBX import task returned empty `imported_object_paths`.
**Fix:**
- Verify FBX file is valid (open in Blender first).
- Check FBX has animation data (not just mesh).
- Verify `SK_MocapSource_Skeleton` is loadable.

---

## Quick Reference

| Task | Command |
|------|---------|
| Import + retarget (editor) | `import import_rokoko_mocap as m; m.main(import_only=False)` |
| Import only (editor) | `import import_rokoko_mocap as m; m.main(import_only=True)` |
| Headless batch retarget | `powershell -ExecutionPolicy Bypass -File Tools\run_headless_mocap_retarget.ps1` |
| Check report | `Saved/Melodia/retarget_report.json` |
| Canonical retargeter | `RTG_Mocap_to_Melusina_Current` |
| Source mesh | `SK_MocapSource` |
| Target mesh | `SK_Melusina` |
| Target skeleton | `SK_Melusina_Skeleton` |
| Output folder | `Content/Melodia/Characters/Melusina/Animations/Mocap/` |

---

## Related Docs

- `Docs/ROKOKO_MELUSINA_MOCAP.md` — Rokoko setup, Live Link, CharacterRef
- `Docs/CASCADEUR_MELUSINA_PIPELINE_2026-08-07.md` — Cascadeur export/import contract
- `Docs/CASCADEUR_QUATERNIUS_PROVENANCE_2026-08-07.md` — Quaternius source provenance
- `Docs/Handoffs/BLENDER_VERSION_GRAPH_AND_V25_ROKOKO_PLAN_2026-08-28.md` — v25 rebuild + Rokoko suite
- `Imports/Mocap/Rokoko/SETUP_STATUS.md` — hardware/software checklist
