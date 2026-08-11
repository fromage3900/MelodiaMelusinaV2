// Copyright 2024 Tore Lervik. All Rights Reserved.

#include "AutoBlendUserData.h"
#include "Landscape.h"
#include "MeshBlendShared.h"
#include "Engine/Engine.h"

bool FUAutoBlendHelper::TryGetBlendOptionFromActorTag(const AActor* Actor, EAutoBlendOption& AutoBlendOption)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);
	if (Actor->ActorHasTag(GName_Disabled))
	{
		AutoBlendOption = Disabled;
		return true;
	}

	if (Actor->ActorHasTag(GName_AutoBlendSmall))
	{
		AutoBlendOption = Small;
		return true;
	}

	if (Actor->ActorHasTag(GName_AutoBlendMedium))
	{
		AutoBlendOption = Medium;
		return true;
	}

	if (Actor->ActorHasTag(GName_AutoBlendLarge))
	{
		AutoBlendOption = Large;
		return true;
	}

	if (Actor->ActorHasTag(GName_AutoBlendExtraLarge))
	{
		AutoBlendOption = Extra_Large;
		return true;
	}

	const AActor* Owner = Actor->GetOwner();

	if (Owner && TryGetBlendOptionFromActorTag(Owner, AutoBlendOption))
	{
		return true;
	}

	return false;
}

bool FUAutoBlendHelper::TryGetBlendOptionFromComponentTag(const UMeshComponent* MeshComponent, EAutoBlendOption& AutoBlendOption)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);
	if (MeshComponent->ComponentHasTag(GName_Disabled))
	{
		AutoBlendOption = Disabled;
		return true;
	}

	if (MeshComponent->ComponentHasTag(GName_AutoBlendSmall))
	{
		AutoBlendOption = Small;
		return true;
	}

	if (MeshComponent->ComponentHasTag(GName_AutoBlendMedium))
	{
		AutoBlendOption = Medium;
		return true;
	}

	if (MeshComponent->ComponentHasTag(GName_AutoBlendLarge))
	{
		AutoBlendOption = Large;
		return true;
	}

	if (MeshComponent->ComponentHasTag(GName_AutoBlendExtraLarge))
	{
		AutoBlendOption = Extra_Large;
		return true;
	}

	return false;
}


/* Returns the largest blend size an actor can have. Used for deciding activation distance. */
EAutoBlendOption FUAutoBlendHelper::GetLargestAutoBlendState(const AActor* Actor)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);
	EAutoBlendOption ResultState = Small;

	if (!TryGetBlendOptionFromActorTag(Actor, ResultState))
	{
		for (UActorComponent* Component : Actor->GetComponents())
		{
			if (const UMeshComponent* MeshComponent = Cast<UMeshComponent>(Component))
			{
				EAutoBlendOption ComponentResultState = Small;

				if (TryGetBlendOptionFromComponentTag(MeshComponent, ComponentResultState) && ComponentResultState > ResultState && ComponentResultState != Disabled)
				{
					ResultState = ComponentResultState;
				}

				if (const UAutoBlendUserData* AutoBlendUserData = FMeshBlendShared::GetAutoBlendUserData(MeshComponent))
				{
					if (AutoBlendUserData->AutoBlendOption != Disabled && AutoBlendUserData->AutoBlendOption > ResultState)
					{
						ResultState = AutoBlendUserData->AutoBlendOption;
					}
				}
			}
		}
	}

	return ResultState;
}

bool FUAutoBlendHelper::DoesItBlend(const AActor* Actor)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	if (Actor->IsA(ALandscapeProxy::StaticClass()))
	{
		// Landscapes are handled manually
		return false;
	}

	EAutoBlendOption AutoBlendState = Small;

	if (TryGetBlendOptionFromActorTag(Actor, AutoBlendState))
	{
		return AutoBlendState != Disabled;
	}

	for (UActorComponent* Component : Actor->GetComponents())
	{
		if (const UMeshComponent* MeshComponent = Cast<UMeshComponent>(Component))
		{
			if (TryGetBlendOptionFromComponentTag(MeshComponent, AutoBlendState) && AutoBlendState != Disabled)
			{
				return true;
			}

			if (FMeshBlendShared::GetAutoBlendUserData(MeshComponent))
			{
				return true;
			}
		}
	}

	return false;
}
