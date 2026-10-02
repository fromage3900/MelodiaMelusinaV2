// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/AnimNode_ACFBlendPosesByGameplayTag.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(AnimNode_ACFBlendPosesByGameplayTag)

int32 FAnimNode_ACFBlendPosesByGameplayTag::GetActiveChildIndex()
{
	const FGameplayTagContainer& CurrentActiveTags = GetActiveGameplayTags();
	const TArray<FGameplayTag>& CurrentTags = GetGameplayTags();

	for (int32 i = 0; i < CurrentTags.Num(); ++i)
	{
		if (CurrentTags[i].IsValid() && CurrentActiveTags.HasTag(CurrentTags[i]))
		{
			return FMath::Clamp(i + 1, 0, BlendPose.Num() - 1);
		}
	}

	return 0;
}

const FGameplayTagContainer& FAnimNode_ACFBlendPosesByGameplayTag::GetActiveGameplayTags() const
{
	return GET_ANIM_NODE_DATA(FGameplayTagContainer, ActiveGameplayTags);
}

const TArray<FGameplayTag>& FAnimNode_ACFBlendPosesByGameplayTag::GetGameplayTags() const
{
	return GET_ANIM_NODE_DATA(TArray<FGameplayTag>, GameplayTags);
}
