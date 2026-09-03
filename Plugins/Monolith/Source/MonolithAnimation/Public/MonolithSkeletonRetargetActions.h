#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"
#include "Animation/Skeleton.h" // EBoneTranslationRetargetingMode (namespaced enum) — parse/echo by name

class USkeleton;
class UIKRigDefinition;
class UIKRigController;
struct FIKRigSolverBase;
struct FIKRigBoneSettingsBase;

/**
 * Legacy per-bone translation retargeting authoring (T1-R4) +
 * IK-Rig per-solver per-bone settings authoring (T2-1).
 *
 * --- T1-R4 (USkeleton translation retargeting) ---
 * Wraps the plain ENGINE_API surface on USkeleton:
 *   - SetBoneTranslationRetargetingMode(int32 BoneIndex, EBoneTranslationRetargetingMode::Type, bool bChildrenToo)
 *   - GetBoneTranslationRetargetingMode(int32 BoneTreeIdx, bool) const
 *
 * These control how a bone's animated translation is interpreted when an
 * animation authored for one skeleton plays on a differently-proportioned one
 * (the classic "wrong-height pelvis / sliding feet" cross-skeleton problem).
 *
 * EBoneTranslationRetargetingMode is a NAMESPACED enum
 * (`namespace EBoneTranslationRetargetingMode { enum Type : int }`,
 * Skeleton.h:69-86) — its five members are Animation / Skeleton /
 * AnimationScaled / AnimationRelative / OrientAndScale. Parsed/echoed by
 * name (never by raw int) via ParseTranslationRetargetMode /
 * TranslationRetargetModeToString.
 *
 * The `biped_locomotion` preset is a thin convenience layer: a role-keyed map
 * (root -> Animation, pelvis -> AnimationScaled, ik_* -> Animation,
 * everything else -> Skeleton) applied through the same generic setter.
 *
 * --- T2-1 (IK Rig per-solver per-bone settings) ---
 * In UE 5.6+ the IK Rig solver stack was refactored from UObject solvers to
 * UStruct (FInstancedStruct) solvers. Per-bone settings are now SOLVER-SCOPED:
 * each solver in the stack stores its own `FIKRigBoneSettingsBase`-derived
 * struct per bone, and the concrete struct's fields are solver-specific
 * (e.g. FullBodyIK exposes rotation stiffness / per-axis limits; another
 * solver exposes different fields). There is no single flat per-bone settings
 * struct — the wishlist's old `FIKRigBoneSetting` no longer exists.
 *
 * Access path (matches the engine's own FIKRigEditorController, see
 * IKRigEditorController.cpp:972-1016):
 *   UIKRigController::GetController(rig)
 *     -> GetSolverAtIndex(solverIdx) -> FIKRigSolverBase*            (the solver)
 *        -> UsesCustomBoneSettings()                                 (does it support per-bone settings?)
 *        -> GetBoneSettingsType() -> const UScriptStruct*            (the CONCRETE struct type to walk reflectively)
 *        -> GetBoneSettings(BoneName) -> FIKRigBoneSettingsBase*     (the LIVE struct memory in the asset)
 *
 * The deprecated UIKRigController::GetBoneSettings(name, solverIdx) (returns a
 * UObject*, UE_DEPRECATED(5.6)) is NOT used. Bone-setting entries are created
 * with UIKRigController::AddBoneSetting(name, solverIdx) (guarded by
 * CanAddBoneSetting). Because the concrete fields differ per solver, both
 * actions read/write fields REFLECTIVELY off the returned base pointer using
 * the concrete UScriptStruct: writes via FProperty::ImportText_Direct (the
 * proven set_cdo_property scalar path), reads via FMonolithReflectionReader.
 *
 * All actions are editor/game-thread, synchronous, single-call. Writes wrap the
 * mutation in a transaction and MarkPackageDirty(); reads skip the transaction.
 */
class FMonolithSkeletonRetargetActions
{
public:
	/** Register the T1-R4 + T2-1 actions with the tool registry. */
	static void RegisterActions(FMonolithToolRegistry& Registry);

	// --- T1-R4: per-bone translation retargeting ---
	static FMonolithActionResult HandleSetBoneTranslationRetargeting(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetBoneTranslationRetargeting(const TSharedPtr<FJsonObject>& Params);

	// --- T2-1: IK-Rig per-solver per-bone settings ---
	static FMonolithActionResult HandleSetIkRigBoneSettings(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetIkRigBoneSettings(const TSharedPtr<FJsonObject>& Params);

	/**
	 * Parse a mode string (case-insensitive) into the namespaced enum value.
	 * Accepts: Animation | Skeleton | AnimationScaled | AnimationRelative | OrientAndScale.
	 * Returns false (Out untouched) if the string matches no member.
	 */
	static bool ParseTranslationRetargetMode(const FString& In, EBoneTranslationRetargetingMode::Type& Out);
};
