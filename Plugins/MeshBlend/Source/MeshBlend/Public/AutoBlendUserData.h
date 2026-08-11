// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/MeshComponent.h"
#include "Engine/AssetUserData.h"
#include "Engine/StaticMesh.h"
#include "AutoBlendUserData.generated.h"

UENUM(BlueprintType)
enum EAutoBlendOption : uint8
{
	Small = 0 UMETA(DisplayName = "Small"),
	Medium = 1 UMETA(DisplayName = "Medium"),
	Large = 2 UMETA(DisplayName = "Large"),
	Extra_Large = 3 UMETA(DisplayName = "Extra Large"),
	Disabled = 4 UMETA(DisplayName = "Extra Large", Hidden)
};

UCLASS(BlueprintType)
class MESHBLEND_API UAutoBlendUserData : public UAssetUserData
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MeshBlend")
	TEnumAsByte<EAutoBlendOption> AutoBlendOption = Medium;
};


class MESHBLEND_API FUAutoBlendHelper
{
public:
	static bool TryGetBlendOptionFromActorTag(const AActor* Actor, EAutoBlendOption& AutoBlendOption);
	static bool TryGetBlendOptionFromComponentTag(const UMeshComponent* MeshComponent, EAutoBlendOption& AutoBlendOption);
	static EAutoBlendOption GetLargestAutoBlendState(const AActor* Actor);
	static bool DoesItBlend(const AActor* Actor);
};
