// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "AutoBlendUserData.h"
#include "Components/MeshComponent.h"

#include "MeshBlendShared.generated.h"

const FName GName_AutoBlendID = TEXT("AutoBlendID");

const FName GName_AutoBlendSmall = TEXT("AutoBlend_Small");
const FName GName_AutoBlendMedium = TEXT("AutoBlend_Medium");
const FName GName_AutoBlendLarge = TEXT("AutoBlend_Large");
const FName GName_AutoBlendExtraLarge = TEXT("AutoBlend_ExtraLarge");
const FName GName_Disabled = TEXT("AutoBlend_Disabled");
const FName GName_PooledActor = TEXT("AutoBlend_PooledActor");

constexpr int StencilStartSmall = 7;
constexpr int StencilStartMedium = 70;
constexpr int StencilStartLarge = 133;
constexpr int StencilStartExtraLarge = 196;

// StencilRange and ClampedStencilRange should be an odd number since we increase the BlendCounter by 2 each time. We increase by 2 to leave room for inner mesh blending techniques.
constexpr int StencilRange = 57;
constexpr int ReservedStencilRange = 4;
constexpr int ClampedStencilRange = StencilRange - ReservedStencilRange;

USTRUCT()
struct FActorBounds
{
	GENERATED_BODY()

	UPROPERTY()
	FVector Origin = FVector::Zero();

	UPROPERTY()
	float Radius = 0.0f;
};

class MESHBLEND_API FMeshBlendShared
{
public:
	static bool IsOverProcessBudget(const double MaxDuration);
	static FActorBounds GetBounds(const AActor* Actor);
	static const UAutoBlendUserData* GetAutoBlendUserData(const UMeshComponent* MeshComponent);
	static FBoxSphereBounds GetMeshBounds(UMeshComponent* MeshComponent);
	static bool GetCurrentCameraLocation(const UWorld* World, FVector& Location);
};
