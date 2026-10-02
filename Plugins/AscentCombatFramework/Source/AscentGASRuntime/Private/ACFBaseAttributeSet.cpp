// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFBaseAttributeSet.h"
#include "ACFGASTypes.h"
#include "AbilitySystemComponent.h"

void UACFBaseAttributeSet::PreAttributeChange(const FGameplayAttribute& Attribute, float& NewValue)
{
    ExecuteClamp(Attribute, NewValue);
    Super::PreAttributeChange(Attribute, NewValue);
}

void UACFBaseAttributeSet::PreAttributeBaseChange(const FGameplayAttribute& Attribute, float& NewValue) const
{
    ExecuteClamp(Attribute, NewValue);
    Super::PreAttributeBaseChange(Attribute, NewValue);
}

void UACFBaseAttributeSet::PostAttributeChange(const FGameplayAttribute& Attribute, float OldValue, float NewValue)
{
    Super::PostAttributeChange(Attribute, OldValue, NewValue);
    NormalizeClampedAttributesForMaxChange(Attribute, OldValue, NewValue);
}

void UACFBaseAttributeSet::ExecuteClamp(const FGameplayAttribute& Attribute, float& NewValue) const
{
    if (Clamps.Contains(Attribute)) {
        const UAbilitySystemComponent* abilityComp = GetOwningAbilitySystemComponent();
        const FAttributeClamps* clampData = Clamps.FindByKey(Attribute);
        if (abilityComp && clampData) {
            bool bFound;
            const float MaxValue = abilityComp->GetGameplayAttributeValue(clampData->MaxValueAttribute, bFound);
            const float currentValue = abilityComp->GetGameplayAttributeValue(clampData->AttributeToClamp, bFound);
            if (bFound) {
                if (clampData->bClampToZero) {
                    NewValue = FMath::Clamp(NewValue, 0.f, MaxValue);
                } else {
                    NewValue = FMath::Clamp(NewValue, -BIG_NUMBER, MaxValue);
                }
            }
        }
    }
}

void UACFBaseAttributeSet::NormalizeClampedAttributesForMaxChange(const FGameplayAttribute& MaxAttribute, float OldMaxValue, float NewMaxValue) const
{
    if (OldMaxValue <= 0.0f || FMath::IsNearlyEqual(OldMaxValue, NewMaxValue)) {
        return;
    }

    UAbilitySystemComponent* AbilityComp = GetOwningAbilitySystemComponent();
    if (!AbilityComp) {
        return;
    }

    for (const FAttributeClamps& ClampData : Clamps) {
        if (ClampData.MaxValueAttribute != MaxAttribute || !ClampData.AttributeToClamp.IsValid()) {
            continue;
        }

        bool bFoundCurrent = false;
        const float CurrentValue = AbilityComp->GetGameplayAttributeValue(ClampData.AttributeToClamp, bFoundCurrent);
        if (!bFoundCurrent) {
            continue;
        }

        const float NormalizedValue = FMath::Clamp(CurrentValue / OldMaxValue, 0.0f, 1.0f);
        const float NewCurrentValue = NewMaxValue * NormalizedValue;
        AbilityComp->SetNumericAttributeBase(ClampData.AttributeToClamp, NewCurrentValue);
    }
}
