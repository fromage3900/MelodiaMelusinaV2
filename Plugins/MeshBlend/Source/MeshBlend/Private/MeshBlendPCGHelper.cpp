// Copyright 2024 Tore Lervik. All Rights Reserved.

#include "MeshBlendPCGHelper.h"

static TAutoConsoleVariable<bool> CVarMeshBlendPcg(
	TEXT("r.MeshBlend.PCG"),
	true,
	TEXT("Enable/Disable helper functions that hook into PCG systems."));

bool FMeshBlendPCGHelper::ActorIsPCGActor(const AActor* Actor)
{
	if (!IsEnabled())
	{
		return false;
	}

	if (!Actor)
	{
		return false;
	}

	if (Actor->IsA(PCGVolumeClass) || Actor->IsA(PCGPartitionActorClass))
	{
		return true;
	}

	return false;
}

bool FMeshBlendPCGHelper::IsEnabled()
{
	if (!CVarMeshBlendPcg.GetValueOnGameThread())
	{
		return false;
	}

	if (!bIsInitialized)
	{
		PCGVolumeClass = FindObject<UClass>(nullptr, TEXT("PCG.PCGVolume"));
		PCGPartitionActorClass = FindObject<UClass>(nullptr, TEXT("PCG.PCGPartitionActor"));
		bIsPCGEnabled = (PCGVolumeClass != nullptr && PCGPartitionActorClass != nullptr);
		bIsInitialized = true;
	}

	return bIsPCGEnabled;
}
