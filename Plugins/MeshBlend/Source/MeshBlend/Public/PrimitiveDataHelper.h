// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/InstancedStaticMeshComponent.h"

const FName GName_AutoBlendHasPrimitiveData = TEXT("AutoBlend_HasPrimitiveData");


class MESHBLEND_API FPrimitiveDataHelper
{
public:
	static void EnsurePrimitiveDataSlot(UMeshComponent* StaticMeshComponent, const int32 CustomPrimitiveDataIndex);
	static void SetCustomDataValue(UInstancedStaticMeshComponent* InstancedStaticMeshComponent, int32 InstanceIndex, int32 CustomPrimitiveDataIndex, float Value);
};
