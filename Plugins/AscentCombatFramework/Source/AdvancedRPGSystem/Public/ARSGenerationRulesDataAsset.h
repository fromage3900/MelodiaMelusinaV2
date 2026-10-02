// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "ARSGenerationRulesDataAsset.generated.h"

/**
 *
 */
UCLASS()
class ADVANCEDRPGSYSTEM_API UARSGenerationRulesDataAsset : public UPrimaryDataAsset {
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = ARS)
    bool TryGetGenerationRulesForPrimaryAttributes(const FGameplayTag& primaryAttribute, FGenerationRule& outRule) const;

protected:
    /*Define with Curves how your Attributes generates your Parameters and your Statistics */
    UPROPERTY(EditAnywhere, meta = (TitleProperty = "PrimaryAttributesTag"), Category = ARS)
    TArray<FGenerationRule> AttributesGenerationRules;
};
