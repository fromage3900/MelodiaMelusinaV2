// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFStatisticExecutionCalculation.h"
#include "ARSTypes.h"
#include "ARSFunctionLibrary.h"
#include <AttributeSet.h>
#include <GameplayEffectTypes.h>
#include <AbilitySystemComponent.h>

void UACFStatisticExecutionCalculation::Execute_Implementation(const FGameplayEffectCustomExecutionParameters& ExecutionParams, FGameplayEffectCustomExecutionOutput& OutExecutionOutput) const
{
    const FGameplayEffectSpec& Spec = ExecutionParams.GetOwningSpec();
    const FACFStatModifierContext* Context = static_cast<const FACFStatModifierContext*>(Spec.GetContext().Get());
    if (!Context) {
        UE_LOG(LogTemp, Warning, TEXT("Invalid context in execution calculation - UACFStatisticExecutionCalculation"));
        return;
    }

    const TArray<FStatisticValue>& ModifierSet = Context->Costs;
    if (ModifierSet.Num() == 0) {
        UE_LOG(LogTemp, Warning, TEXT("No stat modifiers found in FACFStatModifierContext. - UACFStatisticExecutionCalculation"));
        return;
    }

    UAbilitySystemComponent* TargetASC = ExecutionParams.GetTargetAbilitySystemComponent();
    const UAbilitySystemComponent* SourceASC = ExecutionParams.GetSourceAbilitySystemComponent();

    for (const FStatisticValue& Stat : ModifierSet) {
        FStatisticsConfig statConfig;

        if (!UARSFunctionLibrary::TryGetStatisticFromSetByCallerTag(Stat.Statistic, statConfig)) {
            UE_LOG(LogTemp, Warning, TEXT("Invalid Stat Set By Caller Tag - UACFStatisticExecutionCalculation"));

            continue;
        }

        const FGameplayAttribute finalAttribute = statConfig.CurrentStatAttribute;

        const float finalValue = -Stat.Value;

        OutExecutionOutput.AddOutputModifier(FGameplayModifierEvaluatedData(finalAttribute, EGameplayModOp::Additive, finalValue));
    }
}
