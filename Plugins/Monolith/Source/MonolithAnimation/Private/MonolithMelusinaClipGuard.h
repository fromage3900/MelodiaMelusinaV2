#pragma once

#include "CoreMinimal.h"

class UAnimationAsset;
class USkeleton;

// Editor assignment preflight, never a runtime pose correction.
namespace MonolithMelusinaClipGuard
{
	bool IsCanonicalSkeleton(const USkeleton* Skeleton);
	bool Validate(const UAnimationAsset* Asset, const USkeleton* TargetSkeleton, FString& Error);
}
