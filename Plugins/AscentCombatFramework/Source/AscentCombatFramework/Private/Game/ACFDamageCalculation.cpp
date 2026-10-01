// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "Game/ACFDamageCalculation.h"
#include "Game/ACFDamageType.h"





float UACFDamageCalculation::CalculateFinalDamage_Implementation(const FACFDamageEvent& inDamageEvent , TArray<FAttributeData>& otherAffectedAttributes)
{
    //Implement Me
    return inDamageEvent.FinalDamage;
}

FGameplayTag UACFDamageCalculation::EvaluateHitResponseAction_Implementation(const FACFDamageEvent& inDamageEvent, 
	const TArray<FOnHitActionChances>& hitResponseActions)
{
    return FGameplayTag();
}

bool UACFDamageCalculation::IsCriticalDamage_Implementation(const FACFDamageEvent& inDamageEvent)
{
	return false;
}


UACFDamageType* UACFDamageCalculation::GetDamageType(const FACFDamageEvent& inDamageEvent) 
{
    if (inDamageEvent.DamageClass) {
        return Cast<UACFDamageType>( inDamageEvent.DamageClass->GetDefaultObject(true));
    }
    
    return nullptr;
}

