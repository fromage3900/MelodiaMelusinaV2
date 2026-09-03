// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ChunkedProcessingQueue.h"
#include "MeshBlendShared.h"
#include "Containers/Queue.h"
#include "GameFramework/Actor.h"
#include "MeshBlendPooledActors.generated.h"

DECLARE_DELEGATE_OneParam(FRefreshActorDelegate, AActor*);

/**
 * FMeshBlendPooledActors is a structure that manages a pool of actors for processing.
 * It checks the UMeshComponent of each actor to determine if it should be updated.
 */
USTRUCT()
struct MESHBLEND_API FMeshBlendPooledActors
{
	GENERATED_BODY()

	FMeshBlendPooledActors()
	{
	}

	FRefreshActorDelegate OnRefreshActor;

	void AddActor(AActor* Actor);
	bool ProcessActorQueue(const double MaxProcessDuration);
	void Empty();

private:
	TChunkedProcessingQueue<TWeakObjectPtr<AActor>, 2048> ActorProcessingQueue;
	int IterationIndex = 0;
	int ComponentIndex = 0;

	UPROPERTY()
	TMap<TWeakObjectPtr<UMeshComponent>, int> BoundMeshComponents;

	bool CheckIfActorShouldUpdate(const AActor* Actor, const double MaxProcessDuration);
	bool CheckMeshComponent(UMeshComponent* Component);
};
