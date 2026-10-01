// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/ACFBoneBlendMask.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(ACFBoneBlendMask)

USkeleton* UACFBoneBlendMask::GetSkeleton(bool& bInvalidSkeletonIsError, const IPropertyHandle* PropertyHandle)
{
	bInvalidSkeletonIsError = false;
	return Skeleton;
}
