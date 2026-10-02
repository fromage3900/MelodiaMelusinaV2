// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2024. All Rights Reserved.

#include "ACFClimbingMontageDataAsset.h"

bool UACFClimbingMontageDataAsset::GetEntryForDirection(EClimbingDirection Direction, FClimbingDirectionEntry& OutEntry) const
{
    for (const FClimbingDirectionEntry& Entry : DirectionEntries)
    {
        if (Entry.Direction == Direction)
        {
            OutEntry = Entry;
            return true;
        }
    }
    return false;
}

UAnimMontage* UACFClimbingMontageDataAsset::GetMontageForDirection(EClimbingDirection Direction) const
{
    FClimbingDirectionEntry Entry;
    if (GetEntryForDirection(Direction, Entry))
    {
        return Entry.Montage;
    }
    return nullptr;
}

FGameplayTag UACFClimbingMontageDataAsset::GetAbilityTagForDirection(EClimbingDirection Direction) const
{
    FClimbingDirectionEntry Entry;
    if (GetEntryForDirection(Direction, Entry))
    {
        return Entry.AbilityTag;
    }
    return FGameplayTag();
}
