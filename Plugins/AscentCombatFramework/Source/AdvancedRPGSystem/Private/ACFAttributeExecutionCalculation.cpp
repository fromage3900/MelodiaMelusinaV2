// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAttributeExecutionCalculation.h"
#include "ARSFunctionLibrary.h"
#include "ARSTypes.h"
#include <AbilitySystemComponent.h>

void UACFAttributeExecutionCalculation::Execute_Implementation(
    const FGameplayEffectCustomExecutionParameters& ExecutionParams,
    FGameplayEffectCustomExecutionOutput& OutExecutionOutput) const
{
    const FGameplayEffectSpec& Spec = ExecutionParams.GetOwningSpec();
    const FACFAttributeModifierContext* Context = static_cast<const FACFAttributeModifierContext*>(Spec.GetContext().Get());
    if (!Context) {
        UE_LOG(LogTemp, Warning, TEXT("Invalid context in execution calculation."));
        return;
    }

    const FAttributesSetModifier& ModifierSet = Context->Modifiers;
    if (ModifierSet.PrimaryAttributesMod.Num() == 0 && ModifierSet.AttributesMod.Num() == 0 && ModifierSet.StatisticsMod.Num() == 0) {
        UE_LOG(LogTemp, Warning, TEXT("No attribute modifiers found in FAttributesSetModifier."));
        return;
    }

    UAbilitySystemComponent* TargetASC = ExecutionParams.GetTargetAbilitySystemComponent();
    const UAbilitySystemComponent* SourceASC = ExecutionParams.GetSourceAbilitySystemComponent();

    for (const FAttributeModifier& Modifier : ModifierSet.PrimaryAttributesMod) {
        FGameplayAttribute Attribute;

        if (!UARSFunctionLibrary::TryGetAttributeFromSetByCallerTag(Modifier.AttributeType, Attribute)) {
            continue;
        }

        float FinalValue = Modifier.Value;
        if (Modifier.ModType == EModifierType::EPercentage && SourceASC) {
            const float BaseValue = SourceASC->GetNumericAttribute(Attribute);
            FinalValue = BaseValue * Modifier.Value / 100.f;
        }

        OutExecutionOutput.AddOutputModifier(FGameplayModifierEvaluatedData(Attribute, EGameplayModOp::Additive, FinalValue));
    }

    for (const FAttributeModifier& Modifier : ModifierSet.AttributesMod) {
        FGameplayAttribute Attribute;

        if (!UARSFunctionLibrary::TryGetAttributeFromSetByCallerTag(Modifier.AttributeType, Attribute)) {
            continue;
        }

        float FinalValue = Modifier.Value;
        if (Modifier.ModType == EModifierType::EPercentage && SourceASC) {
            const float BaseValue = SourceASC->GetNumericAttribute(Attribute);
            FinalValue = BaseValue * Modifier.Value / 100.f;
        }

        OutExecutionOutput.AddOutputModifier(FGameplayModifierEvaluatedData(Attribute, EGameplayModOp::Additive, FinalValue));
    }

    for (const FStatisticsModifier& Stat : ModifierSet.StatisticsMod) {
        FGameplayAttribute Attribute;

        if (!UARSFunctionLibrary::TryGetAttributeFromSetByCallerTag(Stat.AttributeType, Attribute)) {
            continue;
        }

        float FinalValue = Stat.MaxValue;
        if (Stat.ModType == EModifierType::EPercentage && SourceASC) {
            const float BaseValue = SourceASC->GetNumericAttribute(Attribute);
            FinalValue = BaseValue * Stat.MaxValue / 100.f;
        }

        OutExecutionOutput.AddOutputModifier(FGameplayModifierEvaluatedData(Attribute, EGameplayModOp::Additive, FinalValue));
    }
}
