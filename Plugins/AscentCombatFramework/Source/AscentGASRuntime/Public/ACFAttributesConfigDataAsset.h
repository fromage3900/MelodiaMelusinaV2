// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include <AttributeSet.h>

#include "ACFAttributesConfigDataAsset.generated.h"


/**
 *
 */
UCLASS()
class ASCENTGASRUNTIME_API UACFAttributesConfigDataAsset : public UPrimaryDataAsset {
    GENERATED_BODY()

public:
    /**
     * Handle to the mapping between the names of the curves
     * and the attributes to be used to automatically generate stats while leveling
     */
    UPROPERTY(EditAnywhere, Category = "ACF")
    TMap<FName, FGameplayAttribute> AttributesByCurveRow;
};
