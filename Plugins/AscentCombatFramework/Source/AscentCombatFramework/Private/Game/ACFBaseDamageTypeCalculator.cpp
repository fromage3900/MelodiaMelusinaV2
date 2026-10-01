// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "Game/ACFBaseDamageTypeCalculator.h"

bool UACFBaseDamageTypeCalculator::EvaluetHitResponseAction(const FOnHitActionChances& action, const FACFDamageEvent& damageEvent)
{
    if ((uint8)damageEvent.DamageDirection != (uint8)action.AllowedFromDirection && action.AllowedFromDirection != EActionDirection::EveryDirection)
        return false;

    for (const TSubclassOf<UDamageType>& damageType : action.AllowedDamageTypes) {
        if (damageEvent.DamageClass->IsChildOf(damageType))
            return true;
    }
    return false;
}

float UACFBaseDamageTypeCalculator::Internal_CalculateDamage(const FACFDamageEvent& inDamageEvent)
{
    return 0.f;
}
