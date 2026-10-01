// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayEffectExecutionCalculation.h"

#include "ACFStatisticExecutionCalculation.generated.h"

/**
 * Custom execution calculation class for handling ACF  statistic modifications.
 * This class extends UGameplayEffectExecutionCalculation to provide specialized calculation logic
 * for statistic-based gameplay effects within the Advanced RPG System.
 */
UCLASS()
class ADVANCEDRPGSYSTEM_API UACFStatisticExecutionCalculation : public UGameplayEffectExecutionCalculation
{
    GENERATED_BODY()

public:
    /**
     * Executes the custom calculation logic for gameplay effects.
     * This implementation handles the computation and application of statistic modifications
     * based on the provided execution parameters.
     * 
     * @param ExecutionParams - Contains all the contextual information needed for the calculation,
     *                         including  the array of statistic values
     * @param OutExecutionOutput - Output structure that will contain the calculated modifications
     *                            to be applied to the target's attributes
     */
    void Execute_Implementation(const FGameplayEffectCustomExecutionParameters& ExecutionParams, 
                              FGameplayEffectCustomExecutionOutput& OutExecutionOutput) const override;
};
