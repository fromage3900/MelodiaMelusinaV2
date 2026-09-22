# Hermes lane: Melusina locomotion root-motion re-export

> **For Hermes (model: Kimi 2.8).** This is an offline Blender lane. It runs in parallel with a Claude
> session that owns the Unreal Editor. You produce files and a measured JSON. You never touch Unreal.
> Jev ruling 2026-09-21 (`jev-1.13.0`, live): lane `reexport_root_motion` 0.70, model Kimi 2.8,
> collision risk 1.74/3 (moderate–high). The guardrails below exist because of that risk.

## Goal

The four locomotion clips have **zero** root translation (`root` and `c_traj` Δ = 0; `root_x` drifts
~3.3 uu/s of noise). Unreal's BlendSpace cannot be placed from real speeds, so her feet slide.

| UE clip | Length | Frames @30 |
|---|---|---|
| `A_Melusina_Idle_Mocap_RootX` | 0.500 s | 15 |
| `A_Melusina_Walk_Mocap_RootX` | 1.167 s | 35 |
| `A_Melusina_Run_Mocap_RootX` | 1.167 s | 35 |
| `A_Melusina_Sprint_Mocap_RootX` | 0.917 s | 27.5 |

**Deliver:** each clip re-exported with root motion baked on the root bone (unlocked), with the
travel measured.

## Step 0: source (owner-confirmed 2026-09-21)

Source folder: `C:\Users\froma\OneDrive - Humber Polytechnic\Recordings\Mocap\` (25 Rokoko FBX,
2025-12-15). The locomotion takes are:

| UE clip | Source take |
|---|---|
| Run | `RunCycle.fbx` (3.2 MB) |
| Sprint | `RunCycle_Sprint.fbx` (4.4 MB) |
| Walk | **no walk take in the folder.** UE's Walk and Run share length and root_x delta, so Walk is probably RunCycle retimed. Report; do not fabricate a walk. |
| Idle | **no idle take.** Idle should have ~0 travel anyway; re-export only if a source turns up. |

Copy the FBX into the work folder first (OneDrive may hold cloud-only placeholders; confirm the copy's
size matches). Measure the raw take's hip/root travel **before** retargeting. If the raw takes also have
no forward travel (recorded on a treadmill or in place), stop and report.

## Step 1: export (only after Step 0 finds a real source)

- Retarget the raw take onto the Melusina skeleton and work on a **copy** in `C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaReexport_20260921/`.
  Run `verify_blend.py` on the copy *after* copying.
- Skeleton must match `SK_Melusina_Skeleton` bone names and hierarchy (binding reference:
  `Tools/Cascadeur/Melusina/SK_Melusina_Skeleton_Cascadeur.fbx`). No skeleton or bone renames.
- Bake root motion onto `root` (the UE root bone). Keep `root_x` as the pelvis chain.
- One FBX per clip, named `A_Melusina_<Clip>_Mocap_RootMotion.fbx`.

## Step 2: measure (this is the acceptance test)

Write `MelusinaReexport_20260921/root_motion_measure.json`:

```json
{ "clip": "Walk", "source": "<path>", "frames": 35, "fps": 30,
  "root_delta_cm": [x, y, z], "speed_cm_s": 0.0, "loops_cleanly": true,
  "root_x_residual_cm": [x, y, z], "verify_blend": "ok" }
```

Pass = Idle speed ≈ 0; Walk < Run < Sprint and all non-zero; start and end pose match for looping.
Also render a 3-frame contact sheet PNG per clip (first / mid / last) next to the FBX.

## Forbidden (the reason this lane is safe)

- **No Unreal.** Don't open the editor, write to `Content/`, use Claireon/Monolith, or import. Claude imports.
- **Don't open, save or modify** `harp_bow_pipeline/Melusina_Harp_HERO01_ArcherPoseV09_ARP_R08_WIP_20260912.blend`.
  It is the owner's live, dirty session. Its cornea re-weight is already done; don't redo it.
- **No second interactive Blender** while the owner's is open (port 9876 double-bind). Headless only
  (`blender -b`).
- Don't overwrite any `.blend` in `harp_bow_pipeline/` or on `D:\_relocated` / `G:`. D: is master; G: is evidence.
- No git operations of any kind.
- No other runbook items: finger controllers need an owner decision; the hair re-rig and skirt are later lanes.
- **Disk:** C: is at 99%. Check free space before each export. **Stop if free space drops below 10 GB.**

## Report back

One message: the Step 0 findings, the JSON, the file list with sizes, and anything that blocked.
No other docs.

Reference: `Docs/Production/MELUSINA_REEXPORT_RUNBOOK.md` §1.
