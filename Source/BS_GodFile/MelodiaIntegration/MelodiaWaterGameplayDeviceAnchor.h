#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "PCGPoint.h"
#include "MelodiaWaterGameplayDeviceAnchor.generated.h"

class UBoxComponent;
class UPCGMetadata;
class UMelodiaWaterGameplayControllerComponent;

/** Stable PCG-spawned anchor for valves, pumps, gates, reservoirs and currents. */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaWaterGameplayDeviceAnchor : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaWaterGameplayDeviceAnchor();

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Melodia|Water|PCG")
	void InitializeFromPCGPoint(FPCGPoint Point, const UPCGMetadata* Metadata);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Water|Anchor")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Water|Anchor")
	TObjectPtr<UBoxComponent> InteractionVolume;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Water|Anchor")
	TObjectPtr<UMelodiaWaterGameplayControllerComponent> ControllerComponent;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Anchor")
	FName StableActorId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Anchor")
	FName GameplayRole = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Anchor")
	FGameplayTag WaterNetworkId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Anchor")
	FGameplayTag WaterNodeId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Anchor")
	FGameplayTag RouteId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Anchor")
	FName GameplayDataLayer = TEXT("DL_Musical_HeroGameplay");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Anchor")
	bool bExcludeFromHLOD = true;
};
