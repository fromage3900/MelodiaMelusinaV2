# Retarget Archive Manifest - 2026-08-24

## RESOLVED 2026-08-24 22:5x - REVERTED on owner instruction

The duplicate copies have been **deleted**. Final state:

| | |
|---|---|
| Archive duplicates deleted | **32** |
| Disk freed | **37 MB** |
| Retained in archive | **1** - `MannequinRetargeted/A_Mann_Walk.uasset` |
| Delete failures | **0** |
| Source folders | **all unchanged** |

Post-revert verification: Mocap 20, FemaleBardRetargeted 16, QuaterniusRetargeted 42,
QuaterniusRetargeted_V2Fixed 4, SourceRetargeted 3, Locomotion 11 - all intact. The four critical
must-keeps confirmed present, including `QuaterniusRetargeted_V2Fixed/A_Q_Melusina_Idle_Loop`
(referenced by `BP_SirMelodiousPlayerUnit`).

`A_Mann_Walk` is deliberately retained in the archive: it is a T-posed artifact produced *before*
the `RTG_UE4Mannequin_To_Melusina` pelvis fix (`pelvis` -> `root_x`) and should not be restored.

**COUNT CORRECTION.** The analysis below reports 64 duplicates / ~161 MB. The revert found and
deleted **32 / 37 MB**. The earlier figure was measured while the hung editor was still flushing
renames, so the archive count was a moving target (observed 30 -> 35 -> 55 -> 65 across successive
reads) rather than a stable state. **Trust the resolved numbers in this section, not the analysis
figures below.** Lesson: do not measure a directory an interrupted process may still be writing to;
wait for the writer to be confirmed dead first.

---

**STATUS: RESOLVED (reverted). The analysis below is retained as the record of how the
half-applied state was diagnosed.**

An automated batch `rename_asset` over 65 unreferenced retarget assets was interrupted when the
editor became unresponsive mid-flight. The operator did not know whether any renames had landed and
correctly refused to retry blind. This is the post-hoc reconciliation.

## What actually happened

- **64 assets were DUPLICATED, not moved.** A copy sits under
  `_Archive/RetargetAttempts_20260824/` **and** the original is still at its source path.
- **1 asset was genuinely MOVED** (source no longer present).
- Redundant bytes on disk: **~161 MB**.

**Nothing is broken.** Every original path still resolves, so no reference can dangle. The archive
copies are pure redundancy. Source folders hold FULL-SIZE assets (1-4 MB), not redirector stubs -
so UE's redirector fixup never ran.

## The one true move

- `Content/Melodia/Characters/Melusina/Animations/MannequinRetargeted/A_Mann_Walk.uasset` -> `Content/Melodia/Characters/Melusina/Animations\_Archive/RetargetAttempts_20260824/MannequinRetargeted/A_Mann_Walk.uasset`

  `A_Mann_Walk` is a known-bad artifact - a T-posed output produced *before* the
  `RTG_UE4Mannequin_To_Melusina` pelvis fix (`pelvis` -> `root_x`). Archiving it is correct; it
  should not be restored.

## Duplicated assets by source folder

| Source folder | Duplicated |
|---|---|
| `FemaleBardRetargeted/` | 16 |
| `FemaleBardRetargeted_InPlace/` | 1 |
| `FemaleBardRetargeted_LocalAxes/` | 1 |
| `FemaleBardRetargeted_V1Pose/` | 1 |
| `MannequinRetargeted/` | 1 |
| `Mocap/` | 17 |
| `QuaterniusAligned/` | 2 |
| `QuaterniusRetargeted/` | 19 |
| `QuaterniusRetargeted_Test/` | 1 |
| `QuaterniusRetargeted_V2Fixed/` | 3 |
| `SourceRetargeted/` | 2 |
| **Total** | **64** |

## Reference audit (done before the move - still valid)

92 candidates checked via `AssetRegistryHelpers.get_referencers`; 28 referenced (never move), 65
unreferenced. All referenced assets confirmed still in place. Notable must-keeps:

- `Mocap/A_Mocap_LittleDance_001` - referenced by the live `ABP_Melusina_Current`
- `Mocap/A_Mocap_MercyStab` - referenced by the `AM_Mocap_BasicAttack` montage
- `QuaterniusRetargeted_V2Fixed/A_Q_Melusina_Idle_Loop` - referenced by `BP_SirMelodiousPlayerUnit`,
  **a different character**. Moving it would have broken Sir Melodious.
- 23 `QuaterniusRetargeted/` clips are wired into live `AM_Melusina_*` / `AM_Q_Melusina_*` montages
  despite Quaternius never having worked as a retarget lane. Referenced is referenced - kept.

## Decision required - three options, none taken

1. **Revert** - delete the 64 archive duplicates. Returns to the exact pre-move state. Lowest risk.
2. **Complete** - delete the 64 sources so the archive becomes canonical. Destructive direction, and
   since no redirectors were created any path-string reference would break.
3. **Leave** - accept the redundancy. Costs disk and preserves exactly the ambiguity that produced
   six parallel retarget folders in the first place.

Deleting `.uasset` is Red-tier per `CLAUDE.md` and needs owner sign-off. **No deletion performed.**

## Full duplicate list

### `FemaleBardRetargeted/`
- `A_FB_Melusina_A_Src_Dodge.uasset`
- `A_FB_Melusina_A_Src_Dodge_001.uasset`
- `A_FB_Melusina_A_Src_FairyWand.uasset`
- `A_FB_Melusina_A_Src_GracefulLanding.uasset`
- `A_FB_Melusina_A_Src_Jump.uasset`
- `A_FB_Melusina_A_Src_Jump_001.uasset`
- `A_FB_Melusina_A_Src_Jump_002.uasset`
- `A_FB_Melusina_A_Src_LiftOff.uasset`
- `A_FB_Melusina_A_Src_LittleDance.uasset`
- `A_FB_Melusina_A_Src_LittleDance_001.uasset`
- `A_FB_Melusina_A_Src_LittleDance_003.uasset`
- `A_FB_Melusina_A_Src_MercyStab.uasset`
- `A_FB_Melusina_A_Src_RunCycle.uasset`
- `A_FB_Melusina_A_Src_RunCycle_Sprint.uasset`
- `A_FB_Melusina_A_Src_Stab.uasset`
- `A_FB_Melusina_A_Src_Twirl_001.uasset`

### `FemaleBardRetargeted_InPlace/`
- `A_FBI_Melusina_A_Src_FairyWand.uasset`

### `FemaleBardRetargeted_LocalAxes/`
- `A_FBL_Melusina_A_Src_FairyWand.uasset`

### `FemaleBardRetargeted_V1Pose/`
- `A_FB1_Melusina_A_Src_FairyWand.uasset`

### `MannequinRetargeted/`
- `A_MannFix_Walk.uasset`

### `Mocap/`
- `A_Mocap_Dodge.uasset`
- `A_Mocap_Dodge_001.uasset`
- `A_Mocap_FairyWand.uasset`
- `A_Mocap_GracefulLanding.uasset`
- `A_Mocap_Jump.uasset`
- `A_Mocap_Jump_001.uasset`
- `A_Mocap_Jump_002.uasset`
- `A_Mocap_LiftOff.uasset`
- `A_Mocap_LittleDance.uasset`
- `A_Mocap_LittleDance_003.uasset`
- `A_Mocap_MachineGun.uasset`
- `A_Mocap_RunCycle.uasset`
- `A_Mocap_RunCycle_Sprint.uasset`
- `A_Mocap_RunCycle_Sprint_Loop.uasset`
- `A_Mocap_Sniper.uasset`
- `A_Mocap_Stab.uasset`
- `A_Mocap_Twirl_001.uasset`

### `QuaterniusAligned/`
- `A_QA_Melusina_Idle_Loop.uasset`
- `A_QA_Melusina_Walk_Loop.uasset`

### `QuaterniusRetargeted/`
- `A_Q_Melusina_Crouch_Fwd_Loop.uasset`
- `A_Q_Melusina_Crouch_Idle_Loop.uasset`
- `A_Q_Melusina_Driving_Loop.uasset`
- `A_Q_Melusina_Fixing_Kneeling.uasset`
- `A_Q_Melusina_Idle_Loop.uasset`
- `A_Q_Melusina_Idle_Torch_Loop.uasset`
- `A_Q_Melusina_Jog_Fwd_Loop.uasset`
- `A_Q_Melusina_Pistol_Aim_Down.uasset`
- `A_Q_Melusina_Pistol_Aim_Neutral.uasset`
- `A_Q_Melusina_Pistol_Aim_Up.uasset`
- `A_Q_Melusina_Pistol_Idle_Loop.uasset`
- `A_Q_Melusina_Pistol_Reload.uasset`
- `A_Q_Melusina_Pistol_Shoot.uasset`
- `A_Q_Melusina_Punch_Cross.uasset`
- `A_Q_Melusina_Punch_Jab.uasset`
- `A_Q_Melusina_Push_Loop.uasset`
- `A_Q_Melusina_Sprint_Loop.uasset`
- `A_Q_Melusina_Walk_Formal_Loop.uasset`
- `A_Q_Melusina_Walk_Loop.uasset`

### `QuaterniusRetargeted_Test/`
- `A_QV2_Test_SK_QuaterniusArmature_Walk_Loop.uasset`

### `QuaterniusRetargeted_V2Fixed/`
- `A_Q_Melusina_Jog_Fwd_Loop.uasset`
- `A_Q_Melusina_Sprint_Loop.uasset`
- `A_Q_Melusina_Walk_Loop.uasset`

### `SourceRetargeted/`
- `A_BL_Source_Idle_Loop__MUAL_SRC.uasset`
- `SK_QuaterniusArmature_Idle_Loop.uasset`
