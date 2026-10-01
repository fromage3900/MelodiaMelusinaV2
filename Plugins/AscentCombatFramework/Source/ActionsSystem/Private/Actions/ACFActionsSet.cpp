// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFActionsSet.h"
#include "ACFActionTypes.h"
#include "GameplayTagContainer.h"

bool UACFActionsSet::GetActionByTag(const FGameplayTag& Action, FActionState& outAction) const
{
    const FActionState* actionState = Actions.FindByKey(Action);
    if (actionState) {
        outAction = *actionState;
        return true;
    }
    return false;
}



