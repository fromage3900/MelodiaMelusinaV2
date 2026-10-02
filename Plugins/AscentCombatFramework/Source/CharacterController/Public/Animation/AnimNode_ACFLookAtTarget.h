// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "BoneControllers/AnimNode_LookAt.h"
#include "BoneControllers/AnimNode_SkeletalControlBase.h"
#include <CommonAnimTypes.h>

#include "AnimNode_ACFLookAtTarget.generated.h"

/**
 *
 */

class USkeletalMeshComponent;

USTRUCT(BlueprintType)
struct CHARACTERCONTROLLER_API FAnimNode_ACFLookAtTarget : public FAnimNode_SkeletalControlBase {
    GENERATED_BODY()

    /** Name of bone to control. This is the main bone chain to modify from. **/
    UPROPERTY(EditAnywhere, Category = SkeletalControl, meta =(PinHiddenByDefault))
    FBoneReference BoneToModify;
   
	FBoneSocketTarget LookAtTarget;

    UPROPERTY(EditAnywhere, Category = SkeletalControl)
    FAxis LookAt_Axis;

    /** Whether or not to use Look up axis */
    UPROPERTY(EditAnywhere, Category = SkeletalControl)
    bool bUseLookUpAxis; 

    UPROPERTY(EditAnywhere, Category = SkeletalControl)
    FAxis LookUp_Axis;

     /*Where to look when there is no target. By Default will be the Actor forward vector*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = SkeletalControl, meta = (PinHiddenByDefault))
    FVector NoTargetOffset;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = SkeletalControl, meta = (PinHiddenByDefault))
    APawn* Owner;

    /** Look at Clamp value in degrees - if your look at axis is Z, only X, Y degree of clamp will be used */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = SkeletalControl, meta = (PinHiddenByDefault))
    float LookAtClamp;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = SkeletalControl, meta = (PinHiddenByDefault))
    float InterpolationSpeed;



public:
    FAnimNode_ACFLookAtTarget();




    // FAnimNode_Base interface
    virtual void UpdateInternal(const FAnimationUpdateContext& Context) override;
    virtual void Initialize_AnyThread(const FAnimationInitializeContext& Context) override;
    // End of FAnimNode_Base interface

    // FAnimNode_SkeletalControlBase interface
    virtual void EvaluateComponentSpaceInternal(FComponentSpacePoseContext& Context) override;
    virtual void EvaluateSkeletalControl_AnyThread(FComponentSpacePoseContext& Output, TArray<FBoneTransform>& OutBoneTransforms) override;
    virtual bool IsValidToEvaluate(const USkeleton* Skeleton, const FBoneContainer& RequiredBones) override;
    // End of FAnimNode_SkeletalControlBase interface
    FVector GetCachedTargetLocation() const { return CachedCurrentTargetLocation; }

private:
    // FAnimNode_SkeletalControlBase interface
    virtual void InitializeBoneReferences(const FBoneContainer& RequiredBones) override;
    // End of FAnimNode_SkeletalControlBase interface


    /** Debug transient data */
    FVector CurrentLookAtLocation;

    /** Current Target Location */
    FVector CurrentTargetLocation;
    FVector PreviousTargetLocation;

    /** Current Alpha */
    float AccumulatedInterpoolationTime;
    FVector CachedCurrentTargetLocation;
    FQuat LerpedDelta;
    float DeltaTime;
protected:
    virtual void ModifyPoseFromDeltaRotation(FComponentSpacePoseContext& Output, TArray<FBoneTransform>& OutBoneTransforms, FTransform& InOutBoneToModifyTransform, const FQuat& DeltaRotation);
};
