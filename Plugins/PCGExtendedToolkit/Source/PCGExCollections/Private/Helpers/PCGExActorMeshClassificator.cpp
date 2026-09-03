// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Helpers/PCGExActorMeshClassificator.h"

#include "GameFramework/Actor.h"

#pragma region UPCGExActorMeshClassificator

bool UPCGExActorMeshClassificator::ShouldClassifyAsMesh_Implementation(AActor* Actor) const
{
	return false;
}

#pragma endregion

#pragma region UPCGExDefaultActorMeshClassificator

UPCGExDefaultActorMeshClassificator::UPCGExDefaultActorMeshClassificator()
{
	IncludeClasses.Add(TSoftClassPtr<AActor>(FSoftObjectPath(TEXT("/Script/Engine.StaticMeshActor"))));
}

bool UPCGExDefaultActorMeshClassificator::ShouldClassifyAsMesh_Implementation(AActor* Actor) const
{
	if (!Actor)
	{
		return false;
	}

	// Exclude takes priority over include
	if (ExcludeClasses.Num() > 0)
	{
		for (const TSoftClassPtr<AActor>& ClassPtr : ExcludeClasses)
		{
			if (const UClass* C = ClassPtr.Get())
			{
				if (Actor->IsA(C))
				{
					return false;
				}
			}
		}
	}
	if (ExcludeTags.Num() > 0)
	{
		for (const FName& Tag : ExcludeTags)
		{
			if (Actor->Tags.Contains(Tag))
			{
				return false;
			}
		}
	}

	// Must match at least one include rule
	if (IncludeClasses.Num() > 0)
	{
		for (const TSoftClassPtr<AActor>& ClassPtr : IncludeClasses)
		{
			if (const UClass* C = ClassPtr.Get())
			{
				if (Actor->IsA(C))
				{
					return true;
				}
			}
		}
	}
	if (IncludeTags.Num() > 0)
	{
		for (const FName& Tag : IncludeTags)
		{
			if (Actor->Tags.Contains(Tag))
			{
				return true;
			}
		}
	}

	return false;
}

#pragma endregion
