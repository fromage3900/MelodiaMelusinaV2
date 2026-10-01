// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFStatisticsSet.h"
#include "ACFGASTypes.h"
#include "Net/UnrealNetwork.h"
#include "AbilitySystemComponent.h"
#include "AttributeSet.h"

UACFStatisticsSet::UACFStatisticsSet()
{

}



void UACFStatisticsSet::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    DOREPLIFETIME(UACFStatisticsSet, MaxHealth);
    DOREPLIFETIME(UACFStatisticsSet, Health);
    DOREPLIFETIME(UACFStatisticsSet, HealthRegen);
    DOREPLIFETIME(UACFStatisticsSet, MaxStamina);
    DOREPLIFETIME(UACFStatisticsSet, Stamina);
    DOREPLIFETIME(UACFStatisticsSet, StaminaRegen);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFStatisticsSet, MaxMana, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFStatisticsSet, Mana, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFStatisticsSet, ManaRegen, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFStatisticsSet, MaxEquilibrium, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFStatisticsSet, Equilibrium, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFStatisticsSet, EquilibriumRegen, COND_None, REPNOTIFY_Always);
 
}
