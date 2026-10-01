// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFExecutionConditionsFragment.h"

#include "ACFCombinedAnimSlaveComponent.h"
#include "CASAnimCondition.h"
#include "GameFramework/Pawn.h"

void UACFExecutionConditionsFragment::ApplyFragment_Implementation(APawn* pawnOwner)
{
    if (!pawnOwner)
    {
        return;
    }

    UACFCombinedAnimSlaveComponent* SlaveComp = pawnOwner->FindComponentByClass<UACFCombinedAnimSlaveComponent>();
    if (!SlaveComp)
    {
        return;
    }

    // Build a plain-pointer array since the slave setter takes TArray<UCASAnimCondition*>.
    // We intentionally replace (not append): the fragment is the authoritative source of
    // conditions when applied, allowing different character archetypes to swap entire
    // execution rule-sets from a DataAsset.
    TArray<UCASAnimCondition*> ResolvedConditions;
    ResolvedConditions.Reserve(Conditions.Num());
    for (const TObjectPtr<UCASAnimCondition>& Condition : Conditions)
    {
        if (Condition)
        {
            ResolvedConditions.Add(Condition);
        }
    }

    SlaveComp->SetAnimStartingConditions(ResolvedConditions);
}
