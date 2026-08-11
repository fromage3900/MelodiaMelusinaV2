#include "MelodiaWaterGameplayDeviceAnchor.h"

#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "MelodiaWaterGameplayControllerComponent.h"

AMelodiaWaterGameplayDeviceAnchor::AMelodiaWaterGameplayDeviceAnchor()
{
	PrimaryActorTick.bCanEverTick = false;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	InteractionVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("InteractionVolume"));
	InteractionVolume->SetupAttachment(Root);
	InteractionVolume->SetBoxExtent(FVector(100.0f, 100.0f, 100.0f));
	InteractionVolume->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	InteractionVolume->SetGenerateOverlapEvents(true);
	ControllerComponent = CreateDefaultSubobject<UMelodiaWaterGameplayControllerComponent>(TEXT("WaterGameplayController"));
	Tags.Add(TEXT("MelodiaWaterGameplay"));
	Tags.Add(TEXT("NoMerging"));
}

void AMelodiaWaterGameplayDeviceAnchor::InitializeFromPCGPoint(FPCGPoint Point, const UPCGMetadata* Metadata)
{
	if (StableActorId.IsNone())
	{
		StableActorId = FName(*FString::Printf(TEXT("WaterDevice_%08X"), static_cast<uint32>(Point.Seed)));
	}
	SetActorTransform(Point.Transform);
	Tags.AddUnique(FName(*FString::Printf(TEXT("StableId_%s"), *StableActorId.ToString())));
	Tags.AddUnique(TEXT("GameplayDataLayer_DL_Musical_HeroGameplay"));
	Tags.AddUnique(TEXT("NoMerging"));
	for (const FName Tag : Tags)
	{
		const FString Value = Tag.ToString();
		if (Value.StartsWith(TEXT("WaterStableId_")))
		{
			StableActorId = FName(*Value.RightChop(14));
		}
		else if (Value.StartsWith(TEXT("WaterRole_")))
		{
			GameplayRole = FName(*Value.RightChop(10));
		}
		else if (Value.StartsWith(TEXT("WaterNetwork_")))
		{
			WaterNetworkId = FName(*Value.RightChop(13));
		}
		else if (Value.StartsWith(TEXT("WaterNode_")))
		{
			WaterNodeId = FName(*Value.RightChop(10));
		}
		else if (Value.StartsWith(TEXT("WaterRoute_")))
		{
			RouteId = FName(*Value.RightChop(11));
		}
	}
	if (ControllerComponent)
	{
		ControllerComponent->NodeConfig.NetworkId = WaterNetworkId;
		ControllerComponent->NodeConfig.NodeId = WaterNodeId;
		ControllerComponent->DeviceId = StableActorId;
		ControllerComponent->InteractionRouteId = RouteId;
	}
}
