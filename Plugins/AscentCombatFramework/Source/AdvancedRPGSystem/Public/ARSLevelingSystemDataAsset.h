// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ARSTypes.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "ARSLevelingSystemDataAsset.generated.h"


struct FAttributesByLevel;

/**
 *
 */
UCLASS()
class ADVANCEDRPGSYSTEM_API UARSLevelingSystemDataAsset : public UPrimaryDataAsset {
    GENERATED_BODY()

public: 

    void GetAllAttributesValueByLevel(const int32 level, TArray<FAttribute>& outAttributes) const;

    
    
 protected:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ARS")
    TArray<FAttributesByLevel> AttributesByLevelCurves;
};
