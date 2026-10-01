// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAttributeSet.h"
#include "ACFGASTypes.h"
#include "AbilitySystemComponent.h"
#include "AttributeSet.h"
#include "Net/UnrealNetwork.h"

UACFAttributeSet::UACFAttributeSet()
{
}

void UACFAttributeSet::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    DOREPLIFETIME_CONDITION_NOTIFY(UACFAttributeSet, MeleeDamage, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFAttributeSet, RangedDamage, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFAttributeSet, SpellDefense, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFAttributeSet, SpellDamage, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFAttributeSet, PhysicalDefense, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFAttributeSet, CritChance, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UACFAttributeSet, BlockDefense, COND_None, REPNOTIFY_Always);
}
