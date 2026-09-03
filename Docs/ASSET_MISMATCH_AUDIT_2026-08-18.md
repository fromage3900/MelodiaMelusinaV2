# Asset Mismatch & Duplicate Audit — READ ONLY

**Date:** 2026-08-18
**Scope:** BS_GodFile Content/ tree — duplicate Blueprints, skeleton mismatches, runtime authority drift
**Status:** OBSERVATION ONLY — no mutations made

---

## 1. Duplicate / Shadow Blueprints

### 1.1 ABP_Melusina (4 variants)

| Path | Skeleton | Bones | Parent | State Machines | Variables | Issue |
|------|----------|-------|--------|----------------|-----------|-------|
| `Content/Characters/Melusina/ABP_Melusina` | SK_Melusina_Skeleton_OLD | 434 | AnimInstance | 1 | 4 | **OLD SKELETON** — dead copy |
| `Content/Melodia/Characters/Melusina/ABP_Melusina` | SK_Melusina_Skeleton_OLD | 434 | AnimInstance | 1 | 4 | **OLD SKELETON** — duplicate of above |
| `Content/Melodia/Characters/Melusina/ABP_Melusina_Current` | SK_Melusina_Skeleton | **465** | MelodiaLocomotionAnimInstance | 1 | **12** | ✅ **LIVE** — in use |
| `Content/Melodia/Characters/Melusina/ABP_Melusina_Current_BACKUP_20260729` | SK_Melusina_Skeleton | 465 | MelodiaLocomotionAnimInstance | 1 | 5 | Backup — archive only |
| `Content/Melodia/Characters/Melusina/ABP_Melusina_Current_Rollback` | SK_Melusina_Skeleton | 465 | MelodiaLocomotionAnimInstance | 1 | 11 | Rollback — archive only |
| `Content/Melodia/Characters/Melusina/V2Test/ABP_Melusina_Current_V2` | SK_MelusinaRigARP_V2Test | 433 | MelodiaLocomotionAnimInstance | 1 | 11 | **ARP SKELETON** — test strip only |
| `Content/Melodia/Characters/Melusina/V2Test/ABP_Melusina_JRPG_V2` | SK_MelusinaRigARP_V2Test | 433 | AnimInstance | 0 | 0 | **ARP SKELETON** — test strip only |
| `Content/Experiments/MelodiaJRPG/ABP_Melusina_JRPGPresentation` | SK_Melusina_Skeleton | 465 | AnimInstance | 0 | 2 | Battle presentation — SEPARATE |

**Verdict:** Two dead ABP copies target OLD 434-bone skeleton. Two V2Test ARP copies target 433-bone ARP skeleton (intentionally separate). Archive copies are safe.

### 1.2 BP_Melusina (3 variants)

| Path | Native Class | Parent Class | AnimClass Inheritance |
|------|-------------|--------------|----------------------|
| `Content/Characters/Melusina/BP_Melusina` | - | Character (Engine) | None (inherited from Character — UE4 Mannequin skeleton) |
| `Content/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation` | - | BP_PlayerUnitBase_C (JRPG template) | JRPG stock skeleton (UE4 Mannequin) |
| `Content/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter` | - | BP_JRPGCharacterBase_C (JRPG template) | **Set to ABP_Melusina_Current (just fixed this session)** |

**Verdict:** Three distinct BPs with three distinct parent classes. The `BP_Melusina` in `Characters/Melusina/` is a standalone exploration pawn. The two JRPG BPs are gameplay characters. Only `BP_MelusinaJRPGCharacter` is the live JRPG pawn.

### 1.3 Skeleton Inventory (4 variants)

| Path | Bones | In Use By |
|------|-------|-----------|
| `/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton` | **465** | ABP_Melusina_Current (LIVE) ✅ |
| `/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton_OLD` | 434 | ABP_Melusina, ABP_Melusina (Melodia/) — DEAD COPIES |
| `/Game/Melodia/Characters/Melusina/V2Test/SK_MelusinaRigARP_V2Test_Skeleton` | 433 | V2Test ABPs (cine/review strip only) |
| `/Game/TurnBasedJRPGTemplate/Meshes/UE4_Mannequin_Skeleton` | 68 | JRPG stock ABPs |

**Verdict:** Two obsolete skeletons still referenced by dead ABPs. The ARP skeleton is intentional for V2Test cine review.

---

## 2. Skeleton Mismatch Issues

### 2.1 (FIXED this session) BP_MelusinaJRPGCharacter

**Before fix:** Inherited `AnimClass` from `BP_JRPGCharacterBase_C` → stock UE4_Mannequin_Skeleton (68 bones)  
**Mesh:** SK_Melusina_Skeleton (465 bones)  
**Result:** Mismatch → T-pose in-game

**After fix:** `AnimClass` explicitly set to `ABP_Melusina_Current` (465-bone Melusina skeleton)  
**Result:** Match → animations play correctly

### 2.2 (Potential) BP_Melusina (Characters/Melusina/)

This BP inherits from Engine `Character` class. Character does not set an AnimClass by default — it uses whatever the SkeletalMeshComponent's mesh has. If the mesh assigned is `SK_Melusina` (465 bones) and AnimClass is left NULL, it will use the default `AnimInstance` which has no state machine. **No animations will play** unless AnimClass is set in the level or via C++.

**Risk:** If this BP is ever used as a pawn in a level without an explicit AnimClass override, Melusina will T-pose.

### 2.3 (No action needed) BP_MelusinaSwordsman_Presentation

Inherits from `BP_PlayerUnitBase_C` (JRPG template). Uses stock JRPG animations (68-bone UE4 Mannequin). **Intentional** — this is the battle presentation, not exploration.

---

## 3. Runtime Authority Drift

### 3.1 Animation Authority

| Authority | Expected | Actual | Drift |
|-----------|----------|--------|-------|
| Idle animation | `A_Melusina_Idle_Mocap_RootX` in ABP_Melusina_Current | ✅ Set this session | None |
| Locomotion blendspace | `BS_Melusina_Locomotion` with 4 samples | ✅ Wired this session | None |
| Glide state | `bIsGliding` variable → Glide state | ✅ Wired | None |
| Face rig | 68 FACS curves in ABP_Melusina_Current | ✅ Added this session | None |
| JRPG character AnimClass | `ABP_Melusina_Current` | ✅ Set this session | None |

### 3.2 Battle Authority

| Authority | Expected | Actual | Drift |
|-----------|----------|--------|-------|
| Battle encounter | `BP_BattleController::Show` no infinite loop | ✅ Fixed per owner this session | None |
| Battle presentation | `ABP_Melusina_JRPGPresentation` for battle | ✅ Separate ABP, 0 state machines | None |
| Battle UI | `BP_BattleUI` (JRPG template) | ✅ Used in battle | None |

### 3.3 Save/Load Authority

| Authority | Expected | Actual | Drift |
|-----------|----------|--------|-------|
| Runtime save game | `BP_JRPGSaveGame` + `BP_JRPGGameInstance` | ✅ JRPG template stock | None |
| Narrative record | `UMelodiaNarrativeSubsystem` | ✅ Custom Melodia subsystem | None |

### 3.4 Wardrobe Authority

| Authority | Expected | Actual | Drift |
|-----------|----------|--------|-------|
| Body ABP | `ABP_Melusina_Current` drives body + garments via Leader Pose | ✅ Same skeleton (465 bones) | None |
| Garment meshes | Skeletal meshes sharing `SK_Melusina_Skeleton` | ✅ Wardrobe plugin uses SetLeaderPoseComponent | None |
| Hair | Separate `ABP_Melusina_WaterHair` on separate 148-bone skeleton | ✅ Deliberately separate | None |

---

## 4. Drift Risk Register

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Dead ABP_Melusina copies confused for LIVE | Medium | Low | Rename or move to `_Archive/` |
| OLD skeleton (434 bones) referenced by dead ABPs | Low | Low | Archive or delete |
| BP_Melusina (Characters/) has no explicit AnimClass | Medium | Medium | Set AnimClass explicitly or don't use as pawn |
| ARP V2Test skeleton (433 bones) may be confused with LIVE | Low | Low | Keep in V2Test/ directory only |
| Duplicate `BP_BattleUI` in ThirdParty and local | Low | Low | Intentional — template vs override |
| `Content/Melodia/Characters/Melusina/_Archive/` | None | None | Archive — safe |

---

## 5. Summary

**Critical (fixed this session):**
- BP_MelusinaJRPGCharacter AnimClass → ABP_Melusina_Current ✅
- ABP_Melusina_Current state machine wired ✅
- Idle/Locomotion/Glide/Face all rebound ✅

**Needs attention (low priority):**
- `Content/Characters/Melusina/ABP_Melusina` → dead, points to OLD skeleton
- `Content/Melodia/Characters/Melusina/ABP_Melusina` → dead, points to OLD skeleton
- `Content/Characters/Melusina/BP_Melusina` → no AnimClass (may T-pose if used)

**No action needed:**
- V2Test/ ABPs — intentional for cine review strip
- Archive/ copies — safe
- Backup/Rollback copies — safe (but could be cleaned)
- Battle presentation ABP — separate, intentional
- All `_ThirdParty/` assets — JRPG template stock
