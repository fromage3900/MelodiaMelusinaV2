// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "MeshBlendShared.h"
#include "GameFramework/Actor.h"

#include "MeshBlendPCGHelper.generated.h"

/**
 * FMeshBlendPCGHelper provides helper functions to check if an actor is a PCG actor
 */
USTRUCT()
struct MESHBLEND_API FMeshBlendPCGHelper
{
	GENERATED_BODY()

	FMeshBlendPCGHelper()
	{
	}

	bool ActorIsPCGActor(const AActor* Actor);
	bool IsEnabled();

private:
	bool bIsPCGEnabled = false;
	bool bIsInitialized = false;
	UClass* PCGVolumeClass = nullptr;
	UClass* PCGPartitionActorClass = nullptr;
};
