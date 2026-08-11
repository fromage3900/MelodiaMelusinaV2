// Copyright 2024 Tore Lervik. All Rights Reserved.

#include "MeshBlendPooledActors.h"

#include "PrimitiveDataHelper.h"
#include "Components/InstancedStaticMeshComponent.h"

void FMeshBlendPooledActors::AddActor(AActor* Actor)
{
	ActorProcessingQueue.AddUnique(Actor);
}

bool FMeshBlendPooledActors::ProcessActorQueue(const double MaxProcessDuration)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	IterationIndex = (IterationIndex + 1) % 100;

	if (IterationIndex != 0)
	{
		return true;
	}

	TWeakObjectPtr<AActor> WeakActor;
	bool bResult = true;

	while (ActorProcessingQueue.Next(WeakActor))
	{
		if (!WeakActor.IsValid())
		{
			ActorProcessingQueue.RemoveCurrent();
			continue;
		}

		AActor* Actor = WeakActor.Get();

		if (CheckIfActorShouldUpdate(Actor, MaxProcessDuration))
		{
			TRACE_CPUPROFILER_EVENT_SCOPE_STR("OnRefreshActor");
			OnRefreshActor.ExecuteIfBound(Actor);
		}

		if (FMeshBlendShared::IsOverProcessBudget(MaxProcessDuration))
		{
			bResult = false;
			break;
		}
	}

	ActorProcessingQueue.KeepCurrentAsNext();
	return bResult;
}

void FMeshBlendPooledActors::Empty()
{
	IterationIndex = 0;
	ComponentIndex = 0;
	ActorProcessingQueue.Empty();
	BoundMeshComponents.Empty();
}

bool FMeshBlendPooledActors::CheckIfActorShouldUpdate(const AActor* Actor, const double MaxProcessDuration)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);
	SCOPE_CYCLE_UOBJECT(Actor, Actor);

	bool bShouldRefresh = false;

	int32 CurrentComponentIndex = 0;

	for (UActorComponent* Component : Actor->GetComponents())
	{
		if (CurrentComponentIndex < ComponentIndex)
		{
			CurrentComponentIndex++;
			continue;
		}

		SCOPE_CYCLE_UOBJECT(Component, Component);

		if (FMeshBlendShared::IsOverProcessBudget(MaxProcessDuration))
		{
			ComponentIndex = CurrentComponentIndex;
			return bShouldRefresh;
		}

		UMeshComponent* MeshComponent = Cast<UMeshComponent>(Component);
		CurrentComponentIndex++;

		if (!MeshComponent)
		{
			continue;
		}

		if (CheckMeshComponent(MeshComponent))
		{
			bShouldRefresh = true;
		}
	}

	ComponentIndex = 0;
	return bShouldRefresh;
}

bool FMeshBlendPooledActors::CheckMeshComponent(UMeshComponent* Component)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	int InstanceCount = 1;

	if (const UInstancedStaticMeshComponent* InstancedStaticMeshComponent = Cast<UInstancedStaticMeshComponent>(Component))
	{
		InstanceCount = InstancedStaticMeshComponent->GetInstanceCount();
	}

	if (!BoundMeshComponents.Contains(Component))
	{
		BoundMeshComponents.Add(Component, InstanceCount);

		if (Component->ComponentHasTag(GName_AutoBlendHasPrimitiveData))
		{
			return false;
		}

		return true;
	}

	if (BoundMeshComponents[Component] != InstanceCount)
	{
		BoundMeshComponents[Component] = InstanceCount;
		Component->ComponentTags.RemoveSwap(GName_AutoBlendHasPrimitiveData);
		return true;
	}

	return false;
}
