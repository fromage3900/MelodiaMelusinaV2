// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Animation/BoneReference.h"
#include "Engine/DataAsset.h"
#include "Interfaces/Interface_BoneReferenceSkeletonProvider.h"
#include "ACFBoneBlendMask.generated.h"

class USkeleton;

UENUM(BlueprintType)
enum class EACFMaskBlendSpace : uint8
{
	LocalSpace,
	MeshSpace
};

/** Editor/runtime branch entry. Not BlueprintType because FBoneReference is animation-internal only. */
USTRUCT()
struct FACFBoneBlendBranch
{
	GENERATED_BODY()

	/** Branch point bone: the alpha is applied to this bone and inherited by all its children,
	 * unless a deeper branch point overrides it. */
	UPROPERTY(EditAnywhere, Category = ACF)
	FBoneReference Bone;

	/** Blend alpha used for this branch of the skeleton. */
	UPROPERTY(EditAnywhere, Category = ACF, meta = (ClampMin = 0.0, ClampMax = 1.0, UIMin = 0.0, UIMax = 1.0))
	float Alpha = 1.f;

	/** Space used to override-blend this branch. Additive blending always uses local space. */
	UPROPERTY(EditAnywhere, Category = ACF)
	EACFMaskBlendSpace BlendSpace = EACFMaskBlendSpace::LocalSpace;
};

/**
 * Defines per-body-part blend alphas through a list of branch points.
 * Every bone inherits the alpha and blend space of its closest ancestor branch point, so deeper
 * branch points have priority over parent ones (e.g. spine_02 = 0.5 and clavicle_l = 0.7
 * means the whole left arm blends at 0.7 while the rest of the upper body blends at 0.5).
 * Bones with no branch point among their ancestors are not affected at all.
 */
UCLASS(BlueprintType)
class CHARACTERCONTROLLER_API UACFBoneBlendMask : public UDataAsset, public IBoneReferenceSkeletonProvider
{
	GENERATED_BODY()

public:
	/** Skeleton used to populate the bone picker for branch entries. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	TObjectPtr<USkeleton> Skeleton;

	UPROPERTY(EditAnywhere, Category = ACF)
	TArray<FACFBoneBlendBranch> Branches;

	// IBoneReferenceSkeletonProvider
	virtual USkeleton* GetSkeleton(bool& bInvalidSkeletonIsError, const IPropertyHandle* PropertyHandle) override;
};
