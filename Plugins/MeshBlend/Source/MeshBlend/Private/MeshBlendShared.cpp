// Copyright 2024 Tore Lervik. All Rights Reserved.

#include "MeshBlendShared.h"

#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Kismet/GameplayStatics.h"

bool FMeshBlendShared::IsOverProcessBudget(const double MaxDuration)
{
	return FPlatformTime::Seconds() > MaxDuration;
}

FActorBounds FMeshBlendShared::GetBounds(const AActor* Actor)
{
	FVector Origin;
	FVector BoxExtent;
	Actor->GetActorBounds(false, Origin, BoxExtent);
	FActorBounds ActorBounds;
	ActorBounds.Origin = Origin;
	ActorBounds.Radius = BoxExtent.Length();
	return ActorBounds;
}

const UAutoBlendUserData* FMeshBlendShared::GetAutoBlendUserData(const UMeshComponent* MeshComponent)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	if (const UStaticMeshComponent* StaticMeshComponent = Cast<UStaticMeshComponent>(MeshComponent))
	{
		if (UStaticMesh* StaticMesh = StaticMeshComponent->GetStaticMesh())
		{
			if (const UAutoBlendUserData* AutoBlendUserData = Cast<UAutoBlendUserData>(StaticMesh->GetAssetUserDataOfClass(UAutoBlendUserData::StaticClass())))
			{
				return AutoBlendUserData;
			}
		}
	}

	if (const USkeletalMeshComponent* SkeletalMeshComponent = Cast<USkeletalMeshComponent>(MeshComponent))
	{
		if (USkeletalMesh* SkeletalMesh = SkeletalMeshComponent->GetSkeletalMeshAsset())
		{
			if (const UAutoBlendUserData* AutoBlendUserData = Cast<UAutoBlendUserData>(SkeletalMesh->GetAssetUserDataOfClass(UAutoBlendUserData::StaticClass())))
			{
				return AutoBlendUserData;
			}
		}
	}

	return nullptr;
}

FBoxSphereBounds FMeshBlendShared::GetMeshBounds(UMeshComponent* MeshComponent)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	if (const UStaticMeshComponent* StaticMeshComponent = Cast<UStaticMeshComponent>(MeshComponent))
	{
		if (const UStaticMesh* StaticMesh = StaticMeshComponent->GetStaticMesh())
		{
			return StaticMesh->GetBounds();
		}
	}

	if (const USkeletalMeshComponent* SkeletalMeshComponent = Cast<USkeletalMeshComponent>(MeshComponent))
	{
		if (const USkeletalMesh* SkeletalMesh = SkeletalMeshComponent->GetSkeletalMeshAsset())
		{
			return SkeletalMesh->GetBounds();
		}
	}

	return FBoxSphereBounds();
}

bool FMeshBlendShared::GetCurrentCameraLocation(const UWorld* World, FVector& Location)
{
	if (World)
	{
		auto ViewLocations = World->ViewLocationsRenderedLastFrame;

		if (ViewLocations.Num() > 0)
		{
			Location = ViewLocations[0];
			return true;
		}
	}

	return false;
}
