// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AnimGraphNode_ACFBlendByMask.h"

#include "Animation/ACFBoneBlendMask.h"
#include "Kismet2/CompilerResultsLog.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(AnimGraphNode_ACFBlendByMask)

#define LOCTEXT_NAMESPACE "AnimGraphNode_ACFBlendByMask"

FText UAnimGraphNode_ACFBlendByMask::GetNodeTitle(ENodeTitleType::Type TitleType) const
{
	return LOCTEXT("NodeTitle", "ACF Blend by Mask");
}

FText UAnimGraphNode_ACFBlendByMask::GetTooltipText() const
{
	return LOCTEXT("NodeTooltip",
		"Blends a pose on top of the base pose using per-body-part alphas defined in a\n"
		"Bone Blend Mask data asset (branch points; deeper branches override parent alpha and space).\n"
		"The mask is a pin and can change at runtime: weights are smoothly interpolated\n"
		"to the new values over Blend Time.\n"
		"Blend modes: Override (lerp, can look stiff at partial alphas), Additive (pre-authored additive input),\n"
		"DynamicAdditive (treats the blend pose as a normal pose and layers its runtime additive delta - natural at partial alphas).");
}

FLinearColor UAnimGraphNode_ACFBlendByMask::GetNodeTitleColor() const
{
	return FLinearColor(0.2f, 0.8f, 0.2f);
}

FString UAnimGraphNode_ACFBlendByMask::GetNodeCategory() const
{
	return TEXT("Animation|ACF");
}

void UAnimGraphNode_ACFBlendByMask::ValidateAnimNodeDuringCompilation(USkeleton* ForSkeleton, FCompilerResultsLog& MessageLog)
{
	Super::ValidateAnimNodeDuringCompilation(ForSkeleton, MessageLog);

	// The mask is a pin, so it is allowed to be None at compile time. Only validate
	// the default value when one is assigned.
	if (Node.BlendMask && ForSkeleton)
	{
		if (!Node.BlendMask->Skeleton)
		{
			MessageLog.Warning(*FText::Format(LOCTEXT("MissingMaskSkeleton", "@@ Blend Mask '{0}' has no Skeleton assigned: branch bones will use a text field instead of the bone picker."),
				FText::FromString(Node.BlendMask->GetName())).ToString(), this);
		}
		else if (Node.BlendMask->Skeleton != ForSkeleton)
		{
			MessageLog.Warning(*FText::Format(LOCTEXT("MaskSkeletonMismatch", "@@ Blend Mask '{0}' uses skeleton '{1}' but this AnimBP targets '{2}'. Runtime uses bone names, so this may still work if the hierarchies match."),
				FText::FromString(Node.BlendMask->GetName()),
				FText::FromString(Node.BlendMask->Skeleton->GetName()),
				FText::FromString(ForSkeleton->GetName())).ToString(), this);
		}

		for (const FACFBoneBlendBranch& Branch : Node.BlendMask->Branches)
		{
			if (Branch.Bone.BoneName != NAME_None && ForSkeleton->GetReferenceSkeleton().FindBoneIndex(Branch.Bone.BoneName) == INDEX_NONE)
			{
				MessageLog.Warning(*FText::Format(LOCTEXT("MissingBone", "@@ bone '{0}' from Blend Mask '{1}' does not exist on the target skeleton."),
					FText::FromName(Branch.Bone.BoneName), FText::FromString(Node.BlendMask->GetName())).ToString(), this);
			}
		}
	}
}

void UAnimGraphNode_ACFBlendByMask::PreloadRequiredAssets()
{
	if (Node.BlendMask)
	{
		PreloadObject(Node.BlendMask);
	}

	Super::PreloadRequiredAssets();
}

#undef LOCTEXT_NAMESPACE
