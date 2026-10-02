// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayEffectExecutionCalculation.h"

#include "ACFAttributeExecutionCalculation.generated.h"

/**
 *
 */
UCLASS()
class ADVANCEDRPGSYSTEM_API UACFAttributeExecutionCalculation : public UGameplayEffectExecutionCalculation {
    GENERATED_BODY()

public:
     void Execute_Implementation(const FGameplayEffectCustomExecutionParameters& ExecutionParams, FGameplayEffectCustomExecutionOutput& OutExecutionOutput) const;
};
