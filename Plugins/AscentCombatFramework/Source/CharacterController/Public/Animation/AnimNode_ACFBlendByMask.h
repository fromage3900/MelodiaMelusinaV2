// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimNodeBase.h"
#include "Animation/ACFBoneBlendMask.h"
#include "AnimNode_ACFBlendByMask.generated.h"

class UACFBoneBlendMask;
class UAnimSequence;

UENUM(BlueprintType)
enum class EACFMaskBlendMode : uint8
{
	/** Lerps between the base pose and the blend pose per-bone, using the branch alphas.
	 * At partial alphas the limbs are dragged towards the blend pose's absolute orientation, which can look stiff. */
	Override,
	/** The blend pose is treated as an already-authored local space additive delta, accumulated on top of the base pose scaled by the branch alphas. */
	Additive,
	/** The blend pose is a normal full pose: its additive delta relative to the base pose is computed at runtime (like Make Dynamic Additive)
	 * and accumulated scaled by the branch alphas. Preserves the base motion, so partial alphas stay natural instead of stiff. */
	DynamicAdditive
};

/** Neutral pose DynamicAdditive subtracts from the blend pose to build the additive delta. Editor-only setting (no pin). */
UENUM(BlueprintType)
enum class EACFMaskReferencePose : uint8
{
	/** Skeleton reference pose (bind / T-pose). The blend pose is made additive relative to bind. */
	SkeletonReferencePose UMETA(DisplayName = "T-Pose (Skeleton Ref)"),
	/** The live base pose. delta = blend - base, so at full alpha the blend pose fully overrides. */
	CurrentBasePose UMETA(DisplayName = "Current Anim Pose"),
	/** First frame of a chosen animation, used as the neutral reference. */
	AnimSequenceFirstFrame UMETA(DisplayName = "Anim Sequence (First Frame)")
};

/**
 * Blends a pose on top of a base pose with per-body-part alphas defined in a
 * UACFBoneBlendMask data asset (branch points; deeper branch points have priority
 * over parent ones). The mask is exposed as a pin and can be swapped at runtime:
 * the per-bone weights are smoothly interpolated to the new values over BlendTime
 * instead of snapping.
 */
USTRUCT(BlueprintInternalUseOnly)
struct CHARACTERCONTROLLER_API FAnimNode_ACFBlendByMask : public FAnimNode_Base
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Links)
	FPoseLink BasePose;

	/** Pose blended on top of the base pose using the branch alphas from the blend mask. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Links)
	FPoseLink BlendPose;

	/**
	 * Branch points (bone + alpha) defining which body parts are affected by the blend pose and how much.
	 * Can change at runtime: weights are smoothly blended towards the new values over BlendTime.
	 * When None, the blend pose is smoothly blended out.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Config, meta = (PinShownByDefault))
	TObjectPtr<UACFBoneBlendMask> BlendMask;

	/** Time used to interpolate the per-bone weights when the blend mask (or its values) changes. 0 = instant. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Config, meta = (ClampMin = 0.0, PinHiddenByDefault))
	float BlendTime = 0.25f;

	/** How the blend pose is applied on top of the base pose. Driven by the overlay data via the
	 * generic layer's CurrentBlendMode: connect it to this pin. Defaults to DynamicAdditive when
	 * left unconnected. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Config, meta = (PinShownByDefault))
	EACFMaskBlendMode BlendMode = EACFMaskBlendMode::DynamicAdditive;

	/** Neutral pose used by DynamicAdditive to build the additive delta (DynamicAdditive only). Editor setting, no pin. */
	UPROPERTY(EditAnywhere, Category = Config)
	EACFMaskReferencePose ReferencePoseSource = EACFMaskReferencePose::SkeletonReferencePose;

	/** Animation whose first frame is used as the neutral reference when ReferencePoseSource is AnimSequenceFirstFrame. */
	UPROPERTY(EditAnywhere, Category = Config, meta = (EditCondition = "ReferencePoseSource == EACFMaskReferencePose::AnimSequenceFirstFrame", EditConditionHides))
	TObjectPtr<UAnimSequence> ReferencePoseAnimation;

	/**
	 * Max LOD that this node is allowed to run.
	 * For example if you have LODThreshold to be 2, it will run until LOD 2 (based on 0 index)
	 * when the component LOD becomes 3, it will stop update/evaluate.
	 */
	UPROPERTY(EditAnywhere, Category = Performance, meta = (DisplayName = "LOD Threshold"))
	int32 LODThreshold = INDEX_NONE;

private:
	// Weights resolved from the current blend mask, per compact pose bone index
	TArray<float> TargetBoneWeights;

	// Blend spaces resolved from the current blend mask, per compact pose bone index
	TArray<EACFMaskBlendSpace> TargetBlendSpaces;

	// Weights actually used for blending, interpolated towards TargetBoneWeights
	TArray<float> CurrentBoneWeights;

	// Highest current weight, used for relevancy, curves and debug
	float MaxCurrentWeight = 0.f;

	uint16 RequiredBonesSerialNumber = 0;

	bool bBlendPoseRelevant = false;

	// When true, current weights snap to their target on the next update (set on initialization and LOD changes)
	bool bSnapWeights = true;

public:
	FAnimNode_ACFBlendByMask() = default;

	// FAnimNode_Base interface
	virtual void Initialize_AnyThread(const FAnimationInitializeContext& Context) override;
	virtual void CacheBones_AnyThread(const FAnimationCacheBonesContext& Context) override;
	virtual void Update_AnyThread(const FAnimationUpdateContext& Context) override;
	virtual void Evaluate_AnyThread(FPoseContext& Output) override;
	virtual void GatherDebugData(FNodeDebugData& DebugData) override;
	virtual int32 GetLODThreshold() const override { return LODThreshold; }
	// End of FAnimNode_Base interface

private:
	// Resolves TargetBoneWeights from the current blend mask
	void RebuildTargetBoneWeights(const FBoneContainer& RequiredBones);
};
