// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "AutoBlendUserData.h"
#include "BlendValueBucket.h"
#include "MeshBlendPrimitiveDataIndexHelper.h"
#include "MeshBlendShared.h"
#include "GameFramework/Actor.h"

#include "MeshBlendProcessor.generated.h"


UCLASS()
class MESHBLEND_API UMeshBlendProcessor : public UObject
{
	GENERATED_BODY()

public:
	void Reset();
	uint8 GetAutoBlendID(EAutoBlendOption MeshAutoBlendState);
	uint8 GetReservedAutoBlendID(EAutoBlendOption MeshAutoBlendState, uint8 Offset);
	uint8 AssignAutoBlendId(const FBox& Box, EAutoBlendOption MeshAutoBlendState);
	bool ActivateActor(AActor* Actor, double MaxProcessDuration, bool bIsCooking);

	int SmallBlendCounter = StencilStartSmall;
	int MediumBlendCounter = StencilStartMedium;
	int LargeBlendCounter = StencilStartLarge;
	int ExtraLargeBlendCounter = StencilStartExtraLarge;

	int ActorActivationComponentIndex = 0;
	int ActorActivationComponentInstanceIndex = 0;

private:
	UPROPERTY(Transient, DuplicateTransient)
	TMap<uint8, FBlendValueBucket> BlendValueBucket;

	UPROPERTY(Transient, DuplicateTransient)
	FMeshBlendPrimitiveDataIndexHelper PrimitiveDataIndexHelper;
};
