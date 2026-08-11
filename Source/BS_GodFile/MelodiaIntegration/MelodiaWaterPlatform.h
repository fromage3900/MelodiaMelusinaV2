#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PCGPoint.h"
#include "MelodiaWaterGameplayTypes.h"
#include "MelodiaWaterPlatform.generated.h"

class UPCGMetadata;
class UMelodiaWaterBuoyancyComponent;
class UMelodiaWaterPlatformMotionComponent;
class UPrimitiveComponent;
class UStaticMeshComponent;

/** Gameplay-owned platform spawned by the interactive PCG placement lane. */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaWaterPlatform : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaWaterPlatform();

	virtual void BeginPlay() override;

	/** PCG post-spawn hook. The point seed is the stable actor identity. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Melodia|Water|PCG")
	void InitializeFromPCGPoint(FPCGPoint Point, const UPCGMetadata* Metadata);

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Platform")
	FName GetStablePlatformId() const { return PlatformId; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Platform")
	EMelodiaWaterPlatformMotionMode GetMotionMode() const { return MotionMode; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Platform")
	UPrimitiveComponent* GetPhysicsPrimitive() const;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Platform")
	void ResetPhysicsToAuthoredState();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Water|Platform")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Water|Platform")
	TObjectPtr<UStaticMeshComponent> PlatformMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Water|Platform")
	TObjectPtr<UMelodiaWaterPlatformMotionComponent> MotionComponent;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Water|Platform")
	TObjectPtr<UMelodiaWaterBuoyancyComponent> BuoyancyComponent;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG")
	FName PlatformId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG")
	int32 WorldSeed = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG")
	int32 ChunkX = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG")
	int32 ChunkY = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG")
	FName HeroSlot = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG")
	int32 LocalIndex = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG")
	FName GameplayRole = TEXT("water_platform");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG")
	FName WaterNetworkId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG")
	FName OwningChunk = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG")
	FName GameplayDataLayer = TEXT("DL_Musical_HeroGameplay");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG")
	bool bExcludeFromHLOD = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG")
	bool bNoMerging = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform")
	EMelodiaWaterPlatformMotionMode MotionMode = EMelodiaWaterPlatformMotionMode::KinematicRoute;

private:
	FTransform AuthoredTransform;
	int32 PointSeed = 0;
};

