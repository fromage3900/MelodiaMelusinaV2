// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CASTypes.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "ACFCombinedAnimationsDataAsset.generated.h"

/**
 * Primary data asset that stores combined animation configurations used in ACF Contextual Animation System.
 */
UCLASS()
class COMBINEDANIMATIONSSYSTEM_API UACFCombinedAnimationsDataAsset : public UPrimaryDataAsset {
    GENERATED_BODY()

public:
    /**
     * Retrieves all the combined animation configurations stored in this asset.
     *
     * @param outCombinedAnims Output array that will be filled with the combined animation data.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    void GetCombinedAnims(TArray<FCombinedAnimConfig>& outCombinedAnims)
    {
        outCombinedAnims = CombinedAnimations;
    }

protected:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combined Animations")
    TArray<FCombinedAnimConfig> CombinedAnimations;
};
