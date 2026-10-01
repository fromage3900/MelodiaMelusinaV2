// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFPrimaryAttributeSet.h"
#include "ACFGASTypes.h"
#include "Net/UnrealNetwork.h"
#include "AbilitySystemComponent.h"
#include "AttributeSet.h"

UACFPrimaryAttributeSet::UACFPrimaryAttributeSet()
{
 

}



void UACFPrimaryAttributeSet::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

   
    DOREPLIFETIME_CONDITION_NOTIFY(UACFPrimaryAttributeSet, Strength, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFPrimaryAttributeSet, Intelligence, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFPrimaryAttributeSet, Endurance, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFPrimaryAttributeSet, Constitution, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFPrimaryAttributeSet, Dexterity, COND_None, REPNOTIFY_Always);
}
